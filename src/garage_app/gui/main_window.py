from __future__ import annotations

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QPixmap, QPainter, QColor, QFont
from PyQt6.QtWidgets import (
    QApplication, QDockWidget, QLabel, QMainWindow, QMdiArea, QMenu,
    QPushButton, QScrollArea, QSizePolicy, QStatusBar, QStyle, QToolBar,
    QToolButton, QVBoxLayout, QWidget,
)
from garage_app.gui.branded_mdi_area import BrandedMdiArea

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.gui.window_registry import WindowRegistry, open_sub


def _std_icon(name: QStyle.StandardPixmap) -> QIcon:
    return QApplication.style().standardIcon(name)


def _color_icon(hex_color: str, char: str, size: int = 32) -> QIcon:
    """Create a simple colored square icon with a character label."""
    px = QPixmap(size, size)
    px.fill(QColor(hex_color))
    painter = QPainter(px)
    painter.setPen(QColor("#ffffff"))
    f = QFont("Segoe UI", int(size * 0.45), QFont.Weight.Bold)
    painter.setFont(f)
    painter.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, char)
    painter.end()
    return QIcon(px)


class _NavButton(QToolButton):
    """Sidebar navigation button with full/compact mode."""

    def __init__(self, label: str, icon: QIcon, slot) -> None:
        super().__init__()
        self._label = label
        self._icon = icon
        self.setIcon(icon)
        self.setText(label)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._set_style()
        self.clicked.connect(slot)
        self._compact = False

    def _set_style(self) -> None:
        self.setStyleSheet("""
            QToolButton {
                border: none;
                border-radius: 6px;
                padding: 4px 2px;
                font-size: 10px;
                color: #1A1A1A;
                background: transparent;
            }
            QToolButton:hover  { background: rgba(0,0,0,0.06); }
            QToolButton:pressed{ background: rgba(0,0,0,0.10); }
        """)

    def set_compact(self, compact: bool) -> None:
        self._compact = compact
        if compact:
            self.setIconSize(QSize(20, 20))
            self.setFixedHeight(38)
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            self.setToolTip(self._label)
        else:
            self.setIconSize(QSize(28, 28))
            self.setFixedHeight(60)
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            self.setToolTip("")


