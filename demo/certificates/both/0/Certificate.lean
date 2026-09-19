import Mathlib.Basic.Real.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Positivity

set_option maxHeartbeats 400000
namespace TheoryDebugger.Generated

-- Variable dictionary: {"x": "v0"}
def original : Prop :=
  ∀ (v0 : ℝ), (v0 ≥ (1 : ℝ)) → (v0 ≥ (2 : ℝ)) → (v0 > (0 : ℝ))

theorem sample_h0 : ((2 : ℝ) ≥ (1 : ℝ)) := by
  norm_num

theorem sample_h1 : ((2 : ℝ) ≥ (2 : ℝ)) := by
  norm_num

theorem feasible : ∃ (_v0 : ℝ), ((_v0 ≥ (1 : ℝ)) ∧ (_v0 ≥ (2 : ℝ))) := by
  refine ⟨(2 : ℝ), ?_⟩
  norm_num

#check sample_h0
#print axioms sample_h0
#check sample_h1
#print axioms sample_h1
#check feasible
#print axioms feasible
end TheoryDebugger.Generated
