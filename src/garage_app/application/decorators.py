from __future__ import annotations

import functools
from typing import Callable

from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.shared.exceptions import PermissionDeniedError


def require_permission(permission: Permission) -> Callable:
    """
    Decorator for application-service methods.
    First positional arg after `self` must be a `UserSession`.
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(self, session: UserSession, *args, **kwargs):  # type: ignore[no-untyped-def]
            session.require(permission)
            return fn(self, session, *args, **kwargs)
        return wrapper
    return decorator
