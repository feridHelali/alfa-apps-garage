from __future__ import annotations

import uuid
from decimal import Decimal

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QMdiSubWindow, QMessageBox,
    QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.stock.piece import Piece
from garage_app.gui.widgets.master_detail_widget import MasterDetailWidget
from garage_app.gui.widgets.searchable_table import SearchableTableWidget


class _PieceModel(QAbstractTableModel):
    HEADERS = ["Référence", "Désignation", "Catégorie", "Emplacement", "Prix vente (DT)", "Stock", "Seuil"]

    def __init__(self, pieces: list[Piece]) -> None:
        super().__init__()
        self._data = pieces

    def rowCount(self, parent=QModelIndex()) -> int: return len(self._data)
    def columnCount(self, parent=QModelIndex()) -> int: return len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        p = self._data[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            return [
                p.reference_constructeur, p.designation, p.categorie,
                p.emplacement, f"{p.prix_vente:.3f}",
                str(p.quantite_stock), str(p.seuil_alerte),
            ][col]
        if role == Qt.ItemDataRole.ForegroundRole and col == 5 and p.en_alerte:
            return QBrush(QColor("#D83B01"))
        if role == Qt.ItemDataRole.BackgroundRole and col == 5 and p.en_alerte:
            return QBrush(QColor("#FFF4CE"))
        return None

    def get_piece(self, row: int) -> Piece:
        return self._data[row]

    def reload(self, pieces: list[Piece]) -> None:
        self.beginResetModel()
        self._data = pieces
        self.endResetModel()


class PieceCatalogWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self._current: Piece | None = None
        self.setWindowTitle("Catalogue pièces")
        self._build_ui()
        self._load()

    def status_info(self) -> str:
        alerte = sum(1 for p in self._model._data if p.en_alerte)
        msg = f"Catalogue — {len(self._model._data)} pièces"
        if alerte:
            msg += f"  |  ⚠ {alerte} en alerte"
        return msg

    def _build_ui(self) -> None:
        master = QWidget()
        mv = QVBoxLayout(master)
        mv.setContentsMargins(4, 4, 4, 4)
        mv.setSpacing(4)

        btn_row = QHBoxLayout()
        btn_new = QPushButton("+ Nouvelle pièce")
        btn_new.clicked.connect(self._new_piece)
        self._btn_del = QPushButton("Supprimer")
        self._btn_del.clicked.connect(self._delete_piece)
        self._btn_del.setEnabled(False)
        self._btn_stock = QPushButton("Ajuster stock")
        self._btn_stock.clicked.connect(self._ajuster_stock)
        self._btn_stock.setEnabled(False)
        btn_row.addWidget(btn_new)
        btn_row.addWidget(self._btn_del)
        btn_row.addWidget(self._btn_stock)
        btn_row.addStretch()
        mv.addLayout(btn_row)

        self._table_w = SearchableTableWidget()
        self._model = _PieceModel([])
        self._table_w.set_source_model(self._model)
        self._table_w.table.selectionModel().currentRowChanged.connect(self._on_select)
        mv.addWidget(self._table_w)

        self._detail = _PieceDetailForm(ctx=self._ctx, session=self._session)
        self._detail.saved.connect(self._on_save)

        container = QWidget()
        QHBoxLayout(container).addWidget(MasterDetailWidget(master, self._detail))
        self.setWidget(container)
        self.resize(1060, 580)

    def _load(self) -> None:
        self._model.reload(self._ctx.stock_service.list_pieces(self._session))

    def _on_select(self, current, _) -> None:
        src_row = self._table_w.proxy.mapToSource(current).row()
        if src_row >= 0:
            self._current = self._model.get_piece(src_row)
            self._detail.load(self._current)
            self._btn_del.setEnabled(True)
            self._btn_stock.setEnabled(True)

    def _new_piece(self) -> None:
        self._current = None
        self._detail.clear()
        self._btn_del.setEnabled(False)
        self._btn_stock.setEnabled(False)

    def _on_save(self, p: Piece) -> None:
        try:
            if self._current and p.id == self._current.id:
                self._ctx.stock_service.update_piece(self._session, p)
            else:
                self._ctx.stock_service.create_piece(self._session, p)
            self._load()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _delete_piece(self) -> None:
        if not self._current:
            return
        rep = QMessageBox.question(
            self, "Confirmer",
            f"Supprimer « {self._current.designation} » ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep == QMessageBox.StandardButton.Yes:
            try:
                self._ctx.stock_service.delete_piece(self._session, self._current.id)
                self._current = None
                self._detail.clear()
                self._btn_del.setEnabled(False)
                self._btn_stock.setEnabled(False)
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def _ajuster_stock(self) -> None:
        if not self._current:
            return
        dlg = _AjustementDialog(self._current, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self._ctx.stock_service.ajuster_stock(
                    self._session, self._current.id, dlg.nouvelle_quantite
                )
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))


class _PieceDetailForm(QWidget):
    from PyQt6.QtCore import pyqtSignal
    saved = pyqtSignal(object)

    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._piece: Piece | None = None
        self._ctx = ctx
        self._session = session

        form = QFormLayout(self)
        form.setContentsMargins(12, 12, 12, 12)
        form.setSpacing(8)

        self._ref = QLineEdit()
        self._desig = QLineEdit()
        self._cat = QLineEdit()
        self._empl = QLineEdit()
        self._prix_a = QDoubleSpinBox()
        self._prix_a.setRange(0, 999999)
        self._prix_a.setDecimals(3)
        self._prix_a.setSuffix(" DT")
        self._prix_v = QDoubleSpinBox()
        self._prix_v.setRange(0, 999999)
        self._prix_v.setDecimals(3)
        self._prix_v.setSuffix(" DT")
        self._seuil = QSpinBox()
        self._seuil.setRange(0, 9999)
        self._fourn = QComboBox()
        self._fourn.addItem("— aucun —", None)
        self._fournisseurs = ctx.fournisseur_service.list_fournisseurs(session, actifs_seulement=True)
        for f in self._fournisseurs:
            self._fourn.addItem(f.raison_sociale, str(f.id))

        form.addRow("Référence *", self._ref)
        form.addRow("Désignation *", self._desig)
        form.addRow("Catégorie", self._cat)
        form.addRow("Emplacement", self._empl)
        form.addRow("Prix achat", self._prix_a)
        form.addRow("Prix vente *", self._prix_v)
        form.addRow("Seuil alerte", self._seuil)
        form.addRow("Fournisseur préféré", self._fourn)

        btn_save = QPushButton("Enregistrer")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save)
        form.addRow("", btn_save)

    def load(self, p: Piece) -> None:
        self._piece = p
        self._ref.setText(p.reference_constructeur)
        self._desig.setText(p.designation)
        self._cat.setText(p.categorie)
        self._empl.setText(p.emplacement)
        self._prix_a.setValue(float(p.prix_achat))
        self._prix_v.setValue(float(p.prix_vente))
        self._seuil.setValue(p.seuil_alerte)
        idx = 0
        if p.fournisseur_id:
            for i in range(self._fourn.count()):
                if self._fourn.itemData(i) == str(p.fournisseur_id):
                    idx = i
                    break
        self._fourn.setCurrentIndex(idx)

    def clear(self) -> None:
        self._piece = None
        for w in [self._ref, self._desig, self._cat, self._empl]:
            w.clear()
        self._prix_a.setValue(0)
        self._prix_v.setValue(0)
        self._seuil.setValue(5)
        self._fourn.setCurrentIndex(0)

    def _save(self) -> None:
        ref = self._ref.text().strip()
        desig = self._desig.text().strip()
        if not ref or not desig:
            QMessageBox.warning(self, "Validation", "Référence et désignation sont obligatoires.")
            return
        p = self._piece if self._piece else Piece()
        p.reference_constructeur = ref
        p.designation = desig
        p.categorie = self._cat.text().strip()
        p.emplacement = self._empl.text().strip()
        p.prix_achat = Decimal(str(self._prix_a.value()))
        p.prix_vente = Decimal(str(self._prix_v.value()))
        p.seuil_alerte = self._seuil.value()
        fourn_id = self._fourn.currentData()
        p.fournisseur_id = uuid.UUID(fourn_id) if fourn_id else None
        self.saved.emit(p)


class _AjustementDialog(QDialog):
    def __init__(self, piece: Piece, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ajustement de stock")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Pièce : {piece.designation}"))
        layout.addWidget(QLabel(f"Stock actuel : {piece.quantite_stock}"))
        form = QFormLayout()
        self._spin = QSpinBox()
        self._spin.setRange(0, 999999)
        self._spin.setValue(piece.quantite_stock)
        form.addRow("Nouvelle quantité :", self._spin)
        layout.addLayout(form)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    @property
    def nouvelle_quantite(self) -> int:
        return self._spin.value()
