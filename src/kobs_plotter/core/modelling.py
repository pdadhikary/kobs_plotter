"""
Core curve fitting module for kobs-plotter.

Handles parameter initialisation, curve fitting via scipy (dispatched to
the active plot-type strategy), and goodness-of-fit computation.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np
from sympy import latex

from kobs_plotter.core.settings import PlotSettings
from kobs_plotter.core.strategies import STRATEGIES
from kobs_plotter.core.types import PlotDataSeries  # noqa: F401


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


@dataclass(frozen=True)
class GoodnessOfFit:
    """Intermediate container for goodness-of-fit metrics computed during fitting.

    Frozen for consistency with the other core DTOs (PlotSettings,
    PlotDataSeries, FitResult, PlotPayload) — it is built once and never
    mutated.
    """

    residuals: np.ndarray
    r2: np.float64
    r2_adj: np.float64
    rmse: np.float64
    mae: np.float64
    sse: np.float64


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
    p0_exprs: Sequence[str],
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
    # Restrict builtins so user-supplied p0 expressions cannot invoke
    # arbitrary Python. Only np and the axis arrays are in scope; np.*
    # helpers (np.max, np.min, np.mean, ...) remain available.
    safe_globals: dict = {"__builtins__": {}}
    p0 = []
    for expr in p0_exprs:
        if not expr or not expr.strip():
            result = 1.0
        else:
            try:
                result = eval(expr, safe_globals, namespace)
            except Exception as e:
                raise ValueError(
                    f'Invalid initial value expression: "{expr}"'
                ) from e

        if result is not None:
            p0.append(float(result))
        else:
            raise ValueError(f'Invalid initial value expression: "{expr}"')
    return p0


def fit(data: PlotDataSeries, settings: PlotSettings) -> FitResult:
    """
    Fit the user-defined model to the loaded data series.

    Resolves initial parameter guesses, dispatches model construction and
    curve fitting to the active plot-type strategy, and computes
    goodness-of-fit metrics. Supports both 2D (x -> y) and 3D (x, y -> z)
    fitting via the strategy registry.

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
    strategy = STRATEGIES[settings.plot_type]
    model, expr = strategy.build_model(settings)
    p0 = _resolve_p0(settings.p0, data)

    popt, pcov, observed, predicted = strategy.run_fit(model, data, p0)
    gof = _goodness_of_fit(observed, predicted, len(p0))
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
