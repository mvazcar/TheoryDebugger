# Try three simple economic models

These examples start with an economic claim, state its assumptions explicitly,
and ask TheoryDebugger to prove it or produce a counterexample. Both kinds of
answer are checked by Lean. Feasibility is checked separately: a proof should
not succeed merely because no economy satisfies the assumptions.

The eight runnable inputs are in [examples/economics](../examples/economics).
The readable Lean version is [examples/Economics.lean](../examples/Economics.lean).
The [saved results](../demo/economics/results.json) contain the exact statements,
witnesses, certificate sources, and compiler logs.

## 1. Does cheaper supply lower the market price?

Imagine downward-sloping demand and upward-sloping or flat supply. Shift the
inverse supply curve down by one price unit. What happens to equilibrium?

Use four real numbers:

| Symbol | Meaning | Restriction |
| --- | --- | --- |
| `d` | Slope of inverse demand | `d < 0` |
| `s` | Slope of inverse supply | `s ≥ 0` |
| `dq` | Change in equilibrium quantity | To be determined |
| `dp` | Change in equilibrium price | To be determined |

The equilibrium changes must satisfy:

```text
dp = d × dq          demand does not shift
dp = s × dq − 1      inverse supply shifts down by one
```

**The checked conclusions are `dq > 0` and `dp < 0`.** These are two separate
universal claims: every real assignment satisfying the assumptions has those
signs. The deliberately opposite claim, `dp > 0`, is refuted.

For a concrete economy, let demand be `P = 10 − Q` and supply be `P = 2 + Q`.
The original equilibrium is `Q = 4, P = 6`. Moving supply to `P = 1 + Q`
gives `Q = 4.5, P = 5.5`. Thus `d = −1`, `s = 1`, `dq = 1/2`, and
`dp = −1/2`. This exact assignment is checked by Lean in the JSON demonstration.

The algebra explains the sign: subtracting the demand equation from the supply
equation gives `(s − d) × dq = 1`. Since `s − d > 0`, quantity rises. Multiplying
that increase by the negative demand slope makes price fall.

These equations also describe a local response to a supply-shift parameter in a
smooth model, once differentiation and an interior equilibrium are justified.
Here they are exact finite changes for affine curves. The checker verifies the
polynomial implications; it does not automatically derive the equations from
arbitrary supply and demand functions.

Files: [quantity](../examples/economics/market_quantity.json),
[price](../examples/economics/market_price.json),
[opposite conjecture](../examples/economics/market_price_rises.json).

## 2. Must a higher tax rate raise revenue?

Let revenue equal the tax rate times the tax base: `R = t × B`. Compare two
situations with `0 < t0 < t1 < 1` and positive bases `B0`, `B1`.

**Conjecture:** `t1 × B1 > t0 × B0`.

**Result: refuted.** The saved, Lean-checked counterexample is:

| | Before | After |
| --- | --- | --- |
| Tax rate | 25% | 50% |
| Tax base | 100 | 40 |
| Revenue | 25 | 20 |

Every stated assumption holds, yet revenue falls. Positivity of the tax base
alone is insufficient. No behavioral law relating the two bases was assumed;
the result identifies a missing restriction, rather than predicting a response
to any actual tax policy.

**Proposed repair:** add `B1 ≥ B0`, meaning that the tax base does not shrink.
Keep the original conclusion unchanged.

**Result: proved, with feasible assumptions.** The proof accounts for both
changes: `t1 B1 − t0 B0 = (t1 − t0) B0 + t1 (B1 − B0)`. The first term is
positive and the second nonnegative. For example, the same 25% and 50% rates
with both bases equal to 100 satisfy the repaired assumptions. The saved
feasibility certificate uses the solver's own exact assignment.

This repair is sufficient, not necessary. For example, a base falling from 100
to 60 still raises revenue from 25 to 30 at those rates. We are not claiming
to have found the weakest repair. Nor is this a replication of a full Laffer
model with household choices and equilibrium restrictions.

This is the intended research loop:

