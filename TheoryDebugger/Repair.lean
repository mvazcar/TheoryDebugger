import TheoryDebugger.Tactic

/-!
# Checking candidate repairs

A repair adds a predicate to an existing claim. It cannot replace its variables,
assumptions, or target. Success requires independent validity and existence
certificates. The commands report evidence without asserting a theorem.
-/

namespace TheoryDebugger
open Lean Meta Elab Tactic

/-- Append one explicitly reified hypothesis; preserve the original target. -/
def Problem.addRepair (p : Problem) (hypothesis : Expr) : MetaM Problem := do
  if p.hypotheses.size >= 30 then throwError "unsupported context size after repair"
  let type ← inferType hypothesis
  let _ ← reifyFormula p.vars type
  let types := p.assumptionTypes.push type
  let assumptionJson ← types.mapM fun a => return (← reifyFormula p.vars a).json
  let json := Json.mkObj [
    ("variables", .arr (p.vars.mapIdx fun i _ => .str s!"v{i}")),
    ("assumptions", .arr assumptionJson), ("goal", (← reifyFormula p.vars p.target).json)]
  return { p with
    hypotheses := p.hypotheses.push hypothesis
    assumptionTypes := types
    hypothesisNames := p.hypothesisNames.push "repair"
    json := json }

/-- Partial proofs do not make a candidate repair successful. -/
def Analysis.repairStatus (a : Analysis) : String :=
  if a.contradiction.isSome then "inconsistent"
  else if a.refutation.isSome then "refuted"
  else if a.validity.isSome && a.feasible.isSome then "valid"
  else "unknown"

def inspectRepairCommand (original candidate : Syntax) (json : Bool) : Command.CommandElabM Unit :=
  Command.liftTermElabM do
    let type ← Term.elabType original
    Term.synthesizeSyntheticMVarsNoPostponing
    forallTelescope (← instantiateMVars type) fun _ target => do
      let goal ← mkFreshExprMVar target
      let p ← extract goal.mvarId!
      let predicateType ← mkForallFVars p.vars (mkSort Level.zero)
      let predicate ← Term.elabTermEnsuringType candidate predicateType
      Term.synthesizeSyntheticMVarsNoPostponing
      let repair := (mkAppN (← instantiateMVars predicate) p.vars).headBeta
      let repairJson := (← reifyFormula p.vars repair).json
      withLocalDeclD `repair repair fun hypothesis => do
        let revised ← p.addRepair hypothesis
        let repairGoal ← mkFreshExprMVar target
        let _ ← Tactic.run repairGoal.mvarId! do
          let before ← analyze p (← discover p)
          let after ← analyze revised (← discover revised)
          let status := after.repairStatus
          if json then
            logInfo (Json.mkObj [("schema_version", toJson (2 : Nat)), ("operation", .str "repair"),
              ("status", .str status), ("accepted", .bool (status == "valid")),
              ("evidence", .str (if status == "unknown" then "none" else "lean_kernel")),
              ("original_problem_id", .str p.json.compress), ("repaired_problem_id", .str revised.json.compress),
              ("candidate", Json.mkObj [("assumptions", .arr #[repairJson])]),
              ("original", ← before.toJson), ("repaired", ← after.toJson)]).compress
          else
            logInfo m!"Original claim\n{← before.message}\nCandidate assumption: {repair}\nRepaired claim\n{← after.message}\nRepair: {status}"

elab "#theory_repair " original:term " with " candidate:term : command =>
  inspectRepairCommand original candidate false
elab "#theory_repair_json " original:term " with " candidate:term : command =>
  inspectRepairCommand original candidate true

end TheoryDebugger
