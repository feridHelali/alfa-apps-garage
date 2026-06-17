from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Element:
    type: str                   # text | field | image | line | box
    x: float = 0
    y: float = 0
    w: float = 100
    h: float = 20
    value: str = ""             # literal or {field_name}
    font_size: int = 10
    bold: bool = False
    align: str = "left"         # left | center | right


@dataclass
class Band:
    type: str                   # header | detail | footer | group_header | group_footer
    height: float = 40
    datasource: str = ""        # name of the data list for detail bands
    elements: list[Element] = field(default_factory=list)


@dataclass
class ReportTemplate:
    template_id: str = ""
    title: dict[str, str] = field(default_factory=dict)  # {"fr": "...", "en": "..."}
    paper_size: str = "A4"
    orientation: str = "portrait"
    bands: list[Band] = field(default_factory=list)
