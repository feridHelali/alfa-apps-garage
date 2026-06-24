from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

APP_VERSION = "1.0.0"


def resource_path(*parts: str) -> Path:
    """Return path to a bundled resource, works both frozen (PyInstaller) and in dev.

    In a PyInstaller onedir bundle the src/ directory level is stripped, so
    sys._MEIPASS is the bundle root where assets/ and resources/ live.
    In development the project root is two levels above this file
    (src/garage_app/settings.py → parents[2]).
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS).joinpath(*parts)  # type: ignore[attr-defined]
    return Path(__file__).parents[2].joinpath(*parts)


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
