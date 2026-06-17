from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from garage_app.domain.stock.fournisseur import Fournisseur
from garage_app.domain.stock.repositories import FournisseurRepository
from garage_app.infrastructure.db.models.piece_model import FournisseurModel


class SqlAlchemyFournisseurRepository(FournisseurRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_by_id(self, entity_id: uuid.UUID) -> Fournisseur | None:
        m = self._s.get(FournisseurModel, str(entity_id))
        return self._to_domain(m) if m else None

    def find_all(self) -> list[Fournisseur]:
        return [self._to_domain(m) for m in self._s.query(FournisseurModel).all()]

    def find_actifs(self) -> list[Fournisseur]:
        rows = self._s.query(FournisseurModel).filter(FournisseurModel.est_actif.is_(True)).all()
        return [self._to_domain(m) for m in rows]

    def find_by_raison_sociale(self, query: str) -> list[Fournisseur]:
        q = f"%{query}%"
        rows = (
            self._s.query(FournisseurModel)
            .filter(FournisseurModel.raison_sociale.ilike(q))
            .all()
        )
        return [self._to_domain(m) for m in rows]

    def save(self, f: Fournisseur) -> None:
        m = self._s.get(FournisseurModel, str(f.id))
        if m:
            m.raison_sociale = f.raison_sociale
            m.contact_nom = f.contact_nom
            m.telephone = f.telephone
            m.email = f.email
            m.adresse = f.adresse
            m.delai_livraison_jours = f.delai_livraison_jours
            m.est_actif = f.est_actif
        else:
            self._s.add(FournisseurModel(
                id=str(f.id),
                raison_sociale=f.raison_sociale,
                contact_nom=f.contact_nom,
                telephone=f.telephone,
                email=f.email,
                adresse=f.adresse,
                delai_livraison_jours=f.delai_livraison_jours,
                est_actif=f.est_actif,
            ))

    def delete(self, entity_id: uuid.UUID) -> None:
        m = self._s.get(FournisseurModel, str(entity_id))
        if m:
            self._s.delete(m)

    @staticmethod
    def _to_domain(m: FournisseurModel) -> Fournisseur:
        f = Fournisseur(id=uuid.UUID(m.id))
        f.raison_sociale = m.raison_sociale or ""
        f.contact_nom = m.contact_nom or ""
        f.telephone = m.telephone or ""
        f.email = m.email or ""
        f.adresse = m.adresse or ""
        f.delai_livraison_jours = m.delai_livraison_jours or 7
        f.est_actif = bool(m.est_actif)
        return f
