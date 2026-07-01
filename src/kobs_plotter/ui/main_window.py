"""
Main application window for kobs-plotter.

Composes all UI panels into a single window, manages the shared
PlotSettingsBuilder, and coordinates communication between the UI
layer and the core computation layer via callbacks.
"""

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

from kobs_plotter.core.diagnostics import PlotDiagnosticType
from kobs_plotter.core.settings import PlotSettingsBuilder, PlotType
from kobs_plotter.ui.config_panel import ConfigPanel
from kobs_plotter.ui.file_panel import FilePanel
from kobs_plotter.ui.plot_panel import PlotPanel
from kobs_plotter.ui.plot_window import PlotWindow
from kobs_plotter.ui.results_panel import ResultsPanel
from kobs_plotter.ui.ui_helpers import show_error, show_warning


class MainWindow(QMainWindow):
    """
    Root window of the kobs-plotter application.

    Hosts four side-by-side panels (file, config, plot, results) and an
    action bar with plot type selection, reset, and generate plot controls.

    The window owns a single PlotSettingsBuilder instance which is shared
    across all panels. Each panel updates the builder directly as the user
    interacts with its widgets. When the user clicks Generate Plot, the
    builder is finalised into an immutable PlotSettings object and passed
    to the compute callable provided at construction time.

    Args:
        compute: callable provided by main() that orchestrates data loading,
                 fitting, and plotting. Signature::

                     compute(settings, result_callback, plot_callback)
    """

    def __init__(self, compute: Callable):
        super().__init__()
        self.setWindowTitle("K Observes Plotter")
        self.setMinimumSize(1600, 800)
        self.compute = compute
        self._plot_window = PlotWindow(parent=self, window_title="Plot")
        self._residual_window = PlotWindow(parent=self, window_title="Residual Plot")
        self._qq_window = PlotWindow(parent=self, window_title="Q-Q Plot")

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
        self.reset_btn.clicked.connect(self._residual_window.on_reset)
        self.reset_btn.clicked.connect(self._qq_window.on_reset)

        self.qq_btn = QPushButton("Show QQ Plot")
        self.qq_btn.setFixedWidth(150)
        self.qq_btn.clicked.connect(lambda _: self._compute(PlotDiagnosticType.QQ_PLOT))

        self.residual_btn = QPushButton("Show Residual")
        self.residual_btn.setFixedWidth(150)
        self.residual_btn.clicked.connect(
            lambda _: self._compute(PlotDiagnosticType.RESIDUAL)
        )

        self.compute_btn = QPushButton("Generate plot")
        self.compute_btn.setFixedWidth(130)
        self.compute_btn.clicked.connect(
            lambda _: self._compute(PlotDiagnosticType.PLOT)
        )

        action_bar.addWidget(self.reset_btn)
        action_bar.addWidget(self.qq_btn)
        action_bar.addWidget(self.residual_btn)
        action_bar.addWidget(self.compute_btn)
        root.addLayout(action_bar)

        self.settings_builder.set_plot_type(PlotType.SCATTER_LINE)

    def _on_plot_type_changed(self, index: int) -> None:
        """
        Handle plot type combo box selection change.

        Propagates the new plot type to the settings builder and updates
        all panels that have mode-dependent UI elements (file panel Z column,
        config panel Z transform and 3D models, plot panel colormap vs line style).

        Args:
            index: combo box index — 0 for Scatter/Line, 1 for Surface 3D.
        """
        plot_type = PlotType.SCATTER_LINE if index == 0 else PlotType.SURFACE_3D
        self.settings_builder.set_plot_type(plot_type)
        is_3d = plot_type == PlotType.SURFACE_3D
        self.file_panel.set_mode(is_3d)
        self.config_panel.set_mode(is_3d)
        self.plot_panel.set_mode(is_3d)

    def _compute(self, diagnostic: PlotDiagnosticType) -> None:
        """
        Handle Generate Plot button click.

        Builds an immutable PlotSettings object from the current builder
        state and passes it to the compute callable along with the result
        and plot callbacks. Displays a warning dialog for validation errors
        and an error dialog for unexpected failures.
        """
        try:
            settings = self.settings_builder.build()

            match diagnostic:
                case PlotDiagnosticType.PLOT:
                    self.compute(
                        settings,
                        self.results_panel._result_callback,
                        self._plot_callback,
                        diagnostic,
                    )
                case PlotDiagnosticType.RESIDUAL:
                    self.compute(
                        settings,
                        self.results_panel._result_callback,
                        self._residual_callback,
                        diagnostic,
                    )
                case PlotDiagnosticType.QQ_PLOT:
                    self.compute(
                        settings,
                        self.results_panel._result_callback,
                        self._qq_callback,
                        diagnostic,
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

    def _plot_callback(self, **kwargs) -> None:
        """
        Callback passed to the compute layer to trigger plot rendering.

        Ensures the plot window is visible and raised to the front before
        delegating all keyword arguments to PlotWindow.plot(). Called after
        a successful fit by the plotting module.
        """
        self._plot_window.show()
        self._plot_window.raise_()
        self._plot_window.plot(**kwargs)

    def _residual_callback(self, **kwargs) -> None:
        self._residual_window.show()
        self._residual_window.raise_()
        self._residual_window.plot(**kwargs)

    def _qq_callback(self, **kwargs) -> None:
        self._qq_window.show()
        self._qq_window.raise_()
        self._qq_window.plot(**kwargs)

    def _reset(self) -> None:
        """
        Handle Reset button click.

        Resets the plot type combo to its default (Scatter / Line) and
        resets the settings builder. Individual panel resets are connected
        directly to the reset button signal in __init__.
        """
        self.plot_type_combo.setCurrentIndex(0)

    def _vdivider(self) -> QFrame:
        """Create and return a vertical divider line for use between panels."""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line

    def _hdivider(self) -> QFrame:
        """Create and return a horizontal divider line for use between layout rows."""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line
