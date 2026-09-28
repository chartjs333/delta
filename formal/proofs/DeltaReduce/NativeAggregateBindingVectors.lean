import DeltaReduce.NativeAggregateBinding
import DeltaReduce.NativeApplyCertificateVectors

/-! Existing native components and small mathematical/encoding counterchecks.
No authenticated full original/draft execution is instantiated. -/
namespace DeltaReduce.NativeAggregateBindingVectors
open NativeBinding NativeCertifiedCorpus NativeAggregateBinding
set_option maxRecDepth 4096

def common := NativeParameterVectors.certificate.common

theorem originalNumbers : ExactBody common common.leaves [1] = true := by
  simp [ExactBody,NativeVectorAuthority.bodyMatches,common,NativeParameterVectors.certificate]; decide
theorem changedNumber : ExactBody common common.leaves [2] = false := by
  simp [ExactBody,NativeVectorAuthority.bodyMatches,common,NativeParameterVectors.certificate]; decide
theorem missingLeaf : ExactBody common [] [1] = false := by
  simp [ExactBody,NativeVectorAuthority.bodyMatches,common,NativeParameterVectors.certificate]
theorem extraLeaf : ExactBody common (common.leaves ++ [[1]]) [1] = false := by
  cases h : ExactBody common (common.leaves ++ [[1]]) [1] with
  | false => rfl
  | true =>
    have count := (exactBody h).1.length_eq
    change 1 = 2 at count
    omega
theorem duplicateLeaf : ExactBody common (common.leaves ++ common.leaves) [1] = false := by
  cases h : ExactBody common (common.leaves ++ common.leaves) [1] with
  | false => rfl
  | true =>
    have count := (exactBody h).1.length_eq
    change 1 = 2 at count
    omega
theorem substitutedLeaf : ExactBody common [[1]] [1] = false := by
  simp [ExactBody,NativeVectorAuthority.bodyMatches,common,NativeParameterVectors.certificate]; decide
theorem negativeAliasRejected : ExactBody { common with numerators := [asciiBytes "-01"] } common.leaves [-1] = false := by
  simp [ExactBody,NativeVectorAuthority.bodyMatches,common,NativeParameterVectors.certificate]; decide
theorem zeroAliasRejected : ExactBody { common with numerators := [asciiBytes "-00"] } common.leaves [0] = false := by
  simp [ExactBody,NativeVectorAuthority.bodyMatches,common,NativeParameterVectors.certificate]; decide
theorem leadingZeroRejected : ExactBody { common with numerators := [asciiBytes "01"] } common.leaves [1] = false := by
  simp [ExactBody,NativeVectorAuthority.bodyMatches,common,NativeParameterVectors.certificate]; decide

def multiple := { common with leaves := [[1],[2]], numerators := [asciiBytes "3",asciiBytes "-1"] }
theorem fullVector : ExactBody multiple [[2],[1]] [3,-1] = true := by
  simp [ExactBody,NativeVectorAuthority.bodyMatches,common,multiple,NativeParameterVectors.certificate,List.mergeSort,NativePolicyBytes.bytesLT]; decide
theorem changedCoordinate : ExactBody multiple [[2],[1]] [3,1] = false := by
  simp [ExactBody,NativeVectorAuthority.bodyMatches,common,multiple,NativeParameterVectors.certificate,List.mergeSort,NativePolicyBytes.bytesLT]; decide
theorem missingCoordinate : ExactBody multiple [[2],[1]] [3] = false := by
  simp [ExactBody,NativeVectorAuthority.bodyMatches,common,multiple,NativeParameterVectors.certificate,List.mergeSort,NativePolicyBytes.bytesLT]
theorem swappedCoordinates : ExactBody multiple [[2],[1]] [-1,3] = false := by
  simp [ExactBody,NativeVectorAuthority.bodyMatches,common,multiple,NativeParameterVectors.certificate,List.mergeSort,NativePolicyBytes.bytesLT]; decide

def root := NativeAggregateVectors.finalizedEdge
def candidate := NativeApplyCertificateVectors.proposedEdge

theorem originalRootProfile : ApplyLinks root candidate.profile.id candidate := ⟨rfl,rfl,rfl⟩
theorem changedRoot : ¬ ApplyLinks { root with id := [1] } candidate.profile.id candidate := by
  intro h
  have sizes := congrArg List.length h.1
  change 71 = 1 at sizes
  omega
