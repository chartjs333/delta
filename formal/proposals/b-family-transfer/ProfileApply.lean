import ProfileAggregate
import DeltaReduce.NativeApplyLineage

/-! T047/T053. Whole successor APPLY profile/candidate/QC collections.
The original candidate remains embedded in a finalized row. Byte identity,
parent consistency and structural quorum do not prove arithmetic or origin. -/
namespace DeltaReduce.ProfileSource.Apply
open NativeReceiptBytes NativePolicyCodec
open NativeApplyCertificate (Candidate Certificate CandidateValid CertificateValid)
open NativeParameterLineage (Mode)
open InputSection (Located)

def profileJSON (sigma : Bytes) (p : NativeApplyProfile.Profile) : Bytes :=
  NativeIscCertificate.object (Lineage.semanticFields sigma (NativeApplyProfile.fields p))
def candidateJSON (sigma : Bytes) (c : Candidate) : Bytes :=
  NativeIscCertificate.object (Lineage.semanticFields sigma (NativeApplyCertificate.candidateFields c))
def certificateJSON (sigma : Bytes) (c : Certificate) : Bytes :=
  NativeIscCertificate.object (Lineage.semanticFields sigma (NativeApplyCertificate.certificateFields c))

def candidateId (sha : Bytes → Bytes) (sigma : Bytes) (c : Candidate) : Option Bytes :=
  NativeContractSize.contentId sha NativeApplyCertificate.candidateDomain (candidateJSON sigma c)
def certificateId (sha : Bytes → Bytes) (sigma : Bytes) (c : Certificate) : Option Bytes :=
  NativeContractSize.contentId sha NativeApplyCertificate.certificateDomain (certificateJSON sigma c)

def bindProfile (sha : Bytes → Bytes) (sigma : Bytes) (tree : Value) (raw : Bytes) :
    Option NativeApplyProfile.Checked := do
  let p ← NativeApplyProfile.readProfile tree
  if NativeVoteBytes.ContentId sigma ∧ NativeApplyProfile.Valid p ∧ raw = profileJSON sigma p then
    let id ← NativeContractSize.contentId sha NativeApplyProfile.domain raw
    some ⟨p,tree,id⟩
  else none

theorem profileSource {sha sigma tree raw out}
    (ok : bindProfile sha sigma tree raw = some out) :
    out.source = tree ∧ tree = NativeApplyProfile.profileValue out.profile ∧
    NativeVoteBytes.ContentId sigma ∧ NativeApplyProfile.Valid out.profile ∧
    raw = profileJSON sigma out.profile ∧
    NativeContractSize.contentId sha NativeApplyProfile.domain raw = some out.id := by
  unfold bindProfile at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨p,hp,last⟩ := ok
  split at last <;> try contradiction
  rename_i checks
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨id,hi,last⟩ := last
  cases Option.some.inj last
  exact ⟨rfl,NativeApplyProfile.profileOriginal hp,checks.1,checks.2.1,checks.2.2,hi⟩

def decode (sha : Bytes → Bytes) (sigma : Bytes) (mode : Mode)
    (committee : List Bytes) (tree : Value) : Option NativeApplyLineage.Decoded :=
  match mode with
  | .proposed => do
    let c ← NativeApplyCertificate.readCandidate tree
    let id ← candidateId sha sigma c
    some ⟨c,NativeApplyCertificate.proposedCertificate committee c id,id⟩
  | .finalized => do
    let f ← NativeApplyCertificate.readFinalized tree
    let id ← candidateId sha sigma f.candidate
    some ⟨f.candidate,f.certificate,id⟩

theorem decodedOriginal {sha sigma mode committee tree out}
    (ok : decode sha sigma mode committee tree = some out) :
    tree = NativeApplyLineage.original mode out ∧ candidateId sha sigma out.candidate = some out.candidateId := by
  cases mode with
  | proposed =>
    simp only [decode,Bind.bind,Option.bind_eq_some_iff] at ok
    obtain ⟨c,hc,id,hi,last⟩ := ok
    cases Option.some.inj last
    exact ⟨NativeApplyCertificate.candidateOriginal hc,hi⟩
  | finalized =>
    simp only [decode,Bind.bind,Option.bind_eq_some_iff] at ok
    obtain ⟨f,hf,id,hi,last⟩ := ok
    cases Option.some.inj last
    exact ⟨NativeApplyCertificate.finalizedOriginal hf,hi⟩

def bytes (sigma : Bytes) (mode : Mode) (d : NativeApplyLineage.Decoded) : Bytes :=
  match mode with
  | .proposed => candidateJSON sigma d.candidate
  | .finalized => certificateJSON sigma d.certificate

def Links (parent : Bytes) (roots : Aggregate.Bound) (d : NativeApplyLineage.Decoded)
    (root : Located Aggregate.Edge) (profile : Located NativeApplyProfile.Checked) : Prop :=
  root.value.id ∈ roots.finalized ∧ d.candidate.parent = parent ∧
  d.candidate.root = root.value.id ∧ d.certificate.root = root.value.id ∧
  d.candidate.profile = profile.value.id ∧ d.certificate.profile = profile.value.id ∧
  d.certificate.candidate = d.candidateId ∧ d.certificate.parent = d.candidate.parent ∧
  d.certificate.model = d.candidate.model ∧ d.certificate.optimizer = d.candidate.optimizer
