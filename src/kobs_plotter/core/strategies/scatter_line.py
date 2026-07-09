"""
Strategy for 2D scatter / line plots.

Handles series extraction from a single dependent column, single-variable
model construction, curve fitting against (x -> y), confidence-band
computation, and 2D plot payload assembly.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import numpy as np

from kobs_plotter.core.diagnostics import PlotDiagnosticType
from kobs_plotter.core.strategies.base import PlotStrategy
from kobs_plotter.core.transforms import apply_transform
from kobs_plotter.core.types import PlotDataSeries, PlotPayload, PlotSettings, PlotType

if TYPE_CHECKING:
    import pandas as pd
    from sympy import Basic

    from kobs_plotter.core.modelling import FitResult


def confidence_band(
    x: np.ndarray,
    y: np.ndarray,
    x_fit: np.ndarray,
    model: Callable,
    popt: np.ndarray,
    pcov: np.ndarray,
    confidence: float = 0.99,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute a pointwise confidence band around a 2D fitted curve.

    Uses the full parameter covariance matrix from curve_fit and a
    numerical Jacobian to compute the standard error of the model
    prediction at each point in x_fit. Does not assume uniform variance
    (heteroscedasticity safe).

    The band represents where the true underlying curve is expected to
    lie with the given confidence level — it is NOT a prediction interval
    for individual observations.
    """
    n = len(x)
    p = len(popt)
    dof = n - p

    from scipy import stats

    t_val = stats.t.ppf((1 + confidence) / 2, dof)

    jacobian = np.zeros((len(x_fit), p))
    for i, xi in enumerate(x_fit):
        for j in range(p):
            eps = np.sqrt(np.finfo(float).eps) * (abs(popt[j]) + 1)
            popt_plus = popt.copy()
            popt_plus[j] += eps
            popt_minus = popt.copy()
            popt_minus[j] -= eps
            jacobian[i, j] = (model(xi, *popt_plus) - model(xi, *popt_minus)) / (2 * eps)

    var_fit = np.einsum("ij,jk,ik->i", jacobian, pcov, jacobian)
    se_fit = np.sqrt(np.maximum(var_fit, 0))

    y_fit = model(x_fit, *popt)
    lower = y_fit - t_val * se_fit
    upper = y_fit + t_val * se_fit

    return lower, upper


class ScatterLineStrategy(PlotStrategy):
    """Strategy for PlotType.SCATTER_LINE (x -> y) fitting and plotting."""

    plot_type = PlotType.SCATTER_LINE
    dependent_label = "y"

    def load_series(self, settings: PlotSettings, df: pd.DataFrame) -> PlotDataSeries:
        x = np.array(df[settings.x_col].dropna(), dtype=float)
        y = np.array(df[settings.y_col].dropna(), dtype=float)
        namespace = {"x": x, "y": y, "z": None, "np": np}
        x_prime = apply_transform(settings.x_transform, namespace, "x")
        y_prime = apply_transform(settings.y_transform, namespace, "y")
        return PlotDataSeries(x_prime, y_prime, None)

    def build_model(self, settings: PlotSettings) -> tuple[Callable, Basic]:
        from sympy import lambdify, symbols, sympify

        param_syms = symbols(settings.params)
        if not isinstance(param_syms, (list, tuple)):
            param_syms = [param_syms]
        expr = sympify(settings.formula)
        x_sym = symbols("x")
        model = lambdify([x_sym, *param_syms], expr, modules="numpy")
        return model, expr

    def run_fit(
        self, model: Callable, data: PlotDataSeries, p0: list[float]
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        from scipy.optimize import curve_fit

        popt, pcov = curve_fit(model, data.x, data.y, p0=p0, method="lm", maxfev=10_000)
        y_pred = model(data.x, *popt)
        return popt, pcov, data.y, y_pred

    def prepare_payload(
        self,
        data: PlotDataSeries,
        result: FitResult,
        settings: PlotSettings,
    ) -> PlotPayload:
        result_string = self.format_result_string(settings, result)
        x_fit = np.linspace(np.min(data.x), np.max(data.x), 1_000)
        y_fit = result.model(x_fit, *result.popt)
        conf_lower, conf_upper = confidence_band(
            data.x, data.y, x_fit, result.model, result.popt, result.pcov
        )
        return PlotPayload(
            x=data.x,
            y=data.y,
            x_fit=x_fit,
            y_fit=y_fit,
            result_string=result_string,
            residuals=result.residuals,
            settings=settings,
            diagnostic=PlotDiagnosticType.PLOT,
            conf_lower=conf_lower,
            conf_upper=conf_upper,
        )
