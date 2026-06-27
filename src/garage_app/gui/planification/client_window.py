from __future__ import annotations

import uuid

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QAbstractItemView, QCheckBox, QDialog, QDialogButtonBox, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMdiSubWindow,
    QMessageBox, QPushButton, QSpinBox, QSplitter, QTableView,
    QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.planification.client import Client
from garage_app.domain.planification.vehicule import Vehicule
from garage_app.gui.widgets.searchable_table import SearchableTableWidget
from garage_app.gui.widgets.icon_helper import icon as _icon


# ── Client list model ────────────────────────────────────────────────────────

class _ClientModel(QAbstractTableModel):
    HEADERS = ["Nom", "Prénom", "Téléphone", "E-mail", "Flotte"]

    def __init__(self) -> None:
        super().__init__()
        self._data: list[Client] = []

    def reload(self, rows: list[Client]) -> None:
        self.beginResetModel()
        self._data = rows
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        c = self._data[index.row()]
        return [c.nom, c.prenom, c.telephone, c.email or "—",
                "Oui" if c.est_flotte else ""][index.column()]

    def get_client(self, row: int) -> Client:
        return self._data[row]


# ── Vehicle list model ───────────────────────────────────────────────────────

class _VehiculeModel(QAbstractTableModel):
    HEADERS = ["Marque", "Modèle", "Année", "Immatriculation", "VIN", "Couleur"]

    def __init__(self) -> None:
        super().__init__()
        self._data: list[Vehicule] = []

    def reload(self, rows: list[Vehicule]) -> None:
        self.beginResetModel()
        self._data = rows
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        v = self._data[index.row()]
        return [v.marque, v.modele, str(v.annee) if v.annee else "—",
                v.immatriculation, v.vin or "—", v.couleur or "—"][index.column()]

    def get_vehicule(self, row: int) -> Vehicule:
        return self._data[row]


# ── Vehicle dialog ───────────────────────────────────────────────────────────

