"""Tests for the :class:`MultivariableRegressionStrategy` (closed-form OLS)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from kobs_plotter.core.strategies.multivariable import MultivariableRegressionStrategy
from kobs_plotter.core.types import PlotSettings, PlotType


def _settings(n: int, **overrides) -> PlotSettings:
    x_cols = [f"x{i}" for i in range(1, n + 1)]
    n_params = n + 1
    return PlotSettings(
        plot_type=PlotType.MULTIVARIABLE_REGRESSION,
        data_path="/dev/null",
        sheet_name="S",
        x_col=x_cols[0],
        y_col="y",
        z_col=None,
        x_transform=None,
        y_transform=None,
        z_transform=None,
        params=tuple(f"B_{i}" for i in range(n_params)),
        formula="B_0 + " + " + ".join(f"B_{i} * x_{i}" for i in range(1, n + 1)),
        p0=tuple(["1.0"] * n_params),
        plot_theme="ggplot",
        title=None,
        x_label=None,
        y_label=None,
        z_label=None,
        x_axis_scale="linear",
        y_axis_scale="linear",
        point_color="black",
        line_color="red",
        line_style="-",
        colormap="viridis",
        x_cols=tuple(x_cols),
        x_transforms=(None,) * n,
    )


def _synthetic_df(n: int, samples: int = 50, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    # True coefficients: B_0 = 1.0, B_i = i (so B_1=1, B_2=2, ...)
    X = rng.uniform(-3, 3, size=(samples, n))
    true_b = np.array([1.0] + [float(i) for i in range(1, n + 1)])
    y = np.hstack([np.ones((samples, 1)), X]) @ true_b
    data = {f"x{i+1}": X[:, i] for i in range(n)}
    data["y"] = y
    return pd.DataFrame(data)


def test_load_series_extracts_matrix_and_observed():
    strat = MultivariableRegressionStrategy()
    df = _synthetic_df(n=3, samples=20)
    settings = _settings(n=3)
    series = strat.load_series(settings, df)
    assert series.X_matrix is not None
    assert series.X_matrix.shape == (20, 3)
    assert series.y.shape == (20,)
    # x / z slots mirror the first / second independent column.
    np.testing.assert_allclose(series.x, series.X_matrix[:, 0])
    z = series.z
    assert z is not None
    np.testing.assert_allclose(z, series.X_matrix[:, 1])


def test_build_model_predicts_linear_combination():
    strat = MultivariableRegressionStrategy()
    settings = _settings(n=2)
    model, expr = strat.build_model(settings)
    X = np.array([[1.0, 2.0], [3.0, 4.0]])
    pred = model(X, 0.5, 1.0, 2.0)  # B_0=0.5, B_1=1, B_2=2
    np.testing.assert_allclose(pred, [0.5 + 1 * 1 + 2 * 2, 0.5 + 1 * 3 + 2 * 4])
    # SymPy expression should reference B_0 and the X symbols.
    assert "B_0" in str(expr)


def test_run_fit_recovers_exact_coefficients():
    strat = MultivariableRegressionStrategy()
    for n in (1, 2, 3):
        df = _synthetic_df(n=n, samples=80)
        settings = _settings(n=n)
        model, _expr = strat.build_model(settings)
        series = strat.load_series(settings, df)
        popt, _pcov, observed, predicted = strat.run_fit(model, series, [1.0] * (n + 1))
        # True coefficients were B_0=1, B_i=i.
        expected = np.array([1.0] + [float(i) for i in range(1, n + 1)])
        np.testing.assert_allclose(popt, expected, atol=1e-9)
        np.testing.assert_allclose(observed, predicted, atol=1e-9)


def test_prepare_payload_1d_uses_scatter_shape():
    strat = MultivariableRegressionStrategy()
    df = _synthetic_df(n=1)
    settings = _settings(n=1)
    model, expr = strat.build_model(settings)
    series = strat.load_series(settings, df)
    popt, pcov, _obs, _pred = strat.run_fit(model, series, [1.0, 1.0])

    from kobs_plotter.core.modelling import FitResult, _goodness_of_fit
    gof = _goodness_of_fit(series.y, model(series.X_matrix, *popt), len(popt))
    result = FitResult(
        formula_latex="",
        popt=popt, pcov=pcov, model=model,
        perr=np.sqrt(np.diag(pcov)),
        residuals=gof.residuals, r2=gof.r2, r2_adj=gof.r2_adj,
        rmse=gof.rmse, mae=gof.mae, sse=gof.sse,
    )
    payload = strat.prepare_payload(series, result, settings)

    assert len(payload.x_cols) == 1
    assert payload.conf_lower is not None and payload.conf_upper is not None
    assert payload.x_fit.shape == (1_000,)
    predicted = payload.predicted
    assert predicted is not None
    assert predicted.shape == series.y.shape


def test_prepare_payload_2d_uses_plane_shape():
    strat = MultivariableRegressionStrategy()
    df = _synthetic_df(n=2)
    settings = _settings(n=2)
    model, _ = strat.build_model(settings)
    series = strat.load_series(settings, df)
    popt, pcov, _, _ = strat.run_fit(model, series, [1.0, 1.0, 1.0])

    from kobs_plotter.core.modelling import FitResult, _goodness_of_fit
    gof = _goodness_of_fit(series.y, model(series.X_matrix, *popt), len(popt))
    result = FitResult(
        formula_latex="",
        popt=popt, pcov=pcov, model=model,
        perr=np.sqrt(np.diag(pcov)),
        residuals=gof.residuals, r2=gof.r2, r2_adj=gof.r2_adj,
        rmse=gof.rmse, mae=gof.mae, sse=gof.sse,
    )
    payload = strat.prepare_payload(series, result, settings)

    assert len(payload.x_cols) == 2
    assert payload.x_fit.shape == (60, 60)
    z_fit = payload.z_fit
    assert z_fit is not None
    assert z_fit.shape == (60, 60)


def test_prepare_payload_3d_uses_actual_vs_predicted():
    strat = MultivariableRegressionStrategy()
    df = _synthetic_df(n=3)
    settings = _settings(n=3)
    model, _ = strat.build_model(settings)
    series = strat.load_series(settings, df)
    popt, pcov, _, _ = strat.run_fit(model, series, [1.0] * 4)

    from kobs_plotter.core.modelling import FitResult, _goodness_of_fit
    gof = _goodness_of_fit(series.y, model(series.X_matrix, *popt), len(popt))
    result = FitResult(
        formula_latex="",
        popt=popt, pcov=pcov, model=model,
        perr=np.sqrt(np.diag(pcov)),
        residuals=gof.residuals, r2=gof.r2, r2_adj=gof.r2_adj,
        rmse=gof.rmse, mae=gof.mae, sse=gof.sse,
    )
    payload = strat.prepare_payload(series, result, settings)

    assert len(payload.x_cols) == 3
    # Actual vs Predicted: x is observed, y is predicted.
    assert payload.x.shape == series.y.shape
    assert payload.y.shape == series.y.shape
    assert payload.conf_lower is None and payload.conf_upper is None
