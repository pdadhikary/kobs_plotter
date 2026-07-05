"""
Plot panel UI component for kobs-plotter.

Centre-right panel: matplotlib theme selection, axis labels, scatter
point styling, and-trend-line-or-surface-colormap styling. State is
pushed into :class:`AppState`.

Hardening relative to the previous version:

- Themes and colormaps are discovered from the running matplotlib at
  startup (``plt.style.available`` / ``matplotlib.colormaps()``), so the
  panel never breaks when matplotlib renames a style.
- Color inputs use :class:`ColorSwatchButton` (a ``QColorDialog`` swatch
  with an advanced hex line edit) instead of bare line edits that
  validated only at plot-render time.
- Default lookups fall back to index 0 when a default is missing
  (:func:`safe_set_current`), preventing ``ValueError`` from ``.index()``.
- Every field has a tooltip; label fields declare that they support
  LaTeX via ``$...$``.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from kobs_plotter.core.defaults import (
    DEFAULT_AXIS_SCALE,
    DEFAULT_COLORMAP,
    DEFAULT_LINE_COLOR,
    DEFAULT_LINE_STYLE,
    DEFAULT_POINT_COLOR,
    DEFAULT_THEME,
)
from kobs_plotter.core.types import AxisScale
from kobs_plotter.ui.ui_helpers import divider, field_label, section_label
from kobs_plotter.ui.viewmodel import AppState
from kobs_plotter.ui.widgets import CollapsibleSection, ColorSwatchButton, safe_set_current

# Curated subset of matplotlib's themes shown in the dropdown. Discovered
# at runtime so renames in newer matplotlib don't break the combo.
_CURATED_THEMES = [
    "ggplot",
    "seaborn-v0_8-whitegrid",
    "seaborn-v0_8-darkgrid",
    "seaborn-v0_8-bright",
    "seaborn-v0_8-paper",
    "fivethirtyeight",
    "bmh",
    "classic",
]


def _available_themes() -> list[str]:
    """Curated themes that actually exist in the running matplotlib."""
    import matplotlib.pyplot as plt

    avail = set(plt.style.available)
    return [t for t in _CURATED_THEMES if t in avail]


def _available_colormaps() -> list[str]:
    """Subset of matplotlib's installed colormaps, kept short for the combo."""
    import matplotlib

    cms = list(matplotlib.colormaps())
    curated = [
        "viridis",
        "plasma",
        "inferno",
        "magma",
        "cividis",
        "coolwarm",
        "RdYlBu",
        "turbo",
    ]
    return [c for c in curated if c in cms] or cms[:8]


LINESTYLES = ["-", "--", "-.", ":"]


