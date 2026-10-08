import ProfileParameter
import DeltaReduce.NativeAggregateLineage

/-! T047/T053. The whole original ROOT links ordered original PARAMETER QCs.
Successor serialization is used for every rehash; no legacy QC is relabeled.
This executes existing Merkle/coverage/size rules, not producer authority. -/
namespace DeltaReduce.ProfileSource.Aggregate
open NativeReceiptBytes NativePolicyCodec
open NativeAggregateRoot (Certificate Common)
open NativeAggregateMerkle (Leaf)
open NativeParameterLineage (Mode)
open InputSection (Located)

def json (sigma : Bytes) (c : Certificate) : Bytes :=
  NativeIscCertificate.object (Lineage.semanticFields sigma (NativeAggregateRoot.fields c))
def bytes (sigma : Bytes) (mode : Mode) (c : Certificate) : Bytes :=
  match mode with
  | .proposed => NativeAggregateRoot.bodyBytes c.common
  | .finalized => json sigma c
def certificateId (sha : Bytes → Bytes) (sigma : Bytes) (c : Certificate) : Option Bytes := do
  let merkle ← NativeAggregateMerkle.root sha c.common.leaves
  if merkle = c.common.merkle then
    NativeContractSize.contentId sha NativeAggregateRoot.domain (json sigma c)
  else none
def resultId (sha : Bytes → Bytes) (mode : Mode) (c : Certificate) (qc : Bytes) : Option Bytes :=
  match mode with
  | .proposed => NativeAggregateRoot.bodyId sha c.common
  | .finalized => some qc

def shardLeaf (e : Located Parameter.Edge) : Leaf :=
  ⟨e.value.certificate.common.domain,e.value.id,e.value.certificate.common.shard⟩
def ShardChecks (expected : NativeInputSetBody.Context) (committee finalized : List Bytes)
    (c : Common) (leaf : Leaf) (e : Located Parameter.Edge) : Prop :=
  e.value.id ∈ finalized ∧ shardLeaf e = leaf ∧
  NativeParameter.Valid expected committee e.value.certificate ∧
  e.value.certificate.common.isc = c.isc ∧ e.value.certificate.common.ec = c.ec ∧
  e.value.certificate.common.plan = c.plan
instance (expected committee finalized c leaf e) :
    Decidable (ShardChecks expected committee finalized c leaf e) := by
  unfold ShardChecks; infer_instance

def resolve (sha : Bytes → Bytes) (sigma : Bytes) (expected : NativeInputSetBody.Context)
    (committee : List Bytes) (parameters : Parameter.Bound) (c : Common) (leaf : Leaf) :
    Option (Located Parameter.Edge) := do
  let e ← parameters.certificates.find? (fun x => x.value.id == leaf.qc)
  if ShardChecks expected committee parameters.finalized c leaf e then
    let id ← NativeContractSize.contentId sha NativeParameter.domain
      (Parameter.bytes sigma .finalized e.value.certificate e.value.voteContext)
    if id = leaf.qc then some e else none
  else none

theorem resolvedSource {sha sigma expected committee parameters c leaf e}
    (ok : resolve sha sigma expected committee parameters c leaf = some e) :
    e ∈ parameters.certificates ∧ ShardChecks expected committee parameters.finalized c leaf e ∧
    NativeContractSize.contentId sha NativeParameter.domain
      (Parameter.bytes sigma .finalized e.value.certificate e.value.voteContext) = some leaf.qc := by
  unfold resolve at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨found,hf,last⟩ := ok
  split at last <;> try contradiction
  rename_i checks
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨id,hi,last⟩ := last
  split at last <;> try contradiction
  rename_i same
  cases Option.some.inj last
  subst id
  exact ⟨List.mem_of_find?_eq_some hf,checks,hi⟩

