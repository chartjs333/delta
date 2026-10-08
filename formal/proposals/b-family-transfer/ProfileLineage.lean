import ProfileInputSection
import DeltaReduce.NativeNormEvidence
import DeltaReduce.NativeSeedTranscript

/-! T047/T053. Successor norm/seed source edges use the approved consensus b.
Original primitive values and field names remain unchanged. The semantics
parameter comes from independent enrollment; no legacy object is converted or
accepted as a source object by replacing bytes after verification. These pure
byte joins do not assert norm correctness, seed authority or release legality. -/
namespace DeltaReduce.ProfileSource.Lineage
open NativeReceiptBytes NativePolicyCodec
open NativeInputSetBody (Context)

def semanticFields (sigma : Bytes) (fields : List (String × Bytes)) : List (String × Bytes) :=
  fields.map (fun row => if row.1 = "formal_semantics_id" then
    (row.1,NativeIscCertificate.quoted sigma) else row)

theorem fieldNamesUnchanged (sigma : Bytes) (fields : List (String × Bytes)) :
    (semanticFields sigma fields).map Prod.fst = fields.map Prod.fst := by
  simp only [semanticFields,List.map_map]
  apply List.map_congr_left
  intro row _
  dsimp only [Function.comp_apply]
  split <;> rfl

def normBytes (sigma : Bytes) (n : NativeNormEvidence.Evidence) : Bytes :=
  NativeIscCertificate.object (semanticFields sigma (NativeNormEvidence.fields n))

def seedBytes (sigma : Bytes) (s : NativeSeedTranscript.Transcript) : Bytes :=
  NativeIscCertificate.object (semanticFields sigma (NativeSeedTranscript.fields s))

structure Norm where
  evidence : NativeNormEvidence.Evidence
  id : Bytes

def bindNorm (sha : Bytes → Bytes) (sigma : Bytes) (expected : Context)
    (finalized : List Bytes) (tree : Value) (raw : Bytes) : Option Norm := do
  let n ← NativeNormEvidence.read tree
  if NativeVoteBytes.ContentId sigma ∧ NativeNormEvidence.Valid expected n ∧
      n.isc ∈ finalized ∧ raw = normBytes sigma n then
    let id ← NativeStateBytes.contentId sha NativeNormEvidence.domain raw
    some ⟨n,id⟩
  else none

structure NormSource (sha : Bytes → Bytes) (sigma : Bytes) (expected : Context)
    (finalized : List Bytes) (tree : Value) (raw : Bytes) (out : Norm) : Prop where
  read : NativeNormEvidence.read tree = some out.evidence
  treeOriginal : tree = NativeNormEvidence.value out.evidence
  semantic : NativeVoteBytes.ContentId sigma
  shape : NativeNormEvidence.Valid expected out.evidence
  parent : out.evidence.isc ∈ finalized
  bytesOriginal : raw = normBytes sigma out.evidence
  identity : NativeStateBytes.contentId sha NativeNormEvidence.domain raw = some out.id

theorem normSource {sha sigma expected finalized tree raw out}
    (ok : bindNorm sha sigma expected finalized tree raw = some out) :
    NormSource sha sigma expected finalized tree raw out := by
  unfold bindNorm at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨n,hn,ok⟩ := ok
  split at ok <;> try contradiction
  rename_i checks
  simp only [Option.bind_eq_some_iff] at ok
  obtain ⟨id,hi,last⟩ := ok
  cases Option.some.inj last
  exact ⟨hn,NativeNormEvidence.readOriginal hn,checks.1,checks.2.1,
    checks.2.2.1,checks.2.2.2,hi⟩

theorem normComplete {sha sigma expected finalized tree raw out}
    (h : NormSource sha sigma expected finalized tree raw out) :
    bindNorm sha sigma expected finalized tree raw = some out := by
  simp only [bindNorm,h.read,Bind.bind,Option.bind]
  rw [if_pos ⟨h.semantic,h.shape,h.parent,h.bytesOriginal⟩,h.identity]

structure Seed where
  transcript : NativeSeedTranscript.Transcript
  id : Bytes

