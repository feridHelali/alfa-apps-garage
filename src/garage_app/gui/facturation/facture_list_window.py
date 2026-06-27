from __future__ import annotations

import uuid

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QMdiSubWindow, QMessageBox,
    QPushButton, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.facturation.facture import Facture, ModePaiement, StatutFacture
from garage_app.domain.shared.value_objects import Money
from garage_app.gui.widgets.searchable_table import SearchableTableWidget
from garage_app.gui.widgets.icon_helper import icon as _icon

_STATUT_COLORS = {
    StatutFacture.BROUILLON:          ("#5D5D5D", "#F3F3F3"),
    StatutFacture.EMISE:              ("#0067C0", "#EEF4FB"),
    StatutFacture.PARTIELLEMENT_PAYEE:("#7A4F00", "#FFF4CE"),
    StatutFacture.PAYEE:              ("#107C10", "#DFF6DD"),
    StatutFacture.ANNULEE:            ("#A4262C", "#FDE7E9"),
}

_STATUT_LABELS = {
    StatutFacture.BROUILLON:           "Brouillon",
    StatutFacture.EMISE:               "Émise",
    StatutFacture.PARTIELLEMENT_PAYEE: "Part. payée",
    StatutFacture.PAYEE:               "Payée",
    StatutFacture.ANNULEE:             "Annulée",
}


class _FactureModel(QAbstractTableModel):
    HEADERS = ["Numéro", "Date", "Montant TTC", "Payé", "Solde restant", "Statut"]

    def __init__(self, rows: list[Facture]) -> None:
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
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            return [
                f.numero,
                f.date_emission.strftime("%d/%m/%Y") if f.date_emission else "—",
                Money.of(f.montant_ttc.amount).format(),
                Money.of(f.montant_paye).format(),
                Money.of(f.solde_restant).format(),
                _STATUT_LABELS.get(f.statut, f.statut),
            ][col]
        if role == Qt.ItemDataRole.ForegroundRole and col == 5:
            fg, _ = _STATUT_COLORS.get(f.statut, ("#1A1A1A", "#FFFFFF"))
            return QBrush(QColor(fg))
        if role == Qt.ItemDataRole.BackgroundRole and col == 5:
            _, bg = _STATUT_COLORS.get(f.statut, ("#FFFFFF", "#FFFFFF"))
            return QBrush(QColor(bg))
        return None

    def get_facture(self, row: int) -> Facture:
        return self._data[row]

    def reload(self, rows: list[Facture]) -> None:
        self.beginResetModel()
        self._data = rows
        self.endResetModel()


class FactureListWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self._current: Facture | None = None
        self.setWindowTitle("Factures")
        self._build_ui()
        self._load()

    def status_info(self) -> str:
        impayees = sum(
            1 for f in self._model._data
            if f.statut in (StatutFacture.EMISE, StatutFacture.PARTIELLEMENT_PAYEE)
        )
        return f"Factures — {len(self._model._data)} total  |  {impayees} impayée(s)"

    def _build_ui(self) -> None:
        main = QWidget()
        layout = QVBoxLayout(main)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # toolbar
        bar = QHBoxLayout()
        lbl = QLabel("Filtre :")
        self._filtre = QComboBox()
        self._filtre.addItems(["Toutes", "Impayées", "Payées", "Annulées"])
        self._filtre.currentIndexChanged.connect(self._load)
        btn_detail = QPushButton(_icon("open"), "Ouvrir détail")
        btn_detail.clicked.connect(self._open_detail)
        btn_annuler = QPushButton(_icon("cancel"), "Annuler facture")
        btn_annuler.clicked.connect(self._annuler)
        bar.addWidget(lbl)
        bar.addWidget(self._filtre)
        bar.addStretch()
        bar.addWidget(btn_detail)
        bar.addWidget(btn_annuler)
        layout.addLayout(bar)

        self._table_w = SearchableTableWidget()
        self._model = _FactureModel([])
        self._table_w.set_source_model(self._model)
        self._table_w.table.selectionModel().currentRowChanged.connect(self._on_select)
        self._table_w.table.doubleClicked.connect(lambda _: self._open_detail())
        layout.addWidget(self._table_w)

        self.setWidget(main)
        self.resize(900, 500)

    def _load(self) -> None:
        idx = self._filtre.currentIndex()
        if idx == 1:
            rows = self._ctx.facture_service.list_impayees(self._session)
        elif idx == 2:
            rows = [f for f in self._ctx.facture_service.list_factures(self._session)
                    if f.statut == StatutFacture.PAYEE]
        elif idx == 3:
            rows = [f for f in self._ctx.facture_service.list_factures(self._session)
                    if f.statut == StatutFacture.ANNULEE]
        else:
            rows = self._ctx.facture_service.list_factures(self._session)
        self._model.reload(rows)

    def _on_select(self, current, _) -> None:
        src_row = self._table_w.proxy.mapToSource(current).row()
        if src_row >= 0:
            self._current = self._model.get_facture(src_row)

    def _open_detail(self) -> None:
        if not self._current:
            return
        from garage_app.gui.facturation.facture_detail_window import FactureDetailWindow
        from garage_app.gui.window_registry import open_sub
        mdi = self.mdiArea()
        if mdi:
            open_sub(mdi, FactureDetailWindow(self._ctx, self._session, self._current.id))

    def _annuler(self) -> None:
        if not self._current:
            return
        rep = QMessageBox.question(
            self, "Confirmer", f"Annuler la facture {self._current.numero} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep == QMessageBox.StandardButton.Yes:
            try:
                self._ctx.facture_service.annuler_facture(self._session, self._current.id)
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))
