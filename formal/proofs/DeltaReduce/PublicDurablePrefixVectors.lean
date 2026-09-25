import DeltaReduce.PublicDurablePrefix
import DeltaReduce.PublicJournalVectors

/-! Small kernel checks and reuse of the original eight-slot journal. No new
native run or successful mixed-kind full-prefix projection is claimed. -/
namespace DeltaReduce.PublicDurablePrefixVectors
open PublicState PublicJournal PublicDurablePrefix
set_option maxRecDepth 10000

def alice : Value := .model "alice"
def bob : Value := .model "bob"
def voteA : Vote := ⟨alice,.text "PARAMETER",.integer 1,.integer 10⟩
def voteB : Vote := ⟨alice,.text "APPLY",.integer 2,.integer 20⟩
def voteOther : Vote := ⟨bob,.text "PARAMETER",.integer 1,.integer 30⟩
def frame : Frame := ⟨.model "advanced",8,99,2,[voteB,voteOther,voteA]⟩
def journal : Journal := { PublicJournalVectors.start with slots := [PublicJournalVectors.s4,PublicJournalVectors.s7] }

theorem publicSetOrderIsNotSequenceOrder : alignment alice frame journal [voteA,voteB] := by decide
theorem canonicalSetOrderAlsoMatches : alignment alice frame journal [voteB,voteA] := by decide
theorem otherActorIsNotAnExtraLocalVote : (actorVotes alice frame).length = 2 := by decide
theorem sameCountSubstitutionRejected : ¬ alignment alice frame journal [voteA,{voteB with body := .integer 99}] := by decide
theorem missingVoteRejected : ¬ alignment alice frame journal [voteA] := by decide
theorem extraVoteRejected : ¬ alignment alice frame journal [voteA,voteB,voteOther] := by decide
theorem duplicateReplacingVoteRejected : ¬ alignment alice frame journal [voteA,voteA] := by decide
theorem malformedDuplicateSetRejected : ¬ alignment alice {frame with votes := [voteA,voteA]} journal [voteA,voteA] := by decide
theorem wrongTipRejected : ¬ alignment alice {frame with sequence := 1} journal [voteA,voteB] := by decide
theorem emptySetMatchesEmptyJournal : alignment alice {frame with votes := [],sequence := 0} PublicJournalVectors.start [] := by decide
theorem wrongActorSetRejected : ¬ alignment bob frame journal [voteA,voteB] := by decide

theorem originalMixedPrefixFailsClosed {mapping vocabulary metadataTrust}
    {source : PublicAuthority.Metadata metadataTrust} {limit expected publicFrame actor ordered} :
    checkPrefix PublicJournalVectors.env mapping vocabulary source limit expected PublicJournalVectors.finalJournal publicFrame actor ordered = none :=
  opaqueSlotBlocksCompletePrefix (slot := PublicJournalVectors.s0) (List.mem_cons_self) (by rfl)

theorem firstArithmeticOriginalPrefixFailsClosed {mapping vocabulary metadataTrust}
    {source : PublicAuthority.Metadata metadataTrust} {limit expected publicFrame actor ordered} :
    checkPrefix PublicJournalVectors.env mapping vocabulary source limit expected (PublicJournalVectors.journalAt 4) publicFrame actor ordered = none :=
  opaqueSlotBlocksCompletePrefix (slot := PublicJournalVectors.s0) (List.mem_cons_self) (by rfl)

theorem completeOtherAuthorizationStillFails {mapping vocabulary metadataTrust}
    {source : PublicAuthority.Metadata metadataTrust} {limit expected publicFrame actor ordered} :
    checkPrefix { PublicJournalVectors.env with otherAuthorized := fun _ _ => true }
      mapping vocabulary source limit expected PublicJournalVectors.finalJournal publicFrame actor ordered = none :=
  opaqueSlotBlocksCompletePrefix (slot := PublicJournalVectors.s0) (List.mem_cons_self) (by rfl)

theorem allFiveNonArithmeticKindsRemainUnsupported :
    ([PublicJournalVectors.s0,PublicJournalVectors.s1,PublicJournalVectors.s2,PublicJournalVectors.s3,PublicJournalVectors.s6].map
      (fun slot => slot.envelope.action.arithmetic)) = [false,false,false,false,false] := by decide
theorem viewAndAbortHaveNoFabricatedBridge : Action.view.arithmetic = false ∧ Action.abort.arithmetic = false := by decide
theorem originalArithmeticSequencesUnchanged :
    [PublicJournalVectors.s4.sequence,PublicJournalVectors.s5.sequence,PublicJournalVectors.s7.sequence] = [5,6,8] := by decide

theorem reorderedNativePrefixRejected {env mapping vocabulary metadataTrust}
    {source : PublicAuthority.Metadata metadataTrust} {limit expected first second} :
    checkPairs (codec := NativeGraphVectors.codec) (trust := NativeGraphVectors.syntheticTrust)
      (voteTrust := NativeVoteVectors.voteTrust) env mapping vocabulary source limit expected 1
      [PublicJournalVectors.s1,PublicJournalVectors.s0] [first,second] = none := by
  exact wrongSequencePairsRejected (by decide)

theorem arithmeticSuffixCannotBeRenumberedByOmission {env mapping vocabulary metadataTrust}
    {source : PublicAuthority.Metadata metadataTrust} {limit expected first} :
    checkPairs (codec := NativeGraphVectors.codec) (trust := NativeGraphVectors.syntheticTrust)
      (voteTrust := NativeVoteVectors.voteTrust) env mapping vocabulary source limit expected 1
      [PublicJournalVectors.s4] [first] = none := by
  exact wrongSequencePairsRejected (by decide)

end DeltaReduce.PublicDurablePrefixVectors
