from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from kobs_plotter.core.settings import PlotSettingsBuilder
from kobs_plotter.ui.ui_helpers import divider, field_label, section_label

PLOT_THEMES = [
    "ggplot",
    "fivethirtyeight",
    "seaborn-v0_8-whitegrid",
    "seaborn-v0_8-bright",
    "seaborn-v0_8-paper",
    "seaborn-v0_8-poster",
    "seaborn-v0_8-darkgrid",
]
LINESTYLES = ["-", "--", "-.", ":"]
DEFAULT_SCATTER_COLOR = "black"
DEFAULT_LINE_COLOR = "red"
DEFAULT_LINE_STYLE_INDEX = 0


class PlotPanel(QWidget):
    def __init__(self, settings_builder: PlotSettingsBuilder):
        super().__init__()
        self.setMaximumWidth(320)
        self.settings_builder = settings_builder

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(section_label("Plot Theme"))
        self.plot_theme_combo = QComboBox()
        self.plot_theme_combo.currentTextChanged.connect(
            self.settings_builder.set_plot_theme
        )
        self.plot_theme_combo.addItems(PLOT_THEMES)
        self.plot_theme_combo.setCurrentIndex(0)
        layout.addWidget(self.plot_theme_combo)

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
        self.scatter_color_input.setText(DEFAULT_SCATTER_COLOR)
        layout.addWidget(self.scatter_color_input)

        layout.addWidget(divider())

        # ── Trend line style ─────────────────────────────────
        layout.addWidget(section_label("Trend line style"))

        layout.addWidget(field_label("Line color"))
        self.line_color_input = QLineEdit()
        self.line_color_input.setPlaceholderText("e.g. red, blue, #FF5733")
        self.line_color_input.setFont(QFont("monospace", 9))
        self.line_color_input.textChanged.connect(self.settings_builder.set_line_color)
        self.line_color_input.setText(DEFAULT_LINE_COLOR)
        layout.addWidget(self.line_color_input)

        layout.addWidget(field_label("Line style"))
        self.linestyle_combo = QComboBox()
        self.linestyle_combo.currentTextChanged.connect(
            self.settings_builder.set_line_style
        )
        self.linestyle_combo.addItems(LINESTYLES)
        layout.addWidget(self.linestyle_combo)

        layout.addStretch()

    def on_reset(self):
        self.title_input.setText("")
        self.x_label_input.setText("")
        self.y_label_input.setText("")

        self.plot_theme_combo.setCurrentIndex(0)
        self.scatter_color_input.setText(DEFAULT_SCATTER_COLOR)
        self.line_color_input.setText(DEFAULT_LINE_COLOR)
        self.linestyle_combo.setCurrentIndex(DEFAULT_LINE_STYLE_INDEX)