instance (parent roots d root profile) : Decidable (Links parent roots d root profile) := by
  unfold Links; infer_instance

structure Edge where
  decoded : NativeApplyLineage.Decoded
  root : Located Aggregate.Edge
  profile : Located NativeApplyProfile.Checked
  qc : Bytes
  id : Bytes

def bind (sha : Bytes → Bytes) (sigma : Bytes) (mode : Mode)
    (expected : NativeInputSetBody.Context) (committee : List Bytes) (parent : Bytes)
    (roots : Aggregate.Bound) (profiles : List (Located NativeApplyProfile.Checked))
    (tree : Value) (raw : Bytes) : Option Edge := do
  let d ← decode sha sigma mode committee tree
  let root ← roots.certificates.find? (fun x => x.value.id == d.certificate.root)
  let profile ← profiles.find? (fun x => x.value.id == d.certificate.profile)
  if NativeVoteBytes.ContentId sigma ∧ CandidateValid expected d.candidate ∧
      CertificateValid expected committee d.certificate ∧ Links parent roots d root profile ∧
      raw = bytes sigma mode d then
    let qc ← certificateId sha sigma d.certificate
    some ⟨d,root,profile,qc,NativeApplyLineage.resultId mode d qc⟩
  else none

structure Source (sha : Bytes → Bytes) (sigma : Bytes) (mode : Mode)
    (expected : NativeInputSetBody.Context) (committee : List Bytes) (parent : Bytes)
    (roots : Aggregate.Bound) (profiles : List (Located NativeApplyProfile.Checked))
    (tree : Value) (raw : Bytes) (out : Edge) : Prop where
  decoded : decode sha sigma mode committee tree = some out.decoded
  rootLookup : roots.certificates.find? (fun x => x.value.id == out.decoded.certificate.root) = some out.root
  profileLookup : profiles.find? (fun x => x.value.id == out.decoded.certificate.profile) = some out.profile
  semantic : NativeVoteBytes.ContentId sigma
  candidate : CandidateValid expected out.decoded.candidate
  certificate : CertificateValid expected committee out.decoded.certificate
  links : Links parent roots out.decoded out.root out.profile
  originalBytes : raw = bytes sigma mode out.decoded
  qc : certificateId sha sigma out.decoded.certificate = some out.qc
  identity : out.id = NativeApplyLineage.resultId mode out.decoded out.qc

theorem boundSource {sha sigma mode expected committee parent roots profiles tree raw out}
    (ok : bind sha sigma mode expected committee parent roots profiles tree raw = some out) :
    Source sha sigma mode expected committee parent roots profiles tree raw out := by
  unfold bind at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨d,hd,root,hr,profile,hp,last⟩ := ok
  split at last <;> try contradiction
  rename_i checks
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨qc,hq,last⟩ := last
  cases Option.some.inj last
  exact ⟨hd,hr,hp,checks.1,checks.2.1,checks.2.2.1,checks.2.2.2.1,checks.2.2.2.2,hq,rfl⟩

theorem boundComplete {sha sigma mode expected committee parent roots profiles tree raw out}
    (h : Source sha sigma mode expected committee parent roots profiles tree raw out) :
    bind sha sigma mode expected committee parent roots profiles tree raw = some out := by
  unfold bind
  rw [h.decoded]
  simp only [Bind.bind,Option.bind]
  rw [h.rootLookup,h.profileLookup]
  dsimp only
  rw [if_pos ⟨h.semantic,h.candidate,h.certificate,h.links,h.originalBytes⟩,h.qc]
  dsimp only
  rw [← h.identity]

theorem originalCandidate {sha sigma mode expected committee parent roots profiles tree raw out}
    (ok : bind sha sigma mode expected committee parent roots profiles tree raw = some out) :
    tree = NativeApplyLineage.original mode out.decoded ∧
    candidateId sha sigma out.decoded.candidate = some out.decoded.candidateId :=
  decodedOriginal (boundSource ok).decoded

theorem bothPayloadBounds {sha sigma mode expected committee parent roots profiles tree raw out}
    (ok : bind sha sigma mode expected committee parent roots profiles tree raw = some out) :
    (candidateJSON sigma out.decoded.candidate).length ≤ NativeContractSize.maxBytes ∧
    (certificateJSON sigma out.decoded.certificate).length ≤ NativeContractSize.maxBytes :=
  ⟨(NativeContractSize.accepted (originalCandidate ok).2).1,
   (NativeContractSize.accepted (boundSource ok).qc).1⟩

theorem exactCurrentFields {sha sigma mode expected committee parent roots profiles tree raw out}
    (ok : bind sha sigma mode expected committee parent roots profiles tree raw = some out) :
    out.decoded.candidate.parent = parent ∧
    out.decoded.certificate.candidate = out.decoded.candidateId ∧
    out.decoded.certificate.parent = out.decoded.candidate.parent ∧
    out.decoded.certificate.model = out.decoded.candidate.model ∧
    out.decoded.certificate.optimizer = out.decoded.candidate.optimizer :=
  ⟨(boundSource ok).links.2.1,(boundSource ok).links.2.2.2.2.2.2⟩

