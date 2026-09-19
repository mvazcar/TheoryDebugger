# Backend assessment — 19 September 2026

Environment inspection found no usable Lean, elan, cvc5, Z3, or REDUCE command
on the initial path. A project-local elan 4.2.4 installation then installed Lean
4.34.0; a Python 3.12.14 environment installed cvc5 1.4.0. All project-local
bootstrap binaries live outside this release directory. The exact observed
run is recorded in `demo/environment.json`.

The upstream Lean and Mathlib latest stable releases were both **4.34.0**.
Mathlib's moving master requested **4.35.0-rc2**, which was deliberately not used.
The manifest pins every dependency commit. These observations were checked with
the repositories' release metadata and toolchain files, then by actual execution.

| Candidate | Observed fit | Decision |
| --- | --- | --- |
| Mathlib `nlinarith`, `norm_num`, `positivity` | Actual compilation proves the demo implications, contradictions, and exact rational substitutions; exported axioms audited | Certificate engine now |
| cvc5 1.4.0 | Actual `QF_NRA` SAT/UNSAT queries and exact rational model extraction work; `x^2=2, x>0` returns an algebraic model | Diagnostic engine now; no claim that its nonlinear proofs are reconstructed |
| Lean-SMT | Current README documents uninterpreted functions and linear integer/real arithmetic with quantifiers; reconstructed cvc5 proofs may leave Lean goals | Relevant future comparison; not installed or benchmarked here, not assumed to certify arbitrary nonlinear QE |
| REDLOG / REDUCE | Its documented real quantifier elimination and symbolic conditions fit future parameter analysis; no usable command found on this machine | Future diagnostic adapter; no REDLOG execution or Lean reconstruction claimed |

The chosen path demonstrates a complete small trust loop without waiting for a
general CAD certificate format. Exact rational counterexamples are particularly
useful: their discovery can be sophisticated while their Lean verification is
simple. Algebraic sample points require additional certificate machinery.

References checked during implementation:

- [Lean 4.34.0 release](https://github.com/leanprover/lean4/releases/tag/v4.34.0)
- [Mathlib 4.34.0 release](https://github.com/leanprover-community/mathlib4/releases/tag/v4.34.0)
- [Mathlib arithmetic tactic documentation](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Tactic/Linarith/Frontend.html)
- [cvc5 model and result API](https://cvc5.github.io/docs/latest/binary/quickstart.html)
- [Lean-SMT supported theories and reconstruction limits](https://github.com/ufmg-smite/lean-smt)
- [REDLOG](https://www.redlog.eu/) and [quantifier elimination reference](https://www.redlog.eu/documentation/builtin.php?key=rlqe)

The private reference archive was used to understand the diagnostic questions
and their logical traps. Its 41 Wolfram checks, the paper's TheoryGuru 4.0
screenshots, and recovered TheoryGuru 6.6 code are separate historical evidence,
not Lean certificates or code dependencies of this implementation.
