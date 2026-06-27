from __future__ import annotations

import uuid

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QBrush, QColor, QIcon
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QLabel, QMdiSubWindow, QMessageBox, QPushButton, QSpinBox,
    QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.atelier.dossier_reparation import DossierReparation
from garage_app.domain.atelier.statut_dossier import StatutDossier
from garage_app.gui.widgets.searchable_table import SearchableTableWidget
from garage_app.gui.window_registry import open_sub
from garage_app.gui.widgets.icon_helper import icon as _icon


class _DossierModel(QAbstractTableModel):
    HEADERS = ["N° Dossier", "Immatriculation", "Client", "Kilométrage", "Statut"]

    def __init__(self) -> None:
        super().__init__()
        self._data: list[DossierReparation] = []
        self._clients: dict[str, str] = {}
        self._vehicules: dict[str, str] = {}

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
                self._vehicules.get(str(d.vehicule_id), str(d.vehicule_id)[:8]),
                self._clients.get(str(d.client_id), str(d.client_id)[:8]),
                f"{d.kilometrage_entree:,} km",
                d.statut.label_fr(),
            ][col]
        if role == Qt.ItemDataRole.ForegroundRole and index.column() == 4:
            return QBrush(QColor(d.statut.color()))
        return None

    def get_dossier(self, row: int) -> DossierReparation:
        return self._data[row]

    def reload(
        self,
        dossiers: list[DossierReparation],
        clients: dict[str, str] | None = None,
        vehicules: dict[str, str] | None = None,
    ) -> None:
        self.beginResetModel()
        self._data = dossiers
        self._clients = clients or {}
        self._vehicules = vehicules or {}
        self.endResetModel()


class _NouveauDossierDialog(QDialog):
    def __init__(self, ctx: AppContext, session: UserSession, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nouveau dossier de réparation")
        self.setMinimumWidth(460)
        self._ctx = ctx
        self._session = session
        self._clients_list: list = []
        self._vehicules_list: list = []

        form = QFormLayout(self)
        form.setSpacing(10)
        form.setContentsMargins(14, 14, 14, 14)

        self._client_cb = QComboBox()
        self._client_cb.setMinimumWidth(320)
        self._client_cb.currentIndexChanged.connect(self._on_client_change)
        form.addRow("Client * :", self._client_cb)

        self._vehicule_cb = QComboBox()
        form.addRow("Véhicule * :", self._vehicule_cb)

        self._km = QSpinBox()
        self._km.setRange(0, 9_999_999)
        self._km.setSuffix(" km")
        self._km.setSingleStep(100)
        form.addRow("Kilométrage entrée :", self._km)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

        self._load_clients()

    def _load_clients(self) -> None:
        try:
            self._clients_list = self._ctx.client_service.list_clients(self._session)
        except Exception:
            self._clients_list = []
        self._client_cb.clear()
        if not self._clients_list:
            self._client_cb.addItem("— Aucun client enregistré —")
            return
        for c in self._clients_list:
            label = f"{c.nom} {c.prenom}".strip()
            if c.telephone:
                label += f"  ({c.telephone})"
            self._client_cb.addItem(label, c.id)
        self._on_client_change(0)

    def _on_client_change(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._clients_list):
            self._vehicules_list = []
            self._vehicule_cb.clear()
            return
        client = self._clients_list[idx]
        try:
            self._vehicules_list = self._ctx.client_service.get_vehicules(self._session, client.id)
        except Exception:
            self._vehicules_list = []
        self._vehicule_cb.clear()
        if not self._vehicules_list:
            self._vehicule_cb.addItem("— Aucun véhicule pour ce client —")
            return
        for v in self._vehicules_list:
            year = f" ({v.annee})" if v.annee else ""
            self._vehicule_cb.addItem(
                f"{v.marque} {v.modele}{year} — {v.immatriculation}", v.id
            )

    def _on_ok(self) -> None:
        if not self._vehicules_list or self._vehicule_cb.currentData() is None:
            QMessageBox.warning(self, "Validation", "Veuillez sélectionner un véhicule.")
            return
        self.accept()

    @property
    def vehicule_id(self) -> uuid.UUID:
        return self._vehicule_cb.currentData()

    @property
    def client_id(self) -> uuid.UUID:
        return self._client_cb.currentData()

    @property
    def kilometrage(self) -> int:
        return self._km.value()


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
        self._model = _DossierModel()
        self._table_widget.set_source_model(self._model)
        self._table_widget.table.doubleClicked.connect(self._open_dossier)

        btn_row = QHBoxLayout()
        btn_new = QPushButton(_icon("new"), "+ Nouveau dossier")
        btn_new.clicked.connect(self._new_dossier)
        btn_row.addWidget(btn_new)
        btn_refresh = QPushButton(_icon("refresh"), "Actualiser")
        btn_refresh.clicked.connect(self._load)
        btn_row.addWidget(btn_refresh)
        btn_row.addStretch()
        self._count_lbl = QLabel()
        self._count_lbl.setStyleSheet("color:#555; font-size:10px;")
        btn_row.addWidget(self._count_lbl)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addLayout(btn_row)
        layout.addWidget(self._table_widget)
        self.setWidget(widget)
        self.resize(960, 520)

    def _load(self) -> None:
        dossiers = self._ctx.dossier_service.list_open(self._session)
        clients: dict[str, str] = {}
        vehicules: dict[str, str] = {}
        try:
            for c in self._ctx.client_service.list_clients(self._session):
                clients[str(c.id)] = f"{c.nom} {c.prenom}".strip()
            for row in self._ctx.analytics_service.parc_vehicules(self._session):
                vehicules[str(row["vehicule"].id)] = row["vehicule"].immatriculation
        except Exception:
            pass
        self._model.reload(dossiers, clients, vehicules)
        self._count_lbl.setText(f"{len(dossiers)} dossier(s) en cours")

    def _new_dossier(self) -> None:
        dlg = _NouveauDossierDialog(self._ctx, self._session, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            from garage_app.gui.atelier.dossier_window import DossierWindow
            dossier = self._ctx.dossier_service.ouvrir_dossier(
                self._session, dlg.vehicule_id, dlg.client_id, dlg.kilometrage
            )
            self._load()
            mdi = self.mdiArea()
            if mdi:
                open_sub(mdi, DossierWindow(self._ctx, self._session, dossier))
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _open_dossier(self, index) -> None:
        src_row = self._table_widget.proxy.mapToSource(index).row()
        dossier = self._model.get_dossier(src_row)
        from garage_app.gui.atelier.dossier_window import DossierWindow
        mdi = self.mdiArea()
        if mdi:
            open_sub(mdi, DossierWindow(self._ctx, self._session, dossier))
