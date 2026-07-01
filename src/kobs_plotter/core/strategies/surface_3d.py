"""
Strategy for 3D surface plots.

Handles series extraction from a third dependent column, two-variable
model construction (x, y -> z), curve fitting with the independent
variables packed as a (2, n) tuple, surface mesh generation, and 3D
plot payload assembly.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from sympy import Basic, lambdify, symbols, sympify

from kobs_plotter.core.diagnostics import PlotDiagnosticType
from kobs_plotter.core.settings import PlotSettings, PlotType
from kobs_plotter.core.strategies.base import PlotStrategy
from kobs_plotter.core.transforms import apply_transform
from kobs_plotter.core.types import PlotDataSeries, PlotPayload

if TYPE_CHECKING:
    from kobs_plotter.core.modelling import FitResult


class Surface3DStrategy(PlotStrategy):
    """Strategy for PlotType.SURFACE_3D (x, y -> z) fitting and plotting."""

    plot_type = PlotType.SURFACE_3D
    dependent_label = "z"

    def load_series(self, settings: PlotSettings, df: pd.DataFrame) -> PlotDataSeries:
        x = np.array(df[settings.x_col], dtype=float)
        y = np.array(df[settings.y_col], dtype=float)
        z = np.array(df[settings.z_col], dtype=float)
        namespace = {"x": x, "y": y, "z": z, "np": np}
        x_prime = apply_transform(settings.x_transform, namespace, "x")
        y_prime = apply_transform(settings.y_transform, namespace, "y")
        z_prime = apply_transform(settings.z_transform, namespace, "z")
        return PlotDataSeries(x_prime, y_prime, z_prime)

    def build_model(self, settings: PlotSettings) -> tuple[Callable, Basic]:
        param_syms = symbols(settings.params)
        if not isinstance(param_syms, (list, tuple)):
            param_syms = [param_syms]
        expr = sympify(settings.formula)
        x_sym, y_sym = symbols("x y")
        raw_func = lambdify([x_sym, y_sym, *param_syms], expr, modules="numpy")

        def model(XY, *params):
            x, y = XY
            return raw_func(x, y, *params)

        return model, expr

    def run_fit(
        self, model: Callable, data: PlotDataSeries, p0: list[float]
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        z = data.z if isinstance(data.z, np.ndarray) else np.array([])
        popt, pcov = curve_fit(
            model, (data.x, data.y), z, p0=p0, method="lm", maxfev=10_000
        )
        z_pred = model((data.x, data.y), *popt)
        return popt, pcov, z, z_pred

    def prepare_payload(
        self,
        data: PlotDataSeries,
        result: FitResult,
        settings: PlotSettings,
    ) -> PlotPayload:
        result_string = self.format_result_string(settings, result)

        x_range = np.linspace(data.x.min(), data.x.max(), 100)
        y_range = np.linspace(data.y.min(), data.y.max(), 100)
        x_fit, y_fit = np.meshgrid(x_range, y_range)
        z_fit = result.model((x_fit, y_fit), *result.popt)

        return PlotPayload(
            x=data.x,
            y=data.y,
            z=data.z,
            x_fit=x_fit,
            y_fit=y_fit,
            z_fit=z_fit,
            result_string=result_string,
            residuals=result.residuals,
            settings=settings,
            diagnostic=PlotDiagnosticType.PLOT,
        )

