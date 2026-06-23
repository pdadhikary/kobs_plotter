import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd

from kobs_plotter.core.settings import PlotSettings


@dataclass(frozen=True)
class PlotDataSeries:
    x: np.ndarray
    y: np.ndarray


def load_data(settings: PlotSettings) -> PlotDataSeries:
    df = pd.read_excel(settings.data_path, sheet_name=settings.sheet_name)
    x = np.array(df[settings.x_col])
    y = np.array(df[settings.y_col])

    x_prime = None
    y_prime = None
    try:
        if settings.x_transform and settings.x_transform.strip():
            x_prime = eval(settings.x_transform)
    except Exception as e:
        print(f"[error] x transform: {e}", file=sys.stderr)
        raise ValueError(f'Invalid transform: "{settings.x_transform}"')

    if isinstance(x_prime, np.ndarray):
        x = x_prime
    elif settings.x_transform:
        raise ValueError(
            f'Transform "{settings.x_transform}" did not return a valid numpy array.'
        )

    try:
        if settings.y_transform and settings.y_transform.strip():
            y_prime = eval(settings.y_transform)
    except Exception as e:
        print(f"[error] x transform: {e}", file=sys.stderr)
        raise ValueError(f'Invalid tansform: "{settings.y_transform}"')

    if isinstance(y_prime, np.ndarray):
        y = y_prime
    elif settings.y_transform:
        raise ValueError(
            f'Transform "{settings.y_transform}" did not return a valid numpy array.'
        )

    return PlotDataSeries(x, y)
