import Mathlib.Data.Finset.Card
import Lean.Elab.Tactic.Omega

/-! PO-Q1 quorum intersection and PO-Q2 conflicting-certificate exclusion. -/

namespace DeltaReduce

theorem quorumIntersection {Validator : Type*} [DecidableEq Validator]
    (validators q₁ q₂ : Finset Validator) (f : ℕ)
    (hV : validators.card = 3 * f + 1)
    (hq₁ : q₁ ⊆ validators) (hq₂ : q₂ ⊆ validators)
    (hcard₁ : 2 * f + 1 ≤ q₁.card) (hcard₂ : 2 * f + 1 ≤ q₂.card) :
    f + 1 ≤ (q₁ ∩ q₂).card := by
  have hunion : (q₁ ∪ q₂).card ≤ validators.card :=
    Finset.card_le_card (Finset.union_subset hq₁ hq₂)
  have hcount := Finset.card_union_add_card_inter q₁ q₂
  omega

theorem quorumIntersectionContainsHonest
    {Validator : Type*} [DecidableEq Validator]
    (validators q₁ q₂ byzantine : Finset Validator) (f : ℕ)
    (hV : validators.card = 3 * f + 1)
    (hq₁ : q₁ ⊆ validators) (hq₂ : q₂ ⊆ validators)
    (hcard₁ : 2 * f + 1 ≤ q₁.card) (hcard₂ : 2 * f + 1 ≤ q₂.card)
    (hbyzantine : byzantine.card ≤ f) :
    ∃ validator ∈ q₁ ∩ q₂, validator ∉ byzantine := by
  have hinter := quorumIntersection validators q₁ q₂ f hV hq₁ hq₂ hcard₁ hcard₂
  by_contra hnone
  have hsubset : q₁ ∩ q₂ ⊆ byzantine := by
    intro validator hvalidator
    by_contra hhonest
    exact hnone ⟨validator, hvalidator, hhonest⟩
  have hle := Finset.card_le_card hsubset
  omega

theorem conflictingQCImpossible
    {Validator Body : Type*} [DecidableEq Validator]
    (validators q₁ q₂ byzantine : Finset Validator) (f : ℕ)
    (body₁ body₂ : Body)
    (hV : validators.card = 3 * f + 1)
    (hq₁ : q₁ ⊆ validators) (hq₂ : q₂ ⊆ validators)
    (hcard₁ : 2 * f + 1 ≤ q₁.card) (hcard₂ : 2 * f + 1 ≤ q₂.card)
    (hbyzantine : byzantine.card ≤ f)
    (honestDurableVoteUnique : ∀ validator,
      validator ∈ q₁ ∩ q₂ → validator ∉ byzantine → body₁ = body₂) :
    body₁ = body₂ := by
  obtain ⟨validator, hinter, hhonest⟩ :=
    quorumIntersectionContainsHonest validators q₁ q₂ byzantine f
      hV hq₁ hq₂ hcard₁ hcard₂ hbyzantine
  exact honestDurableVoteUnique validator hinter hhonest

end DeltaReduce
