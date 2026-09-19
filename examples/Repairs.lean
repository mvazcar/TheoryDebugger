import TheoryDebugger

/-! Explicit candidate repairs of the paper's scalar tax-incidence model. -/

-- Removing the supply sign gives both satisfying and refuting instances.
#theory (∀ (d s p : ℝ), d < 0 → d * (p + 1) = s * p → p ≤ 0)

-- The proposed supply restriction preserves feasibility and proves the goal.
#theory_repair (∀ (d s p : ℝ), d < 0 → d * (p + 1) = s * p → p ≤ 0)
  with (fun _ s _ => s ≥ 0)

-- This assumption only "fixes" the implication by making the model impossible.
#theory_repair (∀ (d s p : ℝ), d < 0 → d * (p + 1) = s * p → p ≤ 0)
  with (fun d _ _ => d ≥ 0)

-- The famous (4,1,2) counterexample survives this proposed repair.
#theory_repair (∀ (x y z : ℝ), x > 0 → y > 0 → x*y ≤ z^2 → x+y ≤ 2*z)
  with (fun _ _ z => z ≥ 0)
