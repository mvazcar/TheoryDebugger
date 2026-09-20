# Proposed Uzawa / Jones–Scrimgeour contribution

This independent patch is prepared for review and has not been submitted
upstream. It is based directly on LeanEconomics `main` at
`8e7d5172e253cb20af2aea27e53f384d7ef18a25`; it does not depend on our Solow patch.

- [Patch](uzawa-jones.patch), under the [Apache 2.0 license](LICENSE.txt).
- [Proposed pull-request description](PR-DRAFT.md).
- [Local build and axiom audit record](verification.json).
- [Axiom audit source](UzawaAxiomAudit.lean).
- [Economic statement, source versions, and proof map](../../docs/uzawa-jones.md).

The patch adds `Growth/Uzawa.lean`, `Growth/UzawaElasticity.lean`, and
`Growth/UzawaExamples.lean`, their root imports, and one README layout row.
It contains 25 proved declarations, without proof placeholders, new axioms,
or a dependency on TheoryDebugger/Python. The published 2008 on-path theorem
is formalized. The 2004 argument is covered only by the stated local calculus
lemmas, not its entire proof.

Apply this patch to a clean clone of
[LeanEconomics](https://github.com/LeanEconomics/LeanEconomics) at the base
commit. Keep upstream's Lean/Mathlib `v4.34.0-rc2` pins; run
`lake exe cache get` and `lake build`. Then run
`lake env lean /path/to/UzawaAxiomAudit.lean` for the axiom inspection.
Do not apply the patch in TheoryDebugger, which uses a different Lean version.

The full local build and all theorem audits passed, with no warnings in the
new modules. The audit permits only `propext`, `Classical.choice`, and
`Quot.sound`. Existing warnings elsewhere in upstream remain. TheoryDebugger's
Linux CI checks its separate diagnostic example; it does not build this patch.
No upstream CI run or maintainer acceptance is claimed.

LLM assistance was used in the development. Kernel checking establishes the
formal propositions; the documented economic correspondence remains reviewable
by a researcher. Downloaded papers are not redistributed with this code.

## AI development credit

These proposed additions were developed with **OpenAI Codex**, under the direction of
[@mvazcar](https://github.com/mvazcar), who sets the research questions and reviews
their economic interpretation. Codex assisted with source comparison, proof development,
implementation, documentation, and tests. This follows LeanEconomics' approach to
crediting Claude while preserving that upstream attribution. Lean checks the stated
propositions; the source correspondence and adequacy of economic assumptions require
researcher review. Reasoning settings are not proof certificates.

Development and review used **Astra 6** with **Ultra** and **Extra High**
reasoning settings.
