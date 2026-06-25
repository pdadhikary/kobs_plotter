from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from kobs_plotter.core.settings import PlotSettingsBuilder
from kobs_plotter.ui.ui_helpers import divider, field_label, prefix_label, section_label

PREDEFINED_MODELS = {
    "Exponential Decay": {
        "expr": "B - A * exp(-k * x)",
        "params": ["A", "B", "k"],
    },
    "Exponential": {"expr": "A * exp(k * x)", "params": ["A", "k"]},
    "Linear": {
        "expr": "m * x + b",
        "params": ["m", "b"],
    },
    "Quadratic": {
        "expr": "a * x**2 + b * x + c",
        "params": ["a", "b", "c"],
    },
    "Cubic": {
        "expr": "a * x**3 + b * x**2 + c * x + d",
        "params": ["a", "b", "c", "d"],
    },
    "Logarithmic": {
        "expr": "a + b * log(x)",
        "params": ["a", "b"],
    },
    "Sigmoidal": {
        "expr": "L / (1 + exp(-k * (x - a)))",
        "params": ["L", "a", "k"],
    },
}

PREDEFINED_MODELS_3D = {
    "Plane": {
        "expr": "A * x + B * y + C",
        "params": ["A", "B", "C"],
    },
    "Parabolic": {
        "expr": "A * x**2 + B * y**2 + C",
        "params": ["A", "B", "C"],
    },
    "Gaussian": {
        "expr": "A * exp(-((x - x0)**2 / (2*sx**2) + (y - y0)**2 / (2*sy**2)))",
        "params": ["A", "x0", "sx", "y0", "sy"],
    },
    "Power Law": {
        "expr": "A * x**m * y**n",
        "params": ["A", "m", "n"],
    },
    "Arrhenius": {
        "expr": "A * exp(-Ea / (R * x)) * y**n",
        "params": ["A", "Ea", "R", "n"],
    },
    "Saddle": {
        "expr": "A * x**2 - B * y**2 + C",
        "params": ["A", "B", "C"],
    },
}


