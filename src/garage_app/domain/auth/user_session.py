from __future__ import annotations

import uuid
from dataclasses import dataclass

from garage_app.domain.auth.permission import Permission


@dataclass(frozen=True)
class UserSession:
    user_id: uuid.UUID
    username: str
    full_name: str
    role: str
    permissions: frozenset[Permission]

    def can(self, permission: Permission) -> bool:
        return permission in self.permissions

    def require(self, permission: Permission) -> None:
        from garage_app.domain.shared.exceptions import PermissionDeniedError
        if not self.can(permission):
            raise PermissionDeniedError(
                f"Permission refusée: '{permission}' requise, rôle actuel: '{self.role}'."
            )
