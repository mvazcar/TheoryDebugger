# Architecture and trust

`JSON → validated AST → cvc5 diagnostic → generated Lean source → Lean check → axiom audit`

`ir.py` contains the solver-independent representation and exact rational
evaluation. `backend.py` defines a small `Backend.check(problem, formula)`
interface and a cvc5 implementation. Another backend can implement this interface
without changing the certificate language. No recovered TheoryGuru implementation
was ported or imported.

For assumptions A and goal G the queries are `∃v, A`, `∃v, A ∧ G`, and
`∃v, A ∧ ¬G`. The first checks feasibility; the last searches for a refutation of
`∀v, A → G`. SAT does not imply an available rational witness. UNSAT of the
last query is only a solver diagnosis until a Lean proof succeeds. The two goal
cases distinguish true, mixed, false and inconsistent models when both are
certified. See [schema 2](evidence-v2.md). An internal
solver time limit and a separate Lean subprocess timeout produce inconclusive
results rather than assumed success. The cvc5 time limit is its own internal
limit, not an operating-system hard kill.

## What Lean checks

Every certificate includes an explicit `original : Prop` with the complete
variable list, all assumptions in their original order, and the original target.
Validity and refutation results are exactly `claim : original` or `refutation : ¬ original`.
It is never a proof of a weaker proxy target. For a contradiction the file also
exports `contradiction : ∀v, A → False` and derives `original` by elimination of
False. For a rational sample it proves each substituted assumption, existence
of a feasible assignment and the relevant goal case. A `no_satisfying` certificate
proves `∀v, A → ¬G`; it is distinct from a single counterexample.

Untrusted witnesses are re-evaluated with exact Python fractions before source
generation and then checked independently by Lean over `ℝ`. Rational constants
are explicitly typed as reals and denominators are positive. Variable names are
mapped to generated identifiers; arbitrary Lean syntax is not accepted as input.

`#print axioms` audits every exported theorem, including the sample steps.
Only `propext`, `Classical.choice`, and `Quot.sound` are allowed. These are Lean's
ordinary foundational axioms; the result is not claimed to be axiom-free.
Missing audits, `sorryAx`, and additional axioms are rejected. No `native_decide`,
solver assertion, custom axiom, or unchecked external proof is used. Compiler
success alone is insufficient. Source SHA-256, compiler output, declaration
names, source lines, and axiom dependencies are retained.

The generator uses separate namespaces in separate certificate files. The files
are independently checkable; they are not intended to be concatenated into one
Lean module without renaming declarations.

## What is outside the guarantee

The kernel checks the emitted formal proposition. It does not prove that a human
sentence was faithfully formalized, that the JSON parser/renderer is correct in
all cases, or that the prose explanation says the same thing. The explicit goal,
variable dictionary, regression tests, and source links make that boundary
reviewable. The native frontend now extracts actual Lean expressions and builds
a term of the original goal type, reducing this translation boundary. See
[the native interface](native-interface.md) for its separate checking path.

An explanation step is backed only if its certificate has `lean_verified`
status. Steps in failed certificate attempts are proposed steps. A source hash
binds a report to its file bytes, not to an abstract mathematical equivalence or
an authenticated historical build environment.

The JSON AST permits Boolean formulas, but the arithmetic proof strategy is
not complete for them (or for nonlinear arithmetic). Solver-only conclusions
remain useful diagnoses but must not be called Lean-certified. Unknown is neither
false nor inconsistent. An inconsistent assumption set makes every implication
valid vacuously and is reported separately from a nonvacuous theorem.

For parameters p, feasibility is `∃x, A(x,p)` while validity is
`∀x, A(x,p) → G(x,p)`. They are different projections. A goal of True makes the
second formula True for every p, even where the first is False. This prototype
does not compute either projected region. In particular it does not claim to
derive the discriminant condition for the quadratic example.

Replacing derivatives or function values with independent real coordinates
requires a semantic bridge. A proof in a justified algebraic relaxation can
transfer to models satisfying its assumptions. A counterexample in the relaxation
need not correspond to a realizable function or economic model. Such a bridge
must be explicit and eventually proved; this prototype rejects functional terms.
