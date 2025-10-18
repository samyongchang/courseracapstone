from __future__ import annotations
from typing import Callable
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox


class CorrelationSidebar(QWidget):
    def __init__(self, on_update: Callable[[str], None], parent=None) -> None:
        super().__init__(parent)
        self._on_update = on_update

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Method"))

        self.method_combo = QComboBox()
        self.method_combo.addItems(["pearson", "spearman"])
        self.method_combo.currentTextChanged.connect(self._emit_update)
        layout.addWidget(self.method_combo)

        layout.addStretch(1)

    def _emit_update(self, _: str) -> None:
        self._on_update(self.method_combo.currentText())
