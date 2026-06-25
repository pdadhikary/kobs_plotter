from typing import Callable

import numpy as np
from scipy import stats

from kobs_plotter.core.data_loader import PlotDataSeries
from kobs_plotter.core.modelling import FitResult
from kobs_plotter.core.settings import PlotSettings, PlotType


def _generate_surface(
    data: PlotDataSeries, result: FitResult
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x_range = np.linspace(data.x.min(), data.x.max(), 100)
    y_range = np.linspace(data.y.min(), data.y.max(), 100)

    x_fit, y_fit = np.meshgrid(x_range, y_range)
    z_fit = result.model((x_fit, y_fit), *result.popt)

    return x_fit, y_fit, z_fit


def confidence_band(x, y, x_fit, model, popt, pcov, confidence=0.99):
    n = len(x)
    p = len(popt)
    dof = n - p

    t_val = stats.t.ppf((1 + confidence) / 2, dof)

    # Compute Jacobian — one row per x_fit point, one col per parameter
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

    # Variance at each point: diagonal of J @ pcov @ J^T
    var_fit = np.einsum("ij,jk,ik->i", jacobian, pcov, jacobian)
    se_fit = np.sqrt(np.maximum(var_fit, 0))  # clip negatives from numerical error

    y_fit = model(x_fit, *popt)
    lower = y_fit - t_val * se_fit
    upper = y_fit + t_val * se_fit

    return lower, upper


def plot(
    data: PlotDataSeries,
    result: FitResult,
    settings: PlotSettings,
    plot_callback: Callable,
):
    perr = np.sqrt(np.diag(result.pcov))
    parameter_string = []
    gof = []
    for param, opt, err in zip(settings.params, result.popt, perr):
        parameter_string.append(f"{param}={opt:.4f} $\\pm$ {err:.3f}")
    gof_metrics = ["$R^2$", "Adj. $R^2$", "RMSE", "MAE", "SSE"]
    for metric, value in zip(
        gof_metrics, [result.r2, result.r2_adj, result.rmse, result.mae, result.sse]
    ):
        gof.append(f"{metric}={value:.4f}")

    result_string = [
        "---Formula---",
        f"$z={result.formula_latex}$"
        if settings.plot_type == PlotType.SURFACE_3D
        else f"$y={result.formula_latex}$",
        "",
        "---Result---",
        *parameter_string,
        "",
        "---Goodness of Fit---",
        *gof,
    ]

    if settings.plot_type == PlotType.SURFACE_3D:
        x_fit, y_fit, z_fit = _generate_surface(data, result)
        plot_callback(
            x=data.x,
            y=data.y,
            z=data.z,
            x_fit=x_fit,
            y_fit=y_fit,
            z_fit=z_fit,
            result_string="\n".join(result_string),
            settings=settings,
        )
    else:
        x_fit = np.linspace(np.min(data.x), np.max(data.x), 1_000)
        y_fit = result.model(x_fit, *result.popt)

        conf_lower, conf_upper = confidence_band(
            data.x, data.y, x_fit, result.model, result.popt, result.pcov
        )

        plot_callback(
            x=data.x,
            y=data.y,
            x_fit=x_fit,
            y_fit=y_fit,
            result_string="\n".join(result_string),
            settings=settings,
            conf_lower=conf_lower,
            conf_upper=conf_upper,
        )
