from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from garage_app.application.db_management_service import DbManagementService
from garage_app.domain.auth.user_session import UserSession


def _human_size(n: int) -> str:
    for unit in ("o", "Ko", "Mo", "Go"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} To"


class DbManagementWindow(QWidget):
    def __init__(self, svc: DbManagementService, session: UserSession) -> None:
        super().__init__()
        self._svc = svc
        self._session = session
        self.setWindowTitle("Gestion de la base de données")
        self.resize(800, 560)
        self._build_ui()
        self._refresh_stats()
        self._refresh_snapshots()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)

        # ── Left: stats + maintenance ─────────────────────────────────────
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

        btn_vacuum = QPushButton("VACUUM (compresser)")
        btn_vacuum.setToolTip("Récupère l'espace fragmenté. L'application peut être lente quelques secondes.")
        btn_vacuum.clicked.connect(self._do_vacuum)
        ml.addWidget(btn_vacuum)

        btn_wal = QPushButton("Checkpoint WAL")
        btn_wal.setToolTip("Force l'écriture du journal WAL dans la DB principale.")
        btn_wal.clicked.connect(self._do_wal)
        ml.addWidget(btn_wal)

        btn_integrity = QPushButton("Vérifier l'intégrité")
        btn_integrity.clicked.connect(self._do_integrity)
        ml.addWidget(btn_integrity)

        left.addWidget(maint_box)

        self._result_log = QTextEdit()
        self._result_log.setReadOnly(True)
        self._result_log.setMaximumHeight(160)
        left.addWidget(QLabel("Résultats :"))
        left.addWidget(self._result_log)
        left.addStretch()

        root.addLayout(left, 1)

        # ── Right: snapshots ──────────────────────────────────────────────
        right = QVBoxLayout()
        snap_box = QGroupBox("Snapshots / Sauvegardes")
        sl2 = QVBoxLayout(snap_box)

        self._snap_list = QListWidget()
        self._snap_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        sl2.addWidget(self._snap_list)

        btn_row = QHBoxLayout()
        btn_create = QPushButton("Créer snapshot")
        btn_create.clicked.connect(self._do_create_snap)
        btn_row.addWidget(btn_create)

        btn_restore = QPushButton("Restaurer")
        btn_restore.clicked.connect(self._do_restore)
        btn_row.addWidget(btn_restore)

        btn_del = QPushButton("Supprimer")
        btn_del.clicked.connect(self._do_delete_snap)
        btn_row.addWidget(btn_del)
        sl2.addLayout(btn_row)

        sl2.addWidget(QLabel(
            "⚠ La restauration écrase la BDD active.\nL'application doit être redémarrée.",
            wordWrap=True,
        ))
        right.addWidget(snap_box)
        root.addLayout(right, 1)

    # ── Stats ─────────────────────────────────────────────────────────────

    def _refresh_stats(self) -> None:
        try:
            stats = self._svc.get_stats(self._session)
            self._lbl_size.setText(f"Taille : {_human_size(stats.size_bytes)}")
            self._lbl_pages.setText(f"Pages : {stats.page_count} × {stats.page_size} o")
            self._lbl_frag.setText(f"Fragmentation : {stats.fragmentation_pct} %")
        except Exception as e:
            self._log(f"Erreur stats : {e}")

    # ── Maintenance ───────────────────────────────────────────────────────

    def _do_vacuum(self) -> None:
        try:
            self._svc.vacuum(self._session)
            self._log("VACUUM terminé.")
            self._refresh_stats()
        except Exception as e:
            self._log(f"VACUUM échoué : {e}")

    def _do_wal(self) -> None:
        try:
            self._svc.wal_checkpoint(self._session)
            self._log("WAL checkpoint OK.")
        except Exception as e:
            self._log(f"Checkpoint échoué : {e}")

    def _do_integrity(self) -> None:
        try:
            issues = self._svc.integrity_check(self._session)
            if not issues:
                self._log("Intégrité : OK — aucun problème détecté.")
            else:
                self._log("Problèmes détectés :\n" + "\n".join(issues))
        except Exception as e:
            self._log(f"Vérification échouée : {e}")

    # ── Snapshots ─────────────────────────────────────────────────────────

    def _refresh_snapshots(self) -> None:
        self._snap_list.clear()
        snaps = self._svc.list_snapshots(self._session)
        for p in snaps:
            size = _human_size(p.stat().st_size)
            item = QListWidgetItem(f"{p.name}  ({size})")
            item.setData(Qt.ItemDataRole.UserRole, p)
            self._snap_list.addItem(item)

    def _selected_snap(self) -> Path | None:
        item = self._snap_list.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None

    def _do_create_snap(self) -> None:
        try:
            dest = self._svc.create_snapshot(self._session)
            self._log(f"Snapshot créé : {dest.name}")
            self._refresh_snapshots()
        except Exception as e:
            self._log(f"Erreur snapshot : {e}")

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
            self._svc.restore_snapshot(self._session, p)
            self._log(f"Snapshot restauré : {p.name}\n→ Veuillez redémarrer l'application.")
        except Exception as e:
            self._log(f"Restauration échouée : {e}")

    def _do_delete_snap(self) -> None:
        p = self._selected_snap()
        if not p:
            return
        self._svc.delete_snapshot(self._session, p)
        self._log(f"Snapshot supprimé : {p.name}")
        self._refresh_snapshots()

    def _log(self, msg: str) -> None:
        self._result_log.append(msg)
