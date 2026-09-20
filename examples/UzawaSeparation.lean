import TheoryDebugger
import Mathlib.Analysis.Calculus.Deriv.Inv
import Mathlib.Analysis.Calculus.Deriv.Add
import Mathlib.Tactic.Ring

/-!
# Diagnostics for the repaired elasticity proof

TheoryDebugger checks cancellation of the positive capital/output coordinate.
It also checks a polynomial witness to the difference between a restriction
at one coordinate and a separable function on a whole domain. Mathlib bridges
the algebra to actual derivatives. This polynomial family is a diagnostic,
not a claim to satisfy every neoclassical growth-model assumption.
-/

namespace UzawaSeparationExample

#theory_json (∀ (x u v : ℝ), 0 ≤ x → x * u = x * v → u = v)
#theory_repair_json (∀ (x u v : ℝ), 0 ≤ x → x * u = x * v → u = v)
  with (fun x _ _ => 0 < x)
#theory_repair_json (∀ (x u v : ℝ), 0 ≤ x → x * u = x * v → u = v)
  with (fun x _ _ => x < 0)

/-- Cross-products cancel only at a nonzero coordinate. -/
theorem positive_coordinate_cancellation (x u v : ℝ) (hx : 0 < x)
    (h : x * u = x * v) : u = v := by theory

/-- A bridge from actual derivatives and equal elasticities to the derivative
of the ratio. `m0` and `m1` are certified derivatives, not independent guesses. -/
theorem hasDerivAt_ratio_zero {f0 f1 : ℝ → ℝ} {x m0 m1 : ℝ}
    (hx : 0 < x) (h0 : HasDerivAt f0 m0 x) (h1 : HasDerivAt f1 m1 x)
    (hy0 : 0 < f0 x) (hy1 : 0 < f1 x)
    (helasticity : m1 * x / f1 x = m0 * x / f0 x) :
    HasDerivAt (fun u => f1 u / f0 u) 0 x := by
  have hc := (div_eq_div_iff (ne_of_gt hy1) (ne_of_gt hy0)).mp helasticity
  have heq : m1 * f0 x = f1 x * m0 := by
    apply positive_coordinate_cancellation x _ _ hx
    nlinarith [hc]
  convert! h1.fun_div h0 (ne_of_gt hy0) using 1
  rw [heq]
  simp

def coordinateOutput (t x : ℝ) : ℝ := 1 + x + t * (x - 1) ^ 2

/-- At x=1 every member has the same positive level. -/
theorem anchor_value (t : ℝ) : coordinateOutput t 1 = 2 := by
  norm_num [coordinateOutput]

/-- The derivative at x=1 is also independent of time, so the elasticity
there is always 1/2 despite the family's changing shape. -/
theorem anchor_derivative (t : ℝ) : HasDerivAt (coordinateOutput t) 1 1 := by
  have h := (hasDerivAt_id (1 : ℝ)).sub_const 1
  convert! ((hasDerivAt_id (1 : ℝ)).const_add 1).add
    ((h.mul h).const_mul t) using 1 <;>
    norm_num [coordinateOutput, pow_two]
  funext x
  simp [coordinateOutput, pow_two]

theorem anchor_elasticity (t : ℝ) :
    deriv (coordinateOutput t) 1 * 1 / coordinateOutput t 1 = 1 / 2 := by
  rw [(anchor_derivative t).deriv, anchor_value]
  norm_num

theorem coordinateOutput_pos {t x : ℝ} (ht : 0 ≤ t) (hx : 0 < x) :
    0 < coordinateOutput t x := by
  unfold coordinateOutput
  nlinarith [mul_nonneg ht (sq_nonneg (x - 1))]

-- Separation would preserve the ratio of values at x=2 and x=1.
-- The cross-multiplied equality is false for some t in [0,1], true for t=0.
#theory_json (∀ (t : ℝ), 0 ≤ t → t ≤ 1 →
  (1 + 2 + t * (2 - 1)^2) * (1 + 1) =
    (1 + 2) * (1 + 1 + t * (1 - 1)^2))

/-- A functional check rules out ANY separation, using two dates and inputs. -/
theorem no_separation : ¬ ∃ A ψ : ℝ → ℝ,
    ∀ t, 0 ≤ t → t ≤ 1 → ∀ x, 0 < x → coordinateOutput t x = A t * ψ x := by
  rintro ⟨A, ψ, h⟩
  have h01 := h 0 (by norm_num) (by norm_num) 1 (by norm_num)
  have h11 := h 1 (by norm_num) (by norm_num) 1 (by norm_num)
  have h02 := h 0 (by norm_num) (by norm_num) 2 (by norm_num)
  have h12 := h 1 (by norm_num) (by norm_num) 2 (by norm_num)
  norm_num [coordinateOutput] at h01 h11 h02 h12
  have hψ : ψ 1 ≠ 0 := by intro hz; rw [hz, mul_zero] at h01; norm_num at h01
  have hA : A 0 = A 1 := mul_right_cancel₀ hψ (h01.symm.trans h11)
  rw [hA] at h02
  linarith

#print axioms positive_coordinate_cancellation
#print axioms hasDerivAt_ratio_zero
#print axioms anchor_value
#print axioms anchor_derivative
#print axioms anchor_elasticity
#print axioms coordinateOutput_pos
#print axioms no_separation

end UzawaSeparationExample
