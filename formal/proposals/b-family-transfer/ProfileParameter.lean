import ProfilePlan
import DeltaReduce.NativeParameterLineage
import DeltaReduce.NativeContractSize

/-! T047/T053. Original whole vector PARAMETER objects, with the approved b
reference and existing native assignment guards. Coordinate projections never
create another protocol object. Arithmetic computation and producer origin
are not inferred from these exact byte/lineage checks. -/
namespace DeltaReduce.ProfileSource.Parameter
open NativeReceiptBytes NativePolicyCodec
open NativeParameterLineage (Mode)
open NativeParameter (Certificate Key)
open InputSection (Located)

def bytes (sigma : Bytes) (mode : Mode) (c : Certificate) (ctx : Bytes) : Bytes :=
  match mode with
  | .proposed => NativeParameter.bodyBytes ⟨c.common,ctx⟩
  | .finalized => NativeIscCertificate.object (Lineage.semanticFields sigma (NativeParameter.fields c))
def domain : Mode → Bytes
  | .proposed => NativeParameter.bodyDomain
  | .finalized => NativeParameter.domain

def ProposedChecks (keys : List Key) (c : NativeParameter.Common) (ctx : Bytes)
    (parent : Located ISCSourceV2.BoundCertificate) (ec : Located Eligibility.Edge)
    (plan : Located Plan.Edge) : Prop :=
  ctx ≠ [] ∧ plan.value.certificate.common.isc = parent.value.consensusId ∧
  plan.value.certificate.common.ec = ec.value.id ∧ ⟨c.domain,c.shard⟩ ∈ keys ∧
  ∃ e ∈ ec.value.certificate.common.entries, e.accepted ≠ 0 ∧ e.domain = c.domain
instance (keys c ctx parent ec plan) : Decidable (ProposedChecks keys c ctx parent ec plan) := by
  unfold ProposedChecks; infer_instance

def ParentChecks (mode : Mode) (ecSection : Eligibility.Bound) (planSection : Plan.Bound)
    (keys : List Key) (c : Certificate) (ctx : Bytes)
    (parent : Located ISCSourceV2.BoundCertificate) (ec : Located Eligibility.Edge)
    (plan : Located Plan.Edge) : Prop :=
  parent.value.consensusId ∈ ecSection.lineage.inputs.finalized ∧
  ec.value.id ∈ ecSection.finalized ∧ plan.value.id ∈ planSection.finalized ∧
  c.common.isc = parent.value.consensusId ∧ c.common.ec = ec.value.id ∧
  c.common.plan = plan.value.id ∧
  (mode = .proposed → ProposedChecks keys c.common ctx parent ec plan)
instance (mode ecSection planSection keys c ctx parent ec plan) :
    Decidable (ParentChecks mode ecSection planSection keys c ctx parent ec plan) := by
  unfold ParentChecks; infer_instance

structure Edge where
  certificate : Certificate
  voteContext : Bytes
  id : Bytes
  parent : Located ISCSourceV2.BoundCertificate
  ec : Located Eligibility.Edge
  plan : Located Plan.Edge

def bind (sha : Bytes → Bytes) (sigma : Bytes) (mode : Mode)
    (expected : NativeInputSetBody.Context) (committee : List Bytes)
    (ecSection : Eligibility.Bound) (planSection : Plan.Bound) (keys : List Key)
    (tree : Value) (raw : Bytes) : Option Edge := do
  let (c,ctx) ← NativeParameterLineage.decode mode committee tree
  let parent ← ecSection.lineage.inputs.certificates.find? (fun x => x.value.consensusId == c.common.isc)
  let ec ← ecSection.certificates.find? (fun x => x.value.id == c.common.ec)
  let plan ← planSection.certificates.find? (fun x => x.value.id == c.common.plan)
  if NativeVoteBytes.ContentId sigma ∧ NativeParameter.Valid expected committee c ∧
      ParentChecks mode ecSection planSection keys c ctx parent ec plan ∧
      raw = bytes sigma mode c ctx then
    let id ← NativeStateBytes.contentId sha (domain mode) raw
    some ⟨c,ctx,id,parent,ec,plan⟩
  else none

