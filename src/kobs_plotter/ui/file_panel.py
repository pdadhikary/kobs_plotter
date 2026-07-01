"""
File panel UI component for kobs-plotter.

Left-most panel: Excel file picker + sheet combo + X/Y/Z column combos
+ a small data-preview table showing the first rows of the selected
sheet so the user can map columns with confidence.

State is pushed into :class:`AppState`; reads (``pd.ExcelFile``,
``pd.read_excel``) are offloaded to :class:`QThread` workers so the GUI
never blocks on large files — the single biggest responsiveness fix for
this panel.
"""

from __future__ import annotations

import logging

import pandas as pd
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from kobs_plotter.ui import controller as ctrl
from kobs_plotter.ui.ui_helpers import (
    divider,
    field_label,
    mono_font,
    section_label,
)
from kobs_plotter.ui.viewmodel import AppState

log = logging.getLogger(__name__)


# Sheet-read result returned by the background worker: (sheets, error).
_SheetRead = tuple[list[str], Exception | None]
# Preview-read result: (df, error). df is None on failure.
_PreviewRead = tuple[pd.DataFrame | None, Exception | None]


class _SheetListWorker(QThread):
    """Background thread listing sheet names from an Excel file."""

    finished = Signal(list, object)  # (sheet_names, error_or_None)

    def __init__(self, path: str) -> None:
        super().__init__()
        self._path = path

    def run(self) -> None:  # noqa: D401 - QThread entry point
        try:
            xl = pd.ExcelFile(self._path)
            self.finished.emit(list(xl.sheet_names), None)
        except Exception as e:  # noqa: BLE001 - panel translates
            self.finished.emit([], e)


class _PreviewWorker(QThread):
    """Background thread reading the first ``n_rows`` of a sheet for preview."""

    finished = Signal(object, object)  # (df_or_None, error_or_None)

    def __init__(self, path: str, sheet: str, n_rows: int = 10) -> None:
        super().__init__()
        self._path = path
        self._sheet = sheet
        self._n_rows = n_rows

    def run(self) -> None:  # noqa: D401 - QThread entry point
        try:
            df = pd.read_excel(self._path, sheet_name=self._sheet, nrows=self._n_rows)
            self.finished.emit(df, None)
        except Exception as e:  # noqa: BLE001
            self.finished.emit(None, e)


