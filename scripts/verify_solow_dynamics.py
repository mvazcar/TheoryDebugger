"""Check Solow path positivity, adjustment speed, repairs, and analytic bridges."""
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
    output = ROOT / "demo/solow-dynamics"
    output.mkdir(parents=True, exist_ok=True)
    command = [sys.argv[1] if len(sys.argv) > 1 else "lake", "env", "lean",
               "examples/SolowSwanDynamics.lean"]
    run = subprocess.run(command, cwd=ROOT,
                         env={**os.environ, "THEORYDEBUGGER_PYTHON": sys.executable},
                         capture_output=True, text=True, encoding="utf-8",
                         errors="replace", timeout=240)
    log = run.stdout + run.stderr
    (output / "native-output.txt").write_text(log, encoding="utf-8", newline="\n")
    assert run.returncode == 0 and not any(s in log for s in
        ("error:", "error(", "PANIC", "warning:", "sorryAx")), "\n".join(
        line for line in log.splitlines() if not line.startswith("{"))
    reports = [json.loads(line) for line in log.splitlines() if line.startswith("{")]
    assert len(reports) == 6
    witnesses = []
    for original, repaired, impossible in (reports[:3], reports[3:]):
        assert original["classification"] == "mixed"
        assert original["classification_evidence"] == "lean_kernel"
        for side in ("refuting", "satisfying"):
            certificate(original["cases"][side]["certificate"])
        certificate(original["feasible_assignment"])
        certificate(original["refutation"])
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
        witnesses.append({side: original["cases"][side]["witness"]
                          for side in ("refuting", "satisfying")})
    # Independently evaluate exact rational witnesses, including all assumptions.
    for side, w in witnesses[0].items():
        z, e = Fraction(w["v0"]), Fraction(w["v1"])
        assert z > 0 and e > 0
        assert (1 + (z - 1) * e > 0) == (side == "satisfying")
        if side == "refuting":
            assert e > 1
    for side, w in witnesses[1].items():
        alpha, m = Fraction(w["v0"]), Fraction(w["v1"])
        assert alpha > 0 and m > 0
        assert ((1 - alpha) * m > 0) == (side == "satisfying")
    source = (ROOT / "examples/SolowSwanDynamics.lean").read_text(encoding="utf-8")
    declarations = re.findall(r"^theorem (\w+)", source, re.M)
    assert len(declarations) == 7
    axioms = {}
    for name in declarations:
        qualified = "SolowDynamicsExample." + name
        match = re.search(re.escape("'" + qualified + "'") +
                          r" depends on axioms:\s*\[([^]]*)\]", log)
        assert match, qualified
        found = [a.strip() for a in match[1].split(",") if a.strip()]
        assert set(found) <= ALLOWED, (qualified, found)
        axioms[qualified] = found
    paths = ["examples/SolowSwanDynamics.lean", "scripts/verify_solow_dynamics.py",
             "lean-toolchain", "lake-manifest.json", "TheoryDebugger.lean",
             "TheoryDebugger/Frontend.lean", "TheoryDebugger/Tactic.lean",
             "TheoryDebugger/Classification.lean", "TheoryDebugger/Repair.lean",
             "src/theorydebugger/bridge.py", "src/theorydebugger/backend.py",
             "src/theorydebugger/ir.py", "src/theorydebugger/diagnose.py"]
    record = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "platform": platform.platform(), "python": platform.python_version(),
              "command": command, "exit_code": run.returncode,
              "diagnostics": ["mixed affine positivity", "weight upper bound accepted",
                              "nonpositive weight rejected", "mixed adjustment speed",
                              "exponent below one accepted", "nonpositive exponent rejected"],
              "exact_witnesses": witnesses, "theorems": len(declarations), "axioms": axioms,
              "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
              "scope": "Native polynomial diagnostics and actual exponential/derivative bridges. The full real-power trajectory theorem is checked in the separate LeanEconomics contribution."}
    (output / "verification.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("Passed six Solow dynamics diagnostics, four repair decisions, exact witnesses, and seven axiom audits.")


if __name__ == "__main__":
    main()