structure Source (sha : Bytes → Bytes) (sigma : Bytes) (mode : Mode)
    (expected : NativeInputSetBody.Context) (committee : List Bytes)
    (ecSection : Eligibility.Bound) (planSection : Plan.Bound) (keys : List Key)
    (tree : Value) (raw : Bytes) (out : Edge) : Prop where
  decoded : NativeParameterLineage.decode mode committee tree = some (out.certificate,out.voteContext)
  parent : ecSection.lineage.inputs.certificates.find? (fun x =>
    x.value.consensusId == out.certificate.common.isc) = some out.parent
  ec : ecSection.certificates.find? (fun x => x.value.id == out.certificate.common.ec) = some out.ec
  plan : planSection.certificates.find? (fun x => x.value.id == out.certificate.common.plan) = some out.plan
  semantic : NativeVoteBytes.ContentId sigma
  valid : NativeParameter.Valid expected committee out.certificate
  links : ParentChecks mode ecSection planSection keys out.certificate out.voteContext out.parent out.ec out.plan
  originalBytes : raw = bytes sigma mode out.certificate out.voteContext
  identity : NativeStateBytes.contentId sha (domain mode) raw = some out.id

theorem boundSource {sha sigma mode expected committee ecSection planSection keys tree raw out}
    (ok : bind sha sigma mode expected committee ecSection planSection keys tree raw = some out) :
    Source sha sigma mode expected committee ecSection planSection keys tree raw out := by
  unfold bind at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨⟨c,ctx⟩,hc,parent,hp,ec,he,plan,ha,last⟩ := ok
  split at last <;> try contradiction
  rename_i checks
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨id,hi,last⟩ := last
  cases Option.some.inj last
  exact ⟨hc,hp,he,ha,checks.1,checks.2.1,checks.2.2.1,checks.2.2.2,hi⟩

theorem boundComplete {sha sigma mode expected committee ecSection planSection keys tree raw out}
    (h : Source sha sigma mode expected committee ecSection planSection keys tree raw out) :
    bind sha sigma mode expected committee ecSection planSection keys tree raw = some out := by
  unfold bind
  rw [h.decoded]
  simp only [Bind.bind,Option.bind]
  rw [h.parent,h.ec,h.plan]
  dsimp only
  rw [if_pos ⟨h.semantic,h.valid,h.links,h.originalBytes⟩,h.identity]

theorem originalTree {sha sigma mode expected committee ecSection planSection keys tree raw out}
    (ok : bind sha sigma mode expected committee ecSection planSection keys tree raw = some out) :
    tree = NativeParameterLineage.original mode out.certificate out.voteContext :=
  NativeParameterLineage.decodedOriginal (boundSource ok).decoded

theorem originalParents {sha sigma mode expected committee ecSection planSection keys tree raw out}
    (ok : bind sha sigma mode expected committee ecSection planSection keys tree raw = some out) :
    out.parent ∈ ecSection.lineage.inputs.certificates ∧
    out.parent.value.consensusId = out.certificate.common.isc ∧
    out.ec ∈ ecSection.certificates ∧ out.ec.value.id = out.certificate.common.ec ∧
    out.plan ∈ planSection.certificates ∧ out.plan.value.id = out.certificate.common.plan := by
  have h := boundSource ok
  exact ⟨List.mem_of_find?_eq_some h.parent,by simpa using List.find?_some h.parent,
    List.mem_of_find?_eq_some h.ec,by simpa using List.find?_some h.ec,
    List.mem_of_find?_eq_some h.plan,by simpa using List.find?_some h.plan⟩

theorem proposedAssignment {sha sigma expected committee ecSection planSection keys tree raw out}
    (ok : bind sha sigma .proposed expected committee ecSection planSection keys tree raw = some out) :
    ProposedChecks keys out.certificate.common out.voteContext out.parent out.ec out.plan :=
  (boundSource ok).links.2.2.2.2.2.2 rfl

def asBody (e : Edge) : NativeParameter.Body := ⟨e.certificate.common,e.voteContext⟩
structure Bound where
  keys : List Key
  bodies : List (Located Edge)
  certificates : List (Located Edge)
  finalized : List Bytes

def Sets (out : Bound) : Prop :=
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (out.bodies.map (fun x => x.value.id)) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (out.certificates.map (fun x => x.value.id)) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT out.finalized = true ∧
  (∀ id ∈ out.finalized, id ∈ out.certificates.map (fun x => x.value.id)) ∧
  NativePolicyBytes.strictly NativeParameter.keyLT out.keys = true ∧
  NativeParameter.assignments [] (out.bodies.map (fun x => asBody x.value)) = true
