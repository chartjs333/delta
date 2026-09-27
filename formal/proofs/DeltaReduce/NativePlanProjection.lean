import DeltaReduce.NativePlanAssignments

/-! Full computed PLAN/APC payloads from original prepared assignments and the
complete ISC graph. The APPLY profile reference is an explicit external boundary;
no profile preimage or original-profile identity is manufactured. -/
namespace DeltaReduce.NativePlanProjection
open NativeBinding
open NativeVectorContext (Bound)
open NativeVectorArtifacts (Artifact pack)
open NativePlanAssignments (AssignmentRow assignment nativeKey)
open NativeIscProjection (encodeRef Stored)

def encodeFraction (r : Rational) : Bytes :=
  arrayBytes ([r.numerator,r.denominator].map (asciiBytes ∘ toString))

def encodeContribution (c : Contribution) : Bytes :=
  asciiBytes "{\"q\":" ++ encodeRef "Q_SHARD" c.q ++
  asciiBytes ",\"ticket\":" ++ quotedBytes (asciiBytes c.ticket) ++
  asciiBytes ",\"weight\":" ++ encodeFraction c.weight ++ [125]

def encodeAssignment (a : Assignment) : Bytes :=
  asciiBytes "{\"context\":" ++ quotedBytes (asciiBytes a.context) ++
  asciiBytes ",\"contributions\":" ++ arrayBytes (a.contributions.map encodeContribution) ++
  asciiBytes ",\"denominator\":" ++ asciiBytes (toString a.denominator) ++
  asciiBytes ",\"domain\":" ++ quotedBytes (asciiBytes a.domain) ++
  asciiBytes ",\"quantum\":" ++ encodeFraction a.quantum ++
  asciiBytes ",\"shard\":" ++ quotedBytes (asciiBytes a.shard) ++ [125]

def encodeTicket (t : Ticket) : Bytes :=
  asciiBytes "{\"domain\":" ++ quotedBytes (asciiBytes t.domain) ++
  asciiBytes ",\"id\":" ++ quotedBytes (asciiBytes t.id) ++ [125]

def encodePlan (p : Plan) : Bytes :=
  asciiBytes "{\"kind\":\"PLAN\",\"payload\":{\"assignments\":" ++
  arrayBytes (p.assignments.map encodeAssignment) ++ asciiBytes ",\"profile\":" ++
  encodeRef "PROFILE" p.profile ++ asciiBytes ",\"schema\":" ++ encodeRef "SCHEMA" p.schema ++
  asciiBytes ",\"tickets\":" ++ arrayBytes (p.tickets.map encodeTicket) ++ [125,125]

def encodeApc (ec plan : Ref) : Bytes :=
  asciiBytes "{\"kind\":\"APC_PROJECTION\",\"payload\":{\"ec\":" ++
  encodeRef "EC_PROJECTION" ec ++ asciiBytes ",\"plan\":" ++ encodeRef "PLAN" plan ++ [125,125]

def value (b : Bound) (profile : Ref) (isc : NativeIscProjection.Image) (rs : List AssignmentRow) : Plan :=
  ⟨isc.schema.ref,profile,NativeVectorAuthority.tickets b,rs.map (assignment b)⟩

def ProfileRefValid (profile : Ref) : Prop :=
  profile.kind = .profile ∧ profile.id.length = 32 ∧ 0 < profile.length ∧ profile.length ≤ 4194304
instance (p) : Decidable (ProfileRefValid p) := by unfold ProfileRefValid; infer_instance

def Coverage (b : Bound) (sec : NativeParameterSection.Bound) (rs : List AssignmentRow) : Prop :=
  (rs.map (fun r => NativeParameterLineage.asBody r.original)).Perm
    ((NativeVectorAuthority.selectedBodies b sec).map NativeParameterLineage.asBody)
instance (b s rs) : Decidable (Coverage b s rs) := by unfold Coverage; infer_instance

structure Image where
  isc : NativeIscProjection.Image
  native : NativeSizedParameterSection.Bound
  assignments : List AssignmentRow
  plan : Artifact
  apc : Artifact

