from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from garage_app.domain.stock.commande_fournisseur import (
    CommandeFournisseur, LigneCommande, StatutCommande,
)
from garage_app.domain.stock.repositories import CommandeRepository
from garage_app.infrastructure.db.models.piece_model import (
    CommandeFournisseurModel, LigneCommandeModel,
)


class SqlAlchemyCommandeRepository(CommandeRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_by_id(self, entity_id: uuid.UUID) -> CommandeFournisseur | None:
        m = self._s.get(CommandeFournisseurModel, str(entity_id))
        return self._to_domain(m) if m else None

    def find_all(self) -> list[CommandeFournisseur]:
        return [
            self._to_domain(m)
            for m in self._s.query(CommandeFournisseurModel)
            .order_by(CommandeFournisseurModel.date_commande.desc())
            .all()
        ]

    def find_by_statut(self, statut: StatutCommande) -> list[CommandeFournisseur]:
        rows = (
            self._s.query(CommandeFournisseurModel)
            .filter(CommandeFournisseurModel.statut == statut.value)
            .order_by(CommandeFournisseurModel.date_commande.desc())
            .all()
        )
        return [self._to_domain(m) for m in rows]

    def find_by_fournisseur(self, fournisseur_id: uuid.UUID) -> list[CommandeFournisseur]:
        rows = (
            self._s.query(CommandeFournisseurModel)
            .filter(CommandeFournisseurModel.fournisseur_id == str(fournisseur_id))
            .order_by(CommandeFournisseurModel.date_commande.desc())
            .all()
        )
        return [self._to_domain(m) for m in rows]

    def save(self, c: CommandeFournisseur) -> None:
        m = self._s.get(CommandeFournisseurModel, str(c.id))
        if m:
            m.statut = c.statut.value
            m.date_livraison_prevue = c.date_livraison_prevue
            m.notes = c.notes
            # sync lines
            existing = {l.id: l for l in m.lignes}
            domain_ids = {str(l.id) for l in c.lignes}
            # remove deleted lines
            for lid, lm in list(existing.items()):
                if lid not in domain_ids:
                    self._s.delete(lm)
            # upsert lines
            for ligne in c.lignes:
                lm = existing.get(str(ligne.id))
                if lm:
                    lm.quantite_recue = ligne.quantite_recue
                    lm.prix_unitaire = ligne.prix_unitaire
                else:
                    self._s.add(LigneCommandeModel(
                        id=str(ligne.id),
                        commande_id=str(c.id),
                        piece_id=str(ligne.piece_id),
                        designation=ligne.designation,
                        quantite_commandee=ligne.quantite_commandee,
                        quantite_recue=ligne.quantite_recue,
                        prix_unitaire=ligne.prix_unitaire,
                    ))
        else:
            new_m = CommandeFournisseurModel(
                id=str(c.id),
                fournisseur_id=str(c.fournisseur_id),
                statut=c.statut.value,
                date_commande=c.date_commande,
                date_livraison_prevue=c.date_livraison_prevue,
                notes=c.notes,
            )
            self._s.add(new_m)
            self._s.flush()
            for ligne in c.lignes:
                self._s.add(LigneCommandeModel(
                    id=str(ligne.id),
                    commande_id=str(c.id),
                    piece_id=str(ligne.piece_id),
                    designation=ligne.designation,
                    quantite_commandee=ligne.quantite_commandee,
                    quantite_recue=ligne.quantite_recue,
                    prix_unitaire=ligne.prix_unitaire,
                ))

    def delete(self, entity_id: uuid.UUID) -> None:
        m = self._s.get(CommandeFournisseurModel, str(entity_id))
        if m:
            self._s.delete(m)

    @staticmethod
    def _to_domain(m: CommandeFournisseurModel) -> CommandeFournisseur:
        c = CommandeFournisseur(id=uuid.UUID(m.id))
        c.fournisseur_id = uuid.UUID(m.fournisseur_id)
        c.statut = StatutCommande(m.statut)
        c.date_commande = m.date_commande if isinstance(m.date_commande, datetime) else datetime.now()
        c.date_livraison_prevue = m.date_livraison_prevue
        c.notes = m.notes or ""
        c.lignes = [
            _ligne_to_domain(l)
            for l in (m.lignes or [])
        ]
        return c


def _ligne_to_domain(m: LigneCommandeModel) -> LigneCommande:
    l = LigneCommande(id=uuid.UUID(m.id))
    l.piece_id = uuid.UUID(m.piece_id)
    l.designation = m.designation or ""
    l.quantite_commandee = m.quantite_commandee
    l.quantite_recue = m.quantite_recue
    l.prix_unitaire = float(m.prix_unitaire or 0)
    return l
