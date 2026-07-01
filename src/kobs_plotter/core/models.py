"""
Predefined curve fitting models for kobs-plotter.

Domain model definitions for the built-in 2D and 3D fitting templates
shown in the model dropdown. These previously lived in the UI layer
(ui.config_panel) but are pure domain data — they now belong in core
so the compute layer and any future headless callers can reference
them without depending on Qt.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PredefinedModel:
    """A built-in curve fitting template selectable from the UI dropdown."""

    name: str
    """Display name shown in the model dropdown."""

    expr: str
    """Model formula in standard mathematical notation (no NumPy prefix)."""

    params: tuple[str, ...]
    """Parameter symbols excluding the independent variable(s)."""


PREDEFINED_MODELS: dict[str, PredefinedModel] = {
    "Exponential Decay": PredefinedModel(
        "Exponential Decay", "B - A * exp(-k * x)", ("A", "B", "k")
    ),
    "Exponential": PredefinedModel("Exponential", "A * exp(k * x)", ("A", "k")),
    "Linear": PredefinedModel("Linear", "m * x + b", ("m", "b")),
    "Quadratic": PredefinedModel(
        "Quadratic", "a * x**2 + b * x + c", ("a", "b", "c")
    ),
    "Cubic": PredefinedModel(
        "Cubic", "a * x**3 + b * x**2 + c * x + d", ("a", "b", "c", "d")
    ),
    "Logarithmic": PredefinedModel("Logarithmic", "a + b * log(x)", ("a", "b")),
    "Sigmoidal": PredefinedModel(
        "Sigmoidal", "L / (1 + exp(-k * (x - a)))", ("L", "a", "k")
    ),
}
"""Predefined 2D curve fitting models keyed by display name."""


PREDEFINED_MODELS_3D: dict[str, PredefinedModel] = {
    "Plane": PredefinedModel("Plane", "A * x + B * y + C", ("A", "B", "C")),
    "Parabolic": PredefinedModel(
        "Parabolic", "A * x**2 + B * y**2 + C", ("A", "B", "C")
    ),
    "Gaussian": PredefinedModel(
        "Gaussian",
        "A * exp(-((x - x0)**2 / (2*sx**2) + (y - y0)**2 / (2*sy**2)))",
        ("A", "x0", "sx", "y0", "sy"),
    ),
    "Power Law": PredefinedModel("Power Law", "A * x**m * y**n", ("A", "m", "n")),
    "Arrhenius": PredefinedModel(
        "Arrhenius", "A * exp(-Ea / (R * x)) * y**n", ("A", "Ea", "R", "n")
    ),
    "Saddle": PredefinedModel("Saddle", "A * x**2 - B * y**2 + C", ("A", "B", "C")),
}
"""Predefined 3D surface fitting models keyed by display name."""
