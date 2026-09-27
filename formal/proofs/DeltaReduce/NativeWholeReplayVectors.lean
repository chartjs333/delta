import DeltaReduce.NativeWholeReplay
import DeltaReduce.NativeMixedReplayVectors
import DeltaReduce.NativeSnapshotBaseVectors
import DeltaReduce.NativeCandidateAuthorityVectors

/-! Original two-candidate CONFIG/ISC policy and original ISC1/freeze2 records.
Finite actual SHA samples, not authenticated export or a new native execution. -/
namespace DeltaReduce.NativeWholeReplayVectors
open NativeReceiptBytes NativeVoteBytes NativeStateBytes NativeConfigReplay NativeTransition
open NativeMixedPolicyVectors (policy policyRaw)
open NativeMixedReplayVectors (initial)
open NativeIscAdmissionVectors (state)
set_option maxRecDepth 16384
set_option maxHeartbeats 1000000

def sha (raw : Bytes) : Bytes :=
  if raw = NativeSnapshotBaseVectors.preimage then NativeSnapshotBaseVectors.digest
  else NativeMixedPolicyVectors.sha raw

theorem priorHash : contentId sha stateDomain NativeStateCodecVectors.raw3 =
    some NativeTransitionVectors.priorId := by
  have different : contentPreimage stateDomain NativeStateCodecVectors.raw3 ≠
      NativeSnapshotBaseVectors.preimage := by decide
  simpa only [contentId,sha,if_neg different] using NativeMixedReplayVectors.priorHash

def isc : NativeFinalizedIscSection.Bound :=
  ⟨policy,state,NativeIscAdmissionVectors.bound.schema,NativeIscAdmissionVectors.bound.arithmetic,
    NativeTransitionVectors.priorId,[],[],[]⟩
theorem iscComputed : NativeFinalizedIscSection.bindSection sha policy state = some isc := by
  apply NativeFinalizedIscSection.fromComponents
  refine ⟨rfl,rfl,rfl,?_,rfl,rfl,rfl,rfl,rfl,by decide⟩
  change contentId sha stateDomain (encodeState NativeIscAdmissionVectors.wire) = _
  rw [NativeIscAdmissionVectors.stateEncoded]; exact priorHash

def norms : NativeNormSection.Bound := ⟨isc,[],[]⟩
def ecs : NativeEligibilitySection.Bound := ⟨norms,[],[],[],[],[],[],[]⟩
def plans : NativePlanSection.Bound :=
  ⟨ecs,NativeIscAdmissionVectors.bound.accumulator,[],[],[],[],[]⟩
def parameters : NativeParameterSection.Bound := ⟨plans,[],[],[],[],[],[],[]⟩
def sized : NativeSizedParameterSection.Bound := ⟨parameters,[]⟩
def roots : NativeAggregateSection.Bound := ⟨sized,[],[],[],[],[]⟩
def applies : NativeApplySection.Bound := ⟨roots,[],[],[],[],[],[],[]⟩
def tail : NativeFailureSection.Tail :=
  ⟨⟨[policy.config],[],[],[],[],[],[]⟩,[],[],[],[],[],[],[],[]⟩
def failure : NativeFailureSection.Bound := ⟨applies,tail⟩

theorem normsComputed : NativeNormSection.bindSection sha policy state = some norms := by
  unfold NativeNormSection.bindSection
  rw [iscComputed]
  rfl

theorem ecsComputed : NativeEligibilitySection.bindSection sha policy state = some ecs := by
  unfold NativeEligibilitySection.bindSection
  rw [normsComputed]
  rfl

theorem plansComputed : NativePlanSection.bindSection sha policy state = some plans := by
  unfold NativePlanSection.bindSection
  rw [ecsComputed]
  rfl

theorem parametersComputed : NativeParameterSection.bindSection sha policy state = some parameters := by
  unfold NativeParameterSection.bindSection
  rw [plansComputed]
  rfl

theorem sizedComputed : NativeSizedParameterSection.bindSection sha policy state = some sized := by
  unfold NativeSizedParameterSection.bindSection
  rw [parametersComputed]
  rfl

theorem rootsComputed : NativeAggregateSection.bindSection sha policy state = some roots := by
  unfold NativeAggregateSection.bindSection
  rw [sizedComputed]
  rfl