theorem changedProfile : ¬ ApplyLinks root [1] candidate := by
  intro h
  have sizes := congrArg List.length h.2.2
  change 71 = 1 at sizes
  omega
theorem changedSigner : ¬ ApplyLinks { root with certificate := { root.certificate with signers := [] } } candidate.profile.id candidate := by
  intro h
  have sizes := congrArg List.length (congrArg NativeAggregateRoot.Certificate.signers h.2.1)
  change 3 = 0 at sizes
  omega
theorem changedParent : ¬ ApplyLinks { root with certificate := { root.certificate with common := { root.certificate.common with isc := [1] } } } candidate.profile.id candidate := by
  intro h
  have sizes := congrArg List.length (congrArg (fun c => c.common.isc) h.2.1)
  change 71 = 1 at sizes
  omega
theorem missingRootLeaf : ¬ ApplyLinks { root with certificate := { root.certificate with common := { root.certificate.common with leaves := [] } } } candidate.profile.id candidate := by
  intro h
  have sizes := congrArg List.length (congrArg (fun c => c.common.leaves) h.2.1)
  change 1 = 0 at sizes
  omega

def parameter : ParameterBody := ⟨"PARAMETER_EXPECTED",List.replicate 32 0,"c","d","s0000000000",2,[3,-1],[List.replicate 32 1]⟩

def parameterBytes : Bytes := [123,34,97,117,116,104,111,114,105,116,121,95,105,100,34,58,34,115,104,97,50,53,54,58,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,34,44,34,99,111,110,116,101,120,116,34,58,34,99,34,44,34,100,101,110,111,109,105,110,97,116,111,114,34,58,50,44,34,100,111,109,97,105,110,34,58,34,100,34,44,34,105,110,112,117,116,95,108,101,97,102,95,105,100,115,34,58,91,34,115,104,97,50,53,54,58,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,48,49,34,93,44,34,107,105,110,100,34,58,34,80,65,82,65,77,69,84,69,82,95,69,88,80,69,67,84,69,68,34,44,34,110,117,109,101,114,97,116,111,114,115,34,58,91,51,44,45,49,93,44,34,115,104,97,114,100,34,58,34,115,48,48,48,48,48,48,48,48,48,48,34,125]
theorem parameterCanonical : encodeParameterBody parameter = some parameterBytes := by rfl

def headerBytes : Bytes := [123,34,107,105,110,100,34,58,34,65,71,71,82,69,71,65,84,69,95,80,82,79,74,69,67,84,73,79,78,34,44,34,112,97,121,108,111,97,100,34,58,123,34,97,117,116,104,111,114,105,116,121,95,105,100,34,58]
theorem headerCanonical : asciiBytes "{\"kind\":\"AGGREGATE_PROJECTION\",\"payload\":{\"authority_id\":" = headerBytes := by decide

def authorityBytes : Bytes := [34,115,104,97,50,53,54,58,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,34]
theorem authorityCanonical : quotedBytes (idBytes (List.replicate 32 0)) = authorityBytes := by decide

def parameterField : Bytes := [44,34,112,97,114,97,109,101,116,101,114,115,34,58]
theorem fieldCanonical : asciiBytes ",\"parameters\":" = parameterField := by decide

def aggregateBytes : Bytes := headerBytes ++ authorityBytes ++ parameterField ++ [91] ++ parameterBytes ++ [93] ++ [125,125]
theorem aggregateCanonical : NativeAggregateBinding.encode (List.replicate 32 0) [parameterBytes] = aggregateBytes := by
  simp only [NativeAggregateBinding.encode,headerCanonical,authorityCanonical,fieldCanonical,arrayBytes,
    List.intercalate_singleton,List.append_assoc,aggregateBytes]

theorem sourceParameterEncoding : encodeParameterBodies [parameter] = some [parameterBytes] := by
  simp only [encodeParameterBodies,parameterCanonical,bind,Option.bind]

theorem anchorRoots (a : Anchor) (r : Ref) : (extended a r).roots = [a.authority,r] := rfl
theorem anchorContext (a : Anchor) (r : Ref) : (extended a r).context = a.context := rfl

end DeltaReduce.NativeAggregateBindingVectors