def bindSeed (sha : Bytes → Bytes) (sigma : Bytes) (expected : Context)
    (finalized : List Bytes) (tree : Value) (raw : Bytes) : Option Seed := do
  let s ← NativeSeedTranscript.read tree
  if NativeVoteBytes.ContentId sigma ∧ NativeSeedTranscript.Valid expected s ∧
      s.isc ∈ finalized ∧ raw = seedBytes sigma s then
    let id ← NativeStateBytes.contentId sha NativeSeedTranscript.domain raw
    some ⟨s,id⟩
  else none

structure SeedSource (sha : Bytes → Bytes) (sigma : Bytes) (expected : Context)
    (finalized : List Bytes) (tree : Value) (raw : Bytes) (out : Seed) : Prop where
  read : NativeSeedTranscript.read tree = some out.transcript
  treeOriginal : tree = NativeSeedTranscript.value out.transcript
  semantic : NativeVoteBytes.ContentId sigma
  shape : NativeSeedTranscript.Valid expected out.transcript
  parent : out.transcript.isc ∈ finalized
  bytesOriginal : raw = seedBytes sigma out.transcript
  identity : NativeStateBytes.contentId sha NativeSeedTranscript.domain raw = some out.id

theorem seedSource {sha sigma expected finalized tree raw out}
    (ok : bindSeed sha sigma expected finalized tree raw = some out) :
    SeedSource sha sigma expected finalized tree raw out := by
  unfold bindSeed at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨s,hs,ok⟩ := ok
  split at ok <;> try contradiction
  rename_i checks
  simp only [Option.bind_eq_some_iff] at ok
  obtain ⟨id,hi,last⟩ := ok
  cases Option.some.inj last
  exact ⟨hs,NativeSeedTranscript.readOriginal hs,checks.1,checks.2.1,
    checks.2.2.1,checks.2.2.2,hi⟩

theorem seedComplete {sha sigma expected finalized tree raw out}
    (h : SeedSource sha sigma expected finalized tree raw out) :
    bindSeed sha sigma expected finalized tree raw = some out := by
  simp only [bindSeed,h.read,Bind.bind,Option.bind]
  rw [if_pos ⟨h.semantic,h.shape,h.parent,h.bytesOriginal⟩,h.identity]

theorem normOriginalParent {sha sigma expected parent p bodyRaws certificateRaws b tree raw out}
    (isc : InputSection.bindAt sha sigma expected parent p bodyRaws certificateRaws = some b)
    (norm : bindNorm sha sigma expected b.finalized tree raw = some out) :
    ∃ row ∈ b.certificates, row.value.consensusId = out.evidence.isc ∧
      ISCSourceV2.CertificateSource sha sigma expected parent p.validators row.tree row.raw row.value :=
  InputSection.finalizedBodyWitness isc (normSource norm).parent

theorem seedOriginalParent {sha sigma expected parent p bodyRaws certificateRaws b tree raw out}
    (isc : InputSection.bindAt sha sigma expected parent p bodyRaws certificateRaws = some b)
    (seed : bindSeed sha sigma expected b.finalized tree raw = some out) :
    ∃ row ∈ b.certificates, row.value.consensusId = out.transcript.isc ∧
      ISCSourceV2.CertificateSource sha sigma expected parent p.validators row.tree row.raw row.value :=
  InputSection.finalizedBodyWitness isc (seedSource seed).parent

structure Bound where
  inputs : InputSection.Bound
  norms : List (InputSection.Located Norm)
  seeds : List (InputSection.Located Seed)

def Ordered (b : Bound) : Prop :=
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (b.norms.map (fun x => x.value.id)) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (b.seeds.map (fun x => x.value.id)) = true
instance (b) : Decidable (Ordered b) := by unfold Ordered; infer_instance

def bindSection (sha : Bytes → Bytes) (sigma : Bytes) (expected : Context) (parent : Bytes)
    (p : NativePolicyBytes.Policy) (bodyRaws certificateRaws normRaws seedRaws : List Bytes) :
    Option Bound := do
  let inputs ← InputSection.bindAt sha sigma expected parent p bodyRaws certificateRaws
  let nt ← InputSection.trees p "norm_evidence"
  let norms ← InputSection.collect (bindNorm sha sigma expected inputs.finalized) nt normRaws
  let st ← InputSection.trees p "seed_transcripts"
  let seeds ← InputSection.collect (bindSeed sha sigma expected inputs.finalized) st seedRaws
  let b := Bound.mk inputs norms seeds
  if Ordered b then some b else none