theorem appliesComputed : NativeApplySection.bindSection sha policy state = some applies := by
  unfold NativeApplySection.bindSection
  rw [rootsComputed]
  rfl

theorem failureComputed : NativeFailureSection.bindSection sha policy state = some failure := by
  unfold NativeFailureSection.bindSection
  rw [appliesComputed]
  rfl

theorem bodyHash : NativeInputSetBody.bodyId sha NativeSnapshotBaseVectors.body =
    some NativeSnapshotBaseVectors.checkedBody.id := by
  unfold NativeInputSetBody.bodyId
  change contentId sha NativeInputSetBody.bodyDomain (NativeInputSetBody.bodyBytes _) = _
  unfold contentId sha
  rw [if_neg NativeSnapshotBaseVectors.bodyPreimageDifferent]
  exact NativeMixedReplayVectors.inputHash

theorem expandedHash : NativeContractSize.contentId sha NativeIscCertificate.domain
    (NativeIscCertificate.json NativeSnapshotBaseVectors.expanded) =
    some NativeSnapshotBaseVectors.qc := by
  apply NativeContractSize.fromComponents
  · rw [NativeSnapshotBaseVectors.exactLength]; decide
  · unfold contentId sha
    simp only [NativeSnapshotBaseVectors.preimage,ite_true]
    rfl

theorem proposedComputed : NativeProposedIsc.check sha NativeSnapshotBaseVectors.body.context
    policy.validators NativeIscAdmissionVectors.inputTree = some NativeSnapshotBaseVectors.checked :=
  NativeProposedIsc.fromComponents ⟨NativeInputSetBody.checkFromComponents
    NativeIscAdmissionVectors.bodyRead bodyHash NativeIscAdmissionVectors.inputValid,
    NativeSnapshotBaseVectors.expandedValid,expandedHash⟩

theorem baseComputed : NativeSnapshotBase.checkBase sha policy state =
    some NativeSnapshotBaseVectors.base := by
  apply NativeSnapshotBase.baseFromComponents
  exact ⟨rfl,rfl,rfl,rfl,rfl,rfl,
    NativeProposedIsc.listFromComponents proposedComputed rfl,rfl,by decide⟩

def snapshot : NativeSnapshotBase.Bound := ⟨failure,NativeSnapshotBaseVectors.base⟩
theorem snapshotComputed : NativeSnapshotBase.bindSnapshot sha policy state = some snapshot :=
  NativeSnapshotBase.snapshotFromComponents failureComputed baseComputed


theorem configContext : NativeConfigAdmission.configContext sha 1 policy.epoch =
    some NativeProposalAdmissionVectors.config.context := by
  have different : NativeConfigAdmission.configPreimage 1 policy.epoch ≠
      NativeSnapshotBaseVectors.preimage := by decide
  simpa only [NativeConfigAdmission.configContext,sha,if_neg different] using
    NativeMixedReplayVectors.configContext

theorem iscContext : NativeIscAdmission.iscContext sha policy.round =
    some NativeProposalAdmissionVectors.isc.context := by
  have different : NativeIscAdmission.iscPreimage policy.round ≠
      NativeSnapshotBaseVectors.preimage := by decide
  simpa only [NativeIscAdmission.iscContext,sha,if_neg different] using
    NativeMixedReplayVectors.iscContext

def configEntry : NativeCandidateAuthority.Entry :=
  ⟨NativeProposalAdmissionVectors.config,NativeCandidateAuthorityVectors.parents1⟩
def iscEntry : NativeCandidateAuthority.Entry :=
  ⟨NativeProposalAdmissionVectors.isc,NativeCandidateAuthorityVectors.parents2⟩
def checked : NativeCandidateAuthority.CheckedPolicy := ⟨snapshot,[configEntry,iscEntry]⟩

theorem configComputed : NativeCandidateAuthority.check sha policy state snapshot
    configEntry.original = some configEntry := by
  apply NativeCandidateAuthority.fromComponents (by decide) rfl rfl
  exact ⟨by decide,configContext⟩
theorem iscCandidateComputed : NativeCandidateAuthority.check sha policy state snapshot
    iscEntry.original = some iscEntry := by
  apply NativeCandidateAuthority.fromComponents (by decide) rfl rfl
  exact ⟨by decide,by decide,iscContext⟩
theorem allCandidatesComputed : NativeCandidateAuthority.checkAll sha policy state snapshot
    policy.candidates = some checked.entries := by
  change (NativeCandidateAuthority.check sha policy state snapshot configEntry.original >>=
    fun a => NativeCandidateAuthority.check sha policy state snapshot iscEntry.original >>=
    fun b => some [a,b]) = _
  rw [configComputed,iscCandidateComputed]; rfl
theorem wholePolicyComputed : NativeCandidateAuthority.bindPolicy sha policy state = some checked :=
  NativeCandidateAuthority.policyFromComponents snapshotComputed allCandidatesComputed

def startup : NativeReplayAdmission.WholeStartup := ⟨policy,state,checked⟩
theorem actualStartup : NativeReplayAdmission.prepareWhole sha policyRaw initial.core.state =
    some startup := NativeReplayAdmission.wholeStartupComponents NativeMixedPolicyVectors.parsed
      NativeIscAdmissionVectors.stateDecoded wholePolicyComputed

def selected : NativeSelectedVote.Checked :=
  ⟨policy,state,⟨checked,iscEntry⟩,NativeVoteCodecVectors.vote2⟩
theorem originalGuard : NativeSelectedVote.Checks policy state tail iscEntry
    (facts initial NativeWalVectors.entry2) NativeVoteCodecVectors.vote2 := by decide
theorem originalSelected : NativeSelectedVote.checkSelected policy state checked
    (facts initial NativeWalVectors.entry2) NativeVoteCodecVectors.vote2 = some iscEntry :=
  NativeSelectedVote.selectedFromComponents (by rfl)
    (NativeSelectedVote.voteFromComponents originalGuard)
theorem wholeOriginalVote : NativeSelectedVote.fromBytes sha policyRaw initial.core.state
    NativeWalVectors.entry2.command (facts initial NativeWalVectors.entry2) = some selected :=
  NativeSelectedVote.fromBytesComponents ⟨⟨_,NativeMixedPolicyVectors.parsed⟩,
    NativeIscAdmissionVectors.stateDecoded,NativeVoteCodecVectors.parsed2,
    NativeSelectedVote.admitFromComponents wholePolicyComputed originalSelected⟩
theorem actualAdmission : NativeReplayAdmission.fromBytes .whole sha policyRaw initial.core.state
    NativeWalVectors.entry2.command (facts initial NativeWalVectors.entry2) =
    some (selected,NativeVoteCodecVectors.vote2) :=
  NativeReplayAdmission.wholeFromComponents wholeOriginalVote

theorem policyHash : NativeWalBytes.policyId sha policyRaw = some NativeWalVectors.entry2.record := by
  have different : policyRaw ≠ NativeSnapshotBaseVectors.preimage := by decide
  simpa only [NativeWalBytes.policyId,sha,if_neg different] using NativeMixedReplayVectors.policyHash
theorem voteHash : voteId sha NativeReceiptVectors.frame2 = some NativeReceiptVectors.receipt2.voteId := by
  have different : votePreimage NativeReceiptVectors.frame2 ≠ NativeSnapshotBaseVectors.preimage := by decide
  simpa only [voteId,sha,if_neg different] using NativeMixedReplayVectors.voteHash

theorem entryChecked : VoteEntry .whole sha policyRaw none initial NativeWalVectors.entry2
    selected NativeVoteCodecVectors.vote2 NativeReceiptVectors.receipt2.voteId :=
  ⟨rfl,rfl,by decide,rfl,rfl,policyHash,actualAdmission,voteHash,NativeReceiptVectors.valid2,
    by simp [fresh,NativeMixedReplayVectors.initial,NativeCommandReplayVectors.initial],
    by simp [NativeCommandReplay.snapshotGuard]⟩
def first : Machine := added .whole none initial NativeWalVectors.entry2 selected
  NativeVoteCodecVectors.vote2 NativeReceiptVectors.receipt2.voteId

theorem voteStep : step .whole sha policyRaw none initial NativeWalVectors.entry2 = some first :=
  voteFromComponents entryChecked
