from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from garage_app.infrastructure.db.base import Base


class ClientModel(Base):
    __tablename__ = "clients"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    prenom: Mapped[str] = mapped_column(String(100), nullable=False)
    telephone: Mapped[str] = mapped_column(String(20), default="")
    email: Mapped[str] = mapped_column(String(100), default="")
    adresse: Mapped[str] = mapped_column(Text, default="")
    est_flotte: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    vehicules: Mapped[list[VehiculeModel]] = relationship(
        "VehiculeModel", back_populates="client", lazy="select"
    )


class VehiculeModel(Base):
    __tablename__ = "vehicules"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id: Mapped[str] = mapped_column(String(36), ForeignKey("clients.id"), nullable=False)
    immatriculation: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    vin: Mapped[str] = mapped_column(String(17), default="")
    marque: Mapped[str] = mapped_column(String(50), nullable=False)
    modele: Mapped[str] = mapped_column(String(50), nullable=False)
    annee: Mapped[int] = mapped_column(Integer, default=0)
    couleur: Mapped[str] = mapped_column(String(30), default="")
    client: Mapped[ClientModel] = relationship("ClientModel", back_populates="vehicules")
