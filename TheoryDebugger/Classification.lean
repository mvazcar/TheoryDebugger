import Mathlib.Basic.Real.Basic

/-!
# Logical basis of four-way diagnosis

Presence is an existential certificate. Absence can be certified by a universal
implication. These equivalences justify the two forms of evidence used by the
diagnostic interfaces; solver answers are not hypotheses of these lemmas.
-/

namespace TheoryDebugger

/-- No refuting assignment is equivalent to validity of the original implication. -/
theorem no_refuting_iff {α : Type*} (A H : α → Prop) :
    (¬ ∃ x, A x ∧ ¬ H x) ↔ ∀ x, A x → H x := by
  classical
  constructor
  · intro h x ha
    by_contra hn
    exact h ⟨x, ha, hn⟩
  · intro h ⟨x, ha, hn⟩
    exact hn (h x ha)

/-- No satisfying assignment means the conclusion fails throughout the model. -/
theorem no_satisfying_iff {α : Type*} (A H : α → Prop) :
    (¬ ∃ x, A x ∧ H x) ↔ ∀ x, A x → ¬ H x := by
  constructor
  · intro h x ha hh
    exact h ⟨x, ha, hh⟩
  · intro h ⟨x, ha, hh⟩
    exact h x ha hh

/-- Both kinds of assignment are absent exactly when the assumptions are impossible. -/
theorem no_cases_iff {α : Type*} (A H : α → Prop) :
    ((¬ ∃ x, A x ∧ H x) ∧ (¬ ∃ x, A x ∧ ¬ H x)) ↔ ¬ ∃ x, A x := by
  classical
  constructor
  · intro ⟨hp, hn⟩ ⟨x, ha⟩
    by_cases hh : H x
    · exact hp ⟨x, ha, hh⟩
    · exact hn ⟨x, ha, hh⟩
  · intro h
    exact ⟨fun ⟨x, ha, _⟩ => h ⟨x, ha⟩, fun ⟨x, ha, _⟩ => h ⟨x, ha⟩⟩

/-- A successful repair must admit an instance as well as rule out failures. -/
theorem nonvacuous_repair_iff {α : Type*} (A R H : α → Prop) :
    ((∃ x, A x ∧ R x) ∧ (∀ x, A x ∧ R x → H x)) ↔
      ((∃ x, (A x ∧ R x) ∧ H x) ∧ ¬ ∃ x, (A x ∧ R x) ∧ ¬ H x) := by
  constructor
  · rintro ⟨⟨x, ha⟩, h⟩
    exact ⟨⟨x, ha, h x ha⟩, (no_refuting_iff _ _).mpr h⟩
  · rintro ⟨⟨x, ha, _⟩, h⟩
    exact ⟨⟨x, ha⟩, (no_refuting_iff _ _).mp h⟩

/-- Shared schema-v2 labels; an incomplete pair remains unknown. -/
def classifyCases (satisfying refuting : String) : String :=
  match satisfying, refuting with
  | "present", "absent" => "true"
  | "present", "present" => "mixed"
  | "absent", "present" => "false"
  | "absent", "absent" => "inconsistent"
  | _, _ => "unknown"

end TheoryDebugger
