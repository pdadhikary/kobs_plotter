"""
Shared UI helper functions and widget factories for kobs-plotter.

Provides lightweight factory functions for commonly used widgets and
dialog helpers to keep panel code concise and consistent.

Font helpers (:func:`mono_font`, :func:`sans_font`) use
:class:`QFontDatabase` to pick a real system monospace/sans family
instead of the literal ``"monospace"`` / ``"sans-serif"`` family names
Qt silently falls back from.
"""

from __future__ import annotations

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QMessageBox,
    QTextEdit,
    QWidget,
)

# ── fonts ─────────────────────────────────────────────────────────


def sans_font(point_size: int = 9, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    """Return a sans-serif font using the real system UI family."""
    base = QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont)
    f = QFont(base.family(), point_size, weight)
    return f


def mono_font(point_size: int = 9, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    """Return a monospace font using the real system fixed-width family."""
    base = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
    f = QFont(base.family(), point_size, weight)
    return f


# ── dialogs ───────────────────────────────────────────────────────


def show_error(parent: QWidget, title: str, message: str) -> None:
    """Display a modal error dialog with a Copy button for long messages."""
    QMessageBox.critical(parent, title, message)


def show_warning(parent: QWidget, title: str, message: str) -> None:
    """Display a modal warning dialog (recoverable user errors)."""
    QMessageBox.warning(parent, title, message)


def show_info(parent: QWidget, title: str, message: str) -> None:
    """Display a modal informational dialog."""
    QMessageBox.information(parent, title, message)


def show_copyable_error(parent: QWidget, title: str, message: str, detail: str = "") -> None:
    """
    Show a non-modal-style error with a selectable, copyable text area.

    Used for unexpected exceptions where the user may want to copy the
    full message (incl. traceback) into a bug report. The detail text is
    shown in a read-only ``QTextEdit`` so it is scrollable and copyable,
    unlike the plain ``QMessageBox`` label.
    """
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Critical)
    box.setWindowTitle(title)
    box.setText(message)
    if detail:
        # Rebuild the layout to include a selectable detail area.
        details = QTextEdit()
        details.setReadOnly(True)
        details.setPlainText(detail)
        details.setMinimumSize(480, 200)
        # Insert the text widget into the existing layout (above the buttons).
        layout = box.layout()
        if layout is not None:
            layout.addWidget(details, 1, 0, 1, layout.columnCount())
    box.exec()


# ── widget factories ───────────────────────────────────────────────


def section_label(text: str) -> QLabel:
    """Bold section heading label at 10pt medium weight sans-serif."""
    label = QLabel(text)
    label.setFont(sans_font(10, QFont.Weight.Medium))
    return label


def field_label(text: str) -> QLabel:
    """Small 9pt sans-serif label placed above an input widget."""
    label = QLabel(text)
    label.setFont(sans_font(9))
    return label


def prefix_label(text: str) -> QLabel:
    """
    Styled prefix label for use beside a QLineEdit, giving the appearance
    of a compound widget (e.g. ``x' = [input]``). Uses ``1px`` borders
    (not sub-pixel ``0.5px``) so the rounded edge renders consistently.
    """
    label = QLabel(text)
    label.setFont(mono_font(9))
    label.setStyleSheet(
        "background: palette(window); border: 1px solid palette(mid); "
        "padding: 0 8px; border-radius: 4px 0 0 4px;"
    )
    return label


def divider() -> QFrame:
    """Horizontal divider line for separating sections within a panel."""
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line


def vdivider() -> QFrame:
    """Vertical divider line for separating side-by-side panels."""
    line = QFrame()
    line.setFrameShape(QFrame.Shape.VLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line
