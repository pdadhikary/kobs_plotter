"""
Plotting preparation module for kobs-plotter.

Handles generation of fitted curves and surfaces, confidence band
computation, result string formatting, and assembly of a PlotPayload
that the UI layer renders.
"""

from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np
from scipy import stats

from kobs_plotter.core.data_loader import PlotDataSeries
from kobs_plotter.core.diagnostics import PlotDiagnosticType
from kobs_plotter.core.modelling import FitResult
from kobs_plotter.core.settings import PlotSettings, PlotType


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

    z: Optional[np.ndarray] = None
    """Observed Z values for 3D plots; None for 2D."""

    z_fit: Optional[np.ndarray] = None
    """Fitted Z mesh for 3D plots; None for 2D."""

    conf_lower: Optional[np.ndarray] = None
    """Lower confidence band for 2D plots; None for 3D."""

    conf_upper: Optional[np.ndarray] = None
    """Upper confidence band for 2D plots; None for 3D."""


def _generate_surface(
    data: PlotDataSeries,
    result: FitResult,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate a meshgrid surface from the fitted 3D model.

    Creates a uniform 100x100 grid spanning the observed x and y ranges,
    evaluates the fitted model over the grid, and returns the mesh arrays
    for use with matplotlib's plot_surface.

    Args:
        data:   loaded data series providing x and y range bounds.
        result: fit result containing the compiled model and optimal parameters.

    Returns:
        Tuple of (x_mesh, y_mesh, z_mesh) each of shape (100, 100).
    """
    x_range = np.linspace(data.x.min(), data.x.max(), 100)
    y_range = np.linspace(data.y.min(), data.y.max(), 100)

    x_fit, y_fit = np.meshgrid(x_range, y_range)
    z_fit = result.model((x_fit, y_fit), *result.popt)

    return x_fit, y_fit, z_fit


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

    Args:
        x:          observed independent variable values used for fitting.
        y:          observed dependent variable values used for fitting.
        x_fit:      points at which to evaluate the confidence band.
        model:      fitted model callable with signature f(x, *params).
        popt:       optimal parameter values from curve_fit.
        pcov:       parameter covariance matrix from curve_fit.
        confidence: confidence level between 0 and 1, default 0.99 (99%).

    Returns:
        Tuple of (lower, upper) confidence band arrays, each the same
        length as x_fit.
    """
    n = len(x)
    p = len(popt)
    dof = n - p

    t_val = stats.t.ppf((1 + confidence) / 2, dof)

    # Numerical Jacobian — central difference per parameter at each x_fit point
    # Shape: (n_points, n_params)
    jacobian = np.zeros((len(x_fit), p))
    for i, xi in enumerate(x_fit):
        for j in range(p):
            eps = np.sqrt(np.finfo(float).eps) * (abs(popt[j]) + 1)
            popt_plus = popt.copy()
            popt_plus[j] += eps
            popt_minus = popt.copy()
            popt_minus[j] -= eps
            jacobian[i, j] = (model(xi, *popt_plus) - model(xi, *popt_minus)) / (
                2 * eps
            )

    # Pointwise variance: diagonal of J @ pcov @ J^T
    # Clipped to zero to guard against tiny negatives from floating point error
    var_fit = np.einsum("ij,jk,ik->i", jacobian, pcov, jacobian)
    se_fit = np.sqrt(np.maximum(var_fit, 0))

    y_fit = model(x_fit, *popt)
    lower = y_fit - t_val * se_fit
    upper = y_fit + t_val * se_fit

    return lower, upper


def _format_result_string(
    settings: PlotSettings,
    result: FitResult,
) -> str:
    """
    Format the fit result into a multi-line string for display on the plot.

    Includes the fitted formula in LaTeX notation, optimal parameter values
    with standard errors, and goodness-of-fit metrics.

    Args:
        settings: plot settings providing parameter names and plot type.
        result:   fit result providing popt, pcov, and goodness-of-fit values.

    Returns:
        Newline-joined string ready for use with matplotlib's figure.text().
    """
    perr = np.sqrt(np.diag(result.pcov))

    dep_var = "z" if settings.plot_type == PlotType.SURFACE_3D else "y"
    parameter_lines = [
        f"{param}={opt:.4f} $\\pm$ {err:.3f}"
        for param, opt, err in zip(settings.params, result.popt, perr)
    ]
    gof_lines = [
        f"{metric}={value:.4f}"
        for metric, value in zip(
            ["$R^2$", "Adj. $R^2$", "RMSE", "MAE", "SSE"],
            [result.r2, result.r2_adj, result.rmse, result.mae, result.sse],
        )
    ]

    lines = [
        "---Formula---",
        f"${dep_var}={result.formula_latex}$",
        "",
        "---Result---",
        *parameter_lines,
        "",
        "---Goodness of Fit---",
        *gof_lines,
    ]

    return "\n".join(lines)


def plot(
    data: PlotDataSeries,
    result: FitResult,
    settings: PlotSettings,
    diagnostic: PlotDiagnosticType,
) -> PlotPayload:
    """
    Prepare plot data and return a PlotPayload for the UI to render.

    For 2D plots generates a smooth fitted curve and computes a confidence
    band. For 3D plots generates a surface mesh over the observed x/y range.
    Formats the result string and packages everything into an immutable
    PlotPayload returned to the caller.

    Args:
        data:       loaded and transformed data series.
        result:     fit result from the modelling layer.
        settings:   immutable plot settings.
        diagnostic: which diagnostic view to render from the resulting payload.

    Returns:
        PlotPayload bundling all inputs the UI needs for rendering.
    """
    result_string = _format_result_string(settings, result)

    if settings.plot_type == PlotType.SURFACE_3D:
        x_fit, y_fit, z_fit = _generate_surface(data, result)
        return PlotPayload(
            x=data.x,
            y=data.y,
            z=data.z,
            x_fit=x_fit,
            y_fit=y_fit,
            z_fit=z_fit,
            residuals=result.residuals,
            result_string=result_string,
            settings=settings,
            diagnostic=diagnostic,
        )

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
        conf_lower=conf_lower,
        conf_upper=conf_upper,
        diagnostic=diagnostic,
    )
