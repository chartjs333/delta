import ProfileLineage
import DeltaReduce.NativeEligibilityLineage

/-! T047/T053. The original EC section over the approved ISC consensus b.
The existing proposed/finalized predicates remain distinct. In particular this
does not strengthen finalized native EC admission with the proposed-only norm
parent equality. Origin, signatures and first-finalization permission belong
to the producing history, not to this complete byte/lineage section. -/
namespace DeltaReduce.ProfileSource.Eligibility
open NativeReceiptBytes NativePolicyCodec
open NativeEligibilityLineage (Mode)
open NativeEligibility (Certificate)
open InputSection (Located)

def bytes (sigma : Bytes) (mode : Mode) (c : Certificate) (seed : Bytes) : Bytes :=
  match mode with
  | .proposed => NativeEligibility.bodyBytes ⟨c.common,seed⟩
  | .finalized => NativeIscCertificate.object (Lineage.semanticFields sigma
      (NativeEligibility.fields c))

def domain : Mode → Bytes
  | .proposed => NativeEligibility.bodyDomain
  | .finalized => NativeEligibility.domain

def ParentChecks (mode : Mode) (lineage : Lineage.Bound) (c : Certificate)
    (parent : Located ISCSourceV2.BoundCertificate)
    (norm : Located Lineage.Norm) (seed : Located Lineage.Seed) : Prop :=
  parent.value.consensusId ∈ lineage.inputs.finalized ∧
  seed.value.transcript.isc = parent.value.consensusId ∧
  (mode = .proposed → norm.value.evidence.isc = parent.value.consensusId) ∧
  c.common.entries.map (fun e => (e.ticket,e.domain)) =
    parent.value.certificate.body.tuples.map (fun t => (t.ticket,t.domain))
instance (mode lineage c parent norm seed) :
    Decidable (ParentChecks mode lineage c parent norm seed) := by
  unfold ParentChecks; infer_instance

structure Edge where
  certificate : Certificate
  seedId : Bytes
  id : Bytes
  parent : Located ISCSourceV2.BoundCertificate
  norm : Located Lineage.Norm
  seed : Located Lineage.Seed

def bind (sha : Bytes → Bytes) (sigma : Bytes) (mode : Mode)
    (expected : NativeInputSetBody.Context) (committee : List Bytes)
    (lineage : Lineage.Bound) (tree : Value) (raw : Bytes) : Option Edge := do
  let (c,seedId) ← NativeEligibilityLineage.decode mode committee tree
  let parent ← lineage.inputs.certificates.find? (fun x => x.value.consensusId == c.common.isc)
  let norm ← lineage.norms.find? (fun x => x.value.id == c.common.norm)
  let seed ← lineage.seeds.find? (fun x => x.value.id == seedId)
  if NativeVoteBytes.ContentId sigma ∧ NativeEligibility.Valid expected committee c ∧
      ParentChecks mode lineage c parent norm seed ∧ raw = bytes sigma mode c seedId then
    let id ← NativeStateBytes.contentId sha (domain mode) raw
    some ⟨c,seedId,id,parent,norm,seed⟩
  else none

structure Source (sha : Bytes → Bytes) (sigma : Bytes) (mode : Mode)
    (expected : NativeInputSetBody.Context) (committee : List Bytes)
    (lineage : Lineage.Bound) (tree : Value) (raw : Bytes) (out : Edge) : Prop where
  decoded : NativeEligibilityLineage.decode mode committee tree =
    some (out.certificate,out.seedId)
  parent : lineage.inputs.certificates.find? (fun x =>
    x.value.consensusId == out.certificate.common.isc) = some out.parent
  norm : lineage.norms.find? (fun x => x.value.id == out.certificate.common.norm) = some out.norm
  seed : lineage.seeds.find? (fun x => x.value.id == out.seedId) = some out.seed
  semantic : NativeVoteBytes.ContentId sigma
  valid : NativeEligibility.Valid expected committee out.certificate
  links : ParentChecks mode lineage out.certificate out.parent out.norm out.seed
  originalBytes : raw = bytes sigma mode out.certificate out.seedId
  identity : NativeStateBytes.contentId sha (domain mode) raw = some out.id

