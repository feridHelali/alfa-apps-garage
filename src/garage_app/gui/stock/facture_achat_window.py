from __future__ import annotations

import uuid
from datetime import date

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QDateEdit, QDoubleSpinBox, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMdiSubWindow, QMessageBox,
    QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession


class FactureAchatWindow(QMdiSubWindow):
    """Direct purchase-invoice entry — records stock entries without a prior purchase order."""

    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self.setWindowTitle("Facture d'achat — Entrée stock")
        self._build_ui()
        self._load_lookups()
        self.resize(820, 560)

    def _build_ui(self) -> None:
        root = QWidget()
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(10, 10, 10, 10)
        vbox.setSpacing(8)

        # ── Header form ──────────────────────────────────────────────────────
        hdr = QGroupBox("En-tête de la facture")
        form = QFormLayout(hdr)
        form.setSpacing(6)

        self._fourn_cb = QComboBox()
        self._ref = QLineEdit()
        self._ref.setPlaceholderText("ex. FA-2026-0001")
        self._date = QDateEdit(QDate.currentDate())
        self._date.setCalendarPopup(True)
        self._notes = QLineEdit()

        form.addRow("Fournisseur *", self._fourn_cb)
        form.addRow("N° Facture *", self._ref)
        form.addRow("Date", self._date)
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
            ["Pièce", "Quantité reçue", "Prix unitaire (DT)", "Total (DT)", ""]
        )
        self._lines_tbl.horizontalHeader().setStretchLastSection(True)
        self._lines_tbl.setColumnWidth(0, 280)
        self._lines_tbl.setColumnWidth(1, 110)
        self._lines_tbl.setColumnWidth(2, 130)
        self._lines_tbl.setColumnWidth(3, 100)
        self._lines_tbl.setColumnWidth(4, 40)
        self._lines_tbl.verticalHeader().setVisible(False)
        self._lines_tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._lines_tbl.setAlternatingRowColors(True)
        gv.addWidget(self._lines_tbl)
        vbox.addWidget(grp, stretch=1)

        # ── Footer ───────────────────────────────────────────────────────────
        foot = QHBoxLayout()
        self._lbl_total = QLabel("Total : 0,000 DT")
        self._lbl_total.setStyleSheet("font-weight: 700; font-size: 11pt;")
        btn_valider = QPushButton("Valider la facture — Entrée en stock")
        btn_valider.setDefault(True)
        btn_valider.clicked.connect(self._valider)
        btn_annuler = QPushButton("Annuler")
        btn_annuler.clicked.connect(self.close)
        foot.addWidget(self._lbl_total)
        foot.addStretch()
        foot.addWidget(btn_annuler)
        foot.addWidget(btn_valider)
        vbox.addLayout(foot)

        self.setWidget(root)
        self._pieces: list = []

    def _load_lookups(self) -> None:
        fournisseurs = self._ctx.fournisseur_service.list_fournisseurs(
            self._session, actifs_seulement=True
        )
        self._fourn_cb.clear()
        self._fourn_cb.addItem("— Aucun —", None)
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
        del_btn.clicked.connect(lambda _, r=row: self._remove_line(r))
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
        self._lbl_total.setText(f"Total : {grand_total:,.3f} DT")

    def _valider(self) -> None:
        ref = self._ref.text().strip()
        if not ref:
            QMessageBox.warning(self, "Validation", "Le numéro de facture est obligatoire.")
            return
        if self._lines_tbl.rowCount() == 0:
            QMessageBox.warning(self, "Validation", "Ajoutez au moins une ligne.")
            return

        # Collect lines
        lignes: list[tuple[uuid.UUID, int]] = []
        for row in range(self._lines_tbl.rowCount()):
            cb = self._lines_tbl.cellWidget(row, 0)
            qte_w = self._lines_tbl.cellWidget(row, 1)
            if cb and qte_w:
                piece_id = uuid.UUID(cb.currentData())
                lignes.append((piece_id, qte_w.value()))

        rep = QMessageBox.question(
            self,
            "Confirmer",
            f"Valider la facture '{ref}' et enregistrer {len(lignes)} entrée(s) de stock ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep != QMessageBox.StandardButton.Yes:
            return

        errors: list[str] = []
        for piece_id, qte in lignes:
            try:
                self._ctx.stock_service.entrer_stock(
                    self._session, piece_id, qte, reference=f"FA:{ref}"
                )
            except Exception as e:
                errors.append(str(e))

        if errors:
            QMessageBox.warning(self, "Erreurs partielles", "\n".join(errors))
        else:
            QMessageBox.information(
                self, "Succès",
                f"Facture '{ref}' validée — stock mis à jour pour {len(lignes)} pièce(s)."
            )
            self.close()
