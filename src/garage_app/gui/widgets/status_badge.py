from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel

from garage_app.domain.atelier.statut_dossier import StatutDossier


class StatusBadgeLabel(QLabel):
    """Colored pill label reflecting a StatutDossier value."""

    def __init__(self, statut: StatutDossier | None = None, parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(22)
        self.setMinimumWidth(120)
        if statut:
            self.set_statut(statut)

    def set_statut(self, statut: StatutDossier) -> None:
        color = statut.color()
        self.setText(statut.label_fr())
        self.setStyleSheet(
            f"background-color: {color}; color: white; border-radius: 10px;"
            f"padding: 2px 10px; font-weight: bold; font-size: 10px;"
        )
