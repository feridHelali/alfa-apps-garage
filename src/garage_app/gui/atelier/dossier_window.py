from __future__ import annotations

import uuid
from decimal import Decimal

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMdiSubWindow,
    QMessageBox, QPushButton, QSpinBox, QTabWidget, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.atelier.dossier_reparation import DossierReparation
from garage_app.domain.atelier.ligne_diagnostic import LigneDiagnostic
from garage_app.domain.atelier.operation_mecanique import OperationMecanique
from garage_app.domain.atelier.piece_requise import PieceRequise
from garage_app.domain.atelier.statut_dossier import GravitePanne, StatutDossier, StatutDispo, StatutTache
from garage_app.gui.widgets.status_badge import StatusBadgeLabel
from garage_app.gui.widgets.notification_bar import NotificationBar


_GRAVITE_LABELS = {
    GravitePanne.BLOQUANT: "Bloquant",
    GravitePanne.A_SURVEILLER: "À surveiller",
    GravitePanne.INFO: "Info",
}

_TACHE_LABELS = {
    StatutTache.A_FAIRE: "À faire",
    StatutTache.EN_COURS: "En cours",
    StatutTache.TERMINEE: "Terminée",
}

_DISPO_LABELS = {
    StatutDispo.EN_STOCK: "En stock",
    StatutDispo.COMMANDE: "Commandée",
    StatutDispo.RECU: "Reçue",
}


# ── Diagnostic tab ────────────────────────────────────────────────────────────

class _LigneDiagnosticDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ajouter une panne")
        self.setMinimumWidth(380)
        form = QFormLayout(self)
        self._code = QLineEdit()
        self._code.setPlaceholderText("P0300…")
        self._code.setMaxLength(20)
        form.addRow("Code défaut :", self._code)
        self._desc = QTextEdit()
        self._desc.setFixedHeight(80)
        self._desc.setPlaceholderText("Description de la panne…")
        form.addRow("Description :", self._desc)
        self._gravite = QComboBox()
        for g in GravitePanne:
            self._gravite.addItem(_GRAVITE_LABELS[g], g)
        form.addRow("Gravité :", self._gravite)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def _on_ok(self) -> None:
        if not self._desc.toPlainText().strip():
            QMessageBox.warning(self, "Erreur", "La description est obligatoire.")
            return
        self.accept()

    @property
    def ligne(self) -> LigneDiagnostic:
        l = LigneDiagnostic()
        l.code_defaut = self._code.text().strip()
        l.description = self._desc.toPlainText().strip()
        l.gravite = self._gravite.currentData()
        return l


