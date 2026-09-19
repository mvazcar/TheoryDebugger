import TheoryDebugger
open Lean Meta Elab Tactic TheoryDebugger

/- These commands assert results directly, so a diagnostic that merely prints
   an error cannot accidentally count as a passing test. -/
elab "#expect_theory " expected:str consistency:str removed:num " : " type:term : command =>
  Command.liftTermElabM do
    let t ← Term.elabType type
    Term.synthesizeSyntheticMVarsNoPostponing
    forallTelescope (← instantiateMVars t) fun _ body => do
      let goal ← mkFreshExprMVar body
      let _ ← Tactic.run goal.mvarId! do
        let before ← getGoals
        let a ← inspect goal.mvarId! true
        let actual := if a.refutation.isSome then "refuted" else if a.validity.isSome then "valid" else "unknown"
        let feasible := if a.feasible.isSome then "consistent" else if a.contradiction.isSome then "inconsistent" else "unknown"
        unless actual == expected.getString && feasible == consistency.getString do
          throwError "expected {expected.getString}/{consistency.getString}, got {actual}/{feasible}"
        unless a.dispensable.size == removed.getNat do
          throwError "wrong individually dispensable count: {a.dispensable.size}"
        unless (← getGoals) == before && !(← goal.mvarId!.isAssigned) do
          throwError "diagnosis modified the original goal"

elab "#expect_unsupported " type:term : command => Command.liftTermElabM do
  let t ← Term.elabType type
  Term.synthesizeSyntheticMVarsNoPostponing
  forallTelescope (← instantiateMVars t) fun _ body => do
    let goal ← mkFreshExprMVar body
    let supported ← try let _ ← extract goal.mvarId!; pure true catch _ => pure false
    if supported then throwError "unsupported expression was accepted"

#expect_theory "valid" "consistent" 0 : ∀ (x y : ℝ), x > 0 → y ≥ x ^ 2 → y > 0
#expect_theory "refuted" "consistent" 0 : ∀ (x y z : ℝ), x > 0 → y > 0 → x*y ≤ z^2 → x+y ≤ 2*z
#expect_theory "refuted" "consistent" 0 : ∀ (x y z : ℝ), x > 0 → y > 0 → x*y ≤ z^2 → z ≥ 0 → x+y ≤ 2*z
#expect_theory "valid" "inconsistent" 0 : ∀ (x : ℝ), x > 0 → x ≤ 0 → x = 42
#expect_theory "valid" "consistent" 2 : ∀ (x : ℝ), x ≥ 1 → x ≥ 2 → x > 0
#expect_theory "valid" "consistent" 0 : ∀ (x : ℝ), x ≥ 1 → x > 0
#expect_theory "valid" "consistent" 0 : ∀ (x : ℝ), x ≥ 2 → x > 0
#expect_theory "refuted" "consistent" 0 : ∀ (x : ℝ), x > 0
#expect_theory "valid" "consistent" 1 : ∀ (a x : ℝ), x^2 + a*x + 1 = 0 → True
#expect_theory "valid" "inconsistent" 1 : ∀ (x : ℝ), x^2 + 1 = 0 → True
#expect_theory "refuted" "consistent" 0 : ∀ (x : ℝ), x = -1/3 → x > 0
#expect_theory "refuted" "consistent" 0 : False
#expect_theory "valid" "consistent" 0 : True
#expect_theory "unknown" "unknown" 0 : ∀ (x : ℝ), x^2 = 2 → x > 0 → x < 0

#expect_unsupported ∀ (x : ℝ), x / 2 = x
#expect_unsupported ∀ (x : ℝ), x ^ 9 ≥ 0
#expect_unsupported ∀ (x : ℕ), x ≥ 0
#expect_unsupported ∀ (f : ℝ → ℝ) (x : ℝ), f x = x
#expect_unsupported ∀ (x : ℝ), (∀ (y : ℝ), y ≥ 0) → x > 0

section
-- The notation looks polynomial, but this is a different addition operation.
local instance : HAdd ℝ ℝ ℝ := ⟨fun x y => x - y⟩
#expect_unsupported ∀ (x y : ℝ), x + y = x - y
end

