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
COLORMAPS = [
    "viridis",
    "plasma",
    "inferno",
    "magma",
    "cividis",
    "coolwarm",
    "RdYlBu",
    "spectral",
    "turbo",
    "jet",
]
DEFAULT_SCATTER_COLOR = "black"
DEFAULT_LINE_COLOR = "red"
DEFAULT_LINE_STYLE_INDEX = 0
DEFAULT_COLORMAP_INDEX = 0


class PlotPanel(QWidget):
    def __init__(self, settings_builder: PlotSettingsBuilder):
        super().__init__()
        self.setMaximumWidth(320)
        self.settings_builder = settings_builder
        self.is_3d = False

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── Plot theme ───────────────────────────────────────
        layout.addWidget(section_label("Plot theme"))
        self.plot_theme_combo = QComboBox()
        self.plot_theme_combo.addItems(PLOT_THEMES)
        self.plot_theme_combo.currentTextChanged.connect(
            self.settings_builder.set_plot_theme
        )
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

        # ── Z axis label (3D only, hidden by default) ────────
        self.z_label_widget = QWidget()
        z_label_layout = QVBoxLayout(self.z_label_widget)
        z_label_layout.setContentsMargins(0, 0, 0, 0)
        z_label_layout.setSpacing(4)
        z_label_layout.addWidget(field_label("Z axis"))
        self.z_label_input = QLineEdit()
        self.z_label_input.setPlaceholderText("e.g. Intensity")
        self.z_label_input.textChanged.connect(self.settings_builder.set_z_label)
        z_label_layout.addWidget(self.z_label_input)
        self.z_label_widget.setVisible(False)
        layout.addWidget(self.z_label_widget)

        layout.addWidget(divider())

        # ── Scatter style ────────────────────────────────────
        layout.addWidget(section_label("Scatter style"))

        layout.addWidget(field_label("Point color"))
        self.scatter_color_input = QLineEdit()
        self.scatter_color_input.setPlaceholderText("e.g. black, red, #FF5733")
        self.scatter_color_input.setFont(QFont("monospace", 9))
        self.scatter_color_input.setText(DEFAULT_SCATTER_COLOR)
        self.scatter_color_input.textChanged.connect(
            self.settings_builder.set_point_color
        )
        layout.addWidget(self.scatter_color_input)

        layout.addWidget(divider())

        # ── Trend line style (2D only) ────────────────────────
        self.line_style_widget = QWidget()
        line_style_layout = QVBoxLayout(self.line_style_widget)
        line_style_layout.setContentsMargins(0, 0, 0, 0)
        line_style_layout.setSpacing(4)
        line_style_layout.addWidget(section_label("Trend line style"))

        line_style_layout.addWidget(field_label("Line color"))
        self.line_color_input = QLineEdit()
        self.line_color_input.setPlaceholderText("e.g. red, blue, #FF5733")
        self.line_color_input.setFont(QFont("monospace", 9))
        self.line_color_input.setText(DEFAULT_LINE_COLOR)
        self.line_color_input.textChanged.connect(self.settings_builder.set_line_color)
        line_style_layout.addWidget(self.line_color_input)

        line_style_layout.addWidget(field_label("Line style"))
        self.linestyle_combo = QComboBox()
        self.linestyle_combo.addItems(LINESTYLES)
        self.linestyle_combo.currentTextChanged.connect(
            self.settings_builder.set_line_style
        )
        line_style_layout.addWidget(self.linestyle_combo)
        layout.addWidget(self.line_style_widget)

        # ── Surface colormap (3D only, hidden by default) ─────
        self.colormap_widget = QWidget()
        colormap_layout = QVBoxLayout(self.colormap_widget)
        colormap_layout.setContentsMargins(0, 0, 0, 0)
        colormap_layout.setSpacing(4)
        colormap_layout.addWidget(section_label("Surface style"))
        colormap_layout.addWidget(field_label("Colormap"))
        self.colormap_combo = QComboBox()
        self.colormap_combo.addItems(COLORMAPS)
        self.colormap_combo.currentTextChanged.connect(
            self.settings_builder.set_colormap
        )
        self.colormap_combo.setCurrentIndex(DEFAULT_COLORMAP_INDEX)
        colormap_layout.addWidget(self.colormap_combo)
        self.colormap_widget.setVisible(False)
        layout.addWidget(self.colormap_widget)

        layout.addStretch()

    def set_mode(self, is_3d: bool):
        self.is_3d = is_3d
        self.z_label_widget.setVisible(is_3d)
        self.line_style_widget.setVisible(not is_3d)
        self.colormap_widget.setVisible(is_3d)
        self.colormap_combo.setCurrentIndex(DEFAULT_COLORMAP_INDEX)

    def on_reset(self):
        self.title_input.setText("")
        self.x_label_input.setText("")
        self.y_label_input.setText("")
        self.z_label_input.setText("")
        self.plot_theme_combo.setCurrentIndex(0)
        self.scatter_color_input.setText(DEFAULT_SCATTER_COLOR)
        self.line_color_input.setText(DEFAULT_LINE_COLOR)
        self.linestyle_combo.setCurrentIndex(DEFAULT_LINE_STYLE_INDEX)
        self.colormap_combo.setCurrentIndex(DEFAULT_COLORMAP_INDEX)
        self.is_3d = False
        self.z_label_widget.setVisible(False)
        self.line_style_widget.setVisible(True)
        self.colormap_widget.setVisible(False)
