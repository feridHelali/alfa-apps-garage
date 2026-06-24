from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QMdiSubWindow,
    QPushButton, QTabWidget, QVBoxLayout, QWidget,
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
        self.resize(420, 320)

    def _build_ui(self) -> None:
        root = QWidget()
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(8, 8, 8, 8)

        self._notif = NotificationBar()
        vbox.addWidget(self._notif)

        tabs = QTabWidget()

        # ── Tab: Affichage ───────────────────────────────────────────────────
        display_tab = QWidget()
        dtv = QVBoxLayout(display_tab)
        grp = QGroupBox("Interface")
        form = QFormLayout(grp)
        self._lang = QComboBox()
        self._lang.addItems(["fr — Français", "ar — عربي"])
        self._theme = QComboBox()
        self._theme.addItems(["light — Clair", "dark — Sombre"])
        form.addRow("Langue :", self._lang)
        form.addRow("Thème :", self._theme)
        dtv.addWidget(grp)
        dtv.addStretch()
        tabs.addTab(display_tab, "Affichage")

        # ── Tab: Numérotation (shortcut) ─────────────────────────────────────
        num_tab = QWidget()
        ntv = QVBoxLayout(num_tab)
        btn_open_num = QPushButton("Ouvrir la fenêtre de numérotation…")
        btn_open_num.clicked.connect(self._open_numerotation)
        ntv.addWidget(btn_open_num)
        ntv.addStretch()
        tabs.addTab(num_tab, "Numérotation")

        vbox.addWidget(tabs)

        # ── Footer ───────────────────────────────────────────────────────────
        foot = QHBoxLayout()
        btn_save = QPushButton("Appliquer")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._apply)
        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.close)
        foot.addStretch()
        foot.addWidget(btn_close)
        foot.addWidget(btn_save)
        vbox.addLayout(foot)

        settings = self._ctx.settings_service.get()
        self._lang.setCurrentIndex(0 if settings.language != "ar" else 1)
        self._theme.setCurrentIndex(0 if settings.theme == "light" else 1)

        self.setWidget(root)

    def _apply(self) -> None:
        lang = "fr" if self._lang.currentIndex() == 0 else "ar"
        theme = "light" if self._theme.currentIndex() == 0 else "dark"
        self._ctx.settings_service.set_language(lang)
        self._ctx.settings_service.set_theme(theme)
        self._notif.show_message("Paramètres appliqués. Redémarrez pour le thème.", "info")

    def _open_numerotation(self) -> None:
        from garage_app.gui.admin.numerotation_window import NumerotationWindow
        mdi = self.mdiArea()
        if mdi:
            from garage_app.gui.window_registry import open_sub
            open_sub(mdi, NumerotationWindow(self._ctx, self._session))
