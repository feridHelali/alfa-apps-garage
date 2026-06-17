from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(StrEnum):
    AUTH = "AUTH"               # login / logout / permission denied
    BUSINESS = "BUSINESS"       # domain state transitions
    SYSTEM = "SYSTEM"           # startup / shutdown / seed
    DB = "DB"                   # snapshot / vacuum / restore
    CONFIG = "CONFIG"           # settings / societe changes


@dataclass
class AuditEntry:
    level: LogLevel
    category: LogCategory
    message: str
    user_id: uuid.UUID | None = None
    username: str | None = None
    entity_type: str | None = None      # "DossierReparation", "Facture", …
    entity_id: str | None = None
    extra: dict | None = None           # arbitrary key/value context
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def info(
        cls,
        category: LogCategory,
        message: str,
        *,
        username: str | None = None,
        user_id: uuid.UUID | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        extra: dict | None = None,
    ) -> AuditEntry:
        return cls(
            level=LogLevel.INFO, category=category, message=message,
            username=username, user_id=user_id,
            entity_type=entity_type, entity_id=entity_id, extra=extra,
        )

    @classmethod
    def warning(cls, category: LogCategory, message: str, **kw) -> AuditEntry:
        return cls(level=LogLevel.WARNING, category=category, message=message, **kw)

    @classmethod
    def error(cls, category: LogCategory, message: str, **kw) -> AuditEntry:
        return cls(level=LogLevel.ERROR, category=category, message=message, **kw)