instance (out) : Decidable (Sets out) := by unfold Sets; infer_instance

def bindCollections (sha : Bytes → Bytes) (sigma : Bytes) (expected : NativeInputSetBody.Context)
    (p : NativePolicyBytes.Policy) (ec : Eligibility.Bound) (plan : Plan.Bound)
    (bodyRaws certificateRaws : List Bytes) : Option Bound := do
  let kt ← InputSection.trees p "required_parameter_keys"
  let keys ← NativeParameter.readKeys kt
  let bt ← InputSection.trees p "parameter_bodies"
  let bodies ← InputSection.collect (bind sha sigma .proposed expected p.validators ec plan keys) bt bodyRaws
  let ct ← InputSection.trees p "parameter_qcs"
  let certificates ← InputSection.collect (bind sha sigma .finalized expected p.validators ec plan keys) ct certificateRaws
  let finalized ← InputSection.ids p "finalized_parameter_ids"
  let out := Bound.mk keys bodies certificates finalized
  if Sets out then some out else none

structure CollectionSource (sha : Bytes → Bytes) (sigma : Bytes) (expected : NativeInputSetBody.Context)
    (p : NativePolicyBytes.Policy) (ec : Eligibility.Bound) (plan : Plan.Bound)
    (bodyRaws certificateRaws : List Bytes) (out : Bound) : Prop where
  keys : ∃ kt, InputSection.trees p "required_parameter_keys" = some kt ∧ NativeParameter.readKeys kt = some out.keys
  bodyTrees : InputSection.trees p "parameter_bodies" = some (out.bodies.map Located.tree)
  bodyBytes : out.bodies.map Located.raw = bodyRaws
  bodies : ∀ row ∈ out.bodies, bind sha sigma .proposed expected p.validators ec plan out.keys row.tree row.raw = some row.value
  certificateTrees : InputSection.trees p "parameter_qcs" = some (out.certificates.map Located.tree)
  certificateBytes : out.certificates.map Located.raw = certificateRaws
  certificates : ∀ row ∈ out.certificates, bind sha sigma .finalized expected p.validators ec plan out.keys row.tree row.raw = some row.value
  finalized : InputSection.ids p "finalized_parameter_ids" = some out.finalized
  sets : Sets out

theorem collectionsSource {sha sigma expected p ec plan bodyRaws certificateRaws out}
    (ok : bindCollections sha sigma expected p ec plan bodyRaws certificateRaws = some out) :
    CollectionSource sha sigma expected p ec plan bodyRaws certificateRaws out := by
  unfold bindCollections at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨kt,hkt,keys,hk,bt,hbt,bodies,hb,ct,hct,certificates,hc,finalized,hf,last⟩ := ok
  split at last <;> try contradiction
  rename_i sets
  cases Option.some.inj last
  have bs := InputSection.collectedOriginals hb
  have cs := InputSection.collectedOriginals hc
  exact ⟨⟨kt,hkt,hk⟩,by simpa only [bs.1] using hbt,bs.2,InputSection.collectedEach hb,
    by simpa only [cs.1] using hct,cs.2,InputSection.collectedEach hc,hf,sets⟩

theorem collectionsComplete {sha sigma expected p ec plan bodyRaws certificateRaws out}
    (h : CollectionSource sha sigma expected p ec plan bodyRaws certificateRaws out) :
    bindCollections sha sigma expected p ec plan bodyRaws certificateRaws = some out := by
  obtain ⟨kt,hkt,hk⟩ := h.keys
  unfold bindCollections
  rw [hkt]
  simp only [Bind.bind,Option.bind]
  rw [hk,h.bodyTrees,← h.bodyBytes]
  simp only [InputSection.collectComplete out.bodies h.bodies]
  rw [h.certificateTrees,← h.certificateBytes]
  simp only [InputSection.collectComplete out.certificates h.certificates]
  rw [h.finalized]
  exact if_pos h.sets

theorem assignmentIdentitiesRetained {sha sigma expected p ec plan bodyRaws certificateRaws out}
    (ok : bindCollections sha sigma expected p ec plan bodyRaws certificateRaws = some out) :
    (out.bodies.map (fun x => asBody x.value)).Pairwise (fun a b =>
      NativeParameter.assignmentKey a ≠ NativeParameter.assignmentKey b ∧ a.voteContext ≠ b.voteContext) :=
  NativeParameter.assignmentsDistinct (collectionsSource ok).sets.2.2.2.2.2

