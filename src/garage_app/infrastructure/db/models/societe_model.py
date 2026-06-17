from __future__ import annotations

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from garage_app.infrastructure.db.base import Base


class SocieteModel(Base):
    __tablename__ = "societe"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    raison_sociale: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    siret: Mapped[str] = mapped_column(String(14), default="")
    adresse: Mapped[str] = mapped_column(Text, default="")
    telephone: Mapped[str] = mapped_column(String(20), default="")
    email: Mapped[str] = mapped_column(String(100), default="")
    logo_path: Mapped[str] = mapped_column(String(500), default="")
    licence_key: Mapped[str] = mapped_column(String(100), default="")
    taux_tva_defaut: Mapped[float] = mapped_column(Float, default=20.0)
