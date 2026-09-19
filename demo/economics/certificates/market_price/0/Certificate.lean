import Mathlib.Basic.Real.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Positivity

set_option maxHeartbeats 400000
namespace TheoryDebugger.Generated

-- Variable dictionary: {"d": "v0", "dp": "v3", "dq": "v2", "s": "v1"}
def original : Prop :=
  ∀ (v0 : ℝ), ∀ (v1 : ℝ), ∀ (v2 : ℝ), ∀ (v3 : ℝ), (v0 < (0 : ℝ)) → (v1 ≥ (0 : ℝ)) → (((v1 * v2) - (1 : ℝ)) = v3) → ((v0 * v2) = v3) → (v3 < (0 : ℝ))

theorem sample_h0 : (((-1 : ℝ) / 2) < (0 : ℝ)) := by
  norm_num

theorem sample_h1 : (((1 : ℝ) / 2) ≥ (0 : ℝ)) := by
  norm_num

theorem sample_h2 : (((((1 : ℝ) / 2) * (1 : ℝ)) - (1 : ℝ)) = ((-1 : ℝ) / 2)) := by
  norm_num

theorem sample_h3 : ((((-1 : ℝ) / 2) * (1 : ℝ)) = ((-1 : ℝ) / 2)) := by
  norm_num

theorem feasible : ∃ (_v0 : ℝ), ∃ (_v1 : ℝ), ∃ (_v2 : ℝ), ∃ (_v3 : ℝ), ((_v0 < (0 : ℝ)) ∧ (_v1 ≥ (0 : ℝ)) ∧ (((_v1 * _v2) - (1 : ℝ)) = _v3) ∧ ((_v0 * _v2) = _v3)) := by
  refine ⟨((-1 : ℝ) / 2), ((1 : ℝ) / 2), (1 : ℝ), ((-1 : ℝ) / 2), ?_⟩
  norm_num

#check sample_h0
#print axioms sample_h0
#check sample_h1
#print axioms sample_h1
#check sample_h2
#print axioms sample_h2
#check sample_h3
#print axioms sample_h3
#check feasible
#print axioms feasible
end TheoryDebugger.Generated
