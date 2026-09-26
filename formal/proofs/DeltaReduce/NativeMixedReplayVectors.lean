import DeltaReduce.NativeConfigReplay
import DeltaReduce.NativeMixedPolicyVectors
import DeltaReduce.NativeCommandReplayVectors

/-! Actual original ISC1/freeze2, without rewriting its two-candidate policy.
Ten finite SHA preimages and supplied initial snapshot remain explicit scope. -/
namespace DeltaReduce.NativeMixedReplayVectors
open NativeReceiptBytes NativeVoteBytes NativeStateBytes NativeTransition
open NativeConfigReplay
open NativeMixedPolicyVectors (sha policy policyRaw)
open NativeTransitionVectors (c0 s0 n0 nativeOutput priorId commandId nextId effectsId recordId)
set_option maxRecDepth 16384
set_option maxHeartbeats 100000

def graph : NativeProposalAdmission.Graph := {NativeProposalAdmissionVectors.graph with policy := policy}
def bound : NativeProposalAdmission.Bound := {NativeProposalAdmissionVectors.bound with graph := graph}
def selected : NativeReplayAdmission.Selected .proposals := (bound,NativeProposalAdmissionVectors.iscPrepared)
def initial : Machine := ⟨NativeCommandReplayVectors.initial,[]⟩

theorem hashContent {sha domain raw digest id}
    (hash : sha (contentPreimage domain raw) = digest) (width : digest.length = 32)
    (text : ascii "sha256:" ++ hexBytes digest = id) : contentId sha domain raw = some id := by
  simp only [contentId,hash,width,ite_true,text]
theorem hashVote {sha raw digest id}
    (hash : sha (votePreimage raw) = digest) (width : digest.length = 32)
    (text : ascii "sha256:" ++ hexBytes digest = id) : voteId sha raw = some id := by
  simp only [voteId,hash,width,ite_true,text]
theorem hashPolicy {sha raw digest id}
    (hash : sha raw = digest) (width : digest.length = 32)
    (text : hexBytes digest = id) : NativeWalBytes.policyId sha raw = some id := by
  simp only [NativeWalBytes.policyId,hash,width,ite_true,text]
theorem hashConfig {sha height epoch digest id}
    (hash : sha (NativeConfigAdmission.configPreimage height epoch) = digest)
    (width : digest.length = 32) (text : NativeConfigAdmission.ascii "sha256:" ++ hexBytes digest = id) :
    NativeConfigAdmission.configContext sha height epoch = some id := by
  simp only [NativeConfigAdmission.configContext,hash,width,ite_true,text]
theorem hashIsc {sha round digest id}
    (hash : sha (NativeIscAdmission.iscPreimage round) = digest)
    (width : digest.length = 32) (text : NativeConfigAdmission.ascii "sha256:" ++ hexBytes digest = id) :
    NativeIscAdmission.iscContext sha round = some id := by
  simp only [NativeIscAdmission.iscContext,hash,width,ite_true,text]

theorem priorHash : contentId sha stateDomain NativeStateCodecVectors.raw3 = some priorId := hashContent NativeMixedPolicyVectors.hash5 rfl rfl

theorem commandHash : contentId sha commandDomain NativeWalVectors.command3 = some commandId := hashContent NativeMixedPolicyVectors.hash6 rfl rfl

theorem nextHash : contentId sha stateDomain NativeWalVectors.state3 = some nextId := hashContent NativeMixedPolicyVectors.hash7 rfl rfl

theorem effectsHash : contentId sha effectDomain NativeWalVectors.effects3 = some effectsId := hashContent NativeMixedPolicyVectors.hash8 rfl rfl

theorem recordHash : contentId sha walDomain NativeWalVectors.record3 = some recordId := hashContent NativeMixedPolicyVectors.hash9 rfl rfl

theorem policyHash : NativeWalBytes.policyId sha policyRaw = some NativeWalVectors.entry2.record := hashPolicy NativeMixedPolicyVectors.hash0 rfl rfl

theorem voteHash : voteId sha NativeReceiptVectors.frame2 = some NativeReceiptVectors.receipt2.voteId := hashVote NativeMixedPolicyVectors.hash1 rfl rfl

theorem configContext : NativeConfigAdmission.configContext sha 1 policy.epoch =
    some NativeProposalAdmissionVectors.config.context := hashConfig NativeMixedPolicyVectors.hash2 rfl rfl

theorem iscContext : NativeIscAdmission.iscContext sha policy.round =
    some NativeProposalAdmissionVectors.isc.context := hashIsc NativeMixedPolicyVectors.hash3 rfl rfl

theorem inputHash : NativeInputSetBody.bodyId sha NativeIscAdmissionVectors.inputBody =
    some NativeProposalAdmissionVectors.isc.body := by
  unfold NativeInputSetBody.bodyId
  exact (congrArg (contentId sha NativeInputSetBody.bodyDomain) NativeIscAdmissionVectors.inputEncoded).trans
    (hashContent NativeMixedPolicyVectors.hash4 rfl rfl)