theorem sameOriginalCache : first = NativeMixedReplayVectors.first := rfl

theorem commandHash : contentId sha commandDomain NativeWalVectors.command3 = some NativeTransitionVectors.commandId := by
  have different : contentPreimage commandDomain NativeWalVectors.command3 ≠ NativeSnapshotBaseVectors.preimage := by decide
  simpa only [contentId,sha,if_neg different] using NativeMixedReplayVectors.commandHash

theorem nextHash : contentId sha stateDomain NativeWalVectors.state3 = some NativeTransitionVectors.nextId := by
  have different : contentPreimage stateDomain NativeWalVectors.state3 ≠ NativeSnapshotBaseVectors.preimage := by decide
  simpa only [contentId,sha,if_neg different] using NativeMixedReplayVectors.nextHash

theorem effectsHash : contentId sha effectDomain NativeWalVectors.effects3 = some NativeTransitionVectors.effectsId := by
  have different : contentPreimage effectDomain NativeWalVectors.effects3 ≠ NativeSnapshotBaseVectors.preimage := by decide
  simpa only [contentId,sha,if_neg different] using NativeMixedReplayVectors.effectsHash

theorem recordHash : contentId sha walDomain NativeWalVectors.record3 = some NativeTransitionVectors.recordId := by
  have different : contentPreimage walDomain NativeWalVectors.record3 ≠ NativeSnapshotBaseVectors.preimage := by decide
  simpa only [contentId,sha,if_neg different] using NativeMixedReplayVectors.recordHash

open NativeTransitionVectors (s0 c0 n0 nativeOutput)
theorem nativeBuilt : Built sha s0 c0 n0 nativeOutput := by
  refine ⟨rfl,NativeTransitionVectors.originalStateBytes.symm,?_,?_,nextHash,
    NativeTransitionVectors.originalEffectsValid,NativeTransitionVectors.effectBytes.symm,
    effectsHash,NativeTransitionVectors.originalWalValid,NativeTransitionVectors.recordBytes.symm,recordHash⟩
  · rw [NativeTransitionVectors.originalPriorBytes]; exact priorHash
  · rw [NativeTransitionVectors.originalCommandBytes]; exact commandHash
theorem nativeExecuted : NativeTransition.fromBytes sha NativeStateCodecVectors.raw3
    NativeWalVectors.command3 = some nativeOutput :=
  bytesFromComponents sha _ _ s0 c0 nativeOutput NativeStateCodecVectors.parsed3 NativeStateCodecVectors.parsed1
    (executeFromComponents sha s0 c0 n0 nativeOutput NativeTransitionVectors.step0 nativeBuilt)
theorem freezeComputed : replayEntry sha first.core.state NativeWalVectors.entry3 = some nativeOutput :=
  replayFromComputed sha _ _ _ rfl nativeExecuted ⟨rfl,rfl,rfl⟩
def final : Machine := ⟨NativeCommandReplay.updated (some 0) none first.core NativeWalVectors.entry3 c0 nativeOutput,first.votes⟩
theorem freezeStep : step .whole sha policyRaw none first NativeWalVectors.entry3 = some final := by
  apply commandFromComponents rfl
  exact NativeCommandReplay.stepFromComponents sha _ _ _ _ _ _
    ⟨rfl,rfl,by decide,NativeStateCodecVectors.parsed1,by decide,freezeComputed,by decide,by decide⟩
theorem originalRun : run .whole sha policyRaw none initial
    [NativeWalVectors.entry2,NativeWalVectors.entry3] = some final := by
  simp only [run,voteStep,freezeStep,bind,Option.bind]
theorem originalRecovery : recover .whole sha policyRaw initial.core.state none
    [NativeWalVectors.entry2,NativeWalVectors.entry3] = some final :=
  recoveryFromComponents actualStartup NativeMixedReplayVectors.initialCore originalRun ⟨rfl,by simp⟩
theorem identicalPreviousResult : final = NativeMixedReplayVectors.final := rfl
theorem exactOriginalReceipt : NativeReceiptBytes.encode NativeMixedReplayVectors.stored.receipt =
    NativeReceiptVectors.nativeBytes2 := NativeReceiptVectors.exactBytes2
