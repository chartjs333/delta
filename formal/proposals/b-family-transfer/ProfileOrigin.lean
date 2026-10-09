import ProfileSourceIndex
import DeltaReduce.NativeCurrentPointer

/-! T047/T053. Independent Profile-v1 bootstrap to complete original source
inventory. All selectors come from the retained bootstrap bytes, never from
the imported snapshot. This is the provenance byte/namespace conjunct, not a
claim that the resolved genesis/configuration bytes are lawful native states.
No new source field, certificate protocol or trust authority is introduced. -/
namespace DeltaReduce.ProfileSource.Origin
open NativeReceiptBytes (Bytes)
open NativeVoteBytes (ascii ContentId)
open Control (Node Fields)

structure Pins where
  runtime : Bytes
  semantics : Bytes
  schemas : Bytes
  signatures : Bytes
  producers : Bytes
  deriving DecidableEq, Repr

def Pins.Valid (p : Pins) : Prop :=
  ∀ id ∈ [p.runtime,p.semantics,p.schemas,p.signatures,p.producers], ContentId id
instance (p : Pins) : Decidable p.Valid := by unfold Pins.Valid; infer_instance

def Pins.Match (p : Pins) (f : Fields) : Prop :=
  Index.text (Index.field f "runtime_build_id") = some p.runtime ∧
  Index.text (Index.field f "formal_semantics_id") = some p.semantics ∧
  Index.text (Index.field f "schema_set_id") = some p.schemas ∧
  Index.text (Index.field f "signature_codec_id") = some p.signatures ∧
  Index.text (Index.field f "producer_rules_id") = some p.producers
instance (p f) : Decidable (Pins.Match p f) := by unfold Pins.Match; infer_instance

/-- These are independently provisioned/retained byte digests and installed
verifier pins, not booleans asserting lawfulness or successful refinement. -/
structure Independent where
  bootstrapDigest : Bytes
  indexDigest : Bytes
  pins : Pins
  deriving DecidableEq, Repr

structure Member where
  original : Node
  validator : Bytes
  key : Bytes
  deriving DecidableEq, Repr

def member (original : Node) : Option Member := do
  let f ← Index.object original
  let validator ← Index.text (Index.field f "validator_id")
  let key ← Index.text (Index.field f "key_ref")
  if Control.names f = [ascii "key_ref",ascii "roles",ascii "validator_id"] ∧
      Control.canonicalFields f = true ∧ validator ≠ [] ∧ ContentId key ∧
      Index.array (Index.field f "roles") = some [.text (ascii "validator")] then
    some ⟨original,validator,key⟩ else none

def anchor (original : Node) : Option NativeCurrentPointer.State := do
  let f ← Index.object original
  let checkpoint ← Index.text (Index.field f "checkpoint_id")
  let optimizer ← Index.text (Index.field f "optimizer_id")
  let qc ← Index.text (Index.field f "apply_qc_id")
  let height ← Index.field f "height" >>= Index.decimal
  let state := NativeCurrentPointer.State.mk checkpoint optimizer qc height
  if Control.names f = [ascii "apply_qc_id",ascii "checkpoint_id",ascii "height",ascii "optimizer_id"] ∧
      Control.canonicalFields f = true ∧ NativeCurrentPointer.StateValid state ∧ ContentId qc then
    some state else none

structure Bootstrap where
  original : Bytes
  descriptor : Fields
  origin : Index.Origin
  initialRef : Node
  genesis : Index.Ref
  initial : Index.Ref
  members : List Member
  initialAnchor : NativeCurrentPointer.State