def resolveAll (sha : Bytes → Bytes) (sigma : Bytes) (expected : NativeInputSetBody.Context)
    (committee : List Bytes) (parameters : Parameter.Bound) (c : Common) :
    List Leaf → Option (List (Located Parameter.Edge))
  | [] => some []
  | leaf::tail => do
    let e ← resolve sha sigma expected committee parameters c leaf
    let rest ← resolveAll sha sigma expected committee parameters c tail
    some (e::rest)

theorem resolvedLeaves {sha sigma expected committee parameters c leaves out}
    (ok : resolveAll sha sigma expected committee parameters c leaves = some out) :
    out.map shardLeaf = leaves := by
  induction leaves generalizing out with
  | nil => cases Option.some.inj ok; rfl
  | cons leaf tail ih =>
    simp only [resolveAll,Bind.bind,Option.bind_eq_some_iff] at ok
    obtain ⟨e,he,rest,hr,last⟩ := ok
    cases Option.some.inj last
    simp only [List.map_cons,(resolvedSource he).2.1.2.1,ih hr]

theorem everyResolvedOriginal {sha sigma expected committee parameters c leaves out}
    (ok : resolveAll sha sigma expected committee parameters c leaves = some out)
    (e) (member : e ∈ out) : e ∈ parameters.certificates := by
  induction leaves generalizing out with
  | nil => cases Option.some.inj ok; simp at member
  | cons leaf tail ih =>
    simp only [resolveAll,Bind.bind,Option.bind_eq_some_iff] at ok
    obtain ⟨first,hf,rest,hr,last⟩ := ok
    cases Option.some.inj last
    rcases List.mem_cons.mp member with same | member
    · subst e; exact (resolvedSource hf).1
    · exact ih hr member

def ParentChecks (ec : Eligibility.Bound) (plan : Plan.Bound) (parameters : Parameter.Bound)
    (c : Common) (parent : Located ISCSourceV2.BoundCertificate)
    (ecRow : Located Eligibility.Edge) (planRow : Located Plan.Edge) : Prop :=
  parent.value.consensusId ∈ ec.lineage.inputs.finalized ∧ ecRow.value.id ∈ ec.finalized ∧
  planRow.value.id ∈ plan.finalized ∧ c.isc = parent.value.consensusId ∧
  c.ec = ecRow.value.id ∧ c.plan = planRow.value.id ∧ c.keys = parameters.keys ∧
  c.leaves.map NativeAggregateMerkle.key = parameters.keys
instance (ec plan parameters c parent ecRow planRow) :
    Decidable (ParentChecks ec plan parameters c parent ecRow planRow) := by
  unfold ParentChecks; infer_instance

structure Edge where
  certificate : Certificate
  id : Bytes
  qc : Bytes
  parent : Located ISCSourceV2.BoundCertificate
  ec : Located Eligibility.Edge
  plan : Located Plan.Edge
  shards : List (Located Parameter.Edge)

def bind (sha : Bytes → Bytes) (sigma : Bytes) (mode : Mode)
    (expected : NativeInputSetBody.Context) (committee : List Bytes)
    (ec : Eligibility.Bound) (plan : Plan.Bound) (parameters : Parameter.Bound)
    (tree : Value) (raw : Bytes) : Option Edge := do
  let c ← NativeAggregateLineage.decode mode committee tree
  let parent ← ec.lineage.inputs.certificates.find? (fun x => x.value.consensusId == c.common.isc)
  let ecRow ← ec.certificates.find? (fun x => x.value.id == c.common.ec)
  let planRow ← plan.certificates.find? (fun x => x.value.id == c.common.plan)
  if NativeVoteBytes.ContentId sigma ∧ NativeAggregateRoot.Valid expected committee c ∧
      ParentChecks ec plan parameters c.common parent ecRow planRow ∧ raw = bytes sigma mode c then
    let shards ← resolveAll sha sigma expected committee parameters c.common c.common.leaves
    let qc ← certificateId sha sigma c
    let id ← resultId sha mode c qc
    some ⟨c,id,qc,parent,ecRow,planRow,shards⟩
  else none

