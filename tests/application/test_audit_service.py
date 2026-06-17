"""Unit tests for AuditService — uses an in-memory fake repository."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Sequence
from unittest.mock import MagicMock
import uuid

import pytest

from garage_app.application.audit_service import AuditService
from garage_app.domain.audit.audit_entry import AuditEntry, LogCategory, LogLevel
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.shared.exceptions import PermissionDeniedError
from garage_app.infrastructure.repositories.audit_log_repository import AuditLogRepository


# ─── Fake repo ────────────────────────────────────────────────────────────────

class FakeAuditRepo:
    def __init__(self) -> None:
        self._store: list[AuditEntry] = []

    def save(self, entry: AuditEntry) -> None:
        self._store.append(entry)

    def find_recent(
        self,
        limit: int = 500,
        *,
        category=None,
        level=None,
        username=None,
        entity_type=None,
        since=None,
    ) -> list[AuditEntry]:
        rows = list(self._store)
        if category:
            rows = [r for r in rows if r.category == category]
        if level:
            rows = [r for r in rows if r.level == level]
        if username:
            rows = [r for r in rows if r.username and username in r.username]
        if since:
            rows = [r for r in rows if r.occurred_at >= since]
        return rows[-limit:]


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def repo() -> FakeAuditRepo:
    return FakeAuditRepo()


@pytest.fixture
def svc(repo: FakeAuditRepo) -> AuditService:
    return AuditService(repo)  # type: ignore[arg-type]


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
def technicien() -> UserSession:
    return UserSession(
        user_id=uuid.uuid4(),
        username="tech1",
        full_name="Technicien",
        role="technicien",
        permissions=frozenset({Permission.VIEW_DOSSIERS}),
    )


# ─── Write tests ──────────────────────────────────────────────────────────────

def test_log_auth_success_writes_info(svc: AuditService, repo: FakeAuditRepo) -> None:
    svc.log_auth("Connexion réussie", username="alice", success=True)
    assert len(repo._store) == 1
    entry = repo._store[0]
    assert entry.level == LogLevel.INFO
    assert entry.category == LogCategory.AUTH
    assert entry.username == "alice"


def test_log_auth_failure_writes_warning(svc: AuditService, repo: FakeAuditRepo) -> None:
    svc.log_auth("Mot de passe incorrect", username="bob", success=False)
    entry = repo._store[0]
    assert entry.level == LogLevel.WARNING


def test_log_business_sets_entity(svc: AuditService, repo: FakeAuditRepo, superadmin: UserSession) -> None:
    svc.log_business(
        "Dossier → EN_COURS",
        session=superadmin,
        entity_type="DossierReparation",
        entity_id="abc-123",
    )
    entry = repo._store[0]
    assert entry.category == LogCategory.BUSINESS
    assert entry.entity_type == "DossierReparation"
    assert entry.entity_id == "abc-123"
    assert entry.username == "superadmin"


def test_log_system_writes_system_category(svc: AuditService, repo: FakeAuditRepo) -> None:
    svc.log_system("Application démarrée")
    assert repo._store[0].category == LogCategory.SYSTEM


def test_log_error_writes_error_level(svc: AuditService, repo: FakeAuditRepo) -> None:
    svc.log_error("Exception inattendue", extra={"traceback": "..."})
    entry = repo._store[0]
    assert entry.level == LogLevel.ERROR
    assert entry.extra is not None


# ─── Read / access control tests ──────────────────────────────────────────────

def test_find_recent_requires_superadmin(svc: AuditService, technicien: UserSession) -> None:
    with pytest.raises(PermissionDeniedError):
        svc.find_recent(technicien)


def test_find_recent_superadmin_sees_all(
    svc: AuditService, repo: FakeAuditRepo, superadmin: UserSession
) -> None:
    svc.log_system("boot")
    svc.log_auth("login", username="u", success=True)
    results = svc.find_recent(superadmin)
    assert len(results) == 2


def test_find_recent_filter_by_category(
    svc: AuditService, repo: FakeAuditRepo, superadmin: UserSession
) -> None:
    svc.log_system("boot")
    svc.log_auth("login", username="u", success=True)
    results = svc.find_recent(superadmin, category=LogCategory.AUTH)
    assert all(e.category == LogCategory.AUTH for e in results)
    assert len(results) == 1


def test_find_recent_filter_by_since(
    svc: AuditService, repo: FakeAuditRepo, superadmin: UserSession
) -> None:
    old = AuditEntry.info(LogCategory.SYSTEM, "old event")
    old_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
    object.__setattr__(old, "occurred_at", old_time)
    repo._store.append(old)
    svc.log_system("recent event")
    since = datetime(2024, 1, 1, tzinfo=timezone.utc)
    results = svc.find_recent(superadmin, since=since)
    assert all(e.occurred_at >= since for e in results)
