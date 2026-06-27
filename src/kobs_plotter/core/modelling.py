"""
Core curve fitting module for kobs-plotter.

Handles model construction from user-defined symbolic expressions,
parameter initialisation, curve fitting via scipy, and goodness-of-fit
computation for both 2D and 3D plot types.
"""

from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.optimize import curve_fit
from sympy import Basic, lambdify, latex, symbols, sympify

from kobs_plotter.core.data_loader import PlotDataSeries
from kobs_plotter.core.settings import PlotSettings, PlotType
from kobs_plotter.core.transforms import apply_transform


@dataclass(frozen=True)
class FitResult:
    """
    Immutable container for the results of a curve fitting operation.

    Passed from the core computation layer to the UI callbacks for
    display in the results panel and plot window.
    """

    formula_latex: str
    """The fitted model formula rendered as a LaTeX string."""

    popt: np.ndarray
    """Optimal parameter values found by curve_fit."""

    pcov: np.ndarray
    """Covariance matrix of the optimal parameters from curve_fit."""

    model: Callable
    """The compiled model callable used for fitting and plotting."""

    perr: np.ndarray
    """Standard errors of the optimal parameters (sqrt of pcov diagonal)."""

    residuals: np.ndarray
    """Residuals between observed and predicted values (y - y_pred)."""

    r2: np.float64
    """R² coefficient of determination."""

    r2_adj: np.float64
    """Adjusted R² penalised for number of fitted parameters."""

    rmse: np.float64
    """Root mean squared error."""

    mae: np.float64
    """Mean absolute error."""

    sse: np.float64
    """Sum of squared errors."""


@dataclass
class GoodnessOfFit:
    """Intermediate container for goodness-of-fit metrics computed during fitting."""

    residuals: np.ndarray
    r2: np.float64
    r2_adj: np.float64
    rmse: np.float64
    mae: np.float64
    sse: np.float64


def _build_model(settings: PlotSettings) -> tuple[Callable, Basic]:
    """
    Parse the user-defined formula string into a curve_fit compatible callable.

    For 2D fits the model signature is f(x, *params).
    For 3D fits the independent variables are packed into a single array XY
    of shape (2, n) so that curve_fit receives f(XY, *params), where
    XY[0] = x and XY[1] = y.

    Args:
        settings: immutable PlotSettings containing the formula and params.

    Returns:
        Tuple of (model callable, sympy expression).

    Raises:
        ValueError: if the formula or parameter symbols cannot be parsed.
    """
    param_syms = symbols(settings.params)
    if not isinstance(param_syms, (list, tuple)):
        param_syms = [param_syms]
    expr = sympify(settings.formula)

    if settings.plot_type == PlotType.SURFACE_3D:
        x_sym, y_sym = symbols("x y")
        raw_func = lambdify([x_sym, y_sym, *param_syms], expr, modules="numpy")

        def model(XY, *params):
            x, y = XY
            return raw_func(x, y, *params)

    else:
        x_sym = symbols("x")
        model = lambdify([x_sym, *param_syms], expr, modules="numpy")

    return model, expr


def _goodness_of_fit(
    y: np.ndarray,
    y_pred: np.ndarray,
    n_params: int,
) -> GoodnessOfFit:
    """
    Compute common goodness-of-fit metrics from observed and predicted values.

    Args:
        y:        observed dependent variable values.
        y_pred:   model predicted values at the same points.
        n_params: number of fitted parameters, used to compute adjusted R².

    Returns:
        GoodnessOfFit containing residuals, R², adjusted R², RMSE, MAE, SSE.
    """
    n = len(y)
    residuals = y - y_pred

    sse = np.float64(np.sum(residuals**2))
    ss_tot = np.sum((y - np.mean(y)) ** 2)

    r2 = np.float64(1 - sse / ss_tot)
    r2_adj = np.float64(1 - (1 - r2) * (n - 1) / (n - n_params - 1))
    rmse = np.float64(np.sqrt(np.mean(residuals**2)))
    mae = np.float64(np.mean(np.abs(residuals)))

    return GoodnessOfFit(
        residuals=residuals,
        r2=r2,
        r2_adj=r2_adj,
        rmse=rmse,
        mae=mae,
        sse=sse,
    )


def _resolve_p0(
    p0_exprs: list[str],
    data: PlotDataSeries,
) -> list[float]:
    """
    Evaluate initial parameter guess expressions against the loaded data.

    Each expression in p0_exprs is evaluated with x, y, z, and np available
    in scope, allowing data-driven initial guesses such as 'np.max(y)' or
    'np.mean(x)'.

    Args:
        p0_exprs: list of expression strings, one per parameter.
        data:     loaded data series providing x, y, z arrays for the namespace.

    Returns:
        List of float initial guesses, one per parameter.

    Raises:
        ValueError: if any expression is invalid or does not evaluate to a number.
    """
    namespace = {
        "x": data.x,
        "y": data.y,
        "z": data.z if isinstance(data.z, np.ndarray) else np.array([]),
        "np": np,
    }
    p0 = []
    for expr in p0_exprs:
        result = apply_transform(expr, namespace, label=f"p0 expression '{expr}'")
        if result is not None:
            p0.append(float(result))
        else:
            try:
                p0.append(float(eval(expr, namespace)))
            except Exception:
                raise ValueError(f'Invalid initial value expression: "{expr}"')
    return p0


def fit(data: PlotDataSeries, settings: PlotSettings) -> FitResult:
    """
    Fit the user-defined model to the loaded data series.

    Builds the model callable from the formula string, resolves initial
    parameter guesses, runs scipy curve_fit, and computes goodness-of-fit
    metrics. Supports both 2D (x → y) and 3D (x, y → z) fitting.

    Args:
        data:     loaded and transformed data series from load_data().
        settings: immutable PlotSettings from the builder.

    Returns:
        FitResult containing optimal parameters, covariance, model callable,
        standard errors, residuals, and goodness-of-fit metrics.

    Raises:
        ValueError: if p0 expressions are invalid or the model formula fails.
        RuntimeError: if curve_fit fails to converge within maxfev iterations.
    """
    model, expr = _build_model(settings)
    p0 = _resolve_p0(settings.p0, data)

    if settings.plot_type == PlotType.SURFACE_3D:
        z = data.z if isinstance(data.z, np.ndarray) else np.array([])
        popt, pcov = curve_fit(
            model, (data.x, data.y), z, p0=p0, method="lm", maxfev=10_000
        )
        z_pred = model((data.x, data.y), *popt)
        gof = _goodness_of_fit(z, z_pred, len(p0))
    else:
        popt, pcov = curve_fit(model, data.x, data.y, p0=p0, method="lm", maxfev=10_000)
        y_pred = model(data.x, *popt)
        gof = _goodness_of_fit(data.y, y_pred, len(p0))

    perr = np.sqrt(np.diag(pcov))

    return FitResult(
        formula_latex=latex(expr),
        popt=popt,
        pcov=pcov,
        model=model,
        perr=perr,
        residuals=gof.residuals,
        r2=gof.r2,
        r2_adj=gof.r2_adj,
        rmse=gof.rmse,
        mae=gof.mae,
        sse=gof.sse,
    )
