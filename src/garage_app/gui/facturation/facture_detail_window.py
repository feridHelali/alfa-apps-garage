from __future__ import annotations

import uuid
from decimal import Decimal

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QMdiSubWindow, QMessageBox,
    QPushButton, QTableView, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.facturation.facture import Facture, ModePaiement, Paiement, StatutFacture
from garage_app.domain.shared.value_objects import Money
from garage_app.gui.widgets.icon_helper import icon as _icon

_STATUT_LABELS = {
    StatutFacture.BROUILLON:           "Brouillon",
    StatutFacture.EMISE:               "Émise",
    StatutFacture.PARTIELLEMENT_PAYEE: "Partiellement payée",
    StatutFacture.PAYEE:               "Payée ✓",
    StatutFacture.ANNULEE:             "Annulée",
}

_STATUT_COLORS = {
    StatutFacture.BROUILLON:           "#5D5D5D",
    StatutFacture.EMISE:               "#0067C0",
    StatutFacture.PARTIELLEMENT_PAYEE: "#7A4F00",
    StatutFacture.PAYEE:               "#107C10",
    StatutFacture.ANNULEE:             "#A4262C",
}


class _LignesModel(QAbstractTableModel):
    HEADERS = ["Désignation", "Qté", "Prix unit. (DT)", "Montant (DT)"]

    def __init__(self, facture: Facture) -> None:
        super().__init__()
        self._f = facture

    def rowCount(self, parent=QModelIndex()) -> int: return len(self._f.lignes)
    def columnCount(self, parent=QModelIndex()) -> int: return len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        l = self._f.lignes[index.row()]
        return [
            l.designation,
            str(l.quantite),
            f"{l.prix_unitaire:.3f}",
            f"{l.montant.amount:.3f}",
        ][index.column()]


class FactureDetailWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession, facture_id: uuid.UUID) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self._facture_id = facture_id
        self._facture: Facture | None = None
        self.setWindowTitle("Détail facture")
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        main = QWidget()
        layout = QVBoxLayout(main)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # header
        hdr = QHBoxLayout()
        self._lbl_numero = QLabel("")
        self._lbl_numero.setStyleSheet("font-size: 14pt; font-weight: 700;")
        self._lbl_date = QLabel("")
        self._lbl_date.setStyleSheet("font-size: 9pt; color: #5D5D5D; margin-left: 12px;")
        self._lbl_statut = QLabel("")
        self._lbl_statut.setStyleSheet("font-size: 10pt; font-weight: 600; padding: 3px 10px; border-radius: 4px;")
        hdr.addWidget(self._lbl_numero)
        hdr.addWidget(self._lbl_date)
        hdr.addStretch()
        hdr.addWidget(self._lbl_statut)
        layout.addLayout(hdr)

        # lines
        grp_lignes = QGroupBox("Lignes de facturation")
        gv = QVBoxLayout(grp_lignes)
        self._lignes_view = QTableView()
        self._lignes_view.setAlternatingRowColors(True)
        self._lignes_view.verticalHeader().setVisible(False)
        self._lignes_view.horizontalHeader().setStretchLastSection(True)
        gv.addWidget(self._lignes_view)
        layout.addWidget(grp_lignes, stretch=2)

        # totals
        tot = QFormLayout()
        self._lbl_ht = QLabel("")
        self._lbl_tva = QLabel("")
        self._lbl_ttc = QLabel("")
        self._lbl_ttc.setStyleSheet("font-weight: 700; font-size: 11pt;")
        self._lbl_paye = QLabel("")
        self._lbl_paye.setStyleSheet("color: #107C10; font-weight: 600;")
        self._lbl_solde = QLabel("")
        self._lbl_solde.setStyleSheet("color: #D83B01; font-weight: 600;")
        tot.addRow("Montant HT :", self._lbl_ht)
        tot.addRow("TVA :", self._lbl_tva)
        tot.addRow("Montant TTC :", self._lbl_ttc)
        tot.addRow("Déjà payé :", self._lbl_paye)
        tot.addRow("Solde restant :", self._lbl_solde)
        layout.addLayout(tot)

        # paiements history
        grp_pmts = QGroupBox("Historique des paiements")
        gv2 = QVBoxLayout(grp_pmts)
        self._pmt_labels: list[QLabel] = []
        self._pmt_container = QVBoxLayout()
        gv2.addLayout(self._pmt_container)
        layout.addWidget(grp_pmts)

        # action buttons
        btn_row = QHBoxLayout()
        self._btn_encaisser = QPushButton(_icon("save"), "Encaisser…")
        self._btn_encaisser.setDefault(True)
        self._btn_encaisser.clicked.connect(self._encaisser)
        btn_row.addWidget(self._btn_encaisser)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.setWidget(main)
        self.resize(700, 600)

    def _load(self) -> None:
        f = self._ctx.facture_service.get_facture(self._session, self._facture_id)
        if not f:
            self.close()
            return
        self._facture = f
        self.setWindowTitle(f"Facture {f.numero}")
        self._lbl_numero.setText(f"Facture N° {f.numero}")
        date_str = f.date_emission.strftime("%d/%m/%Y") if f.date_emission else "—"
        self._lbl_date.setText(f"Émise le {date_str}")
        label = _STATUT_LABELS.get(f.statut, f.statut)
        color = _STATUT_COLORS.get(f.statut, "#1A1A1A")
        self._lbl_statut.setText(f" {label} ")
        self._lbl_statut.setStyleSheet(
            f"font-size: 10pt; font-weight: 600; padding: 3px 10px; border-radius: 4px;"
            f"color: {color}; border: 1px solid {color};"
        )
        model = _LignesModel(f)
        self._lignes_view.setModel(model)
        self._lignes_view.resizeColumnsToContents()
        self._lbl_ht.setText(f.montant_ht.format())
        self._lbl_tva.setText(f"{f.montant_tva.format()}  ({f.taux_tva:.0f}%)")
        self._lbl_ttc.setText(f.montant_ttc.format())
        self._lbl_paye.setText(Money.of(f.montant_paye).format())
        self._lbl_solde.setText(Money.of(f.solde_restant).format())

        # clear and rebuild paiements
        while self._pmt_container.count():
            item = self._pmt_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if f.paiements:
            for p in f.paiements:
                lbl = QLabel(
                    f"  {p.date_paiement.strftime('%d/%m/%Y %H:%M')}  —  "
                    f"{ModePaiement.label(p.mode)}  —  "
                    f"{Money.of(p.montant).format()}"
                )
                self._pmt_container.addWidget(lbl)
        else:
            self._pmt_container.addWidget(QLabel("  Aucun paiement enregistré."))

        can_pay = f.statut in (StatutFacture.EMISE, StatutFacture.PARTIELLEMENT_PAYEE)
        self._btn_encaisser.setEnabled(can_pay)

    def _encaisser(self) -> None:
        if not self._facture:
            return
        dlg = _PaiementDialog(self._facture, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self._ctx.facture_service.enregistrer_paiement(
                    self._session,
                    self._facture_id,
                    dlg.montant,
                    dlg.mode,
                )
                # Also encaisser in caisse if active
                try:
                    active = self._ctx.caisse_service.get_session_active(self._session)
                    if active:
                        self._ctx.caisse_service.encaisser(
                            self._session,
                            dlg.montant,
                            f"Paiement facture {self._facture.numero}",
                            reference=str(self._facture_id),
                        )
                except Exception:
                    pass  # caisse optional
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))


class _PaiementDialog(QDialog):
    def __init__(self, facture: Facture, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Enregistrer un paiement")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Facture : {facture.numero}"))
        layout.addWidget(QLabel(f"Solde restant : {Money.of(facture.solde_restant).format()}"))

        form = QFormLayout()
        self._montant = QDoubleSpinBox()
        self._montant.setRange(0.001, float(facture.solde_restant))
        self._montant.setDecimals(3)
        self._montant.setSuffix(" DT")
        self._montant.setValue(float(facture.solde_restant))
        self._mode = QComboBox()
        for m in ModePaiement:
            self._mode.addItem(ModePaiement.label(m), m.value)
        form.addRow("Montant *", self._montant)
        form.addRow("Mode *", self._mode)
        layout.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    @property
    def montant(self) -> Decimal:
        return Decimal(str(self._montant.value()))

    @property
    def mode(self) -> str:
        return self._mode.currentData()
