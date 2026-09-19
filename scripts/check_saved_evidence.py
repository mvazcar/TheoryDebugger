"""Check hashes, original goals, source anchors, and axiom logs in the saved demo.

This is a consistency check of the saved bundle, not a new Lean verification.
Use run_demo.py to compile every certificate again.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from theorydebugger.certificates import audit_axioms, formal_goal
from theorydebugger.ir import parse


def main():
    bundle = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("demo/results.json")
    records = json.loads((ROOT / bundle).read_text(encoding="utf-8"))
    count = 0
    claims = [claim for r in records for claim in ([r["original"], r["repaired"]] if r.get("operation") == "repair" else [r])]
    for record in claims:
        p = parse(record["problem"])
        for cert in record["certificates"]:
            source = (ROOT / cert["source"]).read_bytes()
            assert hashlib.sha256(source).hexdigest() == cert["source_sha256"]
            assert cert["formal_goal"] == formal_goal(p)
            text = source.decode("utf-8")
            assert "def original : Prop :=\n  " + formal_goal(p) + "\n" in text
            declarations = [d.removeprefix("TheoryDebugger.Generated.") for d in cert["declarations"]]
            audit = audit_axioms((ROOT / cert["compiler_log"]).read_text(encoding="utf-8"), declarations)
            assert audit == cert["axioms"]
            lines = text.splitlines()
            for step in cert["steps"]:
                name = step.get("local_lemma") or step["declaration"].split(".")[-1]
                assert name in lines[step["line"] - 1], (cert["source"], step)
            count += 1
    print(f"Saved evidence is internally consistent: {len(records)} cases, {count} certificates.")


if __name__ == "__main__": main()
