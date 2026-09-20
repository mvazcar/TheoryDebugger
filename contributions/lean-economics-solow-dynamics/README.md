# Solow–Swan: complete Cobb–Douglas contribution

This package combines the original 16-theorem contribution with 39 additional
theorems. It formalizes positive trajectories for arbitrary `0 < α < 1`,
their uniqueness within the positive solution class, monotone adjustment,
convergence, output limits, comparative statics, and normalization with
depreciation and effective labour. See the [detailed statement, sources and proof](../../docs/solow-swan-dynamics.md).

## Reproduce

Start with a clean LeanEconomics checkout at
`8e7d5172e253cb20af2aea27e53f384d7ef18a25`, using its pinned Lean/Mathlib
`v4.34.0-rc2`. Apply `solow-complete.patch` once:

```sh
git apply /path/to/solow-complete.patch
lake exe cache get
lake build
lake env lean /path/to/SolowAxiomAudit.lean
lake env lean /path/to/SolowFreshAudit.lean
```

The complete patch already includes the original `SolowSwan` module. Do not
apply it on top of the older square-root patch. The fresh audit imports only
Mathlib and re-elaborates every contributed proof, avoiding dependence on
previously compiled versions of the contributed modules.

The local contribution commit is `2a66abe0ecdf6c448fb8c9024e0e94691bf0ac98`,
on `codex/solow-swan-dynamics`. `verification.json` records source and patch
hashes, successful patch application against the exact upstream base, agreement
of the resulting tree with that commit, and reverse-patch validation.

## Checks and scope

The modules contain 55 theorems: 16 in `SolowSwan`, 33 in `SolowSwanDynamics`,
and 6 in `SolowSwanExamples`. Fresh compilation, the full project build, and
all axiom audits passed locally on Windows. No new-module warnings, proof
placeholders, or extra axioms are admitted. The allowed standard axioms are
`propext`, `Classical.choice`, and `Quot.sound`.

The native TheoryDebugger diagnostics run under the separate `v4.34.0` pin:
`python scripts/verify_solow.py` and `python scripts/verify_solow_dynamics.py`.
TheoryDebugger CI checks those examples; it does not compile this external patch.

The main theorem assumes `b>0`, `m>0`, `0<α<1`, `k₀>0` in
`k'=b k^α-mk`. It proves uniqueness among strictly positive differentiable
solutions on future time. A broader class permitted to hit zero, arbitrary
production functions, and the golden rule are outside this package. The exact
exponential convergence rate is for `k^(1-α)`. Solow's original paper is the
checked primary source; Swan's original presentation has not yet been inspected.

## Development credit and license

The additions were developed with **OpenAI Codex**, under the direction of the
TheoryDebugger project maintainer, who sets the research questions and reviews
their economic interpretation. Codex assists with sources, proofs, implementation,
documentation, and tests. This follows LeanEconomics' approach to crediting
Claude and preserves the upstream attribution in the proposed README.
Lean verifies formal statements; economic correspondence requires researcher
review. Reasoning settings are not proof certificates.

Apache 2.0, matching upstream. This package is prepared for review and has not
been submitted publicly. Downloaded papers are excluded from the release.
