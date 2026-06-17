from __future__ import annotations

import json

from garage_app.tools.report_engine.template_schema import Band, Element, ReportTemplate


class TemplateLoader:
    @staticmethod
    def from_json(json_str: str) -> ReportTemplate:
        data = json.loads(json_str)
        bands = []
        for b in data.get("bands", []):
            elements = [Element(**e) for e in b.get("elements", [])]
            bands.append(Band(
                type=b["type"],
                height=b.get("height", 40),
                datasource=b.get("datasource", ""),
                elements=elements,
            ))
        return ReportTemplate(
            template_id=data.get("templateId", ""),
            title=data.get("title", {}),
            paper_size=data.get("paperSize", "A4"),
            orientation=data.get("orientation", "portrait"),
            bands=bands,
        )

    @staticmethod
    def to_json(template: ReportTemplate) -> str:
        import dataclasses
        return json.dumps(dataclasses.asdict(template), ensure_ascii=False, indent=2)
