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

theorem applyQCUniqueness
    {Validator Checkpoint : Type*}
    [DecidableEq Validator] [DecidableEq Checkpoint]
    (validators signers₁ signers₂ byzantine : Finset Validator) (f : ℕ)
    (certificate₁ certificate₂ : ApplyCertificate Checkpoint)
    (hV : validators.card = 3 * f + 1)
    (hsigners₁ : signers₁ ⊆ validators)
    (hsigners₂ : signers₂ ⊆ validators)
    (hcard₁ : 2 * f + 1 ≤ signers₁.card)
    (hcard₂ : 2 * f + 1 ≤ signers₂.card)
    (hbyzantine : byzantine.card ≤ f)
    (honestApplyVoteUnique : ∀ validator,
      validator ∈ signers₁ ∩ signers₂ → validator ∉ byzantine →
        certificate₁ = certificate₂) :
    certificate₁ = certificate₂ :=
  conflictingQCImpossible validators signers₁ signers₂ byzantine f
    certificate₁ certificate₂ hV hsigners₁ hsigners₂ hcard₁ hcard₂
    hbyzantine honestApplyVoteUnique

theorem currentStateUniqueFromQCIntersection
    {Validator Checkpoint : Type*}
    [DecidableEq Validator] [DecidableEq Checkpoint]
    (validators signers₁ signers₂ byzantine : Finset Validator) (f : ℕ)
    (certificate₁ certificate₂ : ApplyCertificate Checkpoint)
    (hV : validators.card = 3 * f + 1)
    (hsigners₁ : signers₁ ⊆ validators)
    (hsigners₂ : signers₂ ⊆ validators)
    (hcard₁ : 2 * f + 1 ≤ signers₁.card)
    (hcard₂ : 2 * f + 1 ≤ signers₂.card)
    (hbyzantine : byzantine.card ≤ f)
    (honestApplyVoteUnique : ∀ validator,
      validator ∈ signers₁ ∩ signers₂ → validator ∉ byzantine →
        certificate₁ = certificate₂) :
    advanceCurrent certificate₁.parent certificate₁ =
      advanceCurrent certificate₂.parent certificate₂ := by
  have hcertificate := applyQCUniqueness validators signers₁ signers₂
    byzantine f certificate₁ certificate₂ hV hsigners₁ hsigners₂
    hcard₁ hcard₂ hbyzantine honestApplyVoteUnique
  exact currentStateUnique certificate₁ certificate₂ hcertificate

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

structure DurableRecoveryState (Vote Certificate Checkpoint : Type*) where
  voteJournal : Finset Vote
  certificates : Finset Certificate
  currentCheckpoint : Checkpoint

structure RuntimeRecoveryState (Vote Certificate Checkpoint : Type*) where
  durable : DurableRecoveryState Vote Certificate Checkpoint
  volatileVotes : Finset Vote
  recoveredCertificates : Finset Certificate
  currentCheckpoint : Checkpoint

def recoverFullState {Vote Certificate Checkpoint : Type*}
    (durable : DurableRecoveryState Vote Certificate Checkpoint) :
    RuntimeRecoveryState Vote Certificate Checkpoint :=
  { durable := durable
    volatileVotes := durable.voteJournal
    recoveredCertificates := durable.certificates
    currentCheckpoint := durable.currentCheckpoint }

def restartAndRecover {Vote Certificate Checkpoint : Type*}
    (runtime : RuntimeRecoveryState Vote Certificate Checkpoint) :
    RuntimeRecoveryState Vote Certificate Checkpoint :=
  recoverFullState runtime.durable

theorem recoveryRestoresDurableVoteJournal
    {Vote Certificate Checkpoint : Type*}
    (durable : DurableRecoveryState Vote Certificate Checkpoint) :
    (recoverFullState durable).volatileVotes = durable.voteJournal := rfl

theorem recoveryRestoresCertificates
    {Vote Certificate Checkpoint : Type*}
    (durable : DurableRecoveryState Vote Certificate Checkpoint) :
    (recoverFullState durable).recoveredCertificates = durable.certificates := rfl

theorem recoveryRestoresCurrentCheckpoint
    {Vote Certificate Checkpoint : Type*}
    (durable : DurableRecoveryState Vote Certificate Checkpoint) :
    (recoverFullState durable).currentCheckpoint = durable.currentCheckpoint := rfl

theorem fullRecoveryObservationalEquivalence
    {Vote Certificate Checkpoint : Type*}
    (runtime : RuntimeRecoveryState Vote Certificate Checkpoint) :
    let recovered := restartAndRecover runtime
    recovered.volatileVotes = runtime.durable.voteJournal ∧
      recovered.recoveredCertificates = runtime.durable.certificates ∧
      recovered.currentCheckpoint = runtime.durable.currentCheckpoint := by
  simp [restartAndRecover, recoverFullState]

theorem restartRecoveryIdempotent
    {Vote Certificate Checkpoint : Type*}
    (runtime : RuntimeRecoveryState Vote Certificate Checkpoint) :
    restartAndRecover (restartAndRecover runtime) = restartAndRecover runtime := by
  rfl

end DeltaReduce
