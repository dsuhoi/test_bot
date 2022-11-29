import pytest
from app.utils.sympy_wrapper import input_latex, parse_str_expr, sympy_eval


@pytest.mark.parametrize(
    "input_str, result",
    [
        ("1+1", "2"),
        ("2/3+3*4", r"\frac{38}{3}"),
        ("expand((1+I*2)^3)", r"-11 - 2 i"),
        ("diff(x^5 - 4x^2 + 3)", "5 x^{4} - 8 x"),
        ("integrate(x * exp(x))", r"\left(x - 1\right) e^{x}"),
        ("sum(1/n^4, (n, 1, oo)).doit()", r"\frac{\pi^{4}}{90}"),
        ("limit(sin(x)/x, x, 0)", "1"),
        ("solve(x^2 + 2x + 1, x)", r"\left[ -1\right]"),
        ("solve([x + y - 1, x - y + 1])", r"\left\{ x : 0, \  y : 1\right\}"),
        (
            "dsolve(f(x).diff(x) - f(x) + x)",
            r"f{\left(x \right)} = C_{1} e^{x} + x + 1",
        ),
        ("Matrix(2,2,[1,2,3,4]).det()", "-2"),
        ("Matrix(2,2,[1,2, 2, 4]).eigenvals()", r"\left\{ 0 : 1, \  5 : 1\right\}"),
    ],
)
def test_sympy_eval(input_str, result):
    assert sympy_eval(input_str).get("output") == result


def test_sympy_eval_plot():
    assert sympy_eval("ploti(x^2 + y^2 - 1, show=False)", plot=True)


@pytest.mark.parametrize(
    "input_str, result",
    [
        ("1+10 * 2/5", r"1 + 10 \cdot 2 \cdot \frac{1}{5}"),
        ("diff(x^3 + exp(x))", r"\frac{d}{d x} \left(x^{3} + e^{x}\right)"),
    ],
)
def test_input_latex(input_str, result):
    parsed_str = parse_str_expr(input_str)
    assert input_latex(*parsed_str) == result
