from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from numpy import ndarray
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from kobs_plotter.core.settings import PlotSettings


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

    def plot(
        self,
        x: ndarray,
        y: ndarray,
        x_fit: ndarray,
        y_fit: ndarray,
        result_string: str,
        settings: PlotSettings,
    ):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        ax.scatter(x, y, color=settings.point_color, zorder=5)
        ax.plot(x_fit, y_fit, color=settings.line_color, linestyle=settings.line_style)

        ax.set_title(settings.title or "")
        ax.set_xlabel(settings.x_label or "")
        ax.set_ylabel(settings.y_label or "")

        self.figure.text(
            0.67,
            0.50,
            result_string,
            fontsize=9,
            family="monospace",
            verticalalignment="center",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
        )

        self.canvas.draw()

    def on_reset(self):
        with plt.style.context("ggplot"):
            self.figure.clear()
            self.figure.set_facecolor(plt.rcParams["figure.facecolor"])
            self.figure.add_subplot(111)
            self.canvas.draw()
