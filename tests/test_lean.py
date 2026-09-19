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

    def test_solver_valid_but_reconstruction_incomplete(self):
        p = parse({"variables": ["x"], "goal": ["or", ["<", "x", 0], [">=", "x", 0]]})
        r = diagnose(p, CVC5Backend(), self.verifier)
        self.assertEqual(r["validity"], {"status": "valid", "evidence": "solver_only"})
        self.assertEqual(r["certificates"][-1]["status"], "unknown")

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


if __name__ == "__main__": unittest.main()
