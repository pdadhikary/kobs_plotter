# src/kobs_plotter/ui/plot_panel.py
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QComboBox,
)
from PySide6.QtGui import QFont

from kobs_plotter.ui.ui_helpers import section_label, field_label, divider


LINESTYLES = ["-", "--", "-.", ":"]


class PlotPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setMaximumWidth(320)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── Labels ───────────────────────────────────────────
        layout.addWidget(section_label("Plot labels"))

        layout.addWidget(field_label("Title"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Conductance vs Time")
        # TODO: connect to builder.set_title
        layout.addWidget(self.title_input)

        layout.addWidget(field_label("X axis"))
        self.x_label_input = QLineEdit()
        self.x_label_input.setPlaceholderText("e.g. Time (s)")
        # TODO: connect to builder.set_x_label
        layout.addWidget(self.x_label_input)

        layout.addWidget(field_label("Y axis"))
        self.y_label_input = QLineEdit()
        self.y_label_input.setPlaceholderText("e.g. Conductance (S)")
        # TODO: connect to builder.set_y_label
        layout.addWidget(self.y_label_input)

        layout.addWidget(divider())

        # ── Scatter style ────────────────────────────────────
        layout.addWidget(section_label("Scatter style"))

        layout.addWidget(field_label("Point color"))
        self.scatter_color_input = QLineEdit()
        self.scatter_color_input.setPlaceholderText("e.g. black, red, #FF5733")
        self.scatter_color_input.setFont(QFont("monospace", 9))
        self.scatter_color_input.setText("black")
        # TODO: connect to builder.set_scatter_color
        layout.addWidget(self.scatter_color_input)

        layout.addWidget(divider())

        # ── Trend line style ─────────────────────────────────
        layout.addWidget(section_label("Trend line style"))

        layout.addWidget(field_label("Line color"))
        self.line_color_input = QLineEdit()
        self.line_color_input.setPlaceholderText("e.g. red, blue, #FF5733")
        self.line_color_input.setFont(QFont("monospace", 9))
        self.line_color_input.setText("red")
        # TODO: connect to builder.set_line_color
        layout.addWidget(self.line_color_input)

        layout.addWidget(field_label("Line style"))
        self.linestyle_combo = QComboBox()
        self.linestyle_combo.addItems(LINESTYLES)
        # TODO: connect to builder.set_linestyle
        layout.addWidget(self.linestyle_combo)

        layout.addStretch()
