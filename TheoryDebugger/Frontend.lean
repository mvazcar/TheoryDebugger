import Mathlib.Basic.Real.Basic
import Lean

/- Original code. The frontend recognizes a deliberately small syntax and checks
   its semantics against fixed real operations, including the instances used. -/
namespace TheoryDebugger
open Lean Meta

def realNat (n : Nat) : ℝ := if n = 0 then 0 else if n = 1 then 1 else n
def realNeg (a : ℝ) : ℝ := -a
def realAdd (a b : ℝ) : ℝ := a + b
def realSub (a b : ℝ) : ℝ := a - b
def realMul (a b : ℝ) : ℝ := a * b
noncomputable def realDiv (a b : ℝ) : ℝ := a / b
def realPow (a : ℝ) (n : Nat) : ℝ := a ^ n
def realLT (a b : ℝ) : Prop := a < b
def realLE (a b : ℝ) : Prop := a ≤ b
def realGT (a b : ℝ) : Prop := a > b
def realGE (a b : ℝ) : Prop := a ≥ b
def realEq (a b : ℝ) : Prop := a = b
def realNe (a b : ℝ) : Prop := a ≠ b

def jop (op : String) (args : Array Json) : Json := .arr (#[.str op] ++ args)

structure Reified where
  json : Json
  meaning : Expr

def checked (original : Expr) (r : Reified) : MetaM Reified := do
  unless ← isDefEq original r.meaning do
    throwError "unsupported arithmetic instance or semantics: {original}"
  return r

def reifyReal (vars : Array Expr) (e : Expr) (fuel : Nat := 32) : MetaM Reified := do
  match fuel with
  | 0 => throwError "unsupported expression depth (maximum 32)"
  | fuel + 1 =>
    let e := e.consumeMData
    unless ← isDefEq (← inferType e) (mkConst ``Real) do
      throwError "unsupported non-real expression: {e}"
    if let some i := vars.findIdx? (· == e) then
      return { json := .str s!"v{i}", meaning := e }
    if let some (n, _) ← getOfNatValue? e ``Real then
      if n.repr.length > 128 then throwError "unsupported integer size"
      return ← checked e { json := .str n.repr, meaning := mkApp (mkConst ``realNat) (mkNatLit n) }
    let fn := e.getAppFn.constName?
    let args := e.getAppArgs
    if fn == some ``Neg.neg && args.size == 3 then
      let a ← reifyReal vars args[2]! fuel
      return ← checked e { json := jop "neg" #[a.json], meaning := mkApp (mkConst ``realNeg) a.meaning }
    if fn == some ``HDiv.hDiv && args.size == 6 then
      let numerator := args[4]!
      let neg := numerator.isAppOfArity ``Neg.neg 3
      let numeral := if neg then numerator.getAppArgs[2]! else numerator
      let some (n, _) ← getOfNatValue? numeral ``Real
        | throwError "unsupported division: only rational numeral constants are accepted"
      let some (d, _) ← getOfNatValue? args[5]! ``Real
        | throwError "unsupported division: denominator must be a positive numeral"
      if d == 0 || n.repr.length > 128 || d.repr.length > 128 then
        throwError "unsupported rational constant"
      let numerator := mkApp (mkConst ``realNat) (mkNatLit n)
      let numerator := if neg then mkApp (mkConst ``realNeg) numerator else numerator
      let meaning := mkApp2 (mkConst ``realDiv) numerator (mkApp (mkConst ``realNat) (mkNatLit d))
      let sign := if neg then "-" else ""
      return ← checked e ⟨.str s!"{sign}{n}/{d}", meaning⟩
    if fn == some ``HPow.hPow && args.size == 6 then
      let some n ← getNatValue? args[5]! | throwError "unsupported nonliteral exponent"
      if n > 8 then throwError "unsupported power (maximum 8)"
      let a ← reifyReal vars args[4]! fuel
      return ← checked e ⟨jop "^" #[a.json, toJson n], mkApp2 (mkConst ``realPow) a.meaning (mkNatLit n)⟩
    for (leanName, jsonName, meaningName) in
        #[( ``HAdd.hAdd, "+", ``realAdd), (``HSub.hSub, "-", ``realSub), (``HMul.hMul, "*", ``realMul)] do
      if fn == some leanName && args.size == 6 then
        let a ← reifyReal vars args[4]! fuel
        let b ← reifyReal vars args[5]! fuel
        return ← checked e ⟨jop jsonName #[a.json, b.json], mkApp2 (mkConst meaningName) a.meaning b.meaning⟩
    throwError "unsupported real expression: {e}"

def reifyFormula (vars : Array Expr) (e : Expr) (fuel : Nat := 32) : MetaM Reified := do
  match fuel with
  | 0 => throwError "unsupported formula depth (maximum 32)"
  | fuel + 1 =>
    let e := e.consumeMData
    if e.isConstOf ``True then return { json := .bool true, meaning := e }
    if e.isConstOf ``False then return { json := .bool false, meaning := e }
    let fn := e.getAppFn.constName?
    let args := e.getAppArgs
    if fn == some ``Not && args.size == 1 then
      let a ← reifyFormula vars args[0]! fuel
      return ← checked e { json := jop "not" #[a.json], meaning := mkApp (mkConst ``Not) a.meaning }
    for (leanName, jsonName) in #[( ``And, "and"), (``Or, "or")] do
      if fn == some leanName && args.size == 2 then
        let a ← reifyFormula vars args[0]! fuel
        let b ← reifyFormula vars args[1]! fuel
        return ← checked e ⟨jop jsonName #[a.json, b.json], mkApp2 (mkConst leanName) a.meaning b.meaning⟩
    for (leanName, jsonName, meaningName, size) in
        #[( ``LT.lt, "<", ``realLT, 4), (``LE.le, "<=", ``realLE, 4),
          (``GT.gt, ">", ``realGT, 4), (``GE.ge, ">=", ``realGE, 4),
          (``Eq, "=", ``realEq, 3), (``Ne, "!=", ``realNe, 3)] do
      if fn == some leanName && args.size == size then
        let a ← reifyReal vars args[size - 2]!
        let b ← reifyReal vars args[size - 1]!
        return ← checked e ⟨jop jsonName #[a.json, b.json], mkApp2 (mkConst meaningName) a.meaning b.meaning⟩
    throwError "unsupported proposition: {e}"

structure Problem where
  vars : Array Expr
  hypotheses : Array Expr
  assumptionTypes : Array Expr
  target : Expr
  json : Json
  variableNames : Array String
  hypothesisNames : Array String

def Problem.close (p : Problem) (target : Expr) (excluded : Option Nat := none) : MetaM Expr := do
  let mut hyps := #[]
  for i in [:p.hypotheses.size] do
    if excluded != some i then hyps := hyps.push p.hypotheses[i]!
  -- Nested `have` statements can retain already-assigned elaboration variables
  -- in hypothesis types. Resolve those assignments before checking closure;
  -- genuinely unresolved variables and hidden dependencies must still fail.
  let result ← instantiateMVars (← mkForallFVars (p.vars ++ hyps) target)
  if result.hasFVar then
    throwError "unsupported dependent context: the claim still refers to a local declaration outside the extracted variables and hypotheses; state a standalone algebraic lemma"
  if result.hasMVar then
    throwError "unsupported unresolved metavariables: finish elaborating the claim and its hypotheses before using TheoryDebugger"
  return result

def Problem.antecedent (p : Problem) : Expr :=
  p.assumptionTypes.foldr (fun a b => mkApp2 (mkConst ``And) a b) (mkConst ``True)

def extract (goal : MVarId) : MetaM Problem := goal.withContext do
  let mut vars := #[]
  let mut hypotheses := #[]
  let mut assumptionTypes := #[]
  let mut variableNames := #[]
  let mut hypothesisNames := #[]
  for decl in ← getLCtx do
    -- Lean's synthetic self-reference is not a user hypothesis. Closure below
    -- ensures no hidden declaration can become a dependency of our claim.
    if decl.isImplementationDetail then continue
    if decl.isLet then throwError "unsupported local definition: {decl.userName}; inline it first"
    if ← isDefEq decl.type (mkConst ``Real) then
      vars := vars.push decl.toExpr
      variableNames := variableNames.push decl.userName.toString
    else if ← isProp decl.type then
      hypotheses := hypotheses.push decl.toExpr
      assumptionTypes := assumptionTypes.push decl.type
      hypothesisNames := hypothesisNames.push decl.userName.eraseMacroScopes.toString
    else
      throwError "unsupported local declaration {decl.userName} : {decl.type}"
  if vars.size > 8 || hypotheses.size > 30 then throwError "unsupported context size"
  let target ← instantiateMVars (← goal.getType)
  let assumptions ← assumptionTypes.mapM fun a => return (← reifyFormula vars a).json
  let targetJson := (← reifyFormula vars target).json
  let json := Json.mkObj [
    ("variables", .arr (vars.mapIdx fun i _ => .str s!"v{i}")),
    ("assumptions", .arr assumptions), ("goal", targetJson)]
  -- The same normalized propositions must feed both universal proofs and
  -- ground/existential witness checks. Reification may resolve instance slots.
  assumptionTypes ← assumptionTypes.mapM instantiateMVars
  let target ← instantiateMVars target
  let p : Problem := { vars, hypotheses, assumptionTypes, target, json, variableNames, hypothesisNames }
  let _ ← p.close target
  return p

end TheoryDebugger
