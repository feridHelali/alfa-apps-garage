from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from garage_app.domain.facturation.facture_achat import FactureAchat, LigneAchat, StatutAchat
from garage_app.infrastructure.db.models.facture_achat_model import FactureAchatModel, LigneAchatModel
from garage_app.infrastructure.db.session import SessionFactory


class FactureAchatRepository:
    def __init__(self, sf: SessionFactory) -> None:
        self._sf = sf

    def get_by_id(self, entity_id: uuid.UUID) -> FactureAchat | None:
        with self._sf.get_session() as s:
            m = s.get(FactureAchatModel, str(entity_id))
            return self._to_domain(m) if m else None

    def find_all(self) -> list[FactureAchat]:
        with self._sf.get_session() as s:
            rows = (
                s.query(FactureAchatModel)
                .order_by(FactureAchatModel.date_facture.desc())
                .all()
            )
            return [self._to_domain(m) for m in rows]

    def find_by_fournisseur(self, fournisseur_id: uuid.UUID) -> list[FactureAchat]:
        with self._sf.get_session() as s:
            rows = (
                s.query(FactureAchatModel)
                .filter_by(fournisseur_id=str(fournisseur_id))
                .order_by(FactureAchatModel.date_facture.desc())
                .all()
            )
            return [self._to_domain(m) for m in rows]

    def save(self, fa: FactureAchat) -> None:
        with self._sf.get_session() as s:
            m = s.get(FactureAchatModel, str(fa.id))
            if m:
                m.statut = fa.statut.value
                m.notes = fa.notes
                m.montant_ht = float(fa.montant_ht)
                m.montant_ttc = float(fa.montant_ttc)
            else:
                m = FactureAchatModel(
                    id=str(fa.id),
                    fournisseur_id=str(fa.fournisseur_id),
                    numero_fournisseur=fa.numero_fournisseur,
                    notre_numero=fa.notre_numero,
                    date_facture=fa.date_facture,
                    date_echeance=fa.date_echeance,
                    statut=fa.statut.value,
                    commande_id=str(fa.commande_id) if fa.commande_id else None,
                    notes=fa.notes,
                    taux_tva=float(fa.taux_tva),
                    montant_ht=float(fa.montant_ht),
                    montant_ttc=float(fa.montant_ttc),
                )
                for l in fa.lignes:
                    m.lignes.append(LigneAchatModel(
                        id=str(l.id),
                        facture_achat_id=str(fa.id),
                        piece_id=str(l.piece_id),
                        designation=l.designation,
                        quantite=l.quantite,
                        prix_unitaire=float(l.prix_unitaire),
                    ))
                s.add(m)

    @staticmethod
    def _to_domain(m: FactureAchatModel) -> FactureAchat:
        fa = FactureAchat(id=uuid.UUID(m.id))
        fa.fournisseur_id = uuid.UUID(m.fournisseur_id)
        fa.numero_fournisseur = m.numero_fournisseur or ""
        fa.notre_numero = m.notre_numero or ""
        fa.date_facture = m.date_facture if isinstance(m.date_facture, datetime) else datetime.now()
        fa.date_echeance = m.date_echeance if isinstance(m.date_echeance, datetime) else None
        fa.commande_id = uuid.UUID(m.commande_id) if m.commande_id else None
        fa.notes = m.notes or ""
        fa.taux_tva = Decimal(str(m.taux_tva or 19))
        try:
            fa.statut = StatutAchat(m.statut)
        except ValueError:
            fa.statut = StatutAchat.SAISIE
        for l in (m.lignes or []):
            ligne = LigneAchat(id=uuid.UUID(l.id))
            ligne.piece_id = uuid.UUID(l.piece_id)
            ligne.designation = l.designation or ""
            ligne.quantite = l.quantite
            ligne.prix_unitaire = Decimal(str(l.prix_unitaire))
            fa.lignes.append(ligne)
        return fa
