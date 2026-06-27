from typing import Optional

from numpy import ndarray


def apply_transform(
    expr: Optional[str],
    namespace: dict,
    label: str,
) -> Optional[ndarray]:
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
    if not expr or not expr.strip():
        return None

    try:
        result = eval(expr, namespace)
    except Exception:
        raise ValueError(f'Invalid transform: "{expr}"')

    if not isinstance(result, ndarray):
        raise ValueError(
            f'Transform "{expr}" did not return a valid numpy array for {label}.'
        )

    return result
