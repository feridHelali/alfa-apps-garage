from __future__ import annotations

from datetime import datetime
from typing import Sequence

from garage_app.domain.audit.audit_entry import AuditEntry, LogCategory, LogLevel
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.auth.permission import Permission
from garage_app.infrastructure.repositories.audit_log_repository import AuditLogRepository


class AuditService:
    """
    Central façade for writing and reading audit/forensic log entries.
    Write methods are call-anywhere (no permission guard — they are internal).
    Read methods are restricted to superadmin.
    """

    def __init__(self, repo: AuditLogRepository) -> None:
        self._repo = repo

    # ─── Write helpers ───────────────────────────────────────────────────────

    def log_auth(self, message: str, *, username: str, success: bool) -> None:
        level = LogLevel.INFO if success else LogLevel.WARNING
        self._repo.save(AuditEntry(
            level=level, category=LogCategory.AUTH,
            message=message, username=username,
        ))

    def log_business(
        self,
        message: str,
        *,
        session: UserSession,
        entity_type: str,
        entity_id: str,
    ) -> None:
        self._repo.save(AuditEntry.info(
            LogCategory.BUSINESS, message,
            username=session.username,
            user_id=session.user_id,
            entity_type=entity_type,
            entity_id=entity_id,
        ))

    def log_system(self, message: str, level: LogLevel = LogLevel.INFO) -> None:
        self._repo.save(AuditEntry(
            level=level, category=LogCategory.SYSTEM, message=message,
        ))

    def log_db(self, message: str, *, username: str) -> None:
        self._repo.save(AuditEntry.info(
            LogCategory.DB, message, username=username,
        ))

    def log_error(self, message: str, *, extra: dict | None = None) -> None:
        self._repo.save(AuditEntry(
            level=LogLevel.ERROR, category=LogCategory.SYSTEM,
            message=message, extra=extra,
        ))

    # ─── Read (superadmin only) ───────────────────────────────────────────────

    def find_recent(
        self,
        session: UserSession,
        *,
        limit: int = 500,
        category: LogCategory | None = None,
        level: LogLevel | None = None,
        username: str | None = None,
        entity_type: str | None = None,
        since: datetime | None = None,
    ) -> Sequence[AuditEntry]:
        session.require(Permission.MANAGE_USERS)   # superadmin guard
        return self._repo.find_recent(
            limit=limit, category=category, level=level,
            username=username, entity_type=entity_type, since=since,
        )