structure Source (sha : Bytes → Bytes) (sigma : Bytes) (expected : Context) (parent : Bytes)
    (p : NativePolicyBytes.Policy) (bodyRaws certificateRaws normRaws seedRaws : List Bytes)
    (b : Bound) : Prop where
  inputs : InputSection.bindAt sha sigma expected parent p bodyRaws certificateRaws = some b.inputs
  normTrees : InputSection.trees p "norm_evidence" = some (b.norms.map InputSection.Located.tree)
  normBytes : b.norms.map InputSection.Located.raw = normRaws
  norms : ∀ row ∈ b.norms,
    bindNorm sha sigma expected b.inputs.finalized row.tree row.raw = some row.value
  seedTrees : InputSection.trees p "seed_transcripts" = some (b.seeds.map InputSection.Located.tree)
  seedBytes : b.seeds.map InputSection.Located.raw = seedRaws
  seeds : ∀ row ∈ b.seeds,
    bindSeed sha sigma expected b.inputs.finalized row.tree row.raw = some row.value
  ordered : Ordered b

theorem sectionSource {sha sigma expected parent p bodyRaws certificateRaws normRaws seedRaws b}
    (ok : bindSection sha sigma expected parent p bodyRaws certificateRaws normRaws seedRaws = some b) :
    Source sha sigma expected parent p bodyRaws certificateRaws normRaws seedRaws b := by
  unfold bindSection at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨inputs,hi,nt,hnt,norms,hn,st,hst,seeds,hs,last⟩ := ok
  split at last <;> try contradiction
  rename_i ordered
  cases Option.some.inj last
  have ns := InputSection.collectedOriginals hn
  have ss := InputSection.collectedOriginals hs
  exact ⟨hi,by simpa only [ns.1] using hnt,ns.2,InputSection.collectedEach hn,
    by simpa only [ss.1] using hst,ss.2,InputSection.collectedEach hs,ordered⟩

theorem sectionComplete {sha sigma expected parent p bodyRaws certificateRaws normRaws seedRaws b}
    (h : Source sha sigma expected parent p bodyRaws certificateRaws normRaws seedRaws b) :
    bindSection sha sigma expected parent p bodyRaws certificateRaws normRaws seedRaws = some b := by
  unfold bindSection
  rw [h.inputs,h.normTrees,← h.normBytes]
  simp only [InputSection.collectComplete b.norms h.norms,Bind.bind,Option.bind]
  rw [h.seedTrees,← h.seedBytes]
  simp only [InputSection.collectComplete b.seeds h.seeds]
  exact if_pos h.ordered

theorem everyNormParent {sha sigma expected parent p bodyRaws certificateRaws normRaws seedRaws b row}
    (ok : bindSection sha sigma expected parent p bodyRaws certificateRaws normRaws seedRaws = some b)
    (member : row ∈ b.norms) :
    ∃ c ∈ b.inputs.certificates, c.value.consensusId = row.value.evidence.isc ∧
      ISCSourceV2.CertificateSource sha sigma expected parent p.validators c.tree c.raw c.value :=
  normOriginalParent (sectionSource ok).inputs ((sectionSource ok).norms row member)

theorem everySeedParent {sha sigma expected parent p bodyRaws certificateRaws normRaws seedRaws b row}
    (ok : bindSection sha sigma expected parent p bodyRaws certificateRaws normRaws seedRaws = some b)
    (member : row ∈ b.seeds) :
    ∃ c ∈ b.inputs.certificates, c.value.consensusId = row.value.transcript.isc ∧
      ISCSourceV2.CertificateSource sha sigma expected parent p.validators c.tree c.raw c.value :=
  seedOriginalParent (sectionSource ok).inputs ((sectionSource ok).seeds row member)

theorem noOriginalErasure {sha sigma expected parent p bodyRaws certificateRaws normRaws seedRaws b}
    (ok : bindSection sha sigma expected parent p bodyRaws certificateRaws normRaws seedRaws = some b) :
    b.inputs.certificates.map (fun x => x.value.originalBytes) = certificateRaws ∧
    b.norms.map InputSection.Located.raw = normRaws ∧
    b.seeds.map InputSection.Located.raw = seedRaws :=
  ⟨InputSection.cannotHideOriginalWitness (sectionSource ok).inputs,
    (sectionSource ok).normBytes,(sectionSource ok).seedBytes⟩

end DeltaReduce.ProfileSource.Lineage
