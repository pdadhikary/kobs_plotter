import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

import kobs_plotter.resources_rc  # noqa: F401
from kobs_plotter.core.service import ComputeService
from kobs_plotter.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    pixmap = QPixmap(":/images/splash.png")
    splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
    splash.show()

    app.setWindowIcon(QIcon(":/icons/logo.png"))

    window = MainWindow(ComputeService())
    window.show()

    splash.finish(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()