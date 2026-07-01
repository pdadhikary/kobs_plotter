"""
Plot window UI component for kobs-plotter.

Provides a standalone QMainWindow containing an embedded matplotlib
figure with the standard navigation toolbar. Supports both 2D scatter
and line plots with confidence bands, and 3D surface plots with
projected contours. Per-view rendering is dispatched through a
(plot_type, diagnostic) -> renderer registry, replacing the previous
nested match inside plot().
"""

from typing import Callable, Optional

import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from kobs_plotter.core.diagnostics import PlotDiagnosticType
from kobs_plotter.core.plotting import PlotPayload
from kobs_plotter.core.settings import PlotSettings, PlotType

# A renderer draws one (plot_type, diagnostic) view onto a Figure.
Renderer = Callable[[Figure, PlotPayload], None]


def _render_scatter_plot(figure: Figure, payload: PlotPayload) -> None:
    """Render a 2D scatter plot with fitted curve and confidence band."""
    settings = payload.settings
    ax = figure.add_subplot(111)
    ax.scatter(payload.x, payload.y, color=settings.point_color, zorder=5)
    ax.plot(
        payload.x_fit,
        payload.y_fit,
        color=settings.line_color,
        linestyle=settings.line_style,
    )
    ax.fill_between(
        payload.x_fit,
        payload.conf_lower,
        payload.conf_upper,
        alpha=0.2,
        color=settings.line_color,
    )
    ax.set_title(settings.title or "")
    ax.set_xlabel(settings.x_label or "")
    ax.set_ylabel(settings.y_label or "")
    figure.subplots_adjust(right=0.65)
    _add_result_text(figure, payload.result_string)


def _render_surface_plot(figure: Figure, payload: PlotPayload) -> None:
    """Render a 3D scatter plot with fitted surface and projected contour."""
    settings = payload.settings
    ax = figure.add_subplot(111, projection="3d")
    ax.scatter(payload.x, payload.y, payload.z, alpha=0.6, color=settings.point_color, zorder=5)
    ax.plot_surface(payload.x_fit, payload.y_fit, payload.z_fit, cmap=settings.colormap, alpha=0.6)
    ax.contour(
        payload.x_fit,
        payload.y_fit,
        payload.z_fit,
        zdir="z",
        offset=ax.get_zlim()[0],
        cmap=settings.colormap,
    )
    ax.set_title(settings.title or "")
    ax.set_xlabel(settings.x_label or "")
    ax.set_ylabel(settings.y_label or "")
    ax.set_zlabel(settings.z_label or "")
    figure.subplots_adjust(right=0.55)
    _add_result_text(figure, payload.result_string)


def _render_scatter_residual(figure: Figure, payload: PlotPayload) -> None:
    """Render a 2D residual scatter plot against the independent variable."""
    settings = payload.settings
    ax = figure.add_subplot(111)
    ax.scatter(payload.x, payload.residuals, color=settings.point_color, zorder=5)
    ax.axhline(
        y=0,
        label="Baseline",
        color=settings.line_color,
        linestyle=settings.line_style,
    )
    ax.set_title(settings.title or "")
    ax.set_xlabel(settings.x_label or "")
    ax.set_ylabel("Residuals")
    figure.legend()


def _render_surface_residual(figure: Figure, payload: PlotPayload) -> None:
    """Render a 3D residual scatter plot against the two independent variables."""
    settings = payload.settings
    ax = figure.add_subplot(111, projection="3d")
    ax.scatter(payload.x, payload.y, payload.residuals, color=settings.point_color, zorder=5)

    xlim, ylim = ax.get_xlim(), ax.get_ylim()
    xx, yy = np.meshgrid(xlim, ylim)
    zz = np.zeros_like(xx)
    ax.plot_surface(xx, yy, zz, alpha=0.15, color="gray")

    ax.set_title(settings.title or "")
    ax.set_xlabel(settings.x_label or "")
    ax.set_ylabel(settings.y_label or "")
    ax.set_zlabel("Residuals")


def _render_qq(figure: Figure, payload: PlotPayload) -> None:
    """Render a normal Q-Q plot of the fit residuals."""
    settings = payload.settings
    ax = figure.add_subplot(111)
    stats.probplot(payload.residuals, dist="norm", plot=ax)
    ax.set_title(settings.title or "")


def _add_result_text(figure: Figure, result_string: str) -> None:
    """Place the formatted result string in the right margin of the figure."""
    figure.text(
        0.67,
        0.50,
        result_string,
        fontsize=9,
        family="monospace",
        verticalalignment="center",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )


# Registry replacing the nested (plot_type x diagnostic) match in plot().
_RENDERERS: dict[tuple[PlotType, PlotDiagnosticType], Renderer] = {
    (PlotType.SCATTER_LINE, PlotDiagnosticType.PLOT): _render_scatter_plot,
    (PlotType.SCATTER_LINE, PlotDiagnosticType.RESIDUAL): _render_scatter_residual,
    (PlotType.SCATTER_LINE, PlotDiagnosticType.QQ_PLOT): _render_qq,
    (PlotType.SURFACE_3D, PlotDiagnosticType.PLOT): _render_surface_plot,
    (PlotType.SURFACE_3D, PlotDiagnosticType.RESIDUAL): _render_surface_residual,
    (PlotType.SURFACE_3D, PlotDiagnosticType.QQ_PLOT): _render_qq,
}


class PlotWindow(QMainWindow):
    """
    Floating plot window displaying the fitted curve or surface.

    Hosts an embedded matplotlib figure with the standard navigation
    toolbar (zoom, pan, save). The window is created once by MainWindow
    and reused across successive compute runs — calling plot() clears
    and redraws the figure in place. The actual drawing for each
    (plot_type, diagnostic) combination lives in module-level renderer
    functions keyed by the _RENDERERS registry.

    Args:
        parent: optional parent widget. When set to MainWindow the plot
                window stays in front of the main window on most platforms.
        window_title: title shown in the window title bar.
    """

    def __init__(self, parent=None, window_title: str = "Plot"):
        super().__init__(parent)
        self.setWindowTitle(window_title)
        self.setMinimumSize(800, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

    def plot(self, payload: PlotPayload) -> None:
        """
        Clear the figure and render a new plot from the provided payload.

        Looks up the renderer for (settings.plot_type, payload.diagnostic)
        in the _RENDERERS registry and invokes it with the figure and
        payload. The selected plot theme is applied via a style context
        so it does not affect any other matplotlib state outside this
        window.

        Args:
            payload: immutable PlotPayload bundling all data and settings
                      needed to render the requested diagnostic view.
        """
        settings = payload.settings
        with plt.style.context(settings.plot_theme):
            self._clear()
            renderer = _RENDERERS[(settings.plot_type, payload.diagnostic)]
            renderer(self.figure, payload)
            self.canvas.draw()

    def _clear(self) -> None:
        """
        Clear the figure.

        Applies the current theme's figure background color after clearing
        so the canvas background matches the selected plot theme. Called
        at the start of every plot() call.
        """
        self.figure.clear()
        self.figure.set_facecolor(plt.rcParams["figure.facecolor"])

    def on_reset(self) -> None:
        """
        Reset the plot window to its initial empty state.

        Clears the figure and renders a blank axes using the default ggplot
        theme. Connected to the Reset button in MainWindow.
        """
        with plt.style.context("ggplot"):
            self._clear()
            self.figure.add_subplot(111)
            self.canvas.draw()