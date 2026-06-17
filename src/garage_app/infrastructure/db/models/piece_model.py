from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from garage_app.infrastructure.db.base import Base


class FournisseurModel(Base):
    __tablename__ = "fournisseurs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    raison_sociale: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    contact_nom: Mapped[str] = mapped_column(String(100), default="")
    telephone: Mapped[str] = mapped_column(String(30), default="")
    email: Mapped[str] = mapped_column(String(150), default="")
    adresse: Mapped[str] = mapped_column(Text, default="")
    delai_livraison_jours: Mapped[int] = mapped_column(Integer, default=7)
    est_actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    pieces: Mapped[list[PieceModel]] = relationship("PieceModel", back_populates="fournisseur")
    commandes: Mapped[list[CommandeFournisseurModel]] = relationship(
        "CommandeFournisseurModel", back_populates="fournisseur"
    )


class PieceModel(Base):
    __tablename__ = "pieces"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reference_constructeur: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    designation: Mapped[str] = mapped_column(String(200), nullable=False)
    categorie: Mapped[str] = mapped_column(String(50), default="")
    emplacement: Mapped[str] = mapped_column(String(50), default="")
    prix_achat: Mapped[float] = mapped_column(Numeric(10, 3), default=0)
    prix_vente: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False, default=0)
    quantite_stock: Mapped[int] = mapped_column(Integer, default=0)
    seuil_alerte: Mapped[int] = mapped_column(Integer, default=5)
    fournisseur_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("fournisseurs.id"), nullable=True
    )
    fournisseur: Mapped[FournisseurModel | None] = relationship(
        "FournisseurModel", back_populates="pieces"
    )
    mouvements: Mapped[list[MouvementStockModel]] = relationship(
        "MouvementStockModel", back_populates="piece", cascade="all, delete-orphan"
    )


class CommandeFournisseurModel(Base):
    __tablename__ = "commandes_fournisseur"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fournisseur_id: Mapped[str] = mapped_column(String(36), ForeignKey("fournisseurs.id"), nullable=False)
    statut: Mapped[str] = mapped_column(String(30), nullable=False, default="brouillon")
    date_commande: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    date_livraison_prevue: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")

    fournisseur: Mapped[FournisseurModel] = relationship("FournisseurModel", back_populates="commandes")
    lignes: Mapped[list[LigneCommandeModel]] = relationship(
        "LigneCommandeModel", back_populates="commande", cascade="all, delete-orphan"
    )


class LigneCommandeModel(Base):
    __tablename__ = "lignes_commande"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    commande_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("commandes_fournisseur.id"), nullable=False
    )
    piece_id: Mapped[str] = mapped_column(String(36), ForeignKey("pieces.id"), nullable=False)
    designation: Mapped[str] = mapped_column(String(200), default="")
    quantite_commandee: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantite_recue: Mapped[int] = mapped_column(Integer, default=0)
    prix_unitaire: Mapped[float] = mapped_column(Numeric(10, 3), default=0)

    commande: Mapped[CommandeFournisseurModel] = relationship(
        "CommandeFournisseurModel", back_populates="lignes"
    )


class MouvementStockModel(Base):
    __tablename__ = "mouvements_stock"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    piece_id: Mapped[str] = mapped_column(String(36), ForeignKey("pieces.id"), nullable=False)
    type_mouvement: Mapped[str] = mapped_column(String(20), nullable=False)  # entree|sortie|ajustement
    quantite: Mapped[int] = mapped_column(Integer, nullable=False)
    quantite_avant: Mapped[int] = mapped_column(Integer, default=0)
    reference: Mapped[str] = mapped_column(String(100), default="")
    horodatage: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    utilisateur_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    utilisateur_nom: Mapped[str] = mapped_column(String(100), default="")

    piece: Mapped[PieceModel] = relationship("PieceModel", back_populates="mouvements")
