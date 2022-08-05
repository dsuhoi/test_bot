from sympy import latex, parse_expr
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

INPUT_SYNONYMS = {
    "diff": "Derivative",
    "integrate": "Integral",
    "limit": "Limit",
}


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


def input_latex(input_string, namespace):
    for key, value in INPUT_SYNONYMS.items():
        if key in input_string:
            input_string = input_string.replace(key, value)
    return latex(eval_expr(input_string, {}, namespace))


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