def construct (sha : Bytes → Bytes) (codec : Codec) (store : Store) (b : Bound)
    (permission : NativeAvailableQ.Permission) (inputs : List NativeAvailableQ.Input)
    (profile : Ref) : Option Image := do
  if ProfileRefValid profile then
    let isc ← NativeIscProjection.check sha codec store b permission inputs
    let native ← NativeSizedParameterSection.bindSection sha (NativeVectorAuthority.policy b) (NativeVectorAuthority.state b)
    if (NativeVectorArithmetic.keys b).map nativeKey = native.prior.keys then
      let rows ← NativePlanAssignments.loadAssignments b isc native.prior (NativeVectorArithmetic.keys b)
      if Coverage b native.prior rows then
        let plan ← pack codec.hash (encodePlan (value b profile isc rows)) (.plan (value b profile isc rows))
        let apc ← pack codec.hash (encodeApc isc.ec.ref plan.ref) (.apc isc.ec.ref plan.ref)
        some ⟨isc,native,rows,plan,apc⟩
      else none
    else none
  else none

structure Source (sha : Bytes → Bytes) (codec : Codec) (store : Store) (b : Bound)
    (permission : NativeAvailableQ.Permission) (inputs : List NativeAvailableQ.Input)
    (profile : Ref) (out : Image) : Prop where
  profileShape : ProfileRefValid profile
  isc : NativeIscProjection.check sha codec store b permission inputs = some out.isc
  native : NativeSizedParameterSection.bindSection sha (NativeVectorAuthority.policy b)
    (NativeVectorAuthority.state b) = some out.native
  matrix : (NativeVectorArithmetic.keys b).map nativeKey = out.native.prior.keys
  rows : NativePlanAssignments.loadAssignments b out.isc out.native.prior (NativeVectorArithmetic.keys b)
    = some out.assignments
  coverage : Coverage b out.native.prior out.assignments
  plan : pack codec.hash (encodePlan (value b profile out.isc out.assignments))
    (.plan (value b profile out.isc out.assignments)) = some out.plan
  apc : pack codec.hash (encodeApc out.isc.ec.ref out.plan.ref) (.apc out.isc.ec.ref out.plan.ref) = some out.apc

theorem constructed {sha codec store b permission inputs profile out}
    (h : construct sha codec store b permission inputs profile = some out) :
    Source sha codec store b permission inputs profile out := by
  unfold construct at h
  split at h <;> try contradiction
  rename_i profileValid
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨isc,hi,native,hn,last⟩ := h
  split at last <;> try contradiction
  rename_i matrix
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨rs,hr,last⟩ := last
  split at last <;> try contradiction
  rename_i coverage
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨plan,hp,apc,ha,last⟩ := last
  cases Option.some.inj last
  exact ⟨profileValid,hi,hn,matrix,hr,coverage,hp,ha⟩

theorem constructFromSource {sha codec store b permission inputs profile out}
    (h : Source sha codec store b permission inputs profile out) :
    construct sha codec store b permission inputs profile = some out := by
  cases out
  simp only [construct,if_pos h.profileShape,h.isc,h.native,bind,Option.bind,
    if_pos h.matrix,h.rows,if_pos h.coverage,h.plan,h.apc]

theorem originalMatrix {sha codec store b permission inputs profile out}
    (h : construct sha codec store b permission inputs profile = some out) :
    out.assignments.map AssignmentRow.key = NativeVectorArithmetic.keys b ∧
    (out.assignments.map (fun r => nativeKey r.key)) = out.native.prior.keys := by
  have keys := NativePlanAssignments.allKeys (constructed h).rows
  exact ⟨keys,by rw [← (constructed h).matrix,← keys,List.map_map]; rfl⟩

theorem originalBodyCoverage {sha codec store b permission inputs profile out}
    (h : construct sha codec store b permission inputs profile = some out) :
    (out.assignments.map (fun r => NativeParameterLineage.asBody r.original)).Perm
      ((NativeVectorAuthority.selectedBodies b out.native.prior).map NativeParameterLineage.asBody) :=
  (constructed h).coverage

theorem actualAssignment {sha codec store b permission inputs profile out}
    (h : construct sha codec store b permission inputs profile = some out)
    {n : Nat} {r} (position : out.assignments[n]? = some r) :
    ∃ k, (NativeVectorArithmetic.keys b)[n]? = some k ∧
      NativePlanAssignments.AssignmentSource b out.isc out.native.prior k r := by
  obtain ⟨k,hk,hr⟩ := NativePlanAssignments.assignmentAt (constructed h).rows position
  exact ⟨k,hk,NativePlanAssignments.assignmentSource hr⟩

theorem originalProposedPayload {sha codec store b permission inputs profile out}
    (h : construct sha codec store b permission inputs profile = some out)
    {n : Nat} {r} (position : out.assignments[n]? = some r) :
    r.original.source = NativeParameter.bodyValue (NativeParameterLineage.asBody r.original) := by
  obtain ⟨k,_,src⟩ := actualAssignment h position
  have loaded := NativePlanAssignments.assignmentFromSource src
  exact NativeParameterLineage.originalRetained
    (NativeParameterSection.proposedChecked (NativeSizedParameterSection.checkedSource (constructed h).native).1
      (NativePlanAssignments.originalPrepared loaded))

