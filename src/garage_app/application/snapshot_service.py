from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from garage_app.application.decorators import require_permission
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.settings import AppSettings


class SnapshotService:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    @require_permission(Permission.MANAGE_SNAPSHOTS)
    def create(self, session: UserSession) -> Path:
        db = Path(self._settings.db_path)
        snapshots = Path(self._settings.snapshots_dir)
        snapshots.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest = snapshots / f"garage_{ts}.db"
        shutil.copy2(db, dest)
        return dest

    @require_permission(Permission.MANAGE_SNAPSHOTS)
    def restore(self, session: UserSession, snapshot_path: str) -> None:
        db = Path(self._settings.db_path)
        shutil.copy2(snapshot_path, db)

    @require_permission(Permission.MANAGE_SNAPSHOTS)
    def list_snapshots(self, session: UserSession) -> list[Path]:
        snapshots = Path(self._settings.snapshots_dir)
        if not snapshots.exists():
            return []
        return sorted(snapshots.glob("*.db"), reverse=True)
