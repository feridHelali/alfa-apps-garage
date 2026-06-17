from __future__ import annotations

from garage_app.application.decorators import require_permission
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.infrastructure.repositories.report_template_repository import SqlAlchemyReportTemplateRepository
from garage_app.infrastructure.db.models.report_template_model import ReportTemplateModel


class ReportService:
    def __init__(self, repo: SqlAlchemyReportTemplateRepository) -> None:
        self._repo = repo

    def list_templates(self) -> list[ReportTemplateModel]:
        return self._repo.find_all()

    def get_template(self, name: str) -> ReportTemplateModel | None:
        return self._repo.get_by_name(name)

    @require_permission(Permission.MANAGE_REPORTS)
    def save_template(self, session: UserSession, template: ReportTemplateModel) -> None:
        self._repo.save(template)

    @require_permission(Permission.MANAGE_REPORTS)
    def delete_template(self, session: UserSession, name: str) -> None:
        self._repo.delete(name)