class FilePanel(QWidget):
    """Data source panel: file, sheet, column mapping, preview.

    Emits ``fileLoaded`` on a successful load and ``loadFailed`` /
    ``sheetLoadFailed`` when background reads error out. The owning
    :class:`MainWindow` is responsible for surfacing those to the user
    (so this panel stays free of modal dialogs and is test-friendly).
    """

    fileLoaded = Signal(str)
    loadFailed = Signal(str, str)  # (short message, copyable detail)

    def __init__(self, state: AppState):
        super().__init__()
        self.state = state
        self.setMaximumWidth(360)
        self.is_3d = False
        self._path: str | None = None
        self._sheet_worker: _SheetListWorker | None = None
        self._preview_worker: _PreviewWorker | None = None

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(section_label("Data source"))

        # ── File path ─────────────────────────────────────────────
        layout.addWidget(field_label("File path"))
        file_row = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setReadOnly(True)
        self.file_path_input.setPlaceholderText("No file selected…")
        self.file_path_input.setToolTip("Path of the currently loaded Excel file")
        self.file_path_input.setFont(mono_font(9))
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setToolTip("Open a file dialog to pick an .xlsx file")
        self.browse_btn.setWhatsThis(
            "Pick an Excel workbook (.xlsx). Sheet names and column headers are "
            "read without loading the full dataset, so large files load quickly."
        )
        self.browse_btn.clicked.connect(self._browse)
        file_row.addWidget(self.file_path_input)
        file_row.addWidget(self.browse_btn)
        layout.addLayout(file_row)

        layout.addWidget(divider())

        # ── Sheet selector ────────────────────────────────────────
        layout.addWidget(field_label("Sheet"))
        self.sheet_combo = QComboBox()
        self.sheet_combo.setToolTip("Sheet (tab) inside the workbook to read")
        self.sheet_combo.currentTextChanged.connect(self._on_sheet_changed)
        layout.addWidget(self.sheet_combo)

        # ── Column selectors ──────────────────────────────────────
        col_row = QHBoxLayout()
        col_row.setSpacing(12)
        x_col = QVBoxLayout()
        x_col.addWidget(field_label("X column"))
        self.x_combo = QComboBox()
        self.x_combo.setToolTip("Independent variable column")
        self.x_combo.currentTextChanged.connect(self._on_col_changed)
        x_col.addWidget(self.x_combo)
        y_col = QVBoxLayout()
        y_col.addWidget(field_label("Y column"))
        self.y_combo = QComboBox()
        self.y_combo.setToolTip("Dependent variable column")
        self.y_combo.currentTextChanged.connect(self._on_col_changed)
        y_col.addWidget(self.y_combo)
        col_row.addLayout(x_col)
        col_row.addLayout(y_col)
        layout.addLayout(col_row)

        # ── Z column (3D only) ────────────────────────────────────
        self.z_col_widget = QWidget()
        z_col_layout = QVBoxLayout(self.z_col_widget)
        z_col_layout.setContentsMargins(0, 0, 0, 0)
        z_col_layout.setSpacing(4)
        z_col_layout.addWidget(field_label("Z column"))
        self.z_combo = QComboBox()
        self.z_combo.setToolTip("Second independent variable column (3D only)")
        self.z_combo.currentTextChanged.connect(self._on_col_changed)
        z_col_layout.addWidget(self.z_combo)
        self.z_col_widget.setVisible(False)
        layout.addWidget(self.z_col_widget)

        layout.addWidget(divider())

        # ── Data preview ──────────────────────────────────────────
        layout.addWidget(section_label("Data preview"))
        self.preview_label = QLabel("No sheet selected")
        self.preview_label.setStyleSheet("color: palette(mid);")
        layout.addWidget(self.preview_label)
        self.preview_table = QTableWidget(0, 0)
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.preview_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.preview_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.preview_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.preview_table.verticalHeader().setVisible(False)
        self.preview_table.setMaximumHeight(160)
        self.preview_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(self.preview_table)

        layout.addStretch()

        # Tooltips documenting the global column-mapping semantics.
        for combo, tip in [
            (self.x_combo, "X column: independent variable passed to the model"),
            (self.y_combo, "Y column: dependent variable the model fits against"),
        ]:
            combo.setWhatsThis(tip)

    # ── public entry points ───────────────────────────────────────
    def load_file(self, path: str) -> None:
        """Load an Excel file directly (used by the Recent Files menu)."""
        self._path = path
        self.file_path_input.setText(path)
        self.file_path_input.setToolTip(path)
        self.state.set_data_path(path)
        self._load_sheets(path)

    # ── mode / visibility ─────────────────────────────────────────
    def set_mode(self, is_3d: bool) -> None:
        """Toggle 3D mode: show/hide the Z column selector."""
        self.is_3d = is_3d
        self.z_col_widget.setVisible(is_3d)
        if not is_3d:
            self.state.set_z_col(None)

    # ── user actions ─────────────────────────────────────────────
    def _browse(self) -> None:
        """Open a native file dialog starting from the last-used directory."""
        start_dir = ctrl.last_directory() or ""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Excel file", start_dir, "Excel Files (*.xlsx *.xlsm)"
        )
        if not path:
            return
        ctrl.set_last_directory(path)
        self._path = path
        self.file_path_input.setText(path)
        self.file_path_input.setToolTip(path)
        self.state.set_data_path(path)
        self._load_sheets(path)

    def _load_sheets(self, path: str) -> None:
        """List sheet names in a background thread (slow for big files)."""
        self._sheet_worker = _SheetListWorker(path)
        self._sheet_worker.finished.connect(self._on_sheets_loaded)
        self._sheet_worker.start()

    def _on_sheets_loaded(self, sheet_names: list[str], error: object) -> None:
        if isinstance(error, Exception):
            self._path = None
            self.file_path_input.setText("")
            message, detail = _translate_io_error(error)
            self.loadFailed.emit(message, detail)
            return
        self.sheet_combo.clear()
        self.sheet_combo.addItems(sheet_names)
        if sheet_names:
            self.fileLoaded.emit(self._path or "")

    def _on_sheet_changed(self, sheet_name: str) -> None:
        """Populate column combos (headers only) and kick off a preview read."""
        if not self._path or not sheet_name:
            return
        self.state.set_sheet_name(sheet_name)
        try:
            df_header = pd.read_excel(self._path, sheet_name=sheet_name, nrows=0)
        except (pd.errors.ParserError, pd.errors.EmptyDataError, OSError) as e:
            self.loadFailed.emit("Sheet load error", str(e))
            for combo in (self.x_combo, self.y_combo, self.z_combo):
                combo.clear()
            return
        cols = list(df_header.columns)
        for combo in (self.x_combo, self.y_combo, self.z_combo):
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(cols)
            combo.blockSignals(False)
        if len(cols) >= 2:
            self.x_combo.setCurrentIndex(0)
            self.y_combo.setCurrentIndex(1)
        if len(cols) >= 3:
            self.z_combo.setCurrentIndex(2)
        self._refresh_preview(sheet_name)
        # Push freshly defaulted columns to the state.
        self.state.set_x_col(self.x_combo.currentText() or None)
        self.state.set_y_col(self.y_combo.currentText() or None)
        if self.is_3d:
            self.state.set_z_col(self.z_combo.currentText() or None)

    def _refresh_preview(self, sheet_name: str) -> None:
        if self._preview_worker is not None and self._preview_worker.isRunning():
            return
        self._preview_worker = _PreviewWorker(self._path or "", sheet_name, n_rows=8)
        self._preview_worker.finished.connect(self._on_preview_loaded)
        self._preview_worker.start()

    def _on_preview_loaded(self, df: object, error: object) -> None:
        if isinstance(error, Exception) or df is None:
            self.preview_label.setText("Preview unavailable")
            self.preview_table.setRowCount(0)
            self.preview_table.setColumnCount(0)
            return
        df = df  # type: ignore[assignment]
        cols = list(df.columns)
        self.preview_table.setRowCount(len(df))
        self.preview_table.setColumnCount(len(cols))
        self.preview_table.setHorizontalHeaderLabels([str(c) for c in cols])
        for r in range(len(df)):
            for c in range(len(cols)):
                item = QTableWidgetItem(str(df.iloc[r, c]))
                self.preview_table.setItem(r, c, item)
        self.preview_label.setText(
            f"Showing first {len(df)} rows × {len(cols)} columns"
        )

    def _on_col_changed(self, _text: str) -> None:
        """Push the current X/Y/Z selection to the state."""
        self.state.set_x_col(self.x_combo.currentText() or None)
        self.state.set_y_col(self.y_combo.currentText() or None)
        if self.is_3d:
            self.state.set_z_col(self.z_combo.currentText() or None)

    # ── reset ─────────────────────────────────────────────────────
    def on_reset(self) -> None:
        self._path = None
        self.file_path_input.setText("")
        self.file_path_input.setToolTip("No file selected")
        self.state.set_data_path(None)
        self.sheet_combo.clear()
        self.state.set_sheet_name(None)
        for combo in (self.x_combo, self.y_combo, self.z_combo):
            combo.clear()
        self.state.set_x_col(None)
        self.state.set_y_col(None)
        self.state.set_z_col(None)
        self.is_3d = False
        self.z_col_widget.setVisible(False)
        self.preview_table.setRowCount(0)
        self.preview_table.setColumnCount(0)
        self.preview_label.setText("No sheet selected")


def _translate_io_error(error: object) -> tuple[str, str]:
    """Map a sheet-listing I/O error to a short message + copyable detail."""
    import traceback

    detail = f"{type(error).__name__}: {error}\n\n{traceback.format_exc()}"
    if isinstance(error, FileNotFoundError):
        return "File not found", detail
    if isinstance(error, PermissionError):
        return "Permission denied", detail
    return "Could not read the Excel file", detail
