# Combined Uzawa contribution: published and repaired elasticity proofs

This complete patch contains the published Schlicht/Jones-Scrimgeour on-path
proof and a second representation argument motivated by the 2004 elasticity
method. The second theorem explicitly assumes a global positive ratio range
and share invariance at every positive capital/output coordinate. It does not
claim to prove the literal November 2004 statement.

- [Complete patch](uzawa-complete.patch), under the [Apache 2.0 license](LICENSE.txt).
- [Proposed PR description](PR-DRAFT.md).
- [Full build and 63-declaration audit record](verification.json).
- [Independent fresh-source audit](UzawaFreshAudit.lean).
- [Audit of built modules](UzawaAxiomAudit.lean).
- [Additional zero-investment obstruction proofs](UzawaVersionAudit.lean)
  and their [separate three-lemma record](version-audit-verification.json).
- [Detailed repaired statement and proof map](../../docs/uzawa-elasticity-repaired.md).
- [Source-version comparison](../../docs/uzawa-versions-comparison.md).

## Apply and verify

The complete patch applies to a clean LeanEconomics checkout at
`8e7d5172e253cb20af2aea27e53f384d7ef18a25`, with upstream's pinned
Lean/Mathlib `v4.34.0-rc2`. Apply `uzawa-complete.patch` once using
`git apply /path/to/uzawa-complete.patch`. This patch includes the previous
25-declaration Uzawa contribution, so start from the upstream base rather
than applying it on top of the older `uzawa-jones.patch`.

Run `lake exe cache get`, then `lake build`. Inspect the compiled modules with
`lake env lean /path/to/UzawaAxiomAudit.lean`. For a fresh recompilation of
every contributed proof without importing contributed compiled artifacts,
run `lake env lean /path/to/UzawaFreshAudit.lean`. Its imports are Mathlib-only.
Run `lake env lean /path/to/UzawaVersionAudit.lean` for the separate obstruction.

## Content and scope

The five modules contain 63 theorems: 16 in `Uzawa`, 3 in `UzawaElasticity`,
6 in `UzawaExamples`, 28 in `UzawaSeparation`, and 10 in
`UzawaSeparationExamples`. The new proof constructs the global inverse,
proves its regularity, establishes separation by the mean value theorem,
recovers the original technology, and calibrates the labor index using
positive-investment accounting. A square-root Cobb-Douglas family verifies
the stronger assumptions and the same positive balanced-growth economy
used for the published proof.

The two representation arguments share an accounting lemma; the repaired
proof does not invoke the published representation theorem. The global
range is an explicit hypothesis, not derived here from Inada conditions.
The additional three-lemma obstruction audit is not counted among the 63;
its statement and remaining economic interpretation boundaries are explicit.

The full local project build and fresh audit passed. New modules have no
warnings, proof placeholders, or new axioms. Only `propext`, `Classical.choice`,
and `Quot.sound` are admitted by the audit. Existing upstream warnings are
unchanged. TheoryDebugger's CI checks the separate native diagnostics;
it does not build this external LeanEconomics patch.

This package is prepared for review and has not been submitted to public
upstream. LLM assistance was used. Kernel checking verifies the formal
statements; the economic interpretation remains open to researcher review.
Downloaded papers are excluded from the source release.
