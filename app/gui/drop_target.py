from __future__ import annotations
from typing import Callable, Optional
from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtCore import Qt, QMimeData


class DropTarget(QListWidget):
    def __init__(self, title: str, on_changed: Optional[Callable[[list[str]], None]] = None, parent=None) -> None:
        super().__init__(parent)
        self._title = title
        self._on_changed = on_changed
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasText() or event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasText():
            text = event.mimeData().text()
            for token in [t.strip() for t in text.split("\n") if t.strip()]:
                self._add_item(token)
            event.acceptProposedAction()
            self._emit_changed()
        else:
            super().dropEvent(event)

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            for item in self.selectedItems():
                self.takeItem(self.row(item))
            self._emit_changed()
        else:
            super().keyPressEvent(event)

    def _add_item(self, text: str) -> None:
        # Prevent duplicates
        existing = [self.item(i).text() for i in range(self.count())]
        if text not in existing:
            self.addItem(QListWidgetItem(text))

    def get_items(self) -> list[str]:
        return [self.item(i).text() for i in range(self.count())]

    def clear_items(self) -> None:
        self.clear()
        self._emit_changed()

    def _emit_changed(self) -> None:
        if self._on_changed:
            self._on_changed(self.get_items())
