import logging
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

import kobs_plotter.resources_rc  # noqa: F401
from kobs_plotter.core.service import ComputeService
from kobs_plotter.ui.main_window import MainWindow

# QSettings organisation/application identifiers. Must be set before the
# first QSettings() use so persistence keys land under the right place.
_ORG_NAME = "kobs-plotter"
_APP_NAME = "kobs-plotter"


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main():
    _configure_logging()
    app = QApplication(sys.argv)
    app.setOrganizationName(_ORG_NAME)
    app.setApplicationName(_APP_NAME)

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
