from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QDateEdit, QDoubleSpinBox, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMdiSubWindow, QMessageBox,
    QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.gui.widgets.notification_bar import NotificationBar


class FactureAchatWindow(QMdiSubWindow):
    """Direct purchase-invoice entry — creates a FactureAchat and enters stock."""

    saved = pyqtSignal()

    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self.setWindowTitle("Nouvelle facture d'achat")
        self._build_ui()
        self._load_lookups()
        self.resize(820, 580)

    def _build_ui(self) -> None:
        root = QWidget()
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(10, 10, 10, 10)
        vbox.setSpacing(8)

        self._notif = NotificationBar()
        vbox.addWidget(self._notif)

        # ── Header form ──────────────────────────────────────────────────────
        hdr = QGroupBox("En-tête de la facture")
        form = QFormLayout(hdr)
        form.setSpacing(6)

        self._fourn_cb = QComboBox()
        self._ref = QLineEdit()
        self._ref.setPlaceholderText("Numéro figurant sur la facture fournisseur")
        self._date = QDateEdit(QDate.currentDate())
        self._date.setCalendarPopup(True)
        self._echeance = QDateEdit()
        self._echeance.setCalendarPopup(True)
        self._echeance.setSpecialValueText("—")
        self._echeance.setDate(QDate.currentDate().addDays(30))
        self._notes = QLineEdit()

        form.addRow("Fournisseur *", self._fourn_cb)
        form.addRow("N° Facture fournisseur *", self._ref)
        form.addRow("Date facture", self._date)
        form.addRow("Date échéance", self._echeance)
        form.addRow("Notes", self._notes)
        vbox.addWidget(hdr)

        # ── Lines ────────────────────────────────────────────────────────────
        grp = QGroupBox("Lignes de la facture")
        gv = QVBoxLayout(grp)

        add_btn = QPushButton("+ Ajouter une ligne")
        add_btn.clicked.connect(self._add_line)
        gv.addWidget(add_btn)

        self._lines_tbl = QTableWidget(0, 5)
        self._lines_tbl.setHorizontalHeaderLabels(
            ["Pièce", "Quantité reçue", "Prix unitaire (DT)", "Total HT (DT)", ""]
        )
        self._lines_tbl.horizontalHeader().setStretchLastSection(True)
        self._lines_tbl.setColumnWidth(0, 290)
        self._lines_tbl.setColumnWidth(1, 110)
        self._lines_tbl.setColumnWidth(2, 130)
        self._lines_tbl.setColumnWidth(3, 110)
        self._lines_tbl.setColumnWidth(4, 40)
        self._lines_tbl.verticalHeader().setVisible(False)
        self._lines_tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._lines_tbl.setAlternatingRowColors(True)
        gv.addWidget(self._lines_tbl)
        vbox.addWidget(grp, stretch=1)

        # ── Footer ───────────────────────────────────────────────────────────
        foot = QHBoxLayout()
        self._lbl_total = QLabel("Total HT : 0,000 DT")
        self._lbl_total.setStyleSheet("font-weight: 700; font-size: 11pt;")
        btn_valider = QPushButton("Enregistrer et valider (entrée stock)")
        btn_valider.setDefault(True)
        btn_valider.setStyleSheet("background:#107C10; color:white; font-weight:700; padding:6px 16px;")
        btn_valider.clicked.connect(self._valider)
        btn_sauver = QPushButton("Enregistrer (saisie)")
        btn_sauver.clicked.connect(self._sauver)
        btn_annuler = QPushButton("Annuler")
        btn_annuler.clicked.connect(self.close)
        foot.addWidget(self._lbl_total)
        foot.addStretch()
        foot.addWidget(btn_annuler)
        foot.addWidget(btn_sauver)
        foot.addWidget(btn_valider)
        vbox.addLayout(foot)

        self.setWidget(root)
        self._pieces: list = []

    def _load_lookups(self) -> None:
        fournisseurs = self._ctx.fournisseur_service.list_fournisseurs(
            self._session, actifs_seulement=True
        )
        self._fourn_cb.clear()
        self._fourn_cb.addItem("— Sélectionnez un fournisseur —", None)
        for f in fournisseurs:
            self._fourn_cb.addItem(f.raison_sociale, str(f.id))
        self._pieces = self._ctx.stock_service.list_pieces(self._session)

    def _add_line(self) -> None:
        row = self._lines_tbl.rowCount()
        self._lines_tbl.insertRow(row)

        cb = QComboBox()
        for p in self._pieces:
            cb.addItem(f"{p.reference_constructeur} — {p.designation}", str(p.id))
        self._lines_tbl.setCellWidget(row, 0, cb)

        spin_qte = QSpinBox()
        spin_qte.setRange(1, 9999)
        spin_qte.valueChanged.connect(self._update_total)
        self._lines_tbl.setCellWidget(row, 1, spin_qte)

        spin_prix = QDoubleSpinBox()
        spin_prix.setRange(0, 999999)
        spin_prix.setDecimals(3)
        spin_prix.valueChanged.connect(self._update_total)
        self._lines_tbl.setCellWidget(row, 2, spin_prix)

        total_item = QTableWidgetItem("0,000 DT")
        total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._lines_tbl.setItem(row, 3, total_item)

        del_btn = QPushButton("✕")
        del_btn.setFixedWidth(28)
        r = row
        del_btn.clicked.connect(lambda _, row_val=r: self._remove_line(row_val))
        self._lines_tbl.setCellWidget(row, 4, del_btn)

    def _remove_line(self, row: int) -> None:
        self._lines_tbl.removeRow(row)
        self._update_total()

    def _update_total(self) -> None:
        grand_total = 0.0
        for row in range(self._lines_tbl.rowCount()):
            qte_w = self._lines_tbl.cellWidget(row, 1)
            prix_w = self._lines_tbl.cellWidget(row, 2)
            if qte_w and prix_w:
                line_total = qte_w.value() * prix_w.value()
                grand_total += line_total
                item = self._lines_tbl.item(row, 3)
                if item:
                    item.setText(f"{line_total:,.3f} DT")
        self._lbl_total.setText(f"Total HT : {grand_total:,.3f} DT")

    def _collect_lignes(self) -> list[dict] | None:
        lignes: list[dict] = []
        for row in range(self._lines_tbl.rowCount()):
            cb = self._lines_tbl.cellWidget(row, 0)
            qte_w = self._lines_tbl.cellWidget(row, 1)
            prix_w = self._lines_tbl.cellWidget(row, 2)
            if cb and qte_w and prix_w and cb.currentData():
                lignes.append({
                    "piece_id": uuid.UUID(cb.currentData()),
                    "quantite": qte_w.value(),
                    "prix_unitaire": Decimal(str(prix_w.value())),
                })
        return lignes if lignes else None

    def _validate_header(self) -> bool:
        if not self._ref.text().strip():
            self._notif.show_message("Le numéro de facture fournisseur est obligatoire.", "error")
            return False
        if not self._fourn_cb.currentData():
            self._notif.show_message("Sélectionnez un fournisseur.", "error")
            return False
        if self._lines_tbl.rowCount() == 0:
            self._notif.show_message("Ajoutez au moins une ligne.", "error")
            return False
        return True

    def _sauver(self) -> None:
        if not self._validate_header():
            return
        lignes = self._collect_lignes()
        if not lignes:
            self._notif.show_message("Aucune ligne valide.", "error")
            return
        try:
            fa = self._ctx.facture_achat_service.creer_facture_achat(
                self._session,
                fournisseur_id=uuid.UUID(self._fourn_cb.currentData()),
                numero_fournisseur=self._ref.text().strip(),
                date_facture=datetime(
                    self._date.date().year(),
                    self._date.date().month(),
                    self._date.date().day(),
                ),
                lignes=lignes,
                notes=self._notes.text().strip(),
            )
            self._notif.show_message(f"Facture '{fa.notre_numero}' enregistrée (statut Saisie).", "success")
            self.saved.emit()
            self.close()
        except Exception as e:
            self._notif.show_message(str(e), "error")

    def _valider(self) -> None:
        if not self._validate_header():
            return
        lignes = self._collect_lignes()
        if not lignes:
            self._notif.show_message("Aucune ligne valide.", "error")
            return
        rep = QMessageBox.question(
            self, "Confirmer",
            f"Enregistrer ET valider la facture '{self._ref.text().strip()}' ?\n"
            "Cela mettra à jour le stock et le prix d'achat des pièces.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep != QMessageBox.StandardButton.Yes:
            return
        try:
            fa = self._ctx.facture_achat_service.creer_facture_achat(
                self._session,
                fournisseur_id=uuid.UUID(self._fourn_cb.currentData()),
                numero_fournisseur=self._ref.text().strip(),
                date_facture=datetime(
                    self._date.date().year(),
                    self._date.date().month(),
                    self._date.date().day(),
                ),
                lignes=lignes,
                notes=self._notes.text().strip(),
            )
            self._ctx.facture_achat_service.valider(self._session, fa.id)
            QMessageBox.information(
                self, "Succès",
                f"Facture '{fa.notre_numero}' validée — stock mis à jour pour {len(lignes)} pièce(s)."
            )
            self.saved.emit()
            self.close()
        except Exception as e:
            self._notif.show_message(str(e), "error")
