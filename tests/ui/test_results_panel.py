"""Tests for the results panel: empty state, population, export, mismatch guard."""

import numpy as np

from kobs_plotter.core.modelling import FitResult


def _fake_result(formula_latex: str = "A e^{- k x}", n: int = 3):
    return FitResult(
        formula_latex=formula_latex,
        popt=np.arange(n, dtype=float),
        pcov=np.eye(n),
        model=lambda *a: 0.0,
        perr=np.arange(n, dtype=float) + 1,
        residuals=np.zeros(5),
        r2=np.float64(0.99),
        r2_adj=np.float64(0.98),
        rmse=np.float64(0.01),
        mae=np.float64(0.02),
        sse=np.float64(0.05),
    )


def test_empty_state_before_fit(qtbot, main_window):
    rp = main_window.results_panel
    assert rp.params_table.rowCount() == 0
    assert "Run a fit" in rp.formula_label.text()


def test_display_result_populates_tables(qtbot, main_window):
    rp = main_window.results_panel
    rp.display_result(_fake_result(), ["A", "B", "k"])
    assert rp.params_table.rowCount() == 3
    assert rp.gof_table.rowCount() == 5
    assert rp.params_table.item(0, 0).text() == "A"


def test_length_mismatch_raises(qtbot, main_window):
    rp = main_window.results_panel
    import pytest

    with pytest.raises(ValueError):
        rp.display_result(_fake_result(n=3), ["A", "B"])  # 2 names, 3 popt


def test_csv_export(qtbot, main_window):
    from PySide6.QtGui import QGuiApplication

    rp = main_window.results_panel
    rp.display_result(_fake_result(), ["A", "B", "k"])
    rp._copy_csv()
    text = QGuiApplication.clipboard().text()
    assert "Symbol" in text and "Metric" in text
    assert "R²" in text


def test_latex_export(qtbot, main_window):
    from PySide6.QtGui import QGuiApplication

    rp = main_window.results_panel
    rp.display_result(_fake_result(), ["A", "B", "k"])
    rp._copy_latex()
    text = QGuiApplication.clipboard().text()
    assert "\\begin{tabular}" in text
    assert "\\end{tabular}" in text


def test_reset_clears_tables(qtbot, main_window):
    rp = main_window.results_panel
    rp.display_result(_fake_result(), ["A", "B", "k"])
    rp.on_reset()
    assert rp.params_table.rowCount() == 0
    assert rp.gof_table.rowCount() == 0