theorem originalPositions : final.core.sequence = 2 ∧ final.core.requests.length = 1 ∧
    final.votes = [NativeMixedReplayVectors.stored] := ⟨rfl,rfl,rfl⟩
theorem exactRetry : retryVote sha final NativeReceiptVectors.frame2 =
    some NativeMixedReplayVectors.stored := by
  apply retryFromCache NativeVoteCodecVectors.parsed2 voteHash
  · change (if key NativeVoteCodecVectors.vote2 == key NativeVoteCodecVectors.vote2 then _ else none) = _
    simp
    rfl
  · exact ⟨(decodedVoteSound NativeVoteCodecVectors.parsed2).2,rfl⟩
theorem actualCommandRetry : NativeCommandReplay.retry sha final.core NativeWalVectors.command3 =
    some {(NativeCommandReplay.cached NativeWalVectors.entry3 c0 nativeOutput).receipt with replay := true} := by
  apply NativeCommandReplay.retryFromCache sha final.core _ c0 NativeTransitionVectors.commandId _
    NativeStateCodecVectors.parsed1 commandHash
  · change (if c0.wire.request == c0.wire.request then _ else none) = _
    simp
  · rfl

theorem invalidationPreserved : final.core.invalidated = true ∧ final.core.tick = 11 := ⟨rfl,rfl⟩
theorem freshAfterFreezeRejected : step .whole sha policyRaw none final NativeWalVectors.entry2 = none :=
  NativeWholeReplay.invalidatedScanRejected rfl rfl
theorem missingVoteCannotStart : step .whole sha policyRaw none initial NativeWalVectors.entry3 = none :=
  wrongPositionRejected (by decide)
theorem repeatedPositionRejected : step .whole sha policyRaw none first NativeWalVectors.entry2 = none :=
  wrongPositionRejected (by decide)
theorem reorderedRunRejected : run .whole sha policyRaw none initial
    [NativeWalVectors.entry3,NativeWalVectors.entry2] = none := by
  simp only [run,missingVoteCannotStart,bind,Option.bind]
theorem substitutedPolicyRecordRejected : step .whole sha policyRaw none initial
    {NativeWalVectors.entry2 with record := []} = none := by
  apply wrongPolicyRejected rfl
  rw [policyHash]; decide
-- Duplicate-cache guard independently, without using the repeated position guard.
theorem duplicateFreshness : ¬ fresh first NativeVoteCodecVectors.vote2 := by
  simp [fresh,first,added,key]
theorem duplicateOriginalRejected : step .whole sha policyRaw none
    {initial with votes := first.votes} NativeWalVectors.entry2 = none := by
  apply NativeWholeReplay.duplicateScanRejected rfl
  intro b v h
  change NativeReplayAdmission.fromBytes .whole sha policyRaw initial.core.state
    NativeWalVectors.entry2.command (facts initial NativeWalVectors.entry2) = some (b,v) at h
  rw [actualAdmission] at h
  cases Option.some.inj h
  exact duplicateFreshness
-- An arbitrary new core cannot alter the original retry cache result.
theorem retryAfterArbitraryCore (core : NativeCommandReplay.Machine) :
    retryVote sha {final with core := core} NativeReceiptVectors.frame2 =
      some NativeMixedReplayVectors.stored := by
  exact (retryHistorical sha {final with core := core} final NativeReceiptVectors.frame2 rfl).trans exactRetry

theorem snapshotAtVote : NativeCommandReplay.snapshotGuard
    (some ⟨1,initial.core.state⟩) (atVote initial NativeWalVectors.entry2) := by decide
theorem emptyVoteBytesNotState : ¬ NativeCommandReplay.snapshotGuard
    (some ⟨1,initial.core.state⟩) NativeWalVectors.entry2 := by decide

theorem allOriginalCandidatesRetained : checked.entries.map NativeCandidateAuthority.Entry.original =
    policy.candidates := NativeCandidateAuthority.completeCandidateList wholePolicyComputed
theorem originalNonemptyInput : snapshot.base.inputTrees = [NativeIscAdmissionVectors.inputTree] ∧
    snapshot.base.inputs.map (fun x => x.body.source) = [NativeIscAdmissionVectors.inputTree] := ⟨rfl,rfl⟩
end DeltaReduce.NativeWholeReplayVectors
