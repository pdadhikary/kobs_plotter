"""
Strategy for multivariable linear regression.

The model is fixed: ``Y = B_0 + B_1*X_1 + B_2*X_2 + ... + B_n*X_n``.
Unlike the scatter-line and surface-3D strategies, the model is strictly
linear in its parameters, so the fit is solved in closed form via
``numpy.linalg.lstsq`` (ordinary least squares). There are no initial
parameter guesses to supply and no iterative convergence to fail.

Convention for ``PlotDataSeries`` reuse in this strategy:

* ``X_matrix`` is the ``(m, n)`` array of transformed independent columns.
* ``x``     is the first independent column  (``X_matrix[:, 0]``).
* ``y``     is the dependent (observed) array — the series we fit against.
* ``z``     is the second independent column  (``X_matrix[:, 1]``) when
  there are >=2 predictors, else ``None``. Naming a column "Z" here is a
  plotting convenience so the existing 3D scatter renderer can read
  ``(payload.x, payload.y, payload.z)`` as ``(X_1, X_2, Y_observed)``.

The active plot geometry depends on the number of independent columns:

* 1 column  -> 2D scatter ``(X_1, Y)`` with the fitted regression line
  and a pointwise confidence band (same visual as ScatterLine).
* 2 columns -> 3D scatter ``(X_1, X_2, Y)`` with a flat regression-plane mesh
  covering the (X_1, X_2) domain.
* 3+ columns -> 2D Actual vs Predicted scatter with a ``y = x`` reference line
  and fixed axis labels ("Actual" / "Predicted").
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import numpy as np

from kobs_plotter.core.diagnostics import PlotDiagnosticType
from kobs_plotter.core.strategies.base import PlotStrategy
from kobs_plotter.core.transforms import apply_transform
from kobs_plotter.core.types import (
    PlotDataSeries,
    PlotPayload,
    PlotSettings,
    PlotType,
)

if TYPE_CHECKING:
    import pandas as pd
    from sympy import Basic

    from kobs_plotter.core.modelling import FitResult


def _design_matrix(X: np.ndarray) -> np.ndarray:
    """Prepend a column of ones to ``X`` to give the OLS design matrix."""
    m = X.shape[0]
    return np.hstack([np.ones((m, 1)), X])


class MultivariableRegressionStrategy(PlotStrategy):
    """Strategy for ``PlotType.MULTIVARIABLE_REGRESSION`` (OLS fitting)."""

    plot_type = PlotType.MULTIVARIABLE_REGRESSION
    dependent_label = "y"

    # ── series extraction ──────────────────────────────────────────
    def load_series(self, settings: PlotSettings, df: pd.DataFrame) -> PlotDataSeries:
        cols = list(settings.x_cols)
        sub = df[cols + [settings.y_col]].dropna()
        if len(sub) == 0:
            raise ValueError(
                "No rows remain after dropping NaN values across the selected columns."
            )

        X_raw = np.asarray(sub.loc[:, cols], dtype=float)
        y = np.asarray(sub.loc[:, settings.y_col], dtype=float)

        # Transform the independent columns. The transform namespace exposes
        # the current column as `x` (so `np.log(x)` works for any column),
        # plus the dependent `y` for data-driven transforms, plus `np`.
        n = len(cols)
        transforms = list(settings.x_transforms) if settings.x_transforms else []
        if len(transforms) < n:
            transforms = transforms + [None] * (n - len(transforms))

        transformed: list[np.ndarray] = []
        for i in range(n):
            ns = {"x": X_raw[:, i], "y": y, "z": None, "np": np}
            transformed.append(apply_transform(transforms[i], ns, "x"))
        X_matrix = np.column_stack(transformed) if transformed else np.empty((len(y), 0))

        # Transform the dependent column.
        ns_y = {"x": y, "y": y, "z": None, "np": np}
        y_prime = apply_transform(settings.y_transform, ns_y, "y")

        x_first = X_matrix[:, 0] if X_matrix.shape[1] >= 1 else np.array([])
        x_second = X_matrix[:, 1] if X_matrix.shape[1] >= 2 else None

        return PlotDataSeries(
            x=x_first,
            y=y_prime,
            z=x_second,
            X_matrix=X_matrix,
        )

    # ── model construction ────────────────────────────────────────
    def build_model(self, settings: PlotSettings) -> tuple[Callable, Basic]:
        """Build a callable linear model and a SymPy expression for display.

        The callable takes ``(X, *params)`` where ``X`` is an ``(m, n)`` array
        of the independent columns (without intercept) and ``params`` are the
        ``(n+1)`` coefficients ``[B_0, B_1, ..., B_n]``.
        """
        from sympy import symbols, sympify

        n = len(settings.x_cols)
        x_syms = symbols([f"X_{i}" for i in range(1, n + 1)])
        b_syms = symbols([f"B_{i}" for i in range(n + 1)])
        if n == 1:
            expr = b_syms[0] + b_syms[1] * x_syms[0]
        else:
            expr = b_syms[0] + sum(b_syms[i + 1] * x_syms[i] for i in range(n))

        def model(X: np.ndarray, *params: float) -> np.ndarray:
            X = np.atleast_2d(np.asarray(X, dtype=float))
            coeffs = np.asarray(params, dtype=float)
            return coeffs[0] + X @ coeffs[1:]

        return model, sympify(expr)

    # ── fitting ─────────────────────────────────────────────────────
    def run_fit(
        self,
        model: Callable,  # noqa: ARG002 - lstsq does not use the callable
        data: PlotDataSeries,
        p0: list[float],  # noqa: ARG002 - OLS needs no initial guess
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        X = data.X_matrix
        if X is None:
            raise ValueError("Multivariable regression requires an X matrix.")
        observed = data.y
        A = _design_matrix(X)
        popt, _residuals, _rank, _sv = np.linalg.lstsq(A, observed, rcond=None)
        predicted = A @ popt

        m, k = A.shape
        dof = m - k
        residuals = observed - predicted
        sigma2 = float(np.sum(residuals**2) / dof) if dof > 0 else 0.0
        try:
            cov = sigma2 * np.linalg.inv(A.T @ A)
        except np.linalg.LinAlgError:
            cov = np.full((k, k), np.nan)

        return popt, cov, observed, predicted

    # ── payload assembly ────────────────────────────────────────────
    def prepare_payload(
        self,
        data: PlotDataSeries,
        result: FitResult,
        settings: PlotSettings,
    ) -> PlotPayload:
        result_string = self.format_result_string(settings, result)
        X = data.X_matrix
        if X is None:
            raise ValueError("Multivariable regression requires an X matrix.")
        observed = data.y
        predicted = result.model(X, *result.popt)
        n = len(settings.x_cols)

        if n == 1:
            # 2D scatter (X_1, Y) + fitted line + pointwise confidence band.
            x1 = X[:, 0]
            x_fit = np.linspace(float(x1.min()), float(x1.max()), 1_000)
            y_fit = result.model(x_fit.reshape(-1, 1), *result.popt)
            conf_lower, conf_upper = _confidence_band_1d(x1, observed, x_fit, result)
            return PlotPayload(
                x=x1,
                y=observed,
                x_fit=x_fit,
                y_fit=y_fit,
                result_string=result_string,
                residuals=result.residuals,
                settings=settings,
                diagnostic=PlotDiagnosticType.PLOT,
                conf_lower=conf_lower,
                conf_upper=conf_upper,
                predicted=predicted,
                x_cols=tuple(settings.x_cols),
            )

        if n == 2:
            # 3D scatter (X_1, X_2, Y) + flat regression plane.
            x1 = X[:, 0]
            x2 = X[:, 1]
            g1 = np.linspace(float(x1.min()), float(x1.max()), 60)
            g2 = np.linspace(float(x2.min()), float(x2.max()), 60)
            x_fit, y_fit = np.meshgrid(g1, g2)
            plane_in = np.column_stack([x_fit.ravel(), y_fit.ravel()])
            z_fit = result.model(plane_in, *result.popt).reshape(x_fit.shape)
            return PlotPayload(
                x=x1,
                y=x2,
                z=observed,
                x_fit=x_fit,
                y_fit=y_fit,
                z_fit=z_fit,
                result_string=result_string,
                residuals=result.residuals,
                settings=settings,
                diagnostic=PlotDiagnosticType.PLOT,
                predicted=predicted,
                x_cols=tuple(settings.x_cols),
            )

        # 3+ independent columns: Actual vs Predicted.
        return PlotPayload(
            x=observed,
            y=predicted,
            x_fit=np.array([]),
            y_fit=np.array([]),
            result_string=result_string,
            residuals=result.residuals,
            settings=settings,
            diagnostic=PlotDiagnosticType.PLOT,
            predicted=predicted,
            x_cols=tuple(settings.x_cols),
        )


def _confidence_band_1d(
    x: np.ndarray,
    y: np.ndarray,
    x_fit: np.ndarray,
    result: FitResult,
    confidence: float = 0.99,
) -> tuple[np.ndarray, np.ndarray]:
    """Pointwise confidence band for a simple linear regression fit.

    Uses the closed form for OLS prediction variance::

        var(y_hat(x*)) = sigma^2 * (1/m + (x* - x_mean)^2 / S_xx)

    where ``S_xx = sum((x_i - x_mean)^2)`` and ``sigma^2 = RSS / (m - 2)``.
    """
    from scipy import stats

    m = len(x)
    x_mean = float(np.mean(x))
    sxx = float(np.sum((x - x_mean) ** 2))
    residuals = y - result.model(x.reshape(-1, 1), *result.popt)
    dof = m - 2
    sigma2 = float(np.sum(residuals**2) / dof) if dof > 0 else 0.0

    t_val = stats.t.ppf((1 + confidence) / 2, dof)
    var_fit = sigma2 * (1.0 / m + (x_fit - x_mean) ** 2 / sxx) if sxx > 0 else np.zeros_like(x_fit)
    se_fit = np.sqrt(np.maximum(var_fit, 0.0))
    y_fit = result.model(x_fit.reshape(-1, 1), *result.popt)
    lower = y_fit - t_val * se_fit
    upper = y_fit + t_val * se_fit
    return lower, upper
