from __future__ import annotations

from decimal import Decimal

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QMdiSubWindow, QMessageBox,
    QPushButton, QTableView, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.facturation.caisse import MouvementCaisse, SessionCaisse
from garage_app.domain.shared.value_objects import Money
from garage_app.gui.widgets.icon_helper import icon as _icon


class _MouvementsModel(QAbstractTableModel):
    HEADERS = ["Heure", "Type", "Montant (DT)", "Motif", "Référence"]

    def __init__(self, mouvements: list[MouvementCaisse]) -> None:
        super().__init__()
        self._data = mouvements

    def rowCount(self, parent=QModelIndex()) -> int: return len(self._data)
    def columnCount(self, parent=QModelIndex()) -> int: return len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        mv = self._data[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            return [
                mv.horodatage.strftime("%H:%M:%S"),
                "Entrée" if mv.type == "entree" else "Sortie",
                f"{mv.montant:.3f}",
                mv.motif,
                mv.reference,
            ][col]
        if role == Qt.ItemDataRole.ForegroundRole and col == 1:
            return QBrush(QColor("#107C10") if mv.type == "entree" else QColor("#D83B01"))
        return None

    def reload(self, mouvements: list[MouvementCaisse]) -> None:
        self.beginResetModel()
        self._data = mouvements
        self.endResetModel()


class CaisseWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self._sc: SessionCaisse | None = None
        self.setWindowTitle("Caisse")
        self._build_ui()
        self._load()

    def status_info(self) -> str:
        if self._sc and self._sc.statut == "ouverte":
            return f"Caisse ouverte — Solde théorique : {self._sc.solde_theorique:.3f} DT"
        return "Caisse — Aucune session ouverte"

    def _build_ui(self) -> None:
        main = QWidget()
        layout = QVBoxLayout(main)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Status header
        hdr = QHBoxLayout()
        self._lbl_statut = QLabel("Aucune session ouverte")
        self._lbl_statut.setStyleSheet("font-size: 12pt; font-weight: 700;")
        btn_refresh = QPushButton(_icon("refresh"), "Actualiser")
        btn_refresh.clicked.connect(self._load)
        hdr.addWidget(self._lbl_statut)
        hdr.addStretch()
        hdr.addWidget(btn_refresh)
        layout.addLayout(hdr)

        # Balances
        bal = QHBoxLayout()
        self._card_ouverture = _InfoCard("Solde ouverture", "0,000 DT")
        self._card_entrees = _InfoCard("Entrées", "0,000 DT", "#DFF6DD", "#107C10")
        self._card_sorties = _InfoCard("Sorties", "0,000 DT", "#FDE7E9", "#A4262C")
        self._card_theorique = _InfoCard("Solde théorique", "0,000 DT", "#EEF4FB", "#0067C0")
        for card in [self._card_ouverture, self._card_entrees, self._card_sorties, self._card_theorique]:
            bal.addWidget(card)
        layout.addLayout(bal)

        # Mouvements table
        grp = QGroupBox("Mouvements de la session")
        gv = QVBoxLayout(grp)
        self._mvt_view = QTableView()
        self._mvt_model = _MouvementsModel([])
        self._mvt_view.setModel(self._mvt_model)
        self._mvt_view.setAlternatingRowColors(True)
        self._mvt_view.verticalHeader().setVisible(False)
        self._mvt_view.horizontalHeader().setStretchLastSection(True)
        gv.addWidget(self._mvt_view)
        layout.addWidget(grp, stretch=2)

        # Action buttons
        btn_row = QHBoxLayout()
        self._btn_ouvrir = QPushButton(_icon("open"), "Ouvrir session")
        self._btn_ouvrir.clicked.connect(self._ouvrir)
        self._btn_encaisser = QPushButton(_icon("save"), "Encaisser")
        self._btn_encaisser.clicked.connect(self._encaisser)
        self._btn_decaisser = QPushButton(_icon("delete"), "Décaisser")
        self._btn_decaisser.clicked.connect(self._decaisser)
        self._btn_fermer = QPushButton(_icon("close"), "Fermer session")
        self._btn_fermer.clicked.connect(self._fermer)
        for b in [self._btn_ouvrir, self._btn_encaisser, self._btn_decaisser, self._btn_fermer]:
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

        self.setWidget(main)
        self.resize(900, 560)

    def _load(self) -> None:
        self._sc = self._ctx.caisse_service.get_session_active(self._session)
        is_open = self._sc is not None and self._sc.statut == "ouverte"

        if is_open:
            self._lbl_statut.setText(f"Session ouverte — {self._sc.ouvert_le.strftime('%d/%m/%Y %H:%M')}")  # type: ignore[union-attr]
            self._lbl_statut.setStyleSheet("font-size: 12pt; font-weight: 700; color: #107C10;")
            entrees = sum(m.montant for m in self._sc.mouvements if m.type == "entree")  # type: ignore[union-attr]
            sorties = sum(m.montant for m in self._sc.mouvements if m.type == "sortie")  # type: ignore[union-attr]
            self._card_ouverture.set_value(f"{self._sc.solde_ouverture:.3f} DT")  # type: ignore[union-attr]
            self._card_entrees.set_value(f"{entrees:.3f} DT")
            self._card_sorties.set_value(f"{sorties:.3f} DT")
            self._card_theorique.set_value(f"{self._sc.solde_theorique:.3f} DT")  # type: ignore[union-attr]
            self._mvt_model.reload(self._sc.mouvements)  # type: ignore[union-attr]
        else:
            self._lbl_statut.setText("Aucune session ouverte")
            self._lbl_statut.setStyleSheet("font-size: 12pt; font-weight: 700; color: #A4262C;")
            for card in [self._card_ouverture, self._card_entrees, self._card_sorties, self._card_theorique]:
                card.set_value("—")
            self._mvt_model.reload([])

        self._btn_ouvrir.setEnabled(not is_open)
        self._btn_encaisser.setEnabled(is_open)
        self._btn_decaisser.setEnabled(is_open)
        self._btn_fermer.setEnabled(is_open)

    def _ouvrir(self) -> None:
        dlg = _OuvertureDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self._ctx.caisse_service.ouvrir_session(self._session, dlg.solde_ouverture)
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def _encaisser(self) -> None:
        dlg = _MouvementDialog("Encaisser", self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self._ctx.caisse_service.encaisser(self._session, dlg.montant, dlg.motif)
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def _decaisser(self) -> None:
        dlg = _MouvementDialog("Décaisser", self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self._ctx.caisse_service.decaisser(self._session, dlg.montant, dlg.motif)
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def _fermer(self) -> None:
        if not self._sc:
            return
        dlg = _FermetureDialog(self._sc, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                sc, ecart = self._ctx.caisse_service.fermer_session(self._session, dlg.solde_reel)
                msg = f"Session fermée.\nSolde théorique : {sc.solde_theorique:.3f} DT\nSolde réel : {dlg.solde_reel:.3f} DT\nÉcart : {ecart:+.3f} DT"
                if abs(ecart) > Decimal("0.001"):
                    QMessageBox.warning(self, "Écart de caisse détecté", msg)
                else:
                    QMessageBox.information(self, "Session fermée", msg)
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))


class _InfoCard(QGroupBox):
    def __init__(self, title: str, value: str, bg: str = "#F3F3F3", fg: str = "#1A1A1A") -> None:
        super().__init__(title)
        layout = QVBoxLayout(self)
        self._lbl = QLabel(value)
        self._lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl.setStyleSheet(f"font-size: 14pt; font-weight: 700; color: {fg};")
        layout.addWidget(self._lbl)
        self.setStyleSheet(f"QGroupBox {{ background: {bg}; border-radius: 6px; }}")

    def set_value(self, value: str) -> None:
        self._lbl.setText(value)


class _OuvertureDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ouvrir une session de caisse")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._solde = QDoubleSpinBox()
        self._solde.setRange(0, 999999)
        self._solde.setDecimals(3)
        self._solde.setSuffix(" DT")
        form.addRow("Fond de caisse :", self._solde)
        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    @property
    def solde_ouverture(self) -> Decimal:
        return Decimal(str(self._solde.value()))


class _MouvementDialog(QDialog):
    def __init__(self, titre: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(titre)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._montant = QDoubleSpinBox()
        self._montant.setRange(0.001, 999999)
        self._montant.setDecimals(3)
        self._montant.setSuffix(" DT")
        self._motif = QLineEdit()
        form.addRow("Montant *", self._montant)
        form.addRow("Motif *", self._motif)
        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _on_accept(self) -> None:
        if not self._motif.text().strip():
            QMessageBox.warning(self, "Validation", "Le motif est obligatoire.")
            return
        self.accept()

    @property
    def montant(self) -> Decimal:
        return Decimal(str(self._montant.value()))

    @property
    def motif(self) -> str:
        return self._motif.text().strip()


class _FermetureDialog(QDialog):
    def __init__(self, sc: SessionCaisse, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Fermer la session de caisse")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Solde théorique : {sc.solde_theorique:.3f} DT"))
        form = QFormLayout()
        self._solde = QDoubleSpinBox()
        self._solde.setRange(0, 999999)
        self._solde.setDecimals(3)
        self._solde.setSuffix(" DT")
        self._solde.setValue(float(sc.solde_theorique))
        form.addRow("Solde réel compté *", self._solde)
        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    @property
    def solde_reel(self) -> Decimal:
        return Decimal(str(self._solde.value()))
