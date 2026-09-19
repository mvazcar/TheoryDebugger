# A focused path to an open conjecture debugger

The first audience is a researcher using an LLM to work on an algebraic lemma
inside a larger proof. The immediate question is whether the conjecture or a
proposed revision survives exact checking. This does not require solving the
entire research problem.

## Current slice: explicit claims and checked native diagnostics

The Python CLI accepts a small exact representation. The native Lean interface
extracts supported real expressions, checks that their operations have the
intended semantics, diagnoses feasibility and validity, checks rational witnesses,
and reconstructs proofs against the original goal. Leave-one-out analysis can
establish that particular assumptions are individually dispensable.

The standalone source tree is MIT licensed and has pinned mathematical
dependencies. A release builder packages only original source, examples,
documentation, and evidence; it includes neither private Git history nor the
reference archive. The standalone development repository is private. A GitHub
Actions workflow runs the proof and diagnostic checks on pushes and pull requests;
its run results are separate from the saved local verification evidence.

## Next experiment: a researcher and LLM revision loop

The first economics slice is implemented: [eight cases across three simple models](economics.md),
including a tax-revenue counterexample and a sufficient repair checked for both
validity and feasibility. The accompanying native Lean examples exercise the
same claims. This is a small initial corpus, not the full evaluation below.

Build a small corpus of independently written conjectures from elementary
inequalities, geometry, optimization, and finite comparative statics. Include
valid statements, strict-boundary mistakes, inconsistent assumptions, invalid
repairs, and rational/algebraic counterexamples. Start with about 20 cases.

For each case, preserve the original statement and a sequence of proposed edits.
Evaluate each edit independently, retaining the original target when testing a
new assumption. Measure: was the error found, was the witness useful, did the
explanation match a checked step, and how much manual formalization was needed?
These observations are more useful at this stage than a headline solver speed.

The [repair-checking API](evidence-v2.md) now accepts candidate assumptions and
requires both a checked implication and a feasibility certificate before
acceptance. Both native and JSON interfaces preserve the original claim. The
four-way diagnosis distinguishes mixed from universal failure; missing checked
evidence remains unknown. Minimality and automatic repair discovery remain open.

## Later: stronger mathematical diagnosis

Add contradiction cores, checked sequential hypothesis minimization, and exact
parameter feasibility/validity projections as distinct operations. REDLOG is a
candidate discovery backend for projection. Its output remains solver-only until
an appropriate certificate is reconstructed. Algebraic witnesses need an exact
representation and Lean verification of their defining roots and isolating data.

Broader nonlinear certificate formats, derivative abstractions, autoformalization,
and a dedicated editor should follow evidence from actual use. Function-level
claims require an explicit modeling theorem; an algebraic counterexample alone
does not establish that a derivative tuple can arise from a suitable function.

## Open-source release

Develop in the standalone private repository, select maintainers, review CI,
and prepare an initial public release with its limitations and evidence. Preserve
a clean history of original work. Public release is a separate decision from
private development. Do not change the visibility of the private reference
repository or copy its history into the new one.
