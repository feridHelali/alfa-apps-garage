from __future__ import annotations

import bcrypt

from garage_app.application.decorators import require_permission
from garage_app.domain.auth.permission import Permission, ROLE_PERMISSIONS
from garage_app.domain.auth.repositories import UserRepository
from garage_app.domain.auth.user import User
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

    @require_permission(Permission.MANAGE_USERS)
    def list_users(self, session: UserSession) -> list[User]:
        return self._repo.find_all()

    @require_permission(Permission.MANAGE_USERS)
    def create_user(
        self,
        session: UserSession,
        username: str,
        full_name: str,
        role: str,
        password: str,
    ) -> User:
        existing = self._repo.get_by_username(username)
        if existing:
            raise ValueError(f"L'identifiant '{username}' est déjà utilisé.")
        if role not in ROLE_PERMISSIONS:
            raise ValueError(f"Rôle inconnu : {role}")
        user = User(username=username, full_name=full_name, role=role)
        user.password_hash = self.hash_password(password)
        self._repo.save(user)
        return user

    @require_permission(Permission.MANAGE_USERS)
    def update_user(
        self,
        session: UserSession,
        user_id,
        full_name: str,
        role: str,
    ) -> User:
        user = self._repo.get_by_id(user_id)
        if not user:
            raise ValueError("Utilisateur introuvable.")
        if role not in ROLE_PERMISSIONS:
            raise ValueError(f"Rôle inconnu : {role}")
        user.full_name = full_name
        user.role = role
        self._repo.save(user)
        return user

    @require_permission(Permission.MANAGE_USERS)
    def change_password(
        self,
        session: UserSession,
        user_id,
        new_password: str,
    ) -> None:
        user = self._repo.get_by_id(user_id)
        if not user:
            raise ValueError("Utilisateur introuvable.")
        user.password_hash = self.hash_password(new_password)
        self._repo.save(user)

    @require_permission(Permission.MANAGE_USERS)
    def deactivate_user(self, session: UserSession, user_id) -> None:
        if str(user_id) == str(session.user_id):
            raise ValueError("Impossible de désactiver votre propre compte.")
        user = self._repo.get_by_id(user_id)
        if not user:
            raise ValueError("Utilisateur introuvable.")
        user.is_active = False
        self._repo.save(user)

    @require_permission(Permission.MANAGE_USERS)
    def reactivate_user(self, session: UserSession, user_id) -> None:
        user = self._repo.get_by_id(user_id)
        if not user:
            raise ValueError("Utilisateur introuvable.")
        user.is_active = True
        self._repo.save(user)
