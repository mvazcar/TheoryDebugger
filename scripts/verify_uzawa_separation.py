"""Check the coordinate repair, actual calculus bridge, and nonseparable family."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"propext", "Classical.choice", "Quot.sound"}


def certificate(cert):
    assert cert["status"] == "lean_verified", cert
    assert cert["evidence"] == "lean_kernel", cert
    assert set(cert["axioms"]) <= ALLOWED, cert


def main():
    output = ROOT / "demo/uzawa-separation"
    output.mkdir(parents=True, exist_ok=True)
    command = [sys.argv[1] if len(sys.argv) > 1 else "lake", "env", "lean",
               "examples/UzawaSeparation.lean"]
    run = subprocess.run(command, cwd=ROOT,
                         env={**os.environ, "THEORYDEBUGGER_PYTHON": sys.executable},
                         capture_output=True, text=True, encoding="utf-8",
                         errors="replace", timeout=180)
    log = run.stdout + run.stderr
    (output / "native-output.txt").write_text(log, encoding="utf-8", newline="\n")
    clean = run.returncode == 0 and not any(s in log for s in ("error:", "error(", "PANIC", "warning:", "sorryAx"))
    assert clean, "\n".join(line for line in log.splitlines() if not line.startswith("{"))
    reports = [json.loads(line) for line in log.splitlines() if line.startswith("{")]
    assert len(reports) == 4, log
    original, repaired, impossible, separation = reports
    for report in (original, separation):
        assert report["classification"] == "mixed"
        assert report["classification_evidence"] == "lean_kernel"
        for side in ("refuting", "satisfying"):
            certificate(report["cases"][side]["certificate"])
        certificate(report["feasible_assignment"])
        certificate(report["refutation"])
    witness = original["cases"]["refuting"]["witness"]
    assert Fraction(witness["v0"]) == 0
    assert Fraction(witness["v1"]) != Fraction(witness["v2"])
    for report, status, accepted in [(repaired, "valid", True),
                                     (impossible, "inconsistent", False)]:
        assert report["schema_version"] == 2 and report["operation"] == "repair"
        assert report["status"] == status and report["accepted"] is accepted
        assert report["evidence"] == "lean_kernel"
        assert report["original_problem_id"] == original["problem_id"]
        before, after = report["original"]["problem"], report["repaired"]["problem"]
        assert before == original["problem"]
        assert before["variables"] == after["variables"] and before["goal"] == after["goal"]
        assert after["assumptions"] == before["assumptions"] + report["candidate"]["assumptions"]
    certificate(repaired["repaired"]["validity_certificate"])
    certificate(repaired["repaired"]["feasible_assignment"])
    certificate(impossible["repaired"]["contradiction"])
    witness = repaired["repaired"]["cases"]["satisfying"]["witness"]
    assert Fraction(witness["v0"]) > 0
    assert Fraction(witness["v1"]) == Fraction(witness["v2"])
    false_t = Fraction(separation["cases"]["refuting"]["witness"]["v0"])
    true_t = Fraction(separation["cases"]["satisfying"]["witness"]["v0"])
    assert 0 < false_t <= 1 and true_t == 0

    source = (ROOT / "examples/UzawaSeparation.lean").read_text(encoding="utf-8")
    declarations = re.findall(r"^theorem (\w+)", source, re.M)
    assert len(declarations) == 7
    axioms = {}
    for name in declarations:
        qualified = "UzawaSeparationExample." + name
        match = re.search(re.escape("'" + qualified + "'") +
                          r" depends on axioms:\s*\[([^]]*)\]", log)
        assert match, qualified
        found = [a.strip() for a in match[1].split(",") if a.strip()]
        assert set(found) <= ALLOWED, (qualified, found)
        axioms[qualified] = found
    paths = ["examples/UzawaSeparation.lean", "scripts/verify_uzawa_separation.py",
             "lean-toolchain", "lake-manifest.json", "TheoryDebugger.lean",
             "TheoryDebugger/Frontend.lean", "TheoryDebugger/Tactic.lean",
             "TheoryDebugger/Classification.lean", "TheoryDebugger/Repair.lean",
             "src/theorydebugger/bridge.py", "src/theorydebugger/backend.py",
             "src/theorydebugger/ir.py", "src/theorydebugger/diagnose.py"]
    record = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "platform": platform.platform(), "python": platform.python_version(),
              "command": command, "exit_code": run.returncode,
              "diagnostics": ["mixed cancellation", "positive coordinate repair accepted",
                              "negative coordinate repair inconsistent", "mixed separation claim"],
              "separation_counterexample_t": str(false_t),
              "theorems": len(declarations), "axioms": axioms,
              "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
              "scope": "Native diagnostics and bridges; separate LeanEconomics build checks the repaired general theorem."}
    (output / "verification.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("Passed four separation diagnostics, both repair decisions, and seven theorem axiom audits.")


if __name__ == "__main__":
    main()
