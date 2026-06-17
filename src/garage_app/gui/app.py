from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import QTranslator, QLocale

APP_ICON = Path(__file__).parents[3] / "assets" / "icons" / "app_icon.svg"
STYLES_DIR = Path(__file__).parents[3] / "assets" / "styles"


class GarageApplication(QApplication):
    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)
        self.setApplicationName("Gestion Réparation Voiture")
        self.setApplicationVersion("0.1.0")
        self.setOrganizationName("Alfa Computers Apps")
        self.setOrganizationDomain("alfa-computers.app")
        if APP_ICON.exists():
            self.setWindowIcon(QIcon(str(APP_ICON)))
        self._apply_font()
        self._translator = QTranslator()

    def _apply_font(self) -> None:
        font = QFont("Segoe UI", 10)
        self.setFont(font)

    def apply_stylesheet(self, theme: str = "light") -> None:
        qss_file = STYLES_DIR / f"{theme}.qss"
        if qss_file.exists():
            self.setStyleSheet(qss_file.read_text(encoding="utf-8"))

    def load_language(self, lang: str) -> None:
        resources_dir = Path(__file__).parents[3] / "resources" / "i18n"
        qm = resources_dir / f"garage_{lang}.qm"
        if qm.exists() and self._translator.load(str(qm)):
            self.installTranslator(self._translator)
