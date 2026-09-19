import TheoryDebugger

/- Independently transcribed polynomial consequences of the tax-incidence model
   in Mulligan, Davenport and England (2018), Section 3.1, Figures 2, 4, and 5.
   d = demand slope; s = supply slope; p = derivative of the seller's price
   with respect to a per-unit tax. The equilibrium derivative is assumed here;
   no automatic differentiation or general projection is claimed. -/

namespace Paper2018Tax

-- Figures 2 and 4 use strictly falling demand and strictly rising supply.
theorem seller_price_falls (d s p : ℝ) (hd : d < 0) (hs : s > 0)
    (equilibrium : d * (p + 1) = s * p) : p < 0 := by
  theory

theorem seller_price_falls_less_than_tax (d s p : ℝ) (hd : d < 0) (hs : s > 0)
    (equilibrium : d * (p + 1) = s * p) : p > -1 := by
  theory

-- Figure 5 drops the supply-slope restriction: the weak sign claim is refuted.
#theory (∀ (d s p : ℝ), d < 0 → d * (p + 1) = s * p → p ≤ 0)

-- Check the paper's proposed sufficient restriction against the original goal.
-- We supply this restriction ourselves; our prototype does not discover it.
theorem weak_supply_repairs_sign (d s p : ℝ) (hd : d < 0) (hs : s ≥ 0)
    (equilibrium : d * (p + 1) = s * p) : p ≤ 0 := by
  theory

-- Both outcomes really occur when the supply restriction is absent.
-- These are exact substitutions into the same original assumptions and goal.
theorem satisfying_assignment :
    (-1 : ℝ) < 0 ∧ (-1 : ℝ) * (-1 / 2 + 1) = 1 * (-1 / 2) ∧
      (-1 : ℝ) / 2 ≤ 0 := by
  norm_num

theorem refuting_assignment :
    (-1 : ℝ) < 0 ∧ (-1 : ℝ) * (1 + 1) = (-2) * 1 ∧ ¬ (1 : ℝ) ≤ 0 := by
  norm_num

#print axioms seller_price_falls
#print axioms seller_price_falls_less_than_tax
#print axioms weak_supply_repairs_sign
#print axioms satisfying_assignment
#print axioms refuting_assignment

end Paper2018Tax
