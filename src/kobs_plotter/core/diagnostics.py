"""
Diagnostic plot types for kobs-plotter.

Defines the PlotDiagnosticType enum used by both the core computation
layer and the UI layer to distinguish the main fit plot from residual
and Q-Q diagnostic plots.
"""

from enum import Enum, auto


class PlotDiagnosticType(Enum):
    """Kind of plot to render after a compute run."""

    PLOT = auto()
    """Main fitted curve / surface plot."""

    RESIDUAL = auto()
    """Residual scatter plot (residuals vs independent variable)."""

    QQ_PLOT = auto()
    """Normal Q-Q plot of the fit residuals."""
