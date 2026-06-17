from __future__ import annotations

from sqlalchemy import Engine, create_engine, event, text


def create_db_engine(db_path: str) -> Engine:
    url = f"sqlite:///{db_path}"
    engine = create_engine(
        url,
        echo=False,
        future=True,
        connect_args={"timeout": 30, "check_same_thread": False},
        pool_pre_ping=True,
    )

    @event.listens_for(engine, "connect")
    def set_pragmas(dbapi_conn, _):  # type: ignore[misc]
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine
