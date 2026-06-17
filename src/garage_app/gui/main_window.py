from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon, QKeySequence
from PyQt6.QtWidgets import (
    QLabel, QMainWindow, QMdiArea, QMenu, QMenuBar, QStatusBar, QToolBar,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.gui.window_registry import WindowRegistry


class MainWindow(QMainWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self._setup_ui()
        self._build_menu()
        self._build_toolbar()
        self._build_status_bar()

    # ── UI bootstrap ────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        self.setWindowTitle("Gestion Réparation Voiture — Alfa Computers Apps")
        self.resize(1366, 768)
        self._mdi = QMdiArea()
        self._mdi.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._mdi.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setCentralWidget(self._mdi)
        self._registry = WindowRegistry(self._mdi)

    def _can(self, perm: Permission) -> bool:
        return self._session.can(perm)

    def _action(self, label: str, slot, shortcut: str = "", perm: Permission | None = None) -> QAction:
        action = QAction(label, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        if perm and not self._can(perm):
            action.setVisible(False)
            action.setEnabled(False)
        action.triggered.connect(slot)
        return action

    # ── Menu bar ─────────────────────────────────────────────────────────────

    def _build_menu(self) -> None:
        mb = self.menuBar()

        # — Réception —
        m = mb.addMenu("&Réception")
        m.addAction(self._action("Clients", self._open_clients, "Ctrl+K", Permission.VIEW_CLIENTS))
        m.addAction(self._action("Rendez-vous", self._open_rdv, "", Permission.VIEW_RENDEZ_VOUS))
        m.addSeparator()
        m.addAction(self._action("&Quitter", self.close, "Alt+F4"))

        # — Atelier —
        m = mb.addMenu("&Atelier")
        m.addAction(self._action("Dossiers de réparation", self._open_dossiers, "Ctrl+D",
                                  Permission.VIEW_DOSSIERS))
        m.addAction(self._action("Techniciens", self._open_techniciens, "",
                                  Permission.MANAGE_DOSSIER))

        # — Stock —
        m = mb.addMenu("&Stock")
        m.addAction(self._action("Catalogue pièces", self._open_pieces, "Ctrl+P",
                                  Permission.VIEW_STOCK))
        m.addAction(self._action("Fournisseurs", self._open_fournisseurs, "",
                                  Permission.MANAGE_STOCK))
        m.addAction(self._action("Commandes fournisseurs", self._open_commandes, "",
                                  Permission.MANAGE_STOCK))
        m.addSeparator()
        m.addAction(self._action("Alertes stock", self._open_stock_alerts, "",
                                  Permission.VIEW_STOCK))

        # — Facturation —
        m = mb.addMenu("Fa&cturation")
        m.addAction(self._action("Factures", self._open_factures, "Ctrl+F",
                                  Permission.VIEW_FACTURES))

        # — Administration —
        m = mb.addMenu("&Administration")
        m.addAction(self._action("Société", self._open_societe, "", Permission.MANAGE_SOCIETE))
        m.addAction(self._action("Utilisateurs", self._open_users, "", Permission.MANAGE_USERS))
        m.addAction(self._action("Modèles de rapports", self._open_reports, "",
                                  Permission.MANAGE_REPORTS))
        m.addAction(self._action("Snapshots BDD", self._open_snapshots, "",
                                  Permission.MANAGE_SNAPSHOTS))
        m.addSeparator()
        m.addAction(self._action("Paramètres", self._open_settings, "", Permission.MANAGE_SETTINGS))

        # — Fenêtres —
        m = mb.addMenu("&Fenêtres")
        m.addAction(self._action("Cascade", self._mdi.cascadeSubWindows))
        m.addAction(self._action("Mosaïque", self._mdi.tileSubWindows))
        m.addSeparator()
        m.addAction(self._action("Fermer tout", self._mdi.closeAllSubWindows))

    # ── Toolbar ──────────────────────────────────────────────────────────────

    def _build_toolbar(self) -> None:
        tb = self.addToolBar("Principal")
        tb.setMovable(False)
        if self._can(Permission.VIEW_CLIENTS):
            tb.addAction(self._action("Clients", self._open_clients))
        if self._can(Permission.VIEW_DOSSIERS):
            tb.addAction(self._action("Dossiers", self._open_dossiers))
        if self._can(Permission.VIEW_STOCK):
            tb.addAction(self._action("Stock", self._open_pieces))
        if self._can(Permission.VIEW_FACTURES):
            tb.addAction(self._action("Factures", self._open_factures))

    # ── Status bar ───────────────────────────────────────────────────────────

    def _build_status_bar(self) -> None:
        sb = QStatusBar()
        role_label = QLabel(f"  {self._session.full_name}  [{self._session.role.upper()}]  ")
        sb.addPermanentWidget(role_label)
        self.setStatusBar(sb)
        sb.showMessage("Prêt", 3000)

    # ── Window openers ───────────────────────────────────────────────────────

    def _open_clients(self) -> None:
        from garage_app.gui.planification.client_window import ClientWindow
        self._registry.open_or_activate(ClientWindow, self._ctx, self._session)

    def _open_rdv(self) -> None:
        from garage_app.gui.planification.rendez_vous_window import RendezVousWindow
        self._registry.open_or_activate(RendezVousWindow, self._ctx, self._session)

    def _open_dossiers(self) -> None:
        from garage_app.gui.atelier.dossier_list_window import DossierListWindow
        self._registry.open_or_activate(DossierListWindow, self._ctx, self._session)

    def _open_techniciens(self) -> None:
        from garage_app.gui.atelier.technicien_window import TechnicienWindow
        self._registry.open_or_activate(TechnicienWindow, self._ctx, self._session)

    def _open_pieces(self) -> None:
        from garage_app.gui.stock.piece_catalog_window import PieceCatalogWindow
        self._registry.open_or_activate(PieceCatalogWindow, self._ctx, self._session)

    def _open_fournisseurs(self) -> None:
        from garage_app.gui.stock.fournisseur_window import FournisseurWindow
        self._registry.open_or_activate(FournisseurWindow, self._ctx, self._session)

    def _open_commandes(self) -> None:
        from garage_app.gui.stock.commande_window import CommandeWindow
        self._registry.open_or_activate(CommandeWindow, self._ctx, self._session)

    def _open_stock_alerts(self) -> None:
        from garage_app.gui.stock.stock_alert_window import StockAlertWindow
        self._registry.open_or_activate(StockAlertWindow, self._ctx, self._session)

    def _open_factures(self) -> None:
        from garage_app.gui.facturation.facture_list_window import FactureListWindow
        self._registry.open_or_activate(FactureListWindow, self._ctx, self._session)

    def _open_societe(self) -> None:
        from garage_app.gui.admin.societe_window import SocieteWindow
        self._registry.open_or_activate(SocieteWindow, self._ctx, self._session)

    def _open_users(self) -> None:
        from garage_app.gui.admin.user_management_window import UserManagementWindow
        self._registry.open_or_activate(UserManagementWindow, self._ctx, self._session)

    def _open_reports(self) -> None:
        from garage_app.gui.reports.report_list_window import ReportListWindow
        self._registry.open_or_activate(ReportListWindow, self._ctx, self._session)

    def _open_snapshots(self) -> None:
        from garage_app.gui.admin.snapshot_window import SnapshotWindow
        self._registry.open_or_activate(SnapshotWindow, self._ctx, self._session)

    def _open_settings(self) -> None:
        from garage_app.gui.admin.settings_window import SettingsWindow
        self._registry.open_or_activate(SettingsWindow, self._ctx, self._session)
