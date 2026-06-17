from __future__ import annotations

from garage_app.settings import AppSettings


class SettingsService:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def get(self) -> AppSettings:
        return self._settings

    def set_language(self, lang: str) -> None:
        self._settings.language = lang

    def set_theme(self, theme: str) -> None:
        self._settings.theme = theme
