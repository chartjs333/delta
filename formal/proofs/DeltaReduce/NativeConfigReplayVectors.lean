import DeltaReduce.NativeConfigReplay
import DeltaReduce.NativeConfigAdmissionVectors
import DeltaReduce.NativeCommandReplayVectors

set_option maxRecDepth 10000
namespace DeltaReduce.NativeConfigReplayVectors
open NativeReceiptBytes NativeVoteBytes NativeStateBytes NativeConfigReplay

-- Four finite actual hash samples, not general SHA or exporter authentication.
def sha (raw : Bytes) : Bytes :=
  if raw = NativeConfigAdmissionVectors.policyRaw then [80, 9, 113, 225, 36, 212, 202, 165, 164, 83, 6, 246, 56, 131, 238, 78, 70, 246, 51, 93, 46, 31, 89, 139, 86, 234, 144, 231, 255, 39, 145, 106]
  else if raw = votePreimage NativeReceiptVectors.frame1 then
    [92,85,47,180,84,17,56,73,225,110,221,170,218,123,202,75,58,167,252,122,210,146,238,62,161,48,174,87,8,141,142,34]
  else NativeConfigAdmissionVectors.sha raw

theorem snapshotHash : contentId sha stateDomain
    (encodeState NativeConfigAdmissionVectors.state.wire) =
    some NativeConfigAdmissionVectors.bound.snapshotId := by
  change contentId sha stateDomain (encodeState NativeConfigAdmissionVectors.wire) = some (ascii "sha256:bf5e786a100c1a2a658275c1a8019197154941cd9ba833842163a4f85a595d95")
  rw [NativeConfigAdmissionVectors.stateEncoded]
  have old := NativeConfigAdmissionVectors.snapshotHash
  change contentId NativeConfigAdmissionVectors.sha stateDomain (encodeState NativeConfigAdmissionVectors.wire) = _ at old
  rw [NativeConfigAdmissionVectors.stateEncoded] at old
  have p : contentPreimage stateDomain NativeConfigAdmissionVectors.stateRaw ≠ NativeConfigAdmissionVectors.policyRaw := by decide
  have v : contentPreimage stateDomain NativeConfigAdmissionVectors.stateRaw ≠ votePreimage NativeReceiptVectors.frame1 := by decide
  simpa only [contentId,sha,p,v,if_false] using old

theorem contextHash : NativeConfigAdmission.configContext sha 1 NativeConfigAdmissionVectors.policy.epoch =
    some NativeConfigAdmissionVectors.bound.context := by
  change NativeConfigAdmission.configContext sha 1 NativeConfigAdmissionVectors.policy.epoch = some NativeConfigAdmissionVectors.candidate.context
  have p : NativeConfigAdmission.configPreimage 1 NativeConfigAdmissionVectors.policy.epoch ≠ NativeConfigAdmissionVectors.policyRaw := by decide
  have v : NativeConfigAdmission.configPreimage 1 NativeConfigAdmissionVectors.policy.epoch ≠ votePreimage NativeReceiptVectors.frame1 := by decide
  simpa only [NativeConfigAdmission.configContext,sha,p,v,if_false] using NativeConfigAdmissionVectors.contextHash

theorem sourceBinding : NativeConfigAdmission.bindConfig sha NativeConfigAdmissionVectors.policy
    NativeConfigAdmissionVectors.state = some NativeConfigAdmissionVectors.bound := by
  apply NativeConfigAdmission.bindConfigComplete
  exact ⟨rfl,rfl,rfl,by rfl,snapshotHash,by decide,by rfl,by rfl,by rfl,by rfl,by rfl,by rfl,contextHash,NativeConfigAdmissionVectors.boundChecks⟩

theorem sourcePrepared : NativeConfigAdmission.prepare sha NativeConfigAdmissionVectors.policyRaw
    NativeConfigAdmissionVectors.stateRaw = some NativeConfigAdmissionVectors.bound := by
  simp only [NativeConfigAdmission.prepare,NativeConfigAdmissionVectors.policyDecoded,
    NativeConfigAdmissionVectors.stateDecoded,bind,Option.bind,sourceBinding]

def initial : Machine := ⟨⟨NativeConfigAdmissionVectors.stateRaw,0,10,false,[],false⟩,[]⟩
def snap : NativeCommandReplay.Snapshot := ⟨1,NativeConfigAdmissionVectors.stateRaw⟩
def entry : NativeWalBytes.Entry := ⟨1,2,NativeReceiptVectors.frame1,[],[],hexBytes [80, 9, 113, 225, 36, 212, 202, 165, 164, 83, 6, 246, 56, 131, 238, 78, 70, 246, 51, 93, 46, 31, 89, 139, 86, 234, 144, 231, 255, 39, 145, 106]⟩
def stored : Stored := ⟨NativeVoteCodecVectors.vote1,NativeReceiptVectors.receipt1,
  NativeConfigAdmissionVectors.bound.candidate.parents⟩

