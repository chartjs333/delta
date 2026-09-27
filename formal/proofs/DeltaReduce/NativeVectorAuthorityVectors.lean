import DeltaReduce.NativeVectorAuthority

/-! Small body-comparison cases only. The deliberately empty authority and tiny
leaf labels are NOT valid native certificates, bindings or raw-run witnesses. -/
namespace DeltaReduce.NativeVectorAuthorityVectors
open NativeVectorAuthority

def sample : NativeParameter.Common :=
  ⟨⟨[],0,[],[],[],[],0⟩,[],1,[],[],[[1],[2]],[],[[51],[45,52]],[]⟩

theorem exactNumbers : bodyMatches sample [[1],[2]] [3,-4] = true := by
  simp [bodyMatches,sample,List.mergeSort,NativePolicyBytes.bytesLT]
  decide
theorem sourceOrderRetained : bodyMatches sample [[2],[1]] [3,-4] = true := by
  simp [bodyMatches,sample,List.mergeSort,NativePolicyBytes.bytesLT]
  decide
theorem changedNumber : bodyMatches sample [[1],[2]] [3,-3] = false := by
  simp [bodyMatches,sample,List.mergeSort,NativePolicyBytes.bytesLT]
  decide
theorem missingLeaf : bodyMatches sample [[1]] [3,-4] = false := by
  simp [bodyMatches,sample]
theorem extraLeaf : bodyMatches sample [[1],[2],[3]] [3,-4] = false := by
  apply invalidBodyRejected
  left
  intro eq
  have count := congrArg List.length eq
  simp [sample] at count

theorem duplicateLeaf : bodyMatches sample [[1],[2],[2]] [3,-4] = false := by
  apply invalidBodyRejected
  left
  intro eq
  have count := congrArg List.length eq
  simp [sample] at count

theorem originalNegativeZeroPreserved :
    bodyMatches {sample with numerators := [[45,48,48],[45,52]]} [[1],[2]] [0,-4] = true := by
  simp [bodyMatches,sample,List.mergeSort,NativePolicyBytes.bytesLT]
  decide
theorem numericOnlyIsInsufficient : sample.plan = [] ∧ sample.isc = [] ∧
    bodyMatches sample [[1],[2]] [3,-4] = true := ⟨rfl,rfl,exactNumbers⟩

end DeltaReduce.NativeVectorAuthorityVectors
