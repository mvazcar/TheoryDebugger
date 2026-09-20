# Formalize Uzawa representation through scaling and repaired elasticity

Add a proof of the published Jones-Scrimgeour (2008) on-path representation
and a strengthened elasticity-based representation inspired by the 2004
working paper. Both recover the original technology at a reference date.
Positive-investment accounting derives equal output, investment, and capital
growth rates instead of assuming that equality in balanced-growth data.

The elasticity theorem explicitly assumes that capital/output ranges over
the positive half-line and that capital shares at each ratio are invariant
across dates. It constructs and differentiates the inverse, derives the
elasticity equation, and uses the mean value theorem to prove separation.
The representation holds for all positive inputs under these stronger
technology hypotheses; accounting then identifies the index's exponential
growth along the observed path. This is a repaired statement, not a claim
to formalize the literal 2004 theorem under its original hypotheses.

Five Mathlib-only modules include 63 theorems and a shared positive
Cobb-Douglas example. The representation proofs use different routes while
sharing the rate-equality lemma. The contribution does not depend on an
external solver or TheoryDebugger at build time.

Validation: full LeanEconomics build on the pinned v4.34.0-rc2 environment;
fresh re-elaboration of all contributed sources; all 63 axiom audits;
no new module warnings and no proof placeholders. The audit permits only
the standard propext, Classical.choice, and Quot.sound axioms. Source hashes
and separate reproducible audits accompany the proposed patch. LLM-assisted
development; human review of the economic correspondence is welcome.
