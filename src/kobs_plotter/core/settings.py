from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class PlotType(Enum):
    SCATTER_LINE = auto()
    SURFACE_3D = auto()


@dataclass(frozen=True)
class PlotSettings:
    """Immutable settings object passed to the core computation layer."""

    plot_type: PlotType
    data_path: str
    sheet_name: str
    x_col: str
    y_col: str
    z_col: Optional[str]
    x_transform: Optional[str]
    y_transform: Optional[str]
    z_transform: Optional[str]
    params: list[str]
    formula: str
    p0: list[str]
    plot_theme: str
    title: Optional[str]
    x_label: Optional[str]
    y_label: Optional[str]
    z_label: Optional[str]
    point_color: Optional[str]
    line_color: Optional[str]
    line_style: Optional[str]
    colormap: Optional[str]


class PlotSettingsBuilder:
    """
    Accumulates settings from UI panels.
    Mutated freely as the user updates inputs.
    Call .build() only when Compute is clicked.
    """

    def __init__(self):
        self._plot_type: PlotType
        self._data_path: Optional[str] = None
        self._sheet_name: Optional[str] = None
        self._x_col: Optional[str] = None
        self._y_col: Optional[str] = None
        self._z_col: Optional[str] = None
        self._x_transform: Optional[str] = None
        self._y_transform: Optional[str] = None
        self._z_transform: Optional[str] = None
        self._params: Optional[list[str]] = None
        self._formula: Optional[str] = None
        self._p0: Optional[list[str]] = None
        self._title: Optional[str] = None
        self._x_label: Optional[str] = None
        self._y_label: Optional[str] = None
        self._z_label: Optional[str] = None
        self._plot_theme: Optional[str] = "ggplot"
        self._point_color: Optional[str] = "black"
        self._line_color: Optional[str] = "red"
        self._line_style: Optional[str] = "-"
        self._colormap: Optional[str] = "viridis"

    def set_plot_type(self, plot_type: PlotType) -> "PlotSettingsBuilder":
        self._plot_type = plot_type
        return self

    def set_data_path(self, data_path: Optional[str]) -> "PlotSettingsBuilder":
        self._data_path = data_path
        return self

    def set_sheet_name(self, sheet_name: Optional[str]) -> "PlotSettingsBuilder":
        self._sheet_name = sheet_name
        return self

    def set_x_col(self, col: Optional[str]) -> "PlotSettingsBuilder":
        self._x_col = col
        return self

    def set_y_col(self, col: Optional[str]) -> "PlotSettingsBuilder":
        self._y_col = col
        return self

    def set_z_col(self, col: Optional[str]) -> "PlotSettingsBuilder":
        self._z_col = col
        return self

    def set_x_transform(self, transform: Optional[str]) -> "PlotSettingsBuilder":
        self._x_transform = transform
        return self

    def set_y_transform(self, transform: Optional[str]) -> "PlotSettingsBuilder":
        self._y_transform = transform
        return self

    def set_z_transform(self, transform: Optional[str]) -> "PlotSettingsBuilder":
        self._z_transform = transform
        return self

    def set_params(self, params: Optional[list[str]]) -> "PlotSettingsBuilder":
        self._params = params
        return self

    def set_formula(self, formula: Optional[str]) -> "PlotSettingsBuilder":
        self._formula = formula
        return self

    def set_p0(self, p0: Optional[list[str]]) -> "PlotSettingsBuilder":
        self._p0 = p0
        return self

    def set_plot_theme(self, theme: str) -> "PlotSettingsBuilder":
        self._plot_theme = theme
        return self

    def set_title(self, title: Optional[str]) -> "PlotSettingsBuilder":
        self._title = title
        return self

    def set_x_label(self, label: Optional[str]) -> "PlotSettingsBuilder":
        self._x_label = label
        return self

    def set_y_label(self, label: Optional[str]) -> "PlotSettingsBuilder":
        self._y_label = label
        return self

    def set_z_label(self, label: Optional[str]) -> "PlotSettingsBuilder":
        self._z_label = label
        return self

    def set_point_color(self, color: Optional[str]) -> "PlotSettingsBuilder":
        self._point_color = color
        return self

    def set_line_color(self, color: Optional[str]) -> "PlotSettingsBuilder":
        self._line_color = color
        return self

    def set_line_style(self, style: Optional[str]) -> "PlotSettingsBuilder":
        self._line_style = style
        return self

    def set_colormap(self, colormap: Optional[str]) -> "PlotSettingsBuilder":
        self._colormap = colormap
        return self

    def is_ready(self) -> bool:
        """Check if minimum required fields are set."""
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
        """Returns list of missing required fields for user feedback."""
        missing = []
        if self._data_path is None:
            missing.append("Data Path")
        if self._sheet_name is None:
            missing.append("Sheet Name")
        if self._x_col is None:
            missing.append("X Column")
        if self._y_col is None:
            missing.append("Y Column")
        if self._params is None:
            missing.append("Parameters")
        if self._formula is None:
            missing.append("Formula")
        if self._p0 is None:
            missing.append("Initial States")
        return missing

    def build(self) -> PlotSettings:
        if not self.is_ready():
            raise ValueError(f"Missing fields: {', '.join(self.missing_fields())}")

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
            params=self._params,
            formula=self._formula,
            p0=self._p0,
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
