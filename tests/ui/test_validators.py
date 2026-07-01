"""Tests for the pure-parse validators (no Qt widget needed)."""

from kobs_plotter.ui.validators import (
    is_valid_color_string,
    is_valid_formula_syntax,
    params_p0_match,
    parse_param_hints,
)


class TestParseParamHints:
    def test_simple_list(self):
        h = parse_param_hints("A, B, k")
        assert h.params == ["A", "B", "k"]
        assert h.p0 == ["1.0", "1.0", "1.0"]
        assert h.errors == []

    def test_with_initial_values(self):
        h = parse_param_hints("A=np.max(y), B=2.0, k")
        assert h.params == ["A", "B", "k"]
        assert h.p0 == ["np.max(y)", "2.0", "1.0"]

    def test_empty_and_whitespace(self):
        assert parse_param_hints("").params == []
        assert parse_param_hints("   ").params == []
        assert parse_param_hints("A, , B").params == ["A", "B"]

    def test_blank_expr_defaults_to_one(self):
        h = parse_param_hints("A=")
        assert h.p0 == ["1.0"]

    def test_forbidden_names_rejected(self):
        h = parse_param_hints("x, y, z, A")
        assert h.params == ["A"]
        assert len(h.errors) == 3

    def test_duplicate_detected(self):
        h = parse_param_hints("A, A, B")
        assert h.params == ["A", "A", "B"]
        assert any("Duplicate" in e for e in h.errors)

    def test_multiple_equals_flagged(self):
        h = parse_param_hints("A=1=2")
        assert h.params == []
        assert any("multiple" in e.lower() for e in h.errors)


def test_params_p0_match():
    assert params_p0_match(["A"], ["1.0"])
    assert not params_p0_match(["A", "B"], ["1.0"])


class TestColorString:
    def test_named(self):
        assert is_valid_color_string("red")
        assert is_valid_color_string("black")

    def test_hex(self):
        assert is_valid_color_string("#FF5733")
        assert is_valid_color_string("#abc")

    def test_empty(self):
        assert not is_valid_color_string("")
        assert not is_valid_color_string("   ")


class TestFormulaSyntax:
    def test_plain_ok(self):
        assert is_valid_formula_syntax("B - A * exp(-k * x)") is None

    def test_np_rejected(self):
        err = is_valid_formula_syntax("np.exp(x)")
        assert err is not None
        assert "np" in err.lower()

    def test_empty_rejected(self):
        assert is_valid_formula_syntax("") is not None