def checkBootstrap (sha : Bytes → Bytes) (known : Independent)
    (descriptor : Fields) (original : Bytes) : Option Bootstrap := do
  let f ← Control.check .bootstrap descriptor original
  let id ← Index.text (Index.field f "origin_id")
  let epoch ← Index.text (Index.field f "validator_epoch_id")
  let actor ← Index.text (Index.field f "local_validator_id")
  let genesisRef ← Index.field f "genesis_ref"
  let initialRef ← Index.field f "initial_config_ref"
  let genesis ← Index.reference genesisRef
  let initial ← Index.reference initialRef
  let members ← Index.array (Index.field f "validators") >>= Index.collect member
  let initialAnchor ← Index.field f "initial_anchor" >>= anchor
  let origin := Index.Origin.mk id epoch actor genesisRef
  if sha original = known.bootstrapDigest ∧ known.bootstrapDigest.length = 32 ∧
      known.pins.Valid ∧ known.pins.Match f ∧ Index.OriginMatches origin f ∧
      Index.text (Index.field f "quorum_threshold") = some (ascii "3") ∧
      members.length = 4 ∧ (members.map Member.validator).Pairwise (· < ·) ∧
      (members.map Member.key).Nodup ∧ actor ∈ members.map Member.validator then
    some ⟨original,f,origin,initialRef,genesis,initial,members,initialAnchor⟩ else none

