from __future__ import annotations
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.models.dataset_manager import DatasetManager
from app.gui.main_window import MainWindow


def main() -> None:
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("StatX")

    dataset_manager = DatasetManager()
    window = MainWindow(dataset_manager)
    window.resize(1200, 800)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
