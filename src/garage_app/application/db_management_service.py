from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text

from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.auth.permission import Permission
from garage_app.application.audit_service import AuditService
from garage_app.infrastructure.db.session import SessionFactory
from garage_app.settings import AppSettings


@dataclass(frozen=True)
class DbStats:
    page_count: int
    page_size: int
    freelist_count: int

    @property
    def size_bytes(self) -> int:
        return self.page_count * self.page_size

    @property
    def fragmentation_pct(self) -> float:
        if self.page_count == 0:
            return 0.0
        return round(self.freelist_count / self.page_count * 100, 1)


class DbManagementService:
    """
    Self-service database maintenance — superadmin only.
    Covers: stats, VACUUM, integrity check, WAL checkpoint, snapshots.
    """

    def __init__(
        self,
        session_factory: SessionFactory,
        settings: AppSettings,
        audit: AuditService,
    ) -> None:
        self._sf = session_factory
        self._settings = settings
        self._audit = audit

    @property
    def _db_path(self) -> Path:
        return Path(self._settings.db_path)

    @property
    def _snapshots_dir(self) -> Path:
        return Path(self._settings.snapshots_dir)

    def _guard(self, session: UserSession) -> None:
        session.require(Permission.MANAGE_SNAPSHOTS)

    # ─── Stats ───────────────────────────────────────────────────────────────

    def get_stats(self, session: UserSession) -> DbStats:
        self._guard(session)
        with self._sf.get_session() as s:
            page_count = s.execute(text("PRAGMA page_count")).scalar()
            page_size = s.execute(text("PRAGMA page_size")).scalar()
            freelist = s.execute(text("PRAGMA freelist_count")).scalar()
        return DbStats(
            page_count=int(page_count or 0),
            page_size=int(page_size or 4096),
            freelist_count=int(freelist or 0),
        )

    # ─── VACUUM ──────────────────────────────────────────────────────────────

    def vacuum(self, session: UserSession) -> None:
        """Reclaims fragmented space. Rewrites entire DB file — takes a moment."""
        self._guard(session)
        with self._sf.get_session() as s:
            s.execute(text("VACUUM"))
        self._audit.log_db("VACUUM exécuté", username=session.username)

    # ─── WAL checkpoint ──────────────────────────────────────────────────────

    def wal_checkpoint(self, session: UserSession) -> None:
        self._guard(session)
        with self._sf.get_session() as s:
            s.execute(text("PRAGMA wal_checkpoint(FULL)"))
        self._audit.log_db("WAL checkpoint exécuté", username=session.username)

    # ─── Integrity check ─────────────────────────────────────────────────────

    def integrity_check(self, session: UserSession) -> list[str]:
        """Returns list of issues, empty list means OK."""
        self._guard(session)
        with self._sf.get_session() as s:
            rows = s.execute(text("PRAGMA integrity_check")).fetchall()
        results = [r[0] for r in rows]
        ok = results == ["ok"]
        msg = "Integrity check: OK" if ok else f"Integrity check: {len(results)} erreur(s)"
        self._audit.log_db(msg, username=session.username)
        return [] if ok else results

    # ─── Snapshots ───────────────────────────────────────────────────────────

    def list_snapshots(self, session: UserSession) -> list[Path]:
        self._guard(session)
        if not self._snapshots_dir.exists():
            return []
        return sorted(self._snapshots_dir.glob("*.db"), reverse=True)

    def create_snapshot(self, session: UserSession) -> Path:
        self._guard(session)
        self._snapshots_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest = self._snapshots_dir / f"garage_{ts}.db"
        shutil.copy2(self._db_path, dest)
        self._audit.log_db(f"Snapshot créé : {dest.name}", username=session.username)
        return dest

    def restore_snapshot(self, session: UserSession, snapshot_path: Path) -> None:
        """Overwrites the live DB. The caller must restart the application after this."""
        self._guard(session)
        if not snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot introuvable : {snapshot_path}")
        shutil.copy2(snapshot_path, self._db_path)
        self._audit.log_db(
            f"Snapshot restauré : {snapshot_path.name}", username=session.username
        )

    def delete_snapshot(self, session: UserSession, snapshot_path: Path) -> None:
        self._guard(session)
        snapshot_path.unlink(missing_ok=True)
        self._audit.log_db(
            f"Snapshot supprimé : {snapshot_path.name}", username=session.username
        )