class _DiagnosticTab(QWidget):
    changed = pyqtSignal()

    def __init__(self, ctx: AppContext, session: UserSession, dossier: DossierReparation) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self._dossier = dossier
        self._build_ui()
        self.reload(dossier)

    def _build_ui(self) -> None:
        v = QVBoxLayout(self)
        v.setContentsMargins(4, 4, 4, 4)

        btn_row = QHBoxLayout()
        self._btn_add = QPushButton("+ Ajouter panne")
        self._btn_add.clicked.connect(self._add_ligne)
        btn_row.addWidget(self._btn_add)
        self._btn_del = QPushButton("Supprimer")
        self._btn_del.clicked.connect(self._del_ligne)
        self._btn_del.setEnabled(False)
        btn_row.addWidget(self._btn_del)
        btn_row.addStretch()
        v.addLayout(btn_row)

        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Code défaut", "Description", "Gravité"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setColumnWidth(0, 100)
        self._table.setColumnWidth(2, 120)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.itemSelectionChanged.connect(
            lambda: self._btn_del.setEnabled(bool(self._table.selectedItems()))
        )
        v.addWidget(self._table)

    def reload(self, dossier: DossierReparation) -> None:
        self._dossier = dossier
        is_editable = dossier.statut == StatutDossier.DIAGNOSTIC
        self._btn_add.setEnabled(is_editable)
        self._table.setRowCount(0)
        for l in dossier.lignes_diagnostic:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(l.code_defaut))
            self._table.setItem(row, 1, QTableWidgetItem(l.description))
            g_item = QTableWidgetItem(_GRAVITE_LABELS.get(l.gravite, l.gravite))
            self._table.setItem(row, 2, g_item)
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, l.id)

    def _add_ligne(self) -> None:
        dlg = _LigneDiagnosticDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self._dossier = self._ctx.dossier_service.enregistrer_panne(
                    self._session, self._dossier.id, dlg.ligne
                )
                self.reload(self._dossier)
                self.changed.emit()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def _del_ligne(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            return
        ligne_id_item = self._table.item(row, 0)
        if not ligne_id_item:
            return
        ligne_id = ligne_id_item.data(Qt.ItemDataRole.UserRole)
        try:
            self._dossier = self._ctx.dossier_service.supprimer_ligne_diagnostic(
                self._session, self._dossier.id, ligne_id
            )
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
            return
        self.reload(self._dossier)
        self.changed.emit()


# ── Operations tab ─────────────────────────────────────────────────────────────

class _OperationDialog(QDialog):
    def __init__(self, users: list, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ajouter une opération")
        self.setMinimumWidth(420)
        form = QFormLayout(self)

        self._code = QLineEdit()
        self._code.setPlaceholderText("MO-001…")
        form.addRow("Code MO :", self._code)

        self._desc = QLineEdit()
        self._desc.setPlaceholderText("Vidange moteur…")
        form.addRow("Description :", self._desc)

        self._technicien = QComboBox()
        self._technicien.addItem("— Non assigné —", None)
        for u in users:
            self._technicien.addItem(u.full_name, u.id)
        form.addRow("Technicien :", self._technicien)

        self._temps_est = QDoubleSpinBox()
        self._temps_est.setRange(0, 999)
        self._temps_est.setDecimals(2)
        self._temps_est.setSuffix(" h")
        form.addRow("Temps estimé :", self._temps_est)

        self._taux = QDoubleSpinBox()
        self._taux.setRange(0, 9999)
        self._taux.setDecimals(3)
        self._taux.setSuffix(" DT/h")
        form.addRow("Taux horaire :", self._taux)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def _on_ok(self) -> None:
        if not self._desc.text().strip():
            QMessageBox.warning(self, "Erreur", "La description est obligatoire.")
            return
        self.accept()

    @property
    def operation(self) -> OperationMecanique:
        op = OperationMecanique()
        op.code_main_oeuvre = self._code.text().strip()
        op.description = self._desc.text().strip()
        op.technicien_id = self._technicien.currentData()
        op.temps_estime = Decimal(str(self._temps_est.value()))
        op.taux_horaire = Decimal(str(self._taux.value()))
        return op


class _TempsPasseDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Temps passé")
        form = QFormLayout(self)
        self._temps = QDoubleSpinBox()
        self._temps.setRange(0, 999)
        self._temps.setDecimals(2)
        self._temps.setSuffix(" h")
        form.addRow("Temps réel :", self._temps)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    @property
    def temps_passe(self) -> Decimal:
        return Decimal(str(self._temps.value()))


class _OperationsTab(QWidget):
    changed = pyqtSignal()

    def __init__(self, ctx: AppContext, session: UserSession, dossier: DossierReparation) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self._dossier = dossier
        self._users: list = []
        self._build_ui()
        self._load_users()
        self.reload(dossier)

    def _build_ui(self) -> None:
        v = QVBoxLayout(self)
        v.setContentsMargins(4, 4, 4, 4)

        btn_row = QHBoxLayout()
        self._btn_add = QPushButton("+ Ajouter opération")
        self._btn_add.clicked.connect(self._add_op)
        btn_row.addWidget(self._btn_add)
        self._btn_start = QPushButton("Démarrer")
        self._btn_start.clicked.connect(self._start_op)
        self._btn_start.setEnabled(False)
        btn_row.addWidget(self._btn_start)
        self._btn_finish = QPushButton("Terminer")
        self._btn_finish.clicked.connect(self._finish_op)
        self._btn_finish.setEnabled(False)
        btn_row.addWidget(self._btn_finish)
        btn_row.addStretch()
        v.addLayout(btn_row)

        self._table = QTableWidget(0, 7)
        self._table.setHorizontalHeaderLabels([
            "Code MO", "Description", "Technicien", "Est. (h)", "Réel (h)", "Montant", "Statut"
        ])
        self._table.setColumnWidth(0, 90)
        self._table.setColumnWidth(2, 130)
        self._table.setColumnWidth(3, 70)
        self._table.setColumnWidth(4, 70)
        self._table.setColumnWidth(5, 90)
        self._table.setColumnWidth(6, 90)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.itemSelectionChanged.connect(self._on_select)
        v.addWidget(self._table)

    def _load_users(self) -> None:
        try:
            from garage_app.domain.auth.permission import Permission
            self._users = self._ctx.auth_service.list_users(self._session)
        except Exception:
            self._users = []

    def reload(self, dossier: DossierReparation) -> None:
        self._dossier = dossier
        is_editable = dossier.statut == StatutDossier.EN_COURS
        self._btn_add.setEnabled(is_editable)
        self._table.setRowCount(0)
        user_map = {u.id: u.full_name for u in self._users}
        for op in dossier.operations:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(op.code_main_oeuvre))
            self._table.setItem(row, 1, QTableWidgetItem(op.description))
            tech_name = user_map.get(op.technicien_id, "—") if op.technicien_id else "—"
            self._table.setItem(row, 2, QTableWidgetItem(tech_name))
            self._table.setItem(row, 3, QTableWidgetItem(f"{op.temps_estime:.2f}"))
            self._table.setItem(row, 4, QTableWidgetItem(f"{op.temps_passe:.2f}"))
            self._table.setItem(row, 5, QTableWidgetItem(op.montant.format()))
            self._table.setItem(row, 6, QTableWidgetItem(_TACHE_LABELS.get(op.statut, op.statut)))
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, op.id)
        self._on_select()

    def _on_select(self) -> None:
        row = self._table.currentRow()
        op = self._get_op_at(row)
        is_en_cours = self._dossier.statut == StatutDossier.EN_COURS
        self._btn_start.setEnabled(is_en_cours and op is not None and op.statut == StatutTache.A_FAIRE)
        self._btn_finish.setEnabled(is_en_cours and op is not None and op.statut == StatutTache.EN_COURS)

    def _get_op_at(self, row: int) -> OperationMecanique | None:
        if row < 0 or row >= self._table.rowCount():
            return None
        op_id = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        return next((o for o in self._dossier.operations if o.id == op_id), None)

    def _add_op(self) -> None:
        dlg = _OperationDialog(self._users, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self._dossier = self._ctx.dossier_service.ajouter_operation(
                    self._session, self._dossier.id, dlg.operation
                )
                self.reload(self._dossier)
                self.changed.emit()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def _start_op(self) -> None:
        op = self._get_op_at(self._table.currentRow())
        if not op:
            return
        try:
            self._dossier = self._ctx.dossier_service.demarrer_operation(
                self._session, self._dossier.id, op.id
            )
            self.reload(self._dossier)
            self.changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _finish_op(self) -> None:
        op = self._get_op_at(self._table.currentRow())
        if not op:
            return
        dlg = _TempsPasseDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self._dossier = self._ctx.dossier_service.terminer_operation(
                    self._session, self._dossier.id, op.id, dlg.temps_passe
                )
                self.reload(self._dossier)
                self.changed.emit()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))


