from __future__ import annotations

import re
from typing import Any


class DataBinder:
    """Resolves {field_name} placeholders in element values from a data dict."""

    _PLACEHOLDER = re.compile(r"\{(\w+)\}")

    @classmethod
    def bind(cls, template_value: str, data: dict[str, Any]) -> str:
        def replacer(m: re.Match) -> str:
            key = m.group(1)
            return str(data.get(key, m.group(0)))
        return cls._PLACEHOLDER.sub(replacer, template_value)

    @classmethod
    def bind_all(cls, elements_with_values: list[str], data: dict[str, Any]) -> list[str]:
        return [cls.bind(v, data) for v in elements_with_values]
