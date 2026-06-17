from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from garage_app.infrastructure.db.base import Base


class DevisModel(Base):
    __tablename__ = "devis"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dossier_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    numero: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    date_creation: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    statut: Mapped[str] = mapped_column(String(20), default="brouillon")
    montant_ht: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    taux_tva: Mapped[float] = mapped_column(Numeric(5, 2), default=20.0)
    montant_ttc: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    notes: Mapped[str] = mapped_column(Text, default="")


class FactureModel(Base):
    __tablename__ = "factures"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dossier_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    devis_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("devis.id"), nullable=True)
    numero: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    date_emission: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    montant_ht: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    taux_tva: Mapped[float] = mapped_column(Numeric(5, 2), default=20.0)
    montant_ttc: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    statut_paiement: Mapped[str] = mapped_column(String(20), default="en_attente")
    mode_paiement: Mapped[str] = mapped_column(String(20), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    lignes: Mapped[list[LigneFactureModel]] = relationship(
        "LigneFactureModel", back_populates="facture", cascade="all, delete-orphan"
    )


class LigneFactureModel(Base):
    __tablename__ = "lignes_facture"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    facture_id: Mapped[str] = mapped_column(String(36), ForeignKey("factures.id"), nullable=False)
    designation: Mapped[str] = mapped_column(String(200), nullable=False)
    quantite: Mapped[int] = mapped_column(Integer, default=1)
    prix_unitaire: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    facture: Mapped[FactureModel] = relationship("FactureModel", back_populates="lignes")


class PaiementModel(Base):
    __tablename__ = "paiements"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    facture_id: Mapped[str] = mapped_column(String(36), ForeignKey("factures.id"), nullable=False)
    montant: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False)
    date_paiement: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
