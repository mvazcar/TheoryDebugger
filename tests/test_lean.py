"""Opt-in boundary checks with the real Lean executable, not mocked results."""
import os
import hashlib
from pathlib import Path
import tempfile
import unittest
from theorydebugger.backend import CVC5Backend
from theorydebugger.certificates import LeanVerifier
from theorydebugger.diagnose import diagnose
from theorydebugger.ir import parse
from theorydebugger.repair import check_repair

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get("THEORYDEBUGGER_TEST_LEAN") == "1", "Set THEORYDEBUGGER_TEST_LEAN=1 for real Lean boundary checks")
class LeanBoundaryTests(unittest.TestCase):
    def setUp(self):
        (ROOT / "artifacts").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "artifacts")
        self.addCleanup(self.temp.cleanup)
        self.verifier = LeanVerifier(ROOT, self.temp.name)

    def test_false_claim_is_not_certified(self):
        p = parse({"variables": ["x"], "goal": [">", "x", 0]})
        result = self.verifier.verify(p, "valid")
        self.assertEqual(result["status"], "unknown")
        self.assertNotEqual(result["compiler_exit_code"], 0)
        self.assertEqual(hashlib.sha256(Path(result["source"]).read_bytes()).hexdigest(), result["source_sha256"])

    def test_cass_corner_product_reconstruction(self):
        # A real RCK obligation: nlinarith alone misses this cubic product.
        # Positivity must reconstruct a kernel proof, not trust the SMT result.
        p = parse({"variables": ["r", "B"], "assumptions": [
            [">=", "r", 0], ["<=", "r", 1], [">=", "B", 0]],
            "goal": [">=", ["*", ["*", "r", ["-", 1, "r"]], "B"], 0],
            "witness": {"r": "1/2", "B": 1}})
        r = diagnose(p, CVC5Backend(), self.verifier)
        self.assertEqual(r["validity"], {"status": "valid", "evidence": "lean_kernel"})
        self.assertEqual(r["consistency"], {"status": "consistent", "evidence": "lean_kernel"})
        self.assertTrue(all(c["status"] == "lean_verified" for c in r["certificates"]))

    def test_cass_corner_product_requires_upper_bound(self):
        p = parse({"variables": ["r", "B"], "assumptions": [
            [">=", "r", 0], [">=", "B", 0]],
            "goal": [">=", ["*", ["*", "r", ["-", 1, "r"]], "B"], 0],
            "witness": {"r": 2, "B": 1}})
        self.assertEqual(self.verifier.verify(p, "valid")["status"], "unknown")
        r = diagnose(p, CVC5Backend(), self.verifier)
        self.assertEqual(r["validity"], {"status": "refuted", "evidence": "lean_kernel"})

    def test_solver_valid_but_reconstruction_incomplete(self):
        p = parse({"variables": ["x"], "goal": ["or", ["<", "x", 0], [">=", "x", 0]]})
        r = diagnose(p, CVC5Backend(), self.verifier)
        self.assertEqual(r["validity"], {"status": "valid", "evidence": "solver_only"})
        self.assertEqual(r["certificates"][-1]["status"], "unknown")

    def test_nonlinear_definition_substitution(self):
        # The Hamiltonian calculation needs an equality substituted inside a
        # further product, not merely added as a linear arithmetic constraint.
        p = parse({"variables": ["q", "d", "g", "x", "v"],
            "assumptions": [["=", "v", ["*", ["-", "d", "g"], "q"]]],
            "goal": ["=", ["+", ["*", "v", "x"], ["*", ["*", "g", "q"], "x"]],
                      ["*", ["*", "d", "q"], "x"]],
            "witness": {"q": 1, "d": 2, "g": 1, "x": 3, "v": 1}})
        result = diagnose(p, CVC5Backend(), self.verifier)
        self.assertEqual(result["validity"], {"status": "valid", "evidence": "lean_kernel"})
        self.assertEqual(result["consistency"], {"status": "consistent", "evidence": "lean_kernel"})

    def test_equality_multiplied_by_variable(self):
        p = parse({"variables": ["c", "r"],
            "assumptions": [["=", ["*", "c", "r"], 1]],
            "goal": ["=", ["*", "c", ["^", "r", 2]], "r"],
            "witness": {"c": 3, "r": "1/3"}})
        result = diagnose(p, CVC5Backend(), self.verifier)
        self.assertEqual(result["validity"], {"status": "valid", "evidence": "lean_kernel"})
        # Without the defining equation this consequence is false.
        bad = parse({"variables": ["c", "r"],
            "goal": ["=", ["*", "c", ["^", "r", 2]], "r"],
            "witness": {"c": 2, "r": 1}})
        self.assertEqual(self.verifier.verify(bad, "valid")["status"], "unknown")
        self.assertEqual(diagnose(bad, CVC5Backend(), self.verifier)["validity"],
                         {"status": "refuted", "evidence": "lean_kernel"})

    def test_closed_false_goal_has_checked_refutation(self):
        p = parse({"variables": [], "goal": False})
        r = diagnose(p, CVC5Backend(), self.verifier)
        self.assertEqual(r["validity"], {"status": "refuted", "evidence": "lean_kernel"})

    def test_exact_rational_boolean_witness(self):
        p = parse({"variables": ["x"], "assumptions": [
            ["=", "x", "-1/3"], ["!=", "x", 0], ["<", "x", 0], ["<=", "x", 0],
            [">", ["neg", "x"], 0], [">=", ["^", "x", 2], 0],
            ["or", False, ["not", ["=", "x", 0]]],
            ["=", ["-", ["+", "x", 1], 1], "x"],
            ["=", ["*", "x", 3], -1], ["=", ["^", "x", 0], 1]], "goal": [">", "x", 0]})
        r = diagnose(p, CVC5Backend(), self.verifier)
        self.assertEqual(r["validity"], {"status": "refuted", "evidence": "lean_kernel"})

    def test_four_way_classification_with_real_certificates(self):
        for goal, extra, expected in [([">", "x", 0], [], "true"),
                                     (["<", "x", 1], [], "mixed"),
                                     (["<", "x", 0], [], "false"),
                                     (["<", "x", 0], [["<=", "x", 0]], "inconsistent")]:
            with self.subTest(expected=expected):
                p = parse({"variables": ["x"], "assumptions": [[">", "x", 0], *extra], "goal": goal})
                r = diagnose(p, CVC5Backend(), self.verifier)
                self.assertEqual(r["classification"], expected)
                self.assertEqual(r["classification_evidence"], "lean_kernel")
                for c in r["cases"].values():
                    self.assertEqual(c["evidence"], "lean_kernel")

    def test_repair_requires_both_validity_and_feasibility(self):
        p = parse({"variables": ["x"], "assumptions": [[">", "x", 0]], "goal": [">", "x", 1]})
        for assumption, expected in [([">", "x", 2], "valid"),
                                     (["<=", "x", 0], "inconsistent"), ([">", "x", 0], "refuted")]:
            with self.subTest(expected=expected):
                r = check_repair(p, {"assumptions": [assumption]}, CVC5Backend(), self.verifier)
                self.assertEqual(r["status"], expected)
                self.assertEqual(r["accepted"], expected == "valid")
                self.assertEqual(r["original"]["classification"], "mixed")

    def test_algebraic_feasibility_cannot_certify_repair(self):
        p = parse({"variables": ["x"], "assumptions": [["=", ["^", "x", 2], 2], [">", "x", 0]], "goal": True})
        r = check_repair(p, {"assumptions": []}, CVC5Backend(), self.verifier)
        self.assertEqual(r["repaired"]["validity"]["evidence"], "lean_kernel")
        self.assertEqual(r["repaired"]["classification"], "unknown")
        self.assertEqual(r["status"], "unknown")
        self.assertFalse(r["accepted"])


if __name__ == "__main__": unittest.main()