theorem voteHash : voteId sha NativeReceiptVectors.frame1 = some NativeReceiptVectors.receipt1.voteId := by
  have different : votePreimage NativeReceiptVectors.frame1 ≠ NativeConfigAdmissionVectors.policyRaw := by decide
  simp only [voteId,sha,if_neg different]; rfl

theorem policyHash : NativeWalBytes.policyId sha NativeConfigAdmissionVectors.policyRaw = some entry.record := by
  simp only [NativeWalBytes.policyId,sha]; rfl

theorem recoveryFacts : NativeConfigAdmission.VoteChecks NativeConfigAdmissionVectors.bound
    (facts initial entry) NativeVoteCodecVectors.vote1 := by
  rcases NativeConfigAdmissionVectors.originalChecks with ⟨a,b,c,d,e,f,g,h,i,j,k,_,m,n,o,p,q⟩
  exact ⟨a,b,c,d,e,f,g,h,i,j,k,Or.inl rfl,m,n,o,p,q⟩

theorem actualAdmission : NativeConfigAdmission.fromBytes sha NativeConfigAdmissionVectors.policyRaw
    initial.core.state entry.command (facts initial entry) =
    some (NativeConfigAdmissionVectors.bound,NativeVoteCodecVectors.vote1) :=
  NativeConfigAdmission.fromComponents sourcePrepared NativeVoteCodecVectors.parsed1 recoveryFacts

theorem entryChecked : VoteEntry sha NativeConfigAdmissionVectors.policyRaw (some snap) initial
    entry NativeConfigAdmissionVectors.bound NativeVoteCodecVectors.vote1 NativeReceiptVectors.receipt1.voteId := by
  exact ⟨rfl,rfl,by decide,rfl,rfl,policyHash,actualAdmission,voteHash,NativeReceiptVectors.valid1,by simp [fresh,initial],by simp [NativeCommandReplay.snapshotGuard,atVote,snap,entry,initial]⟩

def first : Machine := added (some snap) initial entry NativeConfigAdmissionVectors.bound
  NativeVoteCodecVectors.vote1 NativeReceiptVectors.receipt1.voteId

theorem actualVoteStep : NativeConfigReplay.step sha NativeConfigAdmissionVectors.policyRaw
    (some snap) initial entry = some first := voteFromComponents entryChecked

theorem firstCache : first.votes = [stored] ∧ first.core.sequence = 1 ∧
    first.core.requests = [] ∧ first.core.state = initial.core.state ∧ first.core.matched = true :=
  ⟨rfl,rfl,rfl,rfl,rfl⟩

theorem originalReceipt : NativeReceiptBytes.encode stored.receipt = NativeReceiptVectors.nativeBytes1 :=
  NativeReceiptVectors.exactBytes1

theorem voteSnapshotUsesCurrent : NativeCommandReplay.snapshotGuard (some snap) (atVote initial entry) := by decide

theorem emptyVoteStateIsNotSnapshot : ¬ NativeCommandReplay.snapshotGuard (some snap) entry := by decide

theorem originalLookup : first.votes.find? (fun r => key r.vote == key NativeVoteCodecVectors.vote1) = some stored := by
  change (if key NativeVoteCodecVectors.vote1 == key NativeVoteCodecVectors.vote1 then some stored else none) = _
  simp

theorem actualRetry : retryVote sha first NativeReceiptVectors.frame1 = some stored :=
  retryFromCache NativeVoteCodecVectors.parsed1 voteHash originalLookup
    ⟨(decodedVoteSound NativeVoteCodecVectors.parsed1).2,rfl⟩

def advanced : Machine := {first with core := {first.core with tick := 99,sequence := 8,invalidated := true,state := []}}

theorem historicalRetry : retryVote sha advanced NativeReceiptVectors.frame1 = some stored := by
  rw [retryHistorical sha advanced first _ rfl]; exact actualRetry

theorem duplicateContext : ¬ fresh first NativeVoteCodecVectors.vote1 := by
  simp [fresh,first,added,key]

theorem oldISCNotRenumbered : NativeWalVectors.entry2.sequence = 1 ∧ NativeWalVectors.entry3.sequence = 2 := ⟨rfl,rfl⟩

theorem oldISCRejected : (NativeConfigAdmission.checkVote NativeConfigAdmissionVectors.bound
    NativeConfigAdmissionVectors.facts NativeVoteCodecVectors.vote2).isNone = true := by decide

-- Composes any actually recomputed next command; no supplied recovered state.
theorem mixedComposition {e core}
    (command : NativeCommandReplay.step sha (some 0) (some snap) first.core e = some core)
    (kind : e.kind = 1) :
    run sha NativeConfigAdmissionVectors.policyRaw (some snap) initial [entry,e] = some ⟨core,first.votes⟩ := by
  simp only [run,actualVoteStep,commandFromComponents kind command,bind,Option.bind]

end DeltaReduce.NativeConfigReplayVectors
