from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from garage_app.infrastructure.db.base import Base


class ChargeGarageModel(Base):
    __tablename__ = "charges_garage"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    categorie: Mapped[str] = mapped_column(String(30), nullable=False, default="autre")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    montant: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    date_charge: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    date_echeance: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    periodicite: Mapped[str] = mapped_column(String(20), nullable=False, default="unique")
    statut: Mapped[str] = mapped_column(String(20), nullable=False, default="saisie")
    mode_paiement: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    reference_document: Mapped[str] = mapped_column(String(200), nullable=False, default="")
