import DeltaReduce.PublicApplyJoin
import DeltaReduce.PublicParameterBodyVectors

-- Small separate native-arithmetic and constructed-body cases. No joined
-- public-state/native execution or exporter authentication is claimed.
namespace DeltaReduce.PublicApplyBodyVectors
open NativeBinding NativeInputProjection PublicState PublicAuthority PublicApplyBody ApplyKernel NativeGraphVectors
set_option Elab.async false
set_option maxRecDepth 16000
set_option maxHeartbeats 4000000

def limit127 : ModelLimit := ⟨127,by decide,by decide⟩
def convert (lo hi denominator u v x y : Int) (numbers : List Int) :=
  ParameterKernel.checkedDomainVector lo hi minInput maxInput denominator u v x y numbers
def run (lo hi : Int) (model optimizer : List Int) (rows : List DomainRow) (lr mu : Weight) :=
  (deriveApply lo hi model optimizer rows lr mu ⟨0,1⟩).map (fun r => (r.nextModel,r.nextOptimizer))

theorem nativeApplyRecheckedAtModelWidth : ((deriveNativeApply fixtureBinding).bind
    (fun native => (PublicApplyArithmetic.check native limit127).map
      (fun p => (p.arithmetic.nextModel,p.arithmetic.nextOptimizer)))) = some ([19,-19],[2,-2]) := by decide +kernel

theorem conversionRoundsPerDomain : convert (-128) 127 1 1 2 1 1 [1,-1] = some [1,0] := by decide +kernel
theorem conversionFirstProductRejectsCancellation : convert (-128) 127 2 2 1 1 1 [64] = none := by decide +kernel
theorem conversionFirstProductFitsNative : convert minInput maxInput 2 2 1 1 1 [64] = some [64] := by decide +kernel
theorem conversionSecondProductRejects : convert (-128) 127 2 2 1 1 2 [40] = none := by decide +kernel
theorem conversionDenominatorFirstProductRejects : convert (-128) 127 64 1 2 1 1 [0] = none := by decide +kernel
theorem conversionDenominatorSecondProductRejects : convert (-128) 127 40 1 1 4 1 [0] = none := by decide +kernel
theorem conversionDenominatorFitsNative : convert minInput maxInput 40 1 1 4 1 [0] = some [0] := by decide +kernel
theorem invalidQuantumRejects : convert (-128) 127 1 1 0 1 1 [1] = none := by decide +kernel
theorem mixtureFirstProductRejects : checkedMix (-128) 127 3 0 [⟨⟨2,3⟩,70⟩,⟨⟨1,3⟩,-70⟩] = none := by decide +kernel
theorem mixtureFirstProductFitsNative : checkedMix minInput maxInput 3 0 [⟨⟨2,3⟩,70⟩,⟨⟨1,3⟩,-70⟩] = some 70 := by decide +kernel
theorem mixtureScaledProductRejects : run (-128) 127 [10] [0]
    [⟨⟨1,2⟩,[50]⟩,⟨⟨1,3⟩,[-50]⟩,⟨⟨1,6⟩,[-50]⟩] ⟨0,1⟩ ⟨0,1⟩ = none := by decide +kernel
theorem mixtureScaledProductFitsNative : run minInput maxInput [10] [0]
    [⟨⟨1,2⟩,[50]⟩,⟨⟨1,3⟩,[-50]⟩,⟨⟨1,6⟩,[-50]⟩] ⟨0,1⟩ ⟨0,1⟩ = some ([10],[0]) := by decide +kernel
theorem zeroLearningRateDoesNotBypassMomentumProduct : run (-128) 127 [10] [70]
    [⟨⟨1,1⟩,[-100]⟩] ⟨0,1⟩ ⟨2,1⟩ = none := by decide +kernel
theorem momentumProductFitsNative : run minInput maxInput [10] [70]
    [⟨⟨1,1⟩,[-100]⟩] ⟨0,1⟩ ⟨2,1⟩ = some ([10],[40]) := by decide +kernel
theorem learningRateProductRejectsSafeFinal : run (-128) 127 [100] [0]
    [⟨⟨1,1⟩,[100]⟩] ⟨3,2⟩ ⟨0,1⟩ = none := by decide +kernel
theorem learningRateProductFitsNative : run minInput maxInput [100] [0]
    [⟨⟨1,1⟩,[100]⟩] ⟨3,2⟩ ⟨0,1⟩ = some ([-50],[100]) := by decide +kernel
theorem noOptimizerPadding : run (-128) 127 [1,2] [0] [⟨⟨1,1⟩,[0,0]⟩] ⟨1,1⟩ ⟨0,1⟩ = none := by decide +kernel
theorem noDomainPadding : run (-128) 127 [1,2] [0,0] [⟨⟨1,1⟩,[0]⟩] ⟨1,1⟩ ⟨0,1⟩ = none := by decide +kernel

