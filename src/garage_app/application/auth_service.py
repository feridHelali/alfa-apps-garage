from __future__ import annotations

import bcrypt

from garage_app.domain.auth.permission import ROLE_PERMISSIONS
from garage_app.domain.auth.repositories import UserRepository
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.shared.exceptions import PermissionDeniedError
from garage_app.infrastructure.db.session import SessionFactory


class AuthError(Exception):
    pass


class AuthService:
    def __init__(self, session_factory: SessionFactory, user_repo: UserRepository) -> None:
        self._sf = session_factory
        self._repo = user_repo
        self._current_session: UserSession | None = None

    @property
    def current_session(self) -> UserSession | None:
        return self._current_session

    def login(self, username: str, password: str) -> UserSession:
        with self._sf.get_session():
            user = self._repo.get_by_username(username)
        if not user or not user.is_active:
            raise AuthError("Identifiants invalides ou compte désactivé.")
        if not bcrypt.checkpw(password.encode(), user.password_hash):
            raise AuthError("Mot de passe incorrect.")
        permissions = ROLE_PERMISSIONS.get(user.role, frozenset())
        session = UserSession(
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            permissions=permissions,
        )
        self._current_session = session
        return session

    def logout(self) -> None:
        self._current_session = None

    def hash_password(self, password: str) -> bytes:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
