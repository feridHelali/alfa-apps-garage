from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from garage_app.infrastructure.db.base import Base


class AppSettingsModel(Base):
    __tablename__ = "app_settings"
    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[str] = mapped_column(String(500), nullable=False, default="")
