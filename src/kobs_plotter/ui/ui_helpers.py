"""
Shared UI helper functions and widget factories for kobs-plotter.

Provides lightweight factory functions for commonly used widgets and
dialog helpers to keep panel code concise and consistent.
"""

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QLabel, QMessageBox, QWidget


def show_error(parent: QWidget, title: str, message: str) -> None:
    """
    Display a modal error dialog.

    Used for unexpected or unrecoverable errors such as file I/O failures
    or exceptions not caught by the core layer.

    Args:
        parent:  parent widget the dialog is centred relative to.
        title:   dialog window title.
        message: error description shown to the user.
    """
    QMessageBox.critical(parent, title, message)


def show_warning(parent: QWidget, title: str, message: str) -> None:
    """
    Display a modal warning dialog.

    Used for recoverable user errors such as missing required fields
    or invalid formula expressions.

    Args:
        parent:  parent widget the dialog is centred relative to.
        title:   dialog window title.
        message: warning description shown to the user.
    """
    QMessageBox.warning(parent, title, message)


def show_info(parent: QWidget, title: str, message: str) -> None:
    """
    Display a modal informational dialog.

    Args:
        parent:  parent widget the dialog is centred relative to.
        title:   dialog window title.
        message: informational message shown to the user.
    """
    QMessageBox.information(parent, title, message)


def section_label(text: str) -> QLabel:
    """
    Create a bold section heading label.

    Used to introduce groups of related widgets within a panel,
    rendered at 10pt medium weight sans-serif.

    Args:
        text: heading text to display.

    Returns:
        Styled QLabel suitable for use as a section heading.
    """
    label = QLabel(text)
    label.setFont(QFont("sans-serif", 10, QFont.Weight.Medium))
    return label


def field_label(text: str) -> QLabel:
    """
    Create a small field label placed above an input widget.

    Rendered at 9pt sans-serif to visually subordinate it to the
    input it describes.

    Args:
        text: label text to display.

    Returns:
        Styled QLabel suitable for use above a form input.
    """
    label = QLabel(text)
    label.setFont(QFont("sans-serif", 9))
    return label


def prefix_label(text: str) -> QLabel:
    """
    Create a styled prefix label for use beside a QLineEdit.

    Rendered in monospace with a left-rounded border that visually
    connects to the adjacent input field, giving the appearance of
    a single compound widget (e.g. 'x' = [input]).

    Args:
        text: prefix text to display e.g. "x' =" or "y =".

    Returns:
        Styled QLabel suitable for placement to the left of a QLineEdit.
    """
    label = QLabel(text)
    label.setFont(QFont("monospace", 9))
    label.setStyleSheet(
        "background: palette(window); border: 0.5px solid palette(mid); "
        "padding: 0 8px; border-radius: 4px 0 0 4px;"
    )
    return label


def divider() -> QFrame:
    """
    Create a horizontal divider line for separating sections within a panel.

    Returns:
        QFrame configured as a sunken horizontal line.
    """
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line
