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
        def _element_dict(e: Element) -> dict:
            return {
                "type": e.type, "x": e.x, "y": e.y, "w": e.w, "h": e.h,
                "value": e.value, "font_size": e.font_size,
                "bold": e.bold, "align": e.align,
            }

        def _band_dict(b: Band) -> dict:
            return {
                "type": b.type, "height": b.height,
                "datasource": b.datasource,
                "elements": [_element_dict(e) for e in b.elements],
            }

        payload = {
            "templateId": template.template_id,
            "title": template.title,
            "paperSize": template.paper_size,
            "orientation": template.orientation,
            "bands": [_band_dict(b) for b in template.bands],
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)
