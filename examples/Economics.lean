import TheoryDebugger

/- Three small economic models. See docs/economics.md for the assumptions and
   the translation from economics into these polynomial statements.
   Run: lake env lean examples/Economics.lean
   The `theory` tactic must close each original theorem; no proof placeholders. -/

namespace Economics

-- One-unit downward shift of inverse supply, with downward-sloping demand.
theorem supply_shift_quantity (d s dq dp : ℝ)
    (hd : d < 0) (hs : s ≥ 0)
    (supply : s * dq - 1 = dp) (demand : d * dq = dp) : dq > 0 := by
  theory

theorem supply_shift_price (d s dq dp : ℝ)
    (hd : d < 0) (hs : s ≥ 0)
    (supply : s * dq - 1 = dp) (demand : d * dq = dp) : dp < 0 := by
  theory

-- Deliberately false: does that same supply shift raise the price?
#theory (∀ (d s dq dp : ℝ), d < 0 → s ≥ 0 →
  s * dq - 1 = dp → d * dq = dp → dp > 0)

-- A higher tax rate alone does not imply higher revenue.
#theory (∀ (t0 t1 b0 b1 : ℝ), 0 < t0 → t0 < t1 → t1 < 1 →
  0 < b0 → 0 < b1 → t1 * b1 > t0 * b0)

-- Repair: require that the tax base does not shrink.
theorem tax_revenue_with_preserved_base (t0 t1 b0 b1 : ℝ)
    (ht : 0 < t0) (increase : t0 < t1) (cap : t1 < 1)
    (base0 : 0 < b0) (base1 : 0 < b1) (preserved : b1 ≥ b0) :
    t1 * b1 > t0 * b0 := by
  theory

-- Linear inverse demand P(q)=a-b*q; constant marginal cost increases by dc.
-- Subtracting the two interior first-order conditions gives 2*b*dq = -dc.
theorem monopoly_half_pass_through (b dc dq dp : ℝ)
    (slope : b > 0) (cost : dc > 0)
    (foc : 2 * b * dq = -dc) (demand : dp = -(b * dq)) : 2 * dp = dc := by
  theory

theorem monopoly_quantity_falls (b dc dq dp : ℝ)
    (slope : b > 0) (cost : dc > 0)
    (foc : 2 * b * dq = -dc) (demand : dp = -(b * dq)) : dq < 0 := by
  theory

-- Deliberately false: is the entire cost increase passed on to buyers?
#theory (∀ (b dc dq dp : ℝ), b > 0 → dc > 0 →
  2 * b * dq = -dc → dp = -(b * dq) → dp = dc)

#print axioms supply_shift_quantity
#print axioms supply_shift_price
#print axioms tax_revenue_with_preserved_base
#print axioms monopoly_half_pass_through
#print axioms monopoly_quantity_falls

end Economics
