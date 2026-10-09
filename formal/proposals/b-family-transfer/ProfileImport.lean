import ProfileOrigin

/-! T047/T053. Complete import metadata joins the independent bootstrap/index,
trusted T log, original artifact inventory and own journal prefixes. This is
the existing Profile-v1 metadata conjunct, not ApplyQC authentication, native
producer legality, record decoding or public-state acceptance. -/
namespace DeltaReduce.ProfileSource.Import
open NativeReceiptBytes (Bytes)
open NativeVoteBytes (ascii)
open Control (Node Fields)

structure Interval where
  reference : Index.Ref
  count : Nat
  first : Nat
  last : Nat
  deriving DecidableEq, Repr

def Interval.Valid (sha : Bytes → Bytes) (i : Interval) : Prop :=
  if i.count = 0 then
    i.first = 0 ∧ i.last = 0 ∧ i.reference.length = 0 ∧ i.reference.id = Index.rawId sha []
  else i.first ≤ i.last ∧ i.last-i.first+1 = i.count ∧ 0 < i.reference.length
instance (sha i) : Decidable (Interval.Valid sha i) := by unfold Interval.Valid; infer_instance

def interval (sha : Bytes → Bytes) (f : Fields) : Option Interval := do
  let ref ← Index.field f "ref" >>= Index.reference
  let count ← Index.field f "entry_count" >>= Index.decimal
  let first ← Index.field f "first_sequence" >>= Index.decimal
  let last ← Index.field f "last_sequence" >>= Index.decimal
  let i := Interval.mk ref count first last
  if i.Valid sha then some i else none

structure JournalCut where
  actor : Bytes
  journal : Bytes
  span : Interval
  deriving DecidableEq, Repr

def cut (sha : Bytes → Bytes) (n : Node) : Option JournalCut := do
  let f ← Index.object n
  let actor ← Index.text (Index.field f "actor_id")
  let journal ← Index.text (Index.field f "journal_id")
  let i ← interval sha f
  if Control.names f = (["actor_id","entry_count","first_sequence","journal_id",
      "last_sequence","ref"].map ascii) ∧ Control.canonicalFields f = true ∧
      actor ≠ [] ∧ journal ≠ [] then some ⟨actor,journal,i⟩ else none

def cutKey (c : JournalCut) := (c.actor,c.journal)

def CutInventory (cs : List JournalCut) : Prop :=
  (cs.map cutKey).Pairwise (fun a b => a.1 < b.1 ∨ (a.1 = b.1 ∧ a.2 < b.2)) ∧
  (cs.map (·.span.count)).sum ≤ 1000000
instance (cs) : Decidable (CutInventory cs) := by unfold CutInventory; infer_instance

def cuts (sha : Bytes → Bytes) (ns : List Node) : Option (List JournalCut) := do
  let cs ← Index.collect (cut sha) ns
  if CutInventory cs then some cs else none

structure Range where
  actor : Bytes
  journal : Bytes
  atCut : Interval
  target : Interval
  deriving DecidableEq, Repr

def range (sha : Bytes → Bytes) (n : Node) : Option Range := do
  let f ← Index.object n
  let actor ← Index.text (Index.field f "actor_id")
  let journal ← Index.text (Index.field f "journal_id")
  let cf ← Index.field f "cut" >>= Index.object
  let tf ← Index.field f "target" >>= Index.object
  let atCut ← interval sha cf
  let target ← interval sha tf
  if Control.names f = (["actor_id","cut","journal_id","target"].map ascii) ∧
      Control.canonicalFields f = true ∧ actor ≠ [] ∧ journal ≠ [] ∧
      Control.names cf = (["entry_count","first_sequence","last_sequence","ref"].map ascii) ∧
      Control.names tf = Control.names cf ∧ atCut.count ≤ target.count then
    some ⟨actor,journal,atCut,target⟩ else none

def targetCut (r : Range) : JournalCut := ⟨r.actor,r.journal,r.target⟩
def snapshotCut (r : Range) : JournalCut := ⟨r.actor,r.journal,r.atCut⟩

