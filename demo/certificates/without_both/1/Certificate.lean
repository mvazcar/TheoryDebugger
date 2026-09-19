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
  refine ⟨(1 : ℝ), ?_⟩
  norm_num

theorem satisfying : ∃ (_v0 : ℝ), (True ∧ (_v0 > (0 : ℝ))) := by
  refine ⟨(1 : ℝ), ?_⟩
  norm_num

#check feasible
#print axioms feasible
#check satisfying
#print axioms satisfying
end TheoryDebugger.Generated
