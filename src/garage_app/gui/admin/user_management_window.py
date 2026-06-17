from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QMdiSubWindow, QVBoxLayout, QWidget
from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession


class UserManagementWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self.setWindowTitle("Gestion des utilisateurs")
        widget = QWidget()
        QVBoxLayout(widget).addWidget(QLabel("CRUD utilisateurs + RBAC — à implémenter (Sprint 02)"))
        self.setWidget(widget)
        self.resize(700, 450)
