import Mathlib.Basic.Real.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Positivity

set_option maxHeartbeats 400000
namespace TheoryDebugger.Generated

-- Variable dictionary: {"x": "v0"}
def original : Prop :=
  ∀ (v0 : ℝ), (((v0 ^ 2) + (1 : ℝ)) = (0 : ℝ)) → True

theorem contradiction : ∀ (v0 : ℝ), (((v0 ^ 2) + (1 : ℝ)) = (0 : ℝ)) → False := by
  intro v0 h0
  have square_0 : 0 ≤ v0 ^ 2 := sq_nonneg v0
  nlinarith

theorem claim : original := by
  unfold original
  intro v0 h0
  exact False.elim (contradiction v0 h0)

#check contradiction
#print axioms contradiction
#check claim
#print axioms claim
end TheoryDebugger.Generated
