"""
Reset coordination for kobs-plotter panels and windows.

Defines a Resettable Protocol for any widget exposing an on_reset()
method, and a ResetCoordinator that fans a single reset trigger out to
all registered resettables. Replaces the previous chain of N separate
reset_btn.clicked.connect(panel.on_reset) lines in MainWindow, so adding
a new panel only requires one register() call instead of a new signal
connection.
"""

from typing import Protocol, TypeVar, runtime_checkable


@runtime_checkable
class Resettable(Protocol):
    """Anything that can be reset to its initial state."""

    def on_reset(self) -> None:
        ...


R = TypeVar("R", bound=Resettable)


class ResetCoordinator:
    """ Fans out a single reset trigger to all registered resettables. """

    def __init__(self) -> None:
        self._resettables: list[Resettable] = []

    def register(self, resettable: R) -> R:
        """
        Register a resettable and return it for convenient chained assignment.

        The bound TypeVar preserves the concrete type at the call site so
        callers retain access to widget-specific members.

        Example::

            self.file_panel = coordinator.register(FilePanel(builder))
        """
        self._resettables.append(resettable)
        return resettable

    def reset_all(self) -> None:
        """Invoke on_reset() on every registered resettable, in registration order."""
        for resettable in self._resettables:
            resettable.on_reset()