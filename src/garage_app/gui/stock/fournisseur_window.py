from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QMdiSubWindow, QVBoxLayout, QWidget
from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession


class FournisseurWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self.setWindowTitle("Fournisseurs")
        widget = QWidget()
        QVBoxLayout(widget).addWidget(QLabel("Gestion fournisseurs — Sprint 01 Stock"))
        self.setWidget(widget)
        self.resize(800, 480)
