from __future__ import annotations
from PySide6.QtWidgets import QTextEdit


class OutputPane(QTextEdit):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setAcceptRichText(True)

    def show_html(self, html: str) -> None:
        self.setHtml(html)

    def append_html(self, html: str) -> None:
        self.append(html)
