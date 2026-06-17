"""Tests for the report engine template loader and data binder."""
import json

import pytest

from garage_app.tools.report_engine.template_loader import TemplateLoader
from garage_app.tools.report_engine.data_binder import DataBinder
from garage_app.tools.report_engine.template_schema import ReportTemplate


SAMPLE_JSON = json.dumps({
    "templateId": "test_v1",
    "title": {"fr": "Test", "en": "Test"},
    "paperSize": "A4",
    "orientation": "portrait",
    "bands": [
        {
            "type": "header",
            "height": 40,
            "elements": [
                {"type": "field", "x": 0, "y": 0, "w": 100, "h": 20,
                 "value": "N° {numero}", "font_size": 10, "bold": False, "align": "left"}
            ]
        }
    ]
})


class TestTemplateLoader:
    def test_loads_template(self):
        t = TemplateLoader.from_json(SAMPLE_JSON)
        assert isinstance(t, ReportTemplate)
        assert t.template_id == "test_v1"
        assert len(t.bands) == 1
        assert t.bands[0].type == "header"
        assert len(t.bands[0].elements) == 1

    def test_round_trip(self):
        t = TemplateLoader.from_json(SAMPLE_JSON)
        json_out = TemplateLoader.to_json(t)
        t2 = TemplateLoader.from_json(json_out)
        assert t2.template_id == t.template_id


class TestDataBinder:
    def test_binds_field(self):
        result = DataBinder.bind("N° {numero}", {"numero": "F2025-0001"})
        assert result == "N° F2025-0001"

    def test_missing_field_keeps_placeholder(self):
        result = DataBinder.bind("{missing}", {})
        assert result == "{missing}"

    def test_multiple_fields(self):
        result = DataBinder.bind("{a} / {b}", {"a": "foo", "b": "bar"})
        assert result == "foo / bar"
