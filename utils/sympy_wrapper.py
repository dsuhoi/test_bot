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
    "lim": "limit",
    "sum": "Sum",
    "antiderivative": "integrate",
    "factorize": "factor",
    "plotp": "plot_parametric",
    "ploti": "plot_implicit",
    "plot3ds": "plot3d_parametric_surface",
    "plot3dL": "plot3d_parametric_line",
}

INPUT_SYNONYMS = {"diff": "Derivative", "integrate": "Integral", "limit": "Limit"}
NO_PARSE = ["Integer", "Symbol", "Float", "Rational", "Matrix", "Sum"]


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


def check_attrib(node):
    class attr_vis(ast.NodeVisitor):
        def __init__(self):
            self.attribute_flag = False

        def visit_Attribute(self, node):
            self.attribute_flag = True
            ast.NodeVisitor.generic_visit(self, node)

    vis = attr_vis()
    vis.visit(node)
    return vis.attribute_flag


def simpify_block(node, braces=False):
    name_func = node.func.id
    parsed_str = latex(sympify(ast.unparse(node).replace(name_func, "")))
    parsed_str = f"\\left({parsed_str}\\right)" if braces else parsed_str
    name_func = name_func.replace("_", r"\_")
    return f"\\text{{{name_func}}}{parsed_str}"


def parse_block(node):
    if isinstance(node, ast.BinOp):
        op = {ast.Add: "+", ast.Sub: "-"}
        if n_op := op.get(type(node.op)):
            return f"{parse_block(node.left)} {n_op} {parse_block(node.right)}"
    elif isinstance(node, ast.Call):
        attrs_str = ""
        while isinstance(node.func, ast.Attribute):
            tmp = ast.unparse(node)
            node = node.func.value
            tmp = ast.parse(tmp.replace(ast.unparse(node), "")[1:]).body[0].value
            attrs_str = "." + simpify_block(tmp) + attrs_str
        attrs_str = (r"\;" + attrs_str) if attrs_str != "" else ""
        if node.func.id not in (list(INPUT_SYNONYMS.values()) + NO_PARSE):
            return simpify_block(node, braces=True) + attrs_str
        else:
            return latex(sympify(ast.unparse(node))) + attrs_str

    if not check_attrib(node):
        return latex(sympify(ast.unparse(node), evaluate=False))
    else:
        return None


def input_latex(parsed_str, namespace, evaluated):
    for key, value in INPUT_SYNONYMS.items():
        if key in parsed_str and "." + key not in parsed_str:
            parsed_str = parsed_str.replace(key, value)
    node = ast.parse(parsed_str, mode="eval").body
    return result if (result := parse_block(node)) else latex(evaluated)


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
            "input": input_latex(parsed, namespace, evaluated),
            "output": latex(evaluated),
        }
