from __future__ import annotations

import uuid

from garage_app.domain.auth.user import User
from garage_app.domain.auth.repositories import UserRepository
from garage_app.infrastructure.db.models.user_model import UserModel
from garage_app.infrastructure.db.session import SessionFactory


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, sf: SessionFactory) -> None:
        self._sf = sf

    def get_by_id(self, entity_id: uuid.UUID) -> User | None:
        with self._sf.get_session() as s:
            m = s.get(UserModel, str(entity_id))
            return self._to_domain(m) if m else None

    def get_by_username(self, username: str) -> User | None:
        with self._sf.get_session() as s:
            m = s.query(UserModel).filter_by(username=username).first()
            return self._to_domain(m) if m else None

    def find_active(self) -> list[User]:
        with self._sf.get_session() as s:
            return [self._to_domain(m) for m in s.query(UserModel).filter_by(is_active=True).all()]

    def find_all(self) -> list[User]:
        with self._sf.get_session() as s:
            return [self._to_domain(m) for m in s.query(UserModel).all()]

    def save(self, user: User) -> None:
        with self._sf.get_session() as s:
            m = s.get(UserModel, str(user.id))
            if m:
                m.username = user.username
                m.password_hash = user.password_hash
                m.full_name = user.full_name
                m.role = user.role
                m.is_active = user.is_active
            else:
                s.add(UserModel(
                    id=str(user.id),
                    username=user.username,
                    password_hash=user.password_hash,
                    full_name=user.full_name,
                    role=user.role,
                    is_active=user.is_active,
                ))

    def delete(self, entity_id: uuid.UUID) -> None:
        with self._sf.get_session() as s:
            m = s.get(UserModel, str(entity_id))
            if m:
                s.delete(m)

    @staticmethod
    def _to_domain(m: UserModel) -> User:
        u = User(id=uuid.UUID(m.id))
        u.username = m.username
        u.password_hash = m.password_hash
        u.full_name = m.full_name
        u.role = m.role
        u.is_active = m.is_active
        return u
