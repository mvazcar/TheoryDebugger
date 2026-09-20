# Add Uzawa's on-path growth theorem and Jones–Scrimgeour elasticity lemmas

Add a reusable formalization of the labor-augmenting representation in
Jones–Scrimgeour (2008), Theorem 2.1, using Schlicht's constant-returns scaling
argument. Balanced paths are encoded as exponentials with initially separate
growth rates. Resource feasibility, nonnegative consumption, and positive
investment identify output's rate with investment's; accumulation identifies
investment's rate with capital's. The resulting index `A(t)=exp((gY-n)(t-τ))`
satisfies `Y(t)=F(K(t),A(t)L(t),τ)` and `A'(t)/A(t)=gY-n`.

The resource step uses the identity at three dates and a weighted sum of
squares, rather than the paper's second differentiation. It covers zero
consumption without dividing by it. Only constant returns on positive inputs
at the reference date is needed of the technology. The conclusion concerns
the given path, not an identity at all counterfactual inputs.

Two companion modules prove the local elasticity identity `α/(1-α)` in the
2004 NBER version under explicit inverse-parameterization hypotheses, and
check a positive Cobb–Douglas instance of every premise of the general
representation theorem. The later integration step of the 2004 proof is not
claimed as formalized.

The patch adds three modules, their root imports, and a README layout row:
25 proved declarations in total. All proofs use Mathlib, with no external
solver dependency. LLM assistance and a separate TheoryDebugger diagnostic
of the zero-investment cancellation were used during development.

Validation: full `lake build` on the existing Lean/Mathlib `v4.34.0-rc2` pins;
all 25 theorem axiom reports restricted to `propext`, `Classical.choice`, and
`Quot.sound`; no warnings in the new modules. No proof placeholders or new
axioms. Existing upstream warnings are unchanged. Newly written source is
Apache 2.0. Base commit: `8e7d5172e253cb20af2aea27e53f384d7ef18a25`.
