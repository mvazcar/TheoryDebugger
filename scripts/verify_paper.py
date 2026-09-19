"""Recheck the five named tax-incidence proofs and their four native diagnoses."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from theorydebugger.certificates import ALLOWED_AXIOMS


def main():
    source = "examples/Paper2018Tax.lean"
    compiler_log = "demo/paper-2018-tax-output.txt"
    run = subprocess.run(["lake", "env", "lean", source], cwd=ROOT,
                         env={**os.environ, "THEORYDEBUGGER_PYTHON": sys.executable},
                         capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    log = run.stdout + run.stderr
    assert run.returncode == 0 and "PANIC" not in log, log
    assert log.count("Classification: true") == 3 and log.count("Classification: mixed") == 1, log
    assert log.count("Assumptions: feasible assignment checked by Lean") == 4, log
    audits = {}
    for name in ("seller_price_falls", "seller_price_falls_less_than_tax", "weak_supply_repairs_sign",
                 "satisfying_assignment", "refuting_assignment"):
        match = re.search(re.escape("'Paper2018Tax." + name + "'") + r" depends on axioms:\s*\[([^]]*)\]", log)
        assert match, log
        axioms = [a.strip() for a in match.group(1).split(',') if a.strip()]
        assert set(axioms) <= ALLOWED_AXIOMS, axioms
        audits[name] = axioms
    (ROOT / compiler_log).write_text(log, encoding="utf-8", newline="\n")
    record = {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "source": source,
              "source_sha256": hashlib.sha256((ROOT / source).read_bytes()).hexdigest(),
              "compiler_log": compiler_log, "compiler_log_sha256": hashlib.sha256((ROOT / compiler_log).read_bytes()).hexdigest(),
              "exit_code": run.returncode, "universal_theorems": 3, "ground_witness_theorems": 2,
              "checked_diagnostic_refutations": 1, "classifications": ["true", "true", "mixed", "true"],
              "axioms": audits, "limits": ["Derivative equation supplied manually", "Bounds and sufficient restriction supplied manually",
                                           "No general parameter projection or automatic repair discovery"]}
    (ROOT / "demo/paper-2018-tax-verification.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("Passed five named tax-incidence proofs and four native classifications.")


if __name__ == "__main__":
    main()
