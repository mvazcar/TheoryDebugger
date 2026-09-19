import json
from fractions import Fraction
from pathlib import Path
import unittest
from theorydebugger.backend import Answer, CVC5Backend
from theorydebugger.certificates import audit_axioms, build_source, formal_goal, render
from theorydebugger.diagnose import diagnose
from theorydebugger.ir import Unsupported, canonical, evaluate, parse

ROOT = Path(__file__).resolve().parents[1]


def example(name):
    return parse(json.loads((ROOT / "examples" / (name + ".json")).read_text()))


class Stub:
    def __init__(self, answer): self.answer = answer
    def check(self, *args): return self.answer


class CoreTests(unittest.TestCase):
    def test_false_repair_regression(self):
        p = example("false_repair")
        self.assertTrue(evaluate(p.antecedent, p.witness))
        self.assertFalse(evaluate(p.goal, p.witness))
        r = diagnose(p, CVC5Backend())
        self.assertEqual(r["validity"], {"status": "refuted", "evidence": "exact_evaluation"})
        self.assertEqual(r["witness"], {"x": "4", "y": "1", "z": "2"})

    def test_solver_counterexample_without_supplied_hint(self):
        raw = canonical(example("false_repair"))
        p = parse(raw)
        r = diagnose(p, CVC5Backend())
        self.assertEqual(r["validity"]["status"], "refuted")
        self.assertTrue(evaluate(p.antecedent, {v: Fraction(q) for v, q in r["witness"].items()}))

    def test_strict_inequality_and_rationals(self):
        p = parse({"variables": ["x"], "assumptions": [["=", "x", "1/3"]], "goal": [">", "x", "1/3"]})
        self.assertEqual(diagnose(p, CVC5Backend())["validity"]["status"], "refuted")
        self.assertIn("((1 : ℝ) / 3)", formal_goal(p))

    def test_true_validity_is_separate_from_feasibility(self):
        for file, expected in [("true_goal", "consistent"), ("true_infeasible", "inconsistent")]:
            r = diagnose(example(file), CVC5Backend())
            self.assertEqual(r["validity"]["status"], "valid")
            self.assertEqual(r["consistency"]["status"], expected)

    def test_individual_removal_is_not_joint_removal(self):
        h1, h2 = [">=", "x", 1], [">=", "x", 2]
        for assumptions, expected in [([h1, h2], "valid"), ([h1], "valid"), ([h2], "valid"), ([], "refuted")]:
            p = parse({"variables": ["x"], "assumptions": assumptions, "goal": [">", "x", 0]})
            self.assertEqual(diagnose(p, CVC5Backend())["validity"]["status"], expected)

    def test_unknown_is_not_unsat(self):
        p = parse({"variables": ["x"], "goal": [">", "x", 0]})
        r = diagnose(p, Stub(Answer("unknown", detail="timeout")))
        self.assertEqual(r["classification"], "unknown")
        self.assertEqual(r["consistency"]["status"], "unknown")
        self.assertEqual(r["certificates"], [])

    def test_forged_witness_rejected(self):
        p = example("valid")
        with self.assertRaises(ValueError):
            build_source(p, "counterexample", {"x": Fraction(1), "y": Fraction(1)})
        with self.assertRaises(ValueError):
            build_source(p, "counterexample", {"x": Fraction(-1), "y": Fraction(-2)})

    def test_untrusted_solver_model_rechecked(self):
        p = parse({"variables": ["x"], "assumptions": [[">", "x", 0]], "goal": [">=", "x", 0]})
        r = diagnose(p, Stub(Answer("sat", {"x": Fraction(-1)})))
        self.assertEqual(r["validity"]["evidence"], "solver_only")
        self.assertIsNone(r["witness"])
        self.assertTrue(r["warnings"])

    def test_unsupported_does_not_silently_drop_terms(self):
        for expr in [["sin", "x"], ["/", "x", 2], ["^", "x", -1], 0.5, "unknown", ["^", "x", True]]:
            with self.assertRaises(Unsupported):
                parse({"variables": ["x"], "goal": ["=", expr, 0]})
        with self.assertRaises(Unsupported):
            parse({"variables": ["x", "x"], "goal": True})
        with self.assertRaises(Unsupported):
            parse({"variables": ["x"], "goal": True, "parameters": ["x"]})

    def test_syntax_cannot_inject_lean(self):
        with self.assertRaises(Unsupported):
            parse({"variables": ["x) := by sorry"], "goal": True})
        p = parse({"variables": ["theorem"], "goal": [">", "theorem", 0]})
        self.assertEqual(formal_goal(p), "∀ (v0 : ℝ), (v0 > (0 : ℝ))")

    def test_missing_or_unapproved_axioms_fail_closed(self):
        for output in ["", "'TheoryDebugger.Generated.claim' depends on axioms: [sorryAx]",
                       "'TheoryDebugger.Generated.claim' depends on axioms: [oracle]"]:
            with self.assertRaises(ValueError): audit_axioms(output, ["claim"])
        self.assertEqual(audit_axioms("'TheoryDebugger.Generated.claim' depends on axioms: [propext, Quot.sound]", ["claim"]),
                         {"TheoryDebugger.Generated.claim": ["propext", "Quot.sound"]})

    def test_boolean_and_zero_power_semantics(self):
        p = parse({"variables": ["x"], "goal": ["and", ["=", ["^", "x", 0], 1],
                   ["or", ["<", "x", 0], ["not", ["<", "x", 0]]]]})
        self.assertTrue(evaluate(p.goal, {"x": Fraction(0)}))
        self.assertEqual(diagnose(p, CVC5Backend())["validity"]["status"], "valid")


if __name__ == "__main__": unittest.main()
