import TheoryDebugger
import Mathlib.Analysis.Real.Sqrt
import Mathlib.Tactic.Ring

/-!
# Solow–Swan: an LLM claim, a counterexample, and a checked repair

Solow (1956), equation (6), p. 69 and Example 2, pp. 76–77. For Cobb–Douglas
exponent 1/2, write q = sqrt k. The reduced equation is k' = s A q - n q².
The normalized case s = 1/2, A = 2, n = 1 has stationary q = 0 and q = 1.
The first informal claim, "the stationary capital stock is unique", forgets
the zero-capital boundary explicitly discussed in Solow's footnote 4.

TheoryDebugger diagnoses the polynomial statements. The bridge below proves
their connection to actual square-root production using Mathlib. The full
upstream contribution uses ordinary Mathlib proofs and requires no solver.
-/

namespace SolowSwanExample

/-- The polynomial encoding really is the square-root model on k ≥ 0. -/
theorem square_root_bridge (s A n k : ℝ) (hk : 0 ≤ k) :
    s * (A * Real.sqrt k) - n * k =
      s * A * Real.sqrt k - n * (Real.sqrt k) ^ 2 := by
  rw [Real.sq_sqrt hk]
  ring

-- Both witnesses are checked by Lean: q = 0 refutes uniqueness; q = 1 satisfies it.
#theory_json (∀ (q : ℝ), 0 ≤ q → q - q^2 = 0 → q = 1)

-- Preserve the original assumptions and goal; add q > 0. Check nonvacuity too.
#theory_repair_json (∀ (q : ℝ), 0 ≤ q → q - q^2 = 0 → q = 1)
  with (fun q => 0 < q)

-- A tempting "repair" that destroys feasibility must not be accepted.
#theory_repair_json (∀ (q : ℝ), 0 ≤ q → q - q^2 = 0 → q = 1)
  with (fun q => 1 < q)

theorem normalized_positive_stationary_root (q : ℝ) (hq : 0 < q)
    (stationary : q - q^2 = 0) : q = 1 := by
  theory

/-- Apply the checked algebraic argument to the actual economic expression. -/
theorem normalized_positive_stationary_capital (k : ℝ) (hk : 0 < k)
    (stationary : (1 / 2 : ℝ) * (2 * Real.sqrt k) - k = 0) : k = 1 := by
  have hroot : 0 < Real.sqrt k := Real.sqrt_pos.mpr hk
  have hstationary : Real.sqrt k - (Real.sqrt k) ^ 2 = 0 := by
    rw [Real.sq_sqrt hk.le]
    linarith
  have heq := normalized_positive_stationary_root (Real.sqrt k) hroot hstationary
  nlinarith [Real.sq_sqrt hk.le]

theorem normalized_zero_stationary :
    (1 / 2 : ℝ) * (2 * Real.sqrt 0) - 0 = 0 := by norm_num

/-- Positive drift below the normalized positive steady state. -/
theorem normalized_capital_increases (q : ℝ) (hq : 0 < q) (hbelow : q < 1) :
    0 < q - q^2 := by
  theory

/-- Negative drift above the normalized positive steady state. -/
theorem normalized_capital_decreases (q : ℝ) (habove : 1 < q) : q - q^2 < 0 := by
  theory

#print axioms square_root_bridge
#print axioms normalized_positive_stationary_root
#print axioms normalized_positive_stationary_capital
#print axioms normalized_zero_stationary
#print axioms normalized_capital_increases
#print axioms normalized_capital_decreases

end SolowSwanExample
