from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from garage_app.infrastructure.db.base import Base
import garage_app.infrastructure.db.models  # noqa: F401
from garage_app.infrastructure.db.session import SessionFactory
from garage_app.domain.auth.permission import ROLE_PERMISSIONS
from garage_app.domain.auth.user_session import UserSession
import uuid


@pytest.fixture(scope="function")
def engine():
    e = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(e)
    return e


@pytest.fixture(scope="function")
def session_factory(engine):
    return SessionFactory(engine)


@pytest.fixture
def superadmin_session() -> UserSession:
    return UserSession(
        user_id=uuid.uuid4(),
        username="admin",
        full_name="Admin",
        role="superadmin",
        permissions=ROLE_PERMISSIONS["superadmin"],
    )


@pytest.fixture
def admin_session() -> UserSession:
    return UserSession(
        user_id=uuid.uuid4(),
        username="mgr",
        full_name="Manager",
        role="admin",
        permissions=ROLE_PERMISSIONS["admin"],
    )


@pytest.fixture
def tech_session() -> UserSession:
    return UserSession(
        user_id=uuid.uuid4(),
        username="tech1",
        full_name="Technicien 1",
        role="technicien",
        permissions=ROLE_PERMISSIONS["technicien"],
    )
