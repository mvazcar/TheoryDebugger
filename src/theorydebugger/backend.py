"""Untrusted, replaceable diagnosis backend; exact witnesses cross the boundary."""
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Protocol
from .ir import Node, Problem


@dataclass
class Answer:
    status: str
    witness: dict[str, Fraction] | None = None
    detail: str = ""
    raw_model: dict[str, str] = field(default_factory=dict)


class Backend(Protocol):
    def check(self, problem: Problem, formula: Node) -> Answer: ...


class CVC5Backend:
    def __init__(self, timeout_ms=5000):
        self.timeout_ms = timeout_ms

    def check(self, problem, formula):
        import cvc5
        k = cvc5.Kind
        s = cvc5.Solver()
        s.setLogic("QF_NRA")
        s.setOption("produce-models", "true")
        s.setOption("tlimit-per", str(self.timeout_ms))
        variables = {v: s.mkConst(s.getRealSort(), f"v{i}") for i, v in enumerate(problem.variables)}
        ops = {"+": k.ADD, "-": k.SUB, "*": k.MULT, "neg": k.NEG,
               "=": k.EQUAL, "!=": k.DISTINCT, "<": k.LT, "<=": k.LEQ,
               ">": k.GT, ">=": k.GEQ, "and": k.AND, "or": k.OR, "not": k.NOT}

        def term(n):
            if n.op == "var": return variables[n.args[0]]
            if n.op == "rat": return s.mkReal(str(n.args[0]))
            if n.op in {"true", "false"}: return s.mkBoolean(n.op == "true")
            if n.op == "^":
                b, power = n.args
                if power == 0: return s.mkReal(1)
                if power == 1: return term(b)
                return s.mkTerm(k.MULT, *([term(b)] * power))
            if n.op in {"and", "or"} and len(n.args) == 1: return term(n.args[0])
            return s.mkTerm(ops[n.op], *(term(a) for a in n.args))

        try:
            s.assertFormula(term(formula))
            result = s.checkSat()
            if result.isUnsat(): return Answer("unsat")
            if result.isUnknown(): return Answer("unknown", detail=str(result.getUnknownExplanation()))
            raw = {v: s.getValue(t) for v, t in variables.items()}
            display = {v: str(t) for v, t in raw.items()}
            if not all(t.isRealValue() for t in raw.values()):
                return Answer("sat", detail="Algebraic/non-rational witness: certificate unsupported", raw_model=display)
            witness = {v: Fraction(t.getRealValue()) for v, t in raw.items()}
            return Answer("sat", witness, raw_model=display)
        except RuntimeError as e:
            return Answer("unknown", detail=str(e))
