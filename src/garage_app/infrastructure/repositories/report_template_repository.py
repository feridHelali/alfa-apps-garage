from __future__ import annotations

from garage_app.infrastructure.db.models.report_template_model import ReportTemplateModel
from garage_app.infrastructure.db.session import SessionFactory


class SqlAlchemyReportTemplateRepository:
    def __init__(self, sf: SessionFactory) -> None:
        self._sf = sf

    def find_all(self) -> list[ReportTemplateModel]:
        with self._sf.get_session() as s:
            return s.query(ReportTemplateModel).all()

    def get_by_name(self, name: str) -> ReportTemplateModel | None:
        with self._sf.get_session() as s:
            return s.query(ReportTemplateModel).filter_by(name=name).first()

    def save(self, template: ReportTemplateModel) -> None:
        with self._sf.get_session() as s:
            existing = s.query(ReportTemplateModel).filter_by(name=template.name).first()
            if existing:
                existing.json_body = template.json_body
                existing.category = template.category
            else:
                s.add(template)

    def delete(self, name: str) -> None:
        with self._sf.get_session() as s:
            m = s.query(ReportTemplateModel).filter_by(name=name).first()
            if m:
                s.delete(m)
