"""Reproduce the Solow example, including nonvacuous repair and axiom checks."""
from datetime import datetime, timezone
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


def main():
    output = ROOT / "demo/solow"
    output.mkdir(parents=True, exist_ok=True)
    command = [sys.argv[1] if len(sys.argv) > 1 else "lake", "env", "lean",
               "examples/SolowSwan.lean"]
    run = subprocess.run(command, cwd=ROOT,
                         env={**os.environ, "THEORYDEBUGGER_PYTHON": sys.executable},
                         capture_output=True, text=True, encoding="utf-8",
                         errors="replace", timeout=180)
    log = run.stdout + run.stderr
    (output / "native-output.txt").write_text(log, encoding="utf-8", newline="\n")
    assert run.returncode == 0 and "error:" not in log and "PANIC" not in log, log
    reports = [json.loads(line) for line in log.splitlines() if line.startswith("{")]
    assert len(reports) == 3, log
    original, repaired, impossible = reports
    assert original["classification"] == "mixed"
    assert original["classification_evidence"] == "lean_kernel"
    assert original["cases"]["refuting"]["witness"] == {"v0": "0"}
    assert original["cases"]["satisfying"]["witness"] == {"v0": "1"}
    for side in ("refuting", "satisfying"):
        cert = original["cases"][side]["certificate"]
        assert cert["status"] == "lean_verified" and cert["evidence"] == "lean_kernel"
        assert set(cert["axioms"]) <= ALLOWED
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
    for name in ("validity_certificate", "feasible_assignment"):
        cert = repaired["repaired"][name]
        assert cert["status"] == "lean_verified" and cert["evidence"] == "lean_kernel"
        assert set(cert["axioms"]) <= ALLOWED
    assert repaired["repaired"]["classification"] == "true"
    assert impossible["repaired"]["classification"] == "inconsistent"
    assert impossible["repaired"]["contradiction"]["status"] == "lean_verified"

    source = (ROOT / "examples/SolowSwan.lean").read_text(encoding="utf-8")
    declarations = re.findall(r"^theorem (\w+)", source, re.M)
    assert len(declarations) == 6
    axioms = {}
    for name in declarations:
        qualified = "SolowSwanExample." + name
        match = re.search(re.escape("'" + qualified + "'") +
                          r" depends on axioms:\s*\[([^]]*)\]", log)
        assert match, "Missing axiom audit: " + qualified
        found = [a.strip() for a in match[1].split(",") if a.strip()]
        assert set(found) <= ALLOWED, (qualified, found)
        axioms[qualified] = found
    paths = ["examples/SolowSwan.lean", "scripts/verify_solow.py", "lean-toolchain",
             "lake-manifest.json", "TheoryDebugger.lean", "TheoryDebugger/Frontend.lean",
             "TheoryDebugger/Tactic.lean", "TheoryDebugger/Classification.lean",
             "TheoryDebugger/Repair.lean", "src/theorydebugger/bridge.py",
             "src/theorydebugger/backend.py", "src/theorydebugger/ir.py",
             "src/theorydebugger/diagnose.py"]
    record = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "platform": platform.platform(), "python": platform.python_version(),
              "command": command, "exit_code": run.returncode,
              "diagnostics": ["mixed", "valid repair", "inconsistent repair rejected"],
              "theorems": len(declarations), "axioms": axioms,
              "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                                for p in paths},
              "scope": "Local run. Recompile the Lean source to reproduce the proof checks."}
    (output / "verification.json").write_text(json.dumps(record, indent=2) + "\n",
                                             encoding="utf-8", newline="\n")
    print("Passed Solow counterexample, accepted/rejected repairs, and six theorem axiom audits.")


if __name__ == "__main__":
    main()
