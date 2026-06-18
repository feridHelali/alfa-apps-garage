from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from garage_app.infrastructure.db.base import Base


class RendezVousModel(Base):
    __tablename__ = "rendez_vous"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id: Mapped[str] = mapped_column(String(36), ForeignKey("clients.id"), nullable=False)
    vehicule_id: Mapped[str] = mapped_column(String(36), ForeignKey("vehicules.id"), nullable=False)
    date_heure: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    motif: Mapped[str] = mapped_column(Text, default="")
    statut: Mapped[str] = mapped_column(String(20), default="planifie")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
