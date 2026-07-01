"""Tests for the Controller: compute gating, worker dispatch, exception translation."""

import pytest

from kobs_plotter.core.diagnostics import PlotDiagnosticType
from kobs_plotter.core.service import ComputeService
from kobs_plotter.ui.controller import Controller, _translate_exception


def test_compute_when_not_ready_emits_validation_failed(qtbot):
    c = Controller(ComputeService())
    missing = []
    c.validationFailed.connect(lambda m: missing.extend(m))
    c.compute(PlotDiagnosticType.PLOT)
    # Should NOT have dispatched a worker, AND should have listed missing fields.
    assert c._worker is None
    assert len(missing) > 0


def test_compute_finishes_and_emits_result(qtbot, main_window, sample_xlsx):
    fp = main_window.file_panel
    fp.load_file(str(sample_xlsx))
    qtbot.waitUntil(lambda: fp._sheet_worker is not None and not fp._sheet_worker.isRunning(), timeout=10000)
    from PySide6.QtWidgets import QApplication
    QApplication.processEvents()
    cp = main_window.config_panel
    cp.model_combo.setCurrentText("Exponential Decay")
    QApplication.processEvents()
    c = main_window.controller
    assert c.state.is_ready()
    results = []
    c.resultReady.connect(lambda r, p, ps: results.append((r, p, ps)))
    c.compute(PlotDiagnosticType.PLOT)
    qtbot.waitUntil(lambda: c._worker is not None and not c._worker.isRunning(), timeout=15000)
    QApplication.processEvents()
    assert results, "expected a resultReady emission"
    result, payload, params = results[0]
    assert params == ["A", "B", "k"]
    assert len(result.popt) == 3


def test_concurrent_compute_invocations_ignored(qtbot, main_window, sample_xlsx):
    # Because the buttons are disabled during a run, the second invocation
    # should be ignored even if forced via compute().
    fp = main_window.file_panel
    fp.load_file(str(sample_xlsx))
    qtbot.waitUntil(lambda: fp._sheet_worker is not None and not fp._sheet_worker.isRunning(), timeout=10000)
    from PySide6.QtWidgets import QApplication
    QApplication.processEvents()
    cp = main_window.config_panel
    cp.model_combo.setCurrentText("Exponential Decay")
    QApplication.processEvents()
    c = main_window.controller
    c.compute(PlotDiagnosticType.PLOT)
    first_worker = c._worker
    # Force a second call while the first is running -> ignored.
    c.compute(PlotDiagnosticType.PLOT)
    assert c._worker is first_worker
    first_worker.wait(15000)


@pytest.mark.parametrize(
    "exc, expected_substring",
    [
        (FileNotFoundError("x"), "File not found"),
        (ValueError("bad transform"), "Invalid input"),
        (RuntimeError("no converge"), "Fit failed"),
        (RuntimeError("Optimal parameters not found"), "Fit failed"),
    ],
)
def test_translate_exception(exc, expected_substring):
    msg, detail = _translate_exception(exc)
    assert expected_substring in msg
    assert type(exc).__name__ in detail
