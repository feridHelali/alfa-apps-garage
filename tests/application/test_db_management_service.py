"""Unit tests for DbManagementService — uses in-memory SQLite."""
from __future__ import annotations

import uuid
from contextlib import contextmanager
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock

from garage_app.application.audit_service import AuditService
from garage_app.application.db_management_service import DbManagementService, DbStats
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.shared.exceptions import PermissionDeniedError
from garage_app.settings import AppSettings


# ─── Fake SessionFactory ──────────────────────────────────────────────────────

class FakeSessionFactory:
    def __init__(self, engine):
        self._factory = sessionmaker(bind=engine)

    @contextmanager
    def get_session(self):
        session = self._factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_db(tmp_path: Path):
    db_path = tmp_path / "garage.db"
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE test (id INTEGER PRIMARY KEY)"))
        conn.commit()
    return db_path, FakeSessionFactory(engine), tmp_path


@pytest.fixture
def audit_svc() -> AuditService:
    return AuditService(MagicMock())


@pytest.fixture
def settings(tmp_db) -> AppSettings:
    db_path, _, tmp_path = tmp_db
    s = AppSettings()
    s.db_path = str(db_path)
    s.snapshots_dir = str(tmp_path / "snapshots")
    return s


@pytest.fixture
def svc(tmp_db, settings, audit_svc) -> DbManagementService:
    _, session_factory, _ = tmp_db
    return DbManagementService(session_factory, settings, audit_svc)


@pytest.fixture
def superadmin() -> UserSession:
    return UserSession(
        user_id=uuid.uuid4(),
        username="superadmin",
        full_name="Super Admin",
        role="superadmin",
        permissions=frozenset(Permission),
    )


@pytest.fixture
def admin() -> UserSession:
    perms = frozenset(p for p in Permission if p != Permission.MANAGE_SNAPSHOTS)
    return UserSession(
        user_id=uuid.uuid4(),
        username="admin",
        full_name="Admin",
        role="admin",
        permissions=perms,
    )


# ─── Permission guard tests ────────────────────────────────────────────────────

def test_get_stats_blocked_for_admin(svc: DbManagementService, admin: UserSession) -> None:
    with pytest.raises(PermissionDeniedError):
        svc.get_stats(admin)


def test_vacuum_blocked_for_admin(svc: DbManagementService, admin: UserSession) -> None:
    with pytest.raises(PermissionDeniedError):
        svc.vacuum(admin)


def test_create_snapshot_blocked_for_admin(svc: DbManagementService, admin: UserSession) -> None:
    with pytest.raises(PermissionDeniedError):
        svc.create_snapshot(admin)


# ─── Stats tests ───────────────────────────────────────────────────────────────

def test_get_stats_returns_dataclass(svc: DbManagementService, superadmin: UserSession) -> None:
    stats = svc.get_stats(superadmin)
    assert isinstance(stats, DbStats)
    assert stats.page_size > 0
    assert stats.size_bytes > 0


def test_fragmentation_pct_zero_when_no_pages() -> None:
    stats = DbStats(page_count=0, page_size=4096, freelist_count=0)
    assert stats.fragmentation_pct == 0.0


def test_fragmentation_pct_calculated() -> None:
    stats = DbStats(page_count=100, page_size=4096, freelist_count=10)
    assert stats.fragmentation_pct == 10.0


# ─── Integrity check ─────────────────────────────────────────────────────────

def test_integrity_check_ok(svc: DbManagementService, superadmin: UserSession) -> None:
    issues = svc.integrity_check(superadmin)
    assert issues == []


# ─── Snapshot lifecycle ────────────────────────────────────────────────────────

def test_create_and_list_snapshot(
    svc: DbManagementService, superadmin: UserSession
) -> None:
    dest = svc.create_snapshot(superadmin)
    assert dest.exists()
    snaps = svc.list_snapshots(superadmin)
    assert dest in snaps


def test_delete_snapshot(svc: DbManagementService, superadmin: UserSession) -> None:
    dest = svc.create_snapshot(superadmin)
    svc.delete_snapshot(superadmin, dest)
    assert dest not in svc.list_snapshots(superadmin)


def test_restore_snapshot_copies_file(
    svc: DbManagementService, superadmin: UserSession, settings: AppSettings
) -> None:
    snap = svc.create_snapshot(superadmin)
    original_size = snap.stat().st_size
    svc.restore_snapshot(superadmin, snap)
    assert Path(settings.db_path).stat().st_size == original_size


def test_restore_missing_snapshot_raises(
    svc: DbManagementService, superadmin: UserSession, tmp_path: Path
) -> None:
    with pytest.raises(FileNotFoundError):
        svc.restore_snapshot(superadmin, tmp_path / "nonexistent.db")


def test_vacuum_runs_without_error(svc: DbManagementService, superadmin: UserSession) -> None:
    svc.vacuum(superadmin)


def test_wal_checkpoint_runs_without_error(svc: DbManagementService, superadmin: UserSession) -> None:
    svc.wal_checkpoint(superadmin)
