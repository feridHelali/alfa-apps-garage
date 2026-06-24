"""ORM models for Sprint 07 — Devis lines, FactureProforma, LigneProforma.

The parent `devis` table already exists (DevisModel in facture_model.py).
New columns are added via _COLUMN_MIGRATIONS in initializer.py.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from garage_app.infrastructure.db.base import Base


class LigneDevisModel(Base):
    __tablename__ = "lignes_devis"
    id: Mapped[str] = mapped_column(String(36), primary_key=True,
                                    default=lambda: str(uuid.uuid4()))
    devis_id: Mapped[str] = mapped_column(String(36), ForeignKey("devis.id", ondelete="CASCADE"),
                                           nullable=False)
    type_ligne: Mapped[str] = mapped_column(String(20), nullable=False, default="service")
    designation: Mapped[str] = mapped_column(String(255), nullable=False)
    quantite: Mapped[str] = mapped_column(String(20), nullable=False, default="1")
    prix_unitaire_ht: Mapped[str] = mapped_column(String(20), nullable=False, default="0")
    taux_tva: Mapped[str] = mapped_column(String(10), nullable=False, default="0.19")
    remise_pct: Mapped[str] = mapped_column(String(10), nullable=False, default="0")
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    piece_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class FactureProformaModel(Base):
    __tablename__ = "factures_proforma"
    id: Mapped[str] = mapped_column(String(36), primary_key=True,
                                    default=lambda: str(uuid.uuid4()))
    numero: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    client_id: Mapped[str] = mapped_column(String(36), nullable=False)
    devis_id: Mapped[str | None] = mapped_column(String(36),
                                                   ForeignKey("devis.id"), nullable=True)
    statut: Mapped[str] = mapped_column(String(20), nullable=False, default="emise")
    date_emission: Mapped[str] = mapped_column(String(10), nullable=False)
    acompte_recu: Mapped[str] = mapped_column(String(20), nullable=False, default="0")
    facture_finale_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")

    lignes: Mapped[list[LigneProformaModel]] = relationship(
        "LigneProformaModel",
        back_populates="proforma",
        cascade="all, delete-orphan",
        order_by="LigneProformaModel.ordre",
    )


class LigneProformaModel(Base):
    __tablename__ = "lignes_proforma"
    id: Mapped[str] = mapped_column(String(36), primary_key=True,
                                    default=lambda: str(uuid.uuid4()))
    proforma_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("factures_proforma.id", ondelete="CASCADE"), nullable=False
    )
    type_ligne: Mapped[str] = mapped_column(String(20), nullable=False, default="service")
    designation: Mapped[str] = mapped_column(String(255), nullable=False)
    quantite: Mapped[str] = mapped_column(String(20), nullable=False, default="1")
    prix_unitaire_ht: Mapped[str] = mapped_column(String(20), nullable=False, default="0")
    taux_tva: Mapped[str] = mapped_column(String(10), nullable=False, default="0.19")
    remise_pct: Mapped[str] = mapped_column(String(10), nullable=False, default="0")
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    proforma: Mapped[FactureProformaModel] = relationship(
        "FactureProformaModel", back_populates="lignes"
    )
