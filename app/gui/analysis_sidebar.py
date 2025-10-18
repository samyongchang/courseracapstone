from __future__ import annotations
from typing import Callable
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from app.gui.drop_target import DropTarget


class CrosstabSidebar(QWidget):
    def __init__(self, on_update: Callable[[list[str], list[str]], None], parent=None) -> None:
        super().__init__(parent)
        self._on_update = on_update
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Rows"))
        self.rows_target = DropTarget("Rows", on_changed=self._rows_changed)
        layout.addWidget(self.rows_target)
        layout.addWidget(QLabel("Columns"))
        self.cols_target = DropTarget("Columns", on_changed=self._cols_changed)
        layout.addWidget(self.cols_target)
        layout.addStretch(1)

    def _rows_changed(self, items: list[str]) -> None:
        self._on_update(items, self.cols_target.get_items())

    def _cols_changed(self, items: list[str]) -> None:
        self._on_update(self.rows_target.get_items(), items)


class DescriptivesSidebar(QWidget):
    def __init__(self, on_update: Callable[[list[str]], None], parent=None) -> None:
        super().__init__(parent)
        self._on_update = on_update
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Variables"))
        self.vars_target = DropTarget("Variables", on_changed=self._vars_changed)
        layout.addWidget(self.vars_target)
        layout.addStretch(1)

    def _vars_changed(self, items: list[str]) -> None:
        self._on_update(items)
