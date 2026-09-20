# What the growth proofs teach TheoryDebugger

The [Solow–Swan trajectory proof](solow-swan-dynamics.md) and the two
[Uzawa proof routes](uzawa-elasticity-repaired.md) exercise different parts of
the LLM-to-Lean workflow. This document separates changes already implemented
from follow-up tool work. OpenAI Codex assisted under researcher direction;
reasoning settings do not alter the evidence requirements.

## Lessons now represented in executable examples

| Proof issue | Diagnostic lesson | Checked implementation |
| --- | --- | --- |
| Solow zero stationary stock | Cancellation can remove economically meaningful boundaries | `SolowSwan.lean`: mixed original claim, feasible positive repair, inconsistent repair rejected |
| Solow affine path | Positive endpoint stocks and a positive weight do not suffice without the weight's upper bound | `SolowSwanDynamics.lean`: weight restriction and an actual exponential bridge |
| Solow convergence | Adjustment speed needs its own sign assumptions | Same example: exponent restriction checked; full convergence proved separately in Mathlib |
| Uzawa accounting | Balanced-growth accounting may need positive investment for cancellation | `UzawaJones.lean` and the separate contribution |
| Uzawa separation | A condition at one capital/output coordinate does not establish a functional identity over a domain | `UzawaSeparation.lean`: exact polynomial counterexample and derivative bridge |
| Uzawa global coordinates | Inverting a function requires an explicit range and regularity theorem | Mathlib contribution constructs the inverse; range is a visible assumption |

For every repair, the workflow preserves the original proposition, proves the
strengthened implication, and also proves a satisfying assignment exists.
Contradictory restrictions are rejected even though they imply anything.

## Reusable workflow

1. Preserve a primary source with bibliographic details, page locations, and a
   content hash. Separate original assumptions from added hypotheses.
2. Write the full intended theorem before reducing it to algebra. State the
   domain, quantifiers, positivity restrictions, and solution concept.
3. Identify algebraic proof obligations and use TheoryDebugger to search for
   satisfying and refuting cases. A witness is a candidate until Lean checks it.
4. Make proposed repairs explicit. Check feasibility and preserve the original
   claim; do not silently change the theorem.
5. Prove analytic bridges from actual functions and derivatives to the algebra.
   An unproved replacement of a derivative or real power by a variable breaks
   the end-to-end argument.
6. Prove the full theorem in Mathlib. Direction-of-change claims do not replace
   a trajectory theorem, and on-path representation does not establish a global
   technology identity.
7. Include positive examples and excluded-boundary examples. Recompile the
   contributed source fresh, audit transitive axioms, and build the full project.
8. Bind records to source hashes, toolchain, assumptions, and checked commands.
   Report the economic scope and residual interpretation questions alongside
   the successful proof checks.

## Tool limits observed and next work

The native extractor accepts a limited polynomial language. A nested proof
obligation in an unresolved analytic context was rejected during the Solow
example. We used a standalone supported algebraic lemma and a checked analytic
bridge. The rejection was not relabelled as evidence of falsity or bypassed.

The examples and verification scripts now make these obligations reproducible
in CI. They do **not** add automatic derivative abstraction, exponential solving,
or quantifier elimination to the core tool. Useful next improvements are:

- A bridge record linking each abstract variable to a proved analytic identity,
  its domain assumptions, and the concrete theorem that consumes it.
- Clearer unsupported-context diagnostics that identify the obstructing local
  declaration, with a supported standalone-obligation example.
- Explicit scope metadata for pointwise, on-path, and domain-wide statements.
- A review checklist that distinguishes a full convergence result from phase-line
  signs and checks feasibility of the entire model, not only one algebraic slice.

These are follow-up implementation targets, not advertised capabilities. The
proof cases are regression examples for evaluating them. The requested Ultra
review should challenge the source correspondence and assumptions of both
growth proofs before selecting any core changes.
