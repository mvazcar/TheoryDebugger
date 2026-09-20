# Add Solow–Swan intensive dynamics and square-root steady states

LeanEconomics has no Solow–Swan growth module at the base revision. This adds
the capital-per-worker equation and a first Cobb–Douglas specialization with
capital exponent `1/2` and constant productivity.

The module derives the intensive equation from aggregate accumulation, labour
growth, and constant returns. It proves that the nonnegative stationary stocks
are exactly zero and `(s A / n)^2`, with existence and uniqueness among positive
stocks when `s`, `A`, and `n` are positive. It also proves adjustment signs,
steady-state comparative statics for saving, productivity, and population growth,
and the capital/output ratio `s/n`.

The zero-capital boundary is explicit: a uniqueness argument that divides by
`sqrt(k)` without assuming positive capital would lose a stationary state.
Source references are to Solow (1956), equation (6), footnote 4, and Example 2.

The new module contains 16 proved declarations, is imported by the root module,
and has a README layout entry. Proofs use ordinary Mathlib; no external solver
or TheoryDebugger installation is required. LLM assistance and a separate
TheoryDebugger diagnostic example were used during development. The source is
newly written under the repository's Apache 2.0 license.

Validation: full `lake build` on the repository's pinned Lean/Mathlib
`v4.34.0-rc2`, with no warnings in the new module. A separate local audit checks
the transitive axioms of every new theorem against `propext`, `Classical.choice`,
and `Quot.sound`. No proof placeholders or new axioms are introduced.
Existing warnings elsewhere in the repository are unchanged.

Scope: no ODE existence/uniqueness or global convergence theorem is claimed.
General Cobb–Douglas exponents, depreciation, technical progress, and the golden
rule are possible follow-up contributions. The contribution is based on
`8e7d5172e253cb20af2aea27e53f384d7ef18a25`.
