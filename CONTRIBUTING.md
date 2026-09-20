# Contributing

TheoryDebugger's original work is dedicated to the public domain under
[The Unlicense](UNLICENSE). By contributing original work, you agree to this
dedication and confirm that you have the right to contribute it. Identify any
third-party material and preserve its license and notices. Please contribute small, reproducible mathematical examples along
with expected validity, feasibility, and evidence levels.

Use Python 3.12 and the committed Lean/Mathlib toolchain and manifest. Install the
adapter with `python -m pip install -e .`, then follow the README to build. Before
submitting changes, run:

```sh
lake build
lake env lean lean-tests/Native.lean
python -m unittest discover -s tests -v
python scripts/run_demo.py
python scripts/check_saved_evidence.py
python scripts/run_economics.py
python scripts/check_saved_evidence.py demo/economics/results.json
python scripts/run_repairs.py
python scripts/check_saved_evidence.py demo/repairs/results.json
python scripts/verify_paper.py
```

Set `THEORYDEBUGGER_TEST_LEAN=1` when running Python tests to include real Lean
boundary checks. Native tests require the installed Python adapter and cvc5.
`THEORYDEBUGGER_PYTHON` can point Lean to a particular Python executable.

A new supported syntax form must preserve the original Lean semantics. Test
strict versus nonstrict comparisons, rational signs, overloaded instances, and
unsupported terms. Never accept an external result or a placeholder as a proof.
Tests should reject at least one plausible incorrect result related to the change.

Keep proposals, solver diagnoses, exact substitutions, and Lean certificates
distinct. A proof of an implication does not establish feasibility. Removing
several assumptions needs a fresh check of the actual remaining set.

Do not contribute recovered proprietary code, third-party notebooks, paper
copies, private context, credentials, or private repository history. Historical
systems can inform feature questions; their materials do not belong in this
source tree. Independently write examples and explain any mathematical modeling
bridge needed to transfer a scalar result to its intended application.
