from __future__ import annotations

from garage_app.infrastructure.db.models.settings_model import AppSettingsModel
from garage_app.infrastructure.db.session import SessionFactory


class AppSettingsRepository:
    def __init__(self, sf: SessionFactory) -> None:
        self._sf = sf

    def get(self, key: str, default: str = "") -> str:
        with self._sf.get_session() as s:
            m = s.get(AppSettingsModel, key)
            return m.value if m else default

    def set(self, key: str, value: str) -> None:
        with self._sf.get_session() as s:
            m = s.get(AppSettingsModel, key)
            if m:
                m.value = value
            else:
                s.add(AppSettingsModel(key=key, value=value))

    def get_prefix(self, prefix: str) -> dict[str, str]:
        with self._sf.get_session() as s:
            rows = (
                s.query(AppSettingsModel)
                .filter(AppSettingsModel.key.like(f"{prefix}%"))
                .all()
            )
            return {m.key: m.value for m in rows}
