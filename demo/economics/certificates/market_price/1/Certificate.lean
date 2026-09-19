import Mathlib.Basic.Real.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Positivity

set_option maxHeartbeats 400000
namespace TheoryDebugger.Generated

-- Variable dictionary: {"d": "v0", "dp": "v3", "dq": "v2", "s": "v1"}
def original : Prop :=
  ∀ (v0 : ℝ), ∀ (v1 : ℝ), ∀ (v2 : ℝ), ∀ (v3 : ℝ), (v0 < (0 : ℝ)) → (v1 ≥ (0 : ℝ)) → (((v1 * v2) - (1 : ℝ)) = v3) → ((v0 * v2) = v3) → (v3 < (0 : ℝ))

theorem claim : original := by
  unfold original
  intro v0 v1 v2 v3 h0 h1 h2 h3
  have square_0 : 0 ≤ v0 ^ 2 := sq_nonneg v0
  have square_1 : 0 ≤ v1 ^ 2 := sq_nonneg v1
  have square_2 : 0 ≤ v2 ^ 2 := sq_nonneg v2
  have square_3 : 0 ≤ v3 ^ 2 := sq_nonneg v3
  nlinarith

#check claim
#print axioms claim
end TheoryDebugger.Generated
