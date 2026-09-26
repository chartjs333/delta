import DeltaReduce.NativeWalScan
import DeltaReduce.NativeWalVectors

/-! Existing native byte samples plus separately synthetic scanner counterchecks.
These are not new native executions or authenticated recovery observations. -/
set_option maxRecDepth 32768
set_option maxHeartbeats 1000000
namespace DeltaReduce.NativeWalScanVectors
open NativeReceiptBytes NativeWalBytes NativeWalScan

def sha (b : Bytes) : Bytes :=
  if b = NativeWalVectors.rawPrefix3 then NativeWalVectors.digest3 else NativeWalVectors.sha2 b
def stream : Bytes := NativeWalVectors.raw2 ++ NativeWalVectors.raw3
def emptyResult : Result := ⟨[],[],false⟩
def secondResult : Result := ⟨[⟨NativeWalVectors.entry3,NativeWalVectors.raw3⟩],[],false⟩
def fullResult : Result :=
  ⟨[⟨NativeWalVectors.entry2,NativeWalVectors.raw2⟩,
    ⟨NativeWalVectors.entry3,NativeWalVectors.raw3⟩],[],false⟩

theorem firstHead : scanHead sha stream = .frame NativeWalVectors.entry2 823 NativeWalVectors.raw3 := by decide
theorem secondHead : scanHead sha NativeWalVectors.raw3 = .frame NativeWalVectors.entry3 2723 [] := by decide
theorem firstTake : stream.take 823 = NativeWalVectors.raw2 := by rfl
theorem secondTake : NativeWalVectors.raw3.take 2723 = NativeWalVectors.raw3 := by rfl

theorem secondTrace : Trace sha NativeWalVectors.raw3 secondResult := by
  have h := Trace.step NativeWalVectors.raw3 [] NativeWalVectors.entry3 2723 emptyResult secondHead Trace.done
  rw [secondTake] at h
  exact h

theorem fullTrace : Trace sha stream fullResult := by
  have h := Trace.step stream NativeWalVectors.raw3 NativeWalVectors.entry2 823 secondResult firstHead secondTrace
  rw [firstTake] at h
  exact h

theorem scannedNativeStream : scan sha stream = some fullResult :=
  (scanExact sha stream fullResult).mpr fullTrace

theorem checkedNativeStream : check sha stream = some fullResult :=
  checkedFromScan sha stream fullResult scannedNativeStream (by decide)

theorem nativeConsumedAllBytes : consumed fullResult = 3546 ∧ fullResult.tail = [] ∧ fullResult.torn = false := by decide

theorem originalAllEntrySequences : (entries fullResult).map Entry.sequence = [1,2] := by decide
theorem nativeOneVoteOneCommand : (entries fullResult).map Entry.kind = [2,1] := by decide

def partialNative : Bytes := NativeWalVectors.raw1.take 411
def partialResult : Result := ⟨[],partialNative,true⟩
theorem actualPartialHead : scanHead NativeWalVectors.sha1 partialNative = .torn := by decide
theorem actualPartialScan : scan NativeWalVectors.sha1 partialNative = some partialResult :=
  (scanExact NativeWalVectors.sha1 partialNative partialResult).mpr
    (Trace.torn partialNative actualPartialHead)
theorem actualPartialRetained : consumed partialResult = 0 ∧ partialResult.tail = partialNative ∧ partialResult.torn = true := by decide

/- Small branch checks use the deliberately synthetic constant-digest adapter.
No cryptographic collision or native admission claim follows from these bytes. -/
def vote : Entry := ⟨1,2,[1],[],[],[]⟩
def command : Entry := ⟨2,1,[1],[2],[3],[4]⟩
def vb : Bytes := NativeWalBytes.encode NativeWalVectors.tinySHA vote
def cb : Bytes := NativeWalBytes.encode NativeWalVectors.tinySHA command
def vr : Result := ⟨[⟨vote,vb⟩],[],false⟩
def both : Result := ⟨[⟨vote,vb⟩,⟨command,cb⟩],[],false⟩

theorem emptyComplete : scan NativeWalVectors.tinySHA [] = some emptyResult := by decide
theorem singleComplete : check NativeWalVectors.tinySHA vb = some vr := by decide
theorem twoComplete : check NativeWalVectors.tinySHA (vb++cb) = some both := by decide
theorem shortTailPreserved : check NativeWalVectors.tinySHA (vb++[99]) = some ⟨[⟨vote,vb⟩],[99],true⟩ := by decide
theorem incompleteHeaderPreserved : check NativeWalVectors.tinySHA (vb++[68,82,87,49]) = some ⟨[⟨vote,vb⟩],[68,82,87,49],true⟩ := by decide
theorem incompleteBodyPreserved : check NativeWalVectors.tinySHA (vb++NativeWalBytes.header++be 4 72) = some ⟨[⟨vote,vb⟩],NativeWalBytes.header++be 4 72,true⟩ := by decide
theorem corruptSecondFailsWholeScan : scan NativeWalVectors.tinySHA (vb++List.replicate 12 0) = none := by decide
theorem corruptSecondFailsCheck : check NativeWalVectors.tinySHA (vb++List.replicate 12 0) = none := by decide
theorem corruptedCompleteBodyFails : check NativeWalVectors.tinySHA (vb++NativeWalBytes.header++be 4 72++List.replicate 60 0) = none := by decide
theorem reorderedStructuralScanRetainsOrder : scan NativeWalVectors.tinySHA (cb++vb) = some ⟨[⟨command,cb⟩,⟨vote,vb⟩],[],false⟩ := by decide
theorem reorderedSequenceCheckRejects : check NativeWalVectors.tinySHA (cb++vb) = none := by decide
theorem duplicateSequenceRejects : check NativeWalVectors.tinySHA (vb++vb) = none := by decide
theorem omittedFirstSequenceRejects : check NativeWalVectors.tinySHA cb = none := by decide
theorem gapSequenceRejects : check NativeWalVectors.tinySHA (vb++NativeWalBytes.encode NativeWalVectors.tinySHA {command with sequence := 3}) = none := by decide
theorem zeroSequenceRejects : check NativeWalVectors.tinySHA (NativeWalBytes.encode NativeWalVectors.tinySHA {vote with sequence := 0}) = none := by decide
theorem exactSyntheticPrefix : (vb++[99]).take (consumed ⟨[⟨vote,vb⟩],[99],true⟩) = vb := by decide
theorem exactSyntheticSuffix : (vb++[99]).drop (consumed ⟨[⟨vote,vb⟩],[99],true⟩) = [99] := by decide
theorem noPrefixResultOnCorruption : ¬ ∃ r, scan NativeWalVectors.tinySHA (vb++List.replicate 12 0) = some r := by
  rw [corruptSecondFailsWholeScan]; simp

end DeltaReduce.NativeWalScanVectors
