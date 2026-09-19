"""Check eight economic conjectures, their feasibility, and native Lean examples."""
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from theorydebugger.backend import CVC5Backend
from theorydebugger.certificates import ALLOWED_AXIOMS, LeanVerifier
from theorydebugger.diagnose import diagnose
from theorydebugger.ir import parse

CASES = {
    "market_quantity": "valid",
    "market_price": "valid",
    "market_price_rises": "refuted",
    "tax_revenue": "refuted",
    "tax_revenue_repaired": "valid",
    "monopoly_half": "valid",
    "monopoly_quantity": "valid",
    "monopoly_full": "refuted",
}
THEOREMS = ["supply_shift_quantity", "supply_shift_price",
            "tax_revenue_with_preserved_base", "monopoly_half_pass_through",
            "monopoly_quantity_falls"]


def main():
    lake = sys.argv[1] if len(sys.argv) > 1 else "lake"
    output = ROOT / "demo/economics"
    output.mkdir(parents=True, exist_ok=True)
    verifier = LeanVerifier(ROOT, ROOT / "artifacts/economics", lake)
    records, input_hashes = [], {}
    for name, expected in CASES.items():
        path = ROOT / "examples/economics" / (name + ".json")
        input_hashes[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        problem = parse(json.loads(path.read_text(encoding="utf-8")))
        result = diagnose(problem, CVC5Backend(), verifier)
        print(name, result["validity"], result["consistency"], flush=True)
        if result["validity"] != {"status": expected, "evidence": "lean_kernel"}:
            raise RuntimeError(json.dumps(result, indent=2, default=str))
        if result["consistency"] != {"status": "consistent", "evidence": "lean_kernel"}:
            raise RuntimeError("Feasibility was not proved: " + name)
        if result["warnings"]:
            raise RuntimeError("Rejected evidence: " + str(result["warnings"]))
        if problem.witness is not None and result["witness"] != {v: str(q) for v, q in problem.witness.items()}:
            raise RuntimeError("The teaching counterexample was not certified: " + name)
        for index, cert in enumerate(result["certificates"]):
            if cert["status"] != "lean_verified":
                raise RuntimeError("Unverified certificate: " + name)
            destination = output / "certificates" / name / str(index)
            destination.mkdir(parents=True, exist_ok=True)
            for field in ("source", "compiler_log"):
                source = Path(cert[field])
                target = destination / source.name
                shutil.copyfile(source, target)
                cert[field] = target.relative_to(ROOT).as_posix()
        records.append(result)

    env = {**os.environ, "THEORYDEBUGGER_PYTHON": sys.executable}
    native_path = ROOT / "examples/Economics.lean"
    native_hash = hashlib.sha256(native_path.read_bytes()).hexdigest()
    native = subprocess.run([lake, "env", "lean", "examples/Economics.lean"],
                            cwd=ROOT, env=env, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=180)
    log = native.stdout + native.stderr
    (output / "native-output.txt").write_text(log, encoding="utf-8", newline="\n")
    if native.returncode != 0:
        raise RuntimeError(log)
    audits = {}
    for theorem in THEOREMS:
        match = re.search(re.escape("'Economics." + theorem + "'") +
                          r" depends on axioms:\s*\[([^]]*)\]", log)
        if not match:
            raise RuntimeError("Missing named-theorem audit: " + theorem)
        axioms = [item.strip() for item in match.group(1).split(",") if item.strip()]
        if set(axioms) - ALLOWED_AXIOMS:
            raise RuntimeError("Unapproved axioms: " + str(axioms))
        audits[theorem] = axioms
    if log.count("Goal: refuted (Lean checked against the original goal)") != 3:
        raise RuntimeError("Expected three native refutations:\n" + log)
    if log.count("Goal: valid (Lean checked against the original goal)") != 5:
        raise RuntimeError("Expected five native proofs:\n" + log)
    if log.count("Assumptions: feasible assignment checked by Lean") != 8:
        raise RuntimeError("Expected eight native feasibility certificates:\n" + log)

    (output / "results.json").write_text(json.dumps(records, indent=2, default=str) + "\n", encoding="utf-8")
    import cvc5
    environment = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(), "python": platform.python_version(),
        "cvc5": cvc5.Solver().getVersion().decode(),
        "lean": subprocess.check_output([lake, "env", "lean", "--version"], cwd=ROOT, text=True).strip(),
        "manifest_sha256": hashlib.sha256((ROOT / "lake-manifest.json").read_bytes()).hexdigest(),
        "cases": len(records), "certificates": sum(len(r["certificates"]) for r in records),
        "input_sha256": input_hashes,
        "native_source_sha256": native_hash, "native_axioms": audits,
        "native_exit_code": native.returncode,
    }
    (output / "environment.json").write_text(json.dumps(environment, indent=2) + "\n", encoding="utf-8")
    print("Passed eight economic cases, five native theorems, and three native refutations.")


if __name__ == "__main__":
    main()
