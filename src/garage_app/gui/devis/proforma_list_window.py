"""ProformaListWindow — list of Factures Proforma."""
from __future__ import annotations

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QMdiSubWindow, QMessageBox, QPushButton,
    QTableView, QVBoxLayout, QWidget, QHeaderView,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.devis.devis import FactureProforma
from garage_app.domain.shared.exceptions import BusinessRuleError


class _ProformaTableModel(QAbstractTableModel):
    HEADERS = ["Numéro", "Date", "Client", "Total TTC", "Acompte", "Solde", "Statut"]

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[FactureProforma] = []
        self._clients: dict[str, str] = {}

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        pf = self._rows[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            client = self._clients.get(str(pf.client_id), str(pf.client_id)[:8])
            return [
                pf.numero,
                pf.date_emission.isoformat() if pf.date_emission else "—",
                client,
                pf.total_ttc.format(),
                pf.acompte_recu.format(),
                pf.solde_restant.format(),
                pf.statut.label_fr(),
            ][col]
        if role == Qt.ItemDataRole.ForegroundRole and col == 6:
            return QBrush(QColor(pf.statut.color()))
        if role == Qt.ItemDataRole.TextAlignmentRole and col in (3, 4, 5):
            return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        return None

    def get_proforma(self, row: int) -> FactureProforma:
        return self._rows[row]

    def reload(self, rows: list[FactureProforma], clients: dict[str, str]) -> None:
        self.beginResetModel()
        self._rows = rows
        self._clients = clients
        self.endResetModel()


class ProformaListWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self.setWindowTitle("Factures Proforma")
        self.setMinimumSize(860, 480)
        self.resize(920, 540)

        widget = QWidget()
        self.setWidget(widget)
        root = QVBoxLayout(widget)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Liste des factures proforma"))
        toolbar.addStretch()
        btn_refresh = QPushButton("Actualiser")
        btn_refresh.clicked.connect(self._reload)
        toolbar.addWidget(btn_refresh)
        root.addLayout(toolbar)

        self._model = _ProformaTableModel()
        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.doubleClicked.connect(self._open_selected)
        root.addWidget(self._table)

        actions = QHBoxLayout()
        self._btn_open = QPushButton("Ouvrir / Imprimer")
        self._btn_acompte = QPushButton("Enregistrer un acompte…")
        self._btn_open.clicked.connect(self._open_selected)
        self._btn_acompte.clicked.connect(self._acompte)
        actions.addWidget(self._btn_open)
        actions.addWidget(self._btn_acompte)
        actions.addStretch()
        root.addLayout(actions)

        self._table.selectionModel().selectionChanged.connect(self._update_buttons)
        self._update_buttons()
        self._reload()

    def _reload(self) -> None:
        try:
            rows = self._ctx.devis_service.list_proformas(self._session)
        except Exception:
            rows = []
        clients: dict[str, str] = {}
        try:
            for c in self._ctx.client_service.list_clients(self._session):
                clients[str(c.id)] = f"{c.nom} {c.prenom}"
        except Exception:
            pass
        self._model.reload(rows, clients)
        self._update_buttons()

    def _selected(self) -> FactureProforma | None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return None
        return self._model.get_proforma(rows[0].row())

    def _update_buttons(self) -> None:
        pf = self._selected()
        self._btn_open.setEnabled(pf is not None)
        can_manage = self._session.can(Permission.MANAGE_PROFORMA)
        active = pf is not None and pf.statut.value in ("emise", "acompte_recu")
        self._btn_acompte.setEnabled(can_manage and active)

    def _open_selected(self) -> None:
        pf = self._selected()
        if not pf:
            return
        from garage_app.gui.devis.proforma_viewer_window import ProformaViewerWindow
        dlg = ProformaViewerWindow(self._ctx, self._session, pf, parent=self.parentWidget())
        dlg.exec()
        self._reload()

    def _acompte(self) -> None:
        pf = self._selected()
        if not pf:
            return
        from garage_app.gui.devis.proforma_viewer_window import ProformaViewerWindow
        dlg = ProformaViewerWindow(self._ctx, self._session, pf, parent=self.parentWidget())
        dlg.exec()
        self._reload()
