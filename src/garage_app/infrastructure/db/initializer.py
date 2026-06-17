from __future__ import annotations

from sqlalchemy import Engine, inspect, text

from garage_app.infrastructure.db.base import Base
import garage_app.infrastructure.db.models  # noqa: F401 — registers all ORM models
from garage_app.infrastructure.db.session import SessionFactory
from garage_app.infrastructure.db.seed_runner import SeedRunner


class DatabaseInitializer:
    def __init__(self, engine: Engine, session_factory: SessionFactory) -> None:
        self._engine = engine
        self._session_factory = session_factory

    def initialize(self) -> None:
        is_new = not inspect(self._engine).has_table("users")
        Base.metadata.create_all(self._engine)
        if is_new:
            with self._session_factory.get_session() as session:
                SeedRunner(session).run()
