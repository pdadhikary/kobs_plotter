"""
Shared value types for the core layer.

These are pure data-transfer objects plus the small enums/aliases
(PlotType, AxisScale) that the DTOs reference. The module depends only
on kobs_plotter.core.diagnostics, so it can be imported freely by
data_loader, modelling, plotting, defaults, and strategies without
introducing import cycles. settings.py re-exports PlotSettings and
PlotType from here for back-compat with existing call sites.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Literal

import numpy as np

from kobs_plotter.core.diagnostics import PlotDiagnosticType

AxisScale = Literal["linear", "log", "symlog", "logit", "asinh"]


class PlotType(Enum):
    """Enum representing the type of plot to generate."""

    """2D scatter plot with a fitted trend line."""
    SCATTER_LINE = auto()
    """3D surface plot with scatter points."""
    SURFACE_3D = auto()


@dataclass(frozen=True)
class PlotSettings:
    """
    immutable snapshot of all user-configured settings passed to the
    core computation and plotting layer.

    this object is constructed by plotsettingsbuilder.build() and should
    never be mutated after creation. all fields are either required or
    explicitly optional to make missing values visible at the type level.
    """

    plot_type: PlotType
    data_path: str
    sheet_name: str
    x_col: str
    y_col: str
    z_col: str | None
    x_transform: str | None
    y_transform: str | None
    z_transform: str | None
    params: tuple[str, ...]
    formula: str
    p0: tuple[str, ...]
    plot_theme: str
    title: str | None
    x_label: str | None
    y_label: str | None
    z_label: str | None
    x_axis_scale: AxisScale
    y_axis_scale: AxisScale
    point_color: str
    line_color: str
    line_style: str
    colormap: str


@dataclass(frozen=True)
class PlotDataSeries:
    """
    Immutable container for the raw (and optionally transformed)
    data series passed to the fitting and plotting layer.
    """

    x: np.ndarray
    y: np.ndarray
    z: np.ndarray | None


@dataclass(frozen=True)
class PlotPayload:
    """
    Immutable container bundling everything the UI needs to render a plot.

    Returned by plot() and consumed by PlotWindow.plot(). Fields are
    optional depending on plot type and diagnostic — 2D plots populate
    conf_lower/conf_upper and leave z fields None; 3D plots populate
    z_fit and leave the confidence band fields None.
    """

    x: np.ndarray
    """Observed independent variable values."""

    y: np.ndarray
    """Observed dependent variable values (Y for 2D, Y coordinate for 3D)."""

    x_fit: np.ndarray
    """Dense X values along the fitted curve (2D) or X mesh (3D)."""

    y_fit: np.ndarray
    """Fitted Y values (2D) or Y mesh (3D)."""

    result_string: str
    """Formatted multi-line string shown in the right plot margin."""

    residuals: np.ndarray
    """Fit residuals (observed - predicted)."""

    settings: PlotSettings
    """Immutable plot settings driving labels, colors, and theme."""

    diagnostic: PlotDiagnosticType
    """Which diagnostic view the UI should render from this payload."""

    z: np.ndarray | None = None
    """Observed Z values for 3D plots; None for 2D."""

    z_fit: np.ndarray | None = None
    """Fitted Z mesh for 3D plots; None for 2D."""

    conf_lower: np.ndarray | None = None
    """Lower confidence band for 2D plots; None for 3D."""

    conf_upper: np.ndarray | None = None
    """Upper confidence band for 2D plots; None for 3D."""