class _VehiculeDialog(QDialog):
    def __init__(self, client_id: uuid.UUID, vehicule: Vehicule | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._client_id = client_id
        self._vehicule = vehicule
        self.setWindowTitle("Modifier véhicule" if vehicule else "Nouveau véhicule")
        self.setMinimumWidth(380)

        form = QFormLayout(self)
        form.setSpacing(8)

        self._marque = QLineEdit(vehicule.marque if vehicule else "")
        self._modele = QLineEdit(vehicule.modele if vehicule else "")
        self._annee = QSpinBox()
        self._annee.setRange(1900, 2100)
        self._annee.setValue(vehicule.annee if vehicule and vehicule.annee else 2020)
        self._immat = QLineEdit(vehicule.immatriculation if vehicule else "")
        self._immat.setPlaceholderText("ex. 123 TU 1234")
        self._vin = QLineEdit(vehicule.vin if vehicule else "")
        self._couleur = QLineEdit(vehicule.couleur if vehicule else "")

        form.addRow("Marque *", self._marque)
        form.addRow("Modèle *", self._modele)
        form.addRow("Année", self._annee)
        form.addRow("Immatriculation *", self._immat)
        form.addRow("VIN", self._vin)
        form.addRow("Couleur", self._couleur)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

        self._result: Vehicule | None = None

    def _on_accept(self) -> None:
        if not self._marque.text().strip():
            QMessageBox.warning(self, "Validation", "La marque est obligatoire.")
            return
        if not self._immat.text().strip():
            QMessageBox.warning(self, "Validation", "L'immatriculation est obligatoire.")
            return
        v = self._vehicule if self._vehicule else Vehicule(client_id=self._client_id)
        v.marque = self._marque.text().strip()
        v.modele = self._modele.text().strip()
        v.annee = self._annee.value()
        v.immatriculation = self._immat.text().strip().upper()
        v.vin = self._vin.text().strip()
        v.couleur = self._couleur.text().strip()
        self._result = v
        self.accept()

    @property
    def vehicule(self) -> Vehicule | None:
        return self._result


# ── Main window ──────────────────────────────────────────────────────────────

class ClientWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self._current_client: Client | None = None
        self.setWindowTitle("Clients & Véhicules")
        self._build_ui()
        self._load_clients()
        self.resize(1100, 620)

    def _build_ui(self) -> None:
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── Left: client list ────────────────────────────────────────────────
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(4, 4, 4, 4)
        lv.setSpacing(4)

        lv.addWidget(QLabel("<b>Clients</b>"))

        btn_row = QHBoxLayout()
        self._btn_new_client = QPushButton("+ Nouveau client")
        self._btn_new_client.setIcon(_icon("new"))
        self._btn_new_client.clicked.connect(self._new_client)
        btn_row.addWidget(self._btn_new_client)
        btn_row.addStretch()
        lv.addLayout(btn_row)

        self._client_table_w = SearchableTableWidget()
        self._client_model = _ClientModel()
        self._client_table_w.set_source_model(self._client_model)
        self._client_table_w.table.selectionModel().currentRowChanged.connect(self._on_client_select)
        lv.addWidget(self._client_table_w)

        splitter.addWidget(left)

        # ── Right: client detail + vehicles ─────────────────────────────────
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(6, 4, 4, 4)
        rv.setSpacing(8)

        # Client form
        grp_client = QGroupBox("Informations client")
        form = QFormLayout(grp_client)
        form.setSpacing(6)
        self._nom = QLineEdit()
        self._prenom = QLineEdit()
        self._tel = QLineEdit()
        self._email = QLineEdit()
        self._adresse = QLineEdit()
        self._flotte = QCheckBox("Client flotte (entreprise)")
        form.addRow("Nom *", self._nom)
        form.addRow("Prénom", self._prenom)
        form.addRow("Téléphone", self._tel)
        form.addRow("E-mail", self._email)
        form.addRow("Adresse", self._adresse)
        form.addRow("", self._flotte)

        client_btns = QHBoxLayout()
        self._btn_save_client = QPushButton("Enregistrer client")
        self._btn_save_client.setIcon(_icon("save"))
        self._btn_save_client.clicked.connect(self._save_client)
        client_btns.addStretch()
        client_btns.addWidget(self._btn_save_client)
        form.addRow(client_btns)
        rv.addWidget(grp_client)

        # Vehicle panel
        grp_veh = QGroupBox("Véhicules du client")
        vv = QVBoxLayout(grp_veh)

        veh_bar = QHBoxLayout()
        self._btn_add_veh = QPushButton("+ Ajouter véhicule")
        self._btn_add_veh.setIcon(_icon("new"))
        self._btn_add_veh.clicked.connect(self._add_vehicule)
        self._btn_add_veh.setEnabled(False)
        self._btn_edit_veh = QPushButton("Modifier")
        self._btn_edit_veh.setIcon(_icon("edit"))
        self._btn_edit_veh.clicked.connect(self._edit_vehicule)
        self._btn_edit_veh.setEnabled(False)
        self._btn_del_veh = QPushButton("Supprimer")
        self._btn_del_veh.setIcon(_icon("delete"))
        self._btn_del_veh.clicked.connect(self._delete_vehicule)
        self._btn_del_veh.setEnabled(False)
        veh_bar.addWidget(self._btn_add_veh)
        veh_bar.addWidget(self._btn_edit_veh)
        veh_bar.addStretch()
        veh_bar.addWidget(self._btn_del_veh)
        vv.addLayout(veh_bar)

        self._veh_model = _VehiculeModel()
        self._veh_table = QTableView()
        self._veh_table.setModel(self._veh_model)
        self._veh_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._veh_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._veh_table.verticalHeader().setVisible(False)
        self._veh_table.setAlternatingRowColors(True)
        self._veh_table.setColumnWidth(0, 100)
        self._veh_table.setColumnWidth(1, 100)
        self._veh_table.setColumnWidth(2, 60)
        self._veh_table.setColumnWidth(3, 120)
        self._veh_table.horizontalHeader().setStretchLastSection(True)
        self._veh_table.selectionModel().currentRowChanged.connect(self._on_veh_select)
        vv.addWidget(self._veh_table)
        rv.addWidget(grp_veh, stretch=1)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

        container = QWidget()
        QVBoxLayout(container).addWidget(splitter)
        self.setWidget(container)

    # ── Client operations ────────────────────────────────────────────────────

    def _load_clients(self) -> None:
        clients = self._ctx.client_service.list_clients(self._session)
        self._client_model.reload(clients)

    def _on_client_select(self, current, _) -> None:
        src_row = self._client_table_w.proxy.mapToSource(current).row()
        if src_row < 0:
            return
        self._current_client = self._client_model.get_client(src_row)
        self._fill_client_form(self._current_client)
        self._load_vehicules()
        self._btn_add_veh.setEnabled(True)

    def _new_client(self) -> None:
        self._current_client = None
        self._nom.clear()
        self._prenom.clear()
        self._tel.clear()
        self._email.clear()
        self._adresse.clear()
        self._flotte.setChecked(False)
        self._veh_model.reload([])
        self._btn_add_veh.setEnabled(False)
        self._btn_edit_veh.setEnabled(False)
        self._btn_del_veh.setEnabled(False)

    def _fill_client_form(self, c: Client) -> None:
        self._nom.setText(c.nom)
        self._prenom.setText(c.prenom)
        self._tel.setText(c.telephone)
        self._email.setText(c.email or "")
        self._adresse.setText(c.adresse or "")
        self._flotte.setChecked(c.est_flotte)

    def _save_client(self) -> None:
        nom = self._nom.text().strip()
        if not nom:
            QMessageBox.warning(self, "Validation", "Le nom est obligatoire.")
            return
        try:
            if self._current_client:
                self._current_client.nom = nom
                self._current_client.prenom = self._prenom.text().strip()
                self._current_client.telephone = self._tel.text().strip()
                self._current_client.email = self._email.text().strip()
                self._current_client.adresse = self._adresse.text().strip()
                self._current_client.est_flotte = self._flotte.isChecked()
                self._ctx.client_service.update_client(self._session, self._current_client)
            else:
                client = Client()
                client.nom = nom
                client.prenom = self._prenom.text().strip()
                client.telephone = self._tel.text().strip()
                client.email = self._email.text().strip()
                client.adresse = self._adresse.text().strip()
                client.est_flotte = self._flotte.isChecked()
                self._ctx.client_service.create_client(
                    self._session,
                    id=client.id,
                    nom=client.nom,
                    prenom=client.prenom,
                    telephone=client.telephone,
                    email=client.email,
                    adresse=client.adresse,
                    est_flotte=client.est_flotte,
                )
                self._current_client = client
            self._load_clients()
            self._btn_add_veh.setEnabled(True)
            QMessageBox.information(self, "Succès", "Client enregistré.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    # ── Vehicle operations ───────────────────────────────────────────────────

    def _load_vehicules(self) -> None:
        if not self._current_client:
            self._veh_model.reload([])
            return
        vehicules = self._ctx.client_service.get_vehicules(self._session, self._current_client.id)
        self._veh_model.reload(vehicules)
        self._btn_edit_veh.setEnabled(False)
        self._btn_del_veh.setEnabled(False)

    def _on_veh_select(self, current, _) -> None:
        valid = current.isValid() and current.row() >= 0
        self._btn_edit_veh.setEnabled(valid)
        self._btn_del_veh.setEnabled(valid)

    def _selected_vehicule(self) -> Vehicule | None:
        idx = self._veh_table.currentIndex()
        if not idx.isValid():
            return None
        return self._veh_model.get_vehicule(idx.row())

    def _add_vehicule(self) -> None:
        if not self._current_client:
            return
        dlg = _VehiculeDialog(self._current_client.id, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.vehicule:
            try:
                self._ctx.client_service.add_vehicule(self._session, dlg.vehicule)
                self._load_vehicules()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def _edit_vehicule(self) -> None:
        v = self._selected_vehicule()
        if not v or not self._current_client:
            return
        dlg = _VehiculeDialog(self._current_client.id, vehicule=v, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.vehicule:
            try:
                self._ctx.client_service.update_vehicule(self._session, dlg.vehicule)
                self._load_vehicules()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def _delete_vehicule(self) -> None:
        v = self._selected_vehicule()
        if not v:
            return
        rep = QMessageBox.question(
            self, "Supprimer",
            f"Supprimer le véhicule {v.immatriculation} ({v.marque} {v.modele}) ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep == QMessageBox.StandardButton.Yes:
            try:
                self._ctx.client_service.delete_vehicule(self._session, v.id)
                self._load_vehicules()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))
