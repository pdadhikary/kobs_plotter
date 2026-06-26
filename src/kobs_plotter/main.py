import sys
from typing import Callable

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

import kobs_plotter.resources_rc  # noqa: F401
from kobs_plotter.core.data_loader import load_data
from kobs_plotter.core.modelling import fit
from kobs_plotter.core.plotting import plot
from kobs_plotter.core.settings import PlotSettings
from kobs_plotter.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    app.setWindowIcon(QIcon(":/icons/logo.png"))

    window = MainWindow(compute)
    window.show()
    sys.exit(app.exec())


def compute(settings: PlotSettings, result_callback: Callable, plot_callback: Callable):
    data = load_data(settings)
    result = fit(data, settings)
    result_callback(result, settings.params)
    plot(data, result, settings, plot_callback)


if __name__ == "__main__":
    main()
