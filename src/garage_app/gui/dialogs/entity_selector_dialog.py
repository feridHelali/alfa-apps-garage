from __future__ import annotations

import uuid

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QLineEdit, QListWidget,
    QListWidgetItem, QVBoxLayout, QWidget,
)


class EntitySelectorDialog(QDialog):
    """Generic single-entity selection dialog with live search filter."""

    def __init__(
        self,
        title: str,
        items: list[tuple[uuid.UUID, str]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        self._all_items = items
        self._selected_id: uuid.UUID | None = None

        layout = QVBoxLayout(self)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Rechercher…")
        self._search.textChanged.connect(self._filter)
        layout.addWidget(self._search)

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self._list)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self._populate(items)
        self.resize(440, 360)

    def _populate(self, items: list[tuple[uuid.UUID, str]]) -> None:
        self._list.clear()
        for entity_id, label in items:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, entity_id)
            self._list.addItem(item)
        if self._list.count():
            self._list.setCurrentRow(0)

    def _filter(self, text: str) -> None:
        q = text.lower()
        filtered = [(eid, lbl) for eid, lbl in self._all_items if q in lbl.lower()]
        self._populate(filtered)

    def _on_accept(self) -> None:
        current = self._list.currentItem()
        if current:
            self._selected_id = current.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def _on_double_click(self, item: QListWidgetItem) -> None:
        self._selected_id = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    @property
    def selected_id(self) -> uuid.UUID | None:
        return self._selected_id
