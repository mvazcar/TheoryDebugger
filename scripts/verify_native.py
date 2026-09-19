"""Run the native examples and assertions, saving portable evidence and source hashes."""
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


def main():
    env = dict(os.environ)
    env["THEORYDEBUGGER_PYTHON"] = sys.executable
    commands = [(["lake", "build"], "native-build.txt"),
                (["lake", "env", "lean", "lean-tests/Native.lean"], "native-tests.txt"),
                (["lake", "env", "lean", "examples/Native.lean"], "native-output.txt")]
    runs = []
    for command, log in commands:
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=180)
        text = result.stdout + result.stderr
        (ROOT / "demo" / log).write_text(text, encoding="utf-8", newline="\n")
        if result.returncode != 0:
            print(text)
            raise SystemExit(result.returncode)
        runs.append({"command": command, "exit_code": result.returncode, "log": "demo/" + log})
        print("Passed:", " ".join(command), flush=True)
    paths = ["TheoryDebugger.lean", "TheoryDebugger/Frontend.lean", "TheoryDebugger/Tactic.lean",
             "TheoryDebugger/Classification.lean", "TheoryDebugger/Repair.lean",
             "lean-tests/Native.lean", "examples/Native.lean", "src/theorydebugger/bridge.py",
             "src/theorydebugger/ir.py", "src/theorydebugger/backend.py", "src/theorydebugger/diagnose.py",
             "lean-toolchain", "lake-manifest.json"]
    tests = (ROOT / "lean-tests/Native.lean").read_text(encoding="utf-8")
    data = {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "platform": platform.platform(),
            "python": platform.python_version(), "native_cases": len(re.findall(r"^(?:#expect_|#test_|theorem native_test_)", tests, re.M)),
            "runs": runs, "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
            "allowed_axioms": ["propext", "Classical.choice", "Quot.sound"],
            "scope": "This record covers local execution; GitHub Actions records Linux CI separately."}
    (ROOT / "demo/native-verification.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Passed {data['native_cases']} native cases; saved source hashes and compiler output.")


if __name__ == "__main__": main()