theorem nativeSizeBound {sha codec store b permission inputs profile out}
    (h : construct sha codec store b permission inputs profile = some out)
    {row} (member : row ∈ NativeSizedParameterSection.rows out.native.prior) :
    row.payload.length ≤ NativeContractSize.maxBytes :=
  NativeSizedParameterSection.everyCertificateBound (constructed h).native member

theorem completePayloads {sha codec store b permission inputs profile out}
    (h : construct sha codec store b permission inputs profile = some out) :
    out.plan.raw = encodePlan (value b profile out.isc out.assignments) ∧
    out.plan.payload = .plan (value b profile out.isc out.assignments) ∧
    out.apc.raw = encodeApc out.isc.ec.ref out.plan.ref ∧
    out.apc.payload = .apc out.isc.ec.ref out.plan.ref := by
  have p := NativeVectorArtifacts.packed (constructed h).plan
  have a := NativeVectorArtifacts.packed (constructed h).apc
  exact ⟨p.1,p.2.1,a.1,a.2.1⟩

theorem profileNotInvented (b profile isc rs) :
    (value b profile isc rs).profile = profile ∧
    (value b profile isc rs).tickets = NativeVectorAuthority.tickets b := ⟨rfl,rfl⟩

def check (sha : Bytes → Bytes) (codec : Codec) (store : Store) (b : Bound)
    (permission : NativeAvailableQ.Permission) (inputs : List NativeAvailableQ.Input) (profile : Ref) := do
  let out ← construct sha codec store b permission inputs profile
  if Stored codec store out.plan ∧ Stored codec store out.apc then some out else none

theorem checked {sha codec store b permission inputs profile out}
    (h : check sha codec store b permission inputs profile = some out) :
    construct sha codec store b permission inputs profile = some out ∧
    Stored codec store out.plan ∧ Stored codec store out.apc := by
  simp only [check,bind,Option.bind_eq_some_iff] at h
  obtain ⟨o,ho,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨ho,by assumption⟩

theorem planResolved {sha codec store b permission inputs profile out}
    (h : check sha codec store b permission inputs profile = some out) :
    Resolves codec store out.plan.ref out.plan.raw (.plan (value b profile out.isc out.assignments)) := by
  have r := NativeIscProjection.storedResolves (checked h).2.1
  rw [(completePayloads (checked h).1).2.1] at r
  exact r

theorem apcResolved {sha codec store b permission inputs profile out}
    (h : check sha codec store b permission inputs profile = some out) :
    Resolves codec store out.apc.ref out.apc.raw (.apc out.isc.ec.ref out.plan.ref) := by
  have r := NativeIscProjection.storedResolves (checked h).2.2
  rw [(completePayloads (checked h).1).2.2.2] at r
  exact r

theorem schemaResolved {sha codec store b permission inputs profile out}
    (h : check sha codec store b permission inputs profile = some out) :
    Resolves codec store out.isc.schema.ref out.isc.schema.raw
      (.schema out.isc.layout.coordinates out.isc.layout.shards) := by
  have isc := NativeIscProjection.checked (constructed (checked h).1).isc
  have r := NativeIscProjection.storedResolves (isc.2 out.isc.schema (by simp [NativeIscProjection.artifacts]))
  rw [(NativeVectorArtifacts.schemaEncoded (NativeIscProjection.constructed isc.1).schema).2.1] at r
  exact r

def FrameChecks {codec store trust anchor} (binding : Binding codec trust anchor store)
    (b : Bound) (frame : ParameterFrame) (out : Image) : Prop :=
  NativeIscProjection.FrameChecks binding frame out.isc ∧
  binding.authority.plan = out.plan.ref ∧ binding.authority.apc = out.apc.ref ∧
  frame.plan = value b binding.authority.profile out.isc out.assignments ∧
  frame.apcEc = out.isc.ec.ref ∧ frame.apcPlan = out.plan.ref ∧
  frame.coordinates = out.isc.layout.coordinates ∧ frame.shards = out.isc.layout.shards
instance {codec store trust anchor} (binding : Binding codec trust anchor store) (b f out) :
    Decidable (FrameChecks binding b f out) := by unfold FrameChecks; infer_instance

