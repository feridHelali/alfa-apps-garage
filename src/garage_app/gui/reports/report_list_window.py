from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QMdiSubWindow, QVBoxLayout, QWidget
from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession


class ReportListWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self.setWindowTitle("Modèles de rapports")
        widget = QWidget()
        layout = QVBoxLayout(widget)
        templates = ctx.report_service.list_templates()
        for t in templates:
            layout.addWidget(QLabel(f"• {t.name} [{t.category}]"))
        if not templates:
            layout.addWidget(QLabel("Aucun modèle de rapport."))
        self.setWidget(widget)
        self.resize(500, 350)
