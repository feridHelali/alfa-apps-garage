from __future__ import annotations

from sqlalchemy import Engine, inspect, text

from garage_app.infrastructure.db.base import Base
import garage_app.infrastructure.db.models  # noqa: F401 — registers all ORM models
from garage_app.infrastructure.db.session import SessionFactory
from garage_app.infrastructure.db.seed_runner import SeedRunner

# Migrations: (table, column, DDL snippet) — applied once, errors silently ignored
_COLUMN_MIGRATIONS = [
    # Sprint 02 — fournisseurs enrichment
    ("fournisseurs", "raison_sociale",        "ALTER TABLE fournisseurs ADD COLUMN raison_sociale TEXT NOT NULL DEFAULT ''"),
    ("fournisseurs", "contact_nom",           "ALTER TABLE fournisseurs ADD COLUMN contact_nom TEXT NOT NULL DEFAULT ''"),
    ("fournisseurs", "adresse",               "ALTER TABLE fournisseurs ADD COLUMN adresse TEXT NOT NULL DEFAULT ''"),
    ("fournisseurs", "delai_livraison_jours", "ALTER TABLE fournisseurs ADD COLUMN delai_livraison_jours INTEGER NOT NULL DEFAULT 7"),
    ("fournisseurs", "est_actif",             "ALTER TABLE fournisseurs ADD COLUMN est_actif INTEGER NOT NULL DEFAULT 1"),
    # Sprint 02 — pieces enrichment
    ("pieces", "emplacement", "ALTER TABLE pieces ADD COLUMN emplacement TEXT NOT NULL DEFAULT ''"),
    # Sprint 03 — factures enrichment
    ("factures", "client_id",     "ALTER TABLE factures ADD COLUMN client_id TEXT"),
    ("factures", "solde_restant", "ALTER TABLE factures ADD COLUMN solde_restant REAL NOT NULL DEFAULT 0"),
    ("factures", "statut",        "ALTER TABLE factures ADD COLUMN statut TEXT NOT NULL DEFAULT 'brouillon'"),
    ("factures", "est_flotte",    "ALTER TABLE factures ADD COLUMN est_flotte INTEGER NOT NULL DEFAULT 0"),
    ("factures", "notes",         "ALTER TABLE factures ADD COLUMN notes TEXT NOT NULL DEFAULT ''"),
    ("paiements", "reference",    "ALTER TABLE paiements ADD COLUMN reference TEXT NOT NULL DEFAULT ''"),
]


class DatabaseInitializer:
    def __init__(self, engine: Engine, session_factory: SessionFactory) -> None:
        self._engine = engine
        self._session_factory = session_factory

    def initialize(self) -> None:
        is_new = not inspect(self._engine).has_table("users")
        with self._engine.begin() as conn:
            Base.metadata.create_all(conn)
            self._apply_column_migrations(conn)
        if is_new:
            with self._session_factory.get_session() as session:
                SeedRunner(session).run()

    def _apply_column_migrations(self, conn) -> None:
        inspector = inspect(conn)
        for table, column, sql in _COLUMN_MIGRATIONS:
            if not inspector.has_table(table):
                continue
            existing = {c["name"] for c in inspector.get_columns(table)}
            if column not in existing:
                try:
                    conn.execute(text(sql))
                except Exception:
                    pass  # already exists or table absent
