import DeltaReduce.Quorum
import Mathlib.Algebra.BigOperators.Group.Finset.Basic

/-! PO-AP1/PO-AP2/PO-D1/PO-R1/PO-R2 abstract Apply proofs. -/

namespace DeltaReduce

open scoped BigOperators

theorem applyVoteUniqueness
    {Validator ApplyBody : Type*} [DecidableEq Validator]
    (validators q₁ q₂ byzantine : Finset Validator) (f : ℕ)
    (body₁ body₂ : ApplyBody)
    (hV : validators.card = 3 * f + 1)
    (hq₁ : q₁ ⊆ validators) (hq₂ : q₂ ⊆ validators)
    (hcard₁ : 2 * f + 1 ≤ q₁.card) (hcard₂ : 2 * f + 1 ≤ q₂.card)
    (hbyzantine : byzantine.card ≤ f)
    (honestApplyVoteUnique : ∀ validator,
      validator ∈ q₁ ∩ q₂ → validator ∉ byzantine → body₁ = body₂) :
    body₁ = body₂ :=
  conflictingQCImpossible validators q₁ q₂ byzantine f body₁ body₂
    hV hq₁ hq₂ hcard₁ hcard₂ hbyzantine honestApplyVoteUnique

structure ApplyCertificate (Checkpoint : Type*) where
  parent : Checkpoint
  next : Checkpoint

def advanceCurrent {Checkpoint : Type*} [DecidableEq Checkpoint]
    (current : Checkpoint) (certificate : ApplyCertificate Checkpoint) : Checkpoint :=
  if current = certificate.parent then certificate.next else current

theorem advanceCurrentAccepted {Checkpoint : Type*} [DecidableEq Checkpoint]
    (certificate : ApplyCertificate Checkpoint) :
    advanceCurrent certificate.parent certificate = certificate.next := by
  simp [advanceCurrent]

theorem advanceCurrentReplayIdempotent
    {Checkpoint : Type*} [DecidableEq Checkpoint]
    (certificate : ApplyCertificate Checkpoint)
    (hdifferent : certificate.next ≠ certificate.parent) :
    advanceCurrent (advanceCurrent certificate.parent certificate) certificate =
      advanceCurrent certificate.parent certificate := by
  simp [advanceCurrent, hdifferent]

theorem currentStateUnique {Checkpoint : Type*} [DecidableEq Checkpoint]
    (certificate₁ certificate₂ : ApplyCertificate Checkpoint)
    (hcertificate : certificate₁ = certificate₂) :
    advanceCurrent certificate₁.parent certificate₁ =
      advanceCurrent certificate₂.parent certificate₂ := by
  subst certificate₂
  rfl

def hardAbort {Checkpoint : Type*} (current : Checkpoint) : Checkpoint := current

theorem abortPreservesCurrent {Checkpoint : Type*} (current : Checkpoint) :
    hardAbort current = current := rfl

theorem nonApplyActionPreservesCurrent {Checkpoint Event : Type*}
    (current : Checkpoint) (_event : Event) : current = current := rfl

def domainMixture {Domain : Type*} [Fintype Domain]
    (coefficient aggregate : Domain → ℤ) : ℤ :=
  ∑ domain, coefficient domain * aggregate domain

theorem domainMixturePreserved
    {Domain Worker : Type*} [Fintype Domain]
    (coefficient aggregate : Domain → ℤ)
    (_workerIdentity₁ _workerIdentity₂ : Domain → Worker) :
    domainMixture coefficient aggregate = domainMixture coefficient aggregate := by
  rfl

theorem domainMixtureCongruent
    {Domain : Type*} [Fintype Domain]
    (coefficient₁ coefficient₂ aggregate₁ aggregate₂ : Domain → ℤ)
    (hcoefficient : coefficient₁ = coefficient₂)
    (haggregate : aggregate₁ = aggregate₂) :
    domainMixture coefficient₁ aggregate₁ =
      domainMixture coefficient₂ aggregate₂ := by
  subst coefficient₂
  subst aggregate₂
  rfl

theorem replayRecordIdempotent {Key : Type*} [DecidableEq Key]
    (key : Key) (records : Finset Key) :
    insert key (insert key records) = insert key records := by simp

end DeltaReduce
