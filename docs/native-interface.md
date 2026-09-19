# Native Lean interface

`TheoryDebugger/Frontend.lean` reads the actual local context and target. It
accepts explicit variables of type ℝ and supported polynomial propositions.
`TheoryDebugger/Tactic.lean` asks cvc5 for discovery and independently constructs
Lean proof terms against the original expressions. It never imports a solver
truth value as a proof or reads solver output as Lean code.

## Run it

From the standalone project, activate a Python environment and run
`python -m pip install -e .`. Install the pinned Lean toolchain and Mathlib
artifacts using the README instructions, then run:

```sh
lake build
lake env lean examples/Native.lean
lake env lean lean-tests/Native.lean
```

Lean invokes `python -m theorydebugger.bridge` using a direct subprocess and JSON
on standard input. No shell is involved. If Python is not on the editor's path,
set `THEORYDEBUGGER_PYTHON` to its absolute executable path before launching the
editor, or set `theoryDebugger.python` in Lean. The environment variable takes
precedence. `theoryDebugger.timeoutMs` defaults to 2000 per solver query and the
bridge accepts 1..10000. This is a cvc5 internal time limit, not an OS process
deadline. The Python package must be installed in the selected interpreter.

`set_option theoryDebugger.solver false` disables discovery. Native implication
proofs still work; missing feasibility evidence remains unknown. A failed or
missing bridge never establishes that assumptions are feasible or inconsistent.

## Meaning and trust

Each reified expression is checked for definitional equality with a reconstruction
using fixed real operations. This rejects an overloaded `+` that actually means
subtraction even though its surface notation looks like an ordinary polynomial.
No user hypothesis is silently dropped. Lean's synthetic internal declaration
for the theorem being elaborated is excluded; closure checks ensure that it
cannot enter any certificate.

The closed validity obligation universally quantifies all captured real variables
and includes every captured hypothesis in order. Proof search runs in an empty
local context. This prevents the active assumptions from being accidentally
reused to prove a witness or a claim with a hypothesis removed.

For rational witnesses, Lean substitutes exact real rational expressions into
the original assumptions. A refutation additionally proves the negation of the
original specialized implication and derives the negation of the full universal
claim. The native witness need not be the same one chosen in the saved CLI demo:
different correct counterexamples are acceptable. The specific `(4,1,2)` repair
regression is also checked directly in native tests.

Each proof is submitted as a temporary closed theorem to Lean's kernel, and its
transitive axiom dependencies are audited. Only `propext`, `Classical.choice`,
and `Quot.sound` are accepted. The temporary declaration is removed afterward.
For `theory`, the retained proof term is applied to the actual local variables
and hypotheses, its type is checked against the current target, and that goal
is assigned. Final theorem elaboration checks the resulting proof too.

`theory?` and the `#theory` commands make no theorem assertion. They retain the
checked proof terms only during diagnosis. Their evidence can be reproduced by
compiling the source command again. `#theory_json` records the types and axiom
dependencies of successful checks, along with solver-only data under a separate
field. The CLI remains the interface for persistent exported certificate files.

## Scope and behavior

Recognition covers real numeral/rational constants, addition, subtraction,
multiplication, negation, natural powers through eight, comparisons, and Boolean
combinations. Only literal rational division is accepted: `(-1 : ℝ)/3` works;
`x/3` is currently rejected. No automatic division clearing is performed.

Local definitions, natural/integer variables, arbitrary casts, function values,
derivatives, and quantified local hypotheses are rejected. Top-level universal
quantifiers and implications in `#theory` establish the context; nested
quantifiers inside a target or hypothesis are not supported. Unsupported syntax
does not become an independent scalar variable. The native frontend limits
contexts to eight real variables and 30 hypotheses and recursive syntax depth
to 32; the Python representation has additional node limits.

`nlinarith`, `positivity`, and exact normalization are incomplete proof search.
An algebraic counterexample without a rational witness is a solver diagnosis,
not a checked refutation. Native output says unknown to Lean in that case.
These outcomes are intentional boundaries, not evidence that the claim is true.

Individual-removal certificates prove the original target under each smaller
assumption set. They do not establish that all flagged hypotheses can be removed
together. No minimization is performed. If the original assumptions contradict
each other, that fact and vacuous validity are reported prominently.
