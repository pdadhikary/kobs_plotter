"""
File panel UI component for kobs-plotter.

Provides controls for selecting an Excel file, choosing a sheet,
and mapping columns to the X, Y, and Z (3D only) axes. Updates the
shared PlotSettingsBuilder as the user makes selections.
"""

import pandas as pd
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from kobs_plotter.core.settings import PlotSettingsBuilder
from kobs_plotter.ui.ui_helpers import divider, field_label, section_label, show_error


class FilePanel(QWidget):
    """
    Left-most panel handling data source selection.

    Allows the user to browse for an Excel file, select a sheet from
    a dropdown populated on file load, and map sheet columns to the
    X, Y, and Z (3D only) axes. Column headers are read without loading
    data to keep the UI responsive for large files.

    The Z column selector is hidden by default and shown when the user
    switches to Surface 3D plot type via set_mode().

    Args:
        settings_builder: shared builder instance updated as the user
                          interacts with the panel widgets.
    """

    def __init__(self, settings_builder: PlotSettingsBuilder):
        super().__init__()
        self.setMaximumWidth(320)
        self.settings_builder = settings_builder
        self.is_3d = False

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(section_label("Data source"))

        # ── File path ────────────────────────────────────────
        layout.addWidget(field_label("File path"))
        file_row = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setReadOnly(True)
        self.file_path_input.setPlaceholderText("No file selected…")
        self.file_path_input.setFont(QFont("monospace", 9))
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setFixedWidth(80)
        self.browse_btn.clicked.connect(self._browse)
        file_row.addWidget(self.file_path_input)
        file_row.addWidget(self.browse_btn)
        layout.addLayout(file_row)

        layout.addWidget(divider())

        # ── Sheet selector ───────────────────────────────────
        layout.addWidget(field_label("Sheet"))
        self.sheet_combo = QComboBox()
        self.sheet_combo.currentTextChanged.connect(self._on_sheet_changed)
        layout.addWidget(self.sheet_combo)

        # ── Column selectors ─────────────────────────────────
        col_row = QHBoxLayout()
        col_row.setSpacing(12)

        x_col = QVBoxLayout()
        x_col.addWidget(field_label("X column"))
        self.x_combo = QComboBox()
        self.x_combo.currentTextChanged.connect(self.settings_builder.set_x_col)
        x_col.addWidget(self.x_combo)

        y_col = QVBoxLayout()
        y_col.addWidget(field_label("Y column"))
        self.y_combo = QComboBox()
        self.y_combo.currentTextChanged.connect(self.settings_builder.set_y_col)
        y_col.addWidget(self.y_combo)

        col_row.addLayout(x_col)
        col_row.addLayout(y_col)
        layout.addLayout(col_row)

        # ── Z column (3D only, hidden by default) ────────────
        self.z_col_widget = QWidget()
        z_col_layout = QVBoxLayout(self.z_col_widget)
        z_col_layout.setContentsMargins(0, 0, 0, 0)
        z_col_layout.setSpacing(4)
        z_col_layout.addWidget(field_label("Z column"))
        self.z_combo = QComboBox()
        self.z_combo.currentTextChanged.connect(self.settings_builder.set_z_col)
        z_col_layout.addWidget(self.z_combo)
        self.z_col_widget.setVisible(False)
        layout.addWidget(self.z_col_widget)

        layout.addStretch()

    def set_mode(self, is_3d: bool) -> None:
        """
        Switch the panel between 2D and 3D mode.

        Shows or hides the Z column selector and clears the Z column
        from the settings builder when switching back to 2D.

        Args:
            is_3d: True to show Z column selector, False to hide it.
        """
        self.is_3d = is_3d
        self.z_col_widget.setVisible(is_3d)
        if not is_3d:
            self.settings_builder.set_z_col(None)

    def _browse(self) -> None:
        """
        Open a native file dialog and load the selected Excel file.

        Updates the file path display, pushes the path to the settings
        builder, and triggers sheet loading.
        """
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Excel file", "", "Excel Files (*.xlsx *.xls)"
        )
        if path:
            self.file_path_input.setText(path)
            self.settings_builder.set_data_path(path)
            self._load_sheets(path)

    def _load_sheets(self, path: str) -> None:
        """
        Populate the sheet dropdown from the given Excel file.

        Only reads sheet names — no data is loaded at this stage.

        Args:
            path: absolute path to the Excel file.
        """
        try:
            xl = pd.ExcelFile(path)
            self.sheet_combo.clear()
            self.sheet_combo.addItems(xl.sheet_names)
        except Exception as e:
            show_error(self, "I/O Error", str(e))

    def _on_sheet_changed(self, sheet_name: str) -> None:
        """
        Handle sheet selection change.

        Reads only the header row (nrows=0) to populate the column
        dropdowns without loading the full dataset. Sets sensible
        default column selections (index 1 for Y, index 2 for Z).

        Args:
            sheet_name: name of the newly selected sheet.
        """
        path = self.file_path_input.text()
        if not path or not sheet_name:
            return
        try:
            df_header = pd.read_excel(path, sheet_name=sheet_name, nrows=0)
            cols = list(df_header.columns)
            for combo in (self.x_combo, self.y_combo, self.z_combo):
                combo.clear()
                combo.addItems(cols)
            if len(cols) >= 2:
                self.y_combo.setCurrentIndex(1)
            if len(cols) >= 3:
                self.z_combo.setCurrentIndex(2)
            self.settings_builder.set_sheet_name(sheet_name)
        except Exception as e:
            show_error(self, "Sheet load error", str(e))

    def on_reset(self) -> None:
        """
        Reset all panel inputs to their default empty state.

        Clears the file path, sheet dropdown, and all column selectors,
        and pushes None for all corresponding fields to the settings builder.
        Also hides the Z column widget and resets the 3D mode flag.
        """
        self.file_path_input.setText("")
        self.settings_builder.set_data_path(None)
        self.sheet_combo.clear()
        self.settings_builder.set_sheet_name(None)
        self.x_combo.clear()
        self.settings_builder.set_x_col(None)
        self.y_combo.clear()
        self.settings_builder.set_y_col(None)
        self.z_combo.clear()
        self.settings_builder.set_z_col(None)
        self.is_3d = False
        self.z_col_widget.setVisible(False)
