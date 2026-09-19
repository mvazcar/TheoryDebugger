"""Reproduce explicit repair checks and validate both CLI and native JSON contracts."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from theorydebugger.backend import CVC5Backend
from theorydebugger.certificates import LeanVerifier
from theorydebugger.ir import parse
from theorydebugger.repair import check_repair


def main():
    lake = sys.argv[1] if len(sys.argv) > 1 else "lake"
    output = ROOT / "demo/repairs"
    output.mkdir(parents=True, exist_ok=True)
    verifier = LeanVerifier(ROOT, ROOT / "artifacts/repairs", lake)
    records = []
    input_hashes = {}
    for name, original_name, candidate_name, expected in [
        ("tax_supply", "tax_incidence", "nonnegative_supply", "valid"),
        ("tax_impossible", "tax_incidence", "contradictory_demand", "inconsistent"),
        ("false_repair", "false_conjecture", "nonnegative_z", "refuted")]:
        paths = [ROOT / f"examples/{original_name}.json", ROOT / f"examples/repairs/{candidate_name}.json"]
        for path in paths:
            input_hashes[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        original, candidate = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
        r = check_repair(parse(original), candidate, CVC5Backend(), verifier)
        assert r["status"] == expected and r["accepted"] == (expected == "valid"), r
        assert r["original"]["classification"] == "mixed", r
        for side in ("original", "repaired"):
            for index, cert in enumerate(r[side]["certificates"]):
                assert cert["status"] == "lean_verified", cert
                destination = output / "certificates" / name / side / str(index)
                destination.mkdir(parents=True, exist_ok=True)
                for field in ("source", "compiler_log"):
                    source = Path(cert[field])
                    target = destination / source.name
                    shutil.copyfile(source, target)
                    cert[field] = target.relative_to(ROOT).as_posix()
        records.append(r)
        print(name, expected, flush=True)
    (output / "results.json").write_text(json.dumps(records, indent=2, default=str) + "\n", encoding="utf-8", newline="\n")

    env = {**os.environ, "THEORYDEBUGGER_PYTHON": sys.executable}
    for path, filename in [("examples/Repairs.lean", "native-output.txt"), ("lean-tests/Structured.lean", "native-json.txt")]:
        run = subprocess.run([lake, "env", "lean", path], cwd=ROOT, env=env, capture_output=True,
                             text=True, encoding="utf-8", errors="replace", timeout=180)
        log = run.stdout + run.stderr
        (output / filename).write_text(log, encoding="utf-8", newline="\n")
        assert run.returncode == 0 and "PANIC" not in log and "error:" not in log, log
        input_hashes[path] = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        if filename == "native-output.txt":
            for expected in ("valid", "inconsistent", "refuted"):
                assert log.count("Repair: " + expected) == 1, log
        else:
            results = [json.loads(line) for line in log.splitlines() if line.startswith('{')]
            assert len(results) == 5, log
            assert [r["classification"] for r in results[:2]] == ["mixed", "false"], results
            for r, expected in zip(results[2:], ("valid", "inconsistent", "refuted"), strict=True):
                assert r["schema_version"] == 2 and r["status"] == expected, r
                assert r["accepted"] == (expected == "valid") and r["evidence"] == "lean_kernel", r
                before, after = r["original"]["problem"], r["repaired"]["problem"]
                assert before["goal"] == after["goal"] and before["variables"] == after["variables"], r
                assert before["assumptions"] == after["assumptions"][:-1], r
                assert r["original_problem_id"] == r["original"]["problem_id"], r
                assert r["original"]["classification"] == "mixed", r
    (output / "verification.json").write_text(json.dumps({
        "checked_at_utc": datetime.now(timezone.utc).isoformat(), "input_sha256": input_hashes,
        "repair_cases": len(records), "native_json_cases": 5,
        "certificates": sum(len(r[s]["certificates"]) for r in records for s in ("original", "repaired")),
    }, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("Passed three CLI repairs, three native repairs, and five native JSON contract checks.")


if __name__ == "__main__":
    main()
