from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox, QFormLayout, QMdiSubWindow, QPushButton, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.gui.widgets.notification_bar import NotificationBar


class SettingsWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self.setWindowTitle("Paramètres")
        self._build_ui()

    def _build_ui(self) -> None:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self._notif = NotificationBar()
        layout.addWidget(self._notif)

        form = QFormLayout()
        self._lang = QComboBox()
        self._lang.addItems(["fr — Français", "en — English"])
        self._theme = QComboBox()
        self._theme.addItems(["light — Clair", "dark — Sombre"])
        form.addRow("Langue :", self._lang)
        form.addRow("Thème :", self._theme)
        layout.addLayout(form)

        btn = QPushButton("Appliquer")
        btn.clicked.connect(self._apply)
        layout.addWidget(btn)

        settings = self._ctx.settings_service.get()
        self._lang.setCurrentIndex(0 if settings.language == "fr" else 1)
        self._theme.setCurrentIndex(0 if settings.theme == "light" else 1)

        self.setWidget(widget)
        self.resize(350, 220)

    def _apply(self) -> None:
        lang = "fr" if self._lang.currentIndex() == 0 else "en"
        theme = "light" if self._theme.currentIndex() == 0 else "dark"
        self._ctx.settings_service.set_language(lang)
        self._ctx.settings_service.set_theme(theme)
        self._notif.show_message("Paramètres appliqués. Redémarrez pour le thème.", "info")
