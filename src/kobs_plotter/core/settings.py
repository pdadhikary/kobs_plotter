"""
Settings module for kobs-plotter.

Defines the PlotType enum, the immutable PlotSettings dataclass,
and the PlotSettingsBuilder for accumulating UI state before computation.
"""

from dataclasses import dataclass
from enum import Enum, auto

from kobs_plotter.core.defaults import (
    DEFAULT_COLORMAP,
    DEFAULT_LINE_COLOR,
    DEFAULT_LINE_STYLE,
    DEFAULT_POINT_COLOR,
    DEFAULT_THEME,
)


class PlotType(Enum):
    """Enum representing the type of plot to generate."""

    """2D scatter plot with a fitted trend line."""
    SCATTER_LINE = auto()
    """3D surface plot with scatter points."""
    SURFACE_3D = auto()


@dataclass(frozen=True)
class PlotSettings:
    """
    immutable snapshot of all user-configured settings passed to the
    core computation and plotting layer.

    this object is constructed by plotsettingsbuilder.build() and should
    never be mutated after creation. all fields are either required or
    explicitly optional to make missing values visible at the type level.
    """

    plot_type: PlotType
    data_path: str
    sheet_name: str
    x_col: str
    y_col: str
    z_col: str | None
    x_transform: str | None
    y_transform: str | None
    z_transform: str | None
    params: tuple[str, ...]
    formula: str
    p0: tuple[str, ...]
    plot_theme: str
    title: str | None
    x_label: str | None
    y_label: str | None
    z_label: str | None
    point_color: str
    line_color: str
    line_style: str
    colormap: str


