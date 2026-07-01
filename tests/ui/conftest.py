"""
Pytest fixtures for the kobs-plotter UI test suite.

Provides a real :class:`QApplication` (created once per session), a per-test
:class:`MainWindow`, a small in-memory xlsx fixture, and helpers for waiting
on background :class:`QThread` workers via :func:`qtbot`.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Make the app headless-friendly on CI even without an X server.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from kobs_plotter.core.service import ComputeService
from kobs_plotter.ui.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    """Create a singleton QApplication for the whole session (pytest-qt also
    provides one via the ``qapp`` fixture, but we expose our own so the
    offscreen platform is set before it constructs)."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def main_window(qtbot) -> Iterator[MainWindow]:
    """A fresh, isolated :class:`MainWindow` per test."""
    w = MainWindow(ComputeService())
    qtbot.addWidget(w)
    yield w
    # Drain any lingering workers.
    if w.controller._worker is not None and w.controller._worker.isRunning():
        w.controller._worker.wait(2000)
    w.close()


@pytest.fixture
def sample_xlsx(tmp_path) -> Path:
    """A small .xlsx with an Exponential-Decay-shaped dataset (t, signal)."""
    t = np.linspace(0, 5, 20)
    A, B, k = 2.0, 0.5, 0.8
    signal = B - A * np.exp(-k * t)
    df = pd.DataFrame({"t": t, "signal": signal})
    path = tmp_path / "sample.xlsx"
    df.to_excel(path, index=False)
    return path


@pytest.fixture
def multi_sheet_xlsx(tmp_path) -> Path:
    """An .xlsx with two sheets of different column counts."""
    path = tmp_path / "multi.xlsx"
    with pd.ExcelWriter(path) as xl:
        pd.DataFrame({"a": np.arange(5), "b": np.arange(5) * 2}).to_excel(
            xl, sheet_name="Two", index=False
        )
        pd.DataFrame(
            {"x": np.arange(5), "y": np.arange(5) ** 2, "z": np.arange(5) + 10}
        ).to_excel(xl, sheet_name="Three", index=False)


def wait_worker(qtbot, controller, timeout=10000):
    """Block (processing events) until the controller's worker finishes."""
    worker = controller._worker
    if worker is None:
        return
    qtbot.waitUntil(lambda: not worker.isRunning(), timeout=timeout)
