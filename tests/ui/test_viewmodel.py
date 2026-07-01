"""Tests for the AppState view-model: signal emission and readiness tracking."""

from kobs_plotter.core.settings import PlotType
from kobs_plotter.ui.viewmodel import AppState


def test_setters_emit_field_changed(qtbot):
    state = AppState()
    received = []
    state.fieldChanged.connect(lambda name, value: received.append(name))
    state.set_data_path("/tmp/x.xlsx")
    state.set_x_col("t")
    assert received == ["data_path", "x_col"]


def test_ready_flips_and_emits(qtbot):
    state = AppState()
    flips = []
    state.readyChanged.connect(lambda r: flips.append(r))
    assert state.is_ready() is False
    state.set_data_path("p")
    state.set_sheet_name("s")
    state.set_x_col("x")
    state.set_y_col("y")
    state.set_params(["A", "B", "k"])
    state.set_formula("B - A * exp(-k * x)")
    state.set_p0(["1.0", "1.0", "1.0"])
    assert state.is_ready() is True
    # At least one True flip recorded.
    assert True in flips


def test_3d_requires_z(qtbot):
    state = AppState()
    state.set_plot_type(PlotType.SURFACE_3D)
    state.set_data_path("p")
    state.set_sheet_name("s")
    state.set_x_col("x")
    state.set_y_col("y")
    state.set_params(["A"])
    state.set_formula("A * x")
    state.set_p0(["1.0"])
    assert state.is_ready() is False
    state.set_z_col("z")
    assert state.is_ready() is True


def test_reset_emits_ready_false(qtbot):
    state = AppState()
    state.set_data_path("p")
    state.set_sheet_name("s")
    state.set_x_col("x")
    state.set_y_col("y")
    state.set_params(["A"])
    state.set_formula("A*x")
    state.set_p0(["1"])
    assert state.is_ready()
    after = []
    state.readyChanged.connect(lambda r: after.append(r))
    state.reset()
    assert state.is_ready() is False
    assert after and after[-1] is False
