import TheoryDebugger.Frontend
import TheoryDebugger.Classification
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
  satisfying : Option Certificate := none
  refuting : Option Certificate := none
  falseThroughout : Option Certificate := none
  satisfyingWitness : Json := .null
  refutingWitness : Json := .null
  witness : Array String := #[]
  dispensable : Array (Nat × Certificate) := #[]

/-- Existentially close the real variables, without importing local hypotheses. -/
def Problem.existsClosure (p : Problem) (body : Expr) : MetaM Expr := do
  let mut type := body
  for v in p.vars.reverse do
    type ← mkAppM ``Exists #[← mkLambdaFVars #[v] type]
  if type.hasFVar || type.hasMVar then throwError "existential certificate is not closed"
  return type

private def packWitness (type : Expr) (values : List Expr) (ground : Expr) : MetaM Expr := do
  match values with
  | [] => return ground
  | value :: rest =>
    let predicate := type.getAppArgs[1]!
    let proof ← packWitness (← whnf (mkApp predicate value)) rest ground
    return mkApp4 (mkConst ``Exists.intro [Level.one]) (mkConst ``Real) predicate value proof

/-- Turn exact ground evidence into a kernel-checked existential declaration. -/
def checkWitness (p : Problem) (body : Expr) (values : Array Expr) : TacticM (Option Certificate) := do
  let some ground ← proveClosed (body.replaceFVars p.vars values) | return none
  let type ← p.existsClosure body
  return some (← certify type (← packWitness type values.toList ground.proof))

def Analysis.caseStatus (a : Analysis) (positive : Bool) : String :=
  if (if positive then a.satisfying else a.refuting).isSome then "present"
  else if a.contradiction.isSome || (if positive then a.falseThroughout else a.validity).isSome then "absent"
  else "unknown"

def Analysis.classification (a : Analysis) : String :=
  classifyCases (a.caseStatus true) (a.caseStatus false)

def analyze (p : Problem) (solverReport : Json) (checkAssumptions := false) : TacticM Analysis := do
  let original ← p.close p.target
  let mut result : Analysis := { problem := p, solverReport }
  -- Neither a solver truth value nor a solver's claimed evidence level is trusted.
  let mut candidates := #[solverReport]
  for side in #["satisfying", "refuting"] do
    if let .ok cases := solverReport.getObjVal? "cases" then
      if let .ok candidate := cases.getObjVal? side then candidates := candidates.push candidate
  for candidate in candidates do
    if let .ok (values, labels) := witnessValues p candidate then
      if let some feasible ← checkWitness p p.antecedent values then
        result := { result with feasible := some feasible, witness := labels }
        let witness := (candidate.getObjVal? "witness").toOption.getD .null
        if let some satisfying ← checkWitness p (mkApp2 (mkConst ``And) p.antecedent p.target) values then
          result := { result with satisfying := some satisfying, satisfyingWitness := witness }
        if let some refuting ← checkWitness p
            (mkApp2 (mkConst ``And) p.antecedent (mkApp (mkConst ``Not) p.target)) values then
          result := { result with refuting := some refuting, refutingWitness := witness }
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
  if result.satisfying.isNone then
    result := { result with falseThroughout := ← proveClosed (← p.close (mkApp (mkConst ``Not) p.target)) }
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
  let mut msg := m!"TheoryDebugger\nAssumptions: {consistency}\nGoal: {validity}\nClassification: {a.classification}"
  for (label, witness) in #[("satisfying", a.satisfyingWitness), ("refuting", a.refutingWitness)] do
    if let .ok (_, labels) := witnessValues a.problem (Json.mkObj [("witness", witness)]) then
      let assignment := if labels.isEmpty then "{} (no real variables)" else String.intercalate ", " labels.toList
      msg := msg ++ m!"\nChecked {label} assignment: {assignment}"
  if !a.dispensable.isEmpty then
    let names := a.dispensable.map fun (i, _) => a.problem.hypothesisNames[i]!
    msg := msg ++ m!"\nIndividually dispensable (Lean checked): {String.intercalate ", " names.toList}"
    msg := msg ++ m!"\nThis does not authorize removing these assumptions together."
  if a.classification == "unknown" then
    let diagnostic := do
      let solver ← a.solverReport.getObjVal? "solver"
      solver.getObjValAs? String "classification"
    let reason := (a.solverReport.getObjValAs? String "reason").toOption.getD ""
    msg := msg ++ m!"\nSolver only: {diagnostic.toOption.getD "unknown"}."
    if !reason.isEmpty then msg := msg ++ m!"\n{reason}"
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
    | none => return Json.mkObj [("status", .str "unknown"), ("evidence", .str "none")]
    | some value => return Json.mkObj [("status", .str "lean_verified"), ("evidence", .str "lean_kernel"),
        ("type", .str (← ppExpr value.type).pretty), ("axioms", Lean.toJson (value.axioms.map Name.toString))]
  let fact (status : String) := Json.mkObj [("status", .str status),
    ("evidence", .str (if status == "unknown" then "none" else "lean_kernel"))]
  let side (positive : Bool) : MetaM Json := do
    let status := a.caseStatus positive
    let proof := if positive then a.satisfying.or a.falseThroughout else a.refuting.or a.validity
    return Json.mkObj [("status", .str status),
      ("evidence", .str (if status == "unknown" then "none" else "lean_kernel")),
      ("witness", if positive then a.satisfyingWitness else a.refutingWitness),
      ("certificate", ← cert (proof.or a.contradiction))]
  let dispensable ← a.dispensable.mapM fun (i, c) => do
    return Json.mkObj [("index", Lean.toJson i), ("name", Lean.toJson a.problem.hypothesisNames[i]!),
      ("certificate", ← cert (some c))]
  return Json.mkObj [("schema_version", Lean.toJson (2 : Nat)), ("problem", a.problem.json),
    ("problem_id", .str a.problem.json.compress),
    ("original_goal", .str (← ppExpr (← a.problem.close a.problem.target)).pretty),
    ("classification", .str a.classification),
    ("classification_evidence", .str (if a.classification == "unknown" then "none" else "lean_kernel")),
    ("validity", fact (if a.refutation.isSome then "refuted" else if a.validity.isSome then "valid" else "unknown")),
    ("consistency", fact (if a.feasible.isSome then "consistent" else if a.contradiction.isSome then "inconsistent" else "unknown")),
    ("cases", Json.mkObj [("satisfying", ← side true), ("refuting", ← side false)]),
    ("validity_certificate", ← cert a.validity), ("refutation", ← cert a.refutation),
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
            logInfo (Json.mkObj [("schema_version", toJson (2 : Nat)), ("classification", .str "unsupported"),
              ("classification_evidence", .str "none"),
              ("reason", .str (← e.toMessageData.toString))]).compress
          else logInfo m!"TheoryDebugger: unsupported or unavailable\n{e.toMessageData}"

elab "#theory " type:term : command => inspectCommand type false false
elab "#theory_assumptions " type:term : command => inspectCommand type false true
elab "#theory_json " type:term : command => inspectCommand type true true

end TheoryDebugger
