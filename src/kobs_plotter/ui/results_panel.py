"""
Results panel UI component for kobs-plotter.

Right-most panel inside a :class:`QScrollArea`. Two read-only
:class:`QTableWidget`s (Parameters and Goodness-of-fit), a rendered
LaTeX formula label at the top, and CSV / LaTeX export buttons.

Hardening relative to the previous version:

- An empty-state overlay ("Run a fit to see results") is shown before the
  first successful compute, instead of bare empty tables.
- ``FitResult.formula_latex`` is rendered as a matplotlib figure and
  shown at the top of the panel — previously computed but never shown.
- Export buttons produce CSV and LaTeX tables the user can paste into
  a manuscript; :class:`QShortcut` wires Ctrl+C to copy the selection to
  the clipboard (the README promised this but no copy slot was wired).
- Table construction is extracted to :func:`make_readonly_table`.
- ``zip(parameters, popt, perr)`` is replaced with an explicit
  length-mismatch guard so a strategy bug can't silently truncate rows.
"""

from __future__ import annotations

import io

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from kobs_plotter.core.modelling import FitResult
from kobs_plotter.ui.ui_helpers import divider, mono_font, section_label
from kobs_plotter.ui.widgets import make_readonly_table


def _render_latex_pixmap(latex: str, width: int = 320) -> object | None:
    """Render a LaTeX string to a QPixmap via an offscreen matplotlib figure.

    Returns None if matplotlib cannot typeset the formula (e.g. matplotlib's
    mathtext cannot parse a SymPy expression with custom symbols). The
    caller then falls back to a plain-text label.
    """
    import matplotlib

    matplotlib.use("Agg")  # noqa: E402 - LaTeX render uses an offscreen figure
    import matplotlib.pyplot as plt
    from PySide6.QtGui import QPixmap

    try:
        fig = plt.figure(figsize=(width / 100, 1.0))
        fig.text(0.01, 0.5, f"${latex}$", fontsize=12, verticalalignment="center")
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", transparent=True, dpi=150)
        plt.close(fig)
        pix = QPixmap()
        pix.loadFromData(buf.getvalue(), "PNG")
        return pix if not pix.isNull() else None
    except Exception:  # noqa: BLE001 - mathtext is permissive but not total
        plt.close("all")
        return None


