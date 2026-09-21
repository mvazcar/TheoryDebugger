"""Saved reports must not claim more than their archived evidence supports."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("saved_evidence", ROOT / "scripts/check_saved_evidence.py")
saved = importlib.util.module_from_spec(spec)
spec.loader.exec_module(saved)


def bundle(name="demo/results.json"):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class SavedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Git may expand tracked text to CRLF on Windows. The bundles hash the
        # generators' LF source bytes; preserve those bytes in isolated fixtures.
        cls.directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.directory.cleanup)
        cls.fixture_root = Path(cls.directory.name)
        for filename in ["demo/results.json", "demo/economics/results.json", "demo/repairs/results.json"]:
            for record in bundle(filename):
                claims = [record["original"], record["repaired"]] if record.get("operation") == "repair" else [record]
                for claim in claims:
                    for cert in claim["certificates"]:
                        for field in ["source", "compiler_log"]:
                            target = cls.fixture_root / cert[field]
                            target.parent.mkdir(parents=True, exist_ok=True)
                            target.write_text((ROOT / cert[field]).read_text(encoding="utf-8"),
                                              encoding="utf-8", newline="\n")

    def validate(self, records):
        return saved.validate_bundle(records, root=self.fixture_root)

    def test_published_bundles_are_consistent(self):
        for filename in ["demo/results.json", "demo/economics/results.json", "demo/repairs/results.json"]:
            with self.subTest(filename=filename):
                self.assertGreater(self.validate(bundle(filename)), 0)

    def test_false_claim_without_certificates_is_rejected(self):
        record = copy.deepcopy(bundle()[0])
        record["problem"] = {"variables": [], "assumptions": [], "goal": False}
        record["problem_sha256"] = saved.identity(saved.parse(record["problem"]))
        record["certificates"] = []
        record["cases"]["satisfying"].pop("witness")
        record["witness"] = None
        with self.assertRaisesRegex(ValueError, "supporting certificate"):
            self.validate([record])

    def test_identity_and_fact_labels_are_checked(self):
        for field, replacement in [
            ("problem_sha256", "wrong"), ("classification", "false"),
            ("classification_evidence", "solver_only"),
            ("validity", {"status": "refuted", "evidence": "lean_kernel"}),
            ("consistency", {"status": "inconsistent", "evidence": "lean_kernel"})]:
            with self.subTest(field=field):
                record = copy.deepcopy(bundle()[0])
                record[field] = replacement
                with self.assertRaises(ValueError):
                    self.validate([record])

    def test_missing_or_relabelled_certificate_is_rejected(self):
        for mutation in ["remove", "kind", "status", "exit", "declarations", "statement"]:
            with self.subTest(mutation=mutation):
                record = copy.deepcopy(bundle()[0])
                cert = record["certificates"][1]
                if mutation == "remove": record["certificates"].pop()
                if mutation == "kind": cert["kind"] = "false_throughout"
                if mutation == "status": cert["status"] = "unknown"
                if mutation == "exit": cert["compiler_exit_code"] = 1
                if mutation == "declarations": cert["declarations"] = []
                if mutation == "statement": cert["steps"][-1]["statement"] = "True"
                with self.assertRaises(ValueError):
                    self.validate([record])

    def test_rehashed_weaker_theorem_does_not_support_original_kind(self):
        record = copy.deepcopy(bundle()[0])
        cert = record["certificates"][1]
        text = (ROOT / cert["source"]).read_text(encoding="utf-8")
        text = text.replace("theorem claim : original := by", "theorem claim : True := by")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "Certificate.lean"
            source.write_text(text, encoding="utf-8", newline="\n")
            cert["source"] = str(source)
            cert["source_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, "matching declaration"):
                self.validate([record])

    def test_case_witness_and_case_status_are_checked(self):
        for mutation in ["witness", "status", "evidence"]:
            with self.subTest(mutation=mutation):
                record = copy.deepcopy(bundle()[0])
                case = record["cases"]["satisfying"]
                if mutation == "witness": case["witness"] = {"x": "-1", "y": "1"}
                if mutation == "status": case["status"] = "absent"
                if mutation == "evidence": case["evidence"] = "exact_evaluation"
                with self.assertRaises(ValueError):
                    self.validate([record])

    def test_repair_preservation_identity_and_acceptance(self):
        for mutation in ["candidate", "replacement", "original_id", "repaired_id", "accepted", "status", "evidence"]:
            with self.subTest(mutation=mutation):
                record = copy.deepcopy(bundle("demo/repairs/results.json")[0])
                if mutation == "candidate": record["candidate"]["assumptions"] = []
                # Both claims have valid evidence, but this is not an assumptions-only repair.
                if mutation == "replacement": record["original"] = copy.deepcopy(bundle()[0])
                if mutation == "original_id": record["original_problem_sha256"] = "wrong"
                if mutation == "repaired_id": record["repaired_problem_sha256"] = "wrong"
                if mutation == "accepted": record["accepted"] = False
                if mutation == "status": record["status"] = "refuted"
                if mutation == "evidence": record["evidence"] = "none"
                with self.assertRaises(ValueError):
                    self.validate([record])

    def test_solver_only_partial_report_remains_unknown(self):
        record = copy.deepcopy(bundle()[0])
        record["certificates"] = []
        record["classification"] = "unknown"
        record["classification_evidence"] = "none"
        record["consistency"]["evidence"] = "exact_evaluation"
        record["validity"]["evidence"] = "solver_only"
        record["cases"]["satisfying"]["evidence"] = "exact_evaluation"
        record["cases"]["refuting"]["evidence"] = "solver_only"
        self.assertEqual(self.validate([record]), 0)
        record["classification"] = "true"
        record["classification_evidence"] = "lean_kernel"
        with self.assertRaisesRegex(ValueError, "Classification"):
            self.validate([record])

    def test_checks_survive_python_optimization(self):
        record = copy.deepcopy(bundle()[0])
        record["problem_sha256"] = "wrong"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "forged.json"
            path.write_text(json.dumps([record]), encoding="utf-8")
            run = subprocess.run([sys.executable, "-O", str(ROOT / "scripts/check_saved_evidence.py"), str(path)],
                                 cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("Problem identity mismatch", run.stderr)


if __name__ == "__main__":
    unittest.main()
