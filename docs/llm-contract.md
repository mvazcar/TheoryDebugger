# LLM integration contract

Use the CLI as a local tool with a JSON argument and JSON result. No model is
embedded: the conversational model proposes formal statements, reads the result,
and proposes revisions. This makes the tool usable with any LLM and keeps model
output outside the proof trust boundary.

For a statement already in Lean, prefer `theory?`, `theory? +assumptions`, or
`#theory_json (...)`. The native frontend checks evidence against the actual
Lean expressions. In native JSON, `validity`, `refutation`, `contradiction`, and
`feasible_assignment` are separate certificate fields; each successful native
check has status `lean_kernel`. Solver reports are nested under `solver_only`,
even if that backend labels its own substitution `exact_evaluation`.

1. Translate the intended claim into the documented exact input language. Show
   the variable dictionary, domain, assumptions, and conclusion for review.
   The user must be able to see what has actually been formalized.
2. Call the CLI. Read consistency and validity independently, including their
   evidence fields. Never infer success from a timeout, missing witness, exit
   code, a solver's UNSAT alone, or an empty certificate list.
3. Explain a counterexample by substituting its exact values into every
   assumption and the conclusion. Link the corresponding checked declarations.
4. Treat any proposed repair as a new conjecture. Submit the full augmented
   problem, preserving the target. Require both a proof of the implication and
   a feasibility witness before describing a repair as nonvacuously sufficient.
   Blocking one known counterexample is not enough.
5. When removing assumptions, check the actual remaining set. Individual
   leave-one-out results do not license removing all flagged assumptions together.
6. Report `unsupported`, `unknown`, failed reconstruction, and unverified
   algebraic witnesses plainly. Do not fabricate a proof or substitute a weaker
   theorem without making the changed mathematical question explicit.

For the false-repair regression, an appropriate response is:

> Adding z ≥ 0 is insufficient. At x = 4, y = 1, z = 2, both positive-variable
> assumptions hold, xy = z² = 4, and z ≥ 0. But x+y = 5 > 4 = 2z. Lean checks
> these substitutions and the refutation of the full repaired implication.

For the positive-square example:

> Because x is positive, x² is positive. Since y ≥ x², y is positive too.
> The generated `positive_square_0` step and final `claim` check this argument.

This contract supports LLM-assisted mathematical exploration. It does not claim
automatic correctness of informal-to-formal translation or natural-language
proof explanations.
