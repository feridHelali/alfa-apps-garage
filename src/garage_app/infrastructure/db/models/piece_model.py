from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from garage_app.infrastructure.db.base import Base


class FournisseurModel(Base):
    __tablename__ = "fournisseurs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    contact: Mapped[str] = mapped_column(String(100), default="")
    telephone: Mapped[str] = mapped_column(String(20), default="")
    email: Mapped[str] = mapped_column(String(100), default="")
    delai_livraison: Mapped[int] = mapped_column(Integer, default=3)  # jours


class PieceModel(Base):
    __tablename__ = "pieces"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reference_constructeur: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    designation: Mapped[str] = mapped_column(String(200), nullable=False)
    categorie: Mapped[str] = mapped_column(String(50), default="")
    prix_achat: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    prix_vente: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantite_stock: Mapped[int] = mapped_column(Integer, default=0)
    seuil_alerte: Mapped[int] = mapped_column(Integer, default=5)
    fournisseur_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("fournisseurs.id"), nullable=True
    )
    fournisseur: Mapped[FournisseurModel | None] = relationship("FournisseurModel")
