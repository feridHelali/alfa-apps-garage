from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from garage_app.infrastructure.db.base import Base


class LigneAchatModel(Base):
    __tablename__ = "lignes_achat"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    facture_achat_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("factures_achat.id", ondelete="CASCADE"), nullable=False
    )
    piece_id: Mapped[str] = mapped_column(String(36), nullable=False)
    designation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    quantite: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    prix_unitaire: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0)


class FactureAchatModel(Base):
    __tablename__ = "factures_achat"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    fournisseur_id: Mapped[str] = mapped_column(String(36), nullable=False)
    numero_fournisseur: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    notre_numero: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    date_facture: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    date_echeance: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    statut: Mapped[str] = mapped_column(String(20), nullable=False, default="saisie")
    commande_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    taux_tva: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=19.0)
    montant_ht: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    montant_ttc: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0)

    lignes: Mapped[List[LigneAchatModel]] = relationship(
        "LigneAchatModel",
        cascade="all, delete-orphan",
        lazy="selectin",
        foreign_keys=[LigneAchatModel.facture_achat_id],
    )