theorem bootstrapSource {sha known descriptor original out}
    (ok : checkBootstrap sha known descriptor original = some out) :
    Control.check .bootstrap descriptor original = some out.descriptor ∧
    out.original = original ∧ sha original = known.bootstrapDigest ∧
    known.bootstrapDigest.length = 32 ∧ known.pins.Valid ∧ known.pins.Match out.descriptor ∧
    Index.OriginMatches out.origin out.descriptor ∧
    out.members.length = 4 ∧ (out.members.map Member.validator).Pairwise (· < ·) ∧
    (out.members.map Member.key).Nodup ∧ out.origin.actor ∈ out.members.map Member.validator ∧
    (Index.field out.descriptor "initial_anchor" >>= anchor) = some out.initialAnchor := by
  simp only [checkBootstrap,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨f,hf,id,hi,epoch,he,actor,ha,gref,hgr,iref,hir,genesis,hg,initial,hin,
    members,hm,a,hab,last⟩ := ok
  split at last <;> try contradiction
  rename_i valid
  cases Option.some.inj last
  refine ⟨hf,rfl,valid.1,valid.2.1,valid.2.2.1,valid.2.2.2.1,valid.2.2.2.2.1,
    valid.2.2.2.2.2.2.1,valid.2.2.2.2.2.2.2.1,valid.2.2.2.2.2.2.2.2.1,
    valid.2.2.2.2.2.2.2.2.2,?_⟩
  exact Option.bind_eq_some_iff.mpr hab

structure Bound where
  bootstrap : Bootstrap
  source : Index.Bound
  initialConfiguration : Bytes

def bind (sha : Bytes → Bytes) (known : Independent)
    (bootstrap index : Fields) (bootstrapRaw indexRaw : Bytes) (store : List Bytes) :
    Option Bound := do
  let b ← checkBootstrap sha known bootstrap bootstrapRaw
  if sha indexRaw = known.indexDigest ∧ known.indexDigest.length = 32 then
    let source ← Index.check sha b.origin index indexRaw store
    let initial ← Index.resolve sha source.declared store b.initialRef
    some ⟨b,source,initial⟩ else none

structure Source (sha : Bytes → Bytes) (known : Independent)
    (bootstrap index : Fields) (bootstrapRaw indexRaw : Bytes) (store : List Bytes)
    (out : Bound) : Prop where
  bootstrap : checkBootstrap sha known bootstrap bootstrapRaw = some out.bootstrap
  retainedIndex : sha indexRaw = known.indexDigest
  digest : known.indexDigest.length = 32
  source : Index.check sha out.bootstrap.origin index indexRaw store = some out.source
  initial : Index.resolve sha out.source.declared store out.bootstrap.initialRef =
    some out.initialConfiguration

theorem boundSource {sha known bootstrap index bootstrapRaw indexRaw store out}
    (ok : bind sha known bootstrap index bootstrapRaw indexRaw store = some out) :
    Source sha known bootstrap index bootstrapRaw indexRaw store out := by
  simp only [bind,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨b,hb,last⟩ := ok
  split at last <;> try contradiction
  rename_i original
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨source,hs,initial,hi,last⟩ := last
  cases Option.some.inj last
  exact ⟨hb,original.1,original.2,hs,hi⟩

theorem complete {sha known bootstrap index bootstrapRaw indexRaw store out}
    (h : Source sha known bootstrap index bootstrapRaw indexRaw store out) :
    bind sha known bootstrap index bootstrapRaw indexRaw store = some out := by
  simp only [bind,h.bootstrap,Bind.bind,Option.bind,
    if_pos (And.intro h.retainedIndex h.digest),h.source,h.initial]

theorem originalInitialConfiguration {sha known bootstrap index bootstrapRaw indexRaw store out}
    (ok : bind sha known bootstrap index bootstrapRaw indexRaw store = some out) :
    out.initialConfiguration ∈ store ∧ ∃ r,
      Index.reference out.bootstrap.initialRef = some r ∧
      out.initialConfiguration.length = r.length ∧
      Index.rawId sha out.initialConfiguration = r.id := by
  have h := Index.resolved (boundSource ok).initial
  obtain ⟨r,hr,_,hl,hi,_⟩ := h.2.2
  exact ⟨h.2.1,r,hr,hl,hi⟩

theorem originalSourceInventory {sha known bootstrap index bootstrapRaw indexRaw store out}
    (ok : bind sha known bootstrap index bootstrapRaw indexRaw store = some out) :
    Index.check sha out.bootstrap.origin index indexRaw store = some out.source ∧
    sha indexRaw = known.indexDigest :=
  ⟨(boundSource ok).source,(boundSource ok).retainedIndex⟩

def bootstrapId (sha : Bytes → Bytes) (raw : Bytes) : Option Bytes :=
  NativeStateBytes.contentId sha (ascii "deltareduce.snapshot-provenance.bootstrap.v1") raw

structure FloorRecord where
  kind : Control.Kind
  descriptor : Fields
  original : Bytes
  id : Bytes
  ordinal : Nat
  previous : Bytes
  bootstrap : Bytes
  anchor : NativeCurrentPointer.State
  generation : Option Bytes
  manifest : Option Bytes
  cuts : List Node

def presentId : Option Bytes → Prop
  | none => False
  | some id => ContentId id
instance (id) : Decidable (presentId id) := by cases id <;> unfold presentId <;> infer_instance

def readFloor (sha : Bytes → Bytes) (kind : Control.Kind) (f : Fields) (raw : Bytes) :
    Option FloorRecord := do
  let f ← Control.check kind f raw
  let ordinal ← Index.field f "ordinal" >>= Index.decimal
  let previous ← Index.text (Index.field f "previous_record_id")
  let boot ← Index.text (Index.field f "bootstrap_id")
  let a ← Index.field f "anchor" >>= anchor
  let cuts ← Index.array (Index.field f "journal_cuts")
  let generation := Index.text (Index.field f "generation_id")
  let manifest := Index.text (Index.field f "manifest_id")
  let id ← NativeStateBytes.contentId sha (ascii "deltareduce.snapshot-provenance.trust-record.v1") raw
  if ContentId boot ∧
      ((kind = .init ∧ ordinal = 0 ∧ previous = ascii "GENESIS" ∧ generation = none ∧ manifest = none) ∨
       ((kind = .activate ∨ kind = .anchor) ∧ 0 < ordinal ∧ ContentId previous ∧
        presentId generation ∧ presentId manifest)) then
    some ⟨kind,f,raw,id,ordinal,previous,boot,a,generation,manifest,cuts⟩ else none

/-- Existing local metadata framing: exact u32 length, original canonical
payload, domain-separated trust-record digest. Not a consensus WAL slot. -/
def floorFrame (sha : Bytes → Bytes) (raw : Bytes) : Option Bytes :=
  let digest := sha (ascii "deltareduce.snapshot-provenance.trust-record.v1" ++ [0] ++ raw)
  if raw.length < 256^4 ∧ digest.length = 32 then
    some (NativeReceiptBytes.be 4 raw.length ++ raw ++ digest) else none

def KeepsFloor (old next : NativeCurrentPointer.State) : Prop :=
  old.height ≤ next.height ∧ (next.height = old.height → next = old)
instance (old next) : Decidable (KeepsFloor old next) := by unfold KeepsFloor; infer_instance

theorem keepsTrans {a b c} (left : KeepsFloor a b) (right : KeepsFloor b c) : KeepsFloor a c := by
  refine ⟨Nat.le_trans left.1 right.1,?_⟩
  intro same
  have ba : b.height = a.height := by have := left.1; have := right.1; omega
  have cb : c.height = b.height := same.trans ba.symm
  exact (right.2 cb).trans (left.2 ba)

def floorStep (boot : Bytes) (initial : NativeCurrentPointer.State) :
    Option FloorRecord → FloorRecord → Bool
  | none,row => decide (row.bootstrap = boot ∧ row.kind = .init ∧ row.ordinal = 0 ∧
      row.previous = ascii "GENESIS" ∧ row.anchor = initial)
  | some old,row => decide (row.bootstrap = boot ∧ row.kind ≠ .init ∧ row.ordinal = old.ordinal+1 ∧ row.previous = old.id ∧
      KeepsFloor old.anchor row.anchor ∧
      (row.kind = .anchor → row.generation = old.generation))

structure FloorInput where
  kind : Control.Kind
  descriptor : Fields
  original : Bytes

def floorRows (sha : Bytes → Bytes) (boot : Bytes) (initial : NativeCurrentPointer.State) :
    Option FloorRecord → List FloorInput → Option (List FloorRecord)
  | _,[] => some []
  | previous,input::rest => do
    let row ← readFloor sha input.kind input.descriptor input.original
    if floorStep boot initial previous row then
      let next ← floorRows sha boot initial (some row) rest
      some (row::next) else none

theorem rowsLength {sha boot initial previous inputs rows}
    (ok : floorRows sha boot initial previous inputs = some rows) : rows.length = inputs.length := by
  induction inputs generalizing previous rows with
  | nil => cases Option.some.inj ok; rfl
  | cons input rest ih =>
    simp only [floorRows,Bind.bind,Option.bind_eq_some_iff] at ok
    obtain ⟨row,hr,last⟩ := ok
    split at last <;> try contradiction
    obtain ⟨next,hn,last⟩ := Option.bind_eq_some_iff.mp last
    cases Option.some.inj last
    simpa using congrArg Nat.succ (ih hn)

inductive FloorHistory (boot : Bytes) (initial : NativeCurrentPointer.State) :
    Option FloorRecord → List FloorRecord → Prop
  | nil {previous} : FloorHistory boot initial previous []
  | cons {previous row rest} (step : floorStep boot initial previous row = true)
      (tail : FloorHistory boot initial (some row) rest) :
      FloorHistory boot initial previous (row::rest)

theorem rowsHistory {sha boot initial previous inputs rows}
    (ok : floorRows sha boot initial previous inputs = some rows) :
    FloorHistory boot initial previous rows := by
  induction inputs generalizing previous rows with
  | nil => cases Option.some.inj ok; exact .nil
  | cons input rest ih =>
    simp only [floorRows,Bind.bind,Option.bind_eq_some_iff] at ok
    obtain ⟨row,hr,last⟩ := ok
    split at last <;> try contradiction
    rename_i step
    obtain ⟨next,hn,last⟩ := Option.bind_eq_some_iff.mp last
    cases Option.some.inj last
    exact .cons step (ih hn)

theorem historyMonotone {boot initial previous rows}
    (h : FloorHistory boot initial (some previous) rows) :
    ∀ row ∈ rows, previous.anchor.height ≤ row.anchor.height := by
  induction rows generalizing previous with
  | nil => simp
  | cons row rest ih =>
    cases h with
    | cons step tail =>
      unfold floorStep at step
      have p := of_decide_eq_true step
      change row.bootstrap = boot ∧ row.kind ≠ .init ∧ row.ordinal = previous.ordinal+1 ∧
        row.previous = previous.id ∧ KeepsFloor previous.anchor row.anchor ∧
        (row.kind = .anchor → row.generation = previous.generation) at p
      intro selected found
      rcases List.mem_cons.mp found with same | later
      · subst selected; exact p.2.2.2.2.1.1
      · exact Nat.le_trans p.2.2.2.2.1.1 (ih tail selected later)

theorem historyKeepsFloor {boot initial previous rows}
    (h : FloorHistory boot initial (some previous) rows) :
    ∀ row ∈ rows, KeepsFloor previous.anchor row.anchor := by
  induction rows generalizing previous with
  | nil => simp
  | cons row rest ih =>
    cases h with
    | cons step tail =>
      unfold floorStep at step
      have p := of_decide_eq_true step
      intro selected found
      rcases List.mem_cons.mp found with same | later
      · subst selected; exact p.2.2.2.2.1
      · exact keepsTrans p.2.2.2.2.1 (ih tail selected later)

structure Floor where
  original : Bytes
  rows : List FloorRecord
  tip : FloorRecord

def bindFloor (sha : Bytes → Bytes) (b : Bootstrap)
    (inputs : List FloorInput) (independentOriginalLog : Bytes) : Option Floor := do
  let boot ← bootstrapId sha b.original
  let frames ← Index.collect (fun i => floorFrame sha i.original) inputs
  if frames.flatten = independentOriginalLog then
    let rows ← floorRows sha boot b.initialAnchor none inputs
    let tip ← rows.getLast?
    some ⟨independentOriginalLog,rows,tip⟩ else none

theorem boundFloorSource {sha b inputs raw out}
    (ok : bindFloor sha b inputs raw = some out) :
    out.original = raw ∧ ∃ boot frames,
      bootstrapId sha b.original = some boot ∧
      Index.collect (fun i => floorFrame sha i.original) inputs = some frames ∧
      frames.flatten = raw ∧ floorRows sha boot b.initialAnchor none inputs = some out.rows ∧
      out.rows.getLast? = some out.tip := by
  simp only [bindFloor,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨boot,hb,frames,hf,last⟩ := ok
  split at last <;> try contradiction
  rename_i original
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨rows,hr,tip,ht,last⟩ := last
  cases Option.some.inj last
  exact ⟨rfl,boot,frames,hb,hf,original,hr,ht⟩

theorem boundFloorNoRecordErasure {sha b inputs raw out}
    (ok : bindFloor sha b inputs raw = some out) : out.rows.length = inputs.length := by
  obtain ⟨_,boot,frames,_,_,_,hr,_⟩ := boundFloorSource ok
  exact rowsLength hr

theorem floorComplete {sha b inputs raw boot frames rows tip}
    (hb : bootstrapId sha b.original = some boot)
    (hf : Index.collect (fun i => floorFrame sha i.original) inputs = some frames)
    (original : frames.flatten = raw)
    (hr : floorRows sha boot b.initialAnchor none inputs = some rows)
    (ht : rows.getLast? = some tip) :
    bindFloor sha b inputs raw = some ⟨raw,rows,tip⟩ := by
  simp only [bindFloor,hb,hf,Bind.bind,Option.bind,if_pos original,hr,ht]

theorem initialFloor {boot initial rows} (history : FloorHistory boot initial none rows) :
    ∀ row ∈ rows, KeepsFloor initial row.anchor := by
  cases history with
  | nil => simp
  | @cons previous row rest step tail =>
    unfold floorStep at step
    have p := of_decide_eq_true step
    intro selected found
    rcases List.mem_cons.mp found with same | later
    · subst selected
      rw [p.2.2.2.2]
      exact ⟨Nat.le_refl _,fun _ => rfl⟩
    · have h := historyKeepsFloor tail selected later
      simpa only [p.2.2.2.2] using h

theorem floorNeverRollsBack {sha b inputs raw out}
    (ok : bindFloor sha b inputs raw = some out) :
    ∀ row ∈ out.rows, KeepsFloor b.initialAnchor row.anchor := by
  obtain ⟨_,boot,frames,_,_,_,hr,_⟩ := boundFloorSource ok
  exact initialFloor (rowsHistory hr)

theorem emptyLogRejected (sha : Bytes → Bytes) (b : Bootstrap) (raw : Bytes) :
    bindFloor sha b [] raw = none := by
  unfold bindFloor
  cases bootstrapId sha b.original <;> simp [Index.collect,floorRows]

theorem exactImportedFloor {sha b inputs raw out imported}
    (ok : bindFloor sha b inputs raw = some out)
    (same : imported = out.tip.anchor) :
    ∃ rows, rows = out.rows ∧ rows.getLast?.map FloorRecord.anchor = some imported := by
  obtain ⟨_,boot,frames,_,_,_,hr,ht⟩ := boundFloorSource ok
  exact ⟨out.rows,rfl,by simp only [ht,Option.map_some,same]⟩

end DeltaReduce.ProfileSource.Origin
