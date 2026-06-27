from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from kobs_plotter.core.settings import PlotSettings, PlotType
from kobs_plotter.core.transforms import apply_transform


@dataclass(frozen=True)
class PlotDataSeries:
    """
    Immutable container for the raw (and optionally transformed)
    data series passed to the fitting and plotting layer.
    """

    x: np.ndarray
    y: np.ndarray
    z: Optional[np.ndarray]


def load_data(settings: PlotSettings) -> PlotDataSeries:
    """
    Load data from the Excel file specified in settings, apply any
    user-defined transforms, and return a PlotDataSeries.

    The Excel file is always read fresh from disk so any edits the
    user makes between compute runs are picked up automatically.

    Args:
        settings: immutable PlotSettings object from the builder.

    Returns:
        PlotDataSeries containing the (transformed) x, y, and optional z arrays.

    Raises:
        FileNotFoundError: if the Excel file does not exist.
        ValueError: if a transform expression is invalid or does not
                    return a numpy array.
    """
    try:
        df = pd.read_excel(settings.data_path, sheet_name=settings.sheet_name)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {settings.data_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to read Excel file: {e}")

    x = np.array(df[settings.x_col], dtype=float)
    y = np.array(df[settings.y_col], dtype=float)
    z = None

    if settings.plot_type == PlotType.SURFACE_3D:
        z = np.array(df[settings.z_col], dtype=float)

    namespace = {"x": x, "y": y, "z": z, "np": np}

    x_prime = apply_transform(settings.x_transform, namespace, "x") or x
    y_prime = apply_transform(settings.y_transform, namespace, "y") or y

    if settings.plot_type == PlotType.SURFACE_3D:
        z_prime = apply_transform(settings.z_transform, namespace, "z") or z
        z = z_prime

    x = x_prime
    y = y_prime

    return PlotDataSeries(x, y, z)
