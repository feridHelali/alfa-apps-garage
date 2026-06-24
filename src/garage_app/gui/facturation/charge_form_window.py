from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QLineEdit, QVBoxLayout,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.facturation.charge_garage import (
    CategorieCharge, ChargeGarage, PeriodiciteCharge,
)
from garage_app.gui.widgets.notification_bar import NotificationBar

_CATEGORIES = [c for c in CategorieCharge]
_PERIODICITES = [p for p in PeriodiciteCharge]


class ChargeFormDialog(QDialog):
    def __init__(
        self,
        ctx: AppContext,
        session: UserSession,
        charge: ChargeGarage | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._ctx = ctx
        self._session = session
        self._charge = charge
        self.setWindowTitle("Modifier charge" if charge else "Nouvelle charge")
        self._build_ui()
        if charge:
            self._populate(charge)
        self.resize(420, 320)

    def _build_ui(self) -> None:
        vbox = QVBoxLayout(self)
        self._notif = NotificationBar()
        vbox.addWidget(self._notif)

        form = QFormLayout()
        form.setSpacing(8)

        self._cat = QComboBox()
        for c in _CATEGORIES:
            self._cat.addItem(CategorieCharge.label(c.value), c.value)

        self._desc = QLineEdit()
        self._desc.setPlaceholderText("ex. Loyer janvier 2026")

        self._montant = QDoubleSpinBox()
        self._montant.setRange(0, 9_999_999)
        self._montant.setDecimals(3)
        self._montant.setSuffix(" DT")

        self._date = QDateEdit(QDate.currentDate())
        self._date.setCalendarPopup(True)

        self._echeance = QDateEdit(QDate.currentDate().addDays(30))
        self._echeance.setCalendarPopup(True)
        self._echeance.setSpecialValueText("—")

        self._periodicite = QComboBox()
        for p in _PERIODICITES:
            self._periodicite.addItem(PeriodiciteCharge.label(p.value), p.value)

        self._ref = QLineEdit()
        self._ref.setPlaceholderText("Référence, numéro de reçu…")

        form.addRow("Catégorie *", self._cat)
        form.addRow("Description *", self._desc)
        form.addRow("Montant *", self._montant)
        form.addRow("Date", self._date)
        form.addRow("Échéance", self._echeance)
        form.addRow("Périodicité", self._periodicite)
        form.addRow("Référence doc.", self._ref)
        vbox.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        vbox.addWidget(buttons)

    def _populate(self, ch: ChargeGarage) -> None:
        idx = next((i for i, c in enumerate(_CATEGORIES) if c == ch.categorie), 0)
        self._cat.setCurrentIndex(idx)
        self._desc.setText(ch.description)
        self._montant.setValue(float(ch.montant))
        self._date.setDate(QDate(ch.date_charge.year, ch.date_charge.month, ch.date_charge.day))
        if ch.date_echeance:
            self._echeance.setDate(QDate(
                ch.date_echeance.year, ch.date_echeance.month, ch.date_echeance.day
            ))
        idx_p = next((i for i, p in enumerate(_PERIODICITES) if p == ch.periodicite), 0)
        self._periodicite.setCurrentIndex(idx_p)
        self._ref.setText(ch.reference_document)

    def _save(self) -> None:
        if not self._desc.text().strip():
            self._notif.show_message("La description est obligatoire.", "error")
            return
        if self._montant.value() <= 0:
            self._notif.show_message("Le montant doit être positif.", "error")
            return

        d = self._date.date()
        date_charge = datetime(d.year(), d.month(), d.day())
        e = self._echeance.date()
        date_echeance = datetime(e.year(), e.month(), e.day()) if e.isValid() else None

        try:
            if self._charge:
                self._ctx.charge_service.modifier_charge(
                    self._session,
                    self._charge.id,
                    categorie=self._cat.currentData(),
                    description=self._desc.text().strip(),
                    montant=Decimal(str(self._montant.value())),
                    date_charge=date_charge,
                    periodicite=self._periodicite.currentData(),
                    date_echeance=date_echeance,
                    reference_document=self._ref.text().strip(),
                )
            else:
                self._ctx.charge_service.creer_charge(
                    self._session,
                    categorie=self._cat.currentData(),
                    description=self._desc.text().strip(),
                    montant=Decimal(str(self._montant.value())),
                    date_charge=date_charge,
                    periodicite=self._periodicite.currentData(),
                    date_echeance=date_echeance,
                    reference_document=self._ref.text().strip(),
                )
            self.accept()
        except Exception as e:
            self._notif.show_message(str(e), "error")
