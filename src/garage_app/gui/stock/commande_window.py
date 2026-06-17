from __future__ import annotations

import uuid
from datetime import datetime

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QDate
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QDateEdit, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMdiSubWindow, QMessageBox, QPushButton,
    QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.stock.commande_fournisseur import CommandeFournisseur, LigneCommande, StatutCommande
from garage_app.gui.widgets.searchable_table import SearchableTableWidget
from garage_app.gui.widgets.status_badge import StatusBadge

_STATUT_COLORS = {
    StatutCommande.BROUILLON:           ("#5D5D5D", "#F3F3F3"),
    StatutCommande.ENVOYEE:             ("#0067C0", "#EEF4FB"),
    StatutCommande.PARTIELLEMENT_RECUE: ("#7A4F00", "#FFF4CE"),
    StatutCommande.RECUE:               ("#107C10", "#DFF6DD"),
    StatutCommande.ANNULEE:             ("#A4262C", "#FDE7E9"),
}

_STATUT_LABELS = {
    StatutCommande.BROUILLON:           "Brouillon",
    StatutCommande.ENVOYEE:             "Envoyée",
    StatutCommande.PARTIELLEMENT_RECUE: "Partielle",
    StatutCommande.RECUE:               "Reçue",
    StatutCommande.ANNULEE:             "Annulée",
}


