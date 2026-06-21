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
    def __init__(self):
        super().__init__()
        self.setMaximumWidth(320)

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
        # TODO: connect to builder.set_x_transform
        x_row.addWidget(self.x_transform)
        layout.addLayout(x_row)

        layout.addWidget(field_label("Transform Y"))
        y_row = QHBoxLayout()
        y_row.addWidget(prefix_label("y' ="))
        self.y_transform = QLineEdit()
        self.y_transform.setPlaceholderText("y / 1000")
        self.y_transform.setFont(QFont("monospace", 9))
        # TODO: connect to builder.set_y_transform
        y_row.addWidget(self.y_transform)
        layout.addLayout(y_row)

        layout.addWidget(divider())

        # ── Model selection ──────────────────────────────────
        layout.addWidget(section_label("Model selection"))

        layout.addWidget(field_label("Model"))
        self.model_combo = QComboBox()
        self.model_combo.addItems([*PREDEFINED_MODELS.keys(), "Custom"])
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        # TODO: on predefined selection push PREDEFINED_MODELS[name] to builder
        layout.addWidget(self.model_combo)

        # ── Custom model box (hidden by default) ─────────────
        self.custom_box = QWidget()
        custom_layout = QVBoxLayout(self.custom_box)
        custom_layout.setContentsMargins(12, 12, 12, 12)
        custom_layout.setSpacing(10)
        self.custom_box.setStyleSheet(
            "QWidget { background: palette(window); "
            "border: 0.5px solid palette(mid); border-radius: 8px; }"
        )

        custom_layout.addWidget(field_label("Model title"))
        self.model_title_input = QLineEdit()
        self.model_title_input.setPlaceholderText("e.g. Langmuir isotherm")
        custom_layout.addWidget(self.model_title_input)

        custom_layout.addWidget(
            field_label("Parameters (comma separated, exclude x and y)")
        )
        self.params_input = QLineEdit()
        self.params_input.setPlaceholderText("A, B, k")
        self.params_input.setFont(QFont("monospace", 9))
        # TODO: connect to builder.set_indep_vars (parse comma separated string)
        custom_layout.addWidget(self.params_input)

        custom_layout.addWidget(field_label("Formula"))
        formula_row = QHBoxLayout()
        formula_row.addWidget(prefix_label("y ="))
        self.formula_input = QLineEdit()
        self.formula_input.setPlaceholderText("B - A * exp(-k * x)")
        self.formula_input.setFont(QFont("monospace", 9))
        # TODO: connect to builder.set_expr
        formula_row.addWidget(self.formula_input)
        custom_layout.addLayout(formula_row)

        self.save_btn = QPushButton("Save model")
        # TODO: implement _save_custom_model to persist to JSON in user config dir
        custom_layout.addWidget(self.save_btn)

        self.custom_box.setVisible(False)
        layout.addWidget(self.custom_box)
        layout.addStretch()

        self._on_model_changed(self.model_combo.currentText())

    def _on_model_changed(self, name: str):
        self.custom_box.setVisible(name == "Custom")
        # TODO: on predefined selection, push PREDEFINED_MODELS[name] to builder
