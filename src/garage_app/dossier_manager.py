from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

from garage_app.settings import APP_DATA_DIR


_INDEX_FILE = APP_DATA_DIR / "dossiers.json"


@dataclass
class DossierInfo:
    id: str
    nom: str
    societe: str
    chemin: str       # relative to APP_DATA_DIR or absolute
    cree_le: str
    dernier_acces: str

    def db_path(self) -> Path:
        p = Path(self.chemin)
        if not p.is_absolute():
            p = APP_DATA_DIR / p
        return p


class DossierManager:
    # ── Index I/O ────────────────────────────────────────────────────────────

    def _load(self) -> list[DossierInfo]:
        if not _INDEX_FILE.exists():
            self._bootstrap_from_default()
        try:
            raw = json.loads(_INDEX_FILE.read_text(encoding="utf-8"))
            return [DossierInfo(**d) for d in raw]
        except Exception:
            return []

    def _save(self, dossiers: list[DossierInfo]) -> None:
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        _INDEX_FILE.write_text(
            json.dumps([asdict(d) for d in dossiers], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _bootstrap_from_default(self) -> None:
        """Auto-create index from existing garage.db (transparent migration)."""
        default_db = APP_DATA_DIR / "garage.db"
        if default_db.exists():
            dossier = DossierInfo(
                id=str(uuid.uuid4()),
                nom="Dossier principal",
                societe="",
                chemin="garage.db",
                cree_le=datetime.now().isoformat(),
                dernier_acces=datetime.now().isoformat(),
            )
            self._save([dossier])
        else:
            self._save([])

    # ── Public API ───────────────────────────────────────────────────────────

    def list_dossiers(self) -> list[DossierInfo]:
        return self._load()

    def get_dossier(self, dossier_id: str) -> DossierInfo | None:
        return next((d for d in self._load() if d.id == dossier_id), None)

    def creer_dossier(self, nom: str, societe: str, chemin: str) -> DossierInfo:
        """Create the DB file with fresh schema + seed and register in the index."""
        db_path = Path(chemin) if Path(chemin).is_absolute() else APP_DATA_DIR / chemin

        if db_path.exists():
            raise FileExistsError(f"Le fichier '{db_path}' existe déjà.")

        # Bootstrap the new database
        from garage_app.infrastructure.db.engine import create_db_engine
        from garage_app.infrastructure.db.session import SessionFactory
        from garage_app.infrastructure.db.initializer import DatabaseInitializer

        engine = create_db_engine(str(db_path))
        sf = SessionFactory(engine)
        DatabaseInitializer(engine, sf).initialize()
        engine.dispose()

        rel_path = chemin if not Path(chemin).is_absolute() else db_path.name
        dossier = DossierInfo(
            id=str(uuid.uuid4()),
            nom=nom,
            societe=societe,
            chemin=rel_path,
            cree_le=datetime.now().isoformat(),
            dernier_acces=datetime.now().isoformat(),
        )
        dossiers = self._load()
        dossiers.append(dossier)
        self._save(dossiers)
        return dossier

    def touch_acces(self, dossier_id: str) -> None:
        """Update dernier_acces timestamp."""
        dossiers = self._load()
        for d in dossiers:
            if d.id == dossier_id:
                d.dernier_acces = datetime.now().isoformat()
        self._save(dossiers)

    def retirer_dossier(self, dossier_id: str) -> None:
        """Remove from index (does NOT delete the .db file)."""
        dossiers = [d for d in self._load() if d.id != dossier_id]
        self._save(dossiers)

    def has_multiple(self) -> bool:
        return len(self._load()) > 1
