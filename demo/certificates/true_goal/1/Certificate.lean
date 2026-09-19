import Mathlib.Basic.Real.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Positivity

set_option maxHeartbeats 400000
namespace TheoryDebugger.Generated

-- Variable dictionary: {"a": "v0", "x": "v1"}
def original : Prop :=
  ∀ (v0 : ℝ), ∀ (v1 : ℝ), ((((v1 ^ 2) + (v0 * v1)) + (1 : ℝ)) = (0 : ℝ)) → True

theorem claim : original := by
  unfold original
  intro v0 v1 h0
  exact True.intro

#check claim
#print axioms claim
end TheoryDebugger.Generated
