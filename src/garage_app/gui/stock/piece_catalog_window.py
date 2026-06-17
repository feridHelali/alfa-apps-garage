from __future__ import annotations

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QBrush, QColor, QIcon
from PyQt6.QtWidgets import (
    QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMdiSubWindow, QPushButton, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.stock.piece import Piece
from garage_app.gui.widgets.master_detail_widget import MasterDetailWidget
from garage_app.gui.widgets.searchable_table import SearchableTableWidget


class _PieceModel(QAbstractTableModel):
    HEADERS = ["Référence", "Désignation", "Catégorie", "Prix vente", "Stock", "Alerte"]

    def __init__(self, pieces: list[Piece]) -> None:
        super().__init__()
        self._data = pieces

    def rowCount(self, parent=QModelIndex()) -> int: return len(self._data)
    def columnCount(self, parent=QModelIndex()) -> int: return len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid(): return None
        p = self._data[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return [
                p.reference_constructeur, p.designation, p.categorie,
                f"{p.prix_vente:.2f} €", str(p.quantite_stock),
                "⚠" if p.en_alerte else "",
            ][index.column()]
        if role == Qt.ItemDataRole.ForegroundRole and index.column() == 5 and p.en_alerte:
            return QBrush(QColor("#dc3545"))
        return None

    def get_piece(self, row: int) -> Piece: return self._data[row]
    def reload(self, pieces: list[Piece]) -> None:
        self.beginResetModel(); self._data = pieces; self.endResetModel()


class PieceCatalogWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self.setWindowTitle("Catalogue pièces")
        self.setWindowIcon(QIcon.fromTheme("package"))
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        self._table_w = SearchableTableWidget()
        self._model = _PieceModel([])
        self._table_w.set_source_model(self._model)
        self._table_w.table.selectionModel().currentRowChanged.connect(self._on_select)

        master = QWidget()
        mv = QVBoxLayout(master)
        mv.setContentsMargins(4, 4, 4, 4)
        btn_row = QHBoxLayout()
        btn_new = QPushButton(QIcon.fromTheme("list-add"), "Nouvelle pièce")
        btn_new.clicked.connect(self._new_piece)
        btn_row.addWidget(btn_new)
        btn_row.addStretch()
        mv.addLayout(btn_row)
        mv.addWidget(self._table_w)

        self._detail = _PieceDetailForm()

        widget = QWidget()
        QHBoxLayout(widget).addWidget(MasterDetailWidget(master, self._detail))
        self.setWidget(widget)
        self.resize(960, 550)

    def _load(self) -> None:
        self._model.reload(self._ctx.stock_service.list_pieces(self._session))

    def _on_select(self, current, _) -> None:
        src_row = self._table_w.proxy.mapToSource(current).row()
        if src_row >= 0:
            self._detail.load(self._model.get_piece(src_row))

    def _new_piece(self) -> None:
        self._detail.clear()


class _PieceDetailForm(QWidget):
    def __init__(self) -> None:
        super().__init__()
        form = QFormLayout(self)
        self._ref = QLineEdit()
        self._desig = QLineEdit()
        self._cat = QLineEdit()
        self._prix_a = QLineEdit()
        self._prix_v = QLineEdit()
        self._stock = QLineEdit()
        self._seuil = QLineEdit()
        form.addRow("Référence :", self._ref)
        form.addRow("Désignation :", self._desig)
        form.addRow("Catégorie :", self._cat)
        form.addRow("Prix achat :", self._prix_a)
        form.addRow("Prix vente :", self._prix_v)
        form.addRow("Quantité stock :", self._stock)
        form.addRow("Seuil alerte :", self._seuil)
        form.addRow(QPushButton(QIcon.fromTheme("document-save"), "Enregistrer"))

    def load(self, p: Piece) -> None:
        self._ref.setText(p.reference_constructeur)
        self._desig.setText(p.designation)
        self._cat.setText(p.categorie)
        self._prix_a.setText(str(p.prix_achat))
        self._prix_v.setText(str(p.prix_vente))
        self._stock.setText(str(p.quantite_stock))
        self._seuil.setText(str(p.seuil_alerte))

    def clear(self) -> None:
        for w in [self._ref, self._desig, self._cat, self._prix_a,
                  self._prix_v, self._stock, self._seuil]:
            w.clear()
