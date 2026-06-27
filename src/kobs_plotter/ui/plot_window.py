"""
Plot window UI component for kobs-plotter.

Provides a standalone QMainWindow containing an embedded matplotlib
figure with the standard navigation toolbar. Supports both 2D scatter
and line plots with confidence bands, and 3D surface plots with
projected contours.
"""

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from kobs_plotter.core.settings import PlotSettings, PlotType


class PlotWindow(QMainWindow):
    """
    Floating plot window displaying the fitted curve or surface.

    Hosts an embedded matplotlib figure with the standard navigation
    toolbar (zoom, pan, save). The window is created once by MainWindow
    and reused across successive compute runs — calling plot() clears
    and redraws the figure in place.

    Supports two rendering modes driven by PlotSettings.plot_type:

    - **2D (SCATTER_LINE)** — scatter plot of observed data with the
      fitted curve overlaid and a shaded confidence band.
    - **3D (SURFACE_3D)** — 3D scatter of observed points with the
      fitted surface mesh and a projected contour at the base.

    A formatted result string showing the fitted formula, parameter
    values, and goodness-of-fit metrics is placed outside the axes
    in the right margin for both plot types.

    Args:
        parent: optional parent widget. When set to MainWindow the plot
                window stays in front of the main window on most platforms.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plot")
        self.setMinimumSize(800, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self._text_obj = None

    def plot(
        self,
        x: np.ndarray,
        y: np.ndarray,
        x_fit: np.ndarray,
        y_fit: np.ndarray,
        result_string: str,
        settings: PlotSettings,
        z: Optional[np.ndarray] = None,
        z_fit: Optional[np.ndarray] = None,
        conf_lower: Optional[np.ndarray] = None,
        conf_upper: Optional[np.ndarray] = None,
    ) -> None:
        """
        Clear the figure and render a new plot from the provided data.

        Dispatches to _plot_2d or _plot_3d based on settings.plot_type.
        The selected plot theme is applied via a style context so it does
        not affect any other matplotlib state outside this window.

        Args:
            x:             observed X values.
            y:             observed Y values.
            x_fit:         X values for the fitted curve (2D) or X mesh (3D).
            y_fit:         fitted curve Y values (2D) or Y mesh (3D).
            result_string: formatted multi-line string shown in the right margin.
            settings:      immutable plot settings controlling style and labels.
            z:             observed Z values for 3D plots, None for 2D.
            z_fit:         fitted Z mesh for 3D plots, None for 2D.
            conf_lower:    lower confidence band for 2D plots, None for 3D.
            conf_upper:    upper confidence band for 2D plots, None for 3D.
        """
        with plt.style.context(settings.plot_theme):
            self._clear()

            if settings.plot_type == PlotType.SURFACE_3D:
                self._plot_3d(x, y, z, x_fit, y_fit, z_fit, result_string, settings)
            else:
                self._plot_2d(
                    x, y, x_fit, y_fit, conf_lower, conf_upper, result_string, settings
                )

            self.canvas.draw()

    def _plot_2d(
        self,
        x: np.ndarray,
        y: np.ndarray,
        x_fit: np.ndarray,
        y_fit: np.ndarray,
        conf_lower: Optional[np.ndarray],
        conf_upper: Optional[np.ndarray],
        result_string: str,
        settings: PlotSettings,
    ) -> None:
        """
        Render a 2D scatter plot with fitted curve and confidence band.

        Plots observed data as scatter points, overlays the fitted curve,
        and shades the region between conf_lower and conf_upper to indicate
        the confidence band. The result string is placed in the right margin
        outside the axes using figure coordinates.

        Args:
            x:             observed X values.
            y:             observed Y values.
            x_fit:         dense X values along the fitted curve.
            y_fit:         fitted Y values corresponding to x_fit.
            conf_lower:    lower bound of the confidence band at each x_fit point.
            conf_upper:    upper bound of the confidence band at each x_fit point.
            result_string: formatted result text for the right margin annotation.
            settings:      plot settings controlling colors, labels, and line style.
        """
        ax = self.figure.add_subplot(111)
        ax.scatter(x, y, color=settings.point_color, zorder=5)
        ax.plot(x_fit, y_fit, color=settings.line_color, linestyle=settings.line_style)
        ax.fill_between(
            x_fit,
            conf_lower,
            conf_upper,
            alpha=0.2,
            color=settings.line_color,
        )
        ax.set_title(settings.title or "")
        ax.set_xlabel(settings.x_label or "")
        ax.set_ylabel(settings.y_label or "")
        self.figure.subplots_adjust(right=0.65)
        self._text_obj = self.figure.text(
            0.67,
            0.50,
            result_string,
            fontsize=9,
            family="monospace",
            verticalalignment="center",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
        )

    def _plot_3d(
        self,
        x: np.ndarray,
        y: np.ndarray,
        z: Optional[np.ndarray],
        x_fit: np.ndarray,
        y_fit: np.ndarray,
        z_fit: Optional[np.ndarray],
        result_string: str,
        settings: PlotSettings,
    ) -> None:
        """
        Render a 3D scatter plot with fitted surface and projected contour.

        Plots observed (x, y, z) data as semi-transparent scatter points,
        overlays the fitted surface mesh with the selected colormap, and
        projects a contour of the surface onto the base plane for additional
        spatial context. The result string is placed in the right margin.

        Args:
            x:             observed X values.
            y:             observed Y values.
            z:             observed Z values.
            x_fit:         X mesh of shape (n, n) covering the observed X range.
            y_fit:         Y mesh of shape (n, n) covering the observed Y range.
            z_fit:         fitted Z values evaluated over the x_fit/y_fit mesh.
            result_string: formatted result text for the right margin annotation.
            settings:      plot settings controlling colors, colormap, and labels.
        """
        ax = self.figure.add_subplot(111, projection="3d")
        ax.scatter(x, y, z, alpha=0.6, color=settings.point_color, zorder=5)
        ax.plot_surface(x_fit, y_fit, z_fit, cmap=settings.colormap, alpha=0.6)
        ax.contour(
            x_fit,
            y_fit,
            z_fit,
            zdir="z",
            offset=ax.get_zlim()[0],
            cmap=settings.colormap,
        )
        ax.set_title(settings.title or "")
        ax.set_xlabel(settings.x_label or "")
        ax.set_ylabel(settings.y_label or "")
        ax.set_zlabel(settings.z_label or "")
        self.figure.subplots_adjust(right=0.55)
        self._text_obj = self.figure.text(
            0.67,
            0.50,
            result_string,
            fontsize=9,
            family="monospace",
            verticalalignment="center",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
        )

    def _clear(self) -> None:
        """
        Clear the figure and reset the text object reference.

        Applies the current theme's figure background color after clearing
        so the canvas background matches the selected plot theme. Called
        at the start of every plot() call.
        """
        self.figure.clear()
        self.figure.set_facecolor(plt.rcParams["figure.facecolor"])
        self._text_obj = None

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
