import TheoryDebugger.Frontend
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Positivity

open Lean Meta Elab Tactic

register_option theoryDebugger.python : String := {
  defValue := "python"
  descr := "Python executable with the theorydebugger package installed" }
register_option theoryDebugger.solver : Bool := {
  defValue := true
  descr := "Run the untrusted cvc5 discovery bridge; native checking is always required" }
register_option theoryDebugger.timeoutMs : Nat := {
  defValue := 2000
  descr := "cvc5 time limit for each query (1..10000 milliseconds)" }

namespace TheoryDebugger

structure Certificate where
  type : Expr
  proof : Expr
  axioms : Array Name

/-- Ask the kernel to check a closed proof, then audit its transitive axioms.
The temporary declaration is removed; the explicit proof term is retained. -/
def certify (type proof : Expr) : TacticM Certificate := do
  if type.hasMVar || type.hasFVar || proof.hasMVar || proof.hasFVar then
    throwError "certificate is not closed"
  let env ← getEnv
  try
    let name ← mkFreshUserName ((env.asyncPrefix?.getD `TheoryDebugger) ++ `checked)
    addDecl (.thmDecl { name, levelParams := [], type, value := proof })
    let axioms ← collectAxioms name
    for ax in axioms do
      unless #[``propext, ``Classical.choice, ``Quot.sound].contains ax do
        throwError "unapproved axiom dependency: {ax}"
    return { type, proof, axioms }
  finally
    setEnv env

/-- Search in an empty local context. In particular, a current hypothesis cannot
accidentally prove a witness or a leave-one-out claim. Restore all goal state. -/
def proveClosed (type : Expr) : TacticM (Option Certificate) := withCurrHeartbeats do
  let saved ← saveState
  try
    withLCtx {} {} do
      let goal ← mkFreshExprMVar type
      setGoals [goal.mvarId!]
      evalTactic (← `(tactic| intros; first
        | (solve | norm_num [realNat, realNeg, realDiv] at *)
        | assumption | exact True.intro | nlinarith | positivity))
      unless (← getUnsolvedGoals).isEmpty do return none
      let proof ← instantiateMVars goal
      return some (← certify type proof)
  catch _ =>
    return none
  finally
    saved.restore

def discover (p : Problem) : TacticM Json := do
  if !theoryDebugger.solver.get (← getOptions) then
    return Json.mkObj [("classification", .str "unknown"), ("reason", .str "solver disabled")]
  let python := (← IO.getEnv "THEORYDEBUGGER_PYTHON").getD (theoryDebugger.python.get (← getOptions))
  try
    let input := Json.mkObj [("problem", p.json), ("timeout_ms", toJson (theoryDebugger.timeoutMs.get (← getOptions)))]
    let result ← IO.Process.output { cmd := python, args := #["-m", "theorydebugger.bridge"] } (some input.compress)
    if result.exitCode != 0 then
      return Json.mkObj [("classification", .str "unknown"), ("reason", .str result.stderr)]
    match Json.parse result.stdout with
    | .ok result => return result
    | .error msg => return Json.mkObj [("classification", .str "unknown"), ("reason", .str msg)]
  catch e =>
    return Json.mkObj [("classification", .str "unknown"), ("reason", .str (← e.toMessageData.toString))]

def rationalExpr (value : String) : Except String Expr := do
  if value.length > 260 then throw "witness numeral too large"
  let (n, d) ← match value.splitOn "/" with
    | [n] => pure (n, "1")
    | [n, d] => pure (n, d)
    | _ => throw "invalid rational witness"
  let some n := n.toInt? | throw "invalid rational numerator"
  let some d := d.toNat? | throw "invalid rational denominator"
  if d == 0 then throw "zero rational denominator"
  let numerator := mkApp (mkConst ``realNat) (mkNatLit n.natAbs)
  let numerator := if n < 0 then mkApp (mkConst ``realNeg) numerator else numerator
  if d == 1 then return numerator
  return mkApp2 (mkConst ``realDiv) numerator (mkApp (mkConst ``realNat) (mkNatLit d))

def witnessValues (p : Problem) (report : Json) : Except String (Array Expr × Array String) := do
  let witness ← report.getObjVal? "witness"
  let mut values := #[]
  let mut labels := #[]
  for i in [:p.vars.size] do
    let value ← witness.getObjValAs? String s!"v{i}"
    values := values.push (← rationalExpr value)
    labels := labels.push s!"{p.variableNames[i]!} = {value}"
  -- An empty assignment is still an assignment; absence of a witness is not.
  if p.vars.isEmpty then
    let _ ← witness.getObj?
  return (values, labels)

structure Analysis where
  problem : Problem
  solverReport : Json
  validity : Option Certificate := none
  contradiction : Option Certificate := none
  feasible : Option Certificate := none
  refutation : Option Certificate := none
  witness : Array String := #[]
  dispensable : Array (Nat × Certificate) := #[]

def analyze (p : Problem) (solverReport : Json) (checkAssumptions := false) : TacticM Analysis := do
  let original ← p.close p.target
  let mut result : Analysis := { problem := p, solverReport }
  -- Neither a solver truth value nor a solver's claimed evidence level is trusted.
  if let .ok (values, labels) := witnessValues p solverReport then
    if let some feasible ← proveClosed (p.antecedent.replaceFVars p.vars values) then
      result := { result with feasible := some feasible, witness := labels }
      let mut specialized := original
      for value in values do
        let .forallE _ _ body _ := specialized | throwError "internal quantifier mismatch"
        specialized := body.instantiate1 value
      if let some failed ← proveClosed (mkApp (mkConst ``Not) specialized) then
        let refutation ← withLocalDeclD `universal original fun universal => do
          let proof := mkApp failed.proof (mkAppN universal values)
          mkLambdaFVars #[universal] proof
        let checked ← certify (mkApp (mkConst ``Not) original) refutation
        result := { result with refutation := some checked }
  if result.feasible.isNone then
    result := { result with contradiction := ← proveClosed (← p.close (mkConst ``False)) }
  if result.refutation.isNone then
    result := { result with validity := ← proveClosed original }
  if checkAssumptions && result.validity.isSome then
    for i in [:p.hypotheses.size] do
      if let some proof ← proveClosed (← p.close p.target (some i)) then
        result := { result with dispensable := result.dispensable.push (i, proof) }
  return result

def inspect (goal : MVarId) (checkAssumptions := false) : TacticM Analysis := goal.withContext do
  let p ← extract goal
  analyze p (← discover p) checkAssumptions

def Analysis.message (a : Analysis) : MetaM MessageData := do
  let consistency := if a.feasible.isSome then "feasible assignment checked by Lean"
    else if a.contradiction.isSome then "contradictory (Lean checked); validity is vacuous"
    else "unknown to Lean; consult solver-only diagnostics"
  let validity := if a.refutation.isSome then "refuted (Lean checked against the original goal)"
    else if a.validity.isSome then "valid (Lean checked against the original goal)"
    else "unknown to Lean; no proof or checked refutation"
  let mut msg := m!"TheoryDebugger\nAssumptions: {consistency}\nGoal: {validity}"
  if !a.witness.isEmpty then msg := msg ++ m!"\nChecked witness: {String.intercalate ", " a.witness.toList}"
  if !a.dispensable.isEmpty then
    let names := a.dispensable.map fun (i, _) => a.problem.hypothesisNames[i]!
    msg := msg ++ m!"\nIndividually dispensable (Lean checked): {String.intercalate ", " names.toList}"
    msg := msg ++ m!"\nThis does not authorize removing these assumptions together."
  if a.validity.isNone && a.refutation.isNone || a.feasible.isNone && a.contradiction.isNone then
    let diagnostic := (a.solverReport.getObjValAs? String "classification").toOption.getD "unknown"
    let reason := (a.solverReport.getObjValAs? String "reason").toOption.getD ""
    msg := msg ++ m!"\nSolver only: {diagnostic}. {reason}"
  return msg

def runDiagnostic (assumptions : Bool) : TacticM Unit := withMainContext do
  try
    let result ← inspect (← getMainGoal) assumptions
    logInfo (← result.message)
  catch e =>
    logInfo m!"TheoryDebugger: unsupported or unavailable\n{e.toMessageData}"

/-- Diagnose without changing the proof state. -/
elab (name := theoryDiagnostic) "theory?" : tactic => runDiagnostic false
elab (name := theoryAssumptions) "theory?" "+" "assumptions" : tactic => runDiagnostic true

#allow_unused_tactic! theoryDiagnostic theoryAssumptions

/-- Close exactly the current goal using an independently checked native proof. -/
elab "theory" : tactic => withMainContext do
  let goal ← getMainGoal
  let result ← inspect goal
  logInfo (← result.message)
  let some certificate := result.validity | throwError "TheoryDebugger: original goal remains unproved"
  let proof := mkAppN certificate.proof (result.problem.vars ++ result.problem.hypotheses)
  unless ← isDefEq (← inferType proof) (← goal.getType) do
    throwError "TheoryDebugger: proof does not match original goal"
  goal.assign proof
  replaceMainGoal []

def Analysis.toJson (a : Analysis) : MetaM Json := do
  let cert (value : Option Certificate) : MetaM Json := do
    match value with
    | none => return Json.mkObj [("status", .str "unknown")]
    | some value => return Json.mkObj [("status", .str "lean_kernel"),
        ("type", .str (← ppExpr value.type).pretty), ("axioms", Lean.toJson (value.axioms.map Name.toString))]
  let dispensable ← a.dispensable.mapM fun (i, c) => do
    return Json.mkObj [("index", Lean.toJson i), ("name", Lean.toJson a.problem.hypothesisNames[i]!),
      ("certificate", ← cert (some c))]
  return Json.mkObj [("schema_version", Lean.toJson (1 : Nat)), ("input", a.problem.json),
    ("original_goal", .str (← ppExpr (← a.problem.close a.problem.target)).pretty),
    ("validity", ← cert a.validity), ("refutation", ← cert a.refutation),
    ("contradiction", ← cert a.contradiction), ("feasible_assignment", ← cert a.feasible),
    ("witness", Lean.toJson a.witness), ("individually_dispensable", .arr dispensable),
    ("solver_only", a.solverReport)]

/-- Explore even a false conjecture without declaring a false theorem or using a placeholder. -/
def inspectCommand (type : Syntax) (json : Bool) (checkHyps : Bool) : Command.CommandElabM Unit :=
  Command.liftTermElabM do
    let type ← Term.elabType type
    Term.synthesizeSyntheticMVarsNoPostponing
    let type ← instantiateMVars type
    unless ← isProp type do throwError "expected a proposition"
    forallTelescope type fun _ target => do
      let goal ← mkFreshExprMVar target
      let _ ← Tactic.run goal.mvarId! do
        try
          let result ← inspect (← getMainGoal) checkHyps
          if json then logInfo (← result.toJson).compress else logInfo (← result.message)
        catch e =>
          if json then
            logInfo (Json.mkObj [("classification", .str "unsupported"),
              ("reason", .str (← e.toMessageData.toString))]).compress
          else logInfo m!"TheoryDebugger: unsupported or unavailable\n{e.toMessageData}"

elab "#theory " type:term : command => inspectCommand type false false
elab "#theory_assumptions " type:term : command => inspectCommand type false true
elab "#theory_json " type:term : command => inspectCommand type true true

end TheoryDebugger
