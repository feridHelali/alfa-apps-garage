from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from garage_app.infrastructure.db.base import Base


class AuditLogModel(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(primary_key=True)
    occurred_at: Mapped[datetime] = mapped_column(index=True)
    level: Mapped[str]
    category: Mapped[str] = mapped_column(index=True)
    message: Mapped[str]
    username: Mapped[Optional[str]] = mapped_column(nullable=True, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(nullable=True)
    entity_type: Mapped[Optional[str]] = mapped_column(nullable=True, index=True)
    entity_id: Mapped[Optional[str]] = mapped_column(nullable=True)
    extra_json: Mapped[Optional[str]] = mapped_column(nullable=True)
