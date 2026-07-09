"""End-to-end MainWindow tests: button enable gating, menu, compute run."""


from kobs_plotter.core.diagnostics import PlotDiagnosticType


def test_compute_disabled_in_empty_state(qtbot, main_window):
    assert main_window.compute_btn.isEnabled() is False
    assert main_window.qq_btn.isEnabled() is False
    assert main_window.residual_btn.isEnabled() is False
    assert main_window.reset_btn.isEnabled() is True


def test_compute_enables_when_ready(qtbot, main_window, sample_xlsx):
    fp = main_window.file_panel
    fp.load_file(str(sample_xlsx))
    qtbot.waitUntil(lambda: fp._sheet_worker is not None and not fp._sheet_worker.isRunning(), timeout=10000)
    from PySide6.QtWidgets import QApplication
    QApplication.processEvents()
    cp = main_window.config_panel
    cp.model_combo.setCurrentText("Exponential Decay")
    QApplication.processEvents()
    assert main_window.compute_btn.isEnabled() is True


def test_menubar_has_recent_files(qtbot, main_window):
    mb = main_window.menuBar()
    actions = [a.text() for a in mb.actions()]
    assert "&File" in actions
    assert "&Plot" in actions
    assert "&Help" in actions


def test_plot_type_combo_carries_enum(qtbot, main_window):
    from kobs_plotter.core.settings import PlotType

    assert main_window.plot_type_combo.currentData() is PlotType.SCATTER_LINE
    main_window.plot_type_combo.setCurrentIndex(1)
    assert main_window.plot_type_combo.currentData() is PlotType.SURFACE_3D
    # Mode propagation: Z column visible on file panel in 3D.
    assert main_window.file_panel.mode is PlotType.SURFACE_3D
    assert main_window.file_panel.z_col_widget.isHidden() is False


def test_plot_type_combo_has_multivar(qtbot, main_window):
    from kobs_plotter.core.settings import PlotType

    assert main_window.plot_type_combo.count() == 3
    assert main_window.plot_type_combo.itemData(2) is PlotType.MULTIVARIABLE_REGRESSION
    main_window.plot_type_combo.setCurrentIndex(2)
    assert main_window.file_panel.mode is PlotType.MULTIVARIABLE_REGRESSION
    assert main_window.file_panel.multivar_widget.isHidden() is False
    assert main_window.file_panel.col_widget.isHidden() is True
    assert main_window.config_panel.mv_widget.isHidden() is False
    assert main_window.config_panel.model_section_widget.isHidden() is True


def test_full_compute_run_populates_results(qtbot, main_window, sample_xlsx):
    fp = main_window.file_panel
    fp.load_file(str(sample_xlsx))
    qtbot.waitUntil(lambda: fp._sheet_worker is not None and not fp._sheet_worker.isRunning(), timeout=10000)
    from PySide6.QtWidgets import QApplication
    QApplication.processEvents()
    main_window.config_panel.model_combo.setCurrentText("Exponential Decay")
    QApplication.processEvents()
    main_window.controller.compute(PlotDiagnosticType.PLOT)
    qtbot.waitUntil(
        lambda: main_window.controller._worker is not None
        and not main_window.controller._worker.isRunning(),
        timeout=15000,
    )
    QApplication.processEvents()
    assert main_window.results_panel.params_table.rowCount() == 3
    assert "R²" in [main_window.results_panel.gof_table.item(i, 0).text() for i in range(5)]
