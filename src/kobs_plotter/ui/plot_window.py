"""
Plot window UI component for kobs-plotter.

Provides a standalone ``QMainWindow`` containing an embedded matplotlib
figure with the standard navigation toolbar. Supports 2D scatter / line
plots with confidence bands and 3D surface plots with projected
contours. Per-view rendering is dispatched through a
``(plot_type, diagnostic) -> renderer`` registry with a graceful
"unsupported view" fallback.

UI/UX hardening relative to the previous version:

- Result text is drawn via :func:`matplotlib.axes.Axes.annotate` with
  axes-fraction coordinates so it tracks the axes on resize (previously
  it floated in a fixed figure-fraction position).
- Empty / None residuals are guarded so the Q-Q renderer no longer
  silently raises inside ``scipy.stats.probplot``.
- An unknown ``(plot_type, diagnostic)`` combination shows an
  ``"Unsupported view"`` message instead of raising ``KeyError``.
- The figure is created with a HiDPI-aware DPI so the canvas is crisp on
  retina / 4K displays.
- ``Esc`` closes the window, ``Ctrl+S`` triggers the toolbar's save
  figure action, and window geometry is saved/restored via QSettings.
- :meth:`on_reset` shows a helpful placeholder ("Press Generate Plot to
  render") instead of a blank axes.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import numpy as np
from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from kobs_plotter.core.diagnostics import PlotDiagnosticType
from kobs_plotter.core.plotting import PlotPayload
from kobs_plotter.core.settings import PlotType

if TYPE_CHECKING:
    from matplotlib.figure import Figure

type Renderer = Callable[[Figure, PlotPayload], None]


def _add_result_text(figure: Figure, ax, result_string: str) -> None:
    """Place the formatted result string just outside the right edge of ``ax``.

    Using axes-fraction coordinates (``xycoords='axes fraction'``) means
    the annotation follows the axes when the figure is resized, unlike a
    fixed ``figure.text`` call in figure coordinates.
    """
    ax.annotate(
        result_string,
        xy=(1.02, 0.5),
        xycoords="axes fraction",
        verticalalignment="center",
        family="monospace",
        fontsize=9,
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
        annotation_clip=False,
    )


def _render_scatter_plot(figure: Figure, payload: PlotPayload) -> None:
    """Render a 2D scatter plot with fitted curve and confidence band."""
    settings = payload.settings
    ax = figure.add_subplot(111)
    ax.set_xscale(settings.x_axis_scale)
    ax.set_yscale(settings.y_axis_scale)
    ax.scatter(payload.x, payload.y, color=settings.point_color, zorder=5)
    ax.plot(
        payload.x_fit,
        payload.y_fit,
        color=settings.line_color,
        linestyle=settings.line_style,
    )
    if payload.conf_lower is not None and payload.conf_upper is not None:
        ax.fill_between(
            payload.x_fit,
            payload.conf_lower,
            payload.conf_upper,
            alpha=0.2,
            color=settings.line_color,
        )
    ax.set_title(settings.title or "")
    ax.set_xlabel(settings.x_label or "")
    ax.set_ylabel(settings.y_label or "")
    figure.subplots_adjust(right=0.72)
    if payload.result_string:
        _add_result_text(figure, ax, payload.result_string)


def _render_surface_plot(figure: Figure, payload: PlotPayload) -> None:
    """Render a 3D scatter plot with fitted surface and projected contour."""
    settings = payload.settings
    ax = figure.add_subplot(111, projection="3d")
    ax.scatter(payload.x, payload.y, payload.z, alpha=0.6, color=settings.point_color, zorder=5)
    ax.plot_surface(payload.x_fit, payload.y_fit, payload.z_fit, cmap=settings.colormap, alpha=0.6)
    ax.contour(
        payload.x_fit,
        payload.y_fit,
        payload.z_fit,
        zdir="z",
        offset=ax.get_zlim()[0],
        cmap=settings.colormap,
    )
    ax.set_title(settings.title or "")
    ax.set_xlabel(settings.x_label or "")
    ax.set_ylabel(settings.y_label or "")
    ax.set_zlabel(settings.z_label or "")
    figure.subplots_adjust(right=0.62)
    if payload.result_string:
        _add_result_text(figure, ax, payload.result_string)


def _render_scatter_residual(figure: Figure, payload: PlotPayload) -> None:
    """Render a 2D residual scatter plot against the independent variable."""
    settings = payload.settings
    ax = figure.add_subplot(111)
    ax.scatter(payload.x, payload.residuals, color=settings.point_color, zorder=5)
    ax.axhline(y=0, label="Baseline", color=settings.line_color, linestyle=settings.line_style)
    ax.set_title(settings.title or "")
    ax.set_xlabel(settings.x_label or "")
    ax.set_ylabel("Residuals")
    figure.legend()


def _render_surface_residual(figure: Figure, payload: PlotPayload) -> None:
    """Render a 3D residual scatter plot against the two independent variables."""
    settings = payload.settings
    ax = figure.add_subplot(111, projection="3d")
    ax.scatter(payload.x, payload.y, payload.residuals, color=settings.point_color, zorder=5)

    xlim, ylim = ax.get_xlim(), ax.get_ylim()
    xx, yy = np.meshgrid(xlim, ylim)
    zz = np.zeros_like(xx)
    ax.plot_surface(xx, yy, zz, alpha=0.15, color="gray")

    ax.set_title(settings.title or "")
    ax.set_xlabel(settings.x_label or "")
    ax.set_ylabel(settings.y_label or "")
    ax.set_zlabel("Residuals")


def _render_qq(figure: Figure, payload: PlotPayload) -> None:
    """Render a normal Q-Q plot of the fit residuals (guarding empty input)."""
    import scipy.stats as stats

    settings = payload.settings
    ax = figure.add_subplot(111)
    residuals = payload.residuals
    if residuals is None or len(residuals) == 0:
        ax.text(
            0.5,
            0.5,
            "No residuals available",
            transform=ax.transAxes,
            horizontalalignment="center",
        )
    else:
        stats.probplot(residuals, dist="norm", plot=ax)
    ax.set_title(settings.title or "")


def _render_unsupported(figure: Figure, payload: PlotPayload) -> None:
    """Fallback renderer for an unknown (plot_type, diagnostic) combination."""
    ax = figure.add_subplot(111)
    ax.text(
        0.5,
        0.5,
        f"Unsupported view\n{payload.settings.plot_type} / {payload.diagnostic}",
        transform=ax.transAxes,
        horizontalalignment="center",
    )


# ── Multivariable regression renderers ────────────────────────────


def _render_multivar_plot(figure: Figure, payload: PlotPayload) -> None:
    """Render a multivariable regression plot, branching on the predictor count.

    * 1 predictor -> reuse the 2D scatter+line+band renderer.
    * 2 predictors -> reuse the 3D scatter+plane renderer.
    * 3+ predictors -> 2D Actual vs Predicted scatter with a y=x reference line
      and fixed axis labels.
    """
    n = len(payload.x_cols)
    if n == 1:
        _render_scatter_plot(figure, payload)
        return
    if n == 2:
        _render_surface_plot(figure, payload)
        return
    # 3+ predictors: Actual vs Predicted.
    settings = payload.settings
    ax = figure.add_subplot(111)
    ax.scatter(payload.x, payload.y, color=settings.point_color, zorder=5)
    lo = float(min(payload.x.min(), payload.y.min()))
    hi = float(max(payload.x.max(), payload.y.max()))
    ax.plot([lo, hi], [lo, hi], color=settings.line_color, linestyle=settings.line_style)
    ax.set_title(settings.title or "")
    ax.set_xlabel("Actual")
    ax.set_ylabel("Predicted")
    figure.subplots_adjust(right=0.72)
    if payload.result_string:
        _add_result_text(figure, ax, payload.result_string)


def _render_multivar_residual(figure: Figure, payload: PlotPayload) -> None:
    """Residuals plotted against the fitted (predicted) values.

    For 3+ predictors there is no single independent axis to plot against,
    so Predicted vs Residual is the canonical view. We use it for every
    multivar dimension for consistency.
    """
    settings = payload.settings
    ax = figure.add_subplot(111)
    predicted = payload.predicted if payload.predicted is not None else payload.x
    ax.scatter(predicted, payload.residuals, color=settings.point_color, zorder=5)
    ax.axhline(
        y=0, label="Baseline", color=settings.line_color, linestyle=settings.line_style
    )
    ax.set_title(settings.title or "")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Residuals")
    figure.legend()


_RENDERERS: dict[tuple[PlotType, PlotDiagnosticType], Renderer] = {
    (PlotType.SCATTER_LINE, PlotDiagnosticType.PLOT): _render_scatter_plot,
    (PlotType.SCATTER_LINE, PlotDiagnosticType.RESIDUAL): _render_scatter_residual,
    (PlotType.SCATTER_LINE, PlotDiagnosticType.QQ_PLOT): _render_qq,
    (PlotType.SURFACE_3D, PlotDiagnosticType.PLOT): _render_surface_plot,
    (PlotType.SURFACE_3D, PlotDiagnosticType.RESIDUAL): _render_surface_residual,
    (PlotType.SURFACE_3D, PlotDiagnosticType.QQ_PLOT): _render_qq,
    (PlotType.MULTIVARIABLE_REGRESSION, PlotDiagnosticType.PLOT): _render_multivar_plot,
    (PlotType.MULTIVARIABLE_REGRESSION, PlotDiagnosticType.RESIDUAL): _render_multivar_residual,
    (PlotType.MULTIVARIABLE_REGRESSION, PlotDiagnosticType.QQ_PLOT): _render_qq,
}


class PlotWindow(QMainWindow):
    """
    Floating plot window displaying the fitted curve or surface.

    Hosts an embedded matplotlib figure with the standard navigation
    toolbar (zoom, pan, save). The window is created once by
    :class:`Controller` and reused across successive compute runs —
    calling :meth:`plot` clears and redraws the figure in place.

    Keyboard shortcuts:

    - ``Esc``     — close the window
    - ``Ctrl+S``   — trigger the toolbar's "Save Figure" action

    Window geometry is saved/restored via :class:`QSettings` so reopened
    plot windows return to their last size and position.
    """

    def __init__(self, parent=None, window_title: str = "Plot") -> None:
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
        from matplotlib.figure import Figure

        super().__init__(parent)
        self.setObjectName(window_title)
        self.setWindowTitle(window_title)
        self.setMinimumSize(720, 480)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # HiDPI-aware figure: scale the DPI by the screen device pixel ratio
        # so the canvas is crisp on retina / 4K displays.
        dpr = int(self.devicePixelRatioF()) if self.devicePixelRatioF() > 0 else 1
        self.figure = Figure(dpi=100 * max(dpr, 1))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        # Keyboard shortcuts.
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self.close)
        QShortcut(QKeySequence.StandardKey.Save, self, self.toolbar.save_figure)

        self._restore_geometry()

    def plot(self, payload: PlotPayload) -> None:
        """
        Clear the figure and render a new plot from the provided payload.

        Looks up the renderer for ``(plot_type, diagnostic)`` in the
        :data:`_RENDERERS` registry; unknown combinations fall through to
        :func:`_render_unsupported`. The selected plot theme is applied
        via a style context so it does not affect any other matplotlib
        state outside this window.
        """
        settings = payload.settings
        import matplotlib.pyplot as plt

        with plt.style.context(settings.plot_theme):
            self._clear()
            renderer = _RENDERERS.get((settings.plot_type, payload.diagnostic), _render_unsupported)
            renderer(self.figure, payload)
            self.canvas.draw()

    def _clear(self) -> None:
        """Clear the figure, applying the current theme's face color."""
        import matplotlib.pyplot as plt

        self.figure.clear()
        self.figure.set_facecolor(plt.rcParams["figure.facecolor"])

    def on_reset(self) -> None:
        """Reset the window to an empty-state with a helpful placeholder."""
        import matplotlib.pyplot as plt

        with plt.style.context("ggplot"):
            self._clear()
            ax = self.figure.add_subplot(111)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.text(
                0.5,
                0.5,
                "Press Generate Plot to render",
                transform=ax.transAxes,
                horizontalalignment="center",
                fontsize=12,
                color="gray",
            )
            self.canvas.draw()

    # ── geometry persistence ─────────────────────────────────────────
    def _settings_group(self) -> str:
        return f"PlotWindow/{self.objectName()}"

    def _restore_geometry(self) -> None:
        s = QSettings("kobs-plotter", "kobs-plotter")
        s.beginGroup(self._settings_group())
        geom = s.value("geometry")
        if geom is not None:
            self.restoreGeometry(geom)  # type: ignore[arg-type]
        s.endGroup()

    def closeEvent(self, event) -> None:  # noqa: D401, N802 - Qt override
        s = QSettings("kobs-plotter", "kobs-plotter")
        s.beginGroup(self._settings_group())
        s.setValue("geometry", self.saveGeometry())
        s.endGroup()
        super().closeEvent(event)