class PlotPanel(QWidget):
    """Plot appearance and labelling panel."""

    def __init__(self, state: AppState):
        super().__init__()
        self.state = state
        self.setMaximumWidth(360)
        self.is_3d = False

        self._themes = _available_themes()
        self._colormaps = _available_colormaps()
        self._axis_scales: list[AxisScale] = ["linear", "log", "symlog", "logit", "asinh"]

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── Plot theme ────────────────────────────────────────────
        layout.addWidget(section_label("Plot theme"))
        self.plot_theme_combo = QComboBox()
        self.plot_theme_combo.addItems(self._themes)
        self.plot_theme_combo.setToolTip("matplotlib style applied to plot windows")
        self.plot_theme_combo.currentTextChanged.connect(self.state.set_plot_theme)
        safe_set_current(self.plot_theme_combo, DEFAULT_THEME)
        layout.addWidget(self.plot_theme_combo)

        # ── Labels ────────────────────────────────────────────────
        layout.addWidget(section_label("Plot labels"))
        layout.addWidget(field_label("Title"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Conductance vs Time (LaTeX: $\\alpha$)")
        self.title_input.setToolTip("Plot title. LaTeX supported via $...$.")
        self.title_input.textChanged.connect(self.state.set_title)
        layout.addWidget(self.title_input)

        layout.addWidget(field_label("X axis"))
        self.x_label_input = QLineEdit()
        self.x_label_input.setPlaceholderText("e.g. Time (s)")
        self.x_label_input.setToolTip("X axis label. LaTeX supported via $...$.")
        self.x_label_input.textChanged.connect(self.state.set_x_label)
        layout.addWidget(self.x_label_input)

        layout.addWidget(field_label("Y axis"))
        self.y_label_input = QLineEdit()
        self.y_label_input.setPlaceholderText("e.g. Conductance (S)")
        self.y_label_input.setToolTip("Y axis label. LaTeX supported via $...$.")
        self.y_label_input.textChanged.connect(self.state.set_y_label)
        layout.addWidget(self.y_label_input)

        self.z_label_widget = CollapsibleSection()
        self.z_label_widget.add_widget(field_label("Z axis"))
        self.z_label_input = QLineEdit()
        self.z_label_input.setPlaceholderText("e.g. Intensity")
        self.z_label_input.setToolTip("Z axis label (3D). LaTeX supported via $...$.")
        self.z_label_input.textChanged.connect(self.state.set_z_label)
        self.z_label_widget.add_widget(self.z_label_input)
        self.z_label_widget.setVisible(False)
        layout.addWidget(self.z_label_widget)

        layout.addWidget(divider())

        # ── Scatter style ──────────────────────────────────────────
        layout.addWidget(section_label("Scatter style"))
        layout.addWidget(field_label("Point color"))
        self.scatter_color = ColorSwatchButton(initial=DEFAULT_POINT_COLOR)
        self.scatter_color.setToolTip("Color of the observed data scatter points")
        self.scatter_color.colorChanged.connect(self.state.set_point_color)
        layout.addWidget(self.scatter_color)

        layout.addWidget(divider())

        # ── Trend line style (2D) ─────────────────────────────────
        self.line_style_widget = CollapsibleSection()
        self.line_style_widget.add_widget(section_label("Trend line style"))
        self.line_style_widget.add_widget(field_label("Line color"))
        self.line_color = ColorSwatchButton(initial=DEFAULT_LINE_COLOR)
        self.line_color.setToolTip("Color of the fitted trend line")
        self.line_color.colorChanged.connect(self.state.set_line_color)
        self.line_style_widget.add_widget(self.line_color)

        self.line_style_widget.add_widget(field_label("Line style"))
        self.linestyle_combo = QComboBox()
        self.linestyle_combo.addItems(LINESTYLES)
        self.linestyle_combo.setToolTip("matplotlib line style: - -- -. :")
        self.linestyle_combo.currentTextChanged.connect(self.state.set_line_style)
        safe_set_current(self.linestyle_combo, DEFAULT_LINE_STYLE)
        self.line_style_widget.add_widget(self.linestyle_combo)
        layout.addWidget(self.line_style_widget)

        # ── Axis Style ────────────────────────────────────────────
        self.axis_scale_widget = CollapsibleSection()
        self.axis_scale_widget.add_widget(section_label("Axis Scale"))
        self.axis_scale_widget.add_widget(field_label("X Axis Scale"))
        self.x_axis_scale_combo = QComboBox()
        self.x_axis_scale_combo.addItems(self._axis_scales)
        self.x_axis_scale_combo.currentTextChanged.connect(self.state.set_x_axis_scale)
        safe_set_current(self.x_axis_scale_combo, DEFAULT_AXIS_SCALE)
        self.axis_scale_widget.add_widget(self.x_axis_scale_combo)
        self.axis_scale_widget.add_widget(field_label("Y Axis Scale"))
        self.y_axis_scale_combo = QComboBox()
        self.y_axis_scale_combo.addItems(self._axis_scales)
        self.y_axis_scale_combo.currentTextChanged.connect(self.state.set_y_axis_scale)
        safe_set_current(self.y_axis_scale_combo, DEFAULT_AXIS_SCALE)
        self.axis_scale_widget.add_widget(self.y_axis_scale_combo)
        layout.addWidget(self.axis_scale_widget)

        # ── Surface colormap (3D) ─────────────────────────────────
        self.colormap_widget = CollapsibleSection()
        self.colormap_widget.add_widget(section_label("Surface style"))
        self.colormap_widget.add_widget(field_label("Colormap"))
        self.colormap_combo = QComboBox()
        self.colormap_combo.addItems(self._colormaps)
        self.colormap_combo.setToolTip("matplotlib colormap for the fitted surface")
        self.colormap_combo.currentTextChanged.connect(self.state.set_colormap)
        safe_set_current(self.colormap_combo, DEFAULT_COLORMAP)
        self.colormap_widget.add_widget(self.colormap_combo)
        self.colormap_widget.setVisible(False)
        layout.addWidget(self.colormap_widget)

        layout.addStretch()

    def set_mode(self, is_3d: bool) -> None:
        """Toggle 2D/3D sections."""
        self.is_3d = is_3d
        self.z_label_widget.setVisible(is_3d)
        self.line_style_widget.setVisible(not is_3d)
        self.axis_scale_widget.setVisible(not is_3d)
        self.colormap_widget.setVisible(is_3d)

    # ── reset ─────────────────────────────────────────────────────
    def on_reset(self) -> None:
        self.title_input.setText("")
        self.x_label_input.setText("")
        self.y_label_input.setText("")
        self.z_label_input.setText("")
        safe_set_current(self.plot_theme_combo, DEFAULT_THEME)
        self.scatter_color.set_value(DEFAULT_POINT_COLOR)
        self.line_color.set_value(DEFAULT_LINE_COLOR)
        safe_set_current(self.linestyle_combo, DEFAULT_LINE_STYLE)
        safe_set_current(self.x_axis_scale_combo, DEFAULT_AXIS_SCALE)
        safe_set_current(self.y_axis_scale_combo, DEFAULT_AXIS_SCALE)
        safe_set_current(self.colormap_combo, DEFAULT_COLORMAP)
        self.is_3d = False
        self.z_label_widget.setVisible(False)
        self.line_style_widget.setVisible(True)
        self.colormap_widget.setVisible(False)