structure Bound where
  profiles : List (Located NativeApplyProfile.Checked)
  bodies : List (Located Edge)
  certificates : List (Located Edge)
  finalized : List Bytes

def Sets (out : Bound) : Prop :=
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (out.profiles.map (fun x => x.value.id)) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (out.bodies.map (fun x => x.value.id)) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (out.certificates.map (fun x => x.value.id)) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT out.finalized = true ∧
  ∀ id ∈ out.finalized, id ∈ out.certificates.map (fun x => x.value.id)
instance (out) : Decidable (Sets out) := by unfold Sets; infer_instance

def bindCollections (sha : Bytes → Bytes) (sigma : Bytes) (expected : NativeInputSetBody.Context)
    (parent : Bytes) (p : NativePolicyBytes.Policy) (roots : Aggregate.Bound)
    (profileRaws bodyRaws certificateRaws : List Bytes) : Option Bound := do
  let pt ← InputSection.trees p "apply_profiles"
  let profiles ← InputSection.collect (bindProfile sha sigma) pt profileRaws
  let bt ← InputSection.trees p "apply_candidates"
  let bodies ← InputSection.collect (bind sha sigma .proposed expected p.validators parent roots profiles) bt bodyRaws
  let ct ← InputSection.trees p "apply_qcs"
  let certificates ← InputSection.collect (bind sha sigma .finalized expected p.validators parent roots profiles) ct certificateRaws
  let finalized ← InputSection.ids p "finalized_apply_ids"
  let out := Bound.mk profiles bodies certificates finalized
  if Sets out then some out else none

structure CollectionSource (sha : Bytes → Bytes) (sigma : Bytes) (expected : NativeInputSetBody.Context)
    (parent : Bytes) (p : NativePolicyBytes.Policy) (roots : Aggregate.Bound)
    (profileRaws bodyRaws certificateRaws : List Bytes) (out : Bound) : Prop where
  profileTrees : InputSection.trees p "apply_profiles" = some (out.profiles.map Located.tree)
  profileBytes : out.profiles.map Located.raw = profileRaws
  profiles : ∀ row ∈ out.profiles, bindProfile sha sigma row.tree row.raw = some row.value
  bodyTrees : InputSection.trees p "apply_candidates" = some (out.bodies.map Located.tree)
  bodyBytes : out.bodies.map Located.raw = bodyRaws
  bodies : ∀ row ∈ out.bodies, bind sha sigma .proposed expected p.validators parent roots out.profiles row.tree row.raw = some row.value
  certificateTrees : InputSection.trees p "apply_qcs" = some (out.certificates.map Located.tree)
  certificateBytes : out.certificates.map Located.raw = certificateRaws
  certificates : ∀ row ∈ out.certificates, bind sha sigma .finalized expected p.validators parent roots out.profiles row.tree row.raw = some row.value
  finalized : InputSection.ids p "finalized_apply_ids" = some out.finalized
  sets : Sets out

theorem collectionsSource {sha sigma expected parent p roots profileRaws bodyRaws certificateRaws out}
    (ok : bindCollections sha sigma expected parent p roots profileRaws bodyRaws certificateRaws = some out) :
    CollectionSource sha sigma expected parent p roots profileRaws bodyRaws certificateRaws out := by
  unfold bindCollections at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨pt,hpt,profiles,hp,bt,hbt,bodies,hb,ct,hct,certificates,hc,finalized,hf,last⟩ := ok
  split at last <;> try contradiction
  rename_i sets
  cases Option.some.inj last
  have ps := InputSection.collectedOriginals hp
  have bs := InputSection.collectedOriginals hb
  have cs := InputSection.collectedOriginals hc
  exact ⟨by simpa only [ps.1] using hpt,ps.2,InputSection.collectedEach hp,
    by simpa only [bs.1] using hbt,bs.2,InputSection.collectedEach hb,
    by simpa only [cs.1] using hct,cs.2,InputSection.collectedEach hc,hf,sets⟩

theorem collectionsComplete {sha sigma expected parent p roots profileRaws bodyRaws certificateRaws out}
    (h : CollectionSource sha sigma expected parent p roots profileRaws bodyRaws certificateRaws out) :
    bindCollections sha sigma expected parent p roots profileRaws bodyRaws certificateRaws = some out := by
  unfold bindCollections
  rw [h.profileTrees,← h.profileBytes]
  simp only [InputSection.collectComplete out.profiles h.profiles,Bind.bind,Option.bind]
  rw [h.bodyTrees,← h.bodyBytes]
  simp only [InputSection.collectComplete out.bodies h.bodies]
  rw [h.certificateTrees,← h.certificateBytes]
  simp only [InputSection.collectComplete out.certificates h.certificates]
  rw [h.finalized]
  exact if_pos h.sets

end DeltaReduce.ProfileSource.Apply
