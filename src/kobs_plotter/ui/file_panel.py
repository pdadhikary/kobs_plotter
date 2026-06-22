from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QComboBox,
)
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFileDialog
import pandas as pd

from kobs_plotter.ui.ui_helpers import section_label, field_label, divider
from kobs_plotter.core.settings import PlotSettingsBuilder


class FilePanel(QWidget):
    def __init__(self, settings_builder: PlotSettingsBuilder):
        super().__init__()
        self.setMaximumWidth(320)
        self.settings_builder = settings_builder

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

        layout.addStretch()

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Excel file", "", "Excel Files (*.xlsx *.xls)"
        )
        if path:
            self.file_path_input.setText(path)
            self.settings_builder.set_data_path(path)
            self._load_sheets(path)

    def _load_sheets(self, path: str):
        try:
            xl = pd.ExcelFile(path)
            self.sheet_combo.clear()
            self.sheet_combo.addItems(xl.sheet_names)
        except Exception as e:
            self.file_path_input.setText(f"Error: {e}")

    def _on_sheet_changed(self, sheet_name: str):
        path = self.file_path_input.text()
        if not path or not sheet_name:
            return
        try:
            # Read only the first row to get column names — no data loaded
            df_header = pd.read_excel(path, sheet_name=sheet_name, nrows=0)
            cols = list(df_header.columns)
            for combo in (self.x_combo, self.y_combo):
                combo.clear()
                combo.addItems(cols)
            if len(cols) >= 2:
                self.y_combo.setCurrentIndex(1)
            self.settings_builder.set_sheet_name(sheet_name)
        except Exception as e:
            print(f"Sheet load error: {e}")
