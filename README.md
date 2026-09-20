# TheoryDebugger

TheoryDebugger aims to be an **open-source complement to TheoryGuru, adding
Lean capabilities**, so researchers using LLMs can improve their mathematical
research workflows. The central idea is to give an LLM a claim and an informal
proof, let it use automated reasoning tools to examine the logic, and obtain a
Lean formalization with checked proof evidence.

This is also a learning project. We want to understand both **TheoryGuru and
Lean** by studying TheoryGuru's reasoning workflow, implementing its ideas in
original open-source code, and learning how Lean and Mathlib express and verify
the corresponding mathematics. Small economic examples let us compare behavior,
explain what we learn, and build toward more useful research tools. See the
[TheoryGuru comparison](docs/theoryguru-comparison.md) and
[guided economics examples](docs/economics.md).

## Intended research workflow

**Your informal argument → LLM-assisted formalization → diagnostic feedback →
revised formalization → Lean-checked proof and certificate.**

1. **The researcher supplies a claim and an informal proof**, together with the
   definitions, assumptions, and economic interpretation.
2. **The LLM translates the argument into explicit mathematical statements**,
   breaking it into steps and mapping them to Lean definitions and lemmas.
3. **The LLM uses TheoryDebugger to check supported steps**, search for
   counterexamples, diagnose contradictory assumptions, and test proposed repairs.
4. **The LLM revises the formalization using that feedback**, preserving the
   original claim and making any proposed change to the claim or assumptions
   explicit for the researcher to review.
5. **When verification succeeds, the researcher receives a compiling Lean
   proof**, reproducible verification evidence, and a readable correspondence
   between the original argument and the checked statements. Unresolved steps
   remain visible as incomplete work.

Two questions matter throughout: does the formal statement faithfully express
the researcher's argument, and does its proof check? Lean checks the formal
proof. Faithfulness to the intended mathematics requires an inspectable
translation, including any modeling assumptions. An LLM's explanation alone
does not settle either question.

## What works today

The current prototype provides the **checking component** for explicit real
polynomial claims. It has native Lean commands and a JSON CLI, four-way
diagnosis, checked witnesses, and explicit repair checks requiring both validity
and feasibility. It can produce Lean proofs and exported certificate files for
supported claims when proof reconstruction succeeds.

The complete informal-proof-to-Lean assistant described above is the intended
workflow. Automated translation of informal arguments and orchestration of an
LLM through that workflow are still to be built and evaluated. The current tools
provide a foundation for this work and can already be called by an external LLM.

## Explore directly in Lean

Install the Python adapter and build the package as described below, then open
[examples/Native.lean](examples/Native.lean) in a Lean editor. The standard Lean
VS Code extension can show the diagnostics in its InfoView.

```lean
import TheoryDebugger

example (x y : ℝ) (hx : x > 0) (hy : y ≥ x ^ 2) : y > 0 := by
  theory

-- Explore a conjecture without declaring it as a theorem.
#theory (∀ (x y z : ℝ),
  x > 0 → y > 0 → x*y ≤ z^2 → z ≥ 0 → x+y ≤ 2*z)
```

The first claim is proved. The second is refuted by a rational witness checked
against the actual Lean assumptions and target. No proof placeholder is needed
to explore a false conjecture.

| Interface | Behavior |
| --- | --- |
| `theory` | Proves exactly the current goal if a checked proof is found; otherwise fails |
| `theory?` | Reports four-way diagnosis, validity and feasibility; leaves every goal unchanged |
| `theory? +assumptions` | Also checks removal of each assumption individually |
| `#theory (∀ ..., ...)` | Explores a proposition without asserting it |
| `#theory_assumptions (...)` | Explores a proposition with individual-removal checks |
| `#theory_json (...)` | Emits structured native evidence and separately labeled solver output |
| `#theory_repair (...) with (fun ... => ...)` | Checks a supplied additional assumption for validity and feasibility |
| `#theory_repair_json (...) with (fun ... => ...)` | Emits the original claim, candidate and checked repair result |

