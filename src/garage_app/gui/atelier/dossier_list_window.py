from __future__ import annotations

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QBrush, QColor, QIcon
from PyQt6.QtWidgets import (
    QHBoxLayout, QMdiSubWindow, QPushButton, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.atelier.dossier_reparation import DossierReparation
from garage_app.domain.atelier.statut_dossier import StatutDossier
from garage_app.gui.widgets.searchable_table import SearchableTableWidget


class _DossierModel(QAbstractTableModel):
    HEADERS = ["N° Dossier", "Véhicule", "Client", "Kilométrage", "Statut"]

    def __init__(self, dossiers: list[DossierReparation]) -> None:
        super().__init__()
        self._data = dossiers

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        d = self._data[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            col = index.column()
            return [
                str(d.id)[:8] + "…",
                str(d.vehicule_id)[:8],
                str(d.client_id)[:8],
                str(d.kilometrage_entree),
                d.statut.label_fr(),
            ][col]
        if role == Qt.ItemDataRole.ForegroundRole and index.column() == 4:
            return QBrush(QColor(d.statut.color()))
        return None

    def get_dossier(self, row: int) -> DossierReparation:
        return self._data[row]

    def reload(self, dossiers: list[DossierReparation]) -> None:
        self.beginResetModel()
        self._data = dossiers
        self.endResetModel()


class DossierListWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self.setWindowTitle("Dossiers de réparation")
        self.setWindowIcon(QIcon.fromTheme("document-open"))
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        self._table_widget = SearchableTableWidget()
        self._model = _DossierModel([])
        self._table_widget.set_source_model(self._model)
        self._table_widget.table.doubleClicked.connect(self._open_dossier)

        btn_row = QHBoxLayout()
        btn_refresh = QPushButton(QIcon.fromTheme("view-refresh"), "Actualiser")
        btn_refresh.clicked.connect(self._load)
        btn_row.addWidget(btn_refresh)
        btn_row.addStretch()

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addLayout(btn_row)
        layout.addWidget(self._table_widget)
        self.setWidget(widget)
        self.resize(900, 500)

    def _load(self) -> None:
        dossiers = self._ctx.dossier_service.list_open(self._session)
        self._model.reload(dossiers)

    def _open_dossier(self, index) -> None:
        src_row = self._table_widget.proxy.mapToSource(index).row()
        dossier = self._model.get_dossier(src_row)
        from garage_app.gui.atelier.dossier_window import DossierWindow
        from PyQt6.QtWidgets import QApplication
        mdi = self.mdiArea()
        if mdi:
            win = DossierWindow(self._ctx, self._session, dossier)
            sub = mdi.addSubWindow(win)
            sub.show()
