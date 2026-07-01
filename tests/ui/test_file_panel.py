"""Tests for the file panel: async sheet load, column defaults, preview."""


from kobs_plotter.ui.controller import recent_files, settings


def test_load_file_populates_sheets(qtbot, main_window, sample_xlsx):
    fp = main_window.file_panel
    fp.load_file(str(sample_xlsx))
    if fp._sheet_worker is not None:
        qtbot.waitUntil(lambda: fp._sheet_worker is not None and not fp._sheet_worker.isRunning(), timeout=10000)
    from PySide6.QtWidgets import QApplication
    QApplication.processEvents()
    assert fp.sheet_combo.count() == 1
    assert fp.sheet_combo.currentText() == "Sheet1"


def test_column_defaults_xy(qtbot, main_window, sample_xlsx):
    fp = main_window.file_panel
    fp.load_file(str(sample_xlsx))
    if fp._sheet_worker is not None:
        qtbot.waitUntil(lambda: not fp._sheet_worker.isRunning(), timeout=10000)
    from PySide6.QtWidgets import QApplication
    QApplication.processEvents()
    # On a 2-column sheet, X defaults to col 0 and Y to col 1.
    assert fp.x_combo.count() == 2
    assert fp.x_combo.currentIndex() == 0
    assert fp.y_combo.currentIndex() == 1


def test_preview_table_populated(qtbot, main_window, sample_xlsx):
    fp = main_window.file_panel
    fp.load_file(str(sample_xlsx))
    qtbot.waitUntil(lambda: not fp._sheet_worker.isRunning(), timeout=10000)
    from PySide6.QtWidgets import QApplication
    QApplication.processEvents()
    fp.sheet_combo.setCurrentIndex(0)
    if fp._preview_worker is not None:
        qtbot.waitUntil(lambda: not fp._preview_worker.isRunning(), timeout=10000)
    QApplication.processEvents()
    assert fp.preview_table.columnCount() == 2
    assert fp.preview_table.rowCount() > 0


def test_load_failure_clears(qtbot, main_window, tmp_path, monkeypatch):
    # Avoid the modal error dialog blocking the offscreen test session.
    monkeypatch.setattr("kobs_plotter.ui.main_window.show_copyable_error", lambda *a, **kw: None)
    fp = main_window.file_panel
    # Non-existent file -> worker emits error path -> sheet list stays empty.
    fp.load_file(str(tmp_path / "nope.xlsx"))
    qtbot.waitUntil(lambda: fp._sheet_worker is not None and not fp._sheet_worker.isRunning(), timeout=10000)
    from PySide6.QtWidgets import QApplication
    QApplication.processEvents()
    assert fp.sheet_combo.count() == 0


def test_recent_file_recorded(qtbot, main_window, sample_xlsx):
    # Clear settings first to make the test deterministic.
    settings().remove("recentFiles")
    fp = main_window.file_panel
    fp.load_file(str(sample_xlsx))
    qtbot.waitUntil(lambda: not fp._sheet_worker.isRunning(), timeout=10000)
    from PySide6.QtWidgets import QApplication
    QApplication.processEvents()
    files = recent_files()
    assert str(sample_xlsx) in files
