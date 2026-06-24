from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView, QLabel, QMdiSubWindow,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.facturation.facture_achat import FactureAchat, StatutAchat
from garage_app.gui.widgets.notification_bar import NotificationBar

_STATUT_LABELS = {
    StatutAchat.SAISIE:   "Saisie",
    StatutAchat.VALIDEE:  "Validée ✓",
    StatutAchat.PAYEE:    "Payée ✓",
    StatutAchat.ANNULEE:  "Annulée",
}


class FactureAchatListWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self.setWindowTitle("Factures d'achat — Historique")
        self._build_ui()
        self._load()
        self.resize(920, 520)

    def _build_ui(self) -> None:
        root = QWidget()
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(6)

        self._notif = NotificationBar()
        vbox.addWidget(self._notif)

        # Toolbar
        bar = QHBoxLayout()
        btn_new = QPushButton("+ Nouvelle facture d'achat")
        btn_new.clicked.connect(self._open_new)
        btn_valider = QPushButton("Valider")
        btn_valider.clicked.connect(self._valider_selected)
        btn_payer = QPushButton("Marquer payée")
        btn_payer.clicked.connect(self._payer_selected)
        btn_annuler = QPushButton("Annuler")
        btn_annuler.clicked.connect(self._annuler_selected)
        btn_refresh = QPushButton("↺")
        btn_refresh.setFixedWidth(32)
        btn_refresh.clicked.connect(self._load)
        bar.addWidget(btn_new)
        bar.addStretch()
        bar.addWidget(btn_valider)
        bar.addWidget(btn_payer)
        bar.addWidget(btn_annuler)
        bar.addWidget(btn_refresh)
        vbox.addLayout(bar)

        # Table
        self._tbl = QTableWidget(0, 7)
        self._tbl.setHorizontalHeaderLabels([
            "Notre N°", "N° Fournisseur", "Fournisseur", "Date", "Montant HT", "TVA", "Statut"
        ])
        self._tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._tbl.setColumnWidth(0, 110)
        self._tbl.setColumnWidth(1, 120)
        self._tbl.setColumnWidth(3, 90)
        self._tbl.setColumnWidth(4, 110)
        self._tbl.setColumnWidth(5, 60)
        self._tbl.setColumnWidth(6, 90)
        self._tbl.verticalHeader().setVisible(False)
        self._tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tbl.setAlternatingRowColors(True)
        vbox.addWidget(self._tbl, stretch=1)

        # KPIs
        kpi = QHBoxLayout()
        self._lbl_total = QLabel()
        self._lbl_total.setStyleSheet("font-size:9pt; color:#5D5D5D;")
        kpi.addWidget(self._lbl_total)
        kpi.addStretch()
        vbox.addLayout(kpi)

        self.setWidget(root)
        self._factures: list[FactureAchat] = []

    def _load(self) -> None:
        try:
            self._factures = self._ctx.facture_achat_service.list_factures_achat(self._session)
        except Exception as e:
            self._notif.show_message(str(e), "error")
            return
        self._tbl.setRowCount(0)
        total = 0.0
        for fa in self._factures:
            row = self._tbl.rowCount()
            self._tbl.insertRow(row)
            fourn_nom = ""
            try:
                fourn = self._ctx.fournisseur_service.get_fournisseur(self._session, fa.fournisseur_id)
                if fourn:
                    fourn_nom = fourn.raison_sociale
            except Exception:
                pass
            cells = [
                fa.notre_numero,
                fa.numero_fournisseur,
                fourn_nom,
                fa.date_facture.strftime("%d/%m/%Y"),
                f"{fa.montant_ht:,.3f} DT",
                f"{fa.taux_tva:.0f}%",
                _STATUT_LABELS.get(fa.statut, fa.statut.value),
            ]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                if col in (4,):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self._tbl.setItem(row, col, item)
            total += float(fa.montant_ht)
        self._lbl_total.setText(
            f"{len(self._factures)} facture(s) — Total HT : {total:,.3f} DT"
        )

    def _selected_facture(self) -> FactureAchat | None:
        rows = self._tbl.selectedItems()
        if not rows:
            return None
        row = self._tbl.currentRow()
        if 0 <= row < len(self._factures):
            return self._factures[row]
        return None

    def _open_new(self) -> None:
        from garage_app.gui.stock.facture_achat_window import FactureAchatWindow
        from garage_app.gui.window_registry import open_sub
        win = FactureAchatWindow(self._ctx, self._session)
        win.saved.connect(self._load)
        mdi = self.mdiArea()
        if mdi:
            open_sub(mdi, win)

    def _valider_selected(self) -> None:
        fa = self._selected_facture()
        if not fa:
            self._notif.show_message("Sélectionnez une facture.", "warning")
            return
        rep = QMessageBox.question(
            self, "Confirmer",
            f"Valider la facture '{fa.notre_numero}' et mettre à jour le stock ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep != QMessageBox.StandardButton.Yes:
            return
        try:
            self._ctx.facture_achat_service.valider(self._session, fa.id)
            self._notif.show_message(f"Facture '{fa.notre_numero}' validée — stock mis à jour.", "success")
            self._load()
        except Exception as e:
            self._notif.show_message(str(e), "error")

    def _payer_selected(self) -> None:
        fa = self._selected_facture()
        if not fa:
            self._notif.show_message("Sélectionnez une facture.", "warning")
            return
        try:
            self._ctx.facture_achat_service.marquer_payee(self._session, fa.id)
            self._notif.show_message(f"Facture '{fa.notre_numero}' marquée payée.", "success")
            self._load()
        except Exception as e:
            self._notif.show_message(str(e), "error")

    def _annuler_selected(self) -> None:
        fa = self._selected_facture()
        if not fa:
            self._notif.show_message("Sélectionnez une facture.", "warning")
            return
        rep = QMessageBox.question(
            self, "Confirmer",
            f"Annuler la facture '{fa.notre_numero}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep != QMessageBox.StandardButton.Yes:
            return
        try:
            self._ctx.facture_achat_service.annuler(self._session, fa.id)
            self._notif.show_message(f"Facture '{fa.notre_numero}' annulée.", "success")
            self._load()
        except Exception as e:
            self._notif.show_message(str(e), "error")
