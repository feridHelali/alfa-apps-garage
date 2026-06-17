from __future__ import annotations

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QMdiSubWindow,
    QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.gui.widgets.notification_bar import NotificationBar


class SnapshotWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self.setWindowTitle("Snapshots de la base de données")
        self.setWindowIcon(QIcon.fromTheme("drive-harddisk"))
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self._notif = NotificationBar()
        layout.addWidget(self._notif)
        self._list = QListWidget()
        layout.addWidget(self._list)
        btn_row = QHBoxLayout()
        btn_create = QPushButton(QIcon.fromTheme("document-save"), "Créer snapshot")
        btn_create.clicked.connect(self._create)
        btn_restore = QPushButton(QIcon.fromTheme("edit-undo"), "Restaurer")
        btn_restore.clicked.connect(self._restore)
        btn_row.addWidget(btn_create)
        btn_row.addWidget(btn_restore)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        self.setWidget(widget)
        self.resize(600, 350)

    def _load(self) -> None:
        self._list.clear()
        for p in self._ctx.snapshot_service.list_snapshots(self._session):
            self._list.addItem(p.name)

    def _create(self) -> None:
        try:
            path = self._ctx.snapshot_service.create(self._session)
            self._notif.show_message(f"Snapshot créé : {path.name}", "success")
            self._load()
        except Exception as e:
            self._notif.show_message(str(e), "error")

    def _restore(self) -> None:
        item = self._list.currentItem()
        if not item:
            return
        from garage_app.gui.widgets.confirm_dialog import confirm
        if confirm(self, "Restaurer", f"Restaurer le snapshot '{item.text()}' ? L'application va redémarrer."):
            import sys
            from pathlib import Path
            from garage_app.settings import SNAPSHOTS_DIR
            path = SNAPSHOTS_DIR / item.text()
            try:
                self._ctx.snapshot_service.restore(self._session, str(path))
                self._notif.show_message("Snapshot restauré. Redémarrez l'application.", "warning")
            except Exception as e:
                self._notif.show_message(str(e), "error")
