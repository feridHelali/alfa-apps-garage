from __future__ import annotations

import uuid
from decimal import Decimal

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QHBoxLayout, QLabel, QMdiSubWindow, QMessageBox,
    QPushButton, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.facturation.caisse import CreditClient
from garage_app.domain.shared.value_objects import Money
from garage_app.gui.widgets.searchable_table import SearchableTableWidget


class _CreditModel(QAbstractTableModel):
    HEADERS = ["Client ID", "Solde dû (DT)", "Plafond (DT)"]

    def __init__(self, rows: list[CreditClient]) -> None:
        super().__init__()
        self._data = rows
        self._client_names: dict[str, str] = {}

    def set_names(self, names: dict[str, str]) -> None:
        self._client_names = names

    def rowCount(self, parent=QModelIndex()) -> int: return len(self._data)
    def columnCount(self, parent=QModelIndex()) -> int: return len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        c = self._data[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            nom = self._client_names.get(str(c.client_id), str(c.client_id)[:8])
            limite = "Illimité" if c.limite_credit == Decimal("0") else f"{c.limite_credit:.3f}"
            return [nom, f"{c.solde:.3f}", limite][col]
        if role == Qt.ItemDataRole.ForegroundRole and col == 1:
            return QBrush(QColor("#D83B01") if c.solde > 0 else QColor("#107C10"))
        return None

    def get_credit(self, row: int) -> CreditClient:
        return self._data[row]

    def reload(self, rows: list[CreditClient]) -> None:
        self.beginResetModel()
        self._data = rows
        self.endResetModel()


class CreditClientsWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self._current: CreditClient | None = None
        self.setWindowTitle("Créances clients")
        self._build_ui()
        self._load()

    def status_info(self) -> str:
        total = sum(c.solde for c in self._model._data)
        return f"Créances — {len(self._model._data)} clients  |  Total dû : {total:.3f} DT"

    def _build_ui(self) -> None:
        main = QWidget()
        layout = QVBoxLayout(main)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        bar = QHBoxLayout()
        self._lbl_total = QLabel("")
        self._lbl_total.setStyleSheet("font-weight: 700; font-size: 11pt; color: #D83B01;")
        btn_rembourser = QPushButton("Rembourser…")
        btn_rembourser.clicked.connect(self._rembourser)
        btn_refresh = QPushButton("Actualiser")
        btn_refresh.clicked.connect(self._load)
        bar.addWidget(self._lbl_total)
        bar.addStretch()
        bar.addWidget(btn_rembourser)
        bar.addWidget(btn_refresh)
        layout.addLayout(bar)

        self._table_w = SearchableTableWidget()
        self._model = _CreditModel([])
        self._table_w.set_source_model(self._model)
        self._table_w.table.selectionModel().currentRowChanged.connect(self._on_select)
        layout.addWidget(self._table_w)

        self.setWidget(main)
        self.resize(700, 440)

    def _load(self) -> None:
        credits = self._ctx.credit_service.list_credits(self._session)
        # try to get client names
        try:
            clients = self._ctx.client_service.list_clients(self._session)
            names = {str(c.id): f"{c.nom} {c.prenom}".strip() for c in clients}
        except Exception:
            names = {}
        self._model.set_names(names)
        self._model.reload(credits)
        total = sum(c.solde for c in credits)
        self._lbl_total.setText(f"Total dû : {total:.3f} DT" if total > 0 else "Aucune créance")

    def _on_select(self, current, _) -> None:
        src_row = self._table_w.proxy.mapToSource(current).row()
        if src_row >= 0:
            self._current = self._model.get_credit(src_row)

    def _rembourser(self) -> None:
        if not self._current:
            QMessageBox.information(self, "Info", "Sélectionnez un client.")
            return
        dlg = _RemboursementDialog(self._current, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self._ctx.credit_service.rembourser_credit(
                    self._session, self._current.client_id, dlg.montant
                )
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))


class _RemboursementDialog(QDialog):
    def __init__(self, credit: CreditClient, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Enregistrer un remboursement")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Solde dû : {credit.solde:.3f} DT"))
        form = QFormLayout()
        self._montant = QDoubleSpinBox()
        self._montant.setRange(0.001, float(credit.solde))
        self._montant.setDecimals(3)
        self._montant.setSuffix(" DT")
        self._montant.setValue(float(credit.solde))
        form.addRow("Montant remboursé *", self._montant)
        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    @property
    def montant(self) -> Decimal:
        return Decimal(str(self._montant.value()))
