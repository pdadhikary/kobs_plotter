"""
Application controller for kobs-plotter.

The controller sits between the views (panels, plot windows, results
panel) and the view-model (:class:`AppState`). It owns the
:class:`ComputeService` and runs it on a background :class:`QThread` so
the GUI never blocks during data load / fit / payload assembly — the
single biggest responsiveness fix in this restructure.

Responsibilities:

- Run :meth:`ComputeService.compute` on a worker thread, propagating
  progress and completion back to the GUI thread via signals.
- Translate raw exceptions from the worker into user-friendly messages
  with specific catches (file-not-found, malformed Excel, transform
  errors, fit non-convergence) — never leaking Python tracebacks.
- Own the three floating :class:`PlotWindow`s, keyed by
  :class:`PlotDiagnosticType` (no more ``getattr`` string lookup).
- Save and restore window geometry, splitter state, and recent files
  via :class:`QSettings`.

Signals:
    computeStarted(str):     emitted when a worker is dispatched, with a
        short human label ("Fitting…") for the status bar.
    computeFinished():       emitted on the GUI thread after the worker
        returns, regardless of success or failure (use this to re-enable
        buttons in a ``finally``-style manner).
    resultReady(result, payload, params): emitted on success with the
        FitResult, PlotPayload, and parameter names. The MainWindow
        routes these to the results panel + the target plot window.
    computeFailed(str, str): emitted on failure with a short message
        and a selectable detail string (for the copyable error box).
    validationFailed(list): emitted when the user clicks Generate but
        is_ready() is False, with the list of missing field names.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QSettings, QThread, Signal, Slot

from kobs_plotter.core.diagnostics import PlotDiagnosticType
from kobs_plotter.core.modelling import FitResult
from kobs_plotter.core.service import ComputeService
from kobs_plotter.core.types import PlotPayload
from kobs_plotter.ui.plot_window import PlotWindow
from kobs_plotter.ui.viewmodel import AppState

log = logging.getLogger(__name__)

# QSettings organisation/application keys — set once at startup.
_ORG = "kobs-plotter"
_APP = "kobs-plotter"

# "Generate plot" buttons that the controller disables/re-enables around a
# compute run so the user cannot fire two overlapping worker runs. The
# MainWindow registers the actual QPushButton instances via
# :meth:`register_compute_button`.
_RECENT_FILES_KEY = "recentFiles"
_MAX_RECENT = 10


class ComputeWorker(QThread):
    """Background thread running :meth:`ComputeService.compute`.

    A plain :class:`QThread` subclass — the simplest cross-thread pattern
    for a one-shot job with no event loop needed in the worker. Emits
    :attr:`succeeded` or :attr:`failed` from the worker thread; the
    controller's slots are auto-queued back to the GUI thread because the
    controller lives on the GUI thread (the default).
    """

    succeeded = Signal(object, object)
    failed = Signal(Exception)

    def __init__(self, service: ComputeService, settings, diagnostic) -> None:
        super().__init__()
        self._service = service
        self._settings = settings
        self._diagnostic = diagnostic

    def run(self) -> None:  # noqa: D401 - QThread entry point
        try:
            result, payload = self._service.compute(self._settings, self._diagnostic)
            self.succeeded.emit(result, payload)
        except Exception as e:  # noqa: BLE001 - controller translates
            self.failed.emit(e)


class Controller(QObject):
    """
    Application controller.

    Created once by the MainWindow. The MainWindow wires:
      - ``computeStarted``       -> status bar message
      - ``computeFinished``      -> re-enable compute buttons + hide progress
      - ``resultReady``          -> results panel + plot window render
      - ``computeFailed``        -> copyable error dialog
      - ``validationFailed``     -> warning dialog listing missing fields
    """

    computeStarted = Signal(str)
    computeFinished = Signal()
    resultReady = Signal(object, object, object)
    computeFailed = Signal(str, str)
    validationFailed = Signal(list)

    def __init__(self, compute_service: ComputeService) -> None:
        super().__init__()
        self.state = AppState()
        self.compute_service = compute_service
        self._worker: ComputeWorker | None = None
        self._compute_buttons: list = []  # type: ignore[type-arg]

    # ── compute pipelines ──────────────────────────────────────────
    def register_compute_button(self, btn) -> None:  # noqa: ANN001 - QPushButton
        """Register a button to be disabled/re-enabled around compute runs."""
        self._compute_buttons.append(btn)

    def compute(self, diagnostic: PlotDiagnosticType) -> None:
        """
        Validate readiness, then dispatch a :class:`ComputeWorker`.

        On invalid input emits :attr:`validationFailed` and returns. While a
        worker is running, subsequent calls are ignored — the buttons are
        disabled anyway, but this is a belt-and-braces guard for keyboard
        shortcut triggers.
        """
        if self._worker is not None and self._worker.isRunning():
            return
        if not self.state.is_ready():
            self.validationFailed.emit(self.state.missing_fields())
            return

        try:
            settings = self.state.build()
        except ValueError:
            self.validationFailed.emit(self.state.missing_fields())
            return

        for btn in self._compute_buttons:
            btn.setEnabled(False)

        label = {
            PlotDiagnosticType.PLOT: "Fitting…",
            PlotDiagnosticType.RESIDUAL: "Computing residuals…",
            PlotDiagnosticType.QQ_PLOT: "Computing Q-Q plot…",
        }.get(diagnostic, "Computing…")
        self.computeStarted.emit(label)

        self._worker = ComputeWorker(self.compute_service, settings, diagnostic)
        self._worker.succeeded.connect(self._on_succeeded)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self.computeFinished)
        self._worker.start()

    @Slot(object, object)
    def _on_succeeded(self, result: FitResult, payload: PlotPayload) -> None:
        params = list(self.state._params) if self.state._params else []
        self.resultReady.emit(result, payload, params)

    @Slot(object)
    def _on_failed(self, exc: Exception) -> None:
        log.exception("Compute failed", exc_info=exc)
        message, detail = _translate_exception(exc)
        self.computeFailed.emit(message, detail)

    # ── plot windows ───────────────────────────────────────────────
    def make_plot_windows(self, parent) -> dict[PlotDiagnosticType, PlotWindow]:  # noqa: ANN001
        """
        Create the three reusable floating plot windows.

        Returns a dict keyed by :class:`PlotDiagnosticType` so render
        dispatch is a plain lookup — no more ``getattr(self, name)``
        against a hardcoded attribute-name mapping.
        """
        return {
            PlotDiagnosticType.PLOT: PlotWindow(parent=parent, window_title="Plot"),
            PlotDiagnosticType.RESIDUAL: PlotWindow(parent=parent, window_title="Residual Plot"),
            PlotDiagnosticType.QQ_PLOT: PlotWindow(parent=parent, window_title="Q-Q Plot"),
        }


# ── settings persistence ──────────────────────────────────────────


def settings() -> QSettings:
    """Return the application-wide :class:`QSettings` instance."""
    return QSettings(_ORG, _APP)


def add_recent_file(path: str) -> list[str]:
    """Prepend ``path`` to the recent-files list and persist it.

    De-duplicates (an existing entry is moved to the top), caps the list
    at :data:`_MAX_RECENT`, and returns the new ordered list so the caller
    can rebuild its menu immediately.
    """
    s = settings()
    files = list(s.value(_RECENT_FILES_KEY, [], type=list))  # type: ignore[arg-type]
    if path in files:
        files.remove(path)
    files.insert(0, path)
    files = files[:_MAX_RECENT]
    s.setValue(_RECENT_FILES_KEY, files)
    return files


def recent_files() -> list[str]:
    """Return the persisted list of recently opened files (newest first)."""
    s = settings()
    return list(s.value(_RECENT_FILES_KEY, [], type=list))  # type: ignore[arg-type]


def last_directory() -> str:
    """Return the last-used directory for file dialogs (persisted)."""
    return str(settings().value("lastDirectory", ""))  # type: ignore[arg-type]


def set_last_directory(path: str) -> None:
    settings().setValue("lastDirectory", path)


# ── exception translation ─────────────────────────────────────────


def _translate_exception(exc: Exception) -> tuple[str, str]:
    """
    Map a raw worker exception to a (short user message, copyable detail).

    The detail always includes the exception type and message; the short
    message is a friendly, human-readable summary keyed to the known
    failure modes produced by the core layer (file I/O, transforms,
    curve_fit non-convergence). Unknown exceptions get a generic message
    so traceback noise never reaches the end user.
    """
    import traceback

    import pandas as pd

    detail = f"{type(exc).__name__}: {exc}\n\n{traceback.format_exc()}"

    if isinstance(exc, FileNotFoundError):
        return "File not found", detail
    if isinstance(exc, (pd.errors.ParserError, pd.errors.EmptyDataError)):
        return "Could not read the Excel file", detail
    if isinstance(exc, PermissionError):
        return "Permission denied opening the file", detail
    if isinstance(exc, ValueError):
        # Transform errors and build() missing-field errors are ValueError.
        return "Invalid input", detail
    if isinstance(exc, RuntimeError):
        # scipy curve_fit raises RuntimeError on non-convergence.
        return "Fit failed to converge — check initial parameter values", detail
    return "An unexpected error occurred", detail
