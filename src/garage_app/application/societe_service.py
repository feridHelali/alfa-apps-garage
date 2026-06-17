from __future__ import annotations

from garage_app.application.decorators import require_permission
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.societe.societe import Societe
from garage_app.domain.societe.repositories import SocieteRepository
from garage_app.infrastructure.db.session import SessionFactory


class SocieteService:
    def __init__(self, sf: SessionFactory, repo: SocieteRepository) -> None:
        self._sf = sf
        self._repo = repo

    def get(self) -> Societe | None:
        with self._sf.get_session():
            return self._repo.get_singleton()

    @require_permission(Permission.MANAGE_SOCIETE)
    def update(self, session: UserSession, societe: Societe) -> None:
        with self._sf.get_session():
            self._repo.save(societe)
