import TheoryDebugger
import Mathlib.Analysis.SpecialFunctions.ExpDeriv
import Mathlib.Analysis.Calculus.Deriv.Add
import Mathlib.Tactic.Ring

/-!
# Solow–Swan dynamics: diagnostic obligations and analytic bridges

These are deliberate test claims, not errors attributed to the original paper.
An exponential weight is positive, but positivity alone does not ensure that
an affine combination of positive stocks is positive. Forward time supplies
the missing upper bound. Likewise `α > 0` does not ensure a positive speed:
we also need `α < 1`. Repairs retain every original assumption and conclusion.
The full real-power trajectory proof is packaged separately for LeanEconomics.
-/

namespace SolowDynamicsExample

#theory_json (∀ (z₀ e : ℝ), 0 < z₀ → 0 < e → 0 < 1 + (z₀ - 1) * e)
#theory_repair_json (∀ (z₀ e : ℝ), 0 < z₀ → 0 < e → 0 < 1 + (z₀ - 1) * e)
  with (fun _ e => e ≤ 1)
#theory_repair_json (∀ (z₀ e : ℝ), 0 < z₀ → 0 < e → 0 < 1 + (z₀ - 1) * e)
  with (fun _ e => e ≤ 0)

theorem positive_affine_path (z₀ e : ℝ) (hz : 0 < z₀) (he : 0 < e) (he₁ : e ≤ 1) :
    0 < 1 + (z₀ - 1) * e := by theory

#theory_json (∀ (α m : ℝ), 0 < α → 0 < m → 0 < (1 - α) * m)
#theory_repair_json (∀ (α m : ℝ), 0 < α → 0 < m → 0 < (1 - α) * m)
  with (fun α _ => α < 1)
#theory_repair_json (∀ (α m : ℝ), 0 < α → 0 < m → 0 < (1 - α) * m)
  with (fun α _ => α ≤ 0)

theorem positive_adjustment_speed (α m : ℝ) (hα₀ : 0 < α) (hm : 0 < m) (hα₁ : α < 1) :
    0 < (1 - α) * m := by theory

/-- Actual exponential weights satisfy the algebraic repair at nonnegative time. -/
theorem exponential_path_pos {z₀ α m t : ℝ} (hz : 0 < z₀) (hα₀ : 0 < α)
    (hm : 0 < m) (hα₁ : α < 1) (ht : 0 ≤ t) :
    0 < 1 + (z₀ - 1) * Real.exp (-((1 - α) * m) * t) := by
  apply positive_affine_path _ _ hz (Real.exp_pos _)
  apply Real.exp_le_one_iff.mpr
  have hspeed := positive_adjustment_speed α m hα₀ hm hα₁
  nlinarith

noncomputable def gap (speed d t : ℝ) : ℝ := d * Real.exp (-speed * t)

/-- The diagnostic speed is the coefficient in a proved differential equation. -/
theorem hasDerivAt_gap (speed d t : ℝ) :
    HasDerivAt (gap speed d) (-speed * gap speed d t) t := by
  convert! (((hasDerivAt_id t).const_mul (-speed)).exp).const_mul d using 1
  simp only [gap, id_eq]
  ring

/-- Squared deviation cannot increase when the adjustment speed is positive. -/
theorem hasDerivAt_squared_gap (speed d t : ℝ) :
    HasDerivAt (fun u => gap speed d u * gap speed d u) (-2 * speed * gap speed d t ^ 2) t := by
  convert! (hasDerivAt_gap speed d t).mul (hasDerivAt_gap speed d t) using 1
  ring

theorem energy_derivative_sign (l v : ℝ) (hl : 0 < l) (hv : 0 ≤ v) :
    -2 * l * v ≤ 0 := by theory

theorem squared_gap_derivative_nonpos (speed d t : ℝ) (hspeed : 0 < speed) :
    deriv (fun u => gap speed d u * gap speed d u) t ≤ 0 := by
  rw [(hasDerivAt_squared_gap speed d t).deriv]
  exact energy_derivative_sign speed (gap speed d t ^ 2) hspeed (sq_nonneg _)

#print axioms positive_affine_path
#print axioms positive_adjustment_speed
#print axioms exponential_path_pos
#print axioms hasDerivAt_gap
#print axioms hasDerivAt_squared_gap
#print axioms energy_derivative_sign
#print axioms squared_gap_derivative_nonpos

end SolowDynamicsExample
