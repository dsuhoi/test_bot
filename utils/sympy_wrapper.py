import ast

from sympy import latex, sympify
from sympy.parsing.sympy_parser import (NAME, convert_xor, eval_expr,
                                        function_exponentiation,
                                        implicit_application,
                                        implicit_multiplication, split_symbols,
                                        standard_transformations,
                                        stringify_expr)

PREEXEC = """from __future__ import division
from sympy import *
import sympy
from sympy.solvers.diophantine import diophantine
from sympy.plotting import *
f = Function('f')
g = Function('g')
"""


SYNONYMS = {
    "derivative": "diff",
    "derive": "diff",
    "integral": "integrate",
    "antiderivative": "integrate",
    "factorize": "factor",
    "plotp": "plot_parametric",
    "ploti": "plot_implicit",
    "plot3ds": "plot3d_parametric_surface",
    "plot3dL": "plot3d_parametric_line",
}

INPUT_SYNONYMS = {"diff": "Derivative", "integrate": "Integral", "limit": "Limit"}


def custom_implicit_transformation(result, local_dict, global_dict):
    for step in (
        split_symbols,
        implicit_multiplication,
        implicit_application,
        function_exponentiation,
    ):
        result = step(result, local_dict, global_dict)
    return result


def synonyms(tokens, local_dict, global_dict):
    result = []
    for token in tokens:
        if token[0] == NAME:
            if token[1] in SYNONYMS:
                result.append((NAME, SYNONYMS[token[1]]))
                continue
        result.append(token)
    return result


def input_latex(parsed_str, namespace):
    for key, value in INPUT_SYNONYMS.items():
        if key in parsed_str and "." + key not in parsed_str:
            parsed_str = parsed_str.replace(key, value)

    cmd_node = ast.parse(parsed_str, mode="eval").body
    if isinstance(cmd_node, ast.Call) and (
        cmd_node.func.id not in INPUT_SYNONYMS.values()
    ):
        parsed_str = sympify(parsed_str.replace(cmd_node.func.id, ""))
        return f"\\text{{{cmd_node.func.id}}}\\left({latex(parsed_str)}\\right)"
    return latex(eval_expr(parsed_str, {}, namespace))


def sympy_eval(s, plot=False):
    namespace = {}
    exec(PREEXEC, {}, namespace)
    transformations = []
    transformations.append(synonyms)
    transformations.extend(standard_transformations)
    transformations.extend((convert_xor, custom_implicit_transformation))
    parsed = stringify_expr(s, {}, namespace, transformations)
    evaluated = eval_expr(parsed, {}, namespace)

    if plot:
        return evaluated
    else:
        return {
            "input": input_latex(parsed, namespace),
            "output": latex(evaluated),
        }
