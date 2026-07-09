"""
Configuration panel UI component for kobs-plotter.

Centre-left panel: data transformation expressions, model selection
(predefined or custom), and parameter / formula definition. All field
mutations are pushed into :class:`AppState`.

Hardening relative to the previous version:

- Parameter parsing is extracted to :func:`validators.parse_param_hints`
  and the line edit carries a :class:`ParamHintsValidator` so malformed
  input is highlighted inline.
- The custom-formula line edit carries a :class:`FormulaValidator`
  that rejects ``np.`` / ``numpy.`` prefixes inline (the #1 user footgun
  per README) instead of failing only at fit time.
- Selecting another model after editing the Custom inputs no longer
  silently destroys work: the last custom (params, formula) is cached
  and restored when the user re-selects Custom.
- Every field has a ``ToolTip`` and ``WhatThis`` describing the
  NumPy-vs-SymPy distinction that the README is so careful about.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from kobs_plotter.core.models import PREDEFINED_MODELS, PREDEFINED_MODELS_3D
from kobs_plotter.core.types import PlotType
from kobs_plotter.ui.ui_helpers import (
    divider,
    field_label,
    mono_font,
    prefix_label,
    section_label,
)
from kobs_plotter.ui.validators import (
    ParamHintsValidator,
    parse_param_hints,
)
from kobs_plotter.ui.viewmodel import AppState
from kobs_plotter.ui.widgets import CollapsibleSection

# Tooltips shared between the transform fields and the formula field — the
# single most important UX hint the README is careful about.
_TRANSFORM_TIP = (
    "NumPy expression applied before fitting. The axis array is available "
    "as its lower-case name (x, y, z) and `np` is in scope. Example: np.log(y)"
)
_FORMULA_TIP = (
    "Model formula in plain math notation (exp, log, sqrt, sin, cos). "
    "Do NOT use np.* or numpy.* prefixes here."
)
_PARAMS_TIP = (
    "Comma-separated parameter symbols (everything except x, y, z). "
    "Optionally set initial values with '=': A=np.min(y), B, k"
)


class ConfigPanel(QWidget):
    """Data transformation + model configuration panel."""

    def __init__(self, state: AppState):
        super().__init__()
        self.state = state
        self.setMaximumWidth(360)
        self.mode: PlotType = PlotType.SCATTER_LINE
        # Cache of the user's last Custom (params, formula) so re-selecting
        # Custom restores their work instead of silently wiping it. Only
        # updated when the *currently selected* model is Custom.
        self._custom_cache: tuple[str, str] = ("", "")
        self._current_model: str = ""
        # Per-X-column transform line edits owned by the multivar section.
        self._mv_transform_inputs: list[QLineEdit] = []

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── Data transformation (single-variable) ───────────────
        layout.addWidget(section_label("Data transformation"))

        self.x_transform_widget = QWidget()
        xt_layout = QVBoxLayout(self.x_transform_widget)
        xt_layout.setContentsMargins(0, 0, 0, 0)
        xt_layout.setSpacing(8)
        xt_layout.addWidget(field_label("Transform X"))
        x_row = QHBoxLayout()
        x_row.addWidget(prefix_label("x' ="))
        self.x_transform = QLineEdit()
        self.x_transform.setPlaceholderText("np.log(x)")
        self.x_transform.setFont(mono_font(9))
        self.x_transform.setToolTip(_TRANSFORM_TIP)
        self.x_transform.setWhatsThis(
            "NumPy expression evaluating to a transformed x array. "
            "Available names: x, np. Leave empty to keep x unchanged."
        )
        self.x_transform.textChanged.connect(self.state.set_x_transform)
        x_row.addWidget(self.x_transform)
        xt_layout.addLayout(x_row)
        layout.addWidget(self.x_transform_widget)

        layout.addWidget(field_label("Transform Y"))
        y_row = QHBoxLayout()
        y_row.addWidget(prefix_label("y' ="))
        self.y_transform = QLineEdit()
        self.y_transform.setPlaceholderText("y / 1000")
        self.y_transform.setFont(mono_font(9))
        self.y_transform.setToolTip(_TRANSFORM_TIP)
        self.y_transform.setWhatsThis(
            "NumPy expression evaluating to a transformed y array. "
            "Available names: y, np. Leave empty to keep y unchanged."
        )
        self.y_transform.textChanged.connect(self.state.set_y_transform)
        y_row.addWidget(self.y_transform)
        layout.addLayout(y_row)

        # ── Multivariable section (per-X transforms + read-only formula) ──
        self.mv_widget = QWidget()
        mv_layout = QVBoxLayout(self.mv_widget)
        mv_layout.setContentsMargins(0, 0, 0, 0)
        mv_layout.setSpacing(10)
        mv_layout.addWidget(field_label("Transform independent variables"))
        self._mv_transforms_layout = QVBoxLayout()
        self._mv_transforms_layout.setSpacing(6)
        mv_layout.addLayout(self._mv_transforms_layout)

        mv_layout.addWidget(field_label("Model formula (read-only)"))
        formula_display_row = QHBoxLayout()
        formula_display_row.addWidget(prefix_label("y ="))
        self.mv_formula_display = QLineEdit()
        self.mv_formula_display.setReadOnly(True)
        self.mv_formula_display.setFont(mono_font(9))
        self.mv_formula_display.setText("B_0 + B_1 * X_1")
        self.mv_formula_display.setToolTip(
            "Fixed multivariable regression model. Coefficients are fit "
            "via ordinary least squares; the formula is shown for reference."
        )
        formula_display_row.addWidget(self.mv_formula_display)
        mv_layout.addLayout(formula_display_row)
        self.mv_widget.setVisible(False)
        layout.addWidget(self.mv_widget)

        # ── Z transform (3D only, hidden) ────────────────────────
        self.z_transform_widget = CollapsibleSection()
        self.z_transform_widget.add_widget(field_label("Transform Z"))
        z_row = QHBoxLayout()
        z_row.addWidget(prefix_label("z' ="))
        self.z_transform = QLineEdit()
        self.z_transform.setPlaceholderText("np.log(z)")
        self.z_transform.setFont(mono_font(9))
        self.z_transform.setToolTip(_TRANSFORM_TIP)
        self.z_transform.textChanged.connect(self.state.set_z_transform)
        z_row.addWidget(self.z_transform)
        self.z_transform_widget.add_layout(z_row)
        self.z_transform_widget.setVisible(False)
        layout.addWidget(self.z_transform_widget)

        layout.addWidget(divider())

        # ── Model selection ──────────────────────────────────────
        self.model_section_widget = QWidget()
        model_section_layout = QVBoxLayout(self.model_section_widget)
        model_section_layout.setContentsMargins(0, 0, 0, 0)
        model_section_layout.setSpacing(12)
        model_section_layout.addWidget(section_label("Model selection"))
        model_section_layout.addWidget(field_label("Model"))
        self.model_combo = QComboBox()
        self.model_combo.setToolTip(
            "Predefined 2D / 3D model, or Custom to define your own formula"
        )
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        model_section_layout.addWidget(self.model_combo)

        # ── Parameter / formula box ──────────────────────────────
        self.param_box = QWidget()
        param_box_layout = QVBoxLayout(self.param_box)
        param_box_layout.setContentsMargins(12, 12, 12, 12)
        param_box_layout.setSpacing(10)
        self.param_box.setStyleSheet(
            "QWidget#paramBox { background: palette(window); "
            "border: 1px solid palette(mid); border-radius: 8px; }"
        )
        self.param_box.setObjectName("paramBox")
        param_box_layout.addWidget(field_label("Parameters (comma separated, exclude x and y)"))
        self.params_input = QLineEdit()
        self.params_input.setPlaceholderText("A, B, k")
        self.params_input.setFont(mono_font(9))
        self.params_input.setToolTip(_PARAMS_TIP)
        self.params_input.setWhatsThis(
            "Parameter symbols the optimiser will vary. Use '=' to give an "
            "initial value, e.g. 'A=np.min(y), B, k'. Parameters without '=' "
            "default to 1.0. Initial values strongly affect fit quality."
        )
        self.params_input.setValidator(ParamHintsValidator())
        self.params_input.textChanged.connect(self._on_params_changed)
        self.params_input.textChanged.connect(self._on_custom_text_changed)
        param_box_layout.addWidget(self.params_input)

        param_box_layout.addWidget(field_label("Formula"))
        formula_row = QHBoxLayout()
        self.formula_prefix = prefix_label("y =")
        formula_row.addWidget(self.formula_prefix)
        self.formula_input = QLineEdit()
        self.formula_input.setPlaceholderText("B - A * exp(-k * x)")
        self.formula_input.setFont(mono_font(9))
        self.formula_input.setToolTip(_FORMULA_TIP)
        self.formula_input.setWhatsThis(
            "SymPy-compatible math expression. Use plain math functions "
            "(exp, log, sqrt, sin, cos) NOT numpy.exp. The independent "
            "variable is x (2D) or x and y (3D)."
        )
        # Defer the FormulaValidator until widgets are parented (validators
        # need the parent to read it in validate()).
        self.formula_input.textChanged.connect(self.state.set_formula)
        self.formula_input.textChanged.connect(self._on_custom_text_changed)
        formula_row.addWidget(self.formula_input)
        param_box_layout.addLayout(formula_row)
        model_section_layout.addWidget(self.param_box)
        layout.addWidget(self.model_section_widget)

        # Status line showing parse errors / param-p0 mismatch in real time.
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #ff5555; font-size: 9pt;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        self._populate_model_combo()
        # Attach formula validator now that the line edit is parented.
        from kobs_plotter.ui.validators import FormulaValidator

        self.formula_input.setValidator(FormulaValidator())

    # ── mode switching ───────────────────────────────────────────
    def set_mode(self, mode: PlotType) -> None:
        self.mode = mode
        is_3d = mode == PlotType.SURFACE_3D
        is_mv = mode == PlotType.MULTIVARIABLE_REGRESSION
        self.x_transform_widget.setVisible(not is_mv)
        self.z_transform_widget.setVisible(is_3d)
        self.formula_prefix.setText("z =" if is_3d else "y =")
        self.mv_widget.setVisible(is_mv)
        self.model_section_widget.setVisible(not is_mv)
        if not is_mv:
            # Leaving multivar: drop any per-X transform state so it never
            # gates readiness for the other modes.
            self.state.set_x_transforms(None)
            self._clear_mv_transform_inputs()
        self._populate_model_combo()

    # ── multivar section helpers ──────────────────────────────────
    def multivar_refresh(self, n: int) -> None:
        """Rebuild the per-X transform rows and read-only formula for ``n`` predictors.

        Called by :class:`MainWindow` whenever the multivar X-row list in
        the file panel changes (add/remove/relabel). Per-X transform text
        that the user already typed is preserved across relabelling.
        """
        if self.mode != PlotType.MULTIVARIABLE_REGRESSION:
            return
        self._rebuild_mv_transform_inputs(n)
        self._refresh_mv_formula(n)
        self._push_mv_transforms()

    def _rebuild_mv_transform_inputs(self, n: int) -> None:
        # Preserve existing text where possible (the row index, not the
        # name, is what the user expects to be stable when they add/remove).
        existing = [le.text() for le in self._mv_transform_inputs]
        self._clear_mv_transform_inputs()
        for i in range(n):
            row_widget = QWidget()
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(8)
            row.addWidget(prefix_label(f"X_{i + 1}' ="))
            le = QLineEdit()
            le.setPlaceholderText("np.log(x)")
            le.setFont(mono_font(9))
            le.setToolTip(_TRANSFORM_TIP)
            if i < len(existing):
                le.setText(existing[i])
            le.textChanged.connect(self._push_mv_transforms)
            row.addWidget(le)
            self._mv_transform_inputs.append(le)
            self._mv_transforms_layout.addWidget(row_widget)

    def _clear_mv_transform_inputs(self) -> None:
        while self._mv_transforms_layout.count():
            item = self._mv_transforms_layout.takeAt(0)
            if item is None:
                break
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._mv_transform_inputs = []

    def _refresh_mv_formula(self, n: int) -> None:
        if n <= 0:
            self.mv_formula_display.setText("")
            return
        rhs = " + ".join(f"B_{i} * X_{i}" for i in range(1, n + 1))
        self.mv_formula_display.setText(f"B_0 + {rhs}")

    def _push_mv_transforms(self) -> None:
        if self.mode != PlotType.MULTIVARIABLE_REGRESSION:
            return
        transforms: list[str | None] = [le.text() or None for le in self._mv_transform_inputs]
        self.state.set_x_transforms(transforms)

    # ── model dropdown ────────────────────────────────────────────
    def _populate_model_combo(self) -> None:
        models = PREDEFINED_MODELS_3D if self.mode == PlotType.SURFACE_3D else PREDEFINED_MODELS
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        self.model_combo.addItems([*models.keys(), "Custom"])
        self.model_combo.blockSignals(False)
        self._on_model_changed(self.model_combo.currentText())

    def _on_model_changed(self, name: str) -> None:
        """Apply the selected model, caching/restoring custom inputs.

        The cache holding the user's last Custom (params, formula) is
        refreshed *before* switching away from Custom, and restored when
        switching back — so visiting a predefined model does not destroy
        in-progress Custom work.
        """
        # If we're LEAVING Custom, save the current Custom edits first.
        if self._current_model == "Custom" and (
            self.params_input.text() or self.formula_input.text()
        ):
            self._custom_cache = (
                self.params_input.text(),
                self.formula_input.text(),
            )
        self._current_model = name

        models = PREDEFINED_MODELS_3D if self.mode == PlotType.SURFACE_3D else PREDEFINED_MODELS
        if name == "Custom":
            cached_params, cached_formula = self._custom_cache
            self.params_input.setText(cached_params)
            self.formula_input.setText(cached_formula)
            # Keep the builder consistent even when the cache is empty (-> None).
            parsed = parse_param_hints(cached_params).params
            self.state.set_params(list(parsed) if parsed else None)
            self.state.set_formula(cached_formula or None)
        elif name in models:
            model = models[name]
            self.params_input.setText(", ".join(model.params))
            self.formula_input.setText(model.expr)

    def _on_custom_text_changed(self) -> None:
        """Keep the Custom cache live while the user edits in Custom mode."""
        if self._current_model == "Custom":
            self._custom_cache = (
                self.params_input.text(),
                self.formula_input.text(),
            )

    # ── param parsing ─────────────────────────────────────────────
    def _on_params_changed(self, param_text: str) -> None:
        """Parse parameters, push (params, p0) to state, surface errors."""
        hints = parse_param_hints(param_text)
        self.state.set_params(list(hints.params) if hints.params else None)
        self.state.set_p0(list(hints.p0) if hints.p0 else None)
        if hints.errors:
            self.status_label.setText(hints.errors[0])
        else:
            self.status_label.setText("")

    # ── reset ─────────────────────────────────────────────────────
    def on_reset(self) -> None:
        self.x_transform.setText("")
        self.y_transform.setText("")
        self.z_transform.setText("")
        self.params_input.setText("")
        self.formula_input.setText("")
        self._custom_cache = ("", "")
        self.mode = PlotType.SCATTER_LINE
        self.formula_prefix.setText("y =")
        self.x_transform_widget.setVisible(True)
        self.z_transform_widget.setVisible(False)
        self.mv_widget.setVisible(False)
        self.model_section_widget.setVisible(True)
        self._clear_mv_transform_inputs()
        self.mv_formula_display.setText("B_0 + B_1 * X_1")
        self.status_label.setText("")
        self._populate_model_combo()
