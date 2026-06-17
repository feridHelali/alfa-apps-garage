from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker


class SessionFactory:
    def __init__(self, engine: Engine) -> None:
        self._factory = sessionmaker(bind=engine, expire_on_commit=False)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        session: Session = self._factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
