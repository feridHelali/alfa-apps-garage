from __future__ import annotations

import uuid

from garage_app.application.decorators import require_permission
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.stock.fournisseur import Fournisseur
from garage_app.domain.stock.repositories import FournisseurRepository
from garage_app.infrastructure.db.session import SessionFactory


class FournisseurService:
    def __init__(self, sf: SessionFactory, repo: FournisseurRepository) -> None:
        self._sf = sf
        self._repo = repo

    @require_permission(Permission.VIEW_STOCK)
    def list_fournisseurs(self, session: UserSession, actifs_seulement: bool = False) -> list[Fournisseur]:
        with self._sf.get_session():
            if actifs_seulement:
                return self._repo.find_actifs()
            return self._repo.find_all()

    @require_permission(Permission.VIEW_STOCK)
    def get_fournisseur(self, session: UserSession, fournisseur_id: uuid.UUID) -> Fournisseur | None:
        with self._sf.get_session():
            return self._repo.get_by_id(fournisseur_id)

    @require_permission(Permission.MANAGE_STOCK)
    def create_fournisseur(self, session: UserSession, fournisseur: Fournisseur) -> Fournisseur:
        with self._sf.get_session():
            self._repo.save(fournisseur)
        return fournisseur

    @require_permission(Permission.MANAGE_STOCK)
    def update_fournisseur(self, session: UserSession, fournisseur: Fournisseur) -> Fournisseur:
        with self._sf.get_session():
            existing = self._repo.get_by_id(fournisseur.id)
            if not existing:
                raise ValueError(f"Fournisseur {fournisseur.id} introuvable.")
            self._repo.save(fournisseur)
        return fournisseur

    @require_permission(Permission.MANAGE_STOCK)
    def desactiver_fournisseur(self, session: UserSession, fournisseur_id: uuid.UUID) -> Fournisseur:
        with self._sf.get_session():
            f = self._repo.get_by_id(fournisseur_id)
            if not f:
                raise ValueError(f"Fournisseur {fournisseur_id} introuvable.")
            f.desactiver()
            self._repo.save(f)
        return f

    @require_permission(Permission.MANAGE_STOCK)
    def activer_fournisseur(self, session: UserSession, fournisseur_id: uuid.UUID) -> Fournisseur:
        with self._sf.get_session():
            f = self._repo.get_by_id(fournisseur_id)
            if not f:
                raise ValueError(f"Fournisseur {fournisseur_id} introuvable.")
            f.activer()
            self._repo.save(f)
        return f