theorem inputChecked : NativeInputSetBody.check sha
    (NativeIscAdmission.expected policy graph.state graph.schema graph.arithmetic)
    NativeIscAdmissionVectors.inputTree = some NativeIscAdmissionVectors.checked :=
  NativeInputSetBody.checkFromComponents NativeIscAdmissionVectors.bodyRead inputHash NativeIscAdmissionVectors.inputValid

theorem graphSource : NativeProposalAdmission.GraphSource sha policy graph.state graph := by
  refine ⟨rfl,rfl,rfl,?_,by decide,rfl,rfl,rfl,rfl,rfl,rfl,rfl,?_,?_⟩
  · change contentId sha stateDomain (encodeState NativeIscAdmissionVectors.wire) = _
    rw [NativeIscAdmissionVectors.stateEncoded]; exact priorHash
  · change NativeInputSetBody.checkAll sha _ [NativeIscAdmissionVectors.inputTree] = some [NativeIscAdmissionVectors.checked]
    simp only [NativeInputSetBody.checkAll,inputChecked,bind,Option.bind]
  · exact NativeProposalAdmissionVectors.completeGraphChecks

theorem configChecked : NativeProposalAdmission.checkCandidate sha graph
    NativeProposalAdmissionVectors.config = some NativeProposalAdmissionVectors.configPrepared :=
  NativeProposalAdmission.candidateFromComponents ⟨rfl,rfl,configContext,by decide⟩
theorem iscChecked : NativeProposalAdmission.checkCandidate sha graph
    NativeProposalAdmissionVectors.isc = some NativeProposalAdmissionVectors.iscPrepared :=
  NativeProposalAdmission.candidateFromComponents ⟨rfl,rfl,iscContext,by decide⟩
theorem candidatesChecked : NativeProposalAdmission.checkCandidates sha graph policy.candidates = some bound.candidates := by
  change (NativeProposalAdmission.checkCandidate sha graph NativeProposalAdmissionVectors.config >>= fun a =>
    (NativeProposalAdmission.checkCandidate sha graph NativeProposalAdmissionVectors.isc >>= fun b => some [a,b])) = _
  rw [configChecked,iscChecked]; rfl
theorem policyPrepared : NativeProposalAdmission.prepare sha policyRaw initial.core.state = some bound :=
  NativeProposalAdmission.prepareFromComponents NativeMixedPolicyVectors.parsed
    NativeIscAdmissionVectors.stateDecoded
    (NativeProposalAdmission.bindFromComponents graphSource candidatesChecked)
theorem initialCore : NativeCommandReplay.initialMachine (some 10) none initial.core.state = some initial.core :=
  NativeCommandReplayVectors.loadedInitial
theorem selectedVote : NativeProposalAdmission.select bound (facts initial NativeWalVectors.entry2)
    NativeVoteCodecVectors.vote2 = some NativeProposalAdmissionVectors.iscPrepared := by rfl
theorem admittedVote : NativeReplayAdmission.fromBytes .proposals sha policyRaw initial.core.state
    NativeWalVectors.entry2.command (facts initial NativeWalVectors.entry2) =
    some (selected,NativeVoteCodecVectors.vote2) :=
  NativeReplayAdmission.proposalFromComponents policyPrepared NativeVoteCodecVectors.parsed2 selectedVote
theorem entryChecked : VoteEntry .proposals sha policyRaw none initial NativeWalVectors.entry2
    selected NativeVoteCodecVectors.vote2 NativeReceiptVectors.receipt2.voteId :=
  ⟨rfl,rfl,by decide,rfl,rfl,policyHash,admittedVote,voteHash,NativeReceiptVectors.valid2,
    by simp [fresh,initial],by simp [NativeCommandReplay.snapshotGuard]⟩
def first : Machine := added .proposals none initial NativeWalVectors.entry2 selected
  NativeVoteCodecVectors.vote2 NativeReceiptVectors.receipt2.voteId
def stored : Stored := ⟨NativeVoteCodecVectors.vote2,NativeReceiptVectors.receipt2,
  NativeProposalAdmissionVectors.isc.parents⟩
theorem voteStep : NativeConfigReplay.step .proposals sha policyRaw none initial NativeWalVectors.entry2 = some first :=
  voteFromComponents entryChecked
theorem originalReceipt : NativeReceiptBytes.encode stored.receipt = NativeReceiptVectors.nativeBytes2 :=
  NativeReceiptVectors.exactBytes2
theorem exactVoteCache : first.votes = [stored] ∧ first.core.sequence = 1 := ⟨rfl,rfl⟩

