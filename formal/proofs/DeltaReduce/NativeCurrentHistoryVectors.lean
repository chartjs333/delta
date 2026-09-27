import DeltaReduce.NativeCurrentHistory
import DeltaReduce.NativeApplyResultVectors
import DeltaReduce.NativeCurrentPointerVectors

/-! Existing synthetic value and WAL components, never new finalized history.
Original golden candidate placeholder hashes deliberately fail value binding. -/
namespace DeltaReduce.NativeCurrentHistoryVectors
open NativeBinding
open NativeCurrentValues

theorem zero : readNumber (asciiBytes "0") = some 0 := by decide
theorem negative : readNumber (asciiBytes "-101") = some (-101) := by decide
theorem minimum : readNumber (asciiBytes "-9223372036854775808") = some minInput := by decide
theorem maximum : readNumber (asciiBytes "9223372036854775807") = some maxInput := by decide
theorem lowOverflow : readNumber (asciiBytes "-9223372036854775809") = none := by decide
theorem highOverflow : readNumber (asciiBytes "9223372036854775808") = none := by decide
theorem plusSign : readNumber (asciiBytes "+1") = none := by decide
theorem positiveAlias : readNumber (asciiBytes "01") = none := by decide
theorem negativeZero : readNumber (asciiBytes "-00") = none :=
  alternateRejected NativeApplyResultVectors.oldNegativeZeroStillAccepted
    NativeApplyResultVectors.negativeZeroNotComputed
theorem negativeAlias : readNumber (asciiBytes "-01") = none :=
  alternateRejected NativeApplyResultVectors.oldNegativeAliasStillAccepted
    NativeApplyResultVectors.negativeAliasNotComputed
theorem emptyNumber : readNumber [] = none := by decide
theorem whitespace : readNumber (asciiBytes " 1") = none := by decide
theorem listRetainsOrder : readValues [asciiBytes "19",asciiBytes "-19"] = some [19,-19] := by decide
theorem badMember : readValues [asciiBytes "19",asciiBytes "-00"] = none := by decide
theorem emptyVectorParsing : readValues [] = some [] := rfl

def existingImage : Image :=
  ⟨NativeApplyResultVectors.candidate,[19,-19],[2,-2],
    NativeApplyResultVectors.hash0,NativeApplyResultVectors.hash1⟩

theorem existingComputedValues : load NativeApplyResultVectors.sha NativeApplyResultVectors.candidate =
    some existingImage := by decide
theorem originalPlaceholderHashRejected :
    load NativeApplyResultVectors.sha NativeApplyCertificateVectors.candidate = none := by decide
theorem changedCoordinate : load NativeApplyResultVectors.sha
    {NativeApplyResultVectors.candidate with modelValues := [asciiBytes "19",asciiBytes "-18"]} = none := by decide
theorem removedCoordinate : load NativeApplyResultVectors.sha
    {NativeApplyResultVectors.candidate with modelValues := [asciiBytes "19"]} = none := by decide
theorem reorderedCoordinates : load NativeApplyResultVectors.sha
    {NativeApplyResultVectors.candidate with modelValues := [asciiBytes "-19",asciiBytes "19"]} = none := by decide
theorem optimizerSubstitution : load NativeApplyResultVectors.sha
    {NativeApplyResultVectors.candidate with optimizerValues := [asciiBytes "19",asciiBytes "-19"]} = none := by decide
theorem absentDigest : load (fun _ => []) NativeApplyResultVectors.candidate = none := by decide
theorem emptyModel : load NativeApplyResultVectors.sha
    {NativeApplyResultVectors.candidate with modelValues := [],optimizerValues := []} = none := by decide

def emptyInput : NativeCurrentHistory.Input := ⟨[],[]⟩
theorem invalidPolicy {sha before record} :
    NativeCurrentHistory.checkRow sha before record emptyInput = none := by
  have emptyPolicy : NativePolicyBytes.decodePolicy [] = none := by decide
  simp [NativeCurrentHistory.checkRow,emptyInput,emptyPolicy]

theorem missingAllEvidence {sha before record rest} :
    NativeCurrentHistory.loadRows sha before (record::rest) [] = none := rfl
theorem extraEvidence {sha before} :
    NativeCurrentHistory.loadRows sha before [] [emptyInput] = none := rfl
theorem unknownCurrent {sha initial inputs} :
    NativeCurrentHistory.current sha initial .unknown inputs = none := rfl
theorem knownEmptyNoCurrent : NativeCurrentHistory.current NativeCurrentPointerVectors.sha
    NativeCurrentPointerVectors.initial (.bytes []) [] = none := by decide
theorem tornOnlyNoCurrent : NativeCurrentHistory.current NativeCurrentPointerVectors.sha
    NativeCurrentPointerVectors.initial (.bytes (asciiBytes "truncated")) [] = none := by decide
set_option maxRecDepth 2048 in
theorem unprovedWalNoCurrent : NativeCurrentHistory.current NativeCurrentPointerVectors.sha
    NativeCurrentPointerVectors.initial (.bytes NativeCurrentPointerVectors.fakeLine) [] = none := by decide
set_option maxRecDepth 2048 in
theorem originalWalRequiresEvidence : NativeCurrentHistory.current NativeCurrentPointerVectors.sha
    NativeCurrentPointerVectors.initial (.bytes NativeCurrentPointerVectors.lineBytes) [] = none := by decide

theorem corruptChecksum {inputs} : NativeCurrentHistory.current NativeCurrentPointerVectors.sha
    NativeCurrentPointerVectors.initial (.bytes (NativeCurrentPointerVectors.pre2 ++ [124] ++
      NativeVoteBytes.ascii "wrong\n")) inputs = none :=
  NativeCurrentHistory.badObservationRejected NativeCurrentPointerVectors.checksumSubstitution

theorem duplicateWal {inputs} : NativeCurrentHistory.current NativeCurrentPointerVectors.sha
    NativeCurrentPointerVectors.initial (.bytes (NativeCurrentPointerVectors.lineBytes ++
      NativeCurrentPointerVectors.lineBytes)) inputs = none :=
  NativeCurrentHistory.badObservationRejected NativeCurrentPointerVectors.doubleRecord

theorem crlfWal {inputs} : NativeCurrentHistory.current NativeCurrentPointerVectors.sha
    NativeCurrentPointerVectors.initial (.bytes (NativeCurrentPointerVectors.pre2 ++ [124] ++
      NativeVoteBytes.hexBytes NativeCurrentPointerVectors.digest2 ++ [13,10])) inputs = none :=
  NativeCurrentHistory.badObservationRejected NativeCurrentPointerVectors.crlfRejected

end DeltaReduce.NativeCurrentHistoryVectors