structure OwnJournal where
  actor : Bytes
  journal : Bytes
  original : Bytes
  deriving DecidableEq, Repr

def ownKey (j : OwnJournal) := (j.actor,j.journal)

def OriginalPrefix (sha : Bytes → Bytes) (own : List OwnJournal) (c : JournalCut) : Prop :=
  ∃ j ∈ own, ownKey j = cutKey c ∧ c.span.reference.length ≤ j.original.length ∧
    Index.rawId sha (j.original.take c.span.reference.length) = c.span.reference.id
instance (sha own c) : Decidable (OriginalPrefix sha own c) := by
  unfold OriginalPrefix; infer_instance

structure Manifest where
  descriptor : Fields
  original : Bytes
  indexRef : Index.Ref
  anchor : NativeCurrentPointer.State
  snapshot : Bytes
  applyQC : Bytes
  candidate : Bytes
  cut : Nat
  target : Nat
  ranges : List Range
  journalTargets : List JournalCut
  trustCuts : List (List JournalCut)

def SameContext (b : Origin.Bootstrap) (f : Fields) : Prop :=
  Index.text (Index.field f "origin_id") = some b.origin.id ∧
  Index.text (Index.field f "validator_epoch_id") = some b.origin.epoch ∧
  Index.text (Index.field f "local_validator_id") = some b.origin.actor ∧
  Index.field f "formal_semantics_id" = Index.field b.descriptor "formal_semantics_id" ∧
  Index.field f "schema_set_id" = Index.field b.descriptor "schema_set_id"
instance (b f) : Decidable (SameContext b f) := by unfold SameContext; infer_instance

def resolveField (sha : Bytes → Bytes) (declared : List Node) (store : List Bytes)
    (f : Fields) (key : String) : Option Bytes :=
  Index.field f key >>= Index.resolve sha declared store

def Checks (sha : Bytes → Bytes) (origin : Origin.Bound) (floor : Origin.Floor)
    (store : List Bytes) (own : List OwnJournal) (m : Manifest) : Prop :=
  SameContext origin.bootstrap m.descriptor ∧
  Index.text (Index.field m.descriptor "bootstrap_id") =
    Origin.bootstrapId sha origin.bootstrap.original ∧
  Index.array (Index.field m.descriptor "artifacts") = some origin.source.declared ∧
  store = origin.source.artifacts ∧
  origin.source.original.length = m.indexRef.length ∧
  Index.rawId sha origin.source.original = m.indexRef.id ∧
  origin.bootstrap.original.length + origin.source.original.length + m.original.length +
    floor.original.length + (store.map List.length).sum ≤ 64*1024^3 ∧
  m.anchor = floor.tip.anchor ∧ m.cut ≤ m.target ∧ m.target ≤ origin.source.events.length ∧
  floor.rows.length ≤ 1000000 ∧
  m.journalTargets = m.ranges.map targetCut ∧ CutInventory m.journalTargets ∧
  own.map ownKey = m.journalTargets.map cutKey ∧
  (∀ j ∈ own, j.actor = origin.bootstrap.origin.actor) ∧
  (∀ (i : Nat) (j : OwnJournal), own[i]? = some j → ∃ c : JournalCut, m.journalTargets[i]? = some c ∧
    Index.resolve sha origin.source.declared store c.span.reference.original = some j.original) ∧
  (∀ c ∈ m.ranges.map snapshotCut, OriginalPrefix sha own c) ∧
  (∀ cs ∈ m.trustCuts, ∀ c ∈ cs, OriginalPrefix sha own c)
-- The indexed own/target condition is a finite executable zip below, not an
-- unbounded decidability oracle.

def ownTargets (sha : Bytes → Bytes) (declared : List Node) (store : List Bytes) :
    List OwnJournal → List JournalCut → Bool
  | [],[] => true
  | j::js,c::cs => decide (ownKey j = cutKey c ∧
      Index.resolve sha declared store c.span.reference.original = some j.original) &&
      ownTargets sha declared store js cs
  | _,_ => false

