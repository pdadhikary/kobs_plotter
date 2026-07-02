"""
Plot-type strategy registry for kobs-plotter.

Each concrete PlotStrategy encapsulates the plot-type-specific behaviour
that was previously spread across data_loader, modelling, and plotting as
if-plot_type branches. The dispatcher modules look up the strategy via
the STRATEGIES registry and delegate to its methods.

The concrete strategy modules are imported on first access so that simply
importing this package (pulled in transitively by modelling / data_loader
/ plotting during application startup) does not eagerly load pandas,
scipy, and sympy. Strategy instances are created once and cached.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from functools import cache

from kobs_plotter.core.settings import PlotType
from kobs_plotter.core.strategies.base import PlotStrategy


@cache
def _scatter_line() -> PlotStrategy:
    from kobs_plotter.core.strategies.scatter_line import ScatterLineStrategy

    return ScatterLineStrategy()


@cache
def _surface_3d() -> PlotStrategy:
    from kobs_plotter.core.strategies.surface_3d import Surface3DStrategy

    return Surface3DStrategy()


class _LazyStrategyRegistry:
    """A Mapping[PlotType, PlotStrategy] that imports strategies on first use."""

    def __getitem__(self, key: PlotType) -> PlotStrategy:
        try:
            factory = _FACTORIES[key]
        except KeyError:
            raise KeyError(key) from None
        return factory()

    def __contains__(self, key: object) -> bool:
        return key in _FACTORIES

    def __iter__(self) -> Iterator[PlotType]:
        return iter(_FACTORIES)

    def keys(self) -> tuple[PlotType, ...]:
        return tuple(_FACTORIES)

    def values(self) -> list[PlotStrategy]:
        return [factory() for factory in _FACTORIES.values()]

    def items(self) -> list[tuple[PlotType, PlotStrategy]]:
        return [(key, factory()) for key, factory in _FACTORIES.items()]


_FACTORIES: dict[PlotType, Callable[[], PlotStrategy]] = {
    PlotType.SCATTER_LINE: _scatter_line,
    PlotType.SURFACE_3D: _surface_3d,
}

STRATEGIES: _LazyStrategyRegistry = _LazyStrategyRegistry()

__all__ = ["PlotStrategy", "STRATEGIES"]
