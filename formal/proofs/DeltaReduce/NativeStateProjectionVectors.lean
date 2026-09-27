import DeltaReduce.NativeStateProjection
import DeltaReduce.NativeApplyResultVectors

/-! Small separate mathematical encodings; no authenticated unit source or
positive full native history is manufactured by these examples. -/
namespace DeltaReduce.NativeStateProjectionVectors
open NativeBinding NativeStateArtifacts

def profile : Profile := profileValue 64 ⟨1,4⟩ NativeApplyResultVectors.sourceProfile
def schema : Ref := ⟨[],.schema,1⟩
def model : StateVector := ⟨schema,⟨1,4⟩,[19,-19]⟩
def optimizer : StateVector := ⟨schema,⟨1,4⟩,[2,-2]⟩

theorem numericProfile : ProfileChecks NativeApplyResultVectors.sourceProfile profile := by decide
theorem badWidth : ¬ ProfileChecks NativeApplyResultVectors.sourceProfile
    {profile with accumulatorBits := 32} := by decide
theorem zeroQuantum : ¬ ProfileChecks NativeApplyResultVectors.sourceProfile
    {profile with applyQuantum := ⟨0,1⟩} := by decide
theorem nonReducedQuantum : ¬ ProfileChecks NativeApplyResultVectors.sourceProfile
    {profile with applyQuantum := ⟨2,8⟩} := by decide
theorem wrongCoefficient : ¬ ProfileChecks NativeApplyResultVectors.sourceProfile
    {profile with learningRate := ⟨1,3⟩} := by decide
theorem removedDomain : ¬ ProfileChecks NativeApplyResultVectors.sourceProfile
    {profile with domainWeights := []} := by decide
theorem wrongDomain : ¬ ProfileChecks NativeApplyResultVectors.sourceProfile
    {profile with domainWeights := [⟨"different",⟨1,1⟩⟩]} := by decide
theorem duplicateDomain : ¬ ProfileChecks NativeApplyResultVectors.sourceProfile
    {profile with domainWeights := profile.domainWeights ++ profile.domainWeights} := by decide
theorem sourceAllowsAnotherQuantum : ProfileChecks NativeApplyResultVectors.sourceProfile
    (profileValue 64 ⟨1,2⟩ NativeApplyResultVectors.sourceProfile) := by decide
theorem differentCompleteProfiles : profile ≠ profileValue 64 ⟨1,2⟩ NativeApplyResultVectors.sourceProfile :=
  sourceCannotDetermineQuantum (by decide)
theorem cannotInferUniqueProfile (f : NativeApplyProfile.Profile → Profile) :
    ¬ (f NativeApplyResultVectors.sourceProfile = profile ∧
      f NativeApplyResultVectors.sourceProfile = profileValue 64 ⟨1,2⟩ NativeApplyResultVectors.sourceProfile) :=
  noUniqueQuantumProjection (by decide) f

theorem missingUnits {sha codec store b pid initial observation history permission inputs} :
    NativeStateProjection.construct sha codec store b (fun _ => none) pid initial observation history permission inputs = none :=
  NativeStateProjection.noUnitsRejected
theorem unknownHistory {sha codec store b units pid initial history permission inputs} :
    NativeStateProjection.construct sha codec store b units pid initial .unknown history permission inputs = none := rfl

def profileBytes : Bytes := [123,34,107,105,110,100,34,58,34,80,82,79,70,73,76,69,34,44,34,112,97,121,108,111,97,100,34,58,123,34,97,99,99,117,109,117,108,97,116,111,114,95,98,105,116,115,34,58,54,52,44,34,97,112,112,108,121,95,113,117,97,110,116,117,109,34,58,91,49,44,52,93,44,34,100,111,109,97,105,110,95,119,101,105,103,104,116,115,34,58,91,123,34,100,111,109,97,105,110,34,58,34,100,49,34,44,34,119,101,105,103,104,116,34,58,91,49,44,49,93,125,93,44,34,108,101,97,114,110,105,110,103,95,114,97,116,101,34,58,91,49,44,50,93,44,34,109,111,109,101,110,116,117,109,34,58,91,49,44,50,93,44,34,110,101,115,116,101,114,111,118,34,58,116,114,117,101,44,34,111,117,116,112,117,116,95,114,97,110,103,101,34,58,34,70,85,76,76,95,83,73,71,78,69,68,95,73,78,84,54,52,34,44,34,114,111,117,110,100,105,110,103,34,58,34,72,65,76,70,95,84,79,87,65,82,68,95,80,79,83,73,84,73,86,69,34,44,34,119,101,105,103,104,116,95,100,101,99,97,121,34,58,91,48,44,49,93,125,125]

set_option maxRecDepth 4096 in
theorem profileEncoding : NativeStateArtifacts.profileBytes profile = profileBytes := by decide

def modelBytes : Bytes := [123,34,107,105,110,100,34,58,34,77,79,68,69,76,34,44,34,112,97,121,108,111,97,100,34,58,123,34,113,117,97,110,116,117,109,34,58,91,49,44,52,93,44,34,115,99,104,101,109,97,34,58,123,34,105,100,34,58,34,115,104,97,50,53,54,58,34,44,34,107,105,110,100,34,58,34,83,67,72,69,77,65,34,44,34,108,101,110,103,116,104,34,58,49,125,44,34,118,97,108,117,101,115,34,58,91,49,57,44,45,49,57,93,125,125]

set_option maxRecDepth 4096 in
theorem modelEncoding : vectorBytes "MODEL" model = modelBytes := by decide

def optimizerBytes : Bytes := [123,34,107,105,110,100,34,58,34,79,80,84,73,77,73,90,69,82,34,44,34,112,97,121,108,111,97,100,34,58,123,34,113,117,97,110,116,117,109,34,58,91,49,44,52,93,44,34,115,99,104,101,109,97,34,58,123,34,105,100,34,58,34,115,104,97,50,53,54,58,34,44,34,107,105,110,100,34,58,34,83,67,72,69,77,65,34,44,34,108,101,110,103,116,104,34,58,49,125,44,34,118,97,108,117,101,115,34,58,91,50,44,45,50,93,125,125]

set_option maxRecDepth 4096 in
theorem optimizerEncoding : vectorBytes "OPTIMIZER" optimizer = optimizerBytes := by decide

end DeltaReduce.NativeStateProjectionVectors