The native frontend checks recognized operations against fixed real arithmetic,
including their instances. Native proofs, contradictions, and witness substitutions
are checked in an empty local context and their axioms are audited. A proof of
the original goal is applied back to that exact goal. See
[the native interface](docs/native-interface.md) for setup and limits.

## Checked CLI demonstration

Run `python scripts/run_demo.py` from this directory after setup. It requires real
cvc5 and Lean executions and fails unless every expected result has a checked
certificate and an allowed axiom audit. The saved [results](demo/results.json)
include complete formal goals, exact witnesses, proof steps with source lines,
and compiler logs. [Environment](demo/environment.json) records the tested tools.

| Claim | Result checked by Lean |
| --- | --- |
| `x > 0`, `y >= x^2` imply `y > 0` | Valid; feasible at `(1,1)` |
| `x > 0`, `y > 0`, `x*y <= z^2` imply `x+y <= 2*z` | Refuted at `(1,1,-1)` |
| Same claim with proposed repair `z >= 0` | Still refuted at `(4,1,2)`: `5 <= 4` fails |
| `x > 0`, `x <= 0` imply `x = 42` | Contradictory assumptions; implication valid vacuously |
| `x^2+a*x+1 = 0` implies `True` | Valid for every `a`; this says nothing about feasibility for each `a` |
| At `a = 0`, `x^2+1 = 0` implies `True` | Still valid; assumptions infeasible |
| `x >= 1`, `x >= 2` imply `x > 0` | Either assumption can be removed individually; removing both refutes the goal |

The native interface now performs checked individual-removal analysis; the CLI
demonstration still records that final row as four separate problems. No joint
minimization algorithm is claimed. Witness hints preserve regression points;
cvc5 also searches independently, and every hint is checked against the original
assumptions and goal before it is used.

## Setup and use

For a guided economics session, start with [three small economic models](docs/economics.md):
a supply shift, a tax-revenue conjecture and repair, and linear monopoly pass-through.
There are eight runnable cases with separate validity and feasibility checks.
After setup, `python scripts/run_economics.py` checks both the JSON examples and
[their native Lean version](examples/Economics.lean).

