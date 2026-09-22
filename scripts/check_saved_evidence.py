"""Check saved certificate contents and the report facts they support.

This checks internal consistency, including stored compiler logs; it is not a
new Lean verification. Regenerate each bundle with its run_*.py script to
compile certificates again.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from theorydebugger.certificates import audit_axioms, build_source, formal_goal
from theorydebugger.diagnose import classify, identity
from theorydebugger.ir import canonical, evaluate, parse, rational


def require(condition, message):
    if not condition:
        raise ValueError(message)


def assignment(p, value):
    require(isinstance(value, dict) and set(value) == set(p.variables), "Incomplete saved witness")
    witness = {v: rational(q) for v, q in value.items()}
    require(evaluate(p.antecedent, witness), "Saved witness violates the assumptions")
    return witness


def check_certificate(cert, p, record, root):
    """Bind a certificate kind to its expected declarations, not just its label."""
    require(isinstance(cert, dict), "Invalid certificate")
    kind = cert.get("kind")
    witness = None
    if kind in {"satisfying", "counterexample"}:
        side = "satisfying" if kind == "satisfying" else "refuting"
        witness = assignment(p, record["cases"][side].get("witness"))
    elif kind == "feasible":
        witness = assignment(p, record.get("witness"))
    _, expected_names, expected_steps = build_source(p, kind, witness)
    expected = {step["declaration"]: step["statement"] for step in expected_steps if "declaration" in step}
    source = (root / cert["source"]).read_bytes()
    require(hashlib.sha256(source).hexdigest() == cert.get("source_sha256"), "Certificate source hash mismatch")
    require(cert.get("formal_goal") == formal_goal(p), "Certificate formal goal mismatch")
    text = source.decode("utf-8")
    require("def original : Prop :=\n  " + formal_goal(p) + "\n" in text, "Original goal missing from certificate")
    for name, statement in expected.items():
        short = name.removeprefix("TheoryDebugger.Generated.")
        require(f"theorem {short} : {statement} := by\n" in text,
                f"Certificate kind has no matching declaration: {name}")
    status = cert.get("status")
    require(status in {"lean_verified", "unknown"}, "Invalid certificate status")
    if status == "unknown":
        return None
    require(cert.get("compiler_exit_code") == 0, "Verified certificate has no successful compiler exit")
    names = ["TheoryDebugger.Generated." + name for name in expected_names]
    require(cert.get("declarations") == names, "Certificate declaration coverage mismatch")
    audit = audit_axioms((root / cert["compiler_log"]).read_text(encoding="utf-8"), expected_names)
    require(audit == cert.get("axioms"), "Certificate axiom report mismatch")
    lines = text.splitlines()
    declared = {}
    for step in cert["steps"]:
        line = step.get("line")
        require(type(line) is int and 1 <= line <= len(lines), "Invalid source anchor")
        name = step.get("local_lemma") or step["declaration"].split(".")[-1]
        require(name in lines[line - 1], "Source anchor does not name its step")
        if "declaration" in step:
            require(step["declaration"] not in declared, "Duplicate declaration step")
            declared[step["declaration"]] = step["statement"]
    require(declared == expected, "Certificate statement metadata mismatch")
    return kind


def check_fact(fact, statuses, proved, exact, solver, label):
    require(isinstance(fact, dict), f"Invalid {label} fact")
    status, evidence = fact.get("status"), fact.get("evidence")
    require(status in statuses, f"Invalid {label} status")
    require(evidence in {"none", "solver_only", "exact_evaluation", "lean_kernel"}, f"Invalid {label} evidence")
    if proved is not None:
        require((status, evidence) == (proved, "lean_kernel"), f"{label} disagrees with its certificates")
    elif evidence == "lean_kernel":
        raise ValueError(f"{label} has no supporting certificate")
    elif evidence == "exact_evaluation":
        require(status == exact and exact is not None, f"{label} has no matching exact witness")
    elif evidence == "solver_only":
        require(status == solver and solver is not None, f"{label} disagrees with its solver-only query")
    else:
        require(status == "unknown", f"{label} has a result without evidence")


def check_claim(record, root):
    require(record.get("schema_version") == 2, "Expected schema 2")
    p = parse(record["problem"])
    require(record["problem"] == canonical(p), "Saved problem is not canonical")
    require(record.get("problem_sha256") == identity(p), "Problem identity mismatch")
    cases = record["cases"]
    require(isinstance(cases, dict) and set(cases) == {"satisfying", "refuting"}, "Invalid case pair")
    exact_sides = set()
    for side, case in cases.items():
        require(isinstance(case, dict), "Invalid case fact")
        if "witness" in case:
            w = assignment(p, case["witness"])
            require(evaluate(p.goal, w) == (side == "satisfying"), "Witness does not establish its reported side")
            exact_sides.add(side)
    if record.get("witness") is not None:
        assignment(p, record["witness"])
    certs = record["certificates"]
    require(isinstance(certs, list), "Expected a certificate list")
    kinds = {kind for cert in certs if (kind := check_certificate(cert, p, record, root)) is not None}
    present = bool(kinds & {"feasible", "satisfying", "counterexample"})
    require(not ("inconsistent" in kinds and present), "Contradiction and feasibility certificates conflict")
    require(not ("valid" in kinds and "counterexample" in kinds), "Validity and refutation certificates conflict")
    require(not ("false_throughout" in kinds and "satisfying" in kinds), "Satisfying and absence certificates conflict")
    solver = record.get("solver", {})
    require(isinstance(solver, dict), "Invalid solver report")

    def solver_status(query, mapping):
        answer = solver.get(query, {})
        require(isinstance(answer, dict), "Invalid solver query")
        return mapping.get(answer.get("status"))

    consistency = "inconsistent" if "inconsistent" in kinds else "consistent" if present else None
    validity = "refuted" if "counterexample" in kinds else "valid" if kinds & {"valid", "inconsistent"} else None
    check_fact(record["consistency"], {"consistent", "inconsistent", "unknown"}, consistency,
               "consistent" if exact_sides else None,
               solver_status("assumptions", {"sat": "consistent", "unsat": "inconsistent"}), "Consistency")
    check_fact(record["validity"], {"valid", "refuted", "unknown"}, validity,
               "refuted" if "refuting" in exact_sides else None,
               solver_status("counterexample_query", {"sat": "refuted", "unsat": "valid"}), "Validity")
    for side, presence_kind, absence_kinds, query in [
        ("satisfying", "satisfying", {"false_throughout", "inconsistent"}, "satisfying_query"),
        ("refuting", "counterexample", {"valid", "inconsistent"}, "counterexample_query")]:
        proved = "present" if presence_kind in kinds else "absent" if kinds & absence_kinds else None
        check_fact(cases[side], {"present", "absent", "unknown"}, proved,
                   "present" if side in exact_sides else None,
                   solver_status(query, {"sat": "present", "unsat": "absent"}), side)
    classification = classify(*(cases[s]["status"] if cases[s]["evidence"] == "lean_kernel" else "unknown"
                                for s in ("satisfying", "refuting")))
    require(record.get("classification") == classification, "Classification disagrees with checked cases")
    require(record.get("classification_evidence") == ("none" if classification == "unknown" else "lean_kernel"),
            "Classification evidence mismatch")
    return len(certs)


def check_repair(record, root):
    require(record.get("schema_version") == 2, "Expected repair schema 2")
    original, revised = record["original"], record["repaired"]
    count = check_claim(original, root) + check_claim(revised, root)
    before, after = original["problem"], revised["problem"]
    candidate = record["candidate"]
    require(isinstance(candidate, dict) and set(candidate) == {"assumptions"}
            and isinstance(candidate["assumptions"], list), "Repair may only append assumptions")
    require(before["variables"] == after["variables"] and before["goal"] == after["goal"]
            and before["assumptions"] + candidate["assumptions"] == after["assumptions"],
            "Repair changed the original claim instead of appending assumptions")
    require(record.get("original_problem_sha256") == original["problem_sha256"]
            and record.get("repaired_problem_sha256") == revised["problem_sha256"], "Repair identity mismatch")
    status = "unknown"
    if revised["consistency"] == {"status": "inconsistent", "evidence": "lean_kernel"}:
        status = "inconsistent"
    elif revised["validity"] == {"status": "refuted", "evidence": "lean_kernel"}:
        status = "refuted"
    elif (revised["validity"] == {"status": "valid", "evidence": "lean_kernel"}
          and revised["consistency"] == {"status": "consistent", "evidence": "lean_kernel"}):
        status = "valid"
    require(record.get("status") == status and type(record.get("accepted")) is bool
            and record["accepted"] == (status == "valid"), "Repair acceptance lacks the required evidence")
    require(record.get("evidence") == ("none" if status == "unknown" else "lean_kernel"), "Repair evidence mismatch")
    return count


def validate_bundle(records, root=ROOT):
    require(isinstance(records, list) and records, "Expected a nonempty saved report list")
    count = 0
    for index, record in enumerate(records):
        try:
            require(isinstance(record, dict), "Invalid saved report")
            operation = record.get("operation")
            require(operation in {None, "repair"}, "Unsupported saved operation")
            count += check_repair(record, root) if operation == "repair" else check_claim(record, root)
        except (KeyError, TypeError, ValueError, OSError) as error:
            raise ValueError(f"Saved report {index + 1}: {error}") from error
    return count


def main():
    bundle = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("demo/results.json")
    records = json.loads((ROOT / bundle).read_text(encoding="utf-8"))
    count = validate_bundle(records)
    print(f"Saved evidence is internally consistent: {len(records)} cases, {count} certificates. No fresh Lean verification.")


if __name__ == "__main__":
    main()
