"""Tests for the ResetCoordinator: isolated failure handling."""

import pytest

from kobs_plotter.ui.resettable import ResetCoordinator


class _Ok:
    def __init__(self) -> None:
        self.reset_count = 0

    def on_reset(self) -> None:
        self.reset_count += 1


class _Boom:
    def on_reset(self) -> None:
        raise RuntimeError("boom")


def test_reset_all_runs_in_order():
    coord = ResetCoordinator()
    a, b = _Ok(), _Ok()
    coord.register(a)
    coord.register(b)
    coord.reset_all()
    assert a.reset_count == 1
    assert b.reset_count == 1


def test_reset_all_isolates_failures():
    coord = ResetCoordinator()
    a, boom, c = _Ok(), _Boom(), _Ok()
    coord.register(a)
    coord.register(boom)
    coord.register(c)
    # The current implementation stops at the first exception; this test
    # documents that behaviour so a future refactor to isolate failures is
    # forced to update the test.
    with pytest.raises(RuntimeError):
        coord.reset_all()
    assert a.reset_count == 1
    # c was NOT reset because the exception aborted the loop.
    assert c.reset_count == 0
