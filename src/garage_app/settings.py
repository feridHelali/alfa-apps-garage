from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


APP_DATA_DIR = Path.home() / ".garage_reparation"
DB_PATH = APP_DATA_DIR / "garage.db"
SNAPSHOTS_DIR = APP_DATA_DIR / "snapshots"


@dataclass
class AppSettings:
    db_path: str = field(default_factory=lambda: str(DB_PATH))
    language: str = "fr"
    theme: str = "light"
    snapshots_dir: str = field(default_factory=lambda: str(SNAPSHOTS_DIR))
    company_name: str = "Mon Garage"

    @classmethod
    def ensure_dirs(cls) -> None:
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
