"""Integration tests for AuthService user-management methods — in-memory SQLite."""
from __future__ import annotations

import uuid

import pytest

from garage_app.application.auth_service import AuthService, AuthError
from garage_app.domain.shared.exceptions import PermissionDeniedError
from garage_app.infrastructure.repositories.user_repository import SqlAlchemyUserRepository
from garage_app.infrastructure.db.session import SessionFactory


@pytest.fixture
def user_repo(session_factory):
    return SqlAlchemyUserRepository(session_factory)


@pytest.fixture
def svc(session_factory, user_repo):
    return AuthService(session_factory, user_repo)


class TestLogin:
    def test_login_unknown_user_raises(self, svc):
        with pytest.raises(AuthError):
            svc.login("nobody", "pass")

    def test_login_creates_session(self, svc, superadmin_session):
        svc.create_user(superadmin_session, "alice", "Alice Dupont", "technicien", "Secret@1!")
        session = svc.login("alice", "Secret@1!")
        assert session.username == "alice"
        assert session.role == "technicien"

    def test_wrong_password_raises(self, svc, superadmin_session):
        svc.create_user(superadmin_session, "bob", "Bob", "technicien", "Correct@1!")
        with pytest.raises(AuthError):
            svc.login("bob", "wrong")


class TestCreateUser:
    def test_create_user_success(self, svc, superadmin_session):
        user = svc.create_user(superadmin_session, "charlie", "Charlie", "admin", "Pass@123!")
        assert user.username == "charlie"
        assert user.role == "admin"
        assert user.is_active is True

    def test_duplicate_username_raises(self, svc, superadmin_session):
        svc.create_user(superadmin_session, "diana", "Diana", "technicien", "Pass@1!")
        with pytest.raises(ValueError, match="déjà utilisé"):
            svc.create_user(superadmin_session, "diana", "Diana 2", "technicien", "Pass@1!")

    def test_invalid_role_raises(self, svc, superadmin_session):
        with pytest.raises(ValueError, match="inconnu"):
            svc.create_user(superadmin_session, "eve", "Eve", "hacker", "Pass@1!")

    def test_technicien_cannot_create_user(self, svc, tech_session):
        with pytest.raises(PermissionDeniedError):
            svc.create_user(tech_session, "frank", "Frank", "technicien", "Pass@1!")

    def test_admin_cannot_create_user(self, svc, admin_session):
        with pytest.raises(PermissionDeniedError):
            svc.create_user(admin_session, "george", "George", "technicien", "Pass@1!")


class TestUpdateUser:
    def test_update_full_name_and_role(self, svc, superadmin_session):
        user = svc.create_user(superadmin_session, "henry", "Henry", "technicien", "P@ss1!")
        updated = svc.update_user(superadmin_session, user.id, "Henry Updated", "admin")
        assert updated.full_name == "Henry Updated"
        assert updated.role == "admin"

    def test_update_not_found_raises(self, svc, superadmin_session):
        with pytest.raises(ValueError, match="introuvable"):
            svc.update_user(superadmin_session, uuid.uuid4(), "Name", "technicien")


class TestChangePassword:
    def test_change_password_allows_new_login(self, svc, superadmin_session):
        svc.create_user(superadmin_session, "ivan", "Ivan", "technicien", "OldPass@1!")
        user = svc.login("ivan", "OldPass@1!")
        svc.change_password(superadmin_session, user.user_id, "NewPass@1!")
        new_session = svc.login("ivan", "NewPass@1!")
        assert new_session.username == "ivan"

    def test_old_password_no_longer_works(self, svc, superadmin_session):
        svc.create_user(superadmin_session, "julia", "Julia", "technicien", "Old@Pass1!")
        user = svc.login("julia", "Old@Pass1!")
        svc.change_password(superadmin_session, user.user_id, "New@Pass1!")
        with pytest.raises(AuthError):
            svc.login("julia", "Old@Pass1!")


class TestDeactivateReactivate:
    def test_deactivate_prevents_login(self, svc, superadmin_session):
        svc.create_user(superadmin_session, "kevin", "Kevin", "technicien", "P@ss1!")
        user = svc.login("kevin", "P@ss1!")
        svc.deactivate_user(superadmin_session, user.user_id)
        with pytest.raises(AuthError, match="désactivé"):
            svc.login("kevin", "P@ss1!")

    def test_reactivate_allows_login(self, svc, superadmin_session):
        svc.create_user(superadmin_session, "lena", "Lena", "technicien", "P@ss1!")
        user = svc.login("lena", "P@ss1!")
        svc.deactivate_user(superadmin_session, user.user_id)
        svc.reactivate_user(superadmin_session, user.user_id)
        session = svc.login("lena", "P@ss1!")
        assert session.username == "lena"

    def test_cannot_deactivate_self(self, svc, superadmin_session):
        with pytest.raises(ValueError, match="propre compte"):
            svc.deactivate_user(superadmin_session, superadmin_session.user_id)


class TestListUsers:
    def test_list_returns_created_users(self, svc, superadmin_session):
        svc.create_user(superadmin_session, "mike", "Mike", "technicien", "P@ss1!")
        users = svc.list_users(superadmin_session)
        usernames = [u.username for u in users]
        assert "mike" in usernames

    def test_list_denied_for_technicien(self, svc, tech_session):
        with pytest.raises(PermissionDeniedError):
            svc.list_users(tech_session)