structure Source (sha : Bytes → Bytes) (sigma : Bytes) (mode : Mode)
    (expected : NativeInputSetBody.Context) (committee : List Bytes)
    (ec : Eligibility.Bound) (plan : Plan.Bound) (parameters : Parameter.Bound)
    (tree : Value) (raw : Bytes) (out : Edge) : Prop where
  decoded : NativeAggregateLineage.decode mode committee tree = some out.certificate
  parent : ec.lineage.inputs.certificates.find? (fun x =>
    x.value.consensusId == out.certificate.common.isc) = some out.parent
  ecLookup : ec.certificates.find? (fun x => x.value.id == out.certificate.common.ec) = some out.ec
  planLookup : plan.certificates.find? (fun x => x.value.id == out.certificate.common.plan) = some out.plan
  semantic : NativeVoteBytes.ContentId sigma
  valid : NativeAggregateRoot.Valid expected committee out.certificate
  links : ParentChecks ec plan parameters out.certificate.common out.parent out.ec out.plan
  originalBytes : raw = bytes sigma mode out.certificate
  shards : resolveAll sha sigma expected committee parameters out.certificate.common
    out.certificate.common.leaves = some out.shards
  qc : certificateId sha sigma out.certificate = some out.qc
  identity : resultId sha mode out.certificate out.qc = some out.id

theorem boundSource {sha sigma mode expected committee ec plan parameters tree raw out}
    (ok : bind sha sigma mode expected committee ec plan parameters tree raw = some out) :
    Source sha sigma mode expected committee ec plan parameters tree raw out := by
  unfold bind at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨c,hc,parent,hp,ecRow,he,planRow,ha,last⟩ := ok
  split at last <;> try contradiction
  rename_i checks
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨shards,hs,qc,hq,id,hi,last⟩ := last
  cases Option.some.inj last
  exact ⟨hc,hp,he,ha,checks.1,checks.2.1,checks.2.2.1,checks.2.2.2,hs,hq,hi⟩

theorem boundComplete {sha sigma mode expected committee ec plan parameters tree raw out}
    (h : Source sha sigma mode expected committee ec plan parameters tree raw out) :
    bind sha sigma mode expected committee ec plan parameters tree raw = some out := by
  unfold bind
  rw [h.decoded]
  simp only [Bind.bind,Option.bind]
  rw [h.parent,h.ecLookup,h.planLookup]
  dsimp only
  rw [if_pos ⟨h.semantic,h.valid,h.links,h.originalBytes⟩,h.shards]
  dsimp only
  rw [h.qc]
  dsimp only
  rw [h.identity]

theorem exactOriginalCoverage {sha sigma mode expected committee ec plan parameters tree raw out}
    (ok : bind sha sigma mode expected committee ec plan parameters tree raw = some out) :
    out.shards.map shardLeaf = out.certificate.common.leaves ∧
    out.certificate.common.keys = parameters.keys ∧
    out.certificate.common.leaves.map NativeAggregateMerkle.key = parameters.keys :=
  ⟨resolvedLeaves (boundSource ok).shards,(boundSource ok).links.2.2.2.2.2.2⟩

theorem checkedMerkleAndBytes {sha sigma c id}
    (ok : certificateId sha sigma c = some id) :
    NativeAggregateMerkle.root sha c.common.leaves = some c.common.merkle ∧
    (json sigma c).length ≤ NativeContractSize.maxBytes ∧
    NativeStateBytes.contentId sha NativeAggregateRoot.domain (json sigma c) = some id := by
  unfold certificateId at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨root,hr,last⟩ := ok
  split at last <;> try contradiction
  rename_i same
  subst root
  exact ⟨hr,NativeContractSize.accepted last⟩

structure Bound where
  sizes : List NativeContractSize.Checked
  bodies : List (Located Edge)
  certificates : List (Located Edge)
  finalized : List Bytes
def Sets (out : Bound) : Prop :=
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (out.bodies.map (fun x => x.value.id)) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (out.certificates.map (fun x => x.value.id)) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT out.finalized = true ∧
  ∀ id ∈ out.finalized, id ∈ out.certificates.map (fun x => x.value.id)
