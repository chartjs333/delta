import ProfileEligibility
import DeltaReduce.NativePlanLineage

/-! T047/T053. Whole original APC payloads and references over successor ISC b.
The existing native Coverage and parent checks are reused exactly. This byte
join does not assert robust-plan computation, signature authority or origin. -/
namespace DeltaReduce.ProfileSource.Plan
open NativeReceiptBytes NativePolicyCodec
open NativePlanLineage (Mode)
open NativePlan (Certificate)
open InputSection (Located)

def bytes (sigma : Bytes) (mode : Mode) (c : Certificate) : Bytes :=
  match mode with
  | .proposed => NativePlan.bodyBytes c.common
  | .finalized => NativeIscCertificate.object (Lineage.semanticFields sigma (NativePlan.fields c))
def domain : Mode → Bytes
  | .proposed => NativePlan.bodyDomain
  | .finalized => NativePlan.domain

def ParentChecks (prior : Eligibility.Bound) (required : Bytes) (c : Certificate)
    (parent : Located ISCSourceV2.BoundCertificate) (ec : Located Eligibility.Edge)
    (seed : Located Lineage.Seed) : Prop :=
  parent.value.consensusId ∈ prior.lineage.inputs.finalized ∧
  ec.value.id ∈ prior.finalized ∧ ec.value.seedId = seed.value.id ∧
  c.common.isc = parent.value.consensusId ∧ c.common.ec = ec.value.id ∧
  c.common.seed = seed.value.id ∧ c.common.accumulator = required ∧
  NativePlan.Coverage c.common ec.value.certificate
instance (prior required c parent ec seed) :
    Decidable (ParentChecks prior required c parent ec seed) := by
  unfold ParentChecks; infer_instance

structure Edge where
  certificate : Certificate
  id : Bytes
  parent : Located ISCSourceV2.BoundCertificate
  ec : Located Eligibility.Edge
  seed : Located Lineage.Seed

def bind (sha : Bytes → Bytes) (sigma : Bytes) (mode : Mode)
    (expected : NativeInputSetBody.Context) (committee : List Bytes)
    (prior : Eligibility.Bound) (required : Bytes) (tree : Value) (raw : Bytes) : Option Edge := do
  let c ← NativePlanLineage.decode mode committee tree
  let parent ← prior.lineage.inputs.certificates.find? (fun x => x.value.consensusId == c.common.isc)
  let ec ← prior.certificates.find? (fun x => x.value.id == c.common.ec)
  let seed ← prior.lineage.seeds.find? (fun x => x.value.id == c.common.seed)
  if NativeVoteBytes.ContentId sigma ∧ NativePlan.Valid expected committee c ∧
      ParentChecks prior required c parent ec seed ∧ raw = bytes sigma mode c then
    let id ← NativeStateBytes.contentId sha (domain mode) raw
    some ⟨c,id,parent,ec,seed⟩
  else none

structure Source (sha : Bytes → Bytes) (sigma : Bytes) (mode : Mode)
    (expected : NativeInputSetBody.Context) (committee : List Bytes)
    (prior : Eligibility.Bound) (required : Bytes) (tree : Value) (raw : Bytes) (out : Edge) : Prop where
  decoded : NativePlanLineage.decode mode committee tree = some out.certificate
  parent : prior.lineage.inputs.certificates.find? (fun x =>
    x.value.consensusId == out.certificate.common.isc) = some out.parent
  ec : prior.certificates.find? (fun x => x.value.id == out.certificate.common.ec) = some out.ec
  seed : prior.lineage.seeds.find? (fun x => x.value.id == out.certificate.common.seed) = some out.seed
  semantic : NativeVoteBytes.ContentId sigma
  valid : NativePlan.Valid expected committee out.certificate
  links : ParentChecks prior required out.certificate out.parent out.ec out.seed
  originalBytes : raw = bytes sigma mode out.certificate
  identity : NativeStateBytes.contentId sha (domain mode) raw = some out.id

