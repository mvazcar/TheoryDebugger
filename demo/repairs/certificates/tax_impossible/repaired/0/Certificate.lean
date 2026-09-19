import Mathlib.Basic.Real.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Positivity

set_option maxHeartbeats 400000
namespace TheoryDebugger.Generated

-- Variable dictionary: {"d": "v0", "p": "v2", "s": "v1"}
def original : Prop :=
  ∀ (v0 : ℝ), ∀ (v1 : ℝ), ∀ (v2 : ℝ), (v0 < (0 : ℝ)) → ((v0 * (v2 + (1 : ℝ))) = (v1 * v2)) → (v0 ≥ (0 : ℝ)) → (v2 ≤ (0 : ℝ))

theorem contradiction : ∀ (v0 : ℝ), ∀ (v1 : ℝ), ∀ (v2 : ℝ), (v0 < (0 : ℝ)) → ((v0 * (v2 + (1 : ℝ))) = (v1 * v2)) → (v0 ≥ (0 : ℝ)) → False := by
  intro v0 v1 v2 h0 h1 h2
  have square_0 : 0 ≤ v0 ^ 2 := sq_nonneg v0
  have square_1 : 0 ≤ v1 ^ 2 := sq_nonneg v1
  have square_2 : 0 ≤ v2 ^ 2 := sq_nonneg v2
  first | (solve | norm_num at *) | nlinarith

theorem claim : original := by
  unfold original
  intro v0 v1 v2 h0 h1 h2
  exact False.elim (contradiction v0 v1 v2 h0 h1 h2)

#check contradiction
#print axioms contradiction
#check claim
#print axioms claim
end TheoryDebugger.Generated
