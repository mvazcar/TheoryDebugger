"""Small solver-independent AST. Parsing never evaluates input as code."""
from dataclasses import dataclass
from fractions import Fraction
import re


class Unsupported(ValueError):
    pass


@dataclass(frozen=True)
class Node:
    op: str
    args: tuple


@dataclass(frozen=True)
class Problem:
    name: str
    variables: tuple[str, ...]
    assumptions: tuple[Node, ...]
    goal: Node
    witness: dict[str, Fraction] | None = None

    @property
    def antecedent(self):
        return conjunction(self.assumptions)


def conjunction(nodes):
    nodes = tuple(nodes)
    return Node("and", nodes) if nodes else Node("true", ())


def rational(value):
    if type(value) is int and len(str(abs(value))) <= 128:
        return Fraction(value)
    if isinstance(value, str) and len(value) <= 260 and re.fullmatch(r"-?\d+(?:/[1-9]\d*)?", value):
        return Fraction(value)
    raise Unsupported(f"Expected an exact integer or rational string, got {value!r}")


def parse(data):
    if not isinstance(data, dict):
        raise Unsupported("Problem must be a JSON object")
    extra = set(data) - {"name", "variables", "assumptions", "goal", "witness"}
    if extra:
        raise Unsupported(f"Unsupported fields: {sorted(extra)}")
    variables = data.get("variables", [])
    if not isinstance(variables, list) or len(variables) > 8 or any(
        not isinstance(v, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,39}", v)
        for v in variables
    ) or len(set(variables)) != len(variables):
        raise Unsupported("Expected at most eight distinct ASCII variable names")
    count = 0

    def node(value, formula=False, depth=0):
        nonlocal count
        count += 1
        if count > 500 or depth > 32:
            raise Unsupported("Expression size/depth exceeds prototype limits")
        if formula and type(value) is bool:
            return Node("true" if value else "false", ())
        if not formula and isinstance(value, str) and value in variables:
            return Node("var", (value,))
        if not formula and (type(value) is int or isinstance(value, str)):
            return Node("rat", (rational(value),))
        if not isinstance(value, list) or not value or not isinstance(value[0], str):
            raise Unsupported(f"Unsupported {'formula' if formula else 'expression'}: {value!r}")
        op, *args = value
        arity = {"+": 2, "-": 2, "*": 2, "^": 2, "neg": 1,
                 "=": 2, "!=": 2, "<": 2, "<=": 2, ">": 2, ">=": 2, "not": 1}
        relations = {"=", "!=", "<", "<=", ">", ">="}
        if formula and op in {"and", "or"}:
            if len(args) < 2:
                raise Unsupported("and/or require at least two arguments")
            return Node(op, tuple(node(a, True, depth + 1) for a in args))
        allowed = relations | {"not"} if formula else {"+", "-", "*", "^", "neg"}
        if op not in allowed or len(args) != arity.get(op):
            raise Unsupported(f"Unsupported operator or arity: {op}")
        if op == "^":
            if type(args[1]) is not int or not 0 <= args[1] <= 8:
                raise Unsupported("Only natural powers 0..8 are supported")
            return Node(op, (node(args[0], False, depth + 1), args[1]))
        return Node(op, tuple(node(a, op == "not", depth + 1) for a in args))

    assumptions = data.get("assumptions", [])
    if not isinstance(assumptions, list) or len(assumptions) > 30:
        raise Unsupported("Expected a list of at most 30 assumptions")
    if "goal" not in data:
        raise Unsupported("Missing goal")
    parsed_assumptions = tuple(node(a, True) for a in assumptions)
    goal = node(data["goal"], True)
    witness = data.get("witness")
    if witness is not None:
        if not isinstance(witness, dict) or set(witness) != set(variables):
            raise Unsupported("Witness must give every variable exactly once")
        witness = {k: rational(v) for k, v in witness.items()}
    name = data.get("name", "claim")
    if not isinstance(name, str) or len(name) > 120:
        raise Unsupported("Name must be a string of at most 120 characters")
    return Problem(name, tuple(variables), parsed_assumptions, goal, witness)


def evaluate(n, values):
    op, args = n.op, n.args
    if op == "var": return values[args[0]]
    if op == "rat": return args[0]
    if op == "true": return True
    if op == "false": return False
    if op == "^": return evaluate(args[0], values) ** args[1]
    a = [evaluate(x, values) for x in args]
    if op == "and": return all(a)
    if op == "or": return any(a)
    if op == "not": return not a[0]
    if op == "neg": return -a[0]
    if op == "+": return a[0] + a[1]
    if op == "-": return a[0] - a[1]
    if op == "*": return a[0] * a[1]
    if op == "=": return a[0] == a[1]
    if op == "!=": return a[0] != a[1]
    if op == "<": return a[0] < a[1]
    if op == "<=": return a[0] <= a[1]
    if op == ">": return a[0] > a[1]
    if op == ">=": return a[0] >= a[1]
    raise Unsupported(op)


def encode(n):
    if n.op == "rat": return str(n.args[0])
    if n.op == "var": return n.args[0]
    if n.op in {"true", "false"}: return n.op == "true"
    if n.op == "^": return ["^", encode(n.args[0]), n.args[1]]
    return [n.op, *(encode(a) for a in n.args)]


def canonical(p):
    return {"variables": list(p.variables), "assumptions": [encode(a) for a in p.assumptions],
            "goal": encode(p.goal)}
