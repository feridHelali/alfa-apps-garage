"""Unit tests for the @require_permission decorator."""
import pytest

from garage_app.application.decorators import require_permission
from garage_app.domain.auth.permission import Permission
from garage_app.domain.shared.exceptions import PermissionDeniedError


class _FakeService:
    @require_permission(Permission.MANAGE_USERS)
    def admin_only(self, session, value: str) -> str:
        return f"ok:{value}"


class TestRequirePermission:
    def test_superadmin_passes(self, superadmin_session):
        svc = _FakeService()
        result = svc.admin_only(superadmin_session, "test")
        assert result == "ok:test"

    def test_technicien_denied(self, tech_session):
        svc = _FakeService()
        with pytest.raises(PermissionDeniedError):
            svc.admin_only(tech_session, "test")

    def test_admin_denied_for_superadmin_perm(self, admin_session):
        svc = _FakeService()
        with pytest.raises(PermissionDeniedError):
            svc.admin_only(admin_session, "test")