-- Native proofs work without an external solver. No consistency claim is inferred.
set_option theoryDebugger.solver false in
#expect_theory "valid" "unknown" 0 : ∀ (x : ℝ), x > 0 → x ≥ 0

-- Actual goal assignment, under a named theorem's restricted elaboration context.
theorem native_test_valid (x y : ℝ) (hx : x > 0) (hy : y ≥ x ^ 2) : y > 0 := by
  theory

-- Diagnostic tactics must leave all goals and hypotheses available.
theorem native_test_unchanged (x : ℝ) (hx : x > 0) : x ≥ 0 ∧ x > 0 := by
  constructor
  · theory?
    linarith
  · theory? +assumptions
    exact hx

elab "#test_untrusted_evidence" : command => Command.liftTermElabM do
  let t ← Term.elabType (← `(term| ∀ (x : ℝ), x > 0 → x ≥ 0))
  Term.synthesizeSyntheticMVarsNoPostponing
  forallTelescope (← instantiateMVars t) fun _ body => do
    let goal ← mkFreshExprMVar body
    let _ ← Tactic.run goal.mvarId! do
      let p ← extract goal.mvarId!
      let bogus := Json.mkObj [("classification", .str "refuted"),
        ("witness", Json.mkObj [("v0", .str "-1")])]
      let a ← analyze p bogus
      unless a.refutation.isNone && a.feasible.isNone && a.validity.isSome do
        throwError "forged solver witness crossed the trust boundary"
      -- The current assumption x > 0 cannot be reused to prove x > 0 after removal.
      unless (← proveClosed (← p.close p.target (some 0))).isNone do
        throwError "removed hypothesis leaked into the closed proof"

#test_untrusted_evidence

elab "#test_known_false_repair" : command => Command.liftTermElabM do
  let t ← Term.elabType (← `(term| ∀ (x y z : ℝ),
    x > 0 → y > 0 → x*y ≤ z^2 → z ≥ 0 → x+y ≤ 2*z))
  Term.synthesizeSyntheticMVarsNoPostponing
  forallTelescope (← instantiateMVars t) fun _ body => do
    let goal ← mkFreshExprMVar body
    let _ ← Tactic.run goal.mvarId! do
      let p ← extract goal.mvarId!
      let candidate := Json.mkObj [("witness", Json.mkObj [
        ("v0", .str "4"), ("v1", .str "1"), ("v2", .str "2")])]
      let a ← analyze p candidate
      unless a.feasible.isSome && a.refutation.isSome && a.validity.isNone do
        throwError "the fixed (4,1,2) false-repair regression failed"

#test_known_false_repair

elab "#test_axiom_boundary" : command => Command.liftTermElabM do
  let goal ← mkFreshExprMVar (mkConst ``True)
  let _ ← Tactic.run goal.mvarId! do
    let bad ← mkSorry (mkConst ``False) true
    let rejected ← try let _ ← certify (mkConst ``False) bad; pure false catch _ => pure true
    unless rejected do throwError "placeholder axiom accepted"
    let mismatch ← try
      let _ ← certify (mkConst ``False) (mkConst ``True.intro)
      pure false
    catch _ => pure true
    unless mismatch do throwError "proof of a different target accepted"

#test_axiom_boundary

#print axioms native_test_valid
#print axioms native_test_unchanged

elab "#expect_cases " expected:str positive:str negative:str " : " type:term : command =>
  Command.liftTermElabM do
    let t ← Term.elabType type
    Term.synthesizeSyntheticMVarsNoPostponing
    forallTelescope (← instantiateMVars t) fun _ body => do
      let goal ← mkFreshExprMVar body
      let _ ← Tactic.run goal.mvarId! do
        let a ← inspect goal.mvarId!
        unless a.classification == expected.getString && a.caseStatus true == positive.getString &&
            a.caseStatus false == negative.getString do
          throwError "wrong case diagnosis: {a.classification}/{a.caseStatus true}/{a.caseStatus false}"
        let json ← a.toJson
        unless (json.getObjValAs? String "classification").toOption == some expected.getString do
          throwError "JSON classification disagrees with native evidence"
        unless (← getGoals) == [goal.mvarId!] && !(← goal.mvarId!.isAssigned) do
          throwError "case diagnosis changed the original goal"

