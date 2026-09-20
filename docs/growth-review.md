# Solow–Swan and Uzawa review

20 September 2026. The user requested the Ultra setting for this review; the
app accepted the setting before the follow-up work. Earlier development is not
retroactively described as an Ultra run. The evidence below is compilation,
proof dependencies, source correspondence and executed diagnostics, not a
claim that a reasoning setting itself establishes correctness.

## Results

| Development | Review finding | Action |
| --- | --- | --- |
| Solow–Swan | The initial trajectory theorem assumed future strict positivity when proving uniqueness | Added a weighted-capital argument deriving strict positivity for every nonnegative solution with positive initial stock; uniqueness and convergence now cover that larger class |
| Published Uzawa route | The conclusion is on the balanced path; positive investment is needed in the rate argument | Retained those assumptions and scope; rechecked the source and all proof dependencies |
| Repaired elasticity route | Global range and share invariance over the whole positive coordinate domain are stronger than the literal 2004 hypotheses | Retained the explicit repair and distinct theorem label; checked inverse construction, regularity, separation and calibration |
| TheoryDebugger | Nested `have` statements could retain assigned elaboration variables and lose supported proof/witness checks | Normalize existing assignments before closure and witness construction; add regression tests for validity, feasibility, unresolved propositions and hidden dependencies |
| Attribution | AI assistance should be explicit, following LeanEconomics' Claude credit | Added OpenAI Codex attribution under researcher direction to the README and contribution packages, preserving upstream credit and licenses |

## Solow–Swan

The reviewed theorem is `nonnegative_dynamics` in the Cobb–Douglas namespace.
For `b,m,k₀>0` and `0<α<1`, it constructs a nonnegative solution of
`k'=b k^α-mk`; every nonnegative differentiable solution with initial value
`k₀` is strictly positive, equals the constructed path for all `t≥0`, and
converges to `(b/m)^(1/(1-α))`.

The added estimate is elementary but closes a meaningful scope gap:
`d[k(t)exp(mt)]/dt=b k(t)^α exp(mt)≥0`. Thus
`k(t)exp(mt)≥k₀>0`. It does not presume the explicit solution or use the
uniqueness result it helps prove. Zero initial capital remains a separate
boundary case. The full source-to-statement discussion and detailed argument
are in [Solow–Swan dynamics](solow-swan-dynamics.md).

The updated contribution has **59 theorems**: 16 original, 37 dynamics, and
6 examples. All were freshly re-elaborated with a full LeanEconomics build.
The contribution commit is `4bed57534cf4f5562be8b90c481bb3dd54360fe0`.

## Both Uzawa routes

The review inspected Jones–Scrimgeour's supplied November 2004 formulation,
their published 2008 theorem on p. 181, and Schlicht's published proof on
numbered p. 2. It compared those statements with the actual Lean hypotheses,
not only with theorem names. Source PDFs and their hashes remain in the private
archive; source links appear in the [version comparison](uzawa-versions-comparison.md).

The published proof derives `gY=gI=gK` from resource feasibility and accumulation,
then applies homogeneity of the original technology at the reference date.
The three-date weighted-square argument is a valid alternative to the paper's
second differentiation. Nonnegative consumption and strictly positive investment
are explicit. It proves neither a global technology identity nor a claim about
the invention process.

The repaired route constructs the capital/output inverse from strict monotonicity
and the explicit positive-half-line range hypothesis. Its derivative and the
elasticity identity are proved. Domain-wide share invariance makes the ratio of
the two coordinate technologies constant in the input coordinate; reconstruction
then yields the global identity. The shared accounting lemma calibrates the
time index on the balanced path. It does not call the published representation
theorem. The stronger share and range assumptions remain visible and are not
renamed as a proof of the literal 2004 statement.

Fresh compilation rechecked **all 63 Uzawa theorems**, with the source hash
matched to the packaged audit and every transitive axiom list checked. The
three additional obstruction lemmas were also recompiled. No source correction
to the two completed Uzawa arguments was required by this review. The informal
Inada calculations in the zero-investment discussion remain mathematical
exposition, not a claim to have formalized the full 2004 countermodel.

## Tool correction and evidence boundary

The Solow regression originally failed even though the nested algebraic statement
was in the supported language. Lean had assigned its elaboration variables, but
the stored expressions still contained references to them. A probe confirmed that
substituting those assignments produced a closed proposition without free or
unresolved variables. The frontend now performs that substitution for both
universal closure and the propositions used in witness checks.

This is not a relaxation of the certificate boundary. Hidden free variables
still fail; genuinely unresolved propositions still fail; proofs are still
checked in an empty local context and audited for allowed axioms. The nested
regression requires a checked satisfying assignment as well as validity and
verifies that diagnosis leaves the original goal unchanged. Existing forged-
evidence, removed-assumption, and placeholder tests remain in the native suite.

The [verification record](../demo/growth-review/verification.json) identifies
the exact checked sources. [Further lessons](growth-proof-lessons.md) distinguish
the implemented fix from proposed future analytic-bridge metadata. No automatic
exponential solver, derivative abstraction, or general quantifier elimination
is claimed.

## Credit

Developed and reviewed with **OpenAI Codex**, under the direction of the
TheoryDebugger project maintainer, who selects the research questions and reviews
the economic interpretation. This follows LeanEconomics' transparent attribution
of Claude's contribution. Lean verifies the encoded propositions; interpreting
them as economic claims still requires researcher judgment. TheoryDebugger is a
complement to TheoryGuru. No public upstream submission or repository visibility
change is part of this review.