def leaf (shard : String) (number : Int) : Value := record
  (PublicParameterBody.fields PublicAuthorityVectors.apc (.model "profile1") PublicAuthorityVectors.authority
    (.model "coeff1") (.model "configA") (.model "d1") PublicAuthorityVectors.ec PublicAuthorityVectors.isc
    (.model "parent1") PublicAuthorityVectors.round (.model "schema1") PublicAuthorityVectors.seed (.model shard) number)
def leaves : List Value := [leaf "shard1" 1,leaf "shard2" (-2)]
def aggregate : Value := record (aggregateFields PublicAuthorityVectors.apc (.model "profile1") (.model "coeff1")
  (.model "configA") PublicAuthorityVectors.ec PublicAuthorityVectors.isc (.model "parent1") PublicAuthorityVectors.round
  (.model "schema1") PublicAuthorityVectors.seed leaves)
def model : Value := vectorValue "MODEL" (.model "schema1") (PublicArithmeticInputs.function [(.model "shard1",.integer 19),(.model "shard2",.integer (-19))])
def optimizer : Value := vectorValue "OPTIMIZER" (.model "schema1") (PublicArithmeticInputs.function [(.model "shard1",.integer 2),(.model "shard2",.integer (-2))])
def bodyFields : List (String × Value) := applyFields aggregate (.model "apply1") PublicAuthorityVectors.authority
  (.model "configA") (.model "next1") model optimizer (.model "parent1") PublicAuthorityVectors.round
def body : Value := record bodyFields

theorem allApplyFields : bodyFields.map Prod.fst = applyFieldNames := rfl
theorem aggregateHasEveryLeaf : readField aggregate "leaves" = some (setValue leaves) ∧
    readField aggregate "canonicalRoot" = some (setValue leaves) := ⟨rfl,rfl⟩
theorem entireAuthorityRetained : readField body "authority" = some PublicAuthorityVectors.authority := rfl
theorem entireAggregateRetained : readField body "aggregate" = some aggregate := rfl
theorem nextValuesShareSchema : readField model "schema" = readField optimizer "schema" := rfl
theorem outputTableUsesModelKeys : readField model "values" = some
    (PublicArithmeticInputs.function [(.model "shard1",.integer 19),(.model "shard2",.integer (-19))]) := rfl
theorem completeConstructedBodyCanonical : canonical
    (PublicAuthorityVectors.vocabulary.models ++ ["next1","apply1"]) body = true := by decide +kernel
theorem deletingLeafChangesRoot : setValue [leaf "shard1" 1] ≠ setValue leaves := by decide +kernel
theorem changedLeafValueChangesRoot : setValue [leaf "shard1" 2,leaf "shard2" (-2)] ≠ setValue leaves := by decide +kernel
theorem duplicateLeafIsNoncanonical : canonical PublicAuthorityVectors.vocabulary.models
    (setValue [leaf "shard1" 1,leaf "shard1" 1]) = false := by decide +kernel

def checkpointMap : IdentityMap := ⟨fun _ => none,
  fun v => if v = .model "next1" then some "sha256:d6c611c6c31a21c04dbed453f2f90ecec18e3db594815466df3fdd3957ed61ba" else none,
  fun _ => none,fun _ => none⟩
theorem nativeCheckpointSpelling : (checkpointMap.checkpoint (.model "next1")).map asciiBytes =
    some (idBytes expectedApply.nextModelHash) := by decide +kernel
theorem unknownCheckpointHasNoIdentity : checkpointMap.checkpoint (.model "invented") = none := by decide +kernel
theorem malformedCheckpointHasNoIdentity : checkpointMap.checkpoint (.text "next1") = none := by decide +kernel

theorem originalNativeCheckpointChecked (native : NativeApply fixtureBinding)
    (computed : deriveNativeApply fixtureBinding = some native) :
    (checkCheckpoint checkpointMap (.model "next1") native).isSome = true := by
  have body := nativeApplyMatchesOracle
  rw [computed] at body
  have exactBody : native.body = expectedApply := Option.some.inj body
  have identifier : (checkpointMap.checkpoint (.model "next1")).map asciiBytes =
      some (idBytes native.body.nextModelHash) := by rw [exactBody]; exact nativeCheckpointSpelling
  simp only [checkCheckpoint,identifier,dif_pos,Option.isSome_some]

theorem missingPublicAuthorityRejects {codec store trust anchor binding corpus limit input vocabulary metadataTrust source}
    (authority : PublicAuthority.Projection (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (corpus := corpus) (limit := limit) input vocabulary (metadataTrust := metadataTrust) source)
    (mapping : IdentityMap) (expected : Value) (native : NativeApply binding) :
    PublicApplyBody.check authority mapping expected native (record [("checked",.boolean true)]) = none :=
  PublicApplyBody.missingAuthorityRejected authority mapping expected native _ rfl

end DeltaReduce.PublicApplyBodyVectors
