from __future__ import annotations
from typing import List
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QSplitter,
    QTabWidget,
)
from PySide6.QtCore import Qt

from app.models.dataset_manager import DatasetManager
from app.gui.variable_list import VariableList
from app.gui.output_pane import OutputPane
from app.gui.analysis_sidebar import CrosstabSidebar, DescriptivesSidebar
from app.gui.correlation_sidebar import CorrelationSidebar
from app.analysis.crosstab import run_crosstab
from app.analysis.descriptives import run_descriptives
from app.analysis.correlation import run_correlation


class MainWindow(QMainWindow):
    def __init__(self, dataset_manager: DatasetManager, parent=None) -> None:
        super().__init__(parent)
        self.dataset_manager = dataset_manager

        self.setWindowTitle("StatX - Statistical Analysis")

        root = QWidget(self)
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)

        toolbar = QHBoxLayout()
        load_btn = QPushButton("Load CSV…")
        load_btn.clicked.connect(self._load_csv)
        toolbar.addWidget(load_btn)
        self.status_label = QLabel("No dataset loaded")
        toolbar.addWidget(self.status_label)
        toolbar.addStretch(1)
        root_layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Horizontal)
        root_layout.addWidget(splitter, 1)

        self.variable_list = VariableList()
        splitter.addWidget(self.variable_list)

        self.sidebar_tabs = QTabWidget()
        splitter.addWidget(self.sidebar_tabs)

        self.crosstab_sidebar = CrosstabSidebar(on_update=self._update_crosstab)
        self.sidebar_tabs.addTab(self.crosstab_sidebar, "Crosstab")

        self.desc_sidebar = DescriptivesSidebar(on_update=self._update_descriptives)
        self.sidebar_tabs.addTab(self.desc_sidebar, "Descriptives")

        self.corr_sidebar = CorrelationSidebar(on_update=self._update_correlation)
        self.sidebar_tabs.addTab(self.corr_sidebar, "Correlation")

        self.output = OutputPane()
        splitter.addWidget(self.output)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 2)

    def _load_csv(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv);;All Files (*)")
        if not file_path:
            return
        try:
            nrows, ncols = self.dataset_manager.load_csv(file_path)
        except Exception as e:  # noqa: BLE001
            self.status_label.setText(f"Failed to load: {e}")
            return
        self.status_label.setText(f"Loaded {nrows} rows, {ncols} columns")
        self.variable_list.set_variables(self.dataset_manager.get_variable_names())

    def _update_crosstab(self, rows: List[str], cols: List[str]) -> None:
        if not self.dataset_manager.is_loaded():
            return
        if not rows or not cols:
            return
        df = self.dataset_manager.get_dataframe()
        html = run_crosstab(df, rows, cols)
        self.output.show_html(html)

    def _update_descriptives(self, variables: List[str]) -> None:
        if not self.dataset_manager.is_loaded():
            return
        if not variables:
            return
        df = self.dataset_manager.get_dataframe()
        html = run_descriptives(df, variables)
        self.output.show_html(html)

    def _update_correlation(self, method: str) -> None:
        if not self.dataset_manager.is_loaded():
            return
        df = self.dataset_manager.get_dataframe()
        html = run_correlation(df, method=method)
        self.output.show_html(html)