def join {codec store trust anchor} (binding : Binding codec trust anchor store)
    (sha : Bytes → Bytes) (b : Bound) (permission : NativeAvailableQ.Permission)
    (inputs : List NativeAvailableQ.Input) (domain : Bytes) (index : Nat) := do
  let verified ← NativeVectorAuthority.verify binding sha b domain index
  let out ← check sha codec store b permission inputs binding.authority.profile
  if FrameChecks binding b verified.computation.native.frame out then some (verified,out) else none

theorem joined {codec store trust anchor binding sha b permission inputs domain index verified out}
    (h : @join codec store trust anchor binding sha b permission inputs domain index = some (verified,out)) :
    NativeVectorAuthority.verify binding sha b domain index = some verified ∧
    check sha codec store b permission inputs binding.authority.profile = some out ∧
    FrameChecks binding b verified.computation.native.frame out := by
  simp only [join,bind,Option.bind_eq_some_iff] at h
  obtain ⟨v,hv,o,ho,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨hv,ho,by assumption⟩

theorem joinedPlanOrigin {codec store trust anchor binding sha b permission inputs domain index verified out}
    (h : @join codec store trust anchor binding sha b permission inputs domain index = some (verified,out)) :
    Resolves codec store binding.authority.plan out.plan.raw (.plan verified.computation.native.frame.plan) := by
  have src := joined h
  rw [src.2.2.2.1,src.2.2.2.2.2.1]
  exact planResolved src.2.1

theorem joinedApcOrigin {codec store trust anchor binding sha b permission inputs domain index verified out}
    (h : @join codec store trust anchor binding sha b permission inputs domain index = some (verified,out)) :
    Resolves codec store binding.authority.apc out.apc.raw
      (.apc verified.computation.native.frame.apcEc verified.computation.native.frame.apcPlan) := by
  have src := joined h
  rw [src.2.2.2.2.1,src.2.2.2.2.2.2.1,src.2.2.2.2.2.2.2.1]
  exact apcResolved src.2.1

theorem joinedFrameOrigin {codec store trust anchor binding sha b permission inputs domain index verified out}
    (h : @join codec store trust anchor binding sha b permission inputs domain index = some (verified,out)) :
    FrameOrigin codec store binding.authority verified.computation.native.frame := by
  have src := joined h
  rcases src.2.2 with ⟨iscFrame,planId,apcId,planValue,apcEc,apcPlan,coords,shards⟩
  rcases iscFrame with ⟨schemaId,iscId,ecId,members,commitments,ecIsc,eligible⟩
  have isc := (constructed (checked src.2.1).1).isc
  refine ⟨⟨out.isc.schema.raw,?_⟩,⟨out.plan.raw,joinedPlanOrigin h⟩,
    ⟨out.isc.isc.raw,?_⟩,⟨out.isc.ec.raw,?_⟩,⟨out.apc.raw,joinedApcOrigin h⟩⟩
  · rw [schemaId,coords,shards]; exact schemaResolved src.2.1
  · rw [iscId,members,commitments]; exact NativeIscProjection.iscResolved isc
  · rw [ecId,ecIsc,eligible]; exact NativeIscProjection.ecResolved isc

def run {codec store trust anchor} (binding : Binding codec trust anchor store)
    (sha : Bytes → Bytes) (policyRaw stateRaw apcId configRaw proofRaw profileRaw : Bytes)
    (permission : NativeAvailableQ.Permission) (eligibleInputs allInputs : List NativeAvailableQ.Input)
    (domain : Bytes) (index : Nat) := do
  let b ← NativeVectorContext.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission eligibleInputs
  let (verified,out) ← join binding sha b permission allInputs domain index
  some ((⟨b,verified⟩ : (b : Bound) × NativeVectorAuthority.Verified binding b domain index),out)

theorem runSource {codec store trust anchor binding sha policyRaw stateRaw apcId configRaw proofRaw profileRaw
    permission eligibleInputs allInputs domain index b verified out}
    (h : @run codec store trust anchor binding sha policyRaw stateRaw apcId configRaw proofRaw profileRaw
      permission eligibleInputs allInputs domain index = some (⟨b,verified⟩,out)) :
    NativeVectorContext.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission eligibleInputs = some b ∧
    join binding sha b permission allInputs domain index = some (verified,out) := by
  simp only [run,bind,Option.bind_eq_some_iff] at h
  obtain ⟨b',hb,⟨v,o⟩,hj,last⟩ := h
  cases Option.some.inj last
  exact ⟨hb,hj⟩

end DeltaReduce.NativePlanProjection