class ConfigPanel(QWidget):
    def __init__(self, settings_builder: PlotSettingsBuilder):
        super().__init__()
        self.setMaximumWidth(320)
        self.settings_builder = settings_builder
        self.is_3d = False

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── Data transformation ──────────────────────────────
        layout.addWidget(section_label("Data transformation"))

        layout.addWidget(field_label("Transform X"))
        x_row = QHBoxLayout()
        x_row.addWidget(prefix_label("x' ="))
        self.x_transform = QLineEdit()
        self.x_transform.setPlaceholderText("np.log(x)")
        self.x_transform.setFont(QFont("monospace", 9))
        self.x_transform.textChanged.connect(self.settings_builder.set_x_transform)
        x_row.addWidget(self.x_transform)
        layout.addLayout(x_row)

        layout.addWidget(field_label("Transform Y"))
        y_row = QHBoxLayout()
        y_row.addWidget(prefix_label("y' ="))
        self.y_transform = QLineEdit()
        self.y_transform.setPlaceholderText("y / 1000")
        self.y_transform.setFont(QFont("monospace", 9))
        self.y_transform.textChanged.connect(self.settings_builder.set_y_transform)
        y_row.addWidget(self.y_transform)
        layout.addLayout(y_row)

        # ── Z transform (3D only, hidden by default) ─────────
        self.z_transform_widget = QWidget()
        z_transform_layout = QVBoxLayout(self.z_transform_widget)
        z_transform_layout.setContentsMargins(0, 0, 0, 0)
        z_transform_layout.setSpacing(4)
        z_transform_layout.addWidget(field_label("Transform Z"))
        z_row = QHBoxLayout()
        z_row.addWidget(prefix_label("z' ="))
        self.z_transform = QLineEdit()
        self.z_transform.setPlaceholderText("np.log(z)")
        self.z_transform.setFont(QFont("monospace", 9))
        self.z_transform.textChanged.connect(self.settings_builder.set_z_transform)
        z_row.addWidget(self.z_transform)
        z_transform_layout.addLayout(z_row)
        self.z_transform_widget.setVisible(False)
        layout.addWidget(self.z_transform_widget)

        layout.addWidget(divider())

        # ── Model selection ──────────────────────────────────
        layout.addWidget(section_label("Model selection"))

        layout.addWidget(field_label("Model"))
        self.model_combo = QComboBox()
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        layout.addWidget(self.model_combo)

        # ── Parameter / formula box ──────────────────────────
        self.param_box = QWidget()
        param_box_layout = QVBoxLayout(self.param_box)
        param_box_layout.setContentsMargins(12, 12, 12, 12)
        param_box_layout.setSpacing(10)
        self.param_box.setStyleSheet(
            "QWidget { background: palette(window); "
            "border: 0.5px solid palette(mid); border-radius: 8px; }"
        )
        param_box_layout.addWidget(
            field_label("Parameters (comma separated, exclude x and y)")
        )
        self.params_input = QLineEdit()
        self.params_input.setPlaceholderText("A, B, k")
        self.params_input.setFont(QFont("monospace", 9))
        self.params_input.textChanged.connect(self._on_params_changed)
        param_box_layout.addWidget(self.params_input)

        param_box_layout.addWidget(field_label("Formula"))
        formula_row = QHBoxLayout()
        self.formula_prefix = prefix_label("y =")
        formula_row.addWidget(self.formula_prefix)
        self.formula_input = QLineEdit()
        self.formula_input.setPlaceholderText("B - A * exp(-k * x)")
        self.formula_input.setFont(QFont("monospace", 9))
        self.formula_input.textChanged.connect(self.settings_builder.set_formula)
        formula_row.addWidget(self.formula_input)
        param_box_layout.addLayout(formula_row)
        layout.addWidget(self.param_box)
        layout.addStretch()

        # Populate with 2D models by default
        self._populate_model_combo()

    def set_mode(self, is_3d: bool):
        self.is_3d = is_3d
        self.z_transform_widget.setVisible(is_3d)
        self.formula_prefix.setText("z =" if is_3d else "y =")
        self._populate_model_combo()

    def _populate_model_combo(self):
        """Populate model combo with 2D or 3D models based on current mode."""
        models = PREDEFINED_MODELS_3D if self.is_3d else PREDEFINED_MODELS
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        self.model_combo.addItems([*models.keys(), "Custom"])
        self.model_combo.blockSignals(False)
        self._on_model_changed(self.model_combo.currentText())

    def _on_params_changed(self, param_text: str):
        tokens = param_text.split(",")
        params = []
        p0 = []

        for token in tokens:
            if "=" in token:
                param, expr = token.split("=", 1)
                params.append(param.strip())
                p0.append(expr.strip() or "1.0")
            else:
                params.append(token.strip())
                p0.append("1.0")

        params = [p for p in params if p]
        self.settings_builder.set_params(params)
        self.settings_builder.set_p0(p0)

    def _on_model_changed(self, name: str):
        models = PREDEFINED_MODELS_3D if self.is_3d else PREDEFINED_MODELS

        if name == "Custom":
            self.params_input.setText("")
            self.settings_builder.set_params(None)
            self.formula_input.setText("")
            self.settings_builder.set_formula(None)
        elif name in models:
            params = models[name]["params"]
            expr = models[name]["expr"]
            self.params_input.setText(", ".join(params))
            self.settings_builder.set_params(params)
            self.formula_input.setText(expr)
            self.settings_builder.set_formula(expr)

    def on_reset(self):
        self.x_transform.setText("")
        self.y_transform.setText("")
        self.z_transform.setText("")
        self.params_input.setText("")
        self.formula_input.setText("")
        self.is_3d = False
        self.formula_prefix.setText("y =")
        self.z_transform_widget.setVisible(False)
        self._populate_model_combo()