# ── Pieces tab ────────────────────────────────────────────────────────────────

class _PieceDialog(QDialog):
    def __init__(self, ctx: AppContext, session: UserSession, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ajouter une pièce")
        self.setMinimumWidth(400)
        self._ctx = ctx
        self._session = session
        self._pieces: list = []
        form = QFormLayout(self)

        self._combo_piece = QComboBox()
        self._combo_piece.setMinimumWidth(280)
        self._combo_piece.currentIndexChanged.connect(self._on_piece_changed)
        form.addRow("Pièce :", self._combo_piece)

        self._qte = QSpinBox()
        self._qte.setRange(1, 9999)
        form.addRow("Quantité :", self._qte)

        self._prix = QDoubleSpinBox()
        self._prix.setRange(0, 999999)
        self._prix.setDecimals(3)
        self._prix.setSuffix(" DT")
        form.addRow("Prix unitaire :", self._prix)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

        self._load_pieces()

    def _load_pieces(self) -> None:
        try:
            self._pieces = self._ctx.stock_service.list_pieces(self._session)
        except Exception:
            self._pieces = []
        for p in self._pieces:
            self._combo_piece.addItem(f"{p.reference_constructeur} — {p.designation}", p.id)

    def _on_piece_changed(self, idx: int) -> None:
        if 0 <= idx < len(self._pieces):
            p = self._pieces[idx]
            self._prix.setValue(float(p.prix_vente.amount))

    @property
    def piece_requise(self) -> PieceRequise | None:
        idx = self._combo_piece.currentIndex()
        if idx < 0 or idx >= len(self._pieces):
            return None
        p = self._pieces[idx]
        pr = PieceRequise()
        pr.piece_id = p.id
        pr.reference = p.reference_constructeur
        pr.designation = p.designation
        pr.quantite = self._qte.value()
        pr.prix_unitaire = Decimal(str(self._prix.value()))
        return pr


class _PiecesTab(QWidget):
    changed = pyqtSignal()

    def __init__(self, ctx: AppContext, session: UserSession, dossier: DossierReparation) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self._dossier = dossier
        self._build_ui()
        self.reload(dossier)

    def _build_ui(self) -> None:
        v = QVBoxLayout(self)
        v.setContentsMargins(4, 4, 4, 4)

        btn_row = QHBoxLayout()
        self._btn_add = QPushButton("+ Ajouter pièce")
        self._btn_add.clicked.connect(self._add_piece)
        btn_row.addWidget(self._btn_add)
        self._btn_del = QPushButton("Retirer")
        self._btn_del.clicked.connect(self._del_piece)
        self._btn_del.setEnabled(False)
        btn_row.addWidget(self._btn_del)
        btn_row.addStretch()
        v.addLayout(btn_row)

        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels([
            "Référence", "Désignation", "Qté", "Prix unit.", "Montant", "Statut"
        ])
        self._table.setColumnWidth(0, 110)
        self._table.setColumnWidth(2, 55)
        self._table.setColumnWidth(3, 90)
        self._table.setColumnWidth(4, 90)
        self._table.setColumnWidth(5, 90)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.itemSelectionChanged.connect(
            lambda: self._btn_del.setEnabled(
                bool(self._table.selectedItems()) and self._dossier.statut == StatutDossier.EN_COURS
            )
        )
        v.addWidget(self._table)

    def reload(self, dossier: DossierReparation) -> None:
        self._dossier = dossier
        is_editable = dossier.statut == StatutDossier.EN_COURS
        self._btn_add.setEnabled(is_editable)
        self._table.setRowCount(0)
        for p in dossier.pieces:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(p.reference))
            self._table.setItem(row, 1, QTableWidgetItem(p.designation))
            self._table.setItem(row, 2, QTableWidgetItem(str(p.quantite)))
            self._table.setItem(row, 3, QTableWidgetItem(f"{p.prix_unitaire:.3f} DT"))
            self._table.setItem(row, 4, QTableWidgetItem(p.montant.format()))
            self._table.setItem(row, 5, QTableWidgetItem(_DISPO_LABELS.get(p.statut_dispo, p.statut_dispo)))
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, p.id)

    def _add_piece(self) -> None:
        dlg = _PieceDialog(self._ctx, self._session, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            pr = dlg.piece_requise
            if not pr:
                return
            try:
                self._dossier = self._ctx.dossier_service.ajouter_piece(
                    self._session, self._dossier.id, pr
                )
                self.reload(self._dossier)
                self.changed.emit()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def _del_piece(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            return
        piece_id = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        try:
            self._dossier = self._ctx.dossier_service.supprimer_piece(
                self._session, self._dossier.id, piece_id
            )
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
            return
        self.reload(self._dossier)
        self.changed.emit()


# ── Main window ───────────────────────────────────────────────────────────────

class DossierWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession, dossier: DossierReparation) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self._dossier = dossier
        self.setWindowTitle(f"Dossier {str(dossier.id)[:8]}…")
        self.setWindowIcon(QIcon.fromTheme("document-properties"))
        self._build_ui()

    def _build_ui(self) -> None:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(6, 6, 6, 6)

        self._notif = NotificationBar()
        layout.addWidget(self._notif)

        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("Statut :"))
        self._badge = StatusBadgeLabel(self._dossier.statut)
        header.addWidget(self._badge)
        header.addStretch()
        self._btn_advance = QPushButton("Avancer →")
        self._btn_advance.clicked.connect(self._advance_state)
        header.addWidget(self._btn_advance)

        self._btn_facture = QPushButton("Générer Facture…")
        self._btn_facture.setStyleSheet(
            "background:#107C10; color:white; font-weight:bold; padding:4px 14px; border-radius:4px;"
        )
        self._btn_facture.clicked.connect(self._generate_facture)
        self._btn_facture.setVisible(False)
        header.addWidget(self._btn_facture)

        layout.addLayout(header)

        # Tabs
        self._tabs = QTabWidget()

        self._diag_tab = _DiagnosticTab(self._ctx, self._session, self._dossier)
        self._diag_tab.changed.connect(self._on_tab_changed)
        self._tabs.addTab(self._diag_tab, "Diagnostic")

        self._ops_tab = _OperationsTab(self._ctx, self._session, self._dossier)
        self._ops_tab.changed.connect(self._on_tab_changed)
        self._tabs.addTab(self._ops_tab, "Opérations")

        self._pieces_tab = _PiecesTab(self._ctx, self._session, self._dossier)
        self._pieces_tab.changed.connect(self._on_tab_changed)
        self._tabs.addTab(self._pieces_tab, "Pièces")

        layout.addWidget(self._tabs)

        self._total_label = QLabel()
        self._total_label.setStyleSheet("font-weight: bold; padding: 4px;")
        layout.addWidget(self._total_label)

        self.setWidget(widget)
        self.resize(920, 600)
        self._refresh_header()

    def _refresh_header(self) -> None:
        self._badge.set_statut(self._dossier.statut)
        self._total_label.setText(
            f"Total HT : {self._dossier.montant_total_ht.format()}  |  "
            f"MO : {self._dossier.montant_main_oeuvre.format()}  |  "
            f"Pièces : {self._dossier.montant_pieces.format()}"
        )
        terminal = self._dossier.statut in (StatutDossier.PRET, StatutDossier.CLOTURE)
        self._btn_advance.setVisible(not terminal)
        self._btn_facture.setVisible(self._dossier.statut == StatutDossier.PRET)

    def _on_tab_changed(self) -> None:
        sender = self.sender()
        if hasattr(sender, '_dossier'):
            self._dossier = sender._dossier
        self._refresh_header()

    def _reload_all_tabs(self) -> None:
        self._diag_tab.reload(self._dossier)
        self._ops_tab.reload(self._dossier)
        self._pieces_tab.reload(self._dossier)
        self._refresh_header()

    def _advance_state(self) -> None:
        statut = self._dossier.statut
        try:
            if statut == StatutDossier.CREE:
                self._dossier = self._ctx.dossier_service.lancer_diagnostic(
                    self._session, self._dossier.id
                )
            elif statut == StatutDossier.DIAGNOSTIC:
                self._dossier = self._ctx.dossier_service.soumettre_au_devis(
                    self._session, self._dossier.id
                )
            elif statut == StatutDossier.EN_ATTENTE_DEVIS:
                self._dossier = self._ctx.dossier_service.approuver_devis(
                    self._session, self._dossier.id, uuid.uuid4()
                )
            elif statut == StatutDossier.EN_COURS:
                self._dossier = self._ctx.dossier_service.terminer_reparation(
                    self._session, self._dossier.id
                )
            elif statut == StatutDossier.QUALITE:
                self._dossier = self._ctx.dossier_service.valider_qualite(
                    self._session, self._dossier.id
                )
            self._reload_all_tabs()
            self._notif.show_message("Statut mis à jour.", "success")
        except Exception as e:
            self._notif.show_message(str(e), "error")

    def _generate_facture(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("Générer la facture")
        dlg.setMinimumWidth(360)
        form = QFormLayout(dlg)
        info = QLabel(
            f"<b>Total HT : {self._dossier.montant_total_ht.format()}</b><br>"
            f"Main d'œuvre : {self._dossier.montant_main_oeuvre.format()}&nbsp;&nbsp;"
            f"Pièces : {self._dossier.montant_pieces.format()}"
        )
        info.setStyleSheet("padding:6px; background:#f0f4ff; border-radius:4px;")
        form.addRow(info)
        tva_spin = QDoubleSpinBox()
        tva_spin.setRange(0, 30)
        tva_spin.setValue(19.0)
        tva_spin.setDecimals(1)
        tva_spin.setSuffix(" %")
        form.addRow("Taux TVA :", tva_spin)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        form.addRow(btns)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            taux = Decimal(str(tva_spin.value()))
            facture = self._ctx.facture_service.generer_facture(self._session, self._dossier.id, taux)
            self._dossier = self._ctx.dossier_service.get_dossier(self._session, self._dossier.id)
            self._reload_all_tabs()
            from garage_app.gui.reports.facture_report_window import FactureReportWindow
            from garage_app.gui.window_registry import open_sub
            mdi = self.mdiArea()
            if mdi:
                open_sub(mdi, FactureReportWindow(self._ctx, self._session, facture))
            self._notif.show_message(f"Facture N° {facture.numero} générée avec succès.", "success")
        except Exception as e:
            self._notif.show_message(str(e), "error")
