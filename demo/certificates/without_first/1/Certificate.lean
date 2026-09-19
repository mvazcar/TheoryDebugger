import Mathlib.Basic.Real.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Positivity

set_option maxHeartbeats 400000
namespace TheoryDebugger.Generated

-- Variable dictionary: {"x": "v0"}
def original : Prop :=
  ∀ (v0 : ℝ), (v0 ≥ (2 : ℝ)) → (v0 > (0 : ℝ))

theorem claim : original := by
  unfold original
  intro v0 h0
  have square_0 : 0 ≤ v0 ^ 2 := sq_nonneg v0
  nlinarith

#check claim
#print axioms claim
end TheoryDebugger.Generated
