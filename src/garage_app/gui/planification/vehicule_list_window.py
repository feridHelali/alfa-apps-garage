from __future__ import annotations

import uuid
from datetime import datetime

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel
from PyQt6.QtGui import QBrush, QColor, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView, QDialog, QHBoxLayout, QLabel, QLineEdit,
    QMdiSubWindow, QMessageBox, QPushButton, QTableView, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession


def _fmt_date(dt: datetime | None) -> str:
    return dt.strftime("%d/%m/%Y") if dt else "—"


class _ParcModel(QAbstractTableModel):
    HEADERS = [
        "Immatriculation", "Marque", "Modèle", "Année",
        "Client", "Téléphone",
        "1ère visite", "Dernière visite", "Km max", "Dossiers",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[dict] = []

    def reload(self, rows: list[dict]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

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
        row = self._rows[index.row()]
        v = row["vehicule"]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            values = [
                v.immatriculation,
                v.marque,
                v.modele,
                str(v.annee) if v.annee else "—",
                row["client_nom"],
                row["client_tel"] or "—",
                _fmt_date(row["premiere_visite"]),
                _fmt_date(row["derniere_visite"]),
                f"{row['km_max']:,} km" if row["km_max"] else "—",
                str(row["nb_dossiers"]),
            ]
            return values[col]

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (3, 8, 9):
                return Qt.AlignmentFlag.AlignCenter

        if role == Qt.ItemDataRole.ForegroundRole and col == 9:
            n = row["nb_dossiers"]
            if n == 0:
                return QBrush(QColor("#AEAEB2"))
            if n >= 5:
                return QBrush(QColor("#0055a5"))

        if role == Qt.ItemDataRole.FontRole and col == 0:
            f = QFont()
            f.setBold(True)
            return f

        return None

    def get_row(self, row: int) -> dict:
        return self._rows[row]


class VehiculeListWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self.setWindowTitle("Parc Véhicules")
        self._build_ui()
        self._load()
        self.resize(1100, 600)

    def _build_ui(self) -> None:
        root = QWidget()
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(6, 6, 6, 6)
        vbox.setSpacing(6)

        # ── Toolbar ──────────────────────────────────────────────────────────
        bar = QHBoxLayout()
        self._btn_refresh = QPushButton("Actualiser")
        self._btn_refresh.clicked.connect(self._load)
        self._btn_carnet = QPushButton("Carnet de Route…")
        self._btn_carnet.clicked.connect(self._open_carnet)
        self._btn_carnet.setEnabled(False)
        bar.addWidget(self._btn_refresh)
        bar.addWidget(self._btn_carnet)
        bar.addStretch()
        self._info = QLabel()
        self._info.setStyleSheet("color: #555; font-size: 10px;")
        bar.addWidget(self._info)
        vbox.addLayout(bar)

        # ── Search ───────────────────────────────────────────────────────────
        self._search = QLineEdit()
        self._search.setPlaceholderText("Rechercher (immatriculation, client, marque…)")
        self._search.textChanged.connect(self._on_search)
        vbox.addWidget(self._search)

        # ── Table ────────────────────────────────────────────────────────────
        self._model = _ParcModel()
        self._proxy = QSortFilterProxyModel()
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy.setFilterKeyColumn(-1)

        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSortingEnabled(True)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setColumnWidth(0, 120)
        self._table.setColumnWidth(1, 90)
        self._table.setColumnWidth(2, 90)
        self._table.setColumnWidth(3, 50)
        self._table.setColumnWidth(4, 160)
        self._table.setColumnWidth(5, 110)
        self._table.setColumnWidth(6, 90)
        self._table.setColumnWidth(7, 90)
        self._table.setColumnWidth(8, 80)
        self._table.setColumnWidth(9, 70)
        self._table.selectionModel().currentRowChanged.connect(self._on_select)
        self._table.doubleClicked.connect(self._open_carnet)
        vbox.addWidget(self._table)

        self.setWidget(root)

    def _load(self) -> None:
        try:
            rows = self._ctx.analytics_service.parc_vehicules(self._session)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
            return
        self._model.reload(rows)
        self._info.setText(f"{len(rows)} véhicule(s) enregistré(s)")
        self._btn_carnet.setEnabled(False)

    def _on_search(self, text: str) -> None:
        self._proxy.setFilterFixedString(text)

    def _on_select(self, current, _) -> None:
        self._btn_carnet.setEnabled(current.isValid())

    def _open_carnet(self, *_) -> None:
        idx = self._table.currentIndex()
        if not idx.isValid():
            return
        src_row = self._proxy.mapToSource(idx).row()
        row = self._model.get_row(src_row)
        vehicule_id: uuid.UUID = row["vehicule"].id
        from garage_app.gui.reports.carnet_de_route_window import CarnetDeRouteWindow
        from garage_app.gui.window_registry import open_sub
        mdi = self.mdiArea()
        if mdi:
            open_sub(mdi, CarnetDeRouteWindow(self._ctx, self._session, vehicule_id))
