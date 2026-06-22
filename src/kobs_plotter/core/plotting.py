from typing import Callable

import numpy as np

from kobs_plotter.core.data_loader import PlotDataSeries
from kobs_plotter.core.modelling import FitResult
from kobs_plotter.core.settings import PlotSettings


def plot(
    data: PlotDataSeries,
    result: FitResult,
    settings: PlotSettings,
    plot_callback: Callable,
):
    x_fit = np.linspace(np.min(data.x), np.max(data.x), 1_000)
    y_fit = result.model(x_fit, *result.popt)

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
        "",
        f"y={settings.formula}",
        "---Result---",
        *parameter_string,
        "",
        "---Goodness of Fit---",
        *gof,
    ]

    plot_callback(
        x=data.x,
        y=data.y,
        x_fit=x_fit,
        y_fit=y_fit,
        result_string="\n".join(result_string),
        settings=settings,
    )
