from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import select

from garage_app.domain.audit.audit_entry import AuditEntry, LogCategory, LogLevel
from garage_app.infrastructure.db.models.audit_log_model import AuditLogModel
from garage_app.infrastructure.db.session import SessionFactory


class AuditLogRepository:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._sf = session_factory

    def save(self, entry: AuditEntry) -> None:
        with self._sf.get_session() as s:
            s.add(AuditLogModel(
                id=str(entry.id),
                occurred_at=entry.occurred_at,
                level=str(entry.level),
                category=str(entry.category),
                message=entry.message,
                username=entry.username,
                user_id=str(entry.user_id) if entry.user_id else None,
                entity_type=entry.entity_type,
                entity_id=entry.entity_id,
                extra_json=json.dumps(entry.extra, default=str) if entry.extra else None,
            ))

    def find_recent(
        self,
        limit: int = 500,
        *,
        category: LogCategory | None = None,
        level: LogLevel | None = None,
        username: str | None = None,
        entity_type: str | None = None,
        since: datetime | None = None,
    ) -> Sequence[AuditEntry]:
        with self._sf.get_session() as s:
            q = select(AuditLogModel).order_by(AuditLogModel.occurred_at.desc())
            if category:
                q = q.where(AuditLogModel.category == str(category))
            if level:
                q = q.where(AuditLogModel.level == str(level))
            if username:
                q = q.where(AuditLogModel.username.ilike(f"%{username}%"))
            if entity_type:
                q = q.where(AuditLogModel.entity_type == entity_type)
            if since:
                q = q.where(AuditLogModel.occurred_at >= since)
            q = q.limit(limit)
            rows = s.scalars(q).all()
            return [_to_entry(r) for r in rows]


def _to_entry(m: AuditLogModel) -> AuditEntry:
    extra = json.loads(m.extra_json) if m.extra_json else None
    return AuditEntry(
        id=uuid.UUID(m.id),
        occurred_at=m.occurred_at,
        level=LogLevel(m.level),
        category=LogCategory(m.category),
        message=m.message,
        username=m.username,
        user_id=uuid.UUID(m.user_id) if m.user_id else None,
        entity_type=m.entity_type,
        entity_id=m.entity_id,
        extra=extra,
    )
