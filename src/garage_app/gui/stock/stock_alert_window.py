from __future__ import annotations

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QMdiSubWindow, QPushButton, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.stock.piece import Piece
from garage_app.gui.widgets.searchable_table import SearchableTableWidget
from garage_app.gui.widgets.icon_helper import icon as _icon


class _AlertModel(QAbstractTableModel):
    HEADERS = ["Référence", "Désignation", "Catégorie", "Stock actuel", "Seuil", "Manque"]

    def __init__(self, rows: list[Piece]) -> None:
        super().__init__()
        self._data = rows

    def rowCount(self, parent=QModelIndex()) -> int: return len(self._data)
    def columnCount(self, parent=QModelIndex()) -> int: return len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        p = self._data[index.row()]
        col = index.column()
        manque = max(0, p.seuil_alerte - p.quantite_stock)
        if role == Qt.ItemDataRole.DisplayRole:
            return [
                p.reference_constructeur, p.designation, p.categorie,
                str(p.quantite_stock), str(p.seuil_alerte), str(manque),
            ][col]
        if role == Qt.ItemDataRole.ForegroundRole:
            if col == 3:
                return QBrush(QColor("#D83B01") if p.quantite_stock == 0 else QColor("#7A4F00"))
            if col == 5 and manque > 0:
                return QBrush(QColor("#A4262C"))
        if role == Qt.ItemDataRole.BackgroundRole and p.quantite_stock == 0:
            return QBrush(QColor("#FDE7E9"))
        return None

    def reload(self, rows: list[Piece]) -> None:
        self.beginResetModel()
        self._data = rows
        self.endResetModel()


class StockAlertWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self.setWindowTitle("Alertes stock")
        self._build_ui()
        self._load()

    def status_info(self) -> str:
        ruptures = sum(1 for p in self._model._data if p.quantite_stock == 0)
        return (
            f"Alertes stock — {len(self._model._data)} pièces sous le seuil"
            + (f"  |  {ruptures} en rupture totale" if ruptures else "")
        )

    def _build_ui(self) -> None:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        hdr = QHBoxLayout()
        self._lbl_summary = QLabel("")
        self._lbl_summary.setStyleSheet("font-weight: 600; color: #D83B01;")
        btn_refresh = QPushButton(_icon("refresh"), "Actualiser")
        btn_refresh.clicked.connect(self._load)
        hdr.addWidget(self._lbl_summary)
        hdr.addStretch()
        hdr.addWidget(btn_refresh)
        layout.addLayout(hdr)

        self._table_w = SearchableTableWidget()
        self._model = _AlertModel([])
        self._table_w.set_source_model(self._model)
        layout.addWidget(self._table_w)

        self.setWidget(container)
        self.resize(800, 420)

    def _load(self) -> None:
        pieces = self._ctx.stock_service.pieces_en_alerte(self._session)
        self._model.reload(pieces)
        ruptures = sum(1 for p in pieces if p.quantite_stock == 0)
        if pieces:
            txt = f"⚠ {len(pieces)} pièce(s) sous le seuil d'alerte"
            if ruptures:
                txt += f"  —  {ruptures} en rupture totale"
        else:
            txt = "✓ Aucune alerte de stock"
            self._lbl_summary.setStyleSheet("font-weight: 600; color: #107C10;")
        self._lbl_summary.setText(txt)
