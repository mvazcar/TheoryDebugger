"""Generate closed Lean proofs; accept only successfully audited declarations."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
from .ir import canonical, evaluate

IMPORTS = """import Mathlib.Basic.Real.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Positivity

set_option maxHeartbeats 400000
namespace TheoryDebugger.Generated
"""
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}


def lean_rat(q):
    if q.denominator == 1:
        return f"({q.numerator} : ℝ)"
    return f"(({q.numerator} : ℝ) / {q.denominator})"


def render(n, names):
    if n.op == "var": return names[n.args[0]]
    if n.op == "rat": return lean_rat(n.args[0])
    if n.op == "true": return "True"
    if n.op == "false": return "False"
    if n.op == "^": return f"({render(n.args[0], names)} ^ {n.args[1]})"
    if n.op in {"neg", "not"}:
        return f"({'-' if n.op == 'neg' else '¬'} {render(n.args[0], names)})"
    op = {"and": "∧", "or": "∨", "!=": "≠", "<=": "≤", ">=": "≥"}.get(n.op, n.op)
    return "(" + f" {op} ".join(render(a, names) for a in n.args) + ")"


def symbols(p):
    return {v: f"v{i}" for i, v in enumerate(p.variables)}


def formal_goal(p, target=None):
    names = symbols(p)
    binders = "".join(f"∀ ({v} : ℝ), " for v in names.values())
    premises = "".join(render(a, names) + " → " for a in p.assumptions)
    return binders + premises + (render(p.goal, names) if target is None else target)


def base_source(p):
    return IMPORTS + f"\n-- Variable dictionary: {json.dumps(symbols(p), sort_keys=True)}\n" + \
        f"def original : Prop :=\n  {formal_goal(p)}\n\n"


def build_source(p, kind, witness=None):
    if kind not in {"valid", "inconsistent", "false_throughout", "feasible", "satisfying", "counterexample"}:
        raise ValueError("Unknown certificate kind: " + kind)
    source = base_source(p)
    steps = []
    declarations = []

    def add(name, statement, proof, explanation):
        nonlocal source
        line = len(source.splitlines()) + 1
        source += f"theorem {name} : {statement} := by\n{proof}\n\n"
        declarations.append(name)
        steps.append({"declaration": f"TheoryDebugger.Generated.{name}", "line": line,
                      "statement": statement, "explanation": explanation})

    if kind in {"valid", "inconsistent", "false_throughout"}:
        variables = list(symbols(p).values())
        intro = variables + [f"h{i}" for i in range(len(p.assumptions))]
        proof = "  unfold original\n" if kind == "valid" else ""
        if intro: proof += "  intro " + " ".join(intro) + "\n"
        for i, v in enumerate(variables if kind != "valid" or p.goal.op != "true" else []):
            proof += f"  have square_{i} : 0 ≤ {v} ^ 2 := sq_nonneg {v}\n"
            steps.append({"local_lemma": f"square_{i}", "explanation": f"The square of {p.variables[i]} is nonnegative.",
                          "statement": f"0 ≤ {v} ^ 2", "line": len(source.splitlines()) + 2 + len(proof.splitlines()) - 1})
        for i, a in enumerate(p.assumptions if kind == "valid" and p.goal.op != "true" else []):
            if a.op == ">" and a.args[0].op == "var" and a.args[1].op == "rat" and a.args[1].args[0] == 0:
                name = a.args[0].args[0]
                v = symbols(p)[name]
                proof += f"  have positive_square_{i} : 0 < {v} ^ 2 := by positivity\n"
                steps.append({"local_lemma": f"positive_square_{i}",
                              "explanation": f"Assumption {i + 1} says {name} is positive, so its square is strictly positive.",
                              "statement": f"0 < {v} ^ 2", "line": len(source.splitlines()) + 1 + len(proof.splitlines())})
        if kind == "false_throughout":
            proof += "  intro h_goal\n"
        proof += "  exact True.intro" if kind == "valid" and p.goal.op == "true" else \
            "  first | (solve | norm_num at *) | nlinarith"
        statement = "original" if kind == "valid" else formal_goal(p, "False")
        if kind == "false_throughout":
            statement = formal_goal(p, f"¬ {render(p.goal, symbols(p))}")
        add({"valid": "claim", "inconsistent": "contradiction", "false_throughout": "no_satisfying"}[kind],
            statement, proof,
            "The original goal follows by checked arithmetic from the listed assumptions and nonnegative squares."
            if kind == "valid" else "The goal fails under every feasible assignment."
            if kind == "false_throughout" else "The listed assumptions imply False; there is no feasible real assignment.")
        if kind == "inconsistent":
            call = " ".join(["contradiction", *variables, *[f"h{i}" for i in range(len(p.assumptions))]])
            proof = "  unfold original\n"
            if intro: proof += "  intro " + " ".join(intro) + "\n"
            proof += f"  exact False.elim ({call})"
            add("claim", "original", proof,
                "The original implication is valid vacuously because its assumptions contradict each other.")
    else:
        if witness is None or set(witness) != set(p.variables):
            raise ValueError("Incomplete witness")
        if not all(evaluate(a, witness) for a in p.assumptions):
            raise ValueError("Witness does not satisfy every original assumption")
        if kind == "counterexample" and evaluate(p.goal, witness):
            raise ValueError("Witness does not refute the original goal")
        if kind == "satisfying" and not evaluate(p.goal, witness):
            raise ValueError("Witness does not satisfy the original goal")
        values = {v: lean_rat(witness[v]) for v in p.variables}
        for i, a in enumerate(p.assumptions):
            add(f"sample_h{i}", render(a, values), "  norm_num",
                f"Exact substitution verifies assumption {i + 1} at the displayed witness.")
        existence_names = {key: "_" + value for key, value in symbols(p).items()}
        existential = "".join(f"∃ ({v} : ℝ), " for v in existence_names.values()) + render(p.antecedent, existence_names)
        proof = ""
        if values: proof += "  refine ⟨" + ", ".join(values.values()) + ", ?_⟩\n"
        proof += "  norm_num"
        add("feasible", existential, proof, "This exact real assignment satisfies all original assumptions together.")
        if kind in {"satisfying", "counterexample"}:
            target = render(p.goal, existence_names)
            if kind == "counterexample":
                target = f"¬ {target}"
            side_exists = "".join(f"∃ ({v} : ℝ), " for v in existence_names.values()) + \
                f"({render(p.antecedent, existence_names)} ∧ {target})"
            add("satisfying" if kind == "satisfying" else "refuting", side_exists, proof,
                "This assignment jointly satisfies the assumptions and the stated side of the goal.")
        if kind == "counterexample":
            add("sample_not_goal", f"¬ {render(p.goal, values)}", "  norm_num",
                "At the same assignment the original conclusion is false.")
            args = " ".join([*values.values(), *[f"sample_h{i}" for i in range(len(p.assumptions))]])
            add("refutation", "¬ original",
                "  intro h\n  unfold original at h\n" + f"  exact sample_not_goal (h {args})",
                "Applying the original universal claim to this witness contradicts the checked failed conclusion.")
    for decl in declarations:
        source += f"#check {decl}\n#print axioms {decl}\n"
    source += "end TheoryDebugger.Generated\n"
    return source, declarations, steps


def audit_axioms(output, declarations):
    axioms = {}
    for name in declarations:
        qualified = "TheoryDebugger.Generated." + name
        empty = f"'{qualified}' does not depend on any axioms"
        match = re.search(re.escape("'" + qualified + "'") + r" depends on axioms:\s*\[([^]]*)\]", output)
        if empty in output:
            found = []
        elif match:
            found = [a.strip() for a in match.group(1).split(",") if a.strip()]
        else:
            raise ValueError(f"Missing axiom audit for {qualified}")
        if set(found) - ALLOWED_AXIOMS:
            raise ValueError(f"Unapproved axiom dependencies: {found}")
        axioms[qualified] = found
    return axioms


class LeanVerifier:
    def __init__(self, project, output, lake="lake", timeout=90):
        self.project = Path(project).resolve()
        self.output = Path(output).resolve()
        self.lake = lake
        self.timeout = timeout

    def verify(self, p, kind, witness=None):
        source, declarations, steps = build_source(p, kind, witness)
        digest = hashlib.sha256(source.encode()).hexdigest()
        folder = self.output / digest[:20]
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "Certificate.lean"
        path.write_text(source, encoding="utf-8", newline="\n")
        result = {"status": "unknown", "source": str(path), "source_sha256": digest,
                  "formal_goal": formal_goal(p), "steps": steps, "axioms": {}}
        try:
            run = subprocess.run([self.lake, "env", "lean", "-o", str(folder / "Certificate.olean"), str(path)],
                                 cwd=self.project, capture_output=True, text=True, encoding="utf-8",
                                 errors="replace", timeout=self.timeout)
            output = run.stdout + run.stderr
            (folder / "lean-output.txt").write_text(output, encoding="utf-8", newline="\n")
            result["compiler_exit_code"] = run.returncode
            result["compiler_log"] = str(folder / "lean-output.txt")
            if run.returncode != 0:
                result["reason"] = "Lean did not complete this certificate; see compiler log"
                return result
            result["axioms"] = audit_axioms(output, declarations)
            result["status"] = "lean_verified"
            result["declarations"] = ["TheoryDebugger.Generated." + d for d in declarations]
        except (OSError, subprocess.TimeoutExpired, ValueError) as e:
            result["reason"] = str(e)
        return result
