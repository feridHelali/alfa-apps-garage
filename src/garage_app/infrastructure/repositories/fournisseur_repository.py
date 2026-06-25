from __future__ import annotations

import uuid

from garage_app.domain.stock.fournisseur import Fournisseur
from garage_app.domain.stock.repositories import FournisseurRepository
from garage_app.infrastructure.db.models.piece_model import FournisseurModel
from garage_app.infrastructure.db.session import SessionFactory


class SqlAlchemyFournisseurRepository(FournisseurRepository):
    def __init__(self, sf: SessionFactory) -> None:
        self._sf = sf

    def get_by_id(self, entity_id: uuid.UUID) -> Fournisseur | None:
        with self._sf.get_session() as s:
            m = s.get(FournisseurModel, str(entity_id))
            return self._to_domain(m) if m else None

    def find_all(self) -> list[Fournisseur]:
        with self._sf.get_session() as s:
            return [self._to_domain(m) for m in s.query(FournisseurModel).all()]

    def find_actifs(self) -> list[Fournisseur]:
        with self._sf.get_session() as s:
            rows = s.query(FournisseurModel).filter(FournisseurModel.est_actif.is_(True)).all()
            return [self._to_domain(m) for m in rows]

    def find_by_raison_sociale(self, query: str) -> list[Fournisseur]:
        q = f"%{query}%"
        with self._sf.get_session() as s:
            rows = s.query(FournisseurModel).filter(FournisseurModel.raison_sociale.ilike(q)).all()
            return [self._to_domain(m) for m in rows]

    def save(self, f: Fournisseur) -> None:
        with self._sf.get_session() as s:
            m = s.get(FournisseurModel, str(f.id))
            if m:
                m.raison_sociale = f.raison_sociale
                m.contact_nom = f.contact_nom
                m.telephone = f.telephone
                m.email = f.email
                m.adresse = f.adresse
                m.delai_livraison_jours = f.delai_livraison_jours
                m.est_actif = f.est_actif
            else:
                s.add(FournisseurModel(
                    id=str(f.id),
                    # Legacy columns — kept in sync so NOT NULL constraint is satisfied
                    nom=f.raison_sociale,
                    contact=f.contact_nom,
                    telephone=f.telephone,
                    email=f.email,
                    delai_livraison=f.delai_livraison_jours,
                    # Current columns
                    raison_sociale=f.raison_sociale,
                    contact_nom=f.contact_nom,
                    adresse=f.adresse,
                    delai_livraison_jours=f.delai_livraison_jours,
                    est_actif=f.est_actif,
                ))

    def delete(self, entity_id: uuid.UUID) -> None:
        with self._sf.get_session() as s:
            m = s.get(FournisseurModel, str(entity_id))
            if m:
                s.delete(m)

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