#expect_cases "true" "present" "absent" : ∀ (d s p : ℝ),
  d < 0 → s > 0 → d*(p+1) = s*p → p < 0
#expect_cases "mixed" "present" "present" : ∀ (d s p : ℝ),
  d < 0 → d*(p+1) = s*p → p ≤ 0
#expect_cases "false" "absent" "present" : ∀ (x : ℝ), x > 0 → x < 0
#expect_cases "inconsistent" "absent" "absent" : ∀ (x : ℝ), x > 0 → x ≤ 0 → x < 0
#expect_cases "true" "present" "absent" : True
#expect_cases "false" "absent" "present" : False
#expect_cases "unknown" "unknown" "absent" : ∀ (x : ℝ), x^2 = 2 → x > 0 → True

set_option theoryDebugger.solver false in
#expect_cases "unknown" "unknown" "absent" : ∀ (x : ℝ), x > 0 → x ≥ 0

elab "#test_repair_boundary" : command => Command.liftTermElabM do
  let t ← Term.elabType (← `(term| ∀ (x : ℝ), x > 0 → x > 1))
  Term.synthesizeSyntheticMVarsNoPostponing
  forallTelescope (← instantiateMVars t) fun _ body => do
    let goal ← mkFreshExprMVar body
    let p ← extract goal.mvarId!
    let predicateType ← mkForallFVars p.vars (mkSort Level.zero)
    for (candidateSyntax, status) in #[
        (← `(term| fun x => x > 2), "valid"),
        (← `(term| fun x => x ≤ 0), "inconsistent"),
        (← `(term| fun x => x > 0), "refuted")] do
      let predicate ← Term.elabTermEnsuringType candidateSyntax predicateType
      Term.synthesizeSyntheticMVarsNoPostponing
      let repair := (mkAppN (← instantiateMVars predicate) p.vars).headBeta
      withLocalDeclD `repair repair fun hypothesis => do
        let revised ← p.addRepair hypothesis
        unless revised.target == p.target && revised.assumptionTypes.pop == p.assumptionTypes do
          throwError "repair replaced part of the original input"
        let repairGoal ← mkFreshExprMVar body
        let _ ← Tactic.run repairGoal.mvarId! do
          let a ← analyze revised (← discover revised)
          unless a.repairStatus == status do throwError "wrong repair status: {a.repairStatus}"
          -- The new local repair hypothesis cannot leak into the original proof.
          unless (← proveClosed (← p.close p.target)).isNone do
            throwError "repair hypothesis contaminated the original claim"
          unless !(← goal.mvarId!.isAssigned) do throwError "repair assigned the original goal"

#test_repair_boundary

elab "#test_poisoned_cases" : command => Command.liftTermElabM do
  let t ← Term.elabType (← `(term| ∀ (x : ℝ), x > 0 → x ≥ 0))
  Term.synthesizeSyntheticMVarsNoPostponing
  forallTelescope (← instantiateMVars t) fun _ body => do
    let goal ← mkFreshExprMVar body
    let _ ← Tactic.run goal.mvarId! do
      let p ← extract goal.mvarId!
      let fake := Json.mkObj [("status", .str "present"), ("evidence", .str "lean_kernel"),
        ("witness", Json.mkObj [("v0", .str "-1")])]
      let a ← analyze p (Json.mkObj [("classification", .str "mixed"),
        ("cases", Json.mkObj [("satisfying", fake), ("refuting", fake)])])
      unless a.classification == "unknown" && a.refuting.isNone && a.satisfying.isNone do
        throwError "forged case evidence was trusted"

#test_poisoned_cases

#print axioms TheoryDebugger.no_refuting_iff
#print axioms TheoryDebugger.no_satisfying_iff
#print axioms TheoryDebugger.no_cases_iff
#print axioms TheoryDebugger.nonvacuous_repair_iff
