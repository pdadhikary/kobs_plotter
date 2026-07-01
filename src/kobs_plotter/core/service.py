"""
Compute orchestration service for kobs-plotter.

Encapsulates the data-load -> fit -> prepare-payload pipeline that was
previously a free function with side-effecting callbacks. The UI now
calls ComputeService.compute() and receives a (FitResult, PlotPayload)
tuple it can render itself, removing private-callback coupling between
MainWindow and the panels.
"""

from kobs_plotter.core.data_loader import load_data
from kobs_plotter.core.diagnostics import PlotDiagnosticType
from kobs_plotter.core.modelling import FitResult, fit
from kobs_plotter.core.plotting import plot
from kobs_plotter.core.settings import PlotSettings
from kobs_plotter.core.types import PlotPayload


class ComputeService:
    """Orchestrates data loading, model fitting, and plot-payload assembly."""

    def compute(
        self, settings: PlotSettings, diagnostic: PlotDiagnosticType
    ) -> tuple[FitResult, PlotPayload]:
        """
        Run the full compute pipeline for the given settings and diagnostic.

        Args:
            settings:   immutable PlotSettings snapshot from the builder.
            diagnostic: which diagnostic view the resulting payload is for.

        Returns:
            A (FitResult, PlotPayload) tuple. The FitResult feeds the results
            panel tables; the PlotPayload drives plot-window rendering.
        """
        data = load_data(settings)
        result = fit(data, settings)
        payload = plot(data, result, settings, diagnostic)
        return result, payload
