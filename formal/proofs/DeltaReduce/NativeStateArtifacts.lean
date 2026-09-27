import DeltaReduce.NativePlanProjection
import DeltaReduce.NativeCurrentHistory

/-! Complete PROFILE/MODEL/OPTIMIZER encodings. Quantum is an explicit missing
source input, not inferred from a native integer vector or a content identifier. -/
namespace DeltaReduce.NativeStateArtifacts
open NativeBinding
open NativeVectorLayout (text)
open NativePlanProjection (encodeFraction)

def profileValue (bits : Nat) (quantum : Rational) (p : NativeApplyProfile.Profile) : Profile :=
  ⟨bits,quantum,p.weights.map (fun w => ⟨text w.domain,NativeApplyResult.fraction w.fraction⟩),
    NativeApplyResult.fraction p.learning,NativeApplyResult.fraction p.momentum,
    NativeApplyResult.fraction p.decay,text p.rounding,p.nesterov == 1,"FULL_SIGNED_INT64"⟩

def weightBytes (w : DomainWeight) : Bytes :=
  asciiBytes "{\"domain\":" ++ quotedBytes (asciiBytes w.domain) ++
    asciiBytes ",\"weight\":" ++ encodeFraction w.weight ++ [125]

def profileBytes (p : Profile) : Bytes :=
  asciiBytes "{\"kind\":\"PROFILE\",\"payload\":{\"accumulator_bits\":" ++ asciiBytes (toString p.accumulatorBits) ++
  asciiBytes ",\"apply_quantum\":" ++ encodeFraction p.applyQuantum ++
  asciiBytes ",\"domain_weights\":" ++ arrayBytes (p.domainWeights.map weightBytes) ++
  asciiBytes ",\"learning_rate\":" ++ encodeFraction p.learningRate ++
  asciiBytes ",\"momentum\":" ++ encodeFraction p.momentum ++
  asciiBytes ",\"nesterov\":" ++ asciiBytes (if p.nesterov then "true" else "false") ++
  asciiBytes ",\"output_range\":" ++ quotedBytes (asciiBytes p.outputRange) ++
  asciiBytes ",\"rounding\":" ++ quotedBytes (asciiBytes p.rounding) ++
  asciiBytes ",\"weight_decay\":" ++ encodeFraction p.weightDecay ++ [125,125]

def vectorBytes (kind : String) (v : StateVector) : Bytes :=
  asciiBytes "{\"kind\":" ++ quotedBytes (asciiBytes kind) ++
  asciiBytes ",\"payload\":{\"quantum\":" ++ encodeFraction v.quantum ++
  asciiBytes ",\"schema\":" ++ NativeVectorArtifacts.encodeSchemaRef v.schema ++
  asciiBytes ",\"values\":" ++ arrayBytes (v.values.map (asciiBytes ∘ toString)) ++ [125,125]

def ProfileChecks (p : NativeApplyProfile.Profile) (q : Profile) : Prop :=
  NativeApplyResult.ProfileMatches p q ∧
  (q.accumulatorBits = 64 ∨ q.accumulatorBits = 128) ∧ positiveQuantum q.applyQuantum ∧
  domains q ≠ [] ∧ (domains q).Pairwise (· < ·) ∧
  (∀ w ∈ q.domainWeights, validIdentifier w.domain = true ∧
    ParameterKernel.ReducedNonnegative minInput maxInput w.weight.numerator w.weight.denominator) ∧
  (∀ r ∈ [q.learningRate,q.momentum,q.weightDecay],
    ParameterKernel.ReducedNonnegative minInput maxInput r.numerator r.denominator)
instance (p q) : Decidable (ProfileChecks p q) := by unfold ProfileChecks; infer_instance

theorem coefficients (bits quantum p) :
    (profileValue bits quantum p).learningRate = NativeApplyResult.fraction p.learning ∧
    (profileValue bits quantum p).momentum = NativeApplyResult.fraction p.momentum ∧
    (profileValue bits quantum p).weightDecay = NativeApplyResult.fraction p.decay := ⟨rfl,rfl,rfl⟩

theorem orderedWeights (bits quantum p) (i : Nat) :
    (profileValue bits quantum p).domainWeights[i]? =
      (p.weights.map (fun w => (⟨text w.domain,NativeApplyResult.fraction w.fraction⟩ : DomainWeight)))[i]? := rfl

theorem fullWeightCount (bits quantum p) : (profileValue bits quantum p).domainWeights.length = p.weights.length :=
  List.length_map _

theorem quantumRetained (bits quantum p) : (profileValue bits quantum p).applyQuantum = quantum := rfl

theorem sourceCannotDetermineQuantum {bits p a b} (different : a ≠ b) :
    profileValue bits a p ≠ profileValue bits b p := by
  intro eq
  exact different (congrArg Profile.applyQuantum eq)

theorem noUniqueQuantumProjection {bits p a b} (different : a ≠ b) (f : NativeApplyProfile.Profile → Profile) :
    ¬ (f p = profileValue bits a p ∧ f p = profileValue bits b p) := by
  intro both
  exact sourceCannotDetermineQuantum different (both.1.symm.trans both.2)

end DeltaReduce.NativeStateArtifacts
