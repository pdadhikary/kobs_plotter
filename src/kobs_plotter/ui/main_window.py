"""
Main application window for kobs-plotter.

Composes all UI panels into a single window and wires the
:class:`Controller` (compute pipeline, plot windows, settings
persistence) to the views via Qt signals.

Key UI/UX features relative to the previous version:

- Panels live in a :class:`QSplitter` (resizeable, persisted) instead of a
  fixed :class:`QHBoxLayout`; each panel is wrapped in a
  :class:`QScrollArea` so it adapts to small screens.
- :class:`QStatusBar` carries a :class:`QProgressBar` that animates while
  a compute run is in flight; the compute buttons disable/re-enable
  around the run so the GUI never appears hung.
- :class:`QMenuBar` with File (Recent Files, Quit), Plot (Generate, Q-Q,
  Residual, Reset), and Help (About, Citation) menus plus keyboard
  shortcuts.
- Plot type combo now carries :class:`PlotType` in ``setItemData`` and is
  read via ``currentData()`` — adding a third plot type no longer breaks
  silently.
- Window geometry and splitter state are saved/restored via
  :class:`QSettings`; the window opens maximised by default on first run.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from kobs_plotter.core.diagnostics import PlotDiagnosticType
from kobs_plotter.core.service import ComputeService
from kobs_plotter.core.settings import PlotType
from kobs_plotter.ui import controller as ctrl
from kobs_plotter.ui.config_panel import ConfigPanel
from kobs_plotter.ui.controller import Controller
from kobs_plotter.ui.file_panel import FilePanel
from kobs_plotter.ui.plot_panel import PlotPanel
from kobs_plotter.ui.resettable import ResetCoordinator
from kobs_plotter.ui.results_panel import ResultsPanel
from kobs_plotter.ui.ui_helpers import show_copyable_error, show_warning

log = logging.getLogger(__name__)

_ORG = "kobs-plotter"
_APP = "kobs-plotter"

# Citation text shown in the About dialog. Kept in sync with README.md /
# CITATION.cff. Update on every release.
_CITATION = (
    "Adhikary, P. D. (2026). Kobs-Plotter (Version 0.5.0) [Software]. "
    "GitHub. https://github.com/pdadhikary/kobs_plotter"
)
_ABOUT_TEXT = (
    "<h3>Kobs-Plotter 0.5.0</h3>"
    "<p>A desktop application for scientific nonlinear curve fitting "
    "and publication-ready visualization.</p>"
    "<p>Built with PySide6, NumPy, Pandas, SciPy, Matplotlib, and SymPy.</p>"
)


class MainWindow(QMainWindow):
    """Root application window — composes panels and wires the controller."""

    def __init__(self, compute_service: ComputeService):
        super().__init__()
        self.setWindowTitle("K Observes Plotter")
        self.setMinimumSize(960, 600)
        self.controller = Controller(compute_service)

        # The single plot-type combo carries the PlotType enum in itemData;
        # reading via currentData() is type-safe against future additions.
        self._plot_types: list[PlotType] = [
            PlotType.SCATTER_LINE,
            PlotType.SURFACE_3D,
        ]

        self.reset_coordinator = ResetCoordinator()

        # Floating plot windows keyed by diagnostic so render dispatch is a
        # plain dict lookup — no more getattr(s) against attribute names.
        self._plot_windows = self.controller.make_plot_windows(self)
        for w in self._plot_windows.values():
            self.reset_coordinator.register(w)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Splitter row of scrolled panels ──────────────────────
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)

        # Build the real panels (each has an on_reset()) and register them
        # with the reset coordinator. We then wrap each in a QScrollArea
        # for the splitter; the real panel is kept on self for signal/Slot.
        self.file_panel: FilePanel = self.reset_coordinator.register(
            FilePanel(self.controller.state)
        )
        self.config_panel: ConfigPanel = self.reset_coordinator.register(
            ConfigPanel(self.controller.state)
        )
        self.plot_panel: PlotPanel = self.reset_coordinator.register(
            PlotPanel(self.controller.state)
        )
        self.results_panel: ResultsPanel = self.reset_coordinator.register(ResultsPanel())

        self.splitter.addWidget(wrap_scroll(self.file_panel))
        self.splitter.addWidget(wrap_scroll(self.config_panel))
        self.splitter.addWidget(self.plot_panel)
        self.splitter.addWidget(wrap_scroll(self.results_panel))
        # Let plot/results breathe relative to input panels.
        for i in range(4):
            self.splitter.setStretchFactor(i, 1)

        root.addWidget(self.splitter, 1)

        # ── Action bar (plot type + buttons) ─────────────────────
        self._build_action_bar(root)

        # ── Status bar + progress ─────────────────────────────────
        self._build_status_bar()

        # ── Menu bar + shortcuts + recent files ──────────────────
        self._build_menu()

        # ── Wire controller signals ──────────────────────────────
        self.controller.computeStarted.connect(self._on_compute_started)
        self.controller.computeFinished.connect(self._on_compute_finished)
        self.controller.resultReady.connect(self._on_result_ready)
        self.controller.computeFailed.connect(self._on_compute_failed)
        self.controller.validationFailed.connect(self._on_validation_failed)
        self.file_panel.fileLoaded.connect(self._on_file_loaded)
        self.file_panel.loadFailed.connect(self._on_file_load_failed)

        # compute-button enable state follows readiness.
        self.controller.state.readyChanged.connect(self._update_button_state)
        self.controller.state.missingFieldsChanged.connect(self._update_status_missing_fields)
        # Multivar config-panel refresh is driven by the file panel's X-row
        # section; the slot itself no-ops unless the active mode is multivar,
        # so wiring it once at startup is safe.
        self.file_panel.multivar_widget.colsChanged.connect(self._on_multivar_cols_changed)
        # Initial plot-type sync.
        self.controller.state.set_plot_type(PlotType.SCATTER_LINE)
        self._update_button_state(self.controller.state.is_ready())

        # Restore saved geometry / splitter state, then open maximised if this
        # is the first run (no saved geometry).
        self._restore_state()
        self._refresh_recent_files_menu()

    # ── UI construction ──────────────────────────────────────────
    def _build_action_bar(self, parent_layout: QVBoxLayout) -> None:
        bar = QWidget()
        bar_layout = QVBoxLayout(bar)
        bar_layout.setContentsMargins(16, 12, 16, 12)
        bar_layout.setSpacing(8)
        row = bar_layout  # a single row is fine; reuse vlayout's stretch

        from PySide6.QtWidgets import QHBoxLayout

        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)
        h.addStretch()
        h.addWidget(QLabel("Plot type:"))
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItem("Scatter / Line", PlotType.SCATTER_LINE)
        self.plot_type_combo.addItem("Surface 3D", PlotType.SURFACE_3D)
        self.plot_type_combo.addItem("Multivariable Regression", PlotType.MULTIVARIABLE_REGRESSION)
        self.plot_type_combo.setToolTip("2D scatter/line, 3D surface, or multivariable linear fit")
        self.plot_type_combo.currentIndexChanged.connect(self._on_plot_type_changed)
        h.addWidget(self.plot_type_combo)
        h.addSpacing(16)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setFixedWidth(100)
        self.reset_btn.setToolTip("Reset every panel to its defaults (Ctrl+R)")
        self.reset_btn.clicked.connect(self.reset_coordinator.reset_all)
        self.reset_btn.clicked.connect(self.controller.state.reset)
        self.reset_btn.clicked.connect(lambda: self.plot_type_combo.setCurrentIndex(0))

        self.qq_btn = QPushButton("Show QQ Plot")
        self.qq_btn.setFixedWidth(150)
        self.qq_btn.setToolTip("Open the Q-Q plot of the latest fit's residuals")
        self.qq_btn.clicked.connect(lambda: self.controller.compute(PlotDiagnosticType.QQ_PLOT))

        self.residual_btn = QPushButton("Show Residual")
        self.residual_btn.setFixedWidth(150)
        self.residual_btn.setToolTip("Open the residual plot of the latest fit")
        self.residual_btn.clicked.connect(
            lambda: self.controller.compute(PlotDiagnosticType.RESIDUAL)
        )

        self.compute_btn = QPushButton("Generate plot")
        self.compute_btn.setFixedWidth(130)
        self.compute_btn.setDefault(True)
        self.compute_btn.setAutoDefault(True)
        self.compute_btn.setToolTip("Fit and render the main plot (Ctrl+Enter)")
        self.compute_btn.clicked.connect(lambda: self.controller.compute(PlotDiagnosticType.PLOT))

        for w in (self.reset_btn, self.qq_btn, self.residual_btn, self.compute_btn):
            self.controller.register_compute_button(w)
            h.addWidget(w)
        row.addLayout(h)
        parent_layout.addWidget(bar)

    def _build_status_bar(self) -> None:
        bar = QStatusBar(self)
        self.setStatusBar(bar)
        self.status_label = QLabel("Ready")
        bar.addWidget(self.status_label)
        self.progress = QProgressBar()
        self.progress.setFixedWidth(200)
        self.progress.setMaximumHeight(18)
        self.progress.setRange(0, 0)  # indeterminate while running
        self.progress.setVisible(False)
        bar.addPermanentWidget(self.progress)

    def _build_menu(self) -> None:
        menubar: QMenuBar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        self._recent_menu: QMenu = file_menu.addMenu("Recent &Files")
        file_menu.addSeparator()
        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Plot menu
        plot_menu = menubar.addMenu("&Plot")
        gen_action = QAction("&Generate plot", self)
        gen_action.setShortcut(QKeySequence("Ctrl+Return"))
        gen_action.triggered.connect(lambda: self.controller.compute(PlotDiagnosticType.PLOT))
        plot_menu.addAction(gen_action)

        qq_action = QAction("Show &Q-Q plot", self)
        qq_action.setShortcut(QKeySequence("Ctrl+Shift+Q"))
        qq_action.triggered.connect(lambda: self.controller.compute(PlotDiagnosticType.QQ_PLOT))
        plot_menu.addAction(qq_action)

        resid_action = QAction("Show &Residual plot", self)
        resid_action.setShortcut(QKeySequence("Ctrl+Shift+R"))
        resid_action.triggered.connect(lambda: self.controller.compute(PlotDiagnosticType.RESIDUAL))
        plot_menu.addAction(resid_action)

        plot_menu.addSeparator()
        reset_action = QAction("&Reset", self)
        reset_action.setShortcut(QKeySequence("Ctrl+R"))
        reset_action.triggered.connect(self.reset_btn.click)
        plot_menu.addAction(reset_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.setShortcut(QKeySequence("F1"))
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        cite_action = QAction("&Citation", self)
        cite_action.triggered.connect(self._show_citation)
        help_menu.addAction(cite_action)

    # ── controller signal handlers ──────────────────────────────
    def _on_compute_started(self, label: str) -> None:
        self.status_label.setText(label)
        self.progress.setVisible(True)
        for w in (self.reset_btn, self.qq_btn, self.residual_btn, self.compute_btn):
            w.setEnabled(False)

    def _on_compute_finished(self) -> None:
        self.progress.setVisible(False)
        self._update_button_state(self.controller.state.is_ready())
        if self.status_label.text() in {
            "Fitting…",
            "Computing residuals…",
            "Computing Q-Q plot…",
            "Computing…",
        }:
            self.status_label.setText("Done")

    def _on_result_ready(self, result, payload, params) -> None:  # noqa: ANN001
        try:
            self.results_panel.display_result(result, params)
            window = self._plot_windows.get(payload.diagnostic)
            if window is None:
                show_warning(self, "Rendering", "No plot window for this diagnostic")
                return
            window.show()
            window.raise_()
            window.plot(payload)
            self.status_label.setText(
                f"Done — R²={float(result.r2):.4g}, RMSE={float(result.rmse):.4g}"
            )
        except ValueError as e:
            show_warning(self, "Results error", str(e))

    def _on_compute_failed(self, message: str, detail: str) -> None:
        show_copyable_error(self, message, message, detail=detail)
        self.status_label.setText("Compute failed")

    def _on_validation_failed(self, missing: list) -> None:  # noqa: ANN001
        if not missing:
            return
        show_warning(self, "Cannot generate plot", "Missing required fields: " + ", ".join(missing))
        self.status_label.setText("Missing: " + ", ".join(missing))

    # ── panel inter-panel wiring ─────────────────────────────────
    def _on_plot_type_changed(self, _index: int) -> None:
        data = self.plot_type_combo.currentData()
        if data is None:
            return
        self.controller.state.set_plot_type(data)
        self.config_panel.set_mode(data)
        self.plot_panel.set_mode(data)
        self.file_panel.set_mode(data)
        if data == PlotType.MULTIVARIABLE_REGRESSION:
            self._on_multivar_cols_changed()

    def _on_multivar_cols_changed(self) -> None:
        n = self.file_panel.multivar_widget.row_count()
        self.config_panel.multivar_refresh(n)
        self.plot_panel.multivar_refresh(n)

    def _on_file_loaded(self, path: str) -> None:
        """Refresh recent-files menu + write to QSettings."""
        ctrl.add_recent_file(path)
        self._refresh_recent_files_menu()

    def _on_file_load_failed(self, message: str, detail: str) -> None:
        """Show a copyable error box when a background file/sheet read fails."""
        show_copyable_error(self, "I/O Error", message, detail=detail)
        self.status_label.setText("File load failed")

    def _refresh_recent_files_menu(self) -> None:
        self._recent_menu.clear()
        files = ctrl.recent_files()
        if not files:
            empty = QAction("(none)", self)
            empty.setEnabled(False)
            self._recent_menu.addAction(empty)
            return
        self._recent_action_pool: list[tuple[QAction, str]] = []
        for path in files:
            action = QAction(path, self)
            action.triggered.connect(lambda _checked=False, p=path: self._open_recent(p))
            self._recent_menu.addAction(action)
            self._recent_action_pool.append((action, path))

    def _open_recent(self, path: str) -> None:
        """Re-use FilePanel's direct-load path for a recent file."""
        self.file_panel.load_file(path)

    # ── bell-shaped enable / status updates ───────────────────────
    def _update_button_state(self, ready: bool) -> None:
        # Reset is always available; compute-family follows readiness.
        self.reset_btn.setEnabled(True)
        for w in (self.qq_btn, self.residual_btn, self.compute_btn):
            w.setEnabled(ready)

    def _update_status_missing_fields(self, missing: list) -> None:  # noqa: ANN001
        if missing:
            self.status_label.setText("Waiting on: " + ", ".join(missing))
        else:
            self.status_label.setText("Ready — press Generate plot")

    # ── About / Citation dialogs ─────────────────────────────────
    def _show_about(self) -> None:
        QMessageBox.about(self, "About Kobs-Plotter", _ABOUT_TEXT)

    def _show_citation(self) -> None:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Information)
        box.setWindowTitle("Citation")
        box.setText("If you use Kobs-Plotter in your research, please cite it as:")
        box.setInformativeText(_CITATION)
        box.exec()

    # ── state save / restore ──────────────────────────────────────
    def _save_state(self) -> None:
        s = QSettings(_ORG, _APP)
        s.setValue("main/geometry", self.saveGeometry())
        s.setValue("main/splitter", self.splitter.saveState())
        s.setValue("main/windowState", self.saveState())

    def _restore_state(self) -> None:
        s = QSettings(_ORG, _APP)
        geom = s.value("main/geometry")
        if geom is not None:
            self.restoreGeometry(geom)  # type: ignore[arg-type]
        sp = s.value("main/splitter")
        if sp is not None:
            self.splitter.restoreState(sp)  # type: ignore[arg-type]
        ws = s.value("main/windowState")
        if ws is not None:
            self.restoreState(ws)  # type: ignore[arg-type]
        if geom is None:
            # First run — open maximised so the panels are comfortable.
            self.showMaximized()

    def closeEvent(self, event) -> None:  # noqa: D401, N802 - Qt override
        # Ensure no lingering worker thread when quitting.
        if self.controller._worker is not None and self.controller._worker.isRunning():
            self.controller._worker.wait(2000)
        self._save_state()
        super().closeEvent(event)


def wrap_scroll(widget: QWidget) -> QScrollArea:
    """Wrap a panel in a non-resizable-border QScrollArea so it survives
    small window sizes without clipping its contents."""
    sa = QScrollArea()
    sa.setWidgetResizable(True)
    sa.setFrameShape(QScrollArea.Shape.NoFrame)
    sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    sa.setWidget(widget)
    return sa