theorem boundSource {sha sigma mode expected committee lineage tree raw out}
    (ok : bind sha sigma mode expected committee lineage tree raw = some out) :
    Source sha sigma mode expected committee lineage tree raw out := by
  unfold bind at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨⟨c,seedId⟩,hc,parent,hp,norm,hn,seed,hs,last⟩ := ok
  split at last <;> try contradiction
  rename_i checks
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨id,hi,last⟩ := last
  cases Option.some.inj last
  exact ⟨hc,hp,hn,hs,checks.1,checks.2.1,checks.2.2.1,checks.2.2.2,hi⟩

theorem boundComplete {sha sigma mode expected committee lineage tree raw out}
    (h : Source sha sigma mode expected committee lineage tree raw out) :
    bind sha sigma mode expected committee lineage tree raw = some out := by
  unfold bind
  rw [h.decoded]
  simp only [Bind.bind,Option.bind]
  rw [h.parent,h.norm,h.seed]
  dsimp only
  rw [if_pos ⟨h.semantic,h.valid,h.links,h.originalBytes⟩,h.identity]

theorem originalTree {sha sigma mode expected committee lineage tree raw out}
    (ok : bind sha sigma mode expected committee lineage tree raw = some out) :
    tree = NativeEligibilityLineage.original mode out.certificate out.seedId :=
  NativeEligibilityLineage.decodedOriginal (boundSource ok).decoded

theorem originalParents {sha sigma mode expected committee lineage tree raw out}
    (ok : bind sha sigma mode expected committee lineage tree raw = some out) :
    out.parent ∈ lineage.inputs.certificates ∧
    out.parent.value.consensusId = out.certificate.common.isc ∧
    out.norm ∈ lineage.norms ∧ out.norm.value.id = out.certificate.common.norm ∧
    out.seed ∈ lineage.seeds ∧ out.seed.value.id = out.seedId := by
  have h := boundSource ok
  exact ⟨List.mem_of_find?_eq_some h.parent,by simpa using List.find?_some h.parent,
    List.mem_of_find?_eq_some h.norm,by simpa using List.find?_some h.norm,
    List.mem_of_find?_eq_some h.seed,by simpa using List.find?_some h.seed⟩

theorem proposedNormParent {sha sigma expected committee lineage tree raw out}
    (ok : bind sha sigma .proposed expected committee lineage tree raw = some out) :
    out.norm.value.evidence.isc = out.parent.value.consensusId :=
  (boundSource ok).links.2.2.1 rfl

theorem exactOriginalMembers {sha sigma mode expected committee lineage tree raw out}
    (ok : bind sha sigma mode expected committee lineage tree raw = some out) :
    out.certificate.common.entries.map (fun e => (e.ticket,e.domain)) =
      out.parent.value.certificate.body.tuples.map (fun t => (t.ticket,t.domain)) :=
  (boundSource ok).links.2.2.2

structure Bound where
  lineage : Lineage.Bound
  bodies : List (Located Edge)
  certificates : List (Located Edge)
  finalized : List Bytes

def Sets (out : Bound) : Prop :=
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (out.bodies.map (fun x => x.value.id)) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (out.certificates.map (fun x => x.value.id)) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT out.finalized = true ∧
  ∀ id ∈ out.finalized, id ∈ out.certificates.map (fun x => x.value.id)
instance (out) : Decidable (Sets out) := by unfold Sets; infer_instance

def bindSection (sha : Bytes → Bytes) (sigma : Bytes) (expected : NativeInputSetBody.Context)
    (parent : Bytes) (p : NativePolicyBytes.Policy)
    (bodyRaws certificateRaws normRaws seedRaws ecBodyRaws ecCertificateRaws : List Bytes) :
    Option Bound := do
  let lineage ← Lineage.bindSection sha sigma expected parent p
    bodyRaws certificateRaws normRaws seedRaws
  let bt ← InputSection.trees p "eligibility_bodies"
  let bodies ← InputSection.collect (bind sha sigma .proposed expected p.validators lineage) bt ecBodyRaws
  let ct ← InputSection.trees p "eligibility_certificates"
  let certificates ← InputSection.collect (bind sha sigma .finalized expected p.validators lineage) ct ecCertificateRaws
  let finalized ← InputSection.ids p "finalized_eligibility_ids"
  let out := Bound.mk lineage bodies certificates finalized
  if Sets out then some out else none