class _CommandeListModel(QAbstractTableModel):
    HEADERS = ["Date", "Fournisseur", "Lignes", "Statut"]

    def __init__(self, rows: list[CommandeFournisseur]) -> None:
        super().__init__()
        self._data = rows
        self._fournisseurs: dict[str, str] = {}

    def set_fournisseurs(self, mapping: dict[str, str]) -> None:
        self._fournisseurs = mapping

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
        c = self._data[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            nom = self._fournisseurs.get(str(c.fournisseur_id), str(c.fournisseur_id)[:8])
            return [
                c.date_commande.strftime("%d/%m/%Y"),
                nom,
                str(len(c.lignes)),
                _STATUT_LABELS.get(c.statut, c.statut),
            ][col]
        if role == Qt.ItemDataRole.ForegroundRole and col == 3:
            fg, _ = _STATUT_COLORS.get(c.statut, ("#1A1A1A", "#FFFFFF"))
            return QBrush(QColor(fg))
        if role == Qt.ItemDataRole.BackgroundRole and col == 3:
            _, bg = _STATUT_COLORS.get(c.statut, ("#1A1A1A", "#FFFFFF"))
            return QBrush(QColor(bg))
        return None

    def get_commande(self, row: int) -> CommandeFournisseur:
        return self._data[row]

    def reload(self, rows: list[CommandeFournisseur]) -> None:
        self.beginResetModel()
        self._data = rows
        self.endResetModel()


class CommandeWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self._current: CommandeFournisseur | None = None
        self.setWindowTitle("Commandes fournisseurs")
        self._build_ui()
        self._load()

    def status_info(self) -> str:
        total = len(self._model._data)
        ouvertes = sum(
            1 for c in self._model._data
            if c.statut in (StatutCommande.BROUILLON, StatutCommande.ENVOYEE,
                            StatutCommande.PARTIELLEMENT_RECUE)
        )
        return f"Commandes — {total} total  |  {ouvertes} en cours"

    def _build_ui(self) -> None:
        main = QWidget()
        layout = QVBoxLayout(main)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # ── toolbar ─────────────────────────────────────────────────────────
        bar = QHBoxLayout()
        btn_new = QPushButton("+ Nouvelle commande")
        btn_new.clicked.connect(self._new_commande)
        bar.addWidget(btn_new)
        bar.addStretch()
        layout.addLayout(bar)

        # ── list ────────────────────────────────────────────────────────────
        self._table_w = SearchableTableWidget()
        self._model = _CommandeListModel([])
        self._table_w.set_source_model(self._model)
        self._table_w.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table_w.table.selectionModel().currentRowChanged.connect(self._on_select)
        layout.addWidget(self._table_w, stretch=2)

        # ── detail ──────────────────────────────────────────────────────────
        self._detail = _CommandeDetailPanel()
        self._detail.action_envoyer.connect(self._envoyer)
        self._detail.action_recevoir_tout.connect(self._recevoir_tout)
        self._detail.action_annuler.connect(self._annuler)
        layout.addWidget(self._detail, stretch=3)

        self.setWidget(main)
        self.resize(1000, 680)

    def _load(self) -> None:
        commandes = self._ctx.commande_service.list_commandes(self._session)
        fournisseurs = {
            str(f.id): f.raison_sociale
            for f in self._ctx.fournisseur_service.list_fournisseurs(self._session)
        }
        self._model.set_fournisseurs(fournisseurs)
        self._model.reload(commandes)

    def _on_select(self, current, _) -> None:
        src_row = self._table_w.proxy.mapToSource(current).row()
        if src_row >= 0:
            self._current = self._model.get_commande(src_row)
            fournisseurs = {
                str(f.id): f.raison_sociale
                for f in self._ctx.fournisseur_service.list_fournisseurs(self._session)
            }
            self._detail.load(self._current, fournisseurs)

    def _new_commande(self) -> None:
        fournisseurs = self._ctx.fournisseur_service.list_fournisseurs(
            self._session, actifs_seulement=True
        )
        pieces = self._ctx.stock_service.list_pieces(self._session)
        if not fournisseurs:
            QMessageBox.information(self, "Info", "Aucun fournisseur actif. Créez-en un d'abord.")
            return
        dlg = _NouvelleCommandeDialog(fournisseurs, pieces, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self._ctx.commande_service.create_commande(
                    self._session,
                    fournisseur_id=dlg.fournisseur_id,
                    lignes=dlg.lignes,
                    notes=dlg.notes,
                )
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def _envoyer(self) -> None:
        if not self._current:
            return
        try:
            self._ctx.commande_service.envoyer_commande(self._session, self._current.id)
            self._load()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _recevoir_tout(self) -> None:
        if not self._current:
            return
        rep = QMessageBox.question(
            self, "Confirmer",
            "Marquer toutes les lignes comme reçues et mettre à jour le stock ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep == QMessageBox.StandardButton.Yes:
            try:
                self._ctx.commande_service.recevoir_tout(self._session, self._current.id)
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def _annuler(self) -> None:
        if not self._current:
            return
        rep = QMessageBox.question(
            self, "Confirmer", "Annuler cette commande ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep == QMessageBox.StandardButton.Yes:
            try:
                self._ctx.commande_service.annuler_commande(self._session, self._current.id)
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))


class _CommandeDetailPanel(QWidget):
    from PyQt6.QtCore import pyqtSignal
    action_envoyer = pyqtSignal()
    action_recevoir_tout = pyqtSignal()
    action_annuler = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # header
        hdr = QHBoxLayout()
        self._lbl_fourn = QLabel("—")
        self._lbl_fourn.setStyleSheet("font-weight: 700; font-size: 11pt;")
        self._lbl_statut = QLabel("")
        hdr.addWidget(self._lbl_fourn)
        hdr.addStretch()
        hdr.addWidget(QLabel("Statut :"))
        hdr.addWidget(self._lbl_statut)
        layout.addLayout(hdr)

        # lines table
        grp = QGroupBox("Lignes de commande")
        gv = QVBoxLayout(grp)
        self._lines_tbl = QTableWidget(0, 4)
        self._lines_tbl.setHorizontalHeaderLabels(["Pièce", "Commandé", "Reçu", "Prix HT"])
        self._lines_tbl.horizontalHeader().setStretchLastSection(True)
        self._lines_tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._lines_tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._lines_tbl.verticalHeader().setVisible(False)
        self._lines_tbl.setAlternatingRowColors(True)
        gv.addWidget(self._lines_tbl)
        layout.addWidget(grp)

        # notes
        self._lbl_notes = QLabel("")
        self._lbl_notes.setWordWrap(True)
        layout.addWidget(self._lbl_notes)

        # action buttons
        btn_row = QHBoxLayout()
        self._btn_envoyer = QPushButton("Envoyer")
        self._btn_envoyer.setDefault(True)
        self._btn_recevoir = QPushButton("Recevoir tout")
        self._btn_annuler = QPushButton("Annuler commande")
        self._btn_envoyer.clicked.connect(self.action_envoyer)
        self._btn_recevoir.clicked.connect(self.action_recevoir_tout)
        self._btn_annuler.clicked.connect(self.action_annuler)
        btn_row.addWidget(self._btn_envoyer)
        btn_row.addWidget(self._btn_recevoir)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_annuler)
        layout.addLayout(btn_row)

        self._set_buttons_state(None)

    def load(self, c: CommandeFournisseur, fournisseurs: dict[str, str]) -> None:
        nom = fournisseurs.get(str(c.fournisseur_id), str(c.fournisseur_id)[:8])
        self._lbl_fourn.setText(f"{nom}  —  {c.date_commande.strftime('%d/%m/%Y')}")
        label = _STATUT_LABELS.get(c.statut, c.statut)
        fg, bg = _STATUT_COLORS.get(c.statut, ("#1A1A1A", "#F3F3F3"))
        self._lbl_statut.setText(f" {label} ")
        self._lbl_statut.setStyleSheet(
            f"color: {fg}; background: {bg}; border-radius: 4px; padding: 2px 8px; font-weight: 600;"
        )
        self._lines_tbl.setRowCount(len(c.lignes))
        for row, ligne in enumerate(c.lignes):
            self._lines_tbl.setItem(row, 0, QTableWidgetItem(ligne.designation or str(ligne.piece_id)[:8]))
            self._lines_tbl.setItem(row, 1, QTableWidgetItem(str(ligne.quantite_commandee)))
            item_recu = QTableWidgetItem(str(ligne.quantite_recue))
            if ligne.est_recue:
                item_recu.setForeground(QBrush(QColor("#107C10")))
            self._lines_tbl.setItem(row, 2, item_recu)
            self._lines_tbl.setItem(row, 3, QTableWidgetItem(f"{ligne.prix_unitaire:.3f} DT"))
        self._lbl_notes.setText(f"Notes : {c.notes}" if c.notes else "")
        self._set_buttons_state(c.statut)

    def _set_buttons_state(self, statut: StatutCommande | None) -> None:
        self._btn_envoyer.setEnabled(statut == StatutCommande.BROUILLON)
        self._btn_recevoir.setEnabled(statut in (StatutCommande.ENVOYEE, StatutCommande.PARTIELLEMENT_RECUE))
        self._btn_annuler.setEnabled(statut in (StatutCommande.BROUILLON, StatutCommande.ENVOYEE))


class _NouvelleCommandeDialog(QDialog):
    def __init__(self, fournisseurs, pieces, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nouvelle commande fournisseur")
        self.setMinimumWidth(640)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self._fourn_cb = QComboBox()
        for f in fournisseurs:
            self._fourn_cb.addItem(f.raison_sociale, str(f.id))
        self._date_livr = QDateEdit(QDate.currentDate().addDays(7))
        self._date_livr.setCalendarPopup(True)
        self._notes = QLineEdit()
        form.addRow("Fournisseur *", self._fourn_cb)
        form.addRow("Livraison prévue", self._date_livr)
        form.addRow("Notes", self._notes)
        layout.addLayout(form)

        # Lines editor
        grp = QGroupBox("Lignes")
        gv = QVBoxLayout(grp)
        self._lines_tbl = QTableWidget(0, 4)
        self._lines_tbl.setHorizontalHeaderLabels(["Pièce", "Quantité", "Prix HT (DT)", ""])
        self._lines_tbl.horizontalHeader().setStretchLastSection(True)
        self._lines_tbl.verticalHeader().setVisible(False)
        gv.addWidget(self._lines_tbl)
        self._pieces = pieces

        add_btn = QPushButton("+ Ajouter une ligne")
        add_btn.clicked.connect(self._add_line)
        gv.addWidget(add_btn)
        layout.addWidget(grp)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self._fournisseur_id: uuid.UUID | None = None
        self._lignes: list[tuple[uuid.UUID, str, int, float]] = []
        self._notes_val = ""
        self._add_line()

    def _add_line(self) -> None:
        row = self._lines_tbl.rowCount()
        self._lines_tbl.insertRow(row)
        cb = QComboBox()
        for p in self._pieces:
            cb.addItem(f"{p.reference_constructeur} — {p.designation}", str(p.id))
        self._lines_tbl.setCellWidget(row, 0, cb)
        spin_qte = QSpinBox()
        spin_qte.setRange(1, 9999)
        self._lines_tbl.setCellWidget(row, 1, spin_qte)
        spin_prix = QDoubleSpinBox()
        spin_prix.setRange(0, 999999)
        spin_prix.setDecimals(3)
        self._lines_tbl.setCellWidget(row, 2, spin_prix)
        del_btn = QPushButton("✕")
        del_btn.setFixedWidth(28)
        del_btn.clicked.connect(lambda _, r=row: self._remove_line(r))
        self._lines_tbl.setCellWidget(row, 3, del_btn)

    def _remove_line(self, row: int) -> None:
        self._lines_tbl.removeRow(row)

    def _on_accept(self) -> None:
        if self._lines_tbl.rowCount() == 0:
            QMessageBox.warning(self, "Validation", "Ajoutez au moins une ligne.")
            return
        self._fournisseur_id = uuid.UUID(self._fourn_cb.currentData())
        self._notes_val = self._notes.text().strip()
        self._lignes = []
        for row in range(self._lines_tbl.rowCount()):
            cb = self._lines_tbl.cellWidget(row, 0)
            spin_q = self._lines_tbl.cellWidget(row, 1)
            spin_p = self._lines_tbl.cellWidget(row, 2)
            piece_id = uuid.UUID(cb.currentData())
            desig = cb.currentText().split(" — ", 1)[-1] if " — " in cb.currentText() else cb.currentText()
            self._lignes.append((piece_id, desig, spin_q.value(), spin_p.value()))
        self.accept()

    @property
    def fournisseur_id(self) -> uuid.UUID:
        return self._fournisseur_id  # type: ignore[return-value]

    @property
    def lignes(self) -> list[tuple[uuid.UUID, str, int, float]]:
        return self._lignes

    @property
    def notes(self) -> str:
        return self._notes_val
