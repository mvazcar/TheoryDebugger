# TheoryGuru (2018) and the current TheoryDebugger prototype

Comparison checked on 2026-09-19 against arXiv:1806.10925v1, including its TeX
source and embedded screenshots. Page references below use the nine-page arXiv
PDF. The screenshots identify TheoryGuru 6.3; the separately recovered private
reference implementation reports 6.6. Those versions must not be conflated.

Source: Casey B. Mulligan, James H. Davenport, and Matthew England,
[*TheoryGuru: A Mathematica Package to apply Quantifier Elimination*](https://arxiv.org/abs/1806.10925).

The paper establishes substantial prior work on the workflow we want: diagnose
a conjecture, inspect examples and counterexamples, and improve its assumptions.
Our current contribution is an independently written, narrower implementation
that connects this workflow to Lean and preserves evidence checked against the
original formal claim. It is not yet a replacement for TheoryGuru's full scope.

## Capability comparison

| Topic | TheoryGuru described in the paper | Our implemented prototype |
| --- | --- | --- |
| Input and solver | Assumptions and hypothesis; Mathematica preprocessing and `Resolve` (§§1.2–2.1, pp.2–3) | Explicit real polynomial JSON or supported native Lean expressions; cvc5 discovers candidate answers |
| Diagnostics | Four outcomes in Table 1, p.2 | Validity and feasibility are separate, but `refuted` does not distinguish mixed behavior from universal failure |
| Witnesses | Dashboard can show instances and counterexamples (§2.1; Fig.3) | Rational assignments can be checked by exact substitution and Lean; algebraic witnesses remain uncertified |
| Parameter ranges | `TheoryPossibilities` projects assumptions onto selected coordinates (p.5, Fig.4) | No general projection; supplied bounds can sometimes be proved |
| Missing assumptions | `TheorySufficient` proposes sufficient restrictions from counterexample projections (p.6, Fig.5) | User-supplied repairs can be checked; automatic repair synthesis is absent |
| Rich notation | Derivatives, integrals, vectors and Gram-matrix restrictions (§2.1; §§3.1–3.2) | Restricted scalar polynomial frontend; modeling reductions must be explicit |
| Proof evidence | The described interface reports and interprets `Resolve` outcomes | Reconstructed Lean proofs/refutations, original-goal checks, axiom audits and saved certificates; incomplete proof search can return unknown |
| Interface | Mathematica notebook dashboard (Fig.3) | Lean commands/tactics and a JSON CLI; no comparable interactive dashboard yet |

The paper does not describe exporting Lean certificates. That observation is
about this paper's interface, not a claim about every later solver or package
version. Likewise, our evidence distinguishes a solver answer from a completed
Lean proof; an unsuccessful reconstruction is not evidence against the theorem.

## An important diagnostic difference

Let `A` be the assumptions and `H` the conclusion. Table 1 classifies assignments
by whether both types of witness exist:

| There exists `A ∧ H` | There exists `A ∧ ¬H` | Paper's label | Current prototype |
| --- | --- | --- | --- |
| Yes | No | True | Consistent and valid |
| Yes | Yes | Mixed | Consistent and refuted |
| No | Yes | False | Consistent and refuted |
| No | No | Contradictory Assumptions | Inconsistent; implication valid vacuously |

Our two queries are currently `∃v, A` and `∃v, A ∧ ¬H`. A refutation disproves
the universal implication, but does not say that the conclusion fails at every
admissible point. Adding a query for `∃v, A ∧ H`, with separately checked evidence,
would recover this useful distinction. Solver timeouts and failed reconstruction
must remain a separate unknown outcome. This comparison identifies the change;
it does not implement the new classification.

## Direct comparison: the paper's tax-incidence example

Our earlier [economics examples](economics.md) included a supply shift, a revenue
comparison, and linear monopoly pricing. The revenue example was not the tax
incidence example in this 2018 paper. We have now added a direct scalar
transcription in [Paper2018Tax.lean](../examples/Paper2018Tax.lean).

In Section 3.1, buyers pay the seller's price plus a per-unit tax. Write `d` for
the demand slope, `s` for the supply slope, and `p` for the derivative of the
seller's price with respect to tax. Differentiating equilibrium gives:

```text
d × (p + 1) = s × p
```

We explicitly assume this equation. The new file does not formalize the
functions, perform differentiation, or prove existence of a differentiable
equilibrium.

Actual executions with our native Lean frontend established:

1. With `d < 0` and `s > 0`, `theory` proves `p < 0` and `p > -1` separately.
   These check the two strict bounds displayed in Figure 4. We supplied the
   proposed bounds; we did not discover them by parameter projection.
2. With the supply restriction removed, the conjecture `p ≤ 0` is refuted.
   The solver found `d = -1`, `s = -3`, `p = 1/2`; Lean checked it.
3. Adding `s ≥ 0` proves the original weak goal `p ≤ 0`. We supplied this
   repair from Figure 5; our program did not synthesize it.
4. Two explicit ground proofs certify a satisfying assignment
   `(d,s,p) = (-1,1,-1/2)` and a refuting assignment `(-1,-2,1)` when the supply
   restriction is absent. Together they establish mixed behavior even though
   the diagnostic currently prints only `refuted`.

The three universal theorems and two ground proofs compiled successfully. Their
axiom audits contain only `propext`, `Classical.choice`, and `Quot.sound`.
The diagnostics also checked feasible assignments for all four invocations.
See the [compiler output](../demo/paper-2018-tax-output.txt) and
[verification record](../demo/paper-2018-tax-verification.json).

To reproduce after installing the adapter and building the package:

```sh
lake env lean examples/Paper2018Tax.lean
```

Set `THEORYDEBUGGER_PYTHON` if the adapter's Python interpreter is not the one
selected by `python`. This is the same setup as the other native examples.

## Priorities suggested by the comparison

1. Add checked evidence for both satisfying and refuting assignments, so a
   researcher can distinguish a conditional result from one that always fails.
2. Make the repair loop explicit: preserve the original claim, show each proposed
   assumption change, and require feasibility as well as a proof after every edit.
3. Add selected parameter projections only with a clear evidence policy. A solver
   projection is useful discovery output, but proving one direction of a proposed
   bound is not a proof that it describes the exact feasible region.
4. Extend function and derivative support through explicit modeling lemmas before
   treating abstract derivative tuples as realizable economic counterexamples.

These are development priorities inferred from the comparison. They are not new
claims about the paper or features already present in the prototype. We have not
replicated the gender-selection model or the historical performance table here.

## Attribution and naming

The prior work is by Mulligan, Davenport and England. We should credit the full
author team and TheoryGuru when describing the inspiration for this project.
The paper's text and TeX do not use `TheoryDebugger`; the figures show the names
TheoryGuru and Proof & Logic Tools. `TheoryDebugger` remains our working name,
drawn from the project handoff, rather than a claim about an unused or exclusive
name.

The paper and its TeX source are research references kept outside this project's
original MIT source tree. This document and the scalar Lean example were newly
written; no recovered proprietary implementation is imported.
