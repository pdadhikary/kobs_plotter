"""Tests for the plot window: empty-state message, empty-residuals guard,
fallback renderer, and reset."""

import numpy as np

from kobs_plotter.core.diagnostics import PlotDiagnosticType
from kobs_plotter.core.types import PlotPayload, PlotSettings
from kobs_plotter.ui.plot_window import PlotWindow, _render_qq, _render_unsupported


def _minimal_settings():
    return PlotSettings(
        plot_type=None,  # type: ignore[arg-type]
        data_path="p",
        sheet_name="s",
        x_col="x",
        y_col="y",
        z_col=None,
        x_transform=None,
        y_transform=None,
        z_transform=None,
        params=(),
        formula="x",
        p0=(),
        plot_theme="ggplot",
        title="t",
        x_label="x",
        y_label="y",
        z_label=None,
        point_color="black",
        line_color="red",
        line_style="-",
        colormap="viridis",
        x_axis_scale="linear",
        y_axis_scale="linear",
    )


def test_reset_shows_placeholder(qtbot):
    w = PlotWindow(window_title="test")
    qtbot.addWidget(w)
    w.on_reset()
    # Placeholder text should be drawn onto the figure (we can't OCR, but the
    # canvas must be non-empty after reset -> axes exist).
    assert w.figure.axes, "expected at least one axes after reset"


def test_qq_handles_empty_residuals(qtbot):
    import matplotlib.pyplot as plt

    fig = plt.figure()
    fig.add_subplot(111)
    payload = PlotPayload(
        x=np.array([]),
        y=np.array([]),
        x_fit=np.array([]),
        y_fit=np.array([]),
        result_string="",
        residuals=None,
        settings=_minimal_settings(),
        diagnostic=PlotDiagnosticType.QQ_PLOT,
    )
    # Must not raise even though residuals is None.
    _render_qq(fig, payload)
    plt.close(fig)


def test_unsupported_view_does_not_raise():
    import matplotlib.pyplot as plt

    from kobs_plotter.core.settings import PlotType

    fig = plt.figure()
    base = _minimal_settings()
    # Forge a settings object carrying a real plot_type.
    settings = PlotSettings(
        plot_type=PlotType.SCATTER_LINE,
        **{k: v for k, v in base.__dict__.items() if k != "plot_type"},
    )
    payload = PlotPayload(
        x=np.array([]),
        y=np.array([]),
        x_fit=np.array([]),
        y_fit=np.array([]),
        result_string="",
        residuals=None,
        settings=settings,
        # Use a value not in the enum so the registry misses it.
        diagnostic=None,  # type: ignore[arg-type]
    )
    _render_unsupported(fig, payload)
    plt.close(fig)


def test_plot_dispatches_scatter(qtbot):
    from kobs_plotter.core.settings import PlotType

    w = PlotWindow(window_title="scatter")
    qtbot.addWidget(w)
    settings = _minimal_settings()
    settings = PlotSettings(
        plot_type=PlotType.SCATTER_LINE,
        **{k: v for k, v in settings.__dict__.items() if k != "plot_type"},
    )
    payload = PlotPayload(
        x=np.linspace(0, 1, 10),
        y=np.linspace(0, 1, 10),
        x_fit=np.linspace(0, 1, 10),
        y_fit=np.linspace(0, 1, 10),
        result_string="r²=1",
        residuals=np.zeros(10),
        settings=settings,
        diagnostic=PlotDiagnosticType.PLOT,
    )
    w.plot(payload)
    assert w.figure.axes
    w.close()