structure SectionSource (sha : Bytes → Bytes) (sigma : Bytes) (expected : NativeInputSetBody.Context)
    (parent : Bytes) (p : NativePolicyBytes.Policy)
    (bodyRaws certificateRaws normRaws seedRaws ecBodyRaws ecCertificateRaws : List Bytes)
    (out : Bound) : Prop where
  lineage : Lineage.bindSection sha sigma expected parent p bodyRaws certificateRaws normRaws seedRaws = some out.lineage
  bodyTrees : InputSection.trees p "eligibility_bodies" = some (out.bodies.map Located.tree)
  bodyBytes : out.bodies.map Located.raw = ecBodyRaws
  bodies : ∀ row ∈ out.bodies, bind sha sigma .proposed expected p.validators out.lineage row.tree row.raw = some row.value
  certificateTrees : InputSection.trees p "eligibility_certificates" = some (out.certificates.map Located.tree)
  certificateBytes : out.certificates.map Located.raw = ecCertificateRaws
  certificates : ∀ row ∈ out.certificates, bind sha sigma .finalized expected p.validators out.lineage row.tree row.raw = some row.value
  finalized : InputSection.ids p "finalized_eligibility_ids" = some out.finalized
  sets : Sets out

theorem sectionSource {sha sigma expected parent p bodyRaws certificateRaws normRaws seedRaws ecBodyRaws ecCertificateRaws out}
    (ok : bindSection sha sigma expected parent p bodyRaws certificateRaws normRaws seedRaws ecBodyRaws ecCertificateRaws = some out) :
    SectionSource sha sigma expected parent p bodyRaws certificateRaws normRaws seedRaws ecBodyRaws ecCertificateRaws out := by
  unfold bindSection at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨lineage,hl,bt,hbt,bodies,hb,ct,hct,certificates,hc,finalized,hf,last⟩ := ok
  split at last <;> try contradiction
  rename_i sets
  cases Option.some.inj last
  have bs := InputSection.collectedOriginals hb
  have cs := InputSection.collectedOriginals hc
  exact ⟨hl,by simpa only [bs.1] using hbt,bs.2,InputSection.collectedEach hb,
    by simpa only [cs.1] using hct,cs.2,InputSection.collectedEach hc,hf,sets⟩

theorem sectionComplete {sha sigma expected parent p bodyRaws certificateRaws normRaws seedRaws ecBodyRaws ecCertificateRaws out}
    (h : SectionSource sha sigma expected parent p bodyRaws certificateRaws normRaws seedRaws ecBodyRaws ecCertificateRaws out) :
    bindSection sha sigma expected parent p bodyRaws certificateRaws normRaws seedRaws ecBodyRaws ecCertificateRaws = some out := by
  unfold bindSection
  rw [h.lineage,h.bodyTrees,← h.bodyBytes]
  simp only [InputSection.collectComplete out.bodies h.bodies,Bind.bind,Option.bind]
  rw [h.certificateTrees,← h.certificateBytes]
  simp only [InputSection.collectComplete out.certificates h.certificates]
  rw [h.finalized]
  exact if_pos h.sets

theorem finalizedWitness {sha sigma expected parent p bodyRaws certificateRaws normRaws seedRaws ecBodyRaws ecCertificateRaws out id}
    (ok : bindSection sha sigma expected parent p bodyRaws certificateRaws normRaws seedRaws ecBodyRaws ecCertificateRaws = some out)
    (member : id ∈ out.finalized) :
    ∃ row ∈ out.certificates, row.value.id = id ∧
      Source sha sigma .finalized expected p.validators out.lineage row.tree row.raw row.value := by
  have h := sectionSource ok
  obtain ⟨row,mem,eq⟩ := List.mem_map.mp (h.sets.2.2.2 id member)
  exact ⟨row,mem,eq,boundSource (h.certificates row mem)⟩

theorem noOriginalErasure {sha sigma expected parent p bodyRaws certificateRaws normRaws seedRaws ecBodyRaws ecCertificateRaws out}
    (ok : bindSection sha sigma expected parent p bodyRaws certificateRaws normRaws seedRaws ecBodyRaws ecCertificateRaws = some out) :
    out.lineage.inputs.certificates.map (fun x => x.value.originalBytes) = certificateRaws ∧
    out.lineage.norms.map Located.raw = normRaws ∧ out.lineage.seeds.map Located.raw = seedRaws ∧
    out.bodies.map Located.raw = ecBodyRaws ∧ out.certificates.map Located.raw = ecCertificateRaws := by
  have h := sectionSource ok
  have originals := Lineage.noOriginalErasure h.lineage
  exact ⟨originals.1,originals.2.1,originals.2.2,h.bodyBytes,h.certificateBytes⟩

end DeltaReduce.ProfileSource.Eligibility
