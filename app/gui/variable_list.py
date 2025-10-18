from __future__ import annotations
from typing import List
from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtCore import Qt, QMimeData


class VariableList(QListWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self.setDragEnabled(True)
        self.setDefaultDropAction(Qt.CopyAction)

    def set_variables(self, variables: List[str]) -> None:
        self.clear()
        for var in variables:
            item = QListWidgetItem(var)
            item.setFlags(item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.addItem(item)

    def mimeData(self, items: list[QListWidgetItem]) -> QMimeData:  # type: ignore[override]
        """Provide plain-text payload for drag operations.

        Items are joined by newlines so drop targets can parse multiple selections.
        """
        mime = QMimeData()
        text = "\n".join(it.text() for it in items)
        mime.setText(text)
        return mime
