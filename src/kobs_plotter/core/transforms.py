from typing import Optional

import numpy as np


def apply_transform(
    expr: Optional[str],
    namespace: dict,
    label: str,
) -> np.ndarray:
    """
    Evaluate a user-supplied NumPy transform expression.

    Args:
        expr:      the transform expression string e.g. 'np.log(x)'
        namespace: dict of variables available to eval e.g. {'x': x, 'np': np}
        label:     human readable name of the variable for error messages

    Returns:
        Transformed numpy array or None if expr is empty.

    Raises:
        ValueError: if the expression is invalid or does not return a numpy array.
    """

    # Restrict builtins so user-supplied expressions cannot invoke arbitrary
    # Python (e.g. open, exec, __import__). Only the names in `namespace`
    # — np and the axis arrays — are available. np.* functions remain
    # accessible because np is exposed explicitly.
    safe_globals: dict = {"__builtins__": {}}

    if not expr or not expr.strip():
        return namespace[label]

    try:
        expr = expr or label
        result = eval(expr, safe_globals, namespace)
    except Exception as e:
        raise ValueError(f'Invalid transform: "{expr}"') from e

    if not isinstance(result, np.ndarray):
        raise ValueError(
            f'Transform "{expr}" did not return a valid numpy array for {label}.'
        )
    if np.any(np.isnan(result)):
        raise ValueError(
            f'Transform "{expr}" produced NaN values in numpy array for {label}.'
        )

    return result