class ResultsPanel(QWidget):
    """Tabular fit results + formula + export, hosted in a scroll area."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── Fitted formula (LaTeX render + plain fallback) ────────
        layout.addWidget(section_label("Fitted model"))
        self.formula_label = QLabel("—")
        self.formula_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formula_label.setStyleSheet(
            "padding: 8px; background: palette(window); border: 1px solid palette(mid);"
        )
        self.formula_label.setMinimumHeight(40)
        layout.addWidget(self.formula_label)
        self._formula_latex: str | None = None

        layout.addWidget(divider())

        # ── Parameters section ───────────────────────────────────
        layout.addWidget(section_label("Parameters"))
        self.params_table = make_readonly_table(["Symbol", "Value", "Std. error"])
        layout.addWidget(self.params_table)
        layout.addWidget(divider())

        # ── Goodness of fit ──────────────────────────────────────
        layout.addWidget(section_label("Goodness of fit"))
        self.gof_table = make_readonly_table(["Metric", "Value"])
        layout.addWidget(self.gof_table)

        # ── Export buttons ────────────────────────────────────────
        export_row = QHBoxLayout()
        self.copy_csv_btn = QPushButton("Copy CSV")
        self.copy_csv_btn.setToolTip("Copy the results tables to the clipboard as CSV")
        self.copy_csv_btn.clicked.connect(self._copy_csv)
        self.copy_latex_btn = QPushButton("Copy LaTeX")
        self.copy_latex_btn.setToolTip("Copy the results tables to the clipboard as a LaTeX table")
        self.copy_latex_btn.clicked.connect(self._copy_latex)
        export_row.addWidget(self.copy_csv_btn)
        export_row.addWidget(self.copy_latex_btn)
        export_row.addStretch()
        layout.addLayout(export_row)

        # Ctrl+C copies the current within-table selection to the clipboard.
        QShortcut(QKeySequence.StandardKey.Copy, self, self._copy_selection)

        self._show_placeholder()

    # ── placeholder / empty state ───────────────────────────────
    def _show_placeholder(self) -> None:
        """Reset tables to empty and show the pre-fit overlay text."""
        self.params_table.setRowCount(0)
        self.gof_table.setRowCount(0)
        self.formula_label.setText("Run a fit to see results")
        self._formula_latex = None
        self._resize_tables()

    # ── populate from a FitResult ────────────────────────────────
    def display_result(self, result: FitResult, parameters: list[str]) -> None:
        """Adapt a FitResult into table rows + formula label.

        Raises ValueError if parameter/popt/perr lengths disagree — the
        previous zip() silently truncated.
        """
        n = len(parameters)
        if not (len(result.popt) == n and len(result.perr) == n):
            raise ValueError(
                "Length mismatch: params/popt/perr must agree "
                f"(got {n}, {len(result.popt)}, {len(result.perr)})."
            )

        params = [
            (name, float(opt), float(err))
            for name, opt, err in zip(parameters, result.popt, result.perr, strict=True)
        ]
        gof = {
            "R²": float(result.r2),
            "Adj. R²": float(result.r2_adj),
            "RMSE": float(result.rmse),
            "MAE": float(result.mae),
            "SSE": float(result.sse),
        }
        self._populate(params, gof)

        # Render the fitted formula. SymPy's latex output may contain
        # symbols matplotlib's mathtext cannot display; fall back to text.
        self._formula_latex = result.formula_latex
        pix = _render_latex_pixmap(result.formula_latex)
        if pix is not None:
            self.formula_label.setText("")
            self.formula_label.setPixmap(pix)
        else:
            self.formula_label.setText(f"${result.formula_latex}$")

    def _populate(
        self,
        params: list[tuple[str, float, float]],
        gof: dict[str, float],
    ) -> None:
        """Populate both tables from already-coerced lists."""
        self.params_table.clearContents()
        self.params_table.setRowCount(len(params))
        for row, (symbol, value, err) in enumerate(params):
            self.params_table.setItem(row, 0, self._cell(symbol, mono=True))
            self.params_table.setItem(row, 1, self._cell(f"{value:.6g}"))
            self.params_table.setItem(row, 2, self._cell(f"± {err:.6g}"))

        self.gof_table.clearContents()
        self.gof_table.setRowCount(len(gof))
        for row, (metric, value) in enumerate(gof.items()):
            self.gof_table.setItem(row, 0, self._cell(metric))
            self.gof_table.setItem(row, 1, self._cell(f"{value:.6g}"))

        self._resize_tables()

    def _cell(self, text: str, mono: bool = False) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if mono:
            item.setFont(mono_font(9))
        return item

    def _resize_tables(self) -> None:
        for table in (self.params_table, self.gof_table):
            table.resizeRowsToContents()
            total = sum(table.rowHeight(i) for i in range(table.rowCount()))
            total += table.horizontalHeader().height() + 4
            table.setFixedHeight(max(total, table.horizontalHeader().height() + 4))

    # ── export / copy ────────────────────────────────────────────
    def _table_csv(self) -> str:
        lines: list[str] = []
        for table in (self.params_table, self.gof_table):
            headers = [
                table.horizontalHeaderItem(i).text() for i in range(table.columnCount())
            ]
            lines.append(",".join(headers))
            for r in range(table.rowCount()):
                row = [table.item(r, c).text() for c in range(table.columnCount())]
                lines.append(",".join(row))
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def _table_latex(self) -> str:
        out: list[str] = []
        for table in (self.params_table, self.gof_table):
            headers = [
                table.horizontalHeaderItem(i).text() for i in range(table.columnCount())
            ]
            out.append("\\begin{tabular}{" + "l" * len(headers) + "}")
            out.append(" & ".join(headers) + " \\\\")
            out.append("\\hline")
            for r in range(table.rowCount()):
                row = [table.item(r, c).text() for c in range(table.columnCount())]
                out.append(" & ".join(row) + " \\\\")
            out.append("\\end{tabular}")
            out.append("")
        return "\n".join(out).rstrip() + "\n"

    def _copy_csv(self) -> None:
        QGuiApplication.clipboard().setText(self._table_csv())

    def _copy_latex(self) -> None:
        QGuiApplication.clipboard().setText(self._table_latex())

    def _copy_selection(self) -> None:
        """Copy the current contiguous MsgBox-style selection from whichever
        table has focus, falling back to all rows if nothing is selected."""
        for table in (self.params_table, self.gof_table):
            if not table.hasFocus():
                continue
            sel = table.selectedRanges()
            if not sel:
                continue
            r = sel[0]
            rows = []
            for row in range(r.topRow(), r.bottomRow() + 1):
                cols = range(r.leftColumn(), r.rightColumn() + 1)
                rows.append("\t".join(table.item(row, c).text() for c in cols))
            QGuiApplication.clipboard().setText("\n".join(rows))
            return

    # ── reset ─────────────────────────────────────────────────────
    def on_reset(self) -> None:
        self._show_placeholder()
