"""Check an explicit additional assumption set without replacing the original claim."""
from .diagnose import diagnose, fact
from .ir import Unsupported, canonical, encode, parse


def augmented_problem(p, candidate):
    if not isinstance(candidate, dict) or set(candidate) - {"assumptions", "witness"}:
        raise Unsupported("A repair accepts only additional assumptions and an optional witness")
    additions = candidate.get("assumptions")
    if not isinstance(additions, list):
        raise Unsupported("A repair requires an assumptions list")
    raw = canonical(p)
    raw["assumptions"] += additions
    # A hint for the old model need not satisfy the proposed repair.
    if "witness" in candidate:
        raw["witness"] = candidate["witness"]
    raw["name"] = p.name
    return parse(raw)


def check_repair(p, candidate, backend, verifier=None):
    repaired = augmented_problem(p, candidate)
    original = diagnose(p, backend, verifier)
    revised = diagnose(repaired, backend, verifier)
    validity, consistency = revised["validity"], revised["consistency"]
    status = "unknown"
    if consistency == fact("inconsistent", "lean_kernel"):
        status = "inconsistent"
    elif validity == fact("refuted", "lean_kernel"):
        status = "refuted"
    elif validity == fact("valid", "lean_kernel") and consistency == fact("consistent", "lean_kernel"):
        status = "valid"
    return {"schema_version": 2, "operation": "repair", "status": status,
            "evidence": "none" if status == "unknown" else "lean_kernel", "accepted": status == "valid",
            "original_problem_sha256": original["problem_sha256"],
            "repaired_problem_sha256": revised["problem_sha256"],
            "candidate": {"assumptions": [encode(a) for a in repaired.assumptions[len(p.assumptions):]]},
            "original": original, "repaired": revised}