Install Python 3.12 and [elan](https://lean-lang.org/install/), then run:

```sh
python -m venv .venv
# Activate .venv using your platform's usual command.
python -m pip install -r requirements.txt
python -m pip install -e .
lake update
lake exe cache get Mathlib.Basic.Real.Basic Mathlib.Tactic.Linarith Mathlib.Tactic.NormNum Mathlib.Tactic.Positivity
lake build
lake env lean examples/Native.lean
lake env lean lean-tests/Native.lean
python -m theorydebugger examples/false_repair.json
python -m unittest discover -s tests -v
python scripts/run_demo.py
```

The default Python tests exercise parsing, solver semantics, release isolation,
and trust boundaries.
Set `THEORYDEBUGGER_TEST_LEAN=1` to include seven more tests that actually invoke
Lean, including a rejected false proof and a valid solver result whose proof
reconstruction remains incomplete. Native tests additionally check the original
goal, overloaded operations, poisoned evidence, state preservation, and actual
placeholder-axiom rejection. See [native verification](demo/native-verification.json)
for the latest recorded results.

`lean-toolchain` pins Lean 4.34.0. `lake-manifest.json` locks Mathlib and its
transitive dependencies; commit it with the project. The Mathlib release resolves
to `5ed2965256430c3649e86755f9576b54eca72435`. cvc5 is pinned to 1.4.0.

If the Mathlib cache endpoint stalls, version 4.34.0 documents the environment
variable `MATHLIB_CACHE_DEBUG_USE_LEGACY=1` as a temporary fallback to its Azure
cache. That fallback was required on the development machine.

For an LLM tool call, send a JSON object through standard input:

```sh
python -m theorydebugger - --out artifacts
```

Example input:

```json
{
  "variables": ["x", "y"],
  "assumptions": [[">", "x", 0], [">=", "y", ["^", "x", 2]]],
  "goal": [">", "y", 0]
}
```

The output distinguishes `consistency` and `validity`, each with its own
`evidence` value: `lean_kernel`, `exact_evaluation`, `solver_only`, or `none`.
`exact_evaluation` means Python rational substitution, not a Lean certificate.
A successful process exit is not evidence of a Lean proof: inspect those labels
and each certificate's `status`. `--solver-only` explicitly skips Lean. Invalid
or unsupported syntax returns `unsupported`; an unresolved query remains
`unknown`. Proof reconstruction failure leaves the solver diagnosis visible
with `solver_only` evidence and the failed certificate marked `unknown`.

Schema 2 adds a checked classification: `true`, `mixed`, `false`, or
`inconsistent`, with `unknown` when either side lacks Lean evidence. Both
satisfying and refuting assignments remain visible. A single counterexample
does not establish universal failure. See [the evidence and repair contract](docs/evidence-v2.md).

To check the paper's proposed supply-sign repair while preserving its original claim:

```sh
python -m theorydebugger examples/tax_incidence.json --repair examples/repairs/nonnegative_supply.json
lake env lean examples/Repairs.lean
python scripts/run_repairs.py
```

A repair is accepted only when Lean proves the revised implication and a
feasible assignment. Making the assumptions contradictory is reported as a
rejected repair. Candidate generation and minimality are not claimed.

Read [the LLM integration contract](docs/llm-contract.md) before interpreting
these outputs. No model API, credentials, or hosted service is needed.

## Boundaries

The accepted language has real variables, exact integer/rational constants,
`+`, `-`, `*`, `neg`, natural powers, comparisons, and Boolean combinations.
Variables are universally quantified in the claim. Assumptions are a conjunction.
The prototype limits inputs to eight variables, 30 assumptions, 500 nodes,
depth 32, and powers through eight. Use `"1/3"` for a rational; floats and
variable division are rejected. See [architecture and trust](docs/architecture.md).

The solver handles more claims than the proof generator. The latter tries
nonnegative-square lemmas and `nlinarith` for implications/contradictions, and
`norm_num` for rational witnesses. It is deliberately incomplete. Algebraic
witnesses such as positive `sqrt(2)` remain visibly uncertified. There is no
general quantifier elimination, parameter projection, automatic repair synthesis,
joint hypothesis minimization, or derivative abstraction yet. Native extraction
supports explicit local real variables and polynomial hypotheses; local `let`
definitions, arbitrary casts, and unsupported hypotheses are rejected explicitly.

## Next milestone

Complete one example that starts with a written economic proof and ends with an
annotated Lean formalization and reproducible verification evidence. Record the
translation choices, diagnostic feedback, and any changes to assumptions, so the
researcher can inspect how the final proof relates to the original argument.

Then evaluate that workflow on about 20 independently written arguments and
conjectures. Use the results to improve the tool and document what we learn about
TheoryGuru, Lean, and LLM-assisted formalization. The [roadmap](docs/roadmap.md)
places this evaluation alongside later parameter projection and more general
nonlinear proof certificates.

## Provenance and release boundary

This project is inspired by **TheoryGuru**, developed by Casey B. Mulligan,
James H. Davenport, and Matthew England. Their
[2018 paper](https://arxiv.org/abs/1806.10925) describes the prior automated
reasoning workflow. Our [comparison](docs/theoryguru-comparison.md) records the
overlap, missing capabilities, and an executed Lean version of its tax-incidence
example. TheoryDebugger is a working name for this independent prototype.

All implementation and example code here was newly written. The private parent
repository is a reference archive; its recovered software, notebooks, paper,
and historical handoff are outside this directory and are not dependencies.
This project is developed in a private repository and structured for a future
public release. The [MIT license](LICENSE) applies only to original files in this
directory; dependencies retain their own licenses.

`python scripts/build_release.py /path/to/TheoryDebugger-0.3.0.zip` creates a
standalone source archive from an explicit allowlist, with file hashes and no
Git history. Use a fresh output filename. It excludes the private reference
archive, handoff, local tools, and build caches. The repository's GitHub Actions
workflow runs the proof and diagnostic checks on pushes and pull requests.
Saved demonstration logs record local runs; current CI results are available
in the repository's Actions tab.

See [backend assessment](docs/backend-assessment.md) for the checked capabilities
and the reasons for starting with cvc5 plus native Mathlib certificates.
