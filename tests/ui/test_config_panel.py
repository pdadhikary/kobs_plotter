"""Tests for the config panel: param caching, custom preservation, validators."""



def test_predefined_model_populates_inputs(qtbot, main_window):
    cp = main_window.config_panel
    cp.model_combo.setCurrentText("Exponential Decay")
    assert cp.params_input.text() == "A, B, k"
    assert cp.formula_input.text() == "B - A * exp(-k * x)"
    assert main_window.controller.state._params == ["A", "B", "k"]
    assert main_window.controller.state._formula == "B - A * exp(-k * x)"


def test_mode_switch_shows_z(qtbot, main_window):
    cp = main_window.config_panel
    cp.set_mode(True)
    assert cp.z_transform_widget.isHidden() is False
    assert cp.formula_prefix.text() == "z ="
    cp.set_mode(False)
    assert cp.z_transform_widget.isHidden() is True
    assert cp.formula_prefix.text() == "y ="


def test_custom_inputs_preserved_on_switch(qtbot, main_window):
    cp = main_window.config_panel
    # Select Custom, type something.
    cp.model_combo.setCurrentText("Custom")
    cp.params_input.setText("alpha, beta")
    cp.formula_input.setText("alpha * x + beta")
    # Switch to a predefined model.
    cp.model_combo.setCurrentText("Linear")
    assert cp.params_input.text() == "m, b"
    # Switch back to Custom — the user's edits must be restored.
    cp.model_combo.setCurrentText("Custom")
    assert cp.params_input.text() == "alpha, beta"
    assert cp.formula_input.text() == "alpha * x + beta"


def test_param_parse_errors_surfaced(qtbot, main_window):
    cp = main_window.config_panel
    cp.params_input.setText("A, x, A")
    # 'x' is forbidden, second 'A' is a duplicate -> status label set.
    assert cp.status_label.text() != ""


def test_param_p0_pushed_to_state(qtbot, main_window):
    cp = main_window.config_panel
    cp.params_input.setText("A=np.max(y), B, k")
    st = main_window.controller.state
    assert st._params == ["A", "B", "k"]
    assert st._p0 == ["np.max(y)", "1.0", "1.0"]


def test_reset_clears_transforms_and_restores_default_model(qtbot, main_window):
    cp = main_window.config_panel
    cp.x_transform.setText("np.log(x)")
    cp.params_input.setText("A, B")
    cp.formula_input.setText("A * x + B")
    cp.on_reset()
    assert cp.x_transform.text() == ""
    # Reset repopulates the model combo and auto-loads the first predefined
    # model (Exponential Decay), so params/formula are NOT empty — they show
    # the default model's values.
    assert cp.params_input.text() == "A, B, k"
    assert cp.formula_input.text() == "B - A * exp(-k * x)"
