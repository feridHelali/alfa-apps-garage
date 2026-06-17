from __future__ import annotations

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMdiSubWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.planification.client import Client
from garage_app.gui.widgets.master_detail_widget import MasterDetailWidget
from garage_app.gui.widgets.searchable_table import SearchableTableWidget


class _ClientModel(QAbstractTableModel):
    HEADERS = ["Nom", "Prénom", "Téléphone", "Email", "Flotte"]

    def __init__(self, clients: list[Client]) -> None:
        super().__init__()
        self._data = clients

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
        return [c.nom, c.prenom, c.telephone, c.email, "Oui" if c.est_flotte else ""][index.column()]

    def get_client(self, row: int) -> Client:
        return self._data[row]

    def reload(self, clients: list[Client]) -> None:
        self.beginResetModel()
        self._data = clients
        self.endResetModel()


class ClientWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self.setWindowTitle("Clients")
        self.setWindowIcon(QIcon.fromTheme("system-users"))
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        # Master
        self._search_table = SearchableTableWidget()
        self._model = _ClientModel([])
        self._search_table.set_source_model(self._model)
        self._search_table.table.selectionModel().currentRowChanged.connect(self._on_select)

        master_panel = QWidget()
        mv = QVBoxLayout(master_panel)
        mv.setContentsMargins(4, 4, 4, 4)
        btn_row = QHBoxLayout()
        self._btn_new = QPushButton(QIcon.fromTheme("list-add"), "Nouveau")
        self._btn_new.clicked.connect(self._new_client)
        btn_row.addWidget(self._btn_new)
        btn_row.addStretch()
        mv.addLayout(btn_row)
        mv.addWidget(self._search_table)

        # Detail
        self._detail = _ClientDetailForm()
        self._detail.saved.connect(self._save_client)

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        splitter = MasterDetailWidget(master_panel, self._detail)
        layout.addWidget(splitter)
        self.setWidget(widget)
        self.resize(900, 550)

    def _load(self) -> None:
        clients = self._ctx.client_service.list_clients(self._session)
        self._model.reload(clients)

    def _on_select(self, current, _previous) -> None:
        src_row = self._search_table.proxy.mapToSource(current).row()
        if src_row >= 0:
            self._detail.load(self._model.get_client(src_row))

    def _new_client(self) -> None:
        self._detail.clear()

    def _save_client(self, client: Client) -> None:
        try:
            self._ctx.client_service.update_client(self._session, client)
            self._load()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", str(e))


from PyQt6.QtCore import pyqtSignal


class _ClientDetailForm(QWidget):
    saved = pyqtSignal(Client)

    def __init__(self) -> None:
        super().__init__()
        self._client: Client | None = None
        form = QFormLayout(self)
        self._nom = QLineEdit()
        self._prenom = QLineEdit()
        self._tel = QLineEdit()
        self._email = QLineEdit()
        self._adresse = QLineEdit()
        form.addRow("Nom :", self._nom)
        form.addRow("Prénom :", self._prenom)
        form.addRow("Téléphone :", self._tel)
        form.addRow("Email :", self._email)
        form.addRow("Adresse :", self._adresse)
        btn = QPushButton(QIcon.fromTheme("document-save"), "Enregistrer")
        btn.clicked.connect(self._on_save)
        form.addRow(btn)

    def load(self, client: Client) -> None:
        self._client = client
        self._nom.setText(client.nom)
        self._prenom.setText(client.prenom)
        self._tel.setText(client.telephone)
        self._email.setText(client.email)
        self._adresse.setText(client.adresse)

    def clear(self) -> None:
        self._client = Client()
        self._nom.clear(); self._prenom.clear(); self._tel.clear()
        self._email.clear(); self._adresse.clear()

    def _on_save(self) -> None:
        if not self._client:
            self._client = Client()
        self._client.nom = self._nom.text().strip()
        self._client.prenom = self._prenom.text().strip()
        self._client.telephone = self._tel.text().strip()
        self._client.email = self._email.text().strip()
        self._client.adresse = self._adresse.text().strip()
        self.saved.emit(self._client)
