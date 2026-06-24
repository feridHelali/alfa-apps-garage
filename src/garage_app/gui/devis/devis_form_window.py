"""DevisFormWindow — create or edit a commercial devis."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal, InvalidOperation

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMessageBox, QPushButton, QSpinBox, QSplitter,
    QTableView, QTextEdit, QVBoxLayout, QWidget,
)
from PyQt6.QtCore import QDate

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.devis.devis import Devis, LigneDevis
from garage_app.domain.devis.statut_devis import StatutDevis, TypeLigne
from garage_app.domain.shared.value_objects import Money


class _LignesModel(QAbstractTableModel):
    HEADERS = ["Type", "Désignation", "Qté", "PU HT (DT)", "TVA %", "Remise %", "Total HT"]

    def __init__(self) -> None:
        super().__init__()
        self._lignes: list[LigneDevis] = []

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._lignes)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        l = self._lignes[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            return [
                l.type_ligne.label_fr(),
                l.designation,
                str(l.quantite),
                l.prix_unitaire_ht.format(),
                f"{float(l.taux_tva) * 100:.0f}%",
                f"{float(l.remise_pct) * 100:.0f}%",
                l.montant_ht.format(),
            ][col]
        if role == Qt.ItemDataRole.TextAlignmentRole and col in (2, 3, 4, 5, 6):
            return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        return None

    def get_ligne(self, row: int) -> LigneDevis:
        return self._lignes[row]

    def reload(self, lignes: list[LigneDevis]) -> None:
        self.beginResetModel()
        self._lignes = list(lignes)
        self.endResetModel()

    def add(self, ligne: LigneDevis) -> None:
        self.beginInsertRows(QModelIndex(), len(self._lignes), len(self._lignes))
        self._lignes.append(ligne)
        self.endInsertRows()

    def remove(self, row: int) -> None:
        if 0 <= row < len(self._lignes):
            self.beginRemoveRows(QModelIndex(), row, row)
            self._lignes.pop(row)
            self.endRemoveRows()

    def all_lignes(self) -> list[LigneDevis]:
        return list(self._lignes)


class _AddLigneDialog(QDialog):
    """Simple dialog to add/edit a devis line."""

    def __init__(self, devis_id: uuid.UUID, parent=None, ligne: LigneDevis | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ligne de devis")
        self.setMinimumWidth(420)
        self._devis_id = devis_id
        self._result: LigneDevis | None = None

        form = QFormLayout(self)

        self._type = QComboBox()
        for t in TypeLigne:
            self._type.addItem(t.label_fr(), t)

        self._designation = QLineEdit()
        self._designation.setPlaceholderText("Ex : Vidange moteur")

        self._qte = QDoubleSpinBox()
        self._qte.setDecimals(3)
        self._qte.setRange(0.001, 99999)
        self._qte.setValue(1)

        self._pu = QDoubleSpinBox()
        self._pu.setDecimals(3)
        self._pu.setRange(0, 999999)
        self._pu.setSuffix(" DT")

        self._tva = QDoubleSpinBox()
        self._tva.setDecimals(0)
        self._tva.setRange(0, 100)
        self._tva.setValue(19)
        self._tva.setSuffix(" %")

        self._remise = QDoubleSpinBox()
        self._remise.setDecimals(1)
        self._remise.setRange(0, 100)
        self._remise.setSuffix(" %")

        if ligne:
            for i in range(self._type.count()):
                if self._type.itemData(i) == ligne.type_ligne:
                    self._type.setCurrentIndex(i)
            self._designation.setText(ligne.designation)
            self._qte.setValue(float(ligne.quantite))
            self._pu.setValue(float(ligne.prix_unitaire_ht.amount))
            self._tva.setValue(float(ligne.taux_tva) * 100)
            self._remise.setValue(float(ligne.remise_pct) * 100)

        form.addRow("Type :", self._type)
        form.addRow("Désignation :", self._designation)
        form.addRow("Quantité :", self._qte)
        form.addRow("Prix unitaire HT :", self._pu)
        form.addRow("TVA :", self._tva)
        form.addRow("Remise :", self._remise)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def _validate(self) -> None:
        if not self._designation.text().strip():
            QMessageBox.warning(self, "Erreur", "La désignation est obligatoire.")
            return
        self._result = LigneDevis(
            devis_id=self._devis_id,
            type_ligne=self._type.currentData(),
            designation=self._designation.text().strip(),
            quantite=Decimal(str(self._qte.value())),
            prix_unitaire_ht=Money(Decimal(str(self._pu.value()))),
            taux_tva=Decimal(str(self._tva.value() / 100)),
            remise_pct=Decimal(str(self._remise.value() / 100)),
        )
        self.accept()

    def get_ligne(self) -> LigneDevis | None:
        return self._result


class DevisFormWindow(QDialog):
    """Create or edit a commercial Devis."""

    def __init__(
        self,
        ctx: AppContext,
        session: UserSession,
        devis: Devis | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._ctx = ctx
        self._session = session
        self._devis = devis
        self._clients_list: list = []
        self._vehicules_list: list = []
        self._read_only = devis is not None and not devis.statut.peut_modifier()

        self.setWindowTitle("Modifier le devis" if devis else "Nouveau devis")
        self.setMinimumSize(800, 580)

        root = QVBoxLayout(self)

        # En-tête
        header_grp = QGroupBox("Informations")
        hform = QFormLayout(header_grp)

        self._client_combo = QComboBox()
        self._client_combo.setMinimumWidth(200)
        self._client_combo.currentIndexChanged.connect(self._on_client_changed)

        self._vehicule_combo = QComboBox()

        self._date_exp = QDateEdit()
        self._date_exp.setCalendarPopup(True)
        self._date_exp.setSpecialValueText("Pas d'expiration")
        self._date_exp.setDate(QDate.currentDate().addDays(30))
        self._date_exp.setDisplayFormat("dd/MM/yyyy")

        self._notes_client = QTextEdit()
        self._notes_client.setMaximumHeight(60)
        self._notes_client.setPlaceholderText("Description des travaux demandés par le client…")

        self._notes_internes = QTextEdit()
        self._notes_internes.setMaximumHeight(60)
        self._notes_internes.setPlaceholderText("Notes internes (non imprimées)…")

        hform.addRow("Client :", self._client_combo)
        hform.addRow("Véhicule :", self._vehicule_combo)
        hform.addRow("Expiration :", self._date_exp)
        hform.addRow("Notes client :", self._notes_client)
        hform.addRow("Notes internes :", self._notes_internes)
        root.addWidget(header_grp)

        # Lignes
        lines_grp = QGroupBox("Lignes du devis")
        lines_layout = QVBoxLayout(lines_grp)

        self._lignes_model = _LignesModel()
        self._table = QTableView()
        self._table.setModel(self._lignes_model)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.setMinimumHeight(160)
        lines_layout.addWidget(self._table)

        line_btns = QHBoxLayout()
        self._btn_add_line = QPushButton("+ Ajouter")
        self._btn_edit_line = QPushButton("Modifier")
        self._btn_del_line = QPushButton("Supprimer")
        line_btns.addWidget(self._btn_add_line)
        line_btns.addWidget(self._btn_edit_line)
        line_btns.addWidget(self._btn_del_line)
        line_btns.addStretch()

        # totals summary
        self._lbl_ht = QLabel("HT : 0,000 DT")
        self._lbl_ttc = QLabel("TTC : 0,000 DT")
        self._lbl_ht.setStyleSheet("font-weight:bold;")
        self._lbl_ttc.setStyleSheet("font-weight:bold; color:#0055a5; font-size:11pt;")
        line_btns.addWidget(self._lbl_ht)
        line_btns.addWidget(self._lbl_ttc)
        lines_layout.addLayout(line_btns)
        root.addWidget(lines_grp)

        self._btn_add_line.clicked.connect(self._add_line)
        self._btn_edit_line.clicked.connect(self._edit_line)
        self._btn_del_line.clicked.connect(self._del_line)
        self._lignes_model.dataChanged.connect(self._refresh_totals)

        # dialog buttons
        btns = QDialogButtonBox()
        if not self._read_only:
            btns.addButton("Enregistrer", QDialogButtonBox.ButtonRole.AcceptRole)
        btns.addButton(
            "Fermer" if self._read_only else "Annuler",
            QDialogButtonBox.ButtonRole.RejectRole,
        )
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

        self._load_clients()
        if devis:
            self._populate(devis)
        if self._read_only:
            self._set_readonly()

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _load_clients(self) -> None:
        try:
            self._clients_list = self._ctx.client_service.list_clients(self._session)
        except Exception:
            self._clients_list = []
        self._client_combo.clear()
        self._client_combo.addItem("— Sélectionner —", None)
        for c in self._clients_list:
            self._client_combo.addItem(f"{c.nom} {c.prenom} ({c.telephone})", c.id)

    def _on_client_changed(self) -> None:
        client_id = self._client_combo.currentData()
        self._vehicule_combo.clear()
        self._vehicule_combo.addItem("— Sélectionner —", None)
        if not client_id:
            return
        try:
            vehicules = self._ctx.client_service.get_vehicules(self._session, client_id)
            self._vehicules_list = vehicules
            for v in vehicules:
                self._vehicule_combo.addItem(
                    f"{v.immatriculation} — {v.marque} {v.modele}", v.id
                )
        except Exception:
            pass

    def _populate(self, d: Devis) -> None:
        # client
        for i in range(self._client_combo.count()):
            if self._client_combo.itemData(i) == d.client_id:
                self._client_combo.setCurrentIndex(i)
                break
        # vehicule (after _on_client_changed loads them)
        if d.vehicule_id:
            for i in range(self._vehicule_combo.count()):
                if self._vehicule_combo.itemData(i) == d.vehicule_id:
                    self._vehicule_combo.setCurrentIndex(i)
                    break
        if d.date_expiration:
            self._date_exp.setDate(
                QDate(d.date_expiration.year, d.date_expiration.month, d.date_expiration.day)
            )
        self._notes_client.setPlainText(d.notes_client)
        self._notes_internes.setPlainText(d.notes_internes)
        self._lignes_model.reload(d.lignes)
        self._refresh_totals()

    def _set_readonly(self) -> None:
        self._client_combo.setEnabled(False)
        self._vehicule_combo.setEnabled(False)
        self._date_exp.setEnabled(False)
        self._notes_client.setReadOnly(True)
        self._notes_internes.setReadOnly(True)
        self._btn_add_line.setEnabled(False)
        self._btn_edit_line.setEnabled(False)
        self._btn_del_line.setEnabled(False)

    def _refresh_totals(self) -> None:
        lignes = self._lignes_model.all_lignes()
        ht = sum((float(l.montant_ht.amount) for l in lignes), 0.0)
        ttc = sum((float(l.montant_ttc.amount) for l in lignes), 0.0)
        self._lbl_ht.setText(f"HT : {ht:,.3f} DT".replace(",", " ").replace(".", ","))
        self._lbl_ttc.setText(f"TTC : {ttc:,.3f} DT".replace(",", " ").replace(".", ","))

    # ── Line actions ────────────────────────────────────────────────────────

    def _add_line(self) -> None:
        devis_id = self._devis.id if self._devis else uuid.uuid4()
        dlg = _AddLigneDialog(devis_id, parent=self)
        if dlg.exec():
            l = dlg.get_ligne()
            if l:
                l.ordre = self._lignes_model.rowCount()
                self._lignes_model.add(l)
                self._refresh_totals()

    def _edit_line(self) -> None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return
        row = rows[0].row()
        ligne = self._lignes_model.get_ligne(row)
        devis_id = self._devis.id if self._devis else uuid.uuid4()
        dlg = _AddLigneDialog(devis_id, parent=self, ligne=ligne)
        if dlg.exec():
            edited = dlg.get_ligne()
            if edited:
                edited.ordre = ligne.ordre
                self._lignes_model._lignes[row] = edited
                self._lignes_model.dataChanged.emit(
                    self._lignes_model.index(row, 0),
                    self._lignes_model.index(row, self._lignes_model.columnCount() - 1),
                )
                self._refresh_totals()

    def _del_line(self) -> None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return
        self._lignes_model.remove(rows[0].row())
        self._refresh_totals()

    # ── Save ────────────────────────────────────────────────────────────────

    def _save(self) -> None:
        client_id = self._client_combo.currentData()
        if not client_id:
            QMessageBox.warning(self, "Erreur", "Sélectionnez un client.")
            return

        vehicule_id = self._vehicule_combo.currentData()
        qd = self._date_exp.date()
        exp = date(qd.year(), qd.month(), qd.day())

        lignes = self._lignes_model.all_lignes()

        try:
            if self._devis is None:
                # new
                devis = self._ctx.devis_service.creer_devis(
                    self._session,
                    client_id=client_id,
                    vehicule_id=vehicule_id,
                    notes_client=self._notes_client.toPlainText(),
                    notes_internes=self._notes_internes.toPlainText(),
                    date_expiration=exp,
                )
                for l in lignes:
                    l.devis_id = devis.id
                    l.ordre = lignes.index(l)
                devis.lignes = lignes
                self._ctx.devis_service.sauvegarder_devis(self._session, devis)
            else:
                self._devis.client_id = client_id
                self._devis.vehicule_id = vehicule_id
                self._devis.notes_client = self._notes_client.toPlainText()
                self._devis.notes_internes = self._notes_internes.toPlainText()
                self._devis.date_expiration = exp
                for l in lignes:
                    l.devis_id = self._devis.id
                    l.ordre = lignes.index(l)
                self._devis.lignes = lignes
                self._ctx.devis_service.sauvegarder_devis(self._session, self._devis)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
