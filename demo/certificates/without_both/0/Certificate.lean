import Mathlib.Basic.Real.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Positivity

set_option maxHeartbeats 400000
namespace TheoryDebugger.Generated

-- Variable dictionary: {"x": "v0"}
def original : Prop :=
  ∀ (v0 : ℝ), (v0 > (0 : ℝ))

theorem feasible : ∃ (_v0 : ℝ), True := by
  refine ⟨(0 : ℝ), ?_⟩
  norm_num

theorem refuting : ∃ (_v0 : ℝ), (True ∧ ¬ (_v0 > (0 : ℝ))) := by
  refine ⟨(0 : ℝ), ?_⟩
  norm_num

theorem sample_not_goal : ¬ ((0 : ℝ) > (0 : ℝ)) := by
  norm_num

theorem refutation : ¬ original := by
  intro h
  unfold original at h
  exact sample_not_goal (h (0 : ℝ))

#check feasible
#print axioms feasible
#check refuting
#print axioms refuting
#check sample_not_goal
#print axioms sample_not_goal
#check refutation
#print axioms refutation
end TheoryDebugger.Generated
