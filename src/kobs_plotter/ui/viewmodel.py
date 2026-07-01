"""
Application view-model for kobs-plotter.

``AppState`` is the single source of truth for UI state. It owns a
``PlotSettingsBuilder`` and exposes the same setter API the panels already
use, but every setter is overridden to emit a Qt signal describing what
changed. Downstream subscribers (the controller, the compute button
enabled-state, the status bar, inline field validators) react to those
signals instead of polling the builder.

This is the view-model layer of the MVC restructure: panels (views) push
user input into ``AppState`` setters; the controller (see ``controller.py``)
listens to ``AppState`` signals to drive plot windows, the status bar, and
the compute pipeline. The builder itself stays pure — it only carries data
and builds the immutable ``PlotSettings`` snapshot at compute time.

Signals:
    fieldChanged(str, object): emitted after any setter, with the field
        name (e.g. ``"x_col"``) and the new value.
    readyChanged(bool): emitted when ``is_ready()`` flips. Drives the
        enabled state of the Generate / Residual / Q-Q buttons.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Signal

from kobs_plotter.core.settings import PlotSettingsBuilder, PlotType

# Field names that affect whether the builder is "ready" for a compute run.
_READY_FIELDS = {
    "data_path",
    "sheet_name",
    "x_col",
    "y_col",
    "z_col",
    "params",
    "formula",
    "p0",
    "plot_type",
}


class AppState(QObject, PlotSettingsBuilder):
    """
    Stateful wrapper around :class:`PlotSettingsBuilder` that emits Qt
    signals on every mutation and re-evaluates :meth:`is_ready` centrally.

    Inherits every ``set_*`` method from the builder so panels can keep
    using the builder API unchanged. Each setter is overridden below to
    call the super implementation and then announce the change.
    """

    fieldChanged = Signal(str, object)
    readyChanged = Signal(bool)
    missingFieldsChanged = Signal(list)

    def __init__(self) -> None:
        # PlotSettingsBuilder is a plain Python class; QObject is the Qt
        # base. Both must be initialised explicitly — Qt's metaclass does
        # not cooperatively chain via super().__init__().
        QObject.__init__(self)
        PlotSettingsBuilder.__init__(self)
        self._was_ready: bool = False

    # ── internal helper ───────────────────────────────────────────
    def _announce(self, field: str, value: Any, affects_ready: bool) -> None:
        """Emit fieldChanged and, when readiness may have flipped, readyChanged."""
        self.fieldChanged.emit(field, value)
        if affects_ready:
            ready = self.is_ready()
            if ready != self._was_ready:
                self._was_ready = ready
                self.readyChanged.emit(ready)
                self.missingFieldsChanged.emit(self.missing_fields())

    # ── overridden setters ────────────────────────────────────────
    def set_plot_type(self, plot_type: PlotType) -> AppState:
        super().set_plot_type(plot_type)
        self._announce("plot_type", plot_type, affects_ready=True)
        return self

    def set_data_path(self, data_path: str | None) -> AppState:
        super().set_data_path(data_path)
        self._announce("data_path", data_path, affects_ready=True)
        return self

    def set_sheet_name(self, sheet_name: str | None) -> AppState:
        super().set_sheet_name(sheet_name)
        self._announce("sheet_name", sheet_name, affects_ready=True)
        return self

    def set_x_col(self, col: str | None) -> AppState:
        super().set_x_col(col)
        self._announce("x_col", col, affects_ready=True)
        return self

    def set_y_col(self, col: str | None) -> AppState:
        super().set_y_col(col)
        self._announce("y_col", col, affects_ready=True)
        return self

    def set_z_col(self, col: str | None) -> AppState:
        super().set_z_col(col)
        self._announce("z_col", col, affects_ready=True)
        return self

    def set_x_transform(self, transform: str | None) -> AppState:
        super().set_x_transform(transform)
        self._announce("x_transform", transform, affects_ready=False)
        return self

    def set_y_transform(self, transform: str | None) -> AppState:
        super().set_y_transform(transform)
        self._announce("y_transform", transform, affects_ready=False)
        return self

    def set_z_transform(self, transform: str | None) -> AppState:
        super().set_z_transform(transform)
        self._announce("z_transform", transform, affects_ready=False)
        return self

    def set_params(self, params: list[str] | None) -> AppState:
        super().set_params(params)
        self._announce("params", params, affects_ready=True)
        return self

    def set_formula(self, formula: str | None) -> AppState:
        super().set_formula(formula)
        self._announce("formula", formula, affects_ready=True)
        return self

    def set_p0(self, p0: list[str] | None) -> AppState:
        super().set_p0(p0)
        self._announce("p0", p0, affects_ready=True)
        return self

    def set_plot_theme(self, theme: str) -> AppState:
        super().set_plot_theme(theme)
        self._announce("plot_theme", theme, affects_ready=False)
        return self

    def set_title(self, title: str | None) -> AppState:
        super().set_title(title)
        self._announce("title", title, affects_ready=False)
        return self

    def set_x_label(self, label: str | None) -> AppState:
        super().set_x_label(label)
        self._announce("x_label", label, affects_ready=False)
        return self

    def set_y_label(self, label: str | None) -> AppState:
        super().set_y_label(label)
        self._announce("y_label", label, affects_ready=False)
        return self

    def set_z_label(self, label: str | None) -> AppState:
        super().set_z_label(label)
        self._announce("z_label", label, affects_ready=False)
        return self

    def set_point_color(self, color: str) -> AppState:
        super().set_point_color(color)
        self._announce("point_color", color, affects_ready=False)
        return self

    def set_line_color(self, color: str) -> AppState:
        super().set_line_color(color)
        self._announce("line_color", color, affects_ready=False)
        return self

    def set_line_style(self, style: str) -> AppState:
        super().set_line_style(style)
        self._announce("line_style", style, affects_ready=False)
        return self

    def set_colormap(self, colormap: str) -> AppState:
        super().set_colormap(colormap)
        self._announce("colormap", colormap, affects_ready=False)
        return self

    # ── bulk reset ─────────────────────────────────────────────────
    def reset(self) -> None:
        """
        Re-initialise every builder field back to its default.

        Called by the controller when the user clicks Reset. After this
        returns we emit one ``fieldChanged`` per field and a final
        ``readyChanged`` so subscribers re-sync their widgets.
        """
        PlotSettingsBuilder.__init__(self)
        self._was_ready = False
        for field, value in [
            ("plot_type", PlotType.SCATTER_LINE),
            ("data_path", None),
            ("sheet_name", None),
            ("x_col", None),
            ("y_col", None),
            ("z_col", None),
            ("x_transform", None),
            ("y_transform", None),
            ("z_transform", None),
            ("params", None),
            ("formula", None),
            ("p0", None),
            ("plot_theme", "ggplot"),
            ("title", None),
            ("x_label", None),
            ("y_label", None),
            ("z_label", None),
            ("point_color", "black"),
            ("line_color", "red"),
            ("line_style", "-"),
            ("colormap", "viridis"),
        ]:
            self.fieldChanged.emit(field, value)
        self.readyChanged.emit(False)
        self.missingFieldsChanged.emit(self.missing_fields())
