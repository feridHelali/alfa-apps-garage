from __future__ import annotations

from abc import abstractmethod

from garage_app.domain.auth.user import User
from garage_app.domain.shared.repository import Repository


class UserRepository(Repository[User]):
    @abstractmethod
    def get_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    def find_active(self) -> list[User]: ...
