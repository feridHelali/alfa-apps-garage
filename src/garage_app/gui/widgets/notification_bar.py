from __future__ import annotations

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget


class NotificationBar(QFrame):
    """Transient info/success/warning bar. Call show_message() to display."""

    COLORS = {
        "success": "#d4edda",
        "info": "#d1ecf1",
        "warning": "#fff3cd",
        "error": "#f8d7da",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._label = QLabel()
        layout = QHBoxLayout(self)
        layout.addWidget(self._label)
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_message(self, text: str, kind: str = "info", duration_ms: int = 4000) -> None:
        color = self.COLORS.get(kind, self.COLORS["info"])
        self.setStyleSheet(f"background-color: {color}; border: 1px solid #c0c0c0; padding: 4px;")
        self._label.setText(text)
        self.show()
        self._timer.start(duration_ms)