theorem boundSource {sha sigma mode expected committee prior required tree raw out}
    (ok : bind sha sigma mode expected committee prior required tree raw = some out) :
    Source sha sigma mode expected committee prior required tree raw out := by
  unfold bind at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨c,hc,parent,hp,ec,he,seed,hs,last⟩ := ok
  split at last <;> try contradiction
  rename_i checks
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨id,hi,last⟩ := last
  cases Option.some.inj last
  exact ⟨hc,hp,he,hs,checks.1,checks.2.1,checks.2.2.1,checks.2.2.2,hi⟩

theorem boundComplete {sha sigma mode expected committee prior required tree raw out}
    (h : Source sha sigma mode expected committee prior required tree raw out) :
    bind sha sigma mode expected committee prior required tree raw = some out := by
  unfold bind
  rw [h.decoded]
  simp only [Bind.bind,Option.bind]
  rw [h.parent,h.ec,h.seed]
  dsimp only
  rw [if_pos ⟨h.semantic,h.valid,h.links,h.originalBytes⟩,h.identity]

theorem originalTree {sha sigma mode expected committee prior required tree raw out}
    (ok : bind sha sigma mode expected committee prior required tree raw = some out) :
    tree = NativePlanLineage.original mode out.certificate :=
  NativePlanLineage.decodedOriginal (boundSource ok).decoded

theorem originalParents {sha sigma mode expected committee prior required tree raw out}
    (ok : bind sha sigma mode expected committee prior required tree raw = some out) :
    out.parent ∈ prior.lineage.inputs.certificates ∧
    out.parent.value.consensusId = out.certificate.common.isc ∧
    out.ec ∈ prior.certificates ∧ out.ec.value.id = out.certificate.common.ec ∧
    out.seed ∈ prior.lineage.seeds ∧ out.seed.value.id = out.certificate.common.seed := by
  have h := boundSource ok
  exact ⟨List.mem_of_find?_eq_some h.parent,by simpa using List.find?_some h.parent,
    List.mem_of_find?_eq_some h.ec,by simpa using List.find?_some h.ec,
    List.mem_of_find?_eq_some h.seed,by simpa using List.find?_some h.seed⟩

theorem coverageOriginal {sha sigma mode expected committee prior required tree raw out}
    (ok : bind sha sigma mode expected committee prior required tree raw = some out) :
    NativePlan.acceptedTickets out.ec.value.certificate =
      out.certificate.common.buckets.map NativePlan.Bucket.ticket ∧
    NativePlan.acceptedTickets out.ec.value.certificate =
      out.certificate.common.weights.map NativePlan.Weight.ticket := by
  have h := boundSource ok
  exact NativePlan.originalCoverage h.valid.1 h.links.2.2.2.2.2.2.2

structure Bound where
  required : Bytes
  bodies : List (Located Edge)
  certificates : List (Located Edge)
  finalized : List Bytes

def Sets (out : Bound) : Prop :=
  ((out.bodies ≠ [] ∨ out.certificates ≠ []) → NativeVoteBytes.ContentId out.required) ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (out.bodies.map (fun x => x.value.id)) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (out.certificates.map (fun x => x.value.id)) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT out.finalized = true ∧
  ∀ id ∈ out.finalized, id ∈ out.certificates.map (fun x => x.value.id)
instance (out) : Decidable (Sets out) := by unfold Sets; infer_instance

/-- `prior` is joined to the same original policy by the enclosing composition;
this function consumes all APC collections, not a caller-selected singleton. -/
def bindCollections (sha : Bytes → Bytes) (sigma : Bytes) (expected : NativeInputSetBody.Context)
    (p : NativePolicyBytes.Policy) (prior : Eligibility.Bound) (bodyRaws certificateRaws : List Bytes) :
    Option Bound := do
  let required ← lookup NativeHeader.snapshotFormat p.snapshot "required_accumulator_proof_id" >>= NativePolicyBytes.text
  let bt ← InputSection.trees p "aggregation_plan_bodies"
  let bodies ← InputSection.collect (bind sha sigma .proposed expected p.validators prior required) bt bodyRaws
  let ct ← InputSection.trees p "aggregation_plan_certificates"
  let certificates ← InputSection.collect (bind sha sigma .finalized expected p.validators prior required) ct certificateRaws
  let finalized ← InputSection.ids p "finalized_aggregation_plan_ids"
  let out := Bound.mk required bodies certificates finalized
  if Sets out then some out else none

