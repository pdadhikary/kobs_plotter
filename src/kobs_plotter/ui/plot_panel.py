# src/kobs_plotter/ui/plot_panel.py
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QComboBox,
)
from PySide6.QtGui import QFont

from kobs_plotter.ui.ui_helpers import section_label, field_label, divider
from kobs_plotter.core.settings import PlotSettingsBuilder


LINESTYLES = ["-", "--", "-.", ":"]


class PlotPanel(QWidget):
    def __init__(self, settings_builder: PlotSettingsBuilder):
        super().__init__()
        self.setMaximumWidth(320)
        self.settings_builder = settings_builder

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── Labels ───────────────────────────────────────────
        layout.addWidget(section_label("Plot labels"))

        layout.addWidget(field_label("Title"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Conductance vs Time")
        self.title_input.textChanged.connect(self.settings_builder.set_title)
        layout.addWidget(self.title_input)

        layout.addWidget(field_label("X axis"))
        self.x_label_input = QLineEdit()
        self.x_label_input.setPlaceholderText("e.g. Time (s)")
        self.x_label_input.textChanged.connect(self.settings_builder.set_x_label)
        layout.addWidget(self.x_label_input)

        layout.addWidget(field_label("Y axis"))
        self.y_label_input = QLineEdit()
        self.y_label_input.setPlaceholderText("e.g. Conductance (S)")
        self.y_label_input.textChanged.connect(self.settings_builder.set_y_label)
        layout.addWidget(self.y_label_input)

        layout.addWidget(divider())

        # ── Scatter style ────────────────────────────────────
        layout.addWidget(section_label("Scatter style"))

        layout.addWidget(field_label("Point color"))
        self.scatter_color_input = QLineEdit()
        self.scatter_color_input.setPlaceholderText("e.g. black, red, #FF5733")
        self.scatter_color_input.setFont(QFont("monospace", 9))
        self.scatter_color_input.textChanged.connect(
            self.settings_builder.set_point_color
        )
        self.scatter_color_input.setText("black")
        layout.addWidget(self.scatter_color_input)

        layout.addWidget(divider())

        # ── Trend line style ─────────────────────────────────
        layout.addWidget(section_label("Trend line style"))

        layout.addWidget(field_label("Line color"))
        self.line_color_input = QLineEdit()
        self.line_color_input.setPlaceholderText("e.g. red, blue, #FF5733")
        self.line_color_input.setFont(QFont("monospace", 9))
        self.line_color_input.textChanged.connect(self.settings_builder.set_line_color)
        self.line_color_input.setText("red")
        layout.addWidget(self.line_color_input)

        layout.addWidget(field_label("Line style"))
        self.linestyle_combo = QComboBox()
        self.linestyle_combo.currentTextChanged.connect(
            self.settings_builder.set_line_style
        )
        self.linestyle_combo.addItems(LINESTYLES)
        layout.addWidget(self.linestyle_combo)

        layout.addStretch()
