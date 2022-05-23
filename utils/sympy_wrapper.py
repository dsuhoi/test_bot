import ast
import collections
import re
import sys

import sympy
from sympy import latex
from sympy.core.function import FunctionClass
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

OTHER_SYMPY_FUNCTIONS = ("sqrt",)

Arguments = collections.namedtuple("Arguments", "function args kwargs")

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


class Eval(object):
    def __init__(self, namespace={}):
        self._namespace = namespace

    def get(self, name):
        return self._namespace.get(name)

    def set(self, name, value):
        self._namespace[name] = value

    def eval_node(self, node):
        tree = ast.fix_missing_locations(ast.Expression(node))
        return eval(compile(tree, "<string>", "eval"), self._namespace)

    def eval(self, x, use_none_for_exceptions=False, repr_expression=True):
        globals = self._namespace
        try:
            x = x.strip()
            x = x.replace("\r", "")
            y = x.split("\n")
            if len(y) == 0:
                return ""
            s = "\n".join(y[:-1]) + "\n"
            t = y[-1]
            try:
                z = compile(t + "\n", "", "eval")
            except SyntaxError:
                s += "\n" + t
                z = None

            try:
                old_stdout = sys.stdout
                sys.stdout = StringIO()
                eval(compile(s, "", "exec", division.compiler_flag), globals, globals)

                if not z is None:
                    r = eval(z, globals)

                    if repr_expression:
                        r = repr(r)
                else:
                    r = ""

                if repr_expression:
                    sys.stdout.seek(0)
                    r = sys.stdout.read() + r
            finally:
                sys.stdout = old_stdout
            return r
        except:
            if use_none_for_exceptions:
                return
            etype, value, tb = sys.exc_info()
            return ""


class TopCallVisitor(ast.NodeVisitor):
    def __init__(self):
        super(TopCallVisitor, self).__init__()
        self.call = None

    def visit_Call(self, node):
        self.call = node

    def visit_Name(self, node):
        if not self.call:
            self.call = node

    def visit_NameConstant(self, node):
        if not self.call:
            self.call = node


class LatexVisitor(ast.NodeVisitor):
    EXCEPTIONS = {"integrate": sympy.Integral, "diff": sympy.Derivative}
    formatters = {}

    @staticmethod
    def formats_function(name):
        def _formats_function(f):
            LatexVisitor.formatters[name] = f
            return f

        return _formats_function

    def format(self, name, node):
        formatter = LatexVisitor.formatters.get(name)

        if not formatter:
            return None

        return formatter(node, self)

    def visit_Call(self, node):
        buffer = []
        fname = node.func.id

        # Only apply to lowercase names (i.e. functions, not classes)
        if fname in self.__class__.EXCEPTIONS:
            node.func.id = self.__class__.EXCEPTIONS[fname].__name__
            self.latex = sympy.latex(self.evaluator.eval_node(node))
        else:
            result = self.format(fname, node)
            if result:
                self.latex = result
            elif fname[0].islower() and fname not in OTHER_SYMPY_FUNCTIONS:
                buffer.append("\\mathrm{%s}" % fname.replace("_", "\\_"))
                buffer.append("(")

                latexes = []
                for arg in node.args:
                    if (
                        isinstance(arg, ast.Call)
                        and getattr(arg.func, "id", None)
                        and arg.func.id[0].lower() == arg.func.id[0]
                    ):
                        latexes.append(self.visit_Call(arg))
                    else:
                        latexes.append(sympy.latex(self.evaluator.eval_node(arg)))

                buffer.append(", ".join(latexes))
                buffer.append(")")

                self.latex = "".join(buffer)
            else:
                self.latex = sympy.latex(self.evaluator.eval_node(node))
        return self.latex


re_calls = re.compile(
    r"(Integer|Symbol|Float|Rational)\s*\([\'\"]?([a-zA-Z0-9\.]+)[\'\"]?\s*\)"
)


def removeSymPy(string):
    try:
        return re_calls.sub(re_calls_sub, string)
    except IndexError:
        return string


def arguments(string_or_node, evaluator):
    node = None
    if not isinstance(string_or_node, ast.Call):
        a = TopCallVisitor()
        a.visit(ast.parse(string_or_node))

        if hasattr(a, "call"):
            node = a.call
    else:
        node = string_or_node

    if node:
        if isinstance(node, ast.Call):
            name = getattr(node.func, "id", None)  # when is it undefined?
            args, kwargs = None, None
            if node.args:
                args = list(map(evaluator.eval_node, node.args))

            kwargs = node.keywords
            if kwargs:
                kwargs = {
                    kwarg.arg: evaluator.eval_node(kwarg.value) for kwarg in kwargs
                }

            return Arguments(name, args, kwargs)
        elif isinstance(node, ast.Name):
            return Arguments(node.id, [], {})

        elif isinstance(node, ast.NameConstant):
            return Arguments(node.value, [], {})
    return None


def latexify(string, evaluator):
    a = LatexVisitor()
    a.evaluator = evaluator
    a.visit(ast.parse(string))
    return a.latex


def latex_result(parsed, evaluator, evaluated):
    argument = arguments(parsed, evaluator)

    first_func_name = argument[0]
    is_function = False

    first_func = evaluator.get(first_func_name)
    is_function = (
        first_func
        and not isinstance(first_func, FunctionClass)
        and not isinstance(first_func, sympy.Atom)
        and first_func_name
        and first_func_name[0].islower()
        and not first_func_name in OTHER_SYMPY_FUNCTIONS
    ) and (argument.args or argument.kwargs)

    if is_function:
        latex_input = latexify(parsed, evaluator)
    else:
        latex_input = latex(evaluated)

    result = {"input": latex_input, "output": latex(evaluated)}

    return result


def vmw_eval(s):
    namespace = {}
    exec(PREEXEC, {}, namespace)
    evaluator = Eval(namespace)
    transformations = []
    transformations.append(synonyms)
    transformations.extend(standard_transformations)
    transformations.extend((convert_xor, custom_implicit_transformation))
    parsed = stringify_expr(s, {}, namespace, transformations)
    evaluated = eval_expr(parsed, {}, namespace)

    return latex_result(parsed, evaluator, evaluated)


def vmw_plot(s):
    namespace = {}
    exec(PREEXEC, {}, namespace)
    evaluator = Eval(namespace)
    transformations = []
    transformations.append(synonyms)
    transformations.extend(standard_transformations)
    transformations.extend((convert_xor, custom_implicit_transformation))
    parsed = stringify_expr(s, {}, namespace, transformations)
    evaluated = eval_expr(parsed, {}, namespace)

    return evaluated
