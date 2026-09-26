import DeltaReduce.NativeCommandReplay
import DeltaReduce.NativeTransitionVectors

set_option maxRecDepth 10000

/-! Original arithmetic-free command components are reused. The sequence-one
single-command history is a separately mathematical case, not a relabeling of
the old native ISC(1)/freeze(2) trace. Fresh C++ three-command cases are separate
finite executions retained by check_native_command_replay.py. -/
namespace DeltaReduce.NativeCommandReplayVectors
open NativeReceiptBytes NativeStateBytes NativeTransition NativeCommandReplay
open NativeTransitionVectors

def initial : Machine := ⟨NativeStateCodecVectors.raw3,0,10,false,[],true⟩
def entry : NativeWalBytes.Entry := {NativeWalVectors.entry3 with sequence := 1}
def first : Machine := updated (some 10) none initial entry c0 nativeOutput

theorem loadedInitial : initialMachine (some 10) none NativeStateCodecVectors.raw3 = some initial := by
  simp only [initialMachine,NativeStateCodecVectors.parsed3,bind,Option.bind]
  rfl

theorem computed : replayEntry sha initial.state entry = some nativeOutput :=
  replayFromComputed sha _ _ _ rfl nativeBytesExecuted ⟨rfl,rfl,rfl⟩

theorem firstAdmitted : Admitted sha (some 10) none initial entry c0 nativeOutput :=
  ⟨rfl,rfl,by decide,NativeStateCodecVectors.parsed1,by decide,computed,by decide,by decide⟩

theorem firstStep : NativeCommandReplay.step sha (some 10) none initial entry = some first :=
  stepFromComponents sha _ _ _ _ _ _ firstAdmitted

theorem firstRun : run sha (some 10) none initial [entry] = some first := by
  simp only [run,firstStep,bind,Option.bind]

theorem completeMathematicalHistory : recover sha (some 10) none NativeStateCodecVectors.raw3 [entry] = some first := by
  simp only [recover,loadedInitial,firstRun,bind,Option.bind]
  rfl

theorem computedFromEmpty : History sha (some 10) none initial [entry] first := runSound firstRun

theorem originalStepAtTwo : NativeCommandReplay.step sha (some 10) none
    {initial with sequence := 1} NativeWalVectors.entry3 =
    some (updated (some 10) none {initial with sequence := 1} NativeWalVectors.entry3 c0 nativeOutput) :=
  stepFromComponents sha _ _ _ _ _ _
    ⟨rfl,rfl,by decide,NativeStateCodecVectors.parsed1,by decide,originalEntryRecomputed,by decide,by decide⟩

theorem originalSequenceTwoCannotStart : NativeCommandReplay.step sha (some 10) none initial NativeWalVectors.entry3 = none :=
  wrongPositionRejected sha _ _ _ _ (by decide)

theorem originalVoteNotSkipped : NativeCommandReplay.step sha (some 10) none initial NativeWalVectors.entry2 = none :=
  voteRejected sha _ _ _ _ (by decide)

theorem fullOldMixedTraceRejected : run sha (some 10) none initial [NativeWalVectors.entry2,NativeWalVectors.entry3] = none := by
  simp only [run,originalVoteNotSkipped,bind,Option.bind]

theorem actualReceiptFields : first.requests = [cached entry c0 nativeOutput] ∧ first.tick = 11 ∧
    first.invalidated = true ∧ first.sequence = 1 := ⟨rfl,rfl,rfl,rfl⟩

theorem historicalLookup : first.requests.find? (fun r => r.request == c0.wire.request) =
    some (cached entry c0 nativeOutput) := by
  change (if c0.wire.request == c0.wire.request then some (cached entry c0 nativeOutput) else none) = _
  simp

theorem retryOriginal : retry sha first NativeWalVectors.command3 =
    some {(cached entry c0 nativeOutput).receipt with replay := true} :=
  retryFromCache sha first _ c0 commandId (cached entry c0 nativeOutput)
    NativeStateCodecVectors.parsed1 hash1 historicalLookup rfl

def moved : Machine := {first with state := [], tick := 99, sequence := 9, invalidated := true}

theorem retryAfterMovement : retry sha moved NativeWalVectors.command3 = retry sha first NativeWalVectors.command3 :=
  retryHistorical sha moved first _ rfl

theorem originalRetrySequence : ({(cached entry c0 nativeOutput).receipt with replay := true}).sequence = 1 := rfl

theorem conflictRejects : retry sha
    {first with requests := [{cached entry c0 nativeOutput with commandId := []}]} NativeWalVectors.command3 = none := by
  apply retryConflict sha _ _ c0 commandId
    {cached entry c0 nativeOutput with commandId := []}
    NativeStateCodecVectors.parsed1 hash1
  · change (if c0.wire.request == c0.wire.request then _ else none) = _
    simp
  · decide

theorem laterClockRejects : NativeCommandReplay.step sha (some 10) none
    {initial with tick := 12} entry = none :=
  oldClockRejected sha _ _ _ _ c0 NativeStateCodecVectors.parsed1 (by decide)

theorem noPolicyClockGuard : clockGuard none {initial with tick := 12} c0 := by decide

theorem duplicateCannotAppend : NativeCommandReplay.step sha (some 10) none
    {initial with requests := [cached entry c0 nativeOutput]} entry = none :=
  duplicateRejected sha _ _ _ _ c0 NativeStateCodecVectors.parsed1 (by decide)

def matching : Snapshot := ⟨1,NativeWalVectors.state3⟩
def wrong : Snapshot := ⟨1,NativeStateCodecVectors.raw3⟩
def zero : Snapshot := ⟨0,NativeWalVectors.state3⟩

theorem snapshotSameAccepts : snapshotGuard (some matching) entry := by decide
theorem snapshotWrongRejects : ¬ snapshotGuard (some wrong) entry := by decide
theorem wrongSnapshotStep : NativeCommandReplay.step sha (some 10) (some wrong) initial entry = none :=
  wrongSnapshotRejected sha _ _ _ _ snapshotWrongRejects

theorem zeroStartsMatched : initialMatch (some zero) = true := rfl
theorem positiveStartsUnmatched : initialMatch (some matching) = false := rfl
theorem zeroDoesNotMatchCommand : mark (some zero) entry = false := rfl
theorem positiveMatchesCommand : mark (some matching) entry = true := rfl

theorem zeroSnapshotOnlyValidated : initialMachine (some 10) (some zero) NativeStateCodecVectors.raw3 = some initial := by
  simp only [initialMachine,NativeStateCodecVectors.parsed3,bind,Option.bind]
  change (if _ then _ else none) = _
  rw [if_pos (by decide)]
  change (decodeState NativeStateCodecVectors.raw2 >>= fun _ => some initial) = _
  rw [NativeStateCodecVectors.parsed2]
  rfl

theorem zeroSnapshotEmptyKeepsInitial : recover sha (some 10) (some zero) NativeStateCodecVectors.raw3 [] = some initial := by
  simp only [recover,zeroSnapshotOnlyValidated,run,bind,Option.bind]
  rfl

theorem stateStillInitial : initial.state = NativeStateCodecVectors.raw3 ∧ initial.state ≠ zero.state := ⟨rfl,by decide⟩

theorem counterNotWalSequence : NativeWalVectors.entry3.sequence = 2 ∧ nativeOutput.next.sequence = 1 := originalWalStateCounters

theorem emptyRequestsUnique : UniqueRequests initial := by simp [UniqueRequests,initial]
theorem recoveredRequestsUnique : UniqueRequests first := recoveryUnique completeMathematicalHistory

end DeltaReduce.NativeCommandReplayVectors
