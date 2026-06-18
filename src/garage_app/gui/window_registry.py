from __future__ import annotations

from typing import Any, Type

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMdiArea, QMdiSubWindow

_SUB_FLAGS = (
    Qt.WindowType.SubWindow
    | Qt.WindowType.WindowTitleHint
    | Qt.WindowType.WindowSystemMenuHint
    | Qt.WindowType.WindowMinMaxButtonsHint
    | Qt.WindowType.WindowCloseButtonHint
)


class WindowRegistry:
    """Ensures only one instance per sub-window type is open at a time."""

    def __init__(self, mdi_area: QMdiArea) -> None:
        self._area = mdi_area
        self._open: dict[type, QMdiSubWindow] = {}

    def open_or_activate(self, window_cls: Type, *args: Any, **kwargs: Any) -> None:
        existing = self._open.get(window_cls)
        if existing and existing in self._area.subWindowList():
            self._area.setActiveSubWindow(existing)
            existing.showNormal()
            return
        widget = window_cls(*args, **kwargs)
        sub = self._area.addSubWindow(widget)
        sub.setWindowFlags(_SUB_FLAGS)
        sub.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        sub.destroyed.connect(lambda: self._open.pop(window_cls, None))
        self._open[window_cls] = sub
        sub.show()
