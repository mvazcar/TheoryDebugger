import TheoryDebugger

-- scripts/run_repairs.py asserts schema fields and acceptance, not just exit code.
#theory_json (∀ (x : ℝ), x > 0 → x < 1)
#theory_json False
#theory_repair_json (∀ (x : ℝ), x > 0 → x > 1) with (fun x => x > 2)
#theory_repair_json (∀ (x : ℝ), x > 0 → x > 1) with (fun x => x ≤ 0)
#theory_repair_json (∀ (x : ℝ), x > 0 → x > 1) with (fun x => x > 0)
