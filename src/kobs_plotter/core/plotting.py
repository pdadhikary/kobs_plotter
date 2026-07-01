"""
Plotting preparation module for kobs-plotter.

Delegates per-plot-type payload assembly (fitted curve / confidence
band for 2D, surface mesh for 3D) to the active plot-type strategy.
The immutable PlotPayload DTO is re-exported from core.types for
backwards compatibility with existing UI imports.
"""

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

    Delegates per-plot-type payload assembly (fitted curve / confidence
    band for 2D, surface mesh for 3D) to the active plot-type strategy.

    Args:
        data:       loaded and transformed data series.
        result:     fit result from the modelling layer.
        settings:   immutable plot settings.
        diagnostic: which diagnostic view to render from the resulting payload.

    Returns:
        PlotPayload bundling all inputs the UI needs for rendering.
    """
    strategy = STRATEGIES[settings.plot_type]
    return strategy.prepare_payload(data, result, settings, diagnostic)