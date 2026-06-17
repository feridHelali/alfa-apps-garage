from __future__ import annotations

from PyQt6.QtCore import Qt, QSortFilterProxyModel
from PyQt6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QLineEdit,
    QTableView, QVBoxLayout, QWidget,
)


class SearchableTableWidget(QWidget):
    """QTableView with a search bar on top wired to a sort/filter proxy model."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._proxy = QSortFilterProxyModel(self)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy.setFilterKeyColumn(-1)  # search all columns

        self._search = QLineEdit()
        self._search.setPlaceholderText("Rechercher…")
        self._search.textChanged.connect(self._proxy.setFilterFixedString)

        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(True)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self._search)
        layout.addWidget(self._table)

    def set_source_model(self, model) -> None:  # type: ignore[no-untyped-def]
        self._proxy.setSourceModel(model)

    @property
    def table(self) -> QTableView:
        return self._table

    @property
    def proxy(self) -> QSortFilterProxyModel:
        return self._proxy