theorem noCoordinateObjects {sha sigma expected p ec plan bodyRaws certificateRaws out}
    (ok : bindCollections sha sigma expected p ec plan bodyRaws certificateRaws = some out) :
    out.bodies.length = bodyRaws.length ∧ out.certificates.length = certificateRaws.length := by
  have h := collectionsSource ok
  exact ⟨by simpa using congrArg List.length h.bodyBytes,
    by simpa using congrArg List.length h.certificateBytes⟩

def ecSizeRow (sigma : Bytes) (finalized : Bool) (x : Located Eligibility.Edge) : NativeContractSize.Row :=
  ⟨if finalized then "EC_FINAL" else "EC_PROPOSED",x.tree,NativeEligibility.domain,
    Eligibility.bytes sigma .finalized x.value.certificate x.value.seedId,
    if finalized then some x.value.id else none⟩
def planSizeRow (sigma : Bytes) (finalized : Bool) (x : Located Plan.Edge) : NativeContractSize.Row :=
  ⟨if finalized then "APC_FINAL" else "APC_PROPOSED",x.tree,NativePlan.domain,
    Plan.bytes sigma .finalized x.value.certificate,if finalized then some x.value.id else none⟩
def sizeRow (sigma : Bytes) (finalized : Bool) (x : Located Edge) : NativeContractSize.Row :=
  ⟨if finalized then "PARAMETER_FINAL" else "PARAMETER_PROPOSED",x.tree,NativeParameter.domain,
    bytes sigma .finalized x.value.certificate x.value.voteContext,
    if finalized then some x.value.id else none⟩

/-- Same nine original native contract-size groups, with successor bytes.
ISC expected identity is c, even though downstream references use b. -/
def sizeGroups (sigma : Bytes) (ec : Eligibility.Bound) (plan : Plan.Bound) (p : Bound) :
    List (List NativeContractSize.Row) :=
  [ec.lineage.inputs.certificates.map (fun x =>
     ⟨"ISC",x.tree,NativeVoteBytes.ascii "deltareduce.008.input-set-certificate.v2",
       x.raw,some x.value.witnessId⟩),
   ec.lineage.norms.map (fun x => ⟨"NORM",x.tree,NativeNormEvidence.domain,x.raw,some x.value.id⟩),
   ec.lineage.seeds.map (fun x => ⟨"SEED",x.tree,NativeSeedTranscript.domain,x.raw,some x.value.id⟩),
   ec.bodies.map (ecSizeRow sigma false),ec.certificates.map (ecSizeRow sigma true),
   plan.bodies.map (planSizeRow sigma false),plan.certificates.map (planSizeRow sigma true),
   p.bodies.map (sizeRow sigma false),p.certificates.map (sizeRow sigma true)]

def checkSizes (sha : Bytes → Bytes) (sigma : Bytes) (ec : Eligibility.Bound)
    (plan : Plan.Bound) (p : Bound) : Option (List NativeContractSize.Checked) :=
  NativeContractSize.checkAll sha (sizeGroups sigma ec plan p).flatten

theorem sizeGroupLengths (sigma ec plan p) :
    (sizeGroups sigma ec plan p).map List.length =
    [ec.lineage.inputs.certificates.length,ec.lineage.norms.length,ec.lineage.seeds.length,
     ec.bodies.length,ec.certificates.length,plan.bodies.length,plan.certificates.length,
     p.bodies.length,p.certificates.length] := by simp [sizeGroups]

theorem sizeRowsRetained {sha sigma ec plan p checked}
    (ok : checkSizes sha sigma ec plan p = some checked) :
    checked.map NativeContractSize.Checked.row = (sizeGroups sigma ec plan p).flatten :=
  NativeContractSize.allSources ok

theorem everyOriginalSizeBound {sha sigma ec plan p checked group row}
    (ok : checkSizes sha sigma ec plan p = some checked)
    (hg : group ∈ sizeGroups sigma ec plan p) (hr : row ∈ group) :
    row.payload.length ≤ NativeContractSize.maxBytes :=
  NativeContractSize.allBounds ok row (List.mem_flatten.mpr ⟨group,hg,hr⟩)

end DeltaReduce.ProfileSource.Parameter
