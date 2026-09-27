import DeltaReduce.NativeVectorJoin

/-! Raw source composition and refusal propagation. A successful certificate
section does not supply absent arithmetic proof bytes or draft authority. -/
namespace DeltaReduce.NativeSourceRefusal
open NativeReceiptBytes

theorem sectionFromSources {sha policyRaw stateRaw tree policy state bound}
    (hp : NativePolicyBytes.decodePolicy policyRaw = some (tree,policy))
    (hs : NativeStateBytes.decodeState stateRaw = some state)
    (hc : NativePlanSection.bindSection sha policy state = some bound) :
    NativePlanSection.prepare sha policyRaw stateRaw = some bound := by
  simp only [NativePlanSection.prepare,hp,hs,hc,Bind.bind,Option.bind]

theorem accumulatorIdentityUnavailable {hash config proof profile proofId}
    (different : hash (NativeAccumulatorBinding.proofInput proof) ≠ proofId) :
    NativeAccumulatorBinding.load hash config proof profile proofId = none := by
  cases h : NativeAccumulatorBinding.load hash config proof profile proofId with
  | none => rfl
  | some b => exact False.elim (different (NativeAccumulatorBinding.loadedSource h).proofId.2)

theorem proofBytesUnavailable {hash config proof profile proofId}
    (absent : NativeAccumulatorBytes.decodeProof proof = none) :
    NativeAccumulatorBinding.load hash config proof profile proofId = none := by
  cases h : NativeAccumulatorBinding.load hash config proof profile proofId with
  | none => rfl
  | some b =>
    have parsed := (NativeAccumulatorBinding.loadedSource h).proof
    rw [absent] at parsed
    contradiction

theorem coefficientsUnavailable {sha policyRaw stateRaw apc config proof profile members}
    (hm : NativePlanMembers.prepare sha policyRaw stateRaw apc = some members)
    (ha : NativeAccumulatorBinding.load (NativePlanCoefficients.contentHash sha)
      config proof profile members.edge.certificate.common.accumulator = none) :
    NativePlanCoefficients.bind sha policyRaw stateRaw apc config proof profile = none := by
  simp only [NativePlanCoefficients.bind,hm,ha,Bind.bind,Option.bind]

theorem corpusUnavailable {sha policyRaw stateRaw apc config proof profile permission inputs}
    (h : NativePlanCoefficients.bind sha policyRaw stateRaw apc config proof profile = none) :
    NativePlanQCorpus.bind sha policyRaw stateRaw apc config proof profile permission inputs = none := by
  simp only [NativePlanQCorpus.bind,h,Bind.bind,Option.bind]

theorem contextUnavailable {sha policyRaw stateRaw apc config proof profile permission inputs}
    (h : NativePlanCoefficients.bind sha policyRaw stateRaw apc config proof profile = none) :
    NativeVectorContext.bind sha policyRaw stateRaw apc config proof profile permission inputs = none := by
  simp only [NativeVectorContext.bind,corpusUnavailable h,Bind.bind,Option.bind]

theorem runUnavailable {codec store trust anchor}
    (binding : NativeBinding.Binding codec trust anchor store)
    {sha policyRaw stateRaw apc config proof profile permission inputs domain index}
    (h : NativePlanCoefficients.bind sha policyRaw stateRaw apc config proof profile = none) :
    NativeVectorJoin.run binding sha policyRaw stateRaw apc config proof profile
      permission inputs domain index = none := by
  simp only [NativeVectorJoin.run,contextUnavailable h,Bind.bind,Option.bind]

end DeltaReduce.NativeSourceRefusal
