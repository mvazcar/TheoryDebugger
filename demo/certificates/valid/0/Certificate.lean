import Mathlib.Basic.Real.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Positivity

set_option maxHeartbeats 400000
namespace TheoryDebugger.Generated

-- Variable dictionary: {"x": "v0", "y": "v1"}
def original : Prop :=
  ∀ (v0 : ℝ), ∀ (v1 : ℝ), (v0 > (0 : ℝ)) → (v1 ≥ (v0 ^ 2)) → (v1 > (0 : ℝ))

theorem sample_h0 : ((1 : ℝ) > (0 : ℝ)) := by
  norm_num

theorem sample_h1 : ((1 : ℝ) ≥ ((1 : ℝ) ^ 2)) := by
  norm_num

theorem feasible : ∃ (_v0 : ℝ), ∃ (_v1 : ℝ), ((_v0 > (0 : ℝ)) ∧ (_v1 ≥ (_v0 ^ 2))) := by
  refine ⟨(1 : ℝ), (1 : ℝ), ?_⟩
  norm_num

theorem satisfying : ∃ (_v0 : ℝ), ∃ (_v1 : ℝ), (((_v0 > (0 : ℝ)) ∧ (_v1 ≥ (_v0 ^ 2))) ∧ (_v1 > (0 : ℝ))) := by
  refine ⟨(1 : ℝ), (1 : ℝ), ?_⟩
  norm_num

#check sample_h0
#print axioms sample_h0
#check sample_h1
#print axioms sample_h1
#check feasible
#print axioms feasible
#check satisfying
#print axioms satisfying
end TheoryDebugger.Generated
