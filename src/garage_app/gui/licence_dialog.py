"""Licence activation dialog — shown on first launch when no valid key is present."""
from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from garage_app.domain.societe.licence import validate_key
from garage_app.settings import APP_VERSION


def _key_file() -> Path:
    """Return path to licence.key — next to the EXE when bundled, else project root."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "licence.key"
    return Path(__file__).resolve().parents[3] / "licence.key"


def read_stored_key() -> str:
    """Return the stored key string, or '' if absent."""
    path = _key_file()
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return ""


def store_key(key: str) -> None:
    _key_file().write_text(key.upper().strip(), encoding="utf-8")


def is_activated() -> bool:
    return validate_key(read_stored_key())


class LicenceDialog(QDialog):
    """Modal dialog prompting the user to enter a valid licence key."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Activation du logiciel")
        self.setFixedWidth(460)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint
        )
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel(f"Gestion Réparation Voiture  v{APP_VERSION}")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        pub = QLabel("Alfa Computers Apps")
        pub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(pub)

        layout.addSpacing(8)

        info = QLabel(
            "Ce logiciel nécessite une clé de licence valide.\n"
            "Saisissez votre clé au format  ALFA-XXXX-XXXX-XXXX-XXXX"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self._key_input = QLineEdit()
        self._key_input.setPlaceholderText("ALFA-XXXX-XXXX-XXXX-XXXX")
        self._key_input.setMaxLength(24)
        font = QFont("Courier New", 11)
        self._key_input.setFont(font)
        self._key_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._key_input)

        self._status = QLabel("")
        self._status.setStyleSheet("color: red;")
        layout.addWidget(self._status)

        layout.addSpacing(4)

        contact = QLabel(
            "Pour obtenir une clé : <a href='mailto:helaliferid@gmail.com'>helaliferid@gmail.com</a>"
            "  |  +216 22 45 79 16<br>"
            "<a href='https://alfa-computers.com'>https://alfa-computers.com</a>"
        )
        contact.setOpenExternalLinks(True)
        contact.setWordWrap(True)
        contact.setStyleSheet("color: #555;")
        layout.addWidget(contact)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_btn.setText("Activer")
        self._ok_btn.setEnabled(False)
        buttons.accepted.connect(self._activate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_text_changed(self, text: str) -> None:
        clean = text.upper().replace(" ", "")
        self._ok_btn.setEnabled(validate_key(clean))
        self._status.setText("")

    def _activate(self) -> None:
        key = self._key_input.text().upper().strip()
        if validate_key(key):
            store_key(key)
            self.accept()
        else:
            self._status.setText("Clé invalide — vérifiez le format et réessayez.")
