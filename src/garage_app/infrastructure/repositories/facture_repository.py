from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from garage_app.domain.facturation.facture import Facture, LigneFacture, Paiement, StatutFacture
from garage_app.domain.facturation.repositories import FactureRepository
from garage_app.infrastructure.db.models.facture_model import FactureModel, LigneFactureModel, PaiementModel
from garage_app.infrastructure.db.session import SessionFactory


class SqlAlchemyFactureRepository(FactureRepository):
    def __init__(self, sf: SessionFactory) -> None:
        self._sf = sf

    def get_by_id(self, entity_id: uuid.UUID) -> Facture | None:
        with self._sf.get_session() as s:
            m = s.get(FactureModel, str(entity_id))
            return self._to_domain(m) if m else None

    def find_by_dossier(self, dossier_id: uuid.UUID) -> Facture | None:
        with self._sf.get_session() as s:
            m = s.query(FactureModel).filter_by(dossier_id=str(dossier_id)).first()
            return self._to_domain(m) if m else None

    def find_by_client(self, client_id: uuid.UUID) -> list[Facture]:
        with self._sf.get_session() as s:
            rows = s.query(FactureModel).filter_by(client_id=str(client_id)).all()
            return [self._to_domain(m) for m in rows]

    def find_by_statut(self, statut: StatutFacture) -> list[Facture]:
        with self._sf.get_session() as s:
            rows = (
                s.query(FactureModel)
                .filter(FactureModel.statut == statut.value)
                .order_by(FactureModel.date_emission.desc())
                .all()
            )
            return [self._to_domain(m) for m in rows]

    def find_impayees(self) -> list[Facture]:
        with self._sf.get_session() as s:
            rows = (
                s.query(FactureModel)
                .filter(FactureModel.statut.in_(["emise", "partiellement_payee"]))
                .order_by(FactureModel.date_emission.desc())
                .all()
            )
            return [self._to_domain(m) for m in rows]

    def find_all(self) -> list[Facture]:
        with self._sf.get_session() as s:
            rows = s.query(FactureModel).order_by(FactureModel.date_emission.desc()).all()
            return [self._to_domain(m) for m in rows]

    def next_numero(self) -> str:
        with self._sf.get_session() as s:
            year = datetime.now(timezone.utc).year
            prefix = f"F{year}-"
            rows = s.query(FactureModel.numero).filter(
                FactureModel.numero.like(f"{prefix}%")
            ).all()
            nums = []
            for (num,) in rows:
                try:
                    nums.append(int(num[len(prefix):]))
                except (ValueError, TypeError):
                    pass
            n = (max(nums) + 1) if nums else 1
            return f"{prefix}{n:04d}"

    def save(self, f: Facture) -> None:
        with self._sf.get_session() as s:
            m = s.get(FactureModel, str(f.id))
            if m:
                m.statut = f.statut.value
                m.solde_restant = float(f.solde_restant)
                m.notes = f.notes
                existing_ids = {p.id for p in m.paiements}
                for paiement in f.paiements:
                    if str(paiement.id) not in existing_ids:
                        m.paiements.append(PaiementModel(
                            id=str(paiement.id),
                            facture_id=str(f.id),
                            montant=float(paiement.montant),
                            mode=paiement.mode,
                            reference=paiement.reference,
                            date_paiement=paiement.date_paiement,
                        ))
            else:
                m = FactureModel(
                    id=str(f.id),
                    dossier_id=str(f.dossier_id),
                    client_id=str(f.client_id),
                    numero=f.numero,
                    date_emission=f.date_emission or datetime.now(timezone.utc),
                    montant_ht=float(f.montant_ht.amount),
                    taux_tva=float(f.taux_tva),
                    montant_ttc=float(f.montant_ttc.amount),
                    solde_restant=float(f.solde_restant),
                    statut=f.statut.value,
                    est_flotte=f.est_flotte,
                    notes=f.notes,
                )
                for l in f.lignes:
                    m.lignes.append(LigneFactureModel(
                        facture_id=str(f.id),
                        designation=l.designation,
                        quantite=l.quantite,
                        prix_unitaire=float(l.prix_unitaire),
                    ))
                for p in f.paiements:
                    m.paiements.append(PaiementModel(
                        id=str(p.id),
                        facture_id=str(f.id),
                        montant=float(p.montant),
                        mode=p.mode,
                        reference=p.reference,
                        date_paiement=p.date_paiement,
                    ))
                s.add(m)

    def delete(self, entity_id: uuid.UUID) -> None:
        with self._sf.get_session() as s:
            m = s.get(FactureModel, str(entity_id))
            if m:
                s.delete(m)

    @staticmethod
    def _to_domain(m: FactureModel) -> Facture:
        f = Facture(id=uuid.UUID(m.id))
        f.dossier_id = uuid.UUID(m.dossier_id) if m.dossier_id else f.dossier_id
        f.client_id = uuid.UUID(m.client_id) if m.client_id else f.client_id
        f.numero = m.numero
        f.taux_tva = Decimal(str(m.taux_tva or 19))
        f.est_flotte = bool(m.est_flotte)
        f.notes = m.notes or ""
        f.date_emission = m.date_emission if isinstance(m.date_emission, datetime) else None
        try:
            f.statut = StatutFacture(m.statut)
        except ValueError:
            f.statut = StatutFacture.BROUILLON
        for l in (m.lignes or []):
            f.lignes.append(LigneFacture(
                designation=l.designation,
                quantite=l.quantite,
                prix_unitaire=Decimal(str(l.prix_unitaire)),
            ))
        for p in (m.paiements or []):
            pmt = Paiement(id=uuid.UUID(p.id))
            pmt.montant = Decimal(str(p.montant))
            pmt.mode = p.mode
            pmt.reference = p.reference or ""
            pmt.date_paiement = p.date_paiement if isinstance(p.date_paiement, datetime) else datetime.now()
            f.paiements.append(pmt)
        return f
