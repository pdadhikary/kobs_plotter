from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from kobs_plotter.core.settings import PlotSettings, PlotType


class PlotWindow(QMainWindow):
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
    ):
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
        self, x, y, x_fit, y_fit, conf_lower, conf_upper, result_string, settings
    ):
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

    def _plot_3d(self, x, y, z, x_fit, y_fit, z_fit, result_string, settings):
        ax = self.figure.add_subplot(111, projection="3d")
        ax.scatter(x, y, z, color=settings.point_color, zorder=5)
        ax.plot_surface(x_fit, y_fit, z_fit, cmap=settings.colormap, alpha=0.6)
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

    def _clear(self):
        self.figure.clear()
        self.figure.set_facecolor(plt.rcParams["figure.facecolor"])
        self._text_obj = None

    def on_reset(self):
        with plt.style.context("ggplot"):
            self._clear()
            self.figure.add_subplot(111)
            self.canvas.draw()