theorem nativeBuilt : Built sha s0 c0 n0 nativeOutput := by
  refine ⟨rfl,NativeTransitionVectors.originalStateBytes.symm,?_,?_,nextHash,
    NativeTransitionVectors.originalEffectsValid,NativeTransitionVectors.effectBytes.symm,
    effectsHash,NativeTransitionVectors.originalWalValid,NativeTransitionVectors.recordBytes.symm,recordHash⟩
  · rw [NativeTransitionVectors.originalPriorBytes]; exact priorHash
  · rw [NativeTransitionVectors.originalCommandBytes]; exact commandHash
theorem nativeExecuted : NativeTransition.fromBytes sha NativeStateCodecVectors.raw3 NativeWalVectors.command3 = some nativeOutput :=
  bytesFromComponents sha _ _ s0 c0 nativeOutput NativeStateCodecVectors.parsed3 NativeStateCodecVectors.parsed1
    (executeFromComponents sha s0 c0 n0 nativeOutput NativeTransitionVectors.step0 nativeBuilt)
theorem freezeComputed : replayEntry sha first.core.state NativeWalVectors.entry3 = some nativeOutput :=
  replayFromComputed sha _ _ _ rfl nativeExecuted ⟨rfl,rfl,rfl⟩
def final : Machine := ⟨NativeCommandReplay.updated (some 0) none first.core NativeWalVectors.entry3 c0 nativeOutput,first.votes⟩
theorem freezeStep : NativeConfigReplay.step .proposals sha policyRaw none first NativeWalVectors.entry3 = some final := by
  apply commandFromComponents rfl
  exact NativeCommandReplay.stepFromComponents sha _ _ _ _ _ _
    ⟨rfl,rfl,by decide,NativeStateCodecVectors.parsed1,by decide,freezeComputed,by decide,by decide⟩
theorem originalRun : run .proposals sha policyRaw none initial [NativeWalVectors.entry2,NativeWalVectors.entry3] = some final := by
  simp only [run,voteStep,freezeStep,bind,Option.bind]
theorem originalRecovery : recover .proposals sha policyRaw initial.core.state none
    [NativeWalVectors.entry2,NativeWalVectors.entry3] = some final :=
  recoveryFromComponents policyPrepared initialCore originalRun ⟨rfl,by simp⟩
theorem history : History .proposals sha policyRaw none initial [NativeWalVectors.entry2,NativeWalVectors.entry3] final := runSound originalRun
theorem originalCounters : final.core.sequence = 2 ∧ final.core.requests.length = 1 ∧ final.votes = [stored] := ⟨rfl,rfl,rfl⟩
theorem commandReceiptSequence : (NativeCommandReplay.cached NativeWalVectors.entry3 c0 nativeOutput).receipt.sequence = 2 := rfl
theorem actualVoteRetry : retryVote sha final NativeReceiptVectors.frame2 = some stored := by
  apply retryFromCache NativeVoteCodecVectors.parsed2 voteHash
  · change (if key NativeVoteCodecVectors.vote2 == key NativeVoteCodecVectors.vote2 then some stored else none) = _
    simp
  · exact ⟨(decodedVoteSound NativeVoteCodecVectors.parsed2).2,rfl⟩
theorem actualCommandRetry : NativeCommandReplay.retry sha final.core NativeWalVectors.command3 =
    some {(NativeCommandReplay.cached NativeWalVectors.entry3 c0 nativeOutput).receipt with replay := true} := by
  apply NativeCommandReplay.retryFromCache sha final.core _ c0 commandId _ NativeStateCodecVectors.parsed1 commandHash
  · change (if c0.wire.request == c0.wire.request then _ else none) = _
    simp
  · rfl
theorem invalidatedAfterFreeze : final.core.invalidated = true ∧ final.core.tick = 11 := ⟨rfl,rfl⟩
theorem freshAfterFreezeRejected : NativeProposalAdmission.select bound (facts final NativeWalVectors.entry2)
    NativeVoteCodecVectors.vote2 = none := by rfl
theorem noRenumbering : NativeWalVectors.entry2.sequence = 1 ∧ NativeWalVectors.entry3.sequence = 2 := ⟨rfl,rfl⟩
theorem missingVoteCannotStart : NativeConfigReplay.step .proposals sha policyRaw none initial NativeWalVectors.entry3 = none :=
  wrongPositionRejected (by decide)
theorem repeatedVoteCannotAppend : NativeConfigReplay.step .proposals sha policyRaw none first NativeWalVectors.entry2 = none :=
  wrongPositionRejected (by decide)
theorem reorderedRunRejects : run .proposals sha policyRaw none initial [NativeWalVectors.entry3,NativeWalVectors.entry2] = none := by
  simp only [run,missingVoteCannotStart,bind,Option.bind]
theorem substitutedPolicyRecordRejects : NativeConfigReplay.step .proposals sha policyRaw none initial
    {NativeWalVectors.entry2 with record := []} = none := by
  apply wrongPolicyRejected rfl
  rw [policyHash]; decide
end DeltaReduce.NativeMixedReplayVectors
