from __future__ import annotations

from PyQt6.QtWidgets import QMessageBox, QWidget


def confirm(parent: QWidget, title: str, message: str) -> bool:
    """Returns True if user clicked Yes."""
    reply = QMessageBox.question(
        parent, title, message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return reply == QMessageBox.StandardButton.Yes
