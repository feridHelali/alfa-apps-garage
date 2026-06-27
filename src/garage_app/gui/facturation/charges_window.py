from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QHBoxLayout, QHeaderView, QLabel,
    QMdiSubWindow, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.facturation.charge_garage import (
    CategorieCharge, ChargeGarage, StatutCharge,
)
from garage_app.gui.widgets.notification_bar import NotificationBar
from garage_app.gui.widgets.icon_helper import icon as _icon

_STATUT_LABELS = {
    StatutCharge.SAISIE:  "En attente",
    StatutCharge.PAYEE:   "Payée ✓",
    StatutCharge.ANNULEE: "Annulée",
}


class ChargesWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self.setWindowTitle("Charges du garage")
        self._build_ui()
        self._load()
        self.resize(960, 540)

    def _build_ui(self) -> None:
        root = QWidget()
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(6)

        self._notif = NotificationBar()
        vbox.addWidget(self._notif)

        # Toolbar
        bar = QHBoxLayout()
        btn_new = QPushButton(_icon("new"), "+ Nouvelle charge")
        btn_new.clicked.connect(self._new_charge)
        btn_edit = QPushButton(_icon("edit"), "Modifier")
        btn_edit.clicked.connect(self._edit_charge)
        btn_pay = QPushButton(_icon("ok"), "Marquer payée")
        btn_pay.clicked.connect(self._pay_selected)
        btn_reconduire = QPushButton(_icon("forward"), "Reconduire")
        btn_reconduire.clicked.connect(self._reconduire_selected)
        btn_annuler = QPushButton(_icon("cancel"), "Annuler")
        btn_annuler.clicked.connect(self._annuler_selected)
        btn_suppr = QPushButton(_icon("delete"), "Supprimer")
        btn_suppr.clicked.connect(self._delete_selected)
        btn_refresh = QPushButton(_icon("refresh"), "↺")
        btn_refresh.setFixedWidth(32)
        btn_refresh.clicked.connect(self._load)
        bar.addWidget(btn_new)
        bar.addStretch()
        bar.addWidget(btn_edit)
        bar.addWidget(btn_pay)
        bar.addWidget(btn_reconduire)
        bar.addWidget(btn_annuler)
        bar.addWidget(btn_suppr)
        bar.addWidget(btn_refresh)
        vbox.addLayout(bar)

        # Table
        self._tbl = QTableWidget(0, 7)
        self._tbl.setHorizontalHeaderLabels([
            "Catégorie", "Description", "Montant", "Date", "Échéance", "Périodicité", "Statut"
        ])
        self._tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._tbl.setColumnWidth(0, 110)
        self._tbl.setColumnWidth(2, 110)
        self._tbl.setColumnWidth(3, 90)
        self._tbl.setColumnWidth(4, 90)
        self._tbl.setColumnWidth(5, 100)
        self._tbl.setColumnWidth(6, 90)
        self._tbl.verticalHeader().setVisible(False)
        self._tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tbl.setAlternatingRowColors(True)
        vbox.addWidget(self._tbl, stretch=1)

        # KPIs
        kpi = QHBoxLayout()
        self._lbl_total = QLabel()
        self._lbl_total_paye = QLabel()
        self._lbl_total_attente = QLabel()
        for lbl in (self._lbl_total, self._lbl_total_paye, self._lbl_total_attente):
            lbl.setStyleSheet("font-size:9pt; color:#5D5D5D; padding:0 8px;")
        kpi.addWidget(self._lbl_total)
        kpi.addWidget(self._lbl_total_paye)
        kpi.addWidget(self._lbl_total_attente)
        kpi.addStretch()
        vbox.addLayout(kpi)

        self.setWidget(root)
        self._charges: list[ChargeGarage] = []

    def _load(self) -> None:
        try:
            self._charges = self._ctx.charge_service.list_charges(self._session)
        except Exception as e:
            self._notif.show_message(str(e), "error")
            return
        self._tbl.setRowCount(0)
        total = 0.0
        total_paye = 0.0
        total_attente = 0.0
        for ch in self._charges:
            row = self._tbl.rowCount()
            self._tbl.insertRow(row)
            cells = [
                CategorieCharge.label(ch.categorie.value),
                ch.description,
                f"{ch.montant:,.3f} DT",
                ch.date_charge.strftime("%d/%m/%Y"),
                ch.date_echeance.strftime("%d/%m/%Y") if ch.date_echeance else "—",
                ch.periodicite.value.capitalize(),
                _STATUT_LABELS.get(ch.statut, ch.statut.value),
            ]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                if col == 2:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self._tbl.setItem(row, col, item)
            m = float(ch.montant)
            total += m
            if ch.statut == StatutCharge.PAYEE:
                total_paye += m
            elif ch.statut == StatutCharge.SAISIE:
                total_attente += m
        self._lbl_total.setText(f"Total : {total:,.3f} DT")
        self._lbl_total_paye.setText(f"Payé : {total_paye:,.3f} DT")
        self._lbl_total_attente.setText(f"En attente : {total_attente:,.3f} DT")

    def _selected_charge(self) -> ChargeGarage | None:
        row = self._tbl.currentRow()
        if 0 <= row < len(self._charges):
            return self._charges[row]
        return None

    def _new_charge(self) -> None:
        from garage_app.gui.facturation.charge_form_window import ChargeFormDialog
        dlg = ChargeFormDialog(self._ctx, self._session, parent=self.window())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load()

    def _edit_charge(self) -> None:
        ch = self._selected_charge()
        if not ch:
            self._notif.show_message("Sélectionnez une charge.", "warning")
            return
        from garage_app.gui.facturation.charge_form_window import ChargeFormDialog
        dlg = ChargeFormDialog(self._ctx, self._session, charge=ch, parent=self.window())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load()

    def _pay_selected(self) -> None:
        ch = self._selected_charge()
        if not ch:
            self._notif.show_message("Sélectionnez une charge.", "warning")
            return
        try:
            self._ctx.charge_service.marquer_payee(self._session, ch.id)
            self._notif.show_message("Charge marquée payée.", "success")
            self._load()
        except Exception as e:
            self._notif.show_message(str(e), "error")

    def _reconduire_selected(self) -> None:
        ch = self._selected_charge()
        if not ch:
            self._notif.show_message("Sélectionnez une charge.", "warning")
            return
        try:
            nouvelle = self._ctx.charge_service.reconduire(self._session, ch.id)
            self._notif.show_message(f"Charge reconduite ({nouvelle.date_charge.strftime('%d/%m/%Y')}).", "success")
            self._load()
        except Exception as e:
            self._notif.show_message(str(e), "error")

    def _annuler_selected(self) -> None:
        ch = self._selected_charge()
        if not ch:
            self._notif.show_message("Sélectionnez une charge.", "warning")
            return
        try:
            self._ctx.charge_service.annuler(self._session, ch.id)
            self._notif.show_message("Charge annulée.", "success")
            self._load()
        except Exception as e:
            self._notif.show_message(str(e), "error")

    def _delete_selected(self) -> None:
        ch = self._selected_charge()
        if not ch:
            self._notif.show_message("Sélectionnez une charge.", "warning")
            return
        rep = QMessageBox.question(
            self, "Confirmer", "Supprimer définitivement cette charge ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep != QMessageBox.StandardButton.Yes:
            return
        try:
            self._ctx.charge_service.supprimer(self._session, ch.id)
            self._load()
        except Exception as e:
            self._notif.show_message(str(e), "error")
