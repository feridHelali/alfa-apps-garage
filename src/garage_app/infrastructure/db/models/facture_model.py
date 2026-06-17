from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
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
    montant_ht: Mapped[float] = mapped_column(Numeric(12, 3), default=0)
    taux_tva: Mapped[float] = mapped_column(Numeric(5, 2), default=19.0)
    montant_ttc: Mapped[float] = mapped_column(Numeric(12, 3), default=0)
    notes: Mapped[str] = mapped_column(Text, default="")


class FactureModel(Base):
    __tablename__ = "factures"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dossier_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    client_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    devis_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("devis.id"), nullable=True)
    numero: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    date_emission: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    montant_ht: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    taux_tva: Mapped[float] = mapped_column(Numeric(5, 2), default=19.0)
    montant_ttc: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    solde_restant: Mapped[float] = mapped_column(Numeric(12, 3), default=0)
    statut: Mapped[str] = mapped_column(String(30), default="brouillon")
    est_flotte: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")

    lignes: Mapped[list[LigneFactureModel]] = relationship(
        "LigneFactureModel", back_populates="facture", cascade="all, delete-orphan"
    )
    paiements: Mapped[list[PaiementModel]] = relationship(
        "PaiementModel", back_populates="facture", cascade="all, delete-orphan"
    )


class LigneFactureModel(Base):
    __tablename__ = "lignes_facture"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    facture_id: Mapped[str] = mapped_column(String(36), ForeignKey("factures.id"), nullable=False)
    designation: Mapped[str] = mapped_column(String(200), nullable=False)
    quantite: Mapped[int] = mapped_column(Integer, default=1)
    prix_unitaire: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    facture: Mapped[FactureModel] = relationship("FactureModel", back_populates="lignes")


class PaiementModel(Base):
    __tablename__ = "paiements"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    facture_id: Mapped[str] = mapped_column(String(36), ForeignKey("factures.id"), nullable=False)
    montant: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False)
    reference: Mapped[str] = mapped_column(String(100), default="")
    date_paiement: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    facture: Mapped[FactureModel] = relationship("FactureModel", back_populates="paiements")


class SessionCaisseModel(Base):
    __tablename__ = "sessions_caisse"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ouvert_par: Mapped[str] = mapped_column(String(36), nullable=False)
    ouvert_par_nom: Mapped[str] = mapped_column(String(100), default="")
    solde_ouverture: Mapped[float] = mapped_column(Numeric(12, 3), default=0)
    currency: Mapped[str] = mapped_column(String(10), default="TND")
    statut: Mapped[str] = mapped_column(String(10), default="ouverte")  # ouverte | fermee
    ouvert_le: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    ferme_le: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    solde_fermeture_reel: Mapped[float | None] = mapped_column(Numeric(12, 3), nullable=True)
    ecart: Mapped[float | None] = mapped_column(Numeric(12, 3), nullable=True)

    mouvements: Mapped[list[MouvementCaisseModel]] = relationship(
        "MouvementCaisseModel", back_populates="session", cascade="all, delete-orphan"
    )


class MouvementCaisseModel(Base):
    __tablename__ = "mouvements_caisse"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions_caisse.id"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(10), nullable=False)  # entree | sortie
    montant: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    motif: Mapped[str] = mapped_column(String(200), default="")
    reference: Mapped[str] = mapped_column(String(100), default="")
    horodatage: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    currency: Mapped[str] = mapped_column(String(10), default="TND")

    session: Mapped[SessionCaisseModel] = relationship("SessionCaisseModel", back_populates="mouvements")


class CreditClientModel(Base):
    __tablename__ = "credits_clients"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    solde: Mapped[float] = mapped_column(Numeric(12, 3), default=0)
    limite_credit: Mapped[float] = mapped_column(Numeric(12, 3), default=0)
    currency: Mapped[str] = mapped_column(String(10), default="TND")
    derniere_mise_a_jour: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