class PlotSettingsBuilder:
    """
    Accumulates plot settings from UI panels incrementally.

    Each panel holds a reference to the shared builder instance and calls
    the appropriate setter whenever a widget value changes. Once the user
    clicks Generate Plot, MainWindow calls build() to produce an immutable
    PlotSettings object for the computation layer.

    Usage::

        builder = PlotSettingsBuilder()
        builder.set_data_path("/data/experiment.xlsx")
        builder.set_sheet_name("Sheet1")
        builder.set_formula("B - A * exp(-k * x)")
        settings = builder.build()
    """

    def __init__(self):
        """
        Initialise the builder with safe defaults.

        Plot theme defaults to 'ggplot', point color to 'black',
        line color to 'red', line style to '-', and colormap to 'viridis'.
        All other fields default to None and must be set before calling build().
        """
        self._plot_type: PlotType = PlotType.SCATTER_LINE
        self._data_path: str | None = None
        self._sheet_name: str | None = None
        self._x_col: str | None = None
        self._y_col: str | None = None
        self._z_col: str | None = None
        self._x_transform: str | None = None
        self._y_transform: str | None = None
        self._z_transform: str | None = None
        self._params: list[str] | None = None
        self._formula: str | None = None
        self._p0: list[str] | None = None
        self._title: str | None = None
        self._x_label: str | None = None
        self._y_label: str | None = None
        self._z_label: str | None = None
        self._plot_theme: str = DEFAULT_THEME
        self._point_color: str = DEFAULT_POINT_COLOR
        self._line_color: str = DEFAULT_LINE_COLOR
        self._line_style: str = DEFAULT_LINE_STYLE
        self._colormap: str = DEFAULT_COLORMAP

    def set_plot_type(self, plot_type: PlotType) -> "PlotSettingsBuilder":
        """Set the plot type (2D scatter/line or 3D surface)."""
        self._plot_type = plot_type
        return self

    def set_data_path(self, data_path: str | None) -> "PlotSettingsBuilder":
        """Set the absolute path to the Excel file."""
        self._data_path = data_path
        return self

    def set_sheet_name(self, sheet_name: str | None) -> "PlotSettingsBuilder":
        """Set the name of the sheet to read from the Excel file."""
        self._sheet_name = sheet_name
        return self

    def set_x_col(self, col: str | None) -> "PlotSettingsBuilder":
        """Set the column name to use as the independent variable (X axis)."""
        self._x_col = col
        return self

    def set_y_col(self, col: str | None) -> "PlotSettingsBuilder":
        """Set the column name to use as the dependent variable (Y axis)."""
        self._y_col = col
        return self

    def set_z_col(self, col: str | None) -> "PlotSettingsBuilder":
        """Set the column name to use as the Z axis. Required for 3D surface plots."""
        self._z_col = col
        return self

    def set_x_transform(self, transform: str | None) -> "PlotSettingsBuilder":
        """
        Set a NumPy expression to transform the X series before fitting.

        The expression is evaluated with x as the input array.

        Example::

            builder.set_x_transform("np.log(x)")
        """
        self._x_transform = transform
        return self

    def set_y_transform(self, transform: str | None) -> "PlotSettingsBuilder":
        """
        Set a NumPy expression to transform the Y series before fitting.

        The expression is evaluated with y as the input array.

        Example::

            builder.set_y_transform("y / 1000")
        """
        self._y_transform = transform
        return self

    def set_z_transform(self, transform: str | None) -> "PlotSettingsBuilder":
        """
        Set a NumPy expression to transform the Z series before fitting.

        Only relevant for 3D surface plots. The expression is evaluated
        with z as the input array.
        """
        self._z_transform = transform
        return self

    def set_params(self, params: list[str] | None) -> "PlotSettingsBuilder":
        """
        Set the list of parameter symbols for the model formula.

        These are the symbols that curve_fit will optimise. Should exclude
        the independent variable symbols (x for 2D, x and y for 3D).

        Example::

            builder.set_params(["A", "B", "k"])
        """
        self._params = params
        return self

    def set_formula(self, formula: str | None) -> "PlotSettingsBuilder":
        """
        Set the model formula as a mathematical expression string.

        The expression is parsed by SymPy and compiled into a callable
        via lambdify. Use standard mathematical notation — do not use
        NumPy prefixes (e.g. use exp not np.exp).

        Example::

            builder.set_formula("B - A * exp(-k * x)")
        """
        self._formula = formula
        return self

    def set_p0(self, p0: list[str] | None) -> "PlotSettingsBuilder":
        """
        Set the initial parameter guesses for curve_fit.

        Each element corresponds to the parameter at the same index in params.
        Values are strings that may be plain numbers or NumPy expressions
        evaluated against the data at fit time.

        Example::

            builder.set_p0(["np.max(y)", "np.min(y)", "1.0"])
        """
        self._p0 = p0
        return self

    def set_plot_theme(self, theme: str) -> "PlotSettingsBuilder":
        """Set the matplotlib style theme to apply to the plot."""
        self._plot_theme = theme
        return self

    def set_title(self, title: str | None) -> "PlotSettingsBuilder":
        """Set the plot title. Supports LaTeX expressions wrapped in $...$."""
        self._title = title
        return self

    def set_x_label(self, label: str | None) -> "PlotSettingsBuilder":
        """Set the X axis label. Supports LaTeX expressions wrapped in $...$."""
        self._x_label = label
        return self

    def set_y_label(self, label: str | None) -> "PlotSettingsBuilder":
        """Set the Y axis label. Supports LaTeX expressions wrapped in $...$."""
        self._y_label = label
        return self

    def set_z_label(self, label: str | None) -> "PlotSettingsBuilder":
        """Set the Z axis label. Only used for 3D surface plots. Supports LaTeX."""
        self._z_label = label
        return self

    def set_point_color(self, color: str) -> "PlotSettingsBuilder":
        """Set the color of scatter plot data points. Accepts any matplotlib color string or hex value."""
        self._point_color = color
        return self

    def set_line_color(self, color: str) -> "PlotSettingsBuilder":
        """Set the color of the fitted trend line. Accepts any matplotlib color string or hex value."""
        self._line_color = color
        return self

    def set_line_style(self, style: str) -> "PlotSettingsBuilder":
        """
        Set the line style of the fitted trend line.

        Accepted values: '-' (solid), '--' (dashed), '-.' (dash-dot), ':' (dotted).
        """
        self._line_style = style
        return self

    def set_colormap(self, colormap: str) -> "PlotSettingsBuilder":
        """Set the colormap for 3D surface plots. Accepts any valid matplotlib colormap name."""
        self._colormap = colormap
        return self

    def is_ready(self) -> bool:
        """
        Check whether all required fields are set for the current plot type.

        Returns True if the builder has enough information to call build().
        The required fields differ between SCATTER_LINE and SURFACE_3D —
        the latter additionally requires z_col to be set.
        """
        if self._plot_type == PlotType.SCATTER_LINE:
            return all(
                [
                    self._data_path is not None,
                    self._sheet_name is not None,
                    self._x_col is not None,
                    self._y_col is not None,
                    self._params is not None,
                    self._formula is not None,
                    self._p0 is not None,
                ]
            )
        elif self._plot_type == PlotType.SURFACE_3D:
            return all(
                [
                    self._data_path is not None,
                    self._sheet_name is not None,
                    self._x_col is not None,
                    self._y_col is not None,
                    self._z_col is not None,
                    self._params is not None,
                    self._formula is not None,
                    self._p0 is not None,
                ]
            )
        else:
            return False

    def missing_fields(self) -> list[str]:
        """
        Return a list of human-readable names of required fields that are not yet set.

        Used to populate the warning dialog shown to the user when they click
        Generate Plot before filling in all required inputs. The Z column is
        included only for 3D surface plots, where it is required.
        """
        missing = []
        if self._data_path is None:
            missing.append("Data Path")
        if self._sheet_name is None:
            missing.append("Sheet Name")
        if self._x_col is None:
            missing.append("X Column")
        if self._y_col is None:
            missing.append("Y Column")
        if self._plot_type == PlotType.SURFACE_3D and self._z_col is None:
            missing.append("Z Column")
        if self._params is None:
            missing.append("Parameters")
        if self._formula is None:
            missing.append("Formula")
        if self._p0 is None:
            missing.append("Initial States")
        return missing

    def build(self) -> PlotSettings:
        """
        Construct and return an immutable PlotSettings object.

        Raises ValueError if any required fields are missing, with a message
        listing the missing field names from missing_fields().

        Returns:
            PlotSettings: immutable snapshot of the current builder state.

        Raises:
            ValueError: if is_ready() returns False.
        """
        if not self.is_ready():
            raise ValueError(f"Missing fields: {', '.join(self.missing_fields())}")

        # is_ready() guarantees these are set; the asserts narrow the types
        # for the type-checker and act as a defensive guard at runtime.
        assert self._data_path is not None
        assert self._sheet_name is not None
        assert self._x_col is not None
        assert self._y_col is not None
        assert self._params is not None
        assert self._formula is not None
        assert self._p0 is not None
        if self._plot_type == PlotType.SURFACE_3D:
            assert self._z_col is not None

        return PlotSettings(
            plot_type=self._plot_type,
            data_path=self._data_path,
            sheet_name=self._sheet_name,
            x_col=self._x_col,
            y_col=self._y_col,
            z_col=self._z_col,
            x_transform=self._x_transform,
            y_transform=self._y_transform,
            z_transform=self._z_transform,
            params=tuple(self._params),
            formula=self._formula,
            p0=tuple(self._p0),
            plot_theme=self._plot_theme,
            title=self._title,
            x_label=self._x_label,
            y_label=self._y_label,
            z_label=self._z_label,
            point_color=self._point_color,
            line_color=self._line_color,
            line_style=self._line_style,
            colormap=self._colormap,
        )
