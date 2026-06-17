from __future__ import annotations

import json
from pathlib import Path

import bcrypt
from sqlalchemy.orm import Session

from garage_app.infrastructure.db.models.user_model import RoleModel, UserModel
from garage_app.infrastructure.db.models.societe_model import SocieteModel
from garage_app.infrastructure.db.models.report_template_model import ReportTemplateModel
from garage_app.infrastructure.db.models.settings_model import AppSettingsModel

_SEED_FILE = Path(__file__).parents[4] / "resources" / "seed" / "seed_data.json"


class SeedRunner:
    def __init__(self, session: Session) -> None:
        self._s = session

    def run(self) -> None:
        data = json.loads(_SEED_FILE.read_text(encoding="utf-8"))
        self._seed_roles(data["roles"])
        self._seed_users(data["users"])
        self._seed_societe(data["societe"])
        self._seed_settings(data["settings"])
        self._seed_report_templates(data["report_templates"])

    def _seed_roles(self, roles: list[dict]) -> None:
        for r in roles:
            if not self._s.get(RoleModel, r["name"]):
                self._s.add(RoleModel(**r))

    def _seed_users(self, users: list[dict]) -> None:
        for u in users:
            if not self._s.query(UserModel).filter_by(username=u["username"]).first():
                pw_hash = bcrypt.hashpw(u["password"].encode(), bcrypt.gensalt())
                self._s.add(UserModel(
                    username=u["username"],
                    password_hash=pw_hash,
                    full_name=u["full_name"],
                    role=u["role"],
                ))

    def _seed_societe(self, data: dict) -> None:
        if not self._s.get(SocieteModel, 1):
            self._s.add(SocieteModel(id=1, **data))

    def _seed_settings(self, settings: dict) -> None:
        for key, value in settings.items():
            if not self._s.get(AppSettingsModel, key):
                self._s.add(AppSettingsModel(key=key, value=str(value)))

    def _seed_report_templates(self, templates: list[dict]) -> None:
        for t in templates:
            if not self._s.query(ReportTemplateModel).filter_by(name=t["name"]).first():
                self._s.add(ReportTemplateModel(
                    name=t["name"],
                    category=t.get("category", "general"),
                    json_body=json.dumps(t["body"], ensure_ascii=False),
                ))