class MainWindow(QMainWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self._setup_ui()
        self._build_sidebar()
        self._build_menu()
        self._build_toolbar()
        self._build_status_bar()

    # ── UI bootstrap ────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        self.setWindowTitle("Gestion Réparation Voiture — Alfa Computers Apps")
        self.resize(1366, 768)
        self._mdi = BrandedMdiArea()
        self._mdi.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._mdi.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # Repaint watermark when last sub-window closes
        self._mdi.subWindowActivated.connect(
            lambda _: self._mdi.viewport().update()
        )
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

    # ── Sidebar ─────────────────────────────────────────────────────────────

    def _build_sidebar(self) -> None:
        # Read compact preference
        try:
            from garage_app.infrastructure.repositories.app_settings_repository import AppSettingsRepository
            _sr = AppSettingsRepository(self._ctx.session_factory)
            self._sidebar_compact = _sr.get("sidebar.compact", "false") == "true"
        except Exception:
            self._sidebar_compact = False

        # Auto-compact on small screens
        screen_h = QApplication.primaryScreen().size().height() if QApplication.primaryScreen() else 900
        if screen_h < 900:
            self._sidebar_compact = True

        self._dock = QDockWidget()
        self._dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self._dock.setTitleBarWidget(QWidget())

        self._sidebar_btns: list[_NavButton] = []

        container = QWidget()
        container.setStyleSheet(
            "QWidget { background: #F3F3F3; border-right: 1px solid #E0E0E0; }"
        )
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # ── Toggle button ────────────────────────────────────────────────────
        self._toggle_btn = QPushButton("◀" if not self._sidebar_compact else "▶")
        self._toggle_btn.setFixedHeight(22)
        self._toggle_btn.setStyleSheet(
            "QPushButton { border:none; background:transparent; font-size:10px; color:#5D5D5D; }"
            "QPushButton:hover { background:rgba(0,0,0,0.06); border-radius:4px; }"
        )
        self._toggle_btn.clicked.connect(self._toggle_sidebar)
        layout.addWidget(self._toggle_btn)

        # ── Brand label ──────────────────────────────────────────────────────
        brand = QLabel("Alfa\nComputers")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand.setStyleSheet(
            "font-size: 9px; color: #0067C0; font-weight: 700; "
            "padding-bottom: 4px; background: transparent; border: none;"
        )
        layout.addWidget(brand)

        def btn(label: str, icon: QIcon, slot, perm: Permission | None = None) -> None:
            if perm and not self._can(perm):
                return
            b = _NavButton(label, icon, slot)
            b.set_compact(self._sidebar_compact)
            self._sidebar_btns.append(b)
            layout.addWidget(b)

        def sep() -> None:
            layout.addSpacing(4)

        # Reception
        btn("Clients",    _color_icon("#0067C0", "C"),  self._open_clients,      Permission.VIEW_CLIENTS)
        btn("Véhicules",  _color_icon("#0055a5", "V"),  self._open_vehicules,    Permission.VIEW_CLIENTS)
        btn("Rendez-v.",  _color_icon("#1876CA", "R"),  self._open_rdv,          Permission.VIEW_RENDEZ_VOUS)
        sep()
        # Atelier
        btn("Dossiers",   _color_icon("#107C10", "D"),  self._open_dossiers,        Permission.VIEW_DOSSIERS)
        btn("Rapide",     _color_icon("#1D7340", "⚡"), self._open_bon_travail_rapide, Permission.MANAGE_FACTURES)
        sep()
        # Stock
        btn("Stock",      _color_icon("#D83B01", "S"),  self._open_pieces,         Permission.VIEW_STOCK)
        btn("Fourniss.",  _color_icon("#A4262C", "F"),  self._open_fournisseurs,   Permission.MANAGE_STOCK)
        btn("Fact.Ach.",  _color_icon("#8B4513", "A"),  self._open_factures_achat, Permission.MANAGE_STOCK)
        sep()
        # Facturation
        btn("Factures",   _color_icon("#5C2D91", "F"),  self._open_factures,     Permission.VIEW_FACTURES)
        btn("Caisse",     _color_icon("#00796B", "Ca"), self._open_caisse,        Permission.MANAGE_CAISSE)
        btn("Créances",   _color_icon("#4A148C", "Cr"), self._open_credits,       Permission.VIEW_FACTURES)
        btn("Charges",    _color_icon("#795548", "€"),  self._open_charges,       Permission.MANAGE_SETTINGS)
        sep()
        # Admin
        btn("Société",    _color_icon("#323130", "Ste"), self._open_societe,      Permission.MANAGE_SOCIETE)
        btn("BDD",        _color_icon("#004578", "DB"),  self._open_db_mgmt,      Permission.MANAGE_SNAPSHOTS)
        btn("Journal",    _color_icon("#004578", "Log"), self._open_audit,        Permission.MANAGE_USERS)

        layout.addStretch()

        # Logged-in user
        user_lbl = QLabel(self._session.full_name.split()[0])
        user_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_lbl.setStyleSheet(
            "font-size: 9px; color: #5D5D5D; padding-top: 4px; background: transparent; border: none;"
        )
        layout.addWidget(user_lbl)

        # ── Wrap in QScrollArea so it never overflows ─────────────────────────
        scroll = QScrollArea()
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        self._sidebar_width_full = 88
        self._sidebar_width_compact = 52
        w = self._sidebar_width_compact if self._sidebar_compact else self._sidebar_width_full
        self._dock.setFixedWidth(w)
        scroll.setFixedWidth(w)

        self._dock.setWidget(scroll)
        self._sidebar_scroll = scroll
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._dock)

    def _toggle_sidebar(self) -> None:
        self._sidebar_compact = not self._sidebar_compact
        self._toggle_btn.setText("▶" if self._sidebar_compact else "◀")
        w = self._sidebar_width_compact if self._sidebar_compact else self._sidebar_width_full
        self._dock.setFixedWidth(w)
        self._sidebar_scroll.setFixedWidth(w)
        for b in self._sidebar_btns:
            b.set_compact(self._sidebar_compact)
        # Persist preference
        try:
            from garage_app.infrastructure.repositories.app_settings_repository import AppSettingsRepository
            AppSettingsRepository(self._ctx.session_factory).set(
                "sidebar.compact", "true" if self._sidebar_compact else "false"
            )
        except Exception:
            pass

    # ── Menu bar ─────────────────────────────────────────────────────────────

    def _build_menu(self) -> None:
        mb = self.menuBar()

        # — Réception —
        m = mb.addMenu("&Réception")
        m.addAction(self._action("Clients", self._open_clients, "Ctrl+K", Permission.VIEW_CLIENTS))
        m.addAction(self._action("Véhicules", self._open_vehicules, "Ctrl+V", Permission.VIEW_CLIENTS))
        m.addAction(self._action("Rendez-vous", self._open_rdv, "", Permission.VIEW_RENDEZ_VOUS))
        m.addSeparator()
        m.addAction(self._action("&Quitter", self.close, "Alt+F4"))

        # — Atelier —
        m = mb.addMenu("&Atelier")
        m.addAction(self._action("Dossiers de réparation", self._open_dossiers, "Ctrl+D",
                                  Permission.VIEW_DOSSIERS))
        m.addAction(self._action("Bon de travail rapide…", self._open_bon_travail_rapide, "Ctrl+R",
                                  Permission.MANAGE_FACTURES))
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
        m.addAction(self._action("Factures d'achat", self._open_factures_achat, "",
                                  Permission.MANAGE_STOCK))
        m.addSeparator()
        m.addAction(self._action("Alertes stock", self._open_stock_alerts, "",
                                  Permission.VIEW_STOCK))

        # — Facturation —
        m = mb.addMenu("Fa&cturation")
        m.addAction(self._action("Factures", self._open_factures, "Ctrl+F",
                                  Permission.VIEW_FACTURES))
        m.addAction(self._action("Caisse", self._open_caisse, "",
                                  Permission.MANAGE_CAISSE))
        m.addAction(self._action("Créances clients", self._open_credits, "",
                                  Permission.VIEW_FACTURES))
        m.addSeparator()
        m.addAction(self._action("Charges du garage", self._open_charges, "",
                                  Permission.MANAGE_SETTINGS))

        # — Rapports —
        m = mb.addMenu("&Rapports")
        m.addAction(self._action("Concepteur de documents…", self._open_report_designer, "",
                                  Permission.MANAGE_REPORTS))
        m.addSeparator()
        m.addAction(self._action("CA Mensuel…", self._open_rapport_mensuel, "",
                                  Permission.VIEW_FACTURES))
        m.addAction(self._action("Stock Valorisé", self._open_rapport_stock, "",
                                  Permission.VIEW_STOCK))
        m.addAction(self._action("Alertes Stock", self._open_rapport_alertes, "",
                                  Permission.VIEW_STOCK))
        m.addAction(self._action("Créances Clients", self._open_rapport_creances, "",
                                  Permission.VIEW_FACTURES))
        m.addSeparator()
        m.addAction(self._action("Fiche Client…", self._open_fiche_client, "",
                                  Permission.VIEW_CLIENTS))
        m.addAction(self._action("Fiche Réparation…", self._open_fiche_reparation, "",
                                  Permission.VIEW_DOSSIERS))
        m.addAction(self._action("Fiche Stock (Pièce)…", self._open_fiche_stock, "",
                                  Permission.VIEW_STOCK))
        m.addAction(self._action("Fiche Fournisseur…", self._open_fiche_fournisseur, "",
                                  Permission.VIEW_STOCK))
        m.addAction(self._action("Carnet de Route…", self._open_carnet_de_route, "",
                                  Permission.VIEW_DOSSIERS))

        # — Administration —
        m = mb.addMenu("&Administration")
        m.addAction(self._action("Société", self._open_societe, "", Permission.MANAGE_SOCIETE))
        m.addAction(self._action("Utilisateurs", self._open_users, "", Permission.MANAGE_USERS))
        m.addAction(self._action("Modèles de rapports", self._open_reports, "",
                                  Permission.MANAGE_REPORTS))
        m.addSeparator()
        m.addAction(self._action("Gestion de la base de données", self._open_db_mgmt, "",
                                  Permission.MANAGE_SNAPSHOTS))
        m.addAction(self._action("Journal d'audit", self._open_audit, "",
                                  Permission.MANAGE_USERS))
        m.addSeparator()
        m.addAction(self._action("Paramètres", self._open_settings, "", Permission.MANAGE_SETTINGS))
        m.addAction(self._action("Numérotation", self._open_numerotation, "", Permission.MANAGE_SETTINGS))
        m.addSeparator()
        m.addAction(self._action("Nouveau dossier…", self._open_nouveau_dossier, "",
                                  Permission.MANAGE_SNAPSHOTS))

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
        tb.setIconSize(QSize(16, 16))
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
        self._status_msg = QLabel("Prêt")
        sb.addWidget(self._status_msg, 1)
        role_label = QLabel(f"  {self._session.full_name}  [{self._session.role.upper()}]  ")
        sb.addPermanentWidget(role_label)
        self.setStatusBar(sb)
        # Update status bar when active MDI sub-window changes
        self._mdi.subWindowActivated.connect(self._on_subwindow_activated)

    def _on_subwindow_activated(self, sub) -> None:
        if sub is None:
            self._status_msg.setText("Prêt")
            return
        widget = sub.widget()
        if hasattr(widget, "status_info"):
            self._status_msg.setText(widget.status_info())
        else:
            title = sub.windowTitle()
            self._status_msg.setText(title if title else "Prêt")

    # ── Window openers ───────────────────────────────────────────────────────

    def _open_clients(self) -> None:
        from garage_app.gui.planification.client_window import ClientWindow
        self._registry.open_or_activate(ClientWindow, self._ctx, self._session)

    def _open_vehicules(self) -> None:
        from garage_app.gui.planification.vehicule_list_window import VehiculeListWindow
        self._registry.open_or_activate(VehiculeListWindow, self._ctx, self._session)

    def _open_rdv(self) -> None:
        from garage_app.gui.planification.rendez_vous_window import RendezVousWindow
        self._registry.open_or_activate(RendezVousWindow, self._ctx, self._session)

    def _open_dossiers(self) -> None:
        from garage_app.gui.atelier.dossier_list_window import DossierListWindow
        self._registry.open_or_activate(DossierListWindow, self._ctx, self._session)

    def _open_techniciens(self) -> None:
        from garage_app.gui.atelier.technicien_window import TechnicienWindow
        self._registry.open_or_activate(TechnicienWindow, self._ctx, self._session)

    def _open_bon_travail_rapide(self) -> None:
        from garage_app.gui.atelier.bon_travail_rapide_window import BonTravailRapideWindow
        self._registry.open_or_activate(BonTravailRapideWindow, self._ctx, self._session)

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

    def _open_caisse(self) -> None:
        from garage_app.gui.facturation.caisse_window import CaisseWindow
        self._registry.open_or_activate(CaisseWindow, self._ctx, self._session)

    def _open_credits(self) -> None:
        from garage_app.gui.facturation.credit_clients_window import CreditClientsWindow
        self._registry.open_or_activate(CreditClientsWindow, self._ctx, self._session)

    def _open_societe(self) -> None:
        from garage_app.gui.admin.societe_window import SocieteWindow
        self._registry.open_or_activate(SocieteWindow, self._ctx, self._session)

    def _open_users(self) -> None:
        from garage_app.gui.admin.user_management_window import UserManagementWindow
        self._registry.open_or_activate(UserManagementWindow, self._ctx, self._session)

    def _open_reports(self) -> None:
        from garage_app.gui.reports.report_list_window import ReportListWindow
        self._registry.open_or_activate(ReportListWindow, self._ctx, self._session)

    def _open_db_mgmt(self) -> None:
        from garage_app.gui.admin.db_management_window import DbManagementWindow
        self._registry.open_or_activate(DbManagementWindow, self._ctx.db_management_service,
                                         self._session)

    def _open_audit(self) -> None:
        from garage_app.gui.admin.audit_log_window import AuditLogWindow
        self._registry.open_or_activate(AuditLogWindow, self._ctx.audit_service, self._session)

    def _open_settings(self) -> None:
        from garage_app.gui.admin.settings_window import SettingsWindow
        self._registry.open_or_activate(SettingsWindow, self._ctx, self._session)

    # ── Report openers ────────────────────────────────────────────────────────

    def _open_rapport_mensuel(self) -> None:
        from PyQt6.QtWidgets import QDialog
        from garage_app.gui.reports.rapport_mensuel_window import AnneeDialog, RapportMensuelWindow
        dlg = AnneeDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            open_sub(self._mdi, RapportMensuelWindow(self._ctx, self._session, dlg.annee))

    def _open_rapport_stock(self) -> None:
        from garage_app.gui.reports.rapport_stock_window import RapportStockWindow
        open_sub(self._mdi, RapportStockWindow(self._ctx, self._session))

    def _open_rapport_alertes(self) -> None:
        from garage_app.gui.reports.rapport_alertes_window import RapportAlertesWindow
        open_sub(self._mdi, RapportAlertesWindow(self._ctx, self._session))

    def _open_rapport_creances(self) -> None:
        from garage_app.gui.reports.rapport_creances_window import RapportCreancesWindow
        open_sub(self._mdi, RapportCreancesWindow(self._ctx, self._session))

    def _open_fiche_client(self) -> None:
        from garage_app.gui.reports.fiche_client_window import FicheClientWindow
        from garage_app.gui.dialogs.entity_selector_dialog import EntitySelectorDialog
        from PyQt6.QtWidgets import QDialog
        clients = self._ctx.client_service.list_clients(self._session)
        items = [(c.id, f"{c.nom} {c.prenom}".strip()) for c in clients]
        dlg = EntitySelectorDialog("Choisir un client", items, self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.selected_id:
            open_sub(self._mdi, FicheClientWindow(self._ctx, self._session, dlg.selected_id))

    def _open_fiche_reparation(self) -> None:
        from garage_app.gui.reports.fiche_reparation_window import FicheReparationWindow
        from garage_app.gui.dialogs.entity_selector_dialog import EntitySelectorDialog
        from PyQt6.QtWidgets import QDialog
        dossiers = self._ctx.dossier_service.list_dossiers(self._session)
        items = [(d.id, f"Dossier {str(d.id)[:8]} — {d.statut.value}") for d in dossiers]
        dlg = EntitySelectorDialog("Choisir un dossier", items, self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.selected_id:
            open_sub(self._mdi, FicheReparationWindow(self._ctx, self._session, dlg.selected_id))

    def _open_fiche_stock(self) -> None:
        from garage_app.gui.reports.fiche_stock_window import FicheStockWindow
        from garage_app.gui.dialogs.entity_selector_dialog import EntitySelectorDialog
        from PyQt6.QtWidgets import QDialog
        pieces = self._ctx.stock_service.list_pieces(self._session)
        items = [(p.id, f"{p.reference_constructeur} — {p.designation}") for p in pieces]
        dlg = EntitySelectorDialog("Choisir une pièce", items, self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.selected_id:
            open_sub(self._mdi, FicheStockWindow(self._ctx, self._session, dlg.selected_id))

    def _open_fiche_fournisseur(self) -> None:
        from garage_app.gui.reports.fiche_fournisseur_window import FicheFournisseurWindow
        from garage_app.gui.dialogs.entity_selector_dialog import EntitySelectorDialog
        from PyQt6.QtWidgets import QDialog
        fournisseurs = self._ctx.fournisseur_service.list_fournisseurs(self._session)
        items = [(f.id, f.raison_sociale) for f in fournisseurs]
        dlg = EntitySelectorDialog("Choisir un fournisseur", items, self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.selected_id:
            open_sub(self._mdi, FicheFournisseurWindow(self._ctx, self._session, dlg.selected_id))

    def _open_carnet_de_route(self) -> None:
        from garage_app.gui.reports.carnet_de_route_window import CarnetDeRouteWindow
        from garage_app.gui.dialogs.entity_selector_dialog import EntitySelectorDialog
        from PyQt6.QtWidgets import QDialog
        clients = self._ctx.client_service.list_clients(self._session)
        vehicules = []
        for c in clients:
            for v in self._ctx.client_service.get_vehicules(self._session, c.id):
                label = f"{c.nom} {c.prenom}".strip() + f" — {v.marque} {v.modele} ({v.immatriculation})"
                vehicules.append((v.id, label))
        if not vehicules:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Carnet de Route", "Aucun véhicule enregistré.")
            return
        dlg = EntitySelectorDialog("Choisir un véhicule", vehicules, self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.selected_id:
            open_sub(self._mdi, CarnetDeRouteWindow(self._ctx, self._session, dlg.selected_id))

    def _open_facture_achat(self) -> None:
        from garage_app.gui.stock.facture_achat_window import FactureAchatWindow
        self._registry.open_or_activate(FactureAchatWindow, self._ctx, self._session)

    def _open_factures_achat(self) -> None:
        from garage_app.gui.stock.facture_achat_list_window import FactureAchatListWindow
        self._registry.open_or_activate(FactureAchatListWindow, self._ctx, self._session)

    def _open_charges(self) -> None:
        from garage_app.gui.facturation.charges_window import ChargesWindow
        self._registry.open_or_activate(ChargesWindow, self._ctx, self._session)

    def _open_numerotation(self) -> None:
        from garage_app.gui.admin.numerotation_window import NumerotationWindow
        self._registry.open_or_activate(NumerotationWindow, self._ctx, self._session)

    def _open_report_designer(self) -> None:
        from garage_app.gui.reports.report_designer_window import ReportDesignerWindow
        self._registry.open_or_activate(ReportDesignerWindow, self._ctx, self._session)

    def _open_nouveau_dossier(self) -> None:
        from garage_app.dossier_manager import DossierManager
        from garage_app.gui.dossier_selector_dialog import NouveauDossierDialog
        from PyQt6.QtWidgets import QMessageBox
        dlg = NouveauDossierDialog(DossierManager(), self)
        if dlg.exec() and dlg.created_path:
            QMessageBox.information(
                self, "Dossier créé",
                f"Nouveau dossier créé :\n{dlg.created_path}\n\n"
                "Redémarrez l'application pour ouvrir ce dossier.",
            )
