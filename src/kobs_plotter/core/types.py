"""
Dependency-free value types shared across the core layer.

These dataclasses are pure data-transfer objects with no behaviour and
no imports from other kobs_plotter modules, so they can be imported
freely by data_loader, modelling, plotting, and strategies without
introducing import cycles.
"""

from dataclasses import dataclass

import numpy as np

from kobs_plotter.core.diagnostics import PlotDiagnosticType
from kobs_plotter.core.settings import PlotSettings


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
