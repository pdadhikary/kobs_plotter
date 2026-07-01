"""
Input validation helpers for kobs-plotter UI.

Centralises user-input parsing and validation that previously lived inline
in the panels (notably ``ConfigPanel._on_params_changed``). Two kinds of
helpers live here:

- **Pure functions** (``parse_param_hints``, ``params_p0_match``,
  ``is_valid_color_string``, ``is_valid_formula_syntax``) that are pure
  Python and unit-testable without Qt. They return parsed results or
  validation errors rather than mutating widgets.

- **Qt ``QValidator`` subclasses** that wrap the pure functions for direct
  use on ``QLineEdit`` widgets. A failed validation paints the line edit
  red via a stylesheet property (``invalid`` state) so the user gets
  immediate inline feedback without modal dialogs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from PySide6.QtGui import QValidator
from PySide6.QtWidgets import QLineEdit

# Names that cannot be used as parameter symbols because they collide with
# the independent variable(s) the fitting engine injects into the eval
# namespace (see core.modelling._resolve_p0 and core.transforms.apply_transform).
_FORBIDDEN_PARAM_NAMES = {"x", "y", "z"}


@dataclass(frozen=True)
class ParamHints:
    """Parsed result of ``parse_param_hints``.

    ``params`` and ``p0`` always have the same length: every parameter has
    exactly one initial-value expression (default ``"1.0"`` when the user
    omitted it). ``errors`` is non-empty when malformed tokens were found;
    the parser still returns best-effort partial results so the UI can show
    partial state.
    """

    params: list[str]
    p0: list[str]
    errors: list[str]


def parse_param_hints(text: str) -> ParamHints:
    """
    Parse a comma-separated parameter hint string into (params, p0) lists.

    Each token is one of:

    - ``"A"``         -> param ``A``, default initial value ``"1.0"``
    - ``"A=2.0"``     -> param ``A``, initial value ``"2.0"``
    - ``"A=np.max(y)"`` -> param ``A``, initial value expression ``"np.max(y)"``

    Empty tokens (trailing commas, blank input) are skipped. A token with
    more than one ``=`` is malformed; a parameter named ``x``, ``y``, or
    ``z`` is rejected (it collides with the axis arrays). Errors are
    collected and returned alongside the best-effort parse.

    Args:
        text: raw text from the parameters QLineEdit.

    Returns:
        :class:`ParamHints` with params, p0, and any errors.
    """
    if not text or not text.strip():
        return ParamHints(params=[], p0=[], errors=[])

    params: list[str] = []
    p0: list[str] = []
    errors: list[str] = []

    for token in text.split(","):
        token = token.strip()
        if not token:
            continue

        if "=" in token:
            name, _, expr = token.partition("=")
            name = name.strip()
            expr = expr.strip()
        else:
            name = token
            expr = "1.0"

        if not name:
            errors.append(f'Malformed token: "{token}"')
            continue
        if "=" in token and token.count("=") > 1:
            errors.append(f'Token has multiple "=": "{token}"')
            continue
        if name in _FORBIDDEN_PARAM_NAMES:
            errors.append(
                f'Parameter "{name}" shadows an axis variable; use a different name.'
            )
            continue

        params.append(name)
        p0.append(expr or "1.0")

    # Duplicate parameter names are a real footgun for curve_fit.
    seen: set[str] = set()
    for p in params:
        if p in seen:
            errors.append(f'Duplicate parameter: "{p}"')
        seen.add(p)

    return ParamHints(params=params, p0=p0, errors=errors)


def params_p0_match(params: list[str], p0: list[str]) -> bool:
    """True iff the two lists have the same length (one p0 per param)."""
    return len(params) == len(p0)


def is_valid_color_string(color: str) -> bool:
    """
    Light-weight pre-check for matplotlib color strings.

    matplotlib accepts named colors, single-letter codes, and CSS hex
    strings — fully validating means asking matplotlib. We only reject
    obviously-bad input (empty, whitespace-only, names with obviously
    illegal characters) so we don't shadow matplotlib's permissive parser.
    """
    if not color or not color.strip():
        return False
    c = color.strip()
    if re.fullmatch(r"#[0-9a-fA-F]{3,8}", c):
        return True
    if re.fullmatch(r"(?:rgba?|tab:)?[\w]+", c) and " " not in c:
        return True
    return False


def is_valid_formula_syntax(formula: str) -> str | None:
    """
    Sanity-check a custom SymPy formula about to be sent to lambdify.

    Returns ``None`` if the formula passes the light syntactic check, or
    a human-readable error string otherwise. We do not fully parse with
    SymPy here (expensive and side-effecty); we only catch the common
    mistakes the README warns about (``np.`` prefixes, empty input).
    """
    if not formula or not formula.strip():
        return "Formula is empty."
    if "np." in formula or "numpy." in formula:
        return (
            "Formula must use plain math functions (exp, log, …), not NumPy "
            "prefixes (np.exp, numpy.log)."
        )
    return None


# ── Qt validators ──────────────────────────────────────────────────


class _InvalidatingValidator(QValidator):
    """Base class that toggles a red stylesheet when validation fails."""

    INVALID_QSS = "QLineEdit { border: 1px solid #ff5555; }"

    def _set_invalid(self, widget: QLineEdit, invalid: bool) -> None:
        widget.setStyleSheet(self.INVALID_QSS if invalid else "")


class ParamHintsValidator(_InvalidatingValidator):
    """Validate the parameters QLineEdit as the user types.

    Emits ``Intermediate`` (with red border) when malformed input is
    detected so the user sees the problem immediately; ``Acceptable`` when
    clean. Pushing the parsed (params, p0) lists to the builder is the
    panel's responsibility (via the ``textChanged`` slot) — this validator
    only paints the inline red-border feedback.
    """

    def validate(self, text: str, cursor_pos: int) -> QValidator.State:
        hints = parse_param_hints(text)
        invalid = bool(hints.errors)
        parent = self.parent()
        if isinstance(parent, QLineEdit):
            self._set_invalid(parent, invalid)
        return QValidator.State.Intermediate if invalid else QValidator.State.Acceptable


class ColorStringValidator(_InvalidatingValidator):
    """Validate a free-text matplotlib color string."""

    def validate(self, text: str, cursor_pos: int) -> QValidator.State:
        ok = is_valid_color_string(text)
        parent = self.parent()
        if isinstance(parent, QLineEdit):
            self._set_invalid(parent, not ok)
        return QValidator.State.Acceptable if ok else QValidator.State.Intermediate


class FormulaValidator(_InvalidatingValidator):
    """Light syntax check on a custom model formula line edit."""

    def validate(self, text: str, cursor_pos: int) -> QValidator.State:
        err = is_valid_formula_syntax(text)
        parent = self.parent()
        if isinstance(parent, QLineEdit):
            self._set_invalid(parent, err is not None)
        return QValidator.State.Intermediate if err is not None else QValidator.State.Acceptable