instance (out) : Decidable (Sets out) := by unfold Sets; infer_instance

def bindCollections (sha : Bytes → Bytes) (sigma : Bytes) (expected : NativeInputSetBody.Context)
    (p : NativePolicyBytes.Policy) (ec : Eligibility.Bound) (plan : Plan.Bound) (parameters : Parameter.Bound)
    (bodyRaws certificateRaws : List Bytes) : Option Bound := do
  let sizes ← Parameter.checkSizes sha sigma ec plan parameters
  let bt ← InputSection.trees p "aggregate_root_bodies"
  let bodies ← InputSection.collect (bind sha sigma .proposed expected p.validators ec plan parameters) bt bodyRaws
  let ct ← InputSection.trees p "aggregate_root_qcs"
  let certificates ← InputSection.collect (bind sha sigma .finalized expected p.validators ec plan parameters) ct certificateRaws
  let finalized ← InputSection.ids p "finalized_aggregate_root_ids"
  let out := Bound.mk sizes bodies certificates finalized
  if Sets out then some out else none

structure CollectionSource (sha : Bytes → Bytes) (sigma : Bytes) (expected : NativeInputSetBody.Context)
    (p : NativePolicyBytes.Policy) (ec : Eligibility.Bound) (plan : Plan.Bound) (parameters : Parameter.Bound)
    (bodyRaws certificateRaws : List Bytes) (out : Bound) : Prop where
  sizes : Parameter.checkSizes sha sigma ec plan parameters = some out.sizes
  bodyTrees : InputSection.trees p "aggregate_root_bodies" = some (out.bodies.map Located.tree)
  bodyBytes : out.bodies.map Located.raw = bodyRaws
  bodies : ∀ row ∈ out.bodies, bind sha sigma .proposed expected p.validators ec plan parameters row.tree row.raw = some row.value
  certificateTrees : InputSection.trees p "aggregate_root_qcs" = some (out.certificates.map Located.tree)
  certificateBytes : out.certificates.map Located.raw = certificateRaws
  certificates : ∀ row ∈ out.certificates, bind sha sigma .finalized expected p.validators ec plan parameters row.tree row.raw = some row.value
  finalized : InputSection.ids p "finalized_aggregate_root_ids" = some out.finalized
  sets : Sets out

theorem collectionsSource {sha sigma expected p ec plan parameters bodyRaws certificateRaws out}
    (ok : bindCollections sha sigma expected p ec plan parameters bodyRaws certificateRaws = some out) :
    CollectionSource sha sigma expected p ec plan parameters bodyRaws certificateRaws out := by
  unfold bindCollections at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨sizes,hs,bt,hbt,bodies,hb,ct,hct,certificates,hc,finalized,hf,last⟩ := ok
  split at last <;> try contradiction
  rename_i sets
  cases Option.some.inj last
  have bs := InputSection.collectedOriginals hb
  have cs := InputSection.collectedOriginals hc
  exact ⟨hs,by simpa only [bs.1] using hbt,bs.2,InputSection.collectedEach hb,
    by simpa only [cs.1] using hct,cs.2,InputSection.collectedEach hc,hf,sets⟩

theorem collectionsComplete {sha sigma expected p ec plan parameters bodyRaws certificateRaws out}
    (h : CollectionSource sha sigma expected p ec plan parameters bodyRaws certificateRaws out) :
    bindCollections sha sigma expected p ec plan parameters bodyRaws certificateRaws = some out := by
  unfold bindCollections
  rw [h.sizes,h.bodyTrees,← h.bodyBytes]
  simp only [InputSection.collectComplete out.bodies h.bodies,Bind.bind,Option.bind]
  rw [h.certificateTrees,← h.certificateBytes]
  simp only [InputSection.collectComplete out.certificates h.certificates]
  rw [h.finalized]
  exact if_pos h.sets

end DeltaReduce.ProfileSource.Aggregate
