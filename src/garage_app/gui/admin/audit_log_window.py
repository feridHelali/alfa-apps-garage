from __future__ import annotations

from datetime import datetime, timezone, timedelta

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from garage_app.application.audit_service import AuditService
from garage_app.domain.audit.audit_entry import AuditEntry, LogCategory, LogLevel
from garage_app.domain.auth.user_session import UserSession

_LEVEL_COLORS = {
    "DEBUG":    QColor("#888888"),
    "INFO":     QColor("#1a6b1a"),
    "WARNING":  QColor("#b35c00"),
    "ERROR":    QColor("#cc0000"),
    "CRITICAL": QColor("#7b0000"),
}

_COLUMNS = ["Date/Heure", "Niveau", "Catégorie", "Utilisateur", "Entité", "Message"]


class _LogModel(QAbstractTableModel):
    def __init__(self) -> None:
        super().__init__()
        self._rows: list[AuditEntry] = []

    def load(self, rows: list[AuditEntry]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(_COLUMNS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return _COLUMNS[section]

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        entry = self._rows[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            match col:
                case 0:
                    return entry.occurred_at.strftime("%Y-%m-%d %H:%M:%S")
                case 1:
                    return str(entry.level)
                case 2:
                    return str(entry.category)
                case 3:
                    return entry.username or "—"
                case 4:
                    if entry.entity_type and entry.entity_id:
                        return f"{entry.entity_type} #{entry.entity_id[:8]}"
                    return "—"
                case 5:
                    return entry.message
        if role == Qt.ItemDataRole.ForegroundRole and col == 1:
            return _LEVEL_COLORS.get(str(entry.level))
        if role == Qt.ItemDataRole.FontRole and entry.level in (LogLevel.ERROR, LogLevel.CRITICAL):
            f = QFont()
            f.setBold(True)
            return f
        return None


class AuditLogWindow(QWidget):
    def __init__(self, audit_service: AuditService, user_session: UserSession) -> None:
        super().__init__()
        self._svc = audit_service
        self._session = user_session
        self.setWindowTitle("Journal d'audit")
        self.resize(1100, 600)
        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        # ── Filter bar ──────────────────────────────────────────────────────
        bar = QHBoxLayout()

        bar.addWidget(QLabel("Période :"))
        self._period = QComboBox()
        self._period.addItems(["Aujourd'hui", "7 jours", "30 jours", "Tout"])
        bar.addWidget(self._period)

        bar.addWidget(QLabel("Catégorie :"))
        self._cat = QComboBox()
        self._cat.addItem("Toutes", None)
        for c in LogCategory:
            self._cat.addItem(str(c), c)
        bar.addWidget(self._cat)

        bar.addWidget(QLabel("Niveau :"))
        self._lvl = QComboBox()
        self._lvl.addItem("Tous", None)
        for l in LogLevel:
            self._lvl.addItem(str(l), l)
        bar.addWidget(self._lvl)

        bar.addWidget(QLabel("Utilisateur :"))
        self._user_filter = QLineEdit()
        self._user_filter.setFixedWidth(120)
        bar.addWidget(self._user_filter)

        btn = QPushButton("Actualiser")
        btn.clicked.connect(self._refresh)
        bar.addWidget(btn)
        bar.addStretch()
        root.addLayout(bar)

        # ── Table ────────────────────────────────────────────────────────────
        self._model = _LogModel()
        self._proxy = QSortFilterProxyModel()
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy.setFilterKeyColumn(5)   # message column

        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        root.addWidget(self._table)

        # ── Status bar ───────────────────────────────────────────────────────
        self._status = QLabel()
        root.addWidget(self._status)

    def _refresh(self) -> None:
        period_text = self._period.currentText()
        since: datetime | None = None
        now = datetime.now(timezone.utc)
        if period_text == "Aujourd'hui":
            since = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period_text == "7 jours":
            since = now - timedelta(days=7)
        elif period_text == "30 jours":
            since = now - timedelta(days=30)

        rows = self._svc.find_recent(
            self._session,
            limit=1000,
            category=self._cat.currentData(),
            level=self._lvl.currentData(),
            username=self._user_filter.text().strip() or None,
            since=since,
        )
        self._model.load(list(rows))
        self._status.setText(f"{len(rows)} entrée(s) trouvée(s)")
