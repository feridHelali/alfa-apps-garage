from __future__ import annotations

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QGroupBox, QHBoxLayout, QLabel, QMdiSubWindow,
    QMessageBox, QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.atelier.dossier_reparation import DossierReparation
from garage_app.gui.widgets.status_badge import StatusBadgeLabel
from garage_app.gui.widgets.notification_bar import NotificationBar


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

        # Notification bar
        self._notif = NotificationBar()
        layout.addWidget(self._notif)

        # Header row: status badge + action buttons
        header = QHBoxLayout()
        self._badge = StatusBadgeLabel(self._dossier.statut)
        header.addWidget(QLabel("Statut :"))
        header.addWidget(self._badge)
        header.addStretch()
        self._btn_advance = QPushButton("Avancer →")
        self._btn_advance.clicked.connect(self._advance_state)
        header.addWidget(self._btn_advance)
        layout.addLayout(header)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._make_diagnostic_tab(), QIcon.fromTheme("edit-find"), "Diagnostic")
        tabs.addTab(self._make_operations_tab(), QIcon.fromTheme("system-run"), "Opérations")
        tabs.addTab(self._make_pieces_tab(), QIcon.fromTheme("package"), "Pièces")
        layout.addWidget(tabs)

        # Total
        self._total_label = QLabel(f"Total HT : {self._dossier.montant_total_ht.format()}")
        layout.addWidget(self._total_label)

        self.setWidget(widget)
        self.resize(860, 560)

    def _make_diagnostic_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("Lignes de diagnostic — à implémenter (Sprint 02)"))
        for l in self._dossier.lignes_diagnostic:
            v.addWidget(QLabel(f"  [{l.code_defaut}] {l.description} — {l.gravite}"))
        return w

    def _make_operations_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("Opérations mécaniques — à implémenter (Sprint 02)"))
        for op in self._dossier.operations:
            v.addWidget(QLabel(f"  {op.description} — {op.statut}"))
        return w

    def _make_pieces_tab(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("Pièces requises — à implémenter (Sprint 02)"))
        for p in self._dossier.pieces:
            v.addWidget(QLabel(f"  {p.designation} × {p.quantite} — {p.statut_dispo}"))
        return w

    def _advance_state(self) -> None:
        from garage_app.domain.atelier.statut_dossier import StatutDossier
        try:
            statut = self._dossier.statut
            if statut == StatutDossier.CREE:
                self._dossier = self._ctx.dossier_service.lancer_diagnostic(
                    self._session, self._dossier.id
                )
            elif statut == StatutDossier.DIAGNOSTIC:
                self._dossier = self._ctx.dossier_service.soumettre_au_devis(
                    self._session, self._dossier.id
                )
            elif statut == StatutDossier.EN_COURS:
                self._dossier = self._ctx.dossier_service.valider_qualite(
                    self._session, self._dossier.id
                )
            self._badge.set_statut(self._dossier.statut)
            self._notif.show_message("Statut mis à jour.", "success")
        except Exception as e:
            self._notif.show_message(str(e), "error")
