"""
Results panel UI component for kobs-plotter.

Provides a scrollable read-only display of curve fitting results,
organised into two tables: fitted parameter values with standard errors,
and goodness-of-fit metrics. Table cells support selection and copying
via Ctrl+C for use in external tools such as Excel.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from kobs_plotter.core.modelling import FitResult
from kobs_plotter.ui.ui_helpers import divider, section_label


class ResultsPanel(QScrollArea):
    """
    Right-most panel displaying curve fitting results in tabular form.

    Contains two read-only tables:

    - **Parameters** — one row per fitted parameter showing symbol,
      optimal value, and standard error. Populated after each successful
      compute run.
    - **Goodness of fit** — one row per metric (R², Adj. R², RMSE, MAE, SSE).

    Both tables are sized to fit their content exactly so the enclosing
    scroll area handles overflow naturally without internal scrollbars.
    Cells support contiguous selection and Ctrl+C copying.

    The panel exposes _result_callback() for direct connection to the
    compute layer, and display() for programmatic population.
    """

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
        self.params_table.setSelectionMode(
            QAbstractItemView.SelectionMode.ContiguousSelection
        )
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
        self.gof_table.setSelectionMode(
            QAbstractItemView.SelectionMode.ContiguousSelection
        )
        self.gof_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.layout_.addWidget(self.gof_table)

        self.layout_.addStretch()

        self._show_placeholder()

    def _show_placeholder(self) -> None:
        """Reset both tables to an empty state before the first computation."""
        self.params_table.setRowCount(0)
        self.gof_table.setRowCount(0)

    def _result_callback(self, result: FitResult, parameters: list[str]) -> None:
        """
        Callback invoked by the compute layer after a successful fit.

        Transforms the FitResult into the format expected by display()
        and delegates rendering. Connected to the compute callable in
        MainWindow._compute().

        Args:
            result:     fit result from the modelling layer containing
                        popt, perr, and goodness-of-fit metrics.
            parameters: list of parameter symbol strings in the same order
                        as result.popt and result.perr.
        """
        params = [
            (param, opt, err)
            for param, opt, err in zip(parameters, result.popt, result.perr)
        ]
        gof = {
            "R²": float(result.r2),
            "Adj. R²": float(result.r2_adj),
            "RMSE": float(result.rmse),
            "MAE": float(result.mae),
            "SSE": float(result.sse),
        }
        self.display(params, gof)

    def display(
        self,
        params: list[tuple[str, float, float]],
        gof: dict[str, float],
    ) -> None:
        """
        Populate both tables with fit results.

        Clears existing content before repopulating so successive compute
        runs always show fresh results regardless of whether the number of
        parameters has changed.

        Args:
            params: list of (symbol, optimal_value, std_error) tuples,
                    one per fitted parameter.
            gof:    dict mapping metric name to value,
                    e.g. {"R²": 0.997, "Adj. R²": 0.996, "RMSE": 0.0023}.
        """
        self.params_table.clearContents()
        self.gof_table.clearContents()

        self.params_table.setRowCount(len(params))
        for row, (symbol, value, err) in enumerate(params):
            self.params_table.setItem(row, 0, self._cell(symbol, mono=True))
            self.params_table.setItem(row, 1, self._cell(f"{value:.6g}"))
            self.params_table.setItem(row, 2, self._cell(f"± {err:.6g}"))
        self._resize_table(self.params_table)

        self.gof_table.setRowCount(len(gof))
        for row, (metric, value) in enumerate(gof.items()):
            self.gof_table.setItem(row, 0, self._cell(metric))
            self.gof_table.setItem(row, 1, self._cell(f"{value:.6g}"))
        self._resize_table(self.gof_table)

    def _cell(self, text: str, mono: bool = False) -> QTableWidgetItem:
        """
        Create a centred, non-editable table cell.

        Args:
            text: display text for the cell.
            mono: if True, renders the text in monospace font — used
                  for parameter symbol cells.

        Returns:
            Configured QTableWidgetItem ready for insertion.
        """
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if mono:
            item.setFont(QFont("monospace", 9))
        return item

    def _resize_table(self, table: QTableWidget) -> None:
        """
        Fix the table height to exactly fit its current row content.

        Prevents QTableWidget from expanding to fill available space inside
        the scroll area, which would leave dead space between the two tables.
        Called after every display() update.

        Args:
            table: the table widget to resize.
        """
        table.resizeRowsToContents()
        total = sum(table.rowHeight(i) for i in range(table.rowCount()))
        total += table.horizontalHeader().height() + 4
        table.setFixedHeight(total)

    def on_reset(self) -> None:
        """
        Clear both tables and reset to empty state.

        Connected to the Reset button in MainWindow. Resizes both tables
        after clearing so the scroll area collapses to the correct height.
        """
        self.params_table.clearContents()
        self.params_table.setRowCount(0)
        self._resize_table(self.params_table)
        self.gof_table.clearContents()
        self.gof_table.setRowCount(0)
        self._resize_table(self.gof_table)