```text
claim → exact counterexample → identify missing assumption
      → propose a repair → check the same claim and feasibility again
```

Files: [original claim](../examples/economics/tax_revenue.json),
[repaired claim](../examples/economics/tax_revenue_repaired.json).

## 3. Does a monopolist pass on the entire cost increase?

Take linear inverse demand `P(Q) = a − bQ`, with `b > 0`, and constant marginal
cost `c`. Assume the profit maximum is interior both before and after a cost
increase, and demand stays fixed.

Profit is `(a − bQ − c)Q`. The interior first-order condition is
`a − 2bQ − c = 0`. Subtracting the conditions before and after the change gives:

```text
2 × b × dq = −dc       change in the first-order condition
dp = −b × dq           change along the demand curve
b > 0, dc > 0
```

**The checker proves `2 × dp = dc` and `dq < 0`.** The price increase is exactly
half the increase in marginal cost, and quantity falls. It refutes the conjecture
`dp = dc`, which would mean full pass-through.

A concrete economy has demand `P = 10 − Q` and marginal cost rising from 2 to 4.
Its interior monopoly quantity falls from 4 to 3, and its price rises from 6 to 7.
The checked assignment is `b = 1`, `dc = 2`, `dq = −1`, `dp = 1`.

The displayed profit has second derivative `−2b < 0`, which explains the use of
the interior first-order condition. The Lean inputs begin with the two change
equations; the calculus and optimization reduction are explained here, not
formalized by this example. Corner solutions and nonlinear demand require
different assumptions. The 50% conclusion is specific to this model.

Files: [half pass-through](../examples/economics/monopoly_half.json),
[quantity](../examples/economics/monopoly_quantity.json),
[full pass-through conjecture](../examples/economics/monopoly_full.json).

## Run and modify the examples

After the setup in the [README](../README.md), run from the TheoryDebugger folder:

```sh
python scripts/run_economics.py
python scripts/check_saved_evidence.py demo/economics/results.json
```

This executes cvc5 and Lean, checks the expected outcomes and feasibility, and
rebuilds the evidence bundle. It also compiles the readable native Lean file,
which contains five proved theorems and three refuted conjectures. It fails if
a result lacks the expected Lean evidence. The checker does not silently
promote a solver answer to a proof.

To inspect a single case or experiment with a copy of it:

```sh
python -m theorydebugger examples/economics/tax_revenue.json
lake env lean examples/Economics.lean
```

For the native file, set `THEORYDEBUGGER_PYTHON` to the Python interpreter that
has the adapter installed if `python` is not that interpreter. The economics
runner does this automatically. It expects `lake build` to have completed.

The three counterexample inputs contain rational witness hints to keep the explanations
reproducible. cvc5 still searches independently, and both Python and Lean check
each hint against the original assumptions and goal. Native `#theory` examples
use solver-discovered witnesses, so their numbers may differ from these tables.
For valid statements, a witness proves feasibility only; a separate universal
proof establishes the conclusion for every assignment.

Useful experiments are to remove the demand-slope condition in the market
example, change the tax-base repair, or replace the monopoly's proposed
pass-through rate. Keep the original version alongside each revision. Inspect
both `validity` and `consistency`, and their `evidence` fields.

## Provenance and scope

The market equations correspond to the local Marshall system in equation (66)
of Casey B. Mulligan's *Automated Economic Reasoning with Quantifier Elimination*,
[NBER Working Paper 22922](https://www.nber.org/papers/w22922), December 2016.
The tax comparison and linear monopoly model are independently written teaching
examples, not reproductions of the paper's full tax or monopoly systems. The
general monopoly pass-through expression in that paper uses a total derivative
of marginal cost; this example specializes to constant marginal cost.

All code, inputs, explanations, and certificates here are original additions to
the open project. They do not require the private reference archive or proprietary
TheoryGuru software. These small examples exercise checked polynomial reasoning;
they do not establish general quantifier elimination or automatic translation
of informal economics into correct formal assumptions.