def Checked (sha : Bytes → Bytes) (origin : Origin.Bound) (floor : Origin.Floor)
    (store : List Bytes) (own : List OwnJournal) (m : Manifest) : Prop :=
  SameContext origin.bootstrap m.descriptor ∧
  Index.text (Index.field m.descriptor "bootstrap_id") =
    Origin.bootstrapId sha origin.bootstrap.original ∧
  Index.array (Index.field m.descriptor "artifacts") = some origin.source.declared ∧
  store = origin.source.artifacts ∧
  origin.source.original.length = m.indexRef.length ∧
  Index.rawId sha origin.source.original = m.indexRef.id ∧
  origin.bootstrap.original.length + origin.source.original.length + m.original.length +
    floor.original.length + (store.map List.length).sum ≤ 64*1024^3 ∧
  m.anchor = floor.tip.anchor ∧ m.cut ≤ m.target ∧ m.target ≤ origin.source.events.length ∧
  floor.rows.length ≤ 1000000 ∧
  m.journalTargets = m.ranges.map targetCut ∧ CutInventory m.journalTargets ∧
  ownTargets sha origin.source.declared store own m.journalTargets = true ∧
  (∀ j ∈ own, j.actor = origin.bootstrap.origin.actor) ∧
  (∀ c ∈ m.ranges.map snapshotCut, OriginalPrefix sha own c) ∧
  (∀ cs ∈ m.trustCuts, ∀ c ∈ cs, OriginalPrefix sha own c)
instance (sha origin floor store own m) : Decidable (Checked sha origin floor store own m) := by
  unfold Checked; infer_instance

def read (sha : Bytes → Bytes) (origin : Origin.Bound) (floor : Origin.Floor)
    (store : List Bytes) (f : Fields) (raw : Bytes) : Option Manifest := do
  let f ← Control.check .manifest f raw
  let indexRef ← Index.field f "source_index_ref" >>= Index.reference
  let anchor ← Index.field f "anchor" >>= Origin.anchor
  let snapshot ← resolveField sha origin.source.declared store f "snapshot_ref"
  let qc ← resolveField sha origin.source.declared store f "apply_qc_ref"
  let candidate ← resolveField sha origin.source.declared store f "apply_candidate_ref"
  let first ← Index.field f "cut_event_index" >>= Index.decimal
  let target ← Index.field f "target_event_index" >>= Index.decimal
  let ranges ← Index.array (Index.field f "journals") >>= Index.collect (range sha)
  let targets ← Index.array (Index.field origin.source.descriptor "original_journal_refs") >>=
    cuts sha
  let trustCuts ← Index.collect (fun row => cuts sha row.cuts) floor.rows
  some ⟨f,raw,indexRef,anchor,snapshot,qc,candidate,first,target,ranges,targets,trustCuts⟩

def bind (sha : Bytes → Bytes) (origin : Origin.Bound) (floor : Origin.Floor)
    (store : List Bytes) (own : List OwnJournal) (f : Fields) (raw : Bytes) : Option Manifest := do
  let m ← read sha origin floor store f raw
  if Checked sha origin floor store own m then some m else none

