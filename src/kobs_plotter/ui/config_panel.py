from math import exp

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
)
from PySide6.QtGui import QFont

from kobs_plotter.ui.ui_helpers import section_label, field_label, prefix_label, divider
from kobs_plotter.core.settings import PlotSettingsBuilder


PREDEFINED_MODELS = {
    "Exponential — y = B - A·exp(-k·x)": {
        "expr": "B - A * exp(-k * x)",
        "params": ["A", "B", "k"],
    },
    "Linear — y = mx + b": {
        "expr": "m * x + b",
        "params": ["m", "b"],
    },
}


class ConfigPanel(QWidget):
    def __init__(self, settings_builder: PlotSettingsBuilder):
        super().__init__()
        self.setMaximumWidth(320)
        self.settings_builder = settings_builder

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

        layout.addWidget(divider())

        # ── Model selection ──────────────────────────────────
        layout.addWidget(section_label("Model selection"))

        layout.addWidget(field_label("Model"))
        self.model_combo = QComboBox()
        self.model_combo.addItems([*PREDEFINED_MODELS.keys(), "Custom"])
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        layout.addWidget(self.model_combo)

        # ── Custom model box (hidden by default) ─────────────
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
        formula_row.addWidget(prefix_label("y ="))
        self.formula_input = QLineEdit()
        self.formula_input.setPlaceholderText("B - A * exp(-k * x)")
        self.formula_input.setFont(QFont("monospace", 9))
        self.formula_input.textChanged.connect(self.settings_builder.set_formula)
        formula_row.addWidget(self.formula_input)
        param_box_layout.addLayout(formula_row)
        layout.addWidget(self.param_box)
        layout.addStretch()

        self._on_model_changed(self.model_combo.currentText())

    def _on_params_changed(self, param_text: str):
        tokens = param_text.split(",")
        params = []
        p0 = []

        for token in tokens:
            if "=" in token:
                param, expr = token.split("=")
                params.append(param.strip())
                p0.append(expr.strip() or "1.0")
            else:
                params.append(token.strip())
                p0.append("1.0")

        self.settings_builder.set_params(params)
        self.settings_builder.set_p0(p0)

    def _on_model_changed(self, name: str):
        if name == "Custom":
            self.params_input.setText("")
            self.settings_builder.set_params(None)
            self.formula_input.setText("")
            self.settings_builder.set_formula(None)
        elif name in PREDEFINED_MODELS:
            self.params_input.setText(", ".join(PREDEFINED_MODELS[name]["params"]))
            self.settings_builder.set_params(PREDEFINED_MODELS[name]["params"])
            self.formula_input.setText(PREDEFINED_MODELS[name]["expr"])
            self.settings_builder.set_formula(PREDEFINED_MODELS[name]["expr"])
