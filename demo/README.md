# Checked demonstration

The [machine-readable record](results.json) holds ten end-to-end cases.
Each result includes the full mathematical input, evidence labels, witness values,
source hashes, declaration names, and axiom dependencies. The
[environment record](environment.json) identifies the toolchain used.

## A valid claim

If x > 0 and y ≥ x², then y > 0. Since x is positive, its square is strictly
positive (`positive_square_0`). The assumption y ≥ x² then gives y > 0 (`claim`).
Both steps are checked in the [proof](certificates/valid/1/Certificate.lean).
The [feasibility certificate](certificates/valid/0/Certificate.lean) checks x=y=1.

## A false conjecture and a false repair

The claim x>0, y>0, xy≤z² ⇒ x+y≤2z fails at (1,1,-1): the assumptions hold,
but 2≤-2 is false. The [certificate](certificates/false_conjecture/0/Certificate.lean)
proves each substitution and exports a refutation of the original claim.

Adding z≥0 still fails. At (4,1,2), positivity holds, xy=z²=4, and z≥0, while
x+y=5>4=2z. The [repair certificate](certificates/false_repair/0/Certificate.lean)
checks all four assumptions, the failed conclusion, and `refutation : ¬ original`.
This is why excluding the first counterexample does not establish sufficiency.

## Contradictory assumptions

x>0 and x≤0 cannot both hold. The
[certificate](certificates/contradiction/0/Certificate.lean) proves `False` from
them and separately proves the original implication by vacuity. It does not
present the claim x=42 as a useful consequence of a feasible model.

## Validity and feasibility are different questions

`x²+a*x+1=0 → True` is [valid for all real a and x](certificates/true_goal/1/Certificate.lean).
A witness at a=-2, x=1 establishes that the assumptions can hold somewhere;
it does not say they are feasible at every a. At a=0,
[the assumptions are impossible and the implication is still valid](certificates/true_infeasible/0/Certificate.lean).
No parameter projection algorithm is claimed.

## Individual and joint removal are different questions

With x≥1 and x≥2 the conclusion x>0 holds. It still holds
[without the first assumption](certificates/without_first/1/Certificate.lean)
or [without the second](certificates/without_second/1/Certificate.lean).
Removing both leaves a false claim, as the
[checked counterexample](certificates/without_both/0/Certificate.lean) demonstrates.

All exported declarations were compiled and audited. Their only dependencies
on axioms are among `propext`, `Classical.choice`, and `Quot.sound`.
Compiler logs sit beside the source files. There are no placeholders or external
solver axioms in these proofs. These files certify these specific formal
statements; they are not a general correctness proof of the tool.
