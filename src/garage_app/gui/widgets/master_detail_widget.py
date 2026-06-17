from __future__ import annotations

from PyQt6.QtWidgets import QSplitter, QWidget
from PyQt6.QtCore import Qt


class MasterDetailWidget(QSplitter):
    """
    Generic Master/Detail container.
    Left side = master list (QWidget), right side = detail form (QWidget).
    Caller wires the selection-change signal to refresh the detail panel.
    """

    def __init__(
        self,
        master: QWidget,
        detail: QWidget,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.addWidget(master)
        self.addWidget(detail)
        self.setSizes([350, 650])
        self.setChildrenCollapsible(False)
