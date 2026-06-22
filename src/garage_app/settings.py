from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

APP_VERSION = "1.0.0"


def _resolve_app_data_dir() -> Path:
    """Return data dir — reads installer-written data_dir.cfg when bundled."""
    if getattr(sys, "frozen", False):
        cfg = Path(sys.executable).parent / "data_dir.cfg"
        if cfg.exists():
            candidate = Path(cfg.read_text(encoding="utf-8").strip())
            if candidate.parts:
                return candidate
    return Path.home() / ".garage_reparation"


APP_DATA_DIR = _resolve_app_data_dir()
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
