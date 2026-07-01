"""
Plotting preparation module for kobs-plotter.

Delegates per-plot-type payload assembly (fitted curve / confidence
band for 2D, surface mesh for 3D) to the active plot-type strategy.
The immutable PlotPayload DTO is re-exported from core.types for
backwards compatibility with existing UI imports.
"""

import numpy as np

from kobs_plotter.core.diagnostics import PlotDiagnosticType
from kobs_plotter.core.modelling import FitResult
from kobs_plotter.core.settings import PlotSettings
from kobs_plotter.core.strategies import STRATEGIES
from kobs_plotter.core.types import PlotDataSeries, PlotPayload  # noqa: F401


def plot(
    data: PlotDataSeries,
    result: FitResult,
    settings: PlotSettings,
    diagnostic: PlotDiagnosticType,
) -> PlotPayload:
    """
    Prepare plot data and return a PlotPayload for the UI to render.

    For the primary fit plot (PlotDiagnosticType.PLOT) delegates per-plot-type
    payload assembly (fitted curve / confidence band for 2D, surface mesh for
    3D) to the active plot-type strategy. For residual and Q-Q diagnostics
    short-circuits into a minimal payload — the curve, mesh, and confidence
    band are not needed for those views and computing them would be wasted work.

    Args:
        data:       loaded and transformed data series.
        result:     fit result from the modelling layer.
        settings:   immutable plot settings.
        diagnostic: which diagnostic view to render from the resulting payload.

    Returns:
        PlotPayload bundling all inputs the UI needs for rendering.
    """
    if diagnostic != PlotDiagnosticType.PLOT:
        return PlotPayload(
            x=data.x,
            y=data.y,
            z=data.z,
            x_fit=np.array([]),
            y_fit=np.array([]),
            result_string="",
            residuals=result.residuals,
            settings=settings,
            diagnostic=diagnostic,
        )

    strategy = STRATEGIES[settings.plot_type]
    return strategy.prepare_payload(data, result, settings)