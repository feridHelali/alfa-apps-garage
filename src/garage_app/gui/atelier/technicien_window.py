from __future__ import annotations

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QLabel, QMdiSubWindow, QMessageBox,
    QPushButton, QSplitter, QTableView, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user import User
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.atelier.statut_dossier import StatutDossier, StatutTache


class _TechnicienModel(QAbstractTableModel):
    HEADERS = ["Nom", "Identifiant", "Ops à faire", "Ops en cours", "Ops terminées"]

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[tuple[User, int, int, int]] = []

    def reload(self, rows: list[tuple[User, int, int, int]]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.HEADERS)

    def headerData(self, section: int, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        user, a_faire, en_cours, terminee = self._rows[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            return [user.full_name, user.username, a_faire, en_cours, terminee][col]

        if role == Qt.ItemDataRole.TextAlignmentRole and col >= 2:
            return Qt.AlignmentFlag.AlignCenter

        if role == Qt.ItemDataRole.ForegroundRole:
            if col == 2 and a_faire > 0:
                return QColor("#856404")
            if col == 3 and en_cours > 0:
                return QColor("#0C5460")
            if col == 4 and terminee > 0:
                return QColor("#155724")

        if role == Qt.ItemDataRole.FontRole and col >= 2:
            f = QFont()
            f.setBold(True)
            return f

        return None

    def get_user(self, row: int) -> User:
        return self._rows[row][0]


class TechnicienWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self.setWindowTitle("Techniciens — Charge de travail")
        self._build_ui()
        self._load()
        self.resize(880, 520)

    def _build_ui(self) -> None:
        root = QWidget()
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(6, 6, 6, 6)

        # Toolbar
        btn_row = QHBoxLayout()
        self._btn_refresh = QPushButton("Actualiser")
        self._btn_refresh.clicked.connect(self._load)
        btn_row.addWidget(self._btn_refresh)
        btn_row.addStretch()
        self._info = QLabel()
        self._info.setStyleSheet("color: #555; font-size: 10px;")
        btn_row.addWidget(self._info)
        vbox.addLayout(btn_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: technician list
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 4, 0)
        lv.addWidget(QLabel("<b>Techniciens</b>"))
        self._model = _TechnicienModel()
        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._table.setColumnWidth(0, 160)
        self._table.setColumnWidth(1, 110)
        self._table.setColumnWidth(2, 90)
        self._table.setColumnWidth(3, 90)
        self._table.setColumnWidth(4, 90)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.selectionModel().currentRowChanged.connect(self._on_select)
        lv.addWidget(self._table)
        splitter.addWidget(left)

        # Right: operations detail for selected technician
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(4, 0, 0, 0)
        self._detail_label = QLabel("<b>Opérations assignées</b>")
        rv.addWidget(self._detail_label)
        self._ops_table = QTableWidget(0, 5)
        self._ops_table.setHorizontalHeaderLabels(
            ["Dossier", "Description", "Temps est.", "Temps passé", "Statut"]
        )
        self._ops_table.horizontalHeader().setStretchLastSection(True)
        self._ops_table.setColumnWidth(0, 90)
        self._ops_table.setColumnWidth(1, 200)
        self._ops_table.setColumnWidth(2, 80)
        self._ops_table.setColumnWidth(3, 80)
        self._ops_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._ops_table.verticalHeader().setVisible(False)
        self._ops_table.setAlternatingRowColors(True)
        rv.addWidget(self._ops_table)
        splitter.addWidget(right)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        vbox.addWidget(splitter)

        self.setWidget(root)

    def _load(self) -> None:
        try:
            all_users = self._ctx.auth_service.list_users(self._session)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
            return

        techs = [u for u in all_users if u.role == "technicien" and u.is_active]

        try:
            dossiers = self._ctx.dossier_service.list_dossiers(self._session)
        except Exception:
            dossiers = []

        # Build workload counts per technician
        self._tech_ops: dict = {}  # user.id -> list of (dossier_id, op)
        for d in dossiers:
            if d.statut == StatutDossier.CLOTURE:
                continue
            for op in d.operations:
                if op.technicien_id is None:
                    continue
                tid = op.technicien_id
                if tid not in self._tech_ops:
                    self._tech_ops[tid] = []
                self._tech_ops[tid].append((d.id, op))

        rows = []
        for u in techs:
            ops = self._tech_ops.get(u.id, [])
            a_faire = sum(1 for _, o in ops if o.statut == StatutTache.A_FAIRE)
            en_cours = sum(1 for _, o in ops if o.statut == StatutTache.EN_COURS)
            terminee = sum(1 for _, o in ops if o.statut == StatutTache.TERMINEE)
            rows.append((u, a_faire, en_cours, terminee))

        self._model.reload(rows)
        self._info.setText(f"{len(techs)} technicien(s) actif(s)")
        self._ops_table.setRowCount(0)

    def _on_select(self, *_) -> None:
        idx = self._table.currentIndex()
        if not idx.isValid():
            self._ops_table.setRowCount(0)
            return
        user = self._model.get_user(idx.row())
        ops_list = self._tech_ops.get(user.id, [])
        self._detail_label.setText(f"<b>Opérations de {user.full_name}</b>")
        self._ops_table.setRowCount(0)
        _tache_labels = {
            StatutTache.A_FAIRE: "À faire",
            StatutTache.EN_COURS: "En cours",
            StatutTache.TERMINEE: "Terminée",
        }
        for dossier_id, op in ops_list:
            row = self._ops_table.rowCount()
            self._ops_table.insertRow(row)
            self._ops_table.setItem(row, 0, QTableWidgetItem(str(dossier_id)[:8] + "…"))
            self._ops_table.setItem(row, 1, QTableWidgetItem(op.description))
            self._ops_table.setItem(row, 2, QTableWidgetItem(f"{op.temps_estime:.2f} h"))
            self._ops_table.setItem(row, 3, QTableWidgetItem(f"{op.temps_passe:.2f} h"))
            self._ops_table.setItem(row, 4, QTableWidgetItem(_tache_labels.get(op.statut, op.statut)))
