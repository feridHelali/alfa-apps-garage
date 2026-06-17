from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from garage_app.infrastructure.db.base import Base


class DossierReparationModel(Base):
    __tablename__ = "dossiers_reparation"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vehicule_id: Mapped[str] = mapped_column(String(36), ForeignKey("vehicules.id"), nullable=False)
    client_id: Mapped[str] = mapped_column(String(36), ForeignKey("clients.id"), nullable=False)
    kilometrage_entree: Mapped[int] = mapped_column(Integer, nullable=False)
    statut: Mapped[str] = mapped_column(String(30), nullable=False, default="cree")
    devis_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    facture_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    lignes_diagnostic: Mapped[list[LigneDiagnosticModel]] = relationship(
        "LigneDiagnosticModel", back_populates="dossier", cascade="all, delete-orphan"
    )
    operations: Mapped[list[OperationMecaniqueModel]] = relationship(
        "OperationMecaniqueModel", back_populates="dossier", cascade="all, delete-orphan"
    )
    pieces: Mapped[list[PieceRequiseModel]] = relationship(
        "PieceRequiseModel", back_populates="dossier", cascade="all, delete-orphan"
    )


class LigneDiagnosticModel(Base):
    __tablename__ = "lignes_diagnostic"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dossier_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("dossiers_reparation.id"), nullable=False
    )
    code_defaut: Mapped[str] = mapped_column(String(20), default="")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    gravite: Mapped[str] = mapped_column(String(20), default="bloquant")
    dossier: Mapped[DossierReparationModel] = relationship(
        "DossierReparationModel", back_populates="lignes_diagnostic"
    )


class OperationMecaniqueModel(Base):
    __tablename__ = "operations_mecaniques"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dossier_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("dossiers_reparation.id"), nullable=False
    )
    technicien_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    code_main_oeuvre: Mapped[str] = mapped_column(String(50), default="")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    temps_estime: Mapped[float] = mapped_column(Numeric(6, 2), default=0)
    temps_passe: Mapped[float] = mapped_column(Numeric(6, 2), default=0)
    taux_horaire: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    statut: Mapped[str] = mapped_column(String(20), default="a_faire")
    dossier: Mapped[DossierReparationModel] = relationship(
        "DossierReparationModel", back_populates="operations"
    )


class PieceRequiseModel(Base):
    __tablename__ = "pieces_requises"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dossier_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("dossiers_reparation.id"), nullable=False
    )
    piece_id: Mapped[str] = mapped_column(String(36), ForeignKey("pieces.id"), nullable=False)
    reference: Mapped[str] = mapped_column(String(50), default="")
    designation: Mapped[str] = mapped_column(String(200), default="")
    quantite: Mapped[int] = mapped_column(Integer, default=1)
    prix_unitaire: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    statut_dispo: Mapped[str] = mapped_column(String(20), default="en_stock")
    dossier: Mapped[DossierReparationModel] = relationship(
        "DossierReparationModel", back_populates="pieces"
    )
