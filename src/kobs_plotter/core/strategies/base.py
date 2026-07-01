"""
Abstract base class for plot-type strategies.

A PlotStrategy bundles the plot-type-specific behaviour that was
previously implemented as if-plot_type branches in data_loader,
modelling, and plotting. Each concrete strategy owns its series
extraction, model construction, curve-fit invocation, and plot
payload assembly. Shared formatting logic lives on the base class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import pandas as pd
    from sympy import Basic

    from kobs_plotter.core.modelling import FitResult
    from kobs_plotter.core.settings import PlotSettings, PlotType
    from kobs_plotter.core.types import PlotDataSeries, PlotPayload


class PlotStrategy(ABC):
    """Strategy encapsulating all plot-type-specific computation."""

    plot_type: PlotType
    """The PlotType this strategy handles."""

    dependent_label: str
    """Symbol used for the dependent variable in the result string ('y' or 'z')."""

    @abstractmethod
    def load_series(
        self, settings: PlotSettings, df: pd.DataFrame
    ) -> PlotDataSeries:
        """Extract the (optionally transformed) data series from the loaded frame."""

    @abstractmethod
    def build_model(self, settings: PlotSettings) -> tuple[Callable, Basic]:
        """Parse the formula string into a curve_fit-compatible callable and sympy expr."""

    @abstractmethod
    def run_fit(
        self, model: Callable, data: PlotDataSeries, p0: list[float]
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Run curve_fit and return (popt, pcov, observed_dep, predicted_dep)."""

    @abstractmethod
    def prepare_payload(
        self,
        data: PlotDataSeries,
        result: FitResult,
        settings: PlotSettings,
    ) -> PlotPayload:
        """
        Assemble the main-plot PlotPayload bundling everything the UI needs.

        Only invoked for the primary fit plot — residual and Q-Q diagnostics
        are short-circuited by the plot() dispatcher into a minimal payload.
        """

    def format_result_string(
        self, settings: PlotSettings, result: FitResult
    ) -> str:
        """Format fit results into the multi-line string shown on the plot."""
        parameter_lines = [
            f"{param}={opt:.4f} $\\pm$ {err:.3f}"
            for param, opt, err in zip(settings.params, result.popt, result.perr, strict=False)
        ]
        gof_lines = [
            f"{metric}={value:.4f}"
            for metric, value in zip(
                ["$R^2$", "Adj. $R^2$", "RMSE", "MAE", "SSE"],
                [result.r2, result.r2_adj, result.rmse, result.mae, result.sse],
                strict=True,
            )
        ]
        lines = [
            "---Formula---",
            f"${self.dependent_label}={result.formula_latex}$",
            "",
            "---Result---",
            *parameter_lines,
            "",
            "---Goodness of Fit---",
            *gof_lines,
        ]
        return "\n".join(lines)

