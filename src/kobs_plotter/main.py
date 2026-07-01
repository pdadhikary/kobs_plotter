import sys
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

import kobs_plotter.resources_rc  # noqa: F401
from kobs_plotter.core.data_loader import load_data
from kobs_plotter.core.diagnostics import PlotDiagnosticType
from kobs_plotter.core.modelling import fit
from kobs_plotter.core.plotting import plot
from kobs_plotter.core.settings import PlotSettings
from kobs_plotter.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    pixmap = QPixmap(":/images/splash.png")
    splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
    splash.show()

    app.setWindowIcon(QIcon(":/icons/logo.png"))

    window = MainWindow(compute)
    window.show()

    splash.finish(window)

    sys.exit(app.exec())


def compute(
    settings: PlotSettings,
    result_callback: Callable,
    plot_callback: Callable,
    diagnostic: PlotDiagnosticType,
):
    data = load_data(settings)
    result = fit(data, settings)
    result_callback(result, settings.params)
    payload = plot(data, result, settings, diagnostic)
    plot_callback(payload)


if __name__ == "__main__":
    main()
