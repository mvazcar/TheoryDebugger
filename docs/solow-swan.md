# Solow–Swan: from an informal argument to checked Lean

**Historical first contribution.** The [general Cobb–Douglas dynamics extension](solow-swan-dynamics.md)
now supplies the trajectory, uniqueness, and convergence results identified as
next steps below, with a detailed statement, proof, source map, and 59-theorem audit.

This is a first, deliberately narrow contribution toward formalizing the
Solow–Swan model in [LeanEconomics](https://github.com/LeanEconomics/LeanEconomics).
TheoryDebugger supplies diagnostic feedback during development. The proposed
LeanEconomics module uses only Mathlib and can be checked independently.

## Source and model

Robert M. Solow, *A Contribution to the Theory of Economic Growth*, Quarterly
Journal of Economics 70(1), 65–94 (1956),
[DOI 10.2307/1884513](https://doi.org/10.2307/1884513), equation (6), p. 69 and
Cobb–Douglas Example 2, pp. 76–77. Footnote 4, pp. 70–71, explicitly discusses
the zero-capital exception.

Let aggregate capital and labour be `K(t)` and `L(t)`, with `L(t) > 0`.
Constant returns gives `F(K,L) = L f(K/L)`. From `K' = s F(K,L)` and `L' = n L`,
the quotient rule yields `k' = s f(k) - n k` for `k = K/L`.
This version has net output and no separate depreciation term. The first
specialization is `f(k) = A sqrt(k)`, with constant productivity `A` and
Cobb–Douglas exponent `1/2`. It does not cover arbitrary capital exponents.

For positive saving, productivity, and labour growth, define
`k* = (s A / n)^2`. Saving is usually restricted to at most one in the economic
interpretation; our comparative-statics implications remain true without that
upper bound. Every theorem states its exact sign assumptions.

## The proposed informal proof — and its error

The following is our teaching example, **not a quotation or an error attributed
to Solow**:

> A stationary stock satisfies `s A sqrt(k) = n k`. Divide by `sqrt(k)` to get
> `sqrt(k) = s A / n`. Squaring gives `k = (s A / n)^2`, so the stationary stock
> is unique.

This argument assumes `sqrt(k)` is nonzero. It loses the stationary state `k=0`.
The correct conclusion is uniqueness **among strictly positive stocks**.
With `s,A,n > 0`, both `0` and `k*` are stationary and `k* > 0`.

## Executed TheoryDebugger workflow

[The Lean example](../examples/SolowSwan.lean) uses `s=1/2`, `A=2`, `n=1`.
Introduce `q=sqrt(k)`, so stationarity becomes `q-q^2=0`. The theorem
`square_root_bridge` checks the equation translation on nonnegative capital;
`normalized_positive_stationary_capital` applies the repaired algebraic result
back to actual `sqrt(k)` production. We never treat an unproved replacement of
square roots by arbitrary variables as a certificate.

1. Diagnose `q ≥ 0` and `q-q^2=0` implying `q=1`. The original claim is mixed:
   `q=0` refutes it, while `q=1` satisfies it. Lean checks both witnesses.
2. Explicitly propose `q>0`. TheoryDebugger checks the unchanged conclusion
   against all original hypotheses plus this restriction, and checks that the
   repaired assumptions have a satisfying assignment.
3. Try the excessive restriction `q>1`. It makes stationarity impossible, so
   the repair must be rejected as inconsistent even though an implication from
   contradictory assumptions is vacuously true.
4. Prove the repaired theorem with `theory`, connect it to `k`, and audit its
   transitive axioms. Also prove the signs of `q-q^2` on either side of one.

Run `python scripts/verify_solow.py` in the pinned TheoryDebugger environment.
It checks the diagnostic classifications, both repair decisions, exact witness
values, preservation of the original claim, and all six theorem axiom reports.
It saves the compiler output and a report with source hashes in `demo/solow/`.
Recompiling the Lean source is the reproducible proof certificate; the JSON log
by itself is not a proof.

## Proposed LeanEconomics contribution

The separate branch `codex/solow-swan`, based on upstream commit
`8e7d5172e253cb20af2aea27e53f384d7ef18a25`, adds
`LeanEconomics/Growth/SolowSwan.lean`, its root import, and a README layout entry.
It uses upstream's Lean/Mathlib `v4.34.0-rc2` pin; TheoryDebugger currently uses
`v4.34.0`. Each has been checked in its own environment.
The [contribution package](../contributions/lean-economics/README.md) preserves
the patch, local verification record, and Apache 2.0 license for review.

| Formal statement | Economic content |
| --- | --- |
| `intensiveForm_of_homogeneous` | Constant returns implies the per-worker normalization |
| `hasDerivAt_capitalPerWorker` | The aggregate equations imply the intensive-form derivative |
| `capitalChange_eq_zero_iff` | Nonnegative stationary stocks are exactly zero and `k*` |
| `existsUnique_positive_steadyState` | Existence and uniqueness on positive capital stocks |
| `capitalChange_pos_of_lt`, `capitalChange_neg_of_gt` | The direction of adjustment below and above `k*` |
| `steadyState_strictMono_saving`, `steadyState_strictMono_productivity` | Higher saving or productivity raises `k*` |
| `steadyState_strictAnti_population` | Higher labour growth lowers `k*` |
| `steadyState_capital_output_ratio` | The stationary capital/output ratio equals `s/n` |

The first two statements are in `LeanEconomics.SolowSwan`; the rest are in its
`SquareRoot` namespace. Supporting lemmas make 16 proved declarations in total.
Their proofs use ordinary Mathlib tactics, without a TheoryDebugger dependency.
The contribution is newly written and follows upstream's Apache 2.0 license.
The TheoryDebugger example is independently written under this project's Unlicense
dedication. Downloaded papers stay in the private research archive.

## Next results and boundaries

The phase-line inequalities are not a proof of global convergence of solutions.
A next contribution should establish trajectories, their positivity, and their
limit under stated initial conditions. Then generalize to `0 < α < 1` using
Mathlib's real powers, and separate out depreciation and technical progress.
Saving/consumption tradeoffs and the golden-rule result belong in a later module.

Swan's original 1956 article is identified by
[DOI 10.1111/j.1475-4932.1956.tb00434.x](https://doi.org/10.1111/j.1475-4932.1956.tb00434.x),
but a downloadable copy was not obtained in this run. The downloaded
[Dimand–Spencer historical study](https://www.nber.org/papers/w13950) is
background, not a substitute for that primary source. Claims specific to Swan's
presentation still require checking against the original.

LLM assistance helped translate and implement the arguments. Lean checks the
stated propositions; a researcher must still inspect their correspondence with
the intended economic model. This remains an application of TheoryDebugger as
a complement to TheoryGuru, and a practical way to learn both workflows.