structure CollectionSource (sha : Bytes → Bytes) (sigma : Bytes) (expected : NativeInputSetBody.Context)
    (p : NativePolicyBytes.Policy) (prior : Eligibility.Bound) (bodyRaws certificateRaws : List Bytes)
    (out : Bound) : Prop where
  required : (lookup NativeHeader.snapshotFormat p.snapshot "required_accumulator_proof_id" >>= NativePolicyBytes.text) = some out.required
  bodyTrees : InputSection.trees p "aggregation_plan_bodies" = some (out.bodies.map Located.tree)
  bodyBytes : out.bodies.map Located.raw = bodyRaws
  bodies : ∀ row ∈ out.bodies, bind sha sigma .proposed expected p.validators prior out.required row.tree row.raw = some row.value
  certificateTrees : InputSection.trees p "aggregation_plan_certificates" = some (out.certificates.map Located.tree)
  certificateBytes : out.certificates.map Located.raw = certificateRaws
  certificates : ∀ row ∈ out.certificates, bind sha sigma .finalized expected p.validators prior out.required row.tree row.raw = some row.value
  finalized : InputSection.ids p "finalized_aggregation_plan_ids" = some out.finalized
  sets : Sets out

theorem collectionsSource {sha sigma expected p prior bodyRaws certificateRaws out}
    (ok : bindCollections sha sigma expected p prior bodyRaws certificateRaws = some out) :
    CollectionSource sha sigma expected p prior bodyRaws certificateRaws out := by
  unfold bindCollections at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨required,hr,bt,hbt,bodies,hb,ct,hct,certificates,hc,finalized,hf,last⟩ := ok
  split at last <;> try contradiction
  rename_i sets
  cases Option.some.inj last
  have bs := InputSection.collectedOriginals hb
  have cs := InputSection.collectedOriginals hc
  exact ⟨by simpa only [Bind.bind,Option.bind_eq_some_iff] using hr,
    by simpa only [bs.1] using hbt,bs.2,InputSection.collectedEach hb,
    by simpa only [cs.1] using hct,cs.2,InputSection.collectedEach hc,hf,sets⟩

theorem collectionsComplete {sha sigma expected p prior bodyRaws certificateRaws out}
    (h : CollectionSource sha sigma expected p prior bodyRaws certificateRaws out) :
    bindCollections sha sigma expected p prior bodyRaws certificateRaws = some out := by
  unfold bindCollections
  rw [h.required,h.bodyTrees,← h.bodyBytes]
  simp only [InputSection.collectComplete out.bodies h.bodies,Bind.bind,Option.bind]
  rw [h.certificateTrees,← h.certificateBytes]
  simp only [InputSection.collectComplete out.certificates h.certificates]
  rw [h.finalized]
  exact if_pos h.sets

theorem finalizedWitness {sha sigma expected p prior bodyRaws certificateRaws out id}
    (ok : bindCollections sha sigma expected p prior bodyRaws certificateRaws = some out)
    (member : id ∈ out.finalized) :
    ∃ row ∈ out.certificates, row.value.id = id ∧
      Source sha sigma .finalized expected p.validators prior out.required row.tree row.raw row.value := by
  have h := collectionsSource ok
  obtain ⟨row,mem,eq⟩ := List.mem_map.mp (h.sets.2.2.2.2 id member)
  exact ⟨row,mem,eq,boundSource (h.certificates row mem)⟩

end DeltaReduce.ProfileSource.Plan
