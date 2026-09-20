# Proposed Solow–Swan contribution to LeanEconomics

This is a reviewable patch, not an upstream submission. It introduces a
Mathlib-only module with 16 proved statements. See the
[case study](../../docs/solow-swan.md) for the economic assumptions, source
correspondence, and separate TheoryDebugger diagnostic workflow.

- Upstream: https://github.com/LeanEconomics/LeanEconomics
- Base commit: `8e7d5172e253cb20af2aea27e53f384d7ef18a25`
- Required Lean and Mathlib: `v4.34.0-rc2`, using upstream's existing pins.
- Patch: [solow-swan.patch](solow-swan.patch).
- Proposed description: [PR-DRAFT.md](PR-DRAFT.md).
- Local verification: [verification.json](verification.json).
- License: [Apache 2.0](LICENSE.txt). This applies to the contribution's code;
  TheoryDebugger's independently written example remains MIT licensed.

Apply the patch in a clean clone of upstream at the base commit, then run
`lake exe cache get` and `lake build`. Do not apply it to TheoryDebugger's source
tree: its current Lean version differs. The patch changes only the new module,
the root import, and a README layout row. The new module has no Python, external
solver, or TheoryDebugger dependency.

To reproduce the axiom inspection after the build, run
`lake env lean /path/to/SolowAxiomAudit.lean` using the
[supplied audit file](SolowAxiomAudit.lean). The recorded hashes identify the
checked source, and the audit prints the transitive axioms of all 16 theorems.
The recorded local build passed; existing upstream warnings remain, while the
new module had none. No upstream CI result or maintainer acceptance is claimed.

Downloaded papers are not redistributed here. Source citations appear in the
module header and the case study. LLM assistance was used during development;
the Lean kernel checks the final formal propositions, while correspondence to
the economic interpretation still requires human review.
