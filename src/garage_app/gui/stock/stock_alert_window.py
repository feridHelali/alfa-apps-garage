from __future__ import annotations

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QLabel, QMdiSubWindow, QVBoxLayout, QWidget
from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession


class StockAlertWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self.setWindowTitle("Alertes stock")
        self.setWindowIcon(QIcon.fromTheme("dialog-warning"))
        widget = QWidget()
        layout = QVBoxLayout(widget)
        pieces = ctx.stock_service.pieces_en_alerte(session)
        if pieces:
            for p in pieces:
                layout.addWidget(QLabel(
                    f"⚠ {p.designation} ({p.reference_constructeur}) — stock: {p.quantite_stock}"
                ))
        else:
            layout.addWidget(QLabel("Aucune alerte de stock."))
        self.setWidget(widget)
        self.resize(500, 300)
