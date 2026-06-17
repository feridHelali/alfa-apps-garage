from __future__ import annotations

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMdiSubWindow,
    QMessageBox, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.stock.fournisseur import Fournisseur
from garage_app.gui.widgets.master_detail_widget import MasterDetailWidget
from garage_app.gui.widgets.searchable_table import SearchableTableWidget


class _FournisseurModel(QAbstractTableModel):
    HEADERS = ["Raison sociale", "Contact", "Téléphone", "E-mail", "Délai (j)", "Actif"]

    def __init__(self, rows: list[Fournisseur]) -> None:
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
        f = self._data[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return [
                f.raison_sociale, f.contact_nom, f.telephone,
                f.email, str(f.delai_livraison_jours),
                "Oui" if f.est_actif else "Non",
            ][index.column()]
        if role == Qt.ItemDataRole.ForegroundRole and index.column() == 5:
            return QBrush(QColor("#107C10") if f.est_actif else QColor("#A4262C"))
        return None

    def get_fournisseur(self, row: int) -> Fournisseur:
        return self._data[row]

    def reload(self, rows: list[Fournisseur]) -> None:
        self.beginResetModel()
        self._data = rows
        self.endResetModel()


class FournisseurWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self._current: Fournisseur | None = None
        self.setWindowTitle("Fournisseurs")
        self._build_ui()
        self._load()

    def status_info(self) -> str:
        return f"Fournisseurs — {len(self._model._data)} enregistrés"

    def _build_ui(self) -> None:
        # ── master ──────────────────────────────────────────────────────────
        master = QWidget()
        mv = QVBoxLayout(master)
        mv.setContentsMargins(4, 4, 4, 4)
        mv.setSpacing(4)

        btn_row = QHBoxLayout()
        self._btn_new = QPushButton("+ Nouveau")
        self._btn_new.clicked.connect(self._new_fournisseur)
        self._btn_toggle = QPushButton("Désactiver")
        self._btn_toggle.clicked.connect(self._toggle_actif)
        self._btn_toggle.setEnabled(False)
        btn_row.addWidget(self._btn_new)
        btn_row.addWidget(self._btn_toggle)
        btn_row.addStretch()
        mv.addLayout(btn_row)

        self._table_w = SearchableTableWidget()
        self._model = _FournisseurModel([])
        self._table_w.set_source_model(self._model)
        self._table_w.table.selectionModel().currentRowChanged.connect(self._on_select)
        mv.addWidget(self._table_w)

        # ── detail ──────────────────────────────────────────────────────────
        self._detail = _FournisseurDetailForm()
        self._detail.saved.connect(self._on_save)

        container = QWidget()
        QHBoxLayout(container).addWidget(MasterDetailWidget(master, self._detail))
        self.setWidget(container)
        self.resize(1000, 560)

    def _load(self) -> None:
        rows = self._ctx.fournisseur_service.list_fournisseurs(self._session)
        self._model.reload(rows)

    def _on_select(self, current, _) -> None:
        src_row = self._table_w.proxy.mapToSource(current).row()
        if src_row >= 0:
            self._current = self._model.get_fournisseur(src_row)
            self._detail.load(self._current)
            self._btn_toggle.setEnabled(True)
            self._btn_toggle.setText("Désactiver" if self._current.est_actif else "Réactiver")

    def _new_fournisseur(self) -> None:
        self._current = None
        self._detail.clear()
        self._btn_toggle.setEnabled(False)

    def _on_save(self, f: Fournisseur) -> None:
        try:
            if self._current and f.id == self._current.id:
                self._ctx.fournisseur_service.update_fournisseur(self._session, f)
            else:
                self._ctx.fournisseur_service.create_fournisseur(self._session, f)
            self._load()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _toggle_actif(self) -> None:
        if not self._current:
            return
        try:
            if self._current.est_actif:
                self._ctx.fournisseur_service.desactiver_fournisseur(self._session, self._current.id)
            else:
                self._ctx.fournisseur_service.activer_fournisseur(self._session, self._current.id)
            self._load()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))


class _FournisseurDetailForm(QWidget):
    from PyQt6.QtCore import pyqtSignal
    saved = pyqtSignal(object)

    def __init__(self) -> None:
        super().__init__()
        self._fournisseur: Fournisseur | None = None
        form = QFormLayout(self)
        form.setContentsMargins(12, 12, 12, 12)
        form.setSpacing(8)

        self._raison = QLineEdit()
        self._contact = QLineEdit()
        self._tel = QLineEdit()
        self._email = QLineEdit()
        self._adresse = QLineEdit()
        self._delai = QSpinBox()
        self._delai.setRange(1, 365)
        self._delai.setSuffix(" jours")

        form.addRow("Raison sociale *", self._raison)
        form.addRow("Contact", self._contact)
        form.addRow("Téléphone", self._tel)
        form.addRow("E-mail", self._email)
        form.addRow("Adresse", self._adresse)
        form.addRow("Délai livraison", self._delai)

        btn_save = QPushButton("Enregistrer")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save)
        form.addRow("", btn_save)

    def load(self, f: Fournisseur) -> None:
        self._fournisseur = f
        self._raison.setText(f.raison_sociale)
        self._contact.setText(f.contact_nom)
        self._tel.setText(f.telephone)
        self._email.setText(f.email)
        self._adresse.setText(f.adresse)
        self._delai.setValue(f.delai_livraison_jours)

    def clear(self) -> None:
        self._fournisseur = None
        for w in [self._raison, self._contact, self._tel, self._email, self._adresse]:
            w.clear()
        self._delai.setValue(7)

    def _save(self) -> None:
        raison = self._raison.text().strip()
        if not raison:
            QMessageBox.warning(self, "Validation", "La raison sociale est obligatoire.")
            return
        if self._fournisseur:
            f = self._fournisseur
        else:
            f = Fournisseur()
        f.raison_sociale = raison
        f.contact_nom = self._contact.text().strip()
        f.telephone = self._tel.text().strip()
        f.email = self._email.text().strip()
        f.adresse = self._adresse.text().strip()
        f.delai_livraison_jours = self._delai.value()
        self.saved.emit(f)
