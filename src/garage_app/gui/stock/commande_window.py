from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QMdiSubWindow, QVBoxLayout, QWidget
from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession


class CommandeWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self.setWindowTitle("Commandes fournisseurs")
        widget = QWidget()
        QVBoxLayout(widget).addWidget(QLabel("Commandes fournisseurs — Sprint 01 Stock"))
        self.setWidget(widget)
        self.resize(800, 480)
