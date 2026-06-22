import sys
from dataclasses import dataclass
from typing import Callable

from scipy.optimize import curve_fit
from sympy import sympify, lambdify, symbols
import numpy as np

from kobs_plotter.core.settings import PlotSettings
from kobs_plotter.core.data_loader import PlotDataSeries


@dataclass(frozen=True)
class FitResult:
    popt: np.ndarray
    pcov: np.ndarray
    model: Callable
    perr: np.ndarray
    r2: np.float64
    r2_adj: np.float64
    rmse: np.float64
    mae: np.float64
    sse: np.float64


@dataclass
class GoodnessOfFit:
    r2: np.float64
    r2_adj: np.float64
    rmse: np.float64
    mae: np.float64
    sse: np.float64


def _build_model(settings: PlotSettings) -> Callable:
    x_sym = symbols("x")
    param_syms = symbols(settings.params)

    if not isinstance(param_syms, (list, tuple)):
        param_syms = [param_syms]

    expr = sympify(settings.formula)

    model = lambdify([x_sym, *param_syms], expr, modules="numpy")

    return model


def _goodness_of_fit(y: np.ndarray, y_pred: np.ndarray, n_params: int) -> GoodnessOfFit:
    n = len(y)
    residuals = y - y_pred

    sse = np.float64(np.sum(residuals**2))
    ss_tot = np.sum((y - np.mean(y)) ** 2)

    r2 = np.float64(1 - sse / ss_tot)
    r2_adj = np.float64(1 - (1 - r2) * (n - 1) / (n - n_params - 1))
    rmse = np.float64(np.sqrt(np.mean(residuals**2)))
    mae = np.float64(np.mean(np.abs(residuals)))

    return GoodnessOfFit(
        r2,
        r2_adj,
        rmse,
        mae,
        sse,
    )


def fit(data: PlotDataSeries, settings: PlotSettings):
    model = _build_model(settings)
    x = data.x
    y = data.y

    p0 = []

    for starting_expr in settings.p0:
        try:
            param_init = eval(starting_expr)
            if param_init:
                p0.append(param_init)
        except Exception as e:
            print(f"[error] fit: {e}", file=sys.stderr)
            raise ValueError(f'Invalid expression: "{starting_expr}"')

    popt, pcov = curve_fit(model, x, y, p0=p0, method="lm")

    y_pred = model(x, *popt)
    gof = _goodness_of_fit(y, y_pred, len(p0))
    perr = np.sqrt(np.diag(pcov))

    return FitResult(
        popt=popt,
        pcov=pcov,
        model=model,
        perr=perr,
        r2=gof.r2,
        r2_adj=gof.r2_adj,
        rmse=gof.rmse,
        mae=gof.mae,
        sse=gof.sse,
    )
