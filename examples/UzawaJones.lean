import TheoryDebugger
import Mathlib.Analysis.SpecialFunctions.ExpDeriv
import Mathlib.Analysis.Real.Sqrt
import Mathlib.Tactic.Ring

/-!
# Uzawa: why positive investment matters

Jones–Scrimgeour (2008), Theorem 2.1 and section III. Their published proof
replaces the 2004 working-paper argument in NBER 10921 with Schlicht's proof.
The positive-investment restriction is explicit in the published theorem.

Differentiating I = (gK + δ) K along constant-rate paths gives
I (gI - gK) = 0. Canceling investment requires it to be nonzero. The first
diagnostic deliberately forgets this condition. The function-level bridge and
the zero-investment example below are separate kernel-checked declarations.
-/

namespace UzawaJonesExample

#theory_json (∀ (I gI gK : ℝ), 0 ≤ I → I * (gI - gK) = 0 → gI = gK)
#theory_repair_json (∀ (I gI gK : ℝ), 0 ≤ I → I * (gI - gK) = 0 → gI = gK)
  with (fun I _ _ => 0 < I)
#theory_repair_json (∀ (I gI gK : ℝ), 0 ≤ I → I * (gI - gK) = 0 → gI = gK)
  with (fun I _ _ => I < 0)

theorem investment_cancellation (I gI gK : ℝ) (hI : 0 < I)
    (h : I * (gI - gK) = 0) : gI = gK := by
  theory

/-- The scalar cancellation equation comes from differentiating a functional
accumulation identity, not from inventing independent derivative variables. -/
theorem accumulation_rate_bridge {I K : ℝ → ℝ} {gI gK δ t : ℝ}
    (hI : HasDerivAt I (gI * I t) t) (hK : HasDerivAt K (gK * K t) t)
    (hlevels : ∀ u, I u = (gK + δ) * K u) : I t * (gI - gK) = 0 := by
  have heq : I = fun u => (gK + δ) * K u := funext hlevels
  have hd := hI.unique (heq ▸ hK.const_mul (gK + δ))
  rw [hlevels t] at hd ⊢
  nlinarith [hd]

/-- A concrete zero-investment path: K=L=1, C=Y=exp(t), δ=0. -/
theorem zero_investment_accumulation (t : ℝ) :
    HasDerivAt (fun _ : ℝ => (1 : ℝ)) (0 - 0 * 1) t := by
  simpa using hasDerivAt_const t (1 : ℝ)

/-- A time-varying Cobb–Douglas technology produces the stated output. -/
theorem zero_investment_production (t : ℝ) :
    Real.exp t * Real.sqrt ((1 : ℝ) * 1) = Real.exp t := by simp

theorem zero_investment_resource (t : ℝ) : Real.exp t = Real.exp t + 0 := by ring

theorem zero_investment_constant_returns (K L t : ℝ) {a : ℝ} (ha : 0 < a) :
    Real.exp t * Real.sqrt ((a * K) * (a * L)) =
      a * (Real.exp t * Real.sqrt (K * L)) := by
  have h : (a * K) * (a * L) = a ^ 2 * (K * L) := by ring
  rw [h, Real.sqrt_mul (sq_nonneg a), Real.sqrt_sq ha.le]
  ring

/-- At t=2 the claimed frozen-technology, labor-augmenting identity fails.
F(K,L,t)=exp(t) sqrt(K L), K=L=1, and the proposed A(t)=exp(t). -/
theorem zero_investment_representation_fails :
    Real.exp 2 ≠ Real.exp 0 * Real.sqrt (1 * (Real.exp 2 * 1)) := by
  simp only [Real.exp_zero, one_mul, mul_one]
  have hsq : Real.exp (2 : ℝ) = (Real.exp 1) ^ 2 := by
    rw [pow_two, ← Real.exp_add]
    norm_num
  rw [hsq, Real.sqrt_sq (Real.exp_pos _).le]
  have hgt : 1 < Real.exp (1 : ℝ) := Real.one_lt_exp_iff.mpr zero_lt_one
  nlinarith

#print axioms investment_cancellation
#print axioms accumulation_rate_bridge
#print axioms zero_investment_accumulation
#print axioms zero_investment_production
#print axioms zero_investment_resource
#print axioms zero_investment_constant_returns
#print axioms zero_investment_representation_fails

end UzawaJonesExample
