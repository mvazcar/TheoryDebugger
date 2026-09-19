"""Keep validity, feasibility, and evidence levels distinct in every result."""
from dataclasses import asdict
import hashlib
import json
from .ir import Node, canonical, evaluate


def diagnose(p, backend, verifier=None):
    sat = backend.check(p, p.antecedent)
    counter = backend.check(p, Node("and", (p.antecedent, Node("not", (p.goal,)))))
    original = canonical(p)
    result = {"schema_version": 1, "name": p.name, "problem": original,
              "problem_sha256": hashlib.sha256(json.dumps(original, sort_keys=True).encode()).hexdigest(),
              "solver": {"assumptions": asdict(sat), "counterexample_query": asdict(counter)},
              "consistency": {"status": "unknown", "evidence": "none"},
              "validity": {"status": "unknown", "evidence": "none"},
              "certificates": [], "witness": None, "warnings": []}
    if sat.status in {"sat", "unsat"}:
        result["consistency"] = {"status": "consistent" if sat.status == "sat" else "inconsistent", "evidence": "solver_only"}
    if counter.status in {"sat", "unsat"}:
        result["validity"] = {"status": "refuted" if counter.status == "sat" else "valid", "evidence": "solver_only"}

    def check(kind, witness=None):
        if verifier is None: return None
        cert = verifier.verify(p, kind, witness)
        cert["kind"] = kind
        result["certificates"].append(cert)
        return cert if cert["status"] == "lean_verified" else None

    candidates = [p.witness, counter.witness, sat.witness]
    feasible = None
    refuting = None
    for witness in candidates:
        if witness is None: continue
        if set(witness) != set(p.variables) or not evaluate(p.antecedent, witness):
            result["warnings"].append("Rejected candidate witness: it fails the original assumptions")
            continue
        feasible = witness
        if not evaluate(p.goal, witness):
            refuting = witness
            break
    if refuting is not None:
        result["witness"] = {v: str(q) for v, q in refuting.items()}
        result["consistency"] = {"status": "consistent", "evidence": "exact_evaluation"}
        result["validity"] = {"status": "refuted", "evidence": "exact_evaluation"}
        if check("counterexample", refuting):
            result["consistency"]["evidence"] = "lean_kernel"
            result["validity"]["evidence"] = "lean_kernel"
    else:
        if feasible is not None:
            result["witness"] = {v: str(q) for v, q in feasible.items()}
            result["consistency"] = {"status": "consistent", "evidence": "exact_evaluation"}
            if check("feasible", feasible): result["consistency"]["evidence"] = "lean_kernel"
        if sat.status == "unsat" and check("inconsistent"):
            result["consistency"] = {"status": "inconsistent", "evidence": "lean_kernel"}
            result["validity"] = {"status": "valid", "evidence": "lean_kernel"}
        elif counter.status != "sat" and check("valid"):
            result["validity"] = {"status": "valid", "evidence": "lean_kernel"}
    c, v = result["consistency"], result["validity"]
    result["classification"] = "vacuous" if c["status"] == "inconsistent" and v["status"] == "valid" else v["status"]
    result["explanation"] = (
        "The assumptions contradict each other. The implication is valid vacuously."
        if result["classification"] == "vacuous" else
        "The displayed assignment satisfies every assumption and violates the conclusion."
        if refuting is not None else
        "The original implication was proved. Feasibility is reported separately."
        if v == {"status": "valid", "evidence": "lean_kernel"} else
        "Consult the separate evidence labels. Solver diagnoses are not Lean certificates."
    )
    return result
