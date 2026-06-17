from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from garage_app.domain.facturation.facture import Facture, LigneFacture
from garage_app.domain.facturation.repositories import FactureRepository
from garage_app.infrastructure.db.models.facture_model import FactureModel, LigneFactureModel


class SqlAlchemyFactureRepository(FactureRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_by_id(self, entity_id: uuid.UUID) -> Facture | None:
        m = self._s.get(FactureModel, str(entity_id))
        return self._to_domain(m) if m else None

    def find_by_dossier(self, dossier_id: uuid.UUID) -> Facture | None:
        m = self._s.query(FactureModel).filter_by(dossier_id=str(dossier_id)).first()
        return self._to_domain(m) if m else None

    def find_impayees(self) -> list[Facture]:
        rows = self._s.query(FactureModel).filter_by(statut_paiement="en_attente").all()
        return [self._to_domain(m) for m in rows]

    def find_all(self) -> list[Facture]:
        return [self._to_domain(m) for m in self._s.query(FactureModel).all()]

    def next_numero(self) -> str:
        year = datetime.now(timezone.utc).year
        count = self._s.query(FactureModel).count() + 1
        return f"F{year}-{count:04d}"

    def save(self, f: Facture) -> None:
        m = self._s.get(FactureModel, str(f.id))
        if m:
            m.statut_paiement = f.statut_paiement
            m.mode_paiement = f.mode_paiement
        else:
            m = FactureModel(
                id=str(f.id),
                dossier_id=str(f.dossier_id),
                numero=f.numero,
                montant_ht=float(f.montant_ht.amount),
                taux_tva=float(f.taux_tva),
                montant_ttc=float(f.montant_ttc.amount),
                statut_paiement=f.statut_paiement,
            )
            for l in f.lignes:
                m.lignes.append(LigneFactureModel(
                    facture_id=str(f.id),
                    designation=l.designation,
                    quantite=l.quantite,
                    prix_unitaire=float(l.prix_unitaire),
                ))
            self._s.add(m)

    def delete(self, entity_id: uuid.UUID) -> None:
        m = self._s.get(FactureModel, str(entity_id))
        if m:
            self._s.delete(m)

    @staticmethod
    def _to_domain(m: FactureModel) -> Facture:
        f = Facture(id=uuid.UUID(m.id))
        f.dossier_id = uuid.UUID(m.dossier_id) if m.dossier_id else f.dossier_id
        f.numero = m.numero
        f.taux_tva = Decimal(str(m.taux_tva))
        f.statut_paiement = m.statut_paiement
        f.mode_paiement = m.mode_paiement
        for l in m.lignes:
            f.lignes.append(LigneFacture(
                designation=l.designation,
                quantite=l.quantite,
                prix_unitaire=Decimal(str(l.prix_unitaire)),
            ))
        return f
