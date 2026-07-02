from kobs_plotter.core.settings import PlotSettings
from kobs_plotter.core.strategies import STRATEGIES
from kobs_plotter.core.types import PlotDataSeries


def load_data(settings: PlotSettings) -> PlotDataSeries:
    """
    Load data from the Excel file specified in settings and apply any
    user-defined transforms via the active plot-type strategy.

    The Excel file is always read fresh from disk so any edits the
    user makes between compute runs are picked up automatically.

    Args:
        settings: immutable PlotSettings object from the builder.

    Returns:
        PlotDataSeries containing the (transformed) x, y, and optional z arrays.

    Raises:
        FileNotFoundError: if the Excel file does not exist.
        RuntimeError: if the Excel file cannot be read.
    """
    import pandas as pd

    try:
        df = pd.read_excel(settings.data_path, sheet_name=settings.sheet_name)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"File not found: {settings.data_path}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to read Excel file: {e}") from e

    strategy = STRATEGIES[settings.plot_type]
    return strategy.load_series(settings, df)