theorem boundSource {sha origin floor store own f raw out}
    (ok : bind sha origin floor store own f raw = some out) :
    read sha origin floor store f raw = some out ∧ Checked sha origin floor store own out := by
  simp only [bind,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨m,hm,last⟩ := ok
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨hm,by assumption⟩

theorem complete {sha origin floor store own f raw out}
    (original : read sha origin floor store f raw = some out)
    (checks : Checked sha origin floor store own out) :
    bind sha origin floor store own f raw = some out := by
  simp only [bind,original,Bind.bind,Option.bind,if_pos checks]

theorem ownTargetsExact {sha declared store own targets}
    (ok : ownTargets sha declared store own targets = true) :
    own.map ownKey = targets.map cutKey ∧
    ∀ (i : Nat) (j : OwnJournal), own[i]? = some j → ∃ c : JournalCut, targets[i]? = some c ∧
      Index.resolve sha declared store c.span.reference.original = some j.original := by
  induction own generalizing targets with
  | nil => cases targets <;> simp_all [ownTargets]
  | cons j js ih =>
    cases targets with
    | nil => simp [ownTargets] at ok
    | cons c cs =>
      simp only [ownTargets,Bool.and_eq_true,decide_eq_true_eq] at ok
      have rest := ih ok.2
      refine ⟨by simp only [List.map_cons,ok.1.1,rest.1],?_⟩
      intro i row found
      cases i with
      | zero =>
        have same : j = row := by simpa using found
        subst row
        exact ⟨c,rfl,ok.1.2⟩
      | succ i =>
        obtain ⟨cut,atCut,source⟩ := rest.2 i row (by simpa using found)
        exact ⟨cut,by simpa using atCut,source⟩

theorem metadataSource {sha origin floor store own f raw out}
    (ok : bind sha origin floor store own f raw = some out) :
    Checks sha origin floor store own out := by
  have h := (boundSource ok).2
  rcases h with ⟨a,b,c,d,e,g,h,i,j,k,l,m,n,o,p,q,r⟩
  exact ⟨a,b,c,d,e,g,h,i,j,k,l,m,n,(ownTargetsExact o).1,p,(ownTargetsExact o).2,q,r⟩

theorem originalManifest {sha origin floor store f raw out}
    (ok : read sha origin floor store f raw = some out) :
    out.original = raw ∧ Control.check .manifest f raw = some out.descriptor ∧
    resolveField sha origin.source.declared store out.descriptor "snapshot_ref" = some out.snapshot ∧
    resolveField sha origin.source.declared store out.descriptor "apply_qc_ref" = some out.applyQC ∧
    resolveField sha origin.source.declared store out.descriptor "apply_candidate_ref" = some out.candidate ∧
    Index.collect (fun row => cuts sha row.cuts) floor.rows = some out.trustCuts := by
  simp only [read,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨f,hf,ref,hr,a,ha,s,hs,q,hq,c,hc,first,hfirst,target,ht,rs,hrs,ts,hts,
    tcs,htcs,last⟩ := ok
  cases Option.some.inj last
  exact ⟨rfl,hf,hs,hq,hc,htcs⟩

theorem originalReferencedBytes {sha origin floor store f raw out}
    (ok : read sha origin floor store f raw = some out) :
    out.snapshot ∈ store ∧ out.applyQC ∈ store ∧ out.candidate ∈ store := by
  have h := originalManifest ok
  have member : ∀ key value,
      resolveField sha origin.source.declared store out.descriptor key = some value → value ∈ store := by
    intro key value source
    obtain ⟨ref,_,bound⟩ := Option.bind_eq_some_iff.mp source
    exact (Index.resolved bound).2.1
  exact ⟨member _ _ h.2.2.1,member _ _ h.2.2.2.1,member _ _ h.2.2.2.2.1⟩

/-- Independent T-side facts. No truth flag, imported authority or projection
result is permitted in this interface. Descriptors below are untrusted views. -/
structure Trusted where
  known : Origin.Independent
  bootstrap : Bytes
  floorLog : Bytes
  ownJournals : List OwnJournal

structure Package where
  bootstrapDescriptor : Fields
  indexDescriptor : Fields
  indexRaw : Bytes
  floorDescriptors : List Origin.FloorInput
  manifestDescriptor : Fields
  manifestRaw : Bytes
  artifacts : List Bytes

structure Bound where
  origin : Origin.Bound
  floor : Origin.Floor
  manifest : Manifest

def bindProfile (sha : Bytes → Bytes) (trusted : Trusted) (p : Package) : Option Bound := do
  let origin ← Origin.bind sha trusted.known p.bootstrapDescriptor p.indexDescriptor
    trusted.bootstrap p.indexRaw p.artifacts
  let floor ← Origin.bindFloor sha origin.bootstrap p.floorDescriptors trusted.floorLog
  let manifest ← bind sha origin floor p.artifacts trusted.ownJournals
    p.manifestDescriptor p.manifestRaw
  some ⟨origin,floor,manifest⟩

structure Source (sha : Bytes → Bytes) (trusted : Trusted) (p : Package) (out : Bound) : Prop where
  origin : Origin.bind sha trusted.known p.bootstrapDescriptor p.indexDescriptor
    trusted.bootstrap p.indexRaw p.artifacts = some out.origin
  floor : Origin.bindFloor sha out.origin.bootstrap p.floorDescriptors trusted.floorLog = some out.floor
  manifest : read sha out.origin out.floor p.artifacts p.manifestDescriptor p.manifestRaw = some out.manifest
  checks : Checked sha out.origin out.floor p.artifacts trusted.ownJournals out.manifest

theorem profileSource {sha trusted p out} (ok : bindProfile sha trusted p = some out) :
    Source sha trusted p out := by
  simp only [bindProfile,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨origin,ho,floor,hf,manifest,hm,last⟩ := ok
  cases Option.some.inj last
  exact ⟨ho,hf,(boundSource hm).1,(boundSource hm).2⟩

theorem profileComplete {sha trusted p out} (h : Source sha trusted p out) :
    bindProfile sha trusted p = some out := by
  have hm := complete h.manifest h.checks
  simp only [bindProfile,h.origin,h.floor,hm,Bind.bind,Option.bind]

theorem exactTrustedFloor {sha trusted p out} (ok : bindProfile sha trusted p = some out) :
    out.floor.original = trusted.floorLog ∧ out.floor.rows.length = p.floorDescriptors.length ∧
    out.manifest.anchor = out.floor.tip.anchor := by
  have h := profileSource ok
  rcases h.checks with ⟨_,_,_,_,_,_,_,anchor,_⟩
  exact ⟨(Origin.boundFloorSource h.floor).1,Origin.boundFloorNoRecordErasure h.floor,anchor⟩

theorem allTrustedPrefixes {sha trusted p out} (ok : bindProfile sha trusted p = some out) :
    ∀ row ∈ out.floor.rows, ∃ cs, cuts sha row.cuts = some cs ∧
      ∀ c ∈ cs, OriginalPrefix sha trusted.ownJournals c := by
  have h := profileSource ok
  have original := (originalManifest h.manifest).2.2.2.2.2
  rcases h.checks with ⟨_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,prefixes⟩
  intro row found
  obtain ⟨i,atRow⟩ := List.mem_iff_getElem?.mp found
  obtain ⟨cs,atCs,bound⟩ := Index.collectPosition original atRow
  exact ⟨cs,bound,prefixes cs (List.mem_of_getElem? atCs)⟩

theorem originalArtifactInventory {sha trusted p out} (ok : bindProfile sha trusted p = some out) :
    p.artifacts = out.origin.source.artifacts ∧
    out.manifest.snapshot ∈ p.artifacts ∧ out.manifest.applyQC ∈ p.artifacts ∧
    out.manifest.candidate ∈ p.artifacts ∧
    out.origin.initialConfiguration ∈ p.artifacts := by
  have h := profileSource ok
  rcases h.checks with ⟨_,_,_,inventory,_⟩
  have originals := originalReferencedBytes h.manifest
  exact ⟨inventory,originals.1,originals.2.1,originals.2.2,
    (Origin.originalInitialConfiguration h.origin).1⟩

theorem eventInventoryAndCuts {sha trusted p out} (ok : bindProfile sha trusted p = some out) :
    out.origin.source.events.map Index.Event.descriptor = out.origin.source.eventDescriptors ∧
    out.manifest.cut ≤ out.manifest.target ∧
    out.manifest.target ≤ out.origin.source.events.length := by
  have h := profileSource ok
  have es := Index.wholeOriginalEvents (Origin.boundSource h.origin).source
  rcases h.checks with ⟨_,_,_,_,_,_,_,_,first,last,_⟩
  exact ⟨es.2.1,first,last⟩

end DeltaReduce.ProfileSource.Import
