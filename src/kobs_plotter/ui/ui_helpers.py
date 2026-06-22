from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QLabel


def section_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setFont(QFont("sans-serif", 10, QFont.Weight.Medium))
    return label


def field_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setFont(QFont("sans-serif", 9))
    return label


def prefix_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setFont(QFont("monospace", 9))
    label.setStyleSheet(
        "background: palette(window); border: 0.5px solid palette(mid); "
        "padding: 0 8px; border-radius: 4px 0 0 4px;"
    )
    return label


def divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line
