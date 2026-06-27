from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMdiSubWindow, QMessageBox, QPushButton, QTabWidget, QTextEdit,
    QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.societe.societe import Societe
from garage_app.gui.widgets.notification_bar import NotificationBar
from garage_app.gui.widgets.icon_helper import icon as _icon


def _human_size(n: int) -> str:
    for unit in ("o", "Ko", "Mo", "Go"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} To"


class SettingsWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self.setWindowTitle("Paramètres")
        self._build_ui()
        self.resize(560, 480)

    def _build_ui(self) -> None:
        root = QWidget()
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(8, 8, 8, 8)

        self._notif = NotificationBar()
        vbox.addWidget(self._notif)

        tabs = QTabWidget()

        # ── Tab: Affichage ───────────────────────────────────────────────────
        display_tab = QWidget()
        dtv = QVBoxLayout(display_tab)
        grp = QGroupBox("Interface")
        form = QFormLayout(grp)
        self._lang = QComboBox()
        self._lang.addItems(["fr — Français", "ar — عربي"])
        self._theme = QComboBox()
        self._theme.addItems(["light — Clair", "dark — Sombre"])
        form.addRow("Langue :", self._lang)
        form.addRow("Thème :", self._theme)
        dtv.addWidget(grp)
        dtv.addStretch()
        tabs.addTab(display_tab, "Affichage")

        # ── Tab: Numérotation (shortcut) ─────────────────────────────────────
        num_tab = QWidget()
        ntv = QVBoxLayout(num_tab)
        btn_open_num = QPushButton(_icon("open"), "Ouvrir la fenêtre de numérotation…")
        btn_open_num.clicked.connect(self._open_numerotation)
        ntv.addWidget(btn_open_num)
        ntv.addStretch()
        tabs.addTab(num_tab, "Numérotation")

        # ── Tab: Société ─────────────────────────────────────────────────────
        if self._session.can(Permission.MANAGE_SOCIETE):
            tabs.addTab(self._build_societe_tab(), "Société")

        # ── Tab: Base de données (superadmin) ────────────────────────────────
        if self._session.can(Permission.MANAGE_SNAPSHOTS):
            tabs.addTab(self._build_db_tab(), "Base de données")

        vbox.addWidget(tabs)

        # ── Footer ───────────────────────────────────────────────────────────
        foot = QHBoxLayout()
        btn_save = QPushButton(_icon("apply"), "Appliquer")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._apply)
        btn_close = QPushButton(_icon("close"), "Fermer")
        btn_close.clicked.connect(self.close)
        foot.addStretch()
        foot.addWidget(btn_close)
        foot.addWidget(btn_save)
        vbox.addLayout(foot)

        settings = self._ctx.settings_service.get()
        self._lang.setCurrentIndex(0 if settings.language != "ar" else 1)
        self._theme.setCurrentIndex(0 if settings.theme == "light" else 1)

        self.setWidget(root)

    # ── Société tab ──────────────────────────────────────────────────────────

    def _build_societe_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(6, 6, 6, 6)

        logo_box = QGroupBox("Logo")
        logo_layout = QHBoxLayout(logo_box)
        self._logo_label = QLabel()
        self._logo_label.setFixedSize(100, 68)
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._logo_label.setStyleSheet("border: 1px solid #c0c0c0; background: #f8f8f8;")
        btn_logo = QPushButton(_icon("logo"), "Choisir…")
        btn_logo.clicked.connect(self._pick_logo)
        logo_layout.addWidget(self._logo_label)
        logo_layout.addWidget(btn_logo)
        logo_layout.addStretch()
        layout.addWidget(logo_box)

        form = QFormLayout()
        self._raison = QLineEdit()
        self._siret = QLineEdit()
        self._adresse = QLineEdit()
        self._tel = QLineEdit()
        self._email_soc = QLineEdit()
        self._licence = QLineEdit()
        self._licence.setReadOnly(True)
        form.addRow("Raison sociale :", self._raison)
        form.addRow("SIRET :", self._siret)
        form.addRow("Adresse :", self._adresse)
        form.addRow("Téléphone :", self._tel)
        form.addRow("Email :", self._email_soc)
        form.addRow("Clé de licence :", self._licence)
        layout.addLayout(form)

        btn_save_soc = QPushButton(_icon("save"), "Enregistrer la société")
        btn_save_soc.clicked.connect(self._save_societe)
        layout.addWidget(btn_save_soc)
        layout.addStretch()

        self._load_societe()
        return tab

    def _load_societe(self) -> None:
        s = self._ctx.societe_service.get()
        if s:
            self._societe = s
            self._raison.setText(s.raison_sociale)
            self._siret.setText(s.siret)
            self._adresse.setText(s.adresse)
            self._tel.setText(s.telephone)
            self._email_soc.setText(s.email)
            self._licence.setText(s.licence_key)
            if s.logo_path and Path(s.logo_path).exists():
                pix = QPixmap(s.logo_path).scaled(
                    100, 68, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._logo_label.setPixmap(pix)
        else:
            self._societe = Societe()

    def _pick_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Choisir un logo", "", "Images (*.png *.jpg *.svg *.ico)"
        )
        if path:
            self._societe.logo_path = path
            pix = QPixmap(path).scaled(
                100, 68, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._logo_label.setPixmap(pix)

    def _save_societe(self) -> None:
        self._societe.raison_sociale = self._raison.text().strip()
        self._societe.siret = self._siret.text().strip()
        self._societe.adresse = self._adresse.text().strip()
        self._societe.telephone = self._tel.text().strip()
        self._societe.email = self._email_soc.text().strip()
        try:
            self._ctx.societe_service.update(self._session, self._societe)
            self._notif.show_message("Société enregistrée.", "success")
        except Exception as e:
            self._notif.show_message(str(e), "error")

    # ── Base de données tab (superadmin) ─────────────────────────────────────

    def _build_db_tab(self) -> QWidget:
        tab = QWidget()
        root = QHBoxLayout(tab)
        root.setContentsMargins(6, 6, 6, 6)

        left = QVBoxLayout()
        stats_box = QGroupBox("Statistiques SQLite")
        sl = QVBoxLayout(stats_box)
        self._lbl_size = QLabel()
        self._lbl_pages = QLabel()
        self._lbl_frag = QLabel()
        for lbl in (self._lbl_size, self._lbl_pages, self._lbl_frag):
            sl.addWidget(lbl)
        left.addWidget(stats_box)

        maint_box = QGroupBox("Maintenance")
        ml = QVBoxLayout(maint_box)
        btn_vacuum = QPushButton(_icon("drive"), "VACUUM (compresser)")
        btn_vacuum.setToolTip("Récupère l'espace fragmenté.")
        btn_vacuum.clicked.connect(self._do_vacuum)
        ml.addWidget(btn_vacuum)
        btn_wal = QPushButton(_icon("refresh"), "Checkpoint WAL")
        btn_wal.clicked.connect(self._do_wal)
        ml.addWidget(btn_wal)
        btn_integrity = QPushButton(_icon("check"), "Vérifier l'intégrité")
        btn_integrity.clicked.connect(self._do_integrity)
        ml.addWidget(btn_integrity)
        left.addWidget(maint_box)

        self._result_log = QTextEdit()
        self._result_log.setReadOnly(True)
        self._result_log.setMaximumHeight(120)
        left.addWidget(QLabel("Résultats :"))
        left.addWidget(self._result_log)
        left.addStretch()
        root.addLayout(left, 1)

        right = QVBoxLayout()
        snap_box = QGroupBox("Snapshots / Sauvegardes")
        sl2 = QVBoxLayout(snap_box)
        self._snap_list = QListWidget()
        self._snap_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        sl2.addWidget(self._snap_list)
        btn_row = QHBoxLayout()
        btn_create = QPushButton(_icon("snapshot"), "Créer snapshot")
        btn_create.clicked.connect(self._do_create_snap)
        btn_row.addWidget(btn_create)
        btn_restore = QPushButton(_icon("restore"), "Restaurer")
        btn_restore.clicked.connect(self._do_restore)
        btn_row.addWidget(btn_restore)
        btn_del = QPushButton(_icon("delete"), "Supprimer")
        btn_del.clicked.connect(self._do_delete_snap)
        btn_row.addWidget(btn_del)
        sl2.addLayout(btn_row)
        sl2.addWidget(QLabel(
            "⚠ La restauration écrase la BDD active.\nRedémarrez l'application après.",
            wordWrap=True,
        ))
        right.addWidget(snap_box)
        root.addLayout(right, 1)

        self._refresh_db_stats()
        self._refresh_snapshots()
        return tab

    def _refresh_db_stats(self) -> None:
        try:
            svc = self._ctx.db_management_service
            stats = svc.get_stats(self._session)
            self._lbl_size.setText(f"Taille : {_human_size(stats.size_bytes)}")
            self._lbl_pages.setText(f"Pages : {stats.page_count} × {stats.page_size} o")
            self._lbl_frag.setText(f"Fragmentation : {stats.fragmentation_pct} %")
        except Exception as e:
            self._db_log(f"Erreur stats : {e}")

    def _do_vacuum(self) -> None:
        try:
            self._ctx.db_management_service.vacuum(self._session)
            self._db_log("VACUUM terminé.")
            self._refresh_db_stats()
        except Exception as e:
            self._db_log(f"VACUUM échoué : {e}")

    def _do_wal(self) -> None:
        try:
            self._ctx.db_management_service.wal_checkpoint(self._session)
            self._db_log("WAL checkpoint OK.")
        except Exception as e:
            self._db_log(f"Checkpoint échoué : {e}")

    def _do_integrity(self) -> None:
        try:
            issues = self._ctx.db_management_service.integrity_check(self._session)
            if not issues:
                self._db_log("Intégrité : OK — aucun problème détecté.")
            else:
                self._db_log("Problèmes détectés :\n" + "\n".join(issues))
        except Exception as e:
            self._db_log(f"Vérification échouée : {e}")

    def _refresh_snapshots(self) -> None:
        self._snap_list.clear()
        snaps = self._ctx.db_management_service.list_snapshots(self._session)
        for p in snaps:
            size = _human_size(p.stat().st_size)
            item = QListWidgetItem(f"{p.name}  ({size})")
            item.setData(Qt.ItemDataRole.UserRole, p)
            self._snap_list.addItem(item)

    def _selected_snap(self) -> Path | None:
        item = self._snap_list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _do_create_snap(self) -> None:
        try:
            dest = self._ctx.db_management_service.create_snapshot(self._session)
            self._db_log(f"Snapshot créé : {dest.name}")
            self._refresh_snapshots()
        except Exception as e:
            self._db_log(f"Erreur snapshot : {e}")

    def _do_restore(self) -> None:
        p = self._selected_snap()
        if not p:
            QMessageBox.warning(self, "Sélection", "Sélectionnez un snapshot à restaurer.")
            return
        confirm = QMessageBox.question(
            self, "Restaurer",
            f"Restaurer '{p.name}' ?\n\nCela écrasera la base de données active.\n"
            "L'application devra être redémarrée.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            self._ctx.db_management_service.restore_snapshot(self._session, p)
            self._db_log(f"Snapshot restauré : {p.name}\n→ Veuillez redémarrer l'application.")
        except Exception as e:
            self._db_log(f"Restauration échouée : {e}")

    def _do_delete_snap(self) -> None:
        p = self._selected_snap()
        if not p:
            return
        self._ctx.db_management_service.delete_snapshot(self._session, p)
        self._db_log(f"Snapshot supprimé : {p.name}")
        self._refresh_snapshots()

    def _db_log(self, msg: str) -> None:
        self._result_log.append(msg)

    # ── Affichage footer ─────────────────────────────────────────────────────

    def _apply(self) -> None:
        lang = "fr" if self._lang.currentIndex() == 0 else "ar"
        theme = "light" if self._theme.currentIndex() == 0 else "dark"
        self._ctx.settings_service.set_language(lang)
        self._ctx.settings_service.set_theme(theme)
        self._notif.show_message("Paramètres appliqués. Redémarrez pour le thème.", "info")

    def _open_numerotation(self) -> None:
        from garage_app.gui.admin.numerotation_window import NumerotationWindow
        mdi = self.mdiArea()
        if mdi:
            from garage_app.gui.window_registry import open_sub
            open_sub(mdi, NumerotationWindow(self._ctx, self._session))
