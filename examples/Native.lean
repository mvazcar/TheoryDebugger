import TheoryDebugger

/- Open this file in a Lean editor, or run `lake env lean examples/Native.lean`.
   #theory explores conjectures without asserting them as theorems. -/

theorem positive_square (x y : ℝ) (hx : x > 0) (hy : y ≥ x ^ 2) : y > 0 := by
  theory

#print axioms positive_square

-- The diagnostic tactic leaves the current goal untouched.
theorem redundant_bounds (x : ℝ) (_h₁ : x ≥ 1) (h₂ : x ≥ 2) : x > 0 := by
  theory? +assumptions
  linarith

#print axioms redundant_bounds

#theory (∀ (x y z : ℝ), x > 0 → y > 0 → x * y ≤ z ^ 2 → x + y ≤ 2 * z)

-- The proposed repair is itself a false conjecture.
#theory (∀ (x y z : ℝ), x > 0 → y > 0 → x * y ≤ z ^ 2 → z ≥ 0 → x + y ≤ 2 * z)

#theory (∀ (x : ℝ), x > 0 → x ≤ 0 → x = 42)

-- Simultaneous removal must be tested separately.
#theory (∀ (x : ℝ), x > 0)

-- A solver can refute this, but its algebraic witness is not certified yet.
#theory (∀ (x : ℝ), x ^ 2 = 2 → x > 0 → x < 0)

-- Structured output for an LLM or editor integration.
#theory_json (∀ (a x : ℝ), x ^ 2 + a * x + 1 = 0 → True)
