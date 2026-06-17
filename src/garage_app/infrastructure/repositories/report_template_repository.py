from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from garage_app.infrastructure.db.models.report_template_model import ReportTemplateModel


class SqlAlchemyReportTemplateRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def find_all(self) -> list[ReportTemplateModel]:
        return self._s.query(ReportTemplateModel).all()

    def get_by_name(self, name: str) -> ReportTemplateModel | None:
        return self._s.query(ReportTemplateModel).filter_by(name=name).first()

    def save(self, template: ReportTemplateModel) -> None:
        existing = self.get_by_name(template.name)
        if existing:
            existing.json_body = template.json_body
            existing.category = template.category
        else:
            self._s.add(template)

    def delete(self, name: str) -> None:
        m = self.get_by_name(name)
        if m:
            self._s.delete(m)
