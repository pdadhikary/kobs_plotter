import traceback
from typing import Callable

from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from kobs_plotter.core.settings import PlotSettingsBuilder, PlotType
from kobs_plotter.ui.config_panel import ConfigPanel
from kobs_plotter.ui.file_panel import FilePanel
from kobs_plotter.ui.plot_panel import PlotPanel
from kobs_plotter.ui.plot_window import PlotWindow
from kobs_plotter.ui.results_panel import ResultsPanel
from kobs_plotter.ui.ui_helpers import show_error, show_warning


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

        action_bar.addWidget(QLabel("Plot type:"))
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(["Scatter / Line", "Surface 3D"])
        self.plot_type_combo.currentIndexChanged.connect(self._on_plot_type_changed)
        action_bar.addWidget(self.plot_type_combo)
        action_bar.addSpacing(16)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setFixedWidth(100)
        self.reset_btn.clicked.connect(self._reset)
        self.reset_btn.clicked.connect(self.file_panel.on_reset)
        self.reset_btn.clicked.connect(self.config_panel.on_reset)
        self.reset_btn.clicked.connect(self.plot_panel.on_reset)
        self.reset_btn.clicked.connect(self.results_panel.on_reset)
        self.reset_btn.clicked.connect(self._plot_window.on_reset)

        self.compute_btn = QPushButton("Generate plot")
        self.compute_btn.setFixedWidth(120)
        self.compute_btn.clicked.connect(self._compute)

        action_bar.addWidget(self.reset_btn)
        action_bar.addWidget(self.compute_btn)
        root.addLayout(action_bar)

        self.settings_builder.set_plot_type(PlotType.SCATTER_LINE)

    def _on_plot_type_changed(self, index: int):
        plot_type = PlotType.SCATTER_LINE if index == 0 else PlotType.SURFACE_3D
        self.settings_builder.set_plot_type(plot_type)
        is_3d = plot_type == PlotType.SURFACE_3D
        self.file_panel.set_mode(is_3d)
        self.config_panel.set_mode(is_3d)
        self.plot_panel.set_mode(is_3d)

    def _compute(self):
        try:
            settings = self.settings_builder.build()
            self.compute(
                settings, self.results_panel._result_callback, self._plot_callback
            )
        except ValueError as e:
            traceback.print_exc()
            show_warning(self, "Error", str(e))
        except RuntimeError as e:
            traceback.print_exc()
            show_warning(self, "Error", str(e))
        except Exception as e:
            traceback.print_exc()
            show_error(self, "Error", str(e))

    def _plot_callback(self, **kwargs):
        self._plot_window.show()
        self._plot_window.raise_()
        self._plot_window.plot(**kwargs)

    def _reset(self):
        self.plot_type_combo.setCurrentIndex(0)

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
