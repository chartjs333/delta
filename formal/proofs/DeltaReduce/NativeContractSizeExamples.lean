import DeltaReduce.NativeSizedParameterSection
import DeltaReduce.NativeNormEvidenceVectors

/-! Small kernel examples and compositional large-length checks. Constant hash
is deliberately synthetic; no new SHA or whole-policy execution claim. -/
namespace DeltaReduce.NativeContractSizeExamples
open NativeReceiptBytes NativeContractSize

def syntheticSha (_ : Bytes) : Bytes := List.replicate 32 0
def syntheticId : Bytes := NativeVoteBytes.ascii "sha256:" ++ NativeVoteBytes.hexBytes (List.replicate 32 0)
def row : Row := ⟨"TEST",.end,[1],[2],some syntheticId⟩

theorem lowHash (domain raw : Bytes) :
    NativeStateBytes.contentId syntheticSha domain raw = some syntheticId := by rfl
theorem belowBound : contentId syntheticSha [1] (List.replicate (maxBytes-1) 0) = some syntheticId :=
  fromComponents (by simp only [List.length_replicate]; decide) (lowHash _ _)
theorem atBound : contentId syntheticSha [1] (List.replicate maxBytes 0) = some syntheticId :=
  fromComponents (by simp only [List.length_replicate]; exact Nat.le_refl _) (lowHash _ _)
theorem overBound : contentId syntheticSha [1] (List.replicate (maxBytes+1) 0) = none :=
  oversized (by simp only [List.length_replicate]; exact Nat.lt_succ_self _)
theorem oldPrimitiveIsUnbounded :
    NativeStateBytes.contentId syntheticSha [1] (List.replicate (maxBytes+1) 0) = some syntheticId :=
  lowHash _ _
theorem validRow : check syntheticSha row = some ⟨row,syntheticId⟩ :=
  checkFromComponents (by decide) (lowHash _ _) (Or.inr rfl)
theorem unknownDigest : check (fun _ => []) row = none := by rfl
theorem wrongDigest : check (fun _ => [0]) row = none := by rfl
theorem wrongExpected : check syntheticSha {row with expected := some []} = none := by
  apply wrongIdentity (id := syntheticId)
  · exact fromComponents (by decide) (lowHash _ _)
  · decide
theorem proposedRow : check syntheticSha {row with expected := none} =
    some ⟨{row with expected := none},syntheticId⟩ :=
  checkFromComponents (by decide) (lowHash _ _) (Or.inl rfl)
theorem emptyList : checkAll syntheticSha [] = some [] := rfl
theorem orderedList : checkAll syntheticSha [row,row] = some [⟨row,syntheticId⟩,⟨row,syntheticId⟩] := by
  simp only [checkAll,validRow,bind,Option.bind]
theorem oneLargeRowRejects :
    checkAll syntheticSha [row,{row with payload := List.replicate (maxBytes+1) 0},row] = none := by
  apply oversizedListRejected (row := {row with payload := List.replicate (maxBytes+1) 0})
  · exact List.mem_cons_of_mem _ (List.mem_cons_self)
  · simp only [List.length_replicate]; exact Nat.lt_succ_self _

set_option maxRecDepth 4096 in
theorem originalNormBound :
    (NativeNormEvidence.json NativeNormEvidenceVectors.evidence).length ≤ maxBytes := by
  rw [NativeNormEvidenceVectors.exactJSON]
  decide

theorem originalNormSized :
    check NativeNormEvidenceVectors.sha
      (NativeSizedParameterSection.normRow NativeNormEvidenceVectors.checked) =
    some ⟨NativeSizedParameterSection.normRow NativeNormEvidenceVectors.checked,
      NativeNormEvidenceVectors.evidenceId⟩ :=
  checkFromComponents originalNormBound NativeNormEvidenceVectors.evidenceComputed (Or.inr rfl)

-- This composition retains actual original parsing/shape/parent/hash checks.
-- The finite original SHA samples still do not authenticate a native exporter.
theorem originalNormComposition :
    NativeNormEvidence.check NativeNormEvidenceVectors.sha
      NativeNormEvidenceVectors.evidence.context [NativeIscCertificateVectors.qc]
      NativeNormEvidenceVectors.tree = some NativeNormEvidenceVectors.checked ∧
    check NativeNormEvidenceVectors.sha
      (NativeSizedParameterSection.normRow NativeNormEvidenceVectors.checked) =
    some ⟨NativeSizedParameterSection.normRow NativeNormEvidenceVectors.checked,
      NativeNormEvidenceVectors.evidenceId⟩ :=
  ⟨NativeNormEvidenceVectors.normChecked,originalNormSized⟩

end DeltaReduce.NativeContractSizeExamples
