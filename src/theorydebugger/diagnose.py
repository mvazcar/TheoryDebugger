"""Four-way diagnosis. Solver answers guide discovery, never certify a result."""
from dataclasses import asdict
import hashlib
import json
from .ir import Node, canonical, evaluate


def identity(p):
    """Identity of the ordered formal input, independent of labels and hints."""
    return hashlib.sha256(json.dumps(canonical(p), sort_keys=True).encode()).hexdigest()


def classify(satisfying, refuting):
    return {("present", "absent"): "true", ("present", "present"): "mixed",
            ("absent", "present"): "false", ("absent", "absent"): "inconsistent"}.get(
                (satisfying, refuting), "unknown")


def fact(status="unknown", evidence="none"):
    return {"status": status, "evidence": evidence}


def diagnose(p, backend, verifier=None):
    sat = backend.check(p, p.antecedent)
    positive = backend.check(p, Node("and", (p.antecedent, p.goal)))
    counter = backend.check(p, Node("and", (p.antecedent, Node("not", (p.goal,)))))
    result = {"schema_version": 2, "name": p.name, "problem": canonical(p),
              "problem_sha256": identity(p),
              "solver": {"assumptions": asdict(sat), "satisfying_query": asdict(positive),
                         "counterexample_query": asdict(counter)},
              "consistency": fact(), "validity": fact(),
              "cases": {"satisfying": fact(), "refuting": fact()},
              "certificates": [], "witness": None, "warnings": []}
    if sat.status in {"sat", "unsat"}:
        result["consistency"] = fact("consistent" if sat.status == "sat" else "inconsistent", "solver_only")
    if counter.status in {"sat", "unsat"}:
        result["validity"] = fact("refuted" if counter.status == "sat" else "valid", "solver_only")
    for side, answer in [("satisfying", positive), ("refuting", counter)]:
        if answer.status in {"sat", "unsat"}:
            result["cases"][side] = fact("present" if answer.status == "sat" else "absent", "solver_only")
    result["solver"]["classification"] = classify(*(result["cases"][s]["status"] for s in ("satisfying", "refuting")))

    def check(kind, witness=None):
        if verifier is None:
            return None
        cert = verifier.verify(p, kind, witness)
        cert["kind"] = kind
        result["certificates"].append(cert)
        return cert if cert["status"] == "lean_verified" else None

    witnesses = {}
    # Hints have priority within their side, but never replace an opposite-side witness.
    for witness in [p.witness, counter.witness, positive.witness, sat.witness]:
        if witness is None:
            continue
        if set(witness) != set(p.variables) or not evaluate(p.antecedent, witness):
            result["warnings"].append("Rejected candidate witness: it fails the original assumptions")
            continue
        side = "satisfying" if evaluate(p.goal, witness) else "refuting"
        witnesses.setdefault(side, witness)

    for side, witness in witnesses.items():
        kind = "satisfying" if side == "satisfying" else "counterexample"
        evidence = "lean_kernel" if check(kind, witness) else "exact_evaluation"
        result["cases"][side] = {**fact("present", evidence),
                                 "witness": {v: str(q) for v, q in witness.items()}}
    if witnesses:
        best = "lean_kernel" if any(c["evidence"] == "lean_kernel" for c in result["cases"].values()) else "exact_evaluation"
        result["consistency"] = fact("consistent", best)
        selected = witnesses.get("refuting", witnesses.get("satisfying"))
        result["witness"] = {v: str(q) for v, q in selected.items()}
    if "refuting" in witnesses:
        result["validity"] = fact("refuted", result["cases"]["refuting"]["evidence"])

    # An untrusted SAT answer must not prevent independent proof reconstruction.
    if not witnesses and check("inconsistent"):
        result["consistency"] = fact("inconsistent", "lean_kernel")
        result["validity"] = fact("valid", "lean_kernel")
        result["cases"] = {s: fact("absent", "lean_kernel") for s in ("satisfying", "refuting")}
    else:
        if "refuting" not in witnesses and check("valid"):
            result["validity"] = fact("valid", "lean_kernel")
            result["cases"]["refuting"] = fact("absent", "lean_kernel")
        if "satisfying" not in witnesses and check("false_throughout"):
            result["cases"]["satisfying"] = fact("absent", "lean_kernel")

    checked = [c["status"] if c["evidence"] == "lean_kernel" else "unknown" for c in result["cases"].values()]
    result["classification"] = classify(*checked)
    result["classification_evidence"] = "none" if result["classification"] == "unknown" else "lean_kernel"
    result["explanation"] = {
        "true": "The goal holds throughout a nonempty feasible model.",
        "mixed": "There are checked feasible assignments where the goal holds and where it fails.",
        "false": "The goal fails throughout a nonempty feasible model.",
        "inconsistent": "The assumptions contradict each other; the implication is valid vacuously.",
        "unknown": "Lean has not established both sides. Inspect the partial results and their evidence labels.",
    }[result["classification"]]
    return result
