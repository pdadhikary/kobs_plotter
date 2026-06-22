from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from kobs_plotter.core.modelling import FitResult
from kobs_plotter.ui.ui_helpers import section_label, divider


class ResultsPanel(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setMinimumWidth(240)
        self.setMaximumWidth(320)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        self.layout_ = QVBoxLayout(container)
        self.layout_.setSpacing(16)
        self.layout_.setContentsMargins(16, 16, 16, 16)
        self.setWidget(container)

        # ── Parameters section ───────────────────────────────
        self.layout_.addWidget(section_label("Parameters"))
        self.params_table = QTableWidget(0, 3)
        self.params_table.setHorizontalHeaderLabels(["Symbol", "Value", "Std. error"])
        self.params_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.params_table.verticalHeader().setVisible(False)
        self.params_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.params_table.setAlternatingRowColors(True)
        self.params_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.layout_.addWidget(self.params_table)

        self.layout_.addWidget(divider())

        # ── Goodness of fit section ──────────────────────────
        self.layout_.addWidget(section_label("Goodness of fit"))
        self.gof_table = QTableWidget(0, 2)
        self.gof_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.gof_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.gof_table.verticalHeader().setVisible(False)
        self.gof_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.gof_table.setAlternatingRowColors(True)
        self.gof_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.layout_.addWidget(self.gof_table)

        self.layout_.addStretch()

        self._show_placeholder()

    def _show_placeholder(self):
        """Show empty state before first computation."""
        self.params_table.setRowCount(0)
        self.gof_table.setRowCount(0)

    def _result_callback(self, result: FitResult, parameters: list[str]):
        params = []

        for param, opt, err in zip(parameters, result.popt, result.perr):
            params.append((param, opt, err))

        gof = {
            "R²": float(result.r2),
            "Adj. R²": float(result.r2_adj),
            "RMSE": float(result.rmse),
            "MAE": float(result.mae),
            "SSE": float(result.sse),
        }

        self.display(params, gof)

    def display(self, params: list[tuple[str, float, float]], gof: dict[str, float]):
        """
        params: list of (symbol, value, std_error)
        gof:    dict of metric_name -> value
                e.g. {"R²": 0.997, "Adj. R²": 0.996, "RMSE": 0.0023}
        TODO: call this from main window after compute returns a PlotResult
        """
        # Clear tables before repopulating
        self.params_table.clearContents()
        self.gof_table.clearContents()

        # Parameters table
        self.params_table.setRowCount(len(params))
        for row, (symbol, value, err) in enumerate(params):
            self.params_table.setItem(row, 0, self._cell(symbol, mono=True))
            self.params_table.setItem(row, 1, self._cell(f"{value:.6g}"))
            self.params_table.setItem(row, 2, self._cell(f"± {err:.6g}"))
        self._resize_table(self.params_table)

        # Goodness of fit table
        self.gof_table.setRowCount(len(gof))
        for row, (metric, value) in enumerate(gof.items()):
            self.gof_table.setItem(row, 0, self._cell(metric))
            self.gof_table.setItem(row, 1, self._cell(f"{value:.6g}"))
        self._resize_table(self.gof_table)

    def _cell(self, text: str, mono: bool = False) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if mono:
            item.setFont(QFont("monospace", 9))
        return item

    def _resize_table(self, table: QTableWidget):
        """Shrink table to fit its content so the scroll area works naturally."""
        table.resizeRowsToContents()
        total = sum(table.rowHeight(i) for i in range(table.rowCount()))
        total += table.horizontalHeader().height() + 4
        table.setFixedHeight(total)
