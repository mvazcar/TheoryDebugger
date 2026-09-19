# Four-way diagnosis and checked repairs (schema 2)

For assumptions `A` and conclusion `H`, each interface checks two questions:
does an assignment satisfying `A ∧ H` exist, and does one satisfying `A ∧ ¬H`
exist? These are `cases.satisfying` and `cases.refuting`.

| Satisfying case | Refuting case | `classification` |
| --- | --- | --- |
| Present | Absent | `true` |
| Present | Present | `mixed` |
| Absent | Present | `false` |
| Absent | Absent | `inconsistent` |
| Either side not established by Lean | | `unknown` |

“False” means failure at every feasible point, with a proof that at least one
feasible point exists. A single counterexample establishes refutation, but may
leave the four-way classification unknown. `inconsistent` means there are no
feasible points; the original implication is then valid vacuously.

Each case has `status: present | absent | unknown` and an independent `evidence`
field. Both interfaces use `lean_kernel`, `exact_evaluation`, `solver_only`, and
`none`. Only the CLI uses the middle two in its main facts; native Lean keeps
untrusted discovery data under `solver_only`. Python rational substitution is
`exact_evaluation`, never a Lean certificate. The top-level classification is
complete only when both cases have `lean_kernel` evidence. Otherwise it is
`unknown`, even if the solver reports a complete classification.

Presence certificates prove `∃v, A ∧ H` or `∃v, A ∧ ¬H`. Absence is established
by a universal implication, respectively `∀v, A → ¬H` or `∀v, A → H`, or by a
contradiction in `A`. The ordinary Lean lemmas in
[`Classification.lean`](../TheoryDebugger/Classification.lean) justify these
equivalences. Every native witness is turned into an existential proof and
checked by the kernel; reported solver evidence labels are ignored.

`validity` retains `valid | refuted | unknown`; `consistency` retains
`consistent | inconsistent | unknown`. They are independent partial results and
carry their own evidence labels. A proved implication with no checked feasible
example remains useful evidence, while its four-way classification is unknown.
Algebraic solver witnesses currently illustrate this limit.

## Check an explicit repair

The CLI takes the original problem and a separate candidate file:

```sh
python -m theorydebugger examples/tax_incidence.json --repair examples/repairs/nonnegative_supply.json
```

The candidate format is `{"assumptions": [[">=", "s", 0]]}`, with an optional
complete exact `witness`. Added assumptions are appended; a candidate cannot
replace the goal, variables, or existing assumptions. Combined size limits are
checked. Original witness hints are not automatically reused for a different
model.

The native equivalent takes a predicate on the original real variables, in
their original order. Underscores mark unused variables:

```lean
#theory_repair (∀ (d s p : ℝ), d < 0 → d*(p+1) = s*p → p ≤ 0)
  with (fun _ s _ => s ≥ 0)
```

Use `#theory_repair_json` for structured output. These commands diagnose both
claims without asserting a theorem. `theory` can still prove the explicitly
revised theorem in the usual Lean workflow.

Repair reports have `operation: repair`, `original`, `candidate`, `repaired`,
`status`, `evidence`, and `accepted`:

| Repair status | Required Lean evidence | Accepted |
| --- | --- | --- |
| `valid` | Revised implication and feasible assignment | Yes |
| `refuted` | Counterexample to the revised implication | No |
| `inconsistent` | Contradiction in the revised assumptions | No |
| `unknown` | Required evidence incomplete | No |

An exit code of zero reports a completed diagnosis, including rejected repairs;
it does not mean the repair was accepted. Unknown and unsupported results exit
with code 2. `--solver-only` leaves the checked classification/acceptance unknown;
its discovery diagnosis is still available in the report.

Each report preserves the complete before/after mathematical input. CLI
`problem_sha256` hashes the canonical ordered input, excluding name and witness
hints. Native `problem_id` is the exact compact JSON representation of its
reified input, with variables named `v0`, `v1`, etc. These identify formal syntax,
not mathematical equivalence, and are not interchangeable across interfaces.
Both are reproducible without trusting a solver-provided identifier.

This operation checks supplied sufficient restrictions. It does not discover
repairs or establish weakest/minimal restrictions. All variables, including any
parameter coordinates, are quantified together: one feasible tuple does not
establish feasibility at every parameter value. Derivative equations still need
an explicit modeling justification outside this scalar fragment.

## Migration from schema 1

- Top-level `classification` is now the checked four-way value, not an alias for
  `validity` or the old `vacuous` label. Inspect `classification_evidence` too.
- Read both witnesses from `cases`; the CLI's older `witness` field selects a
  refuting witness if available, otherwise a satisfying one.
- Native `validity` is now a semantic status/evidence pair. Its proof metadata
  moved to `validity_certificate`; `input` became `problem`. Native certificate
  objects use `status: lean_verified` with `evidence: lean_kernel`.
- CLI certificates remain a list of source files, steps, hashes and axiom
  audits. Native certificate objects contain types and axioms of ephemeral
  proof terms; their commands reproduce the checks. These storage formats differ
  while the mathematical statuses and evidence vocabulary agree.

Run `python scripts/run_repairs.py` to reproduce the paper's supplied repair,
an inconsistent candidate, the `(4,1,2)` failed repair, and native JSON checks.
Saved results are in [`demo/repairs`](../demo/repairs/results.json).
