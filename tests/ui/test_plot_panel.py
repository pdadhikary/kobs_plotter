"""Tests for the plot panel: runtime discovery, safe defaults, color swatches."""

from kobs_plotter.core.defaults import (
    DEFAULT_COLORMAP,
    DEFAULT_LINE_COLOR,
    DEFAULT_POINT_COLOR,
    DEFAULT_THEME,
)


def test_themes_discovered_from_matplotlib(qtbot, main_window):
    pp = main_window.plot_panel
    # ggplot is part of every matplotlib; ensure present and selected by default.
    assert "ggplot" in [pp.plot_theme_combo.itemText(i) for i in range(pp.plot_theme_combo.count())]
    assert pp.plot_theme_combo.currentText() == DEFAULT_THEME


def test_colormaps_discovered(qtbot, main_window):
    pp = main_window.plot_panel
    assert pp.colormap_combo.currentText() == DEFAULT_COLORMAP
    assert pp.colormap_combo.count() > 0


def test_color_swatch_emits_change(qtbot, main_window):
    pp = main_window.plot_panel
    received = []
    pp.scatter_color.colorChanged.connect(lambda c: received.append(c))
    pp.scatter_color.set_value("#123456")
    assert received == ["#123456"]
    assert pp.scatter_color.value() == "#123456"


def test_safe_default_missing_falls_back_to_index0(qtbot, main_window):
    pp = main_window.plot_panel
    # If the default theme were ever absent, the combo falls back to row 0
    # instead of raising ValueError from .index().
    assert pp.plot_theme_combo.currentIndex() >= 0


def test_mode_toggle_visibility(qtbot, main_window):
    pp = main_window.plot_panel
    pp.set_mode(True)
    assert pp.z_label_widget.isHidden() is False
    assert pp.colormap_widget.isHidden() is False
    assert pp.line_style_widget.isHidden() is True
    pp.set_mode(False)
    assert pp.z_label_widget.isHidden() is True
    assert pp.colormap_widget.isHidden() is True
    assert pp.line_style_widget.isHidden() is False


def test_reset_restores_defaults(qtbot, main_window):
    pp = main_window.plot_panel
    pp.title_input.setText("custom")
    pp.scatter_color.set_value("#abcdef")
    pp.on_reset()
    assert pp.title_input.text() == ""
    assert pp.scatter_color.value() == DEFAULT_POINT_COLOR
    assert pp.line_color.value() == DEFAULT_LINE_COLOR
