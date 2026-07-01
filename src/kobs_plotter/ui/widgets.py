"""
Reusable composite widgets for kobs-plotter panels.

Extracts UI patterns that were duplicated across the panels:

- :class:`CollapsibleSection` — a ``QWidget`` wrapper that can be shown
  or hidden as a unit. Previously every panel built its own anonymous
  ``QWidget + QVBoxLayout`` and toggled ``setVisible(...)`` — the wrapper
  is now one helper used eight times across the app.

- :class:`ColorSwatchButton` — a small square ``QPushButton`` showing the
  current color, opening :class:`QColorDialog` on click and falling back
  to a free-text hex entry. Replaces the previous bare ``QLineEdit`` color
  fields that validated only at plot-render time.

- :func:`make_readonly_table` — builds a read-only, alternating-row,
  contiguous-selection ``QTableWidget`` with stretched columns. The two
  tables in :mod:`results_panel` were near-identical ~30-line blocks.
"""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QColorDialog,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from kobs_plotter.ui.ui_helpers import mono_font


class CollapsibleSection(QWidget):
    """A titled group of widgets that can be shown/hidden as one unit.

    Construct with ``title`` shown as a small field label above the
    contents, then :meth:`add_layout` / :meth:`add_widget` to populate.
    Toggle visibility via :meth:`set_visible` (the title stays hidden —
    this wrapper's visibility is controlled by the caller, exactly like
    the previous anonymous wrapper pattern).
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self._layout = layout

    def add_layout(self, layout) -> None:  # noqa: ANN001 - Qt layout hint
        self._layout.addLayout(layout)

    def add_widget(self, widget: QWidget) -> None:
        self._layout.addWidget(widget)


class ColorSwatchButton(QWidget):
    """A color picker combining a square swatch button and a hex text field.

    The swatch opens ``QColorDialog``; choosing a color updates both the
    swatch and the hex text field (and emits :attr:`colorChanged`). The
    hex text field lets advanced users type ``#RRGGBB`` or matplotlib
    named colors directly. The text is accepted verbatim and pushed to the
    builder — matplotlib is the final arbiter of validity.

    Emits:
        colorChanged(str): the current color string (named or hex).
    """

    colorChanged = Signal(str)

    def __init__(self, initial: str = "black", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._value = initial

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        self._swatch = QPushButton()
        self._swatch.setFixedWidth(28)
        self._swatch.setFixedHeight(22)
        self._swatch.setCursor(Qt.CursorShape.PointingHandCursor)
        self._swatch.setToolTip("Click to pick a color")
        self._swatch.clicked.connect(self._pick_color)
        row.addWidget(self._swatch)

        self._line = QLineEdit()
        self._line.setFont(mono_font())
        self._line.setPlaceholderText("#FF5733 or red")
        self._line.setText(initial)
        self._line.editingFinished.connect(self._on_text)
        row.addWidget(self._line)

        self._update_swatch(initial)

    def _pick_color(self) -> None:
        initial = QColor(self._value) if QColor(self._value).isValid() else QColor("black")
        color = QColorDialog.getColor(initial, self, "Select color")
        if color.isValid():
            self._set_color(color.name())

    def _on_text(self) -> None:
        self._set_color(self._line.text().strip())

    def _set_color(self, value: str) -> None:
        self._value = value
        # Block signals while updating the line edit text to avoid feedback loops
        # when the value came from the swatch picker.
        self._line.blockSignals(True)
        self._line.setText(value)
        self._line.blockSignals(False)
        self._update_swatch(value)
        self.colorChanged.emit(value)

    def _update_swatch(self, value: str) -> None:
        if QColor(value).isValid():
            self._swatch.setStyleSheet(
                f"background-color: {value}; border: 1px solid palette(mid); border-radius: 3px;"
            )
        else:
            # Named matplotlib colors that Qt doesn't know (e.g. "tab:blue")
            # fall back to a neutral swatch; matplotlib still resolves them.
            self._swatch.setStyleSheet(
                "background: palette(button); border: 1px solid palette(mid); border-radius: 3px;"
            )

    def value(self) -> str:
        return self._value

    def set_value(self, value: str) -> None:
        self._set_color(value)


def make_readonly_table(headers: Iterable[str]) -> QTableWidget:
    """Build a read-only, stretched-column, alternating-row QTableWidget.

    Used by :class:`ResultsPanel` for both the Parameters and the
    Goodness-of-fit tables, replacing two ~30-line duplicated setup
    blocks. Returns a table with the given horizontal header labels, no
    vertical header, contiguous selection mode, and a fixed vertical
    size policy so the enclosing scroll area handles overflow.
    """
    table = QTableWidget(0, 0)
    headers_list = list(headers)
    table.setColumnCount(len(headers_list))
    table.setHorizontalHeaderLabels(headers_list)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setAlternatingRowColors(True)
    table.setSelectionMode(QAbstractItemView.SelectionMode.ContiguousSelection)
    table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    return table


def safe_set_current(combo: QComboBox, value: str) -> None:
    """Set a combo's current text only if the value is present (else index 0)."""
    idx = combo.findText(value)
    combo.setCurrentIndex(idx if idx >= 0 else 0)
