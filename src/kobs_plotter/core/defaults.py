"""
Single source of truth for default plot settings.

Both the core PlotSettingsBuilder (initial builder state) and the UI
PlotPanel (default widget values) import from here so the two cannot
silently drift out of sync.
"""

DEFAULT_THEME = "ggplot"
"""Default matplotlib style theme applied to plot windows."""

DEFAULT_POINT_COLOR = "black"
"""Default color for observed scatter data points."""

DEFAULT_LINE_COLOR = "red"
"""Default color for the fitted trend line."""

DEFAULT_LINE_STYLE = "-"
"""Default line style for the fitted trend line (solid)."""

DEFAULT_COLORMAP = "viridis"
"""Default colormap for 3D surface plots."""
