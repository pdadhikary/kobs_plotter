from typing import Callable

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QFrame,
)

from kobs_plotter.ui.file_panel import FilePanel
from kobs_plotter.ui.config_panel import ConfigPanel
from kobs_plotter.ui.plot_panel import PlotPanel
from kobs_plotter.ui.plot_window import PlotWindow
from kobs_plotter.ui.results_panel import ResultsPanel

from kobs_plotter.core.settings import PlotSettingsBuilder


class MainWindow(QMainWindow):
    def __init__(self, compute: Callable):
        super().__init__()
        self.setWindowTitle("K Observes Plotter")
        self.setMinimumSize(1600, 800)
        self.compute = compute
        self._plot_window = PlotWindow(parent=self)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Panels row ───────────────────────────────────────
        panels_row = QHBoxLayout()
        panels_row.setSpacing(0)

        self.settings_builder = PlotSettingsBuilder()

        self.file_panel = FilePanel(self.settings_builder)
        self.config_panel = ConfigPanel(self.settings_builder)
        self.plot_panel = PlotPanel(self.settings_builder)
        self.results_panel = ResultsPanel()

        panels_row.addWidget(self.file_panel)
        panels_row.addWidget(self._vdivider())
        panels_row.addWidget(self.config_panel)
        panels_row.addWidget(self._vdivider())
        panels_row.addWidget(self.plot_panel)
        panels_row.addWidget(self._vdivider())
        panels_row.addWidget(self.results_panel)

        root.addLayout(panels_row)
        root.addWidget(self._hdivider())

        # ── Action bar ───────────────────────────────────────
        action_bar = QHBoxLayout()
        action_bar.setContentsMargins(16, 12, 16, 12)
        action_bar.setSpacing(8)
        action_bar.addStretch()

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setFixedWidth(100)
        self.reset_btn.clicked.connect(self._reset)
        # TODO: implement _reset to clear all panel inputs and results

        self.compute_btn = QPushButton("Generate plot")
        self.compute_btn.setFixedWidth(120)
        self.compute_btn.clicked.connect(self._compute)
        # TODO: implement _compute — build settings, call engine, pass result to results_panel.display()

        action_bar.addWidget(self.reset_btn)
        action_bar.addWidget(self.compute_btn)
        root.addLayout(action_bar)

    def _compute(self):
        print(self.settings_builder.build())
        settings = self.settings_builder.build()
        self.compute(settings, self.results_panel._result_callback, self._plot_callback)

    def _plot_callback(self, **kwargs):
        self._plot_window.show()
        self._plot_window.raise_()

        self._plot_window.plot(**kwargs)

    def _reset(self):
        # TODO: clear all inputs across panels and reset results_panel
        pass

    def _vdivider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line

    def _hdivider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line
