"""
Plot-type strategy registry for kobs-plotter.

Each concrete PlotStrategy encapsulates the plot-type-specific behaviour
that was previously spread across data_loader, modelling, and plotting as
if-plot_type branches. The dispatcher modules look up the strategy via
the STRATEGIES registry and delegate to its methods.
"""

from kobs_plotter.core.settings import PlotType
from kobs_plotter.core.strategies.base import PlotStrategy
from kobs_plotter.core.strategies.scatter_line import ScatterLineStrategy
from kobs_plotter.core.strategies.surface_3d import Surface3DStrategy

STRATEGIES: dict[PlotType, PlotStrategy] = {
    PlotType.SCATTER_LINE: ScatterLineStrategy(),
    PlotType.SURFACE_3D: Surface3DStrategy(),
}

__all__ = ["PlotStrategy", "ScatterLineStrategy", "Surface3DStrategy", "STRATEGIES"]
