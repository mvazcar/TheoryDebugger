"""Run real solvers and Lean. Save a portable, reviewable evidence bundle."""
import json
import hashlib
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from theorydebugger.backend import CVC5Backend
from theorydebugger.certificates import LeanVerifier
from theorydebugger.diagnose import diagnose
from theorydebugger.ir import parse


def main():
    lake = sys.argv[1] if len(sys.argv) > 1 else "lake"
    output = ROOT / "demo"
    output.mkdir(exist_ok=True)
    verifier = LeanVerifier(ROOT, ROOT / "artifacts", lake)
    cases = [(f, json.loads((ROOT / "examples" / (f + ".json")).read_text(encoding="utf-8")))
             for f in ["valid", "false_conjecture", "false_repair", "contradiction", "true_goal", "true_infeasible"]]
    for label, assumptions in [("both", [[">=", "x", 1], [">=", "x", 2]]),
                               ("without_first", [[">=", "x", 2]]), ("without_second", [[">=", "x", 1]]),
                               ("without_both", [])]:
        cases.append((label, {"name": label, "variables": ["x"], "assumptions": assumptions, "goal": [">", "x", 0]}))
    results = []
    for label, raw in cases:
        result = diagnose(parse(raw), CVC5Backend(), verifier)
        expected = "refuted" if label in {"false_conjecture", "false_repair", "without_both"} else "valid"
        assert result["validity"] == {"status": expected, "evidence": "lean_kernel"}, result
        assert result["consistency"]["evidence"] == "lean_kernel", result
        for i, cert in enumerate(result["certificates"]):
            assert cert["status"] == "lean_verified", cert
            destination = output / "certificates" / label / str(i)
            destination.mkdir(parents=True, exist_ok=True)
            for field in ["source", "compiler_log"]:
                src = Path(cert[field])
                target = destination / src.name
                shutil.copyfile(src, target)
                cert[field] = target.relative_to(ROOT).as_posix()
        results.append(result)
        print(label, result["classification"], result["validity"]["evidence"], flush=True)
    (output / "results.json").write_text(json.dumps(results, indent=2, default=str, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    import cvc5
    environment = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
                   "platform": platform.platform(), "python": platform.python_version(),
                   "cvc5": cvc5.Solver().getVersion().decode(),
                   "lean": subprocess.check_output([lake, "env", "lean", "--version"], cwd=ROOT, text=True).strip(),
                   "toolchain": (ROOT / "lean-toolchain").read_text().strip(),
                   "mathlib_revision": json.loads((ROOT / "lake-manifest.json").read_text())["packages"][0]["rev"],
                   "manifest_sha256": hashlib.sha256((ROOT / "lake-manifest.json").read_bytes()).hexdigest(),
                   "cases": len(results)}
    (output / "environment.json").write_text(json.dumps(environment, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Passed {len(results)} end-to-end cases with checked feasibility/contradiction and axiom audits.")


if __name__ == "__main__": main()
