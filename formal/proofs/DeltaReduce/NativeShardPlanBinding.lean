import DeltaReduce.NativeShardPlanBytes
import DeltaReduce.NativeShardPartition

/-! Full original004 plan bytes and derived schema partition. Hash adapters and
manifest/configuration/producer authority remain explicit unresolved boundaries. -/
namespace DeltaReduce.NativeShardPlanBinding
open NativeReceiptBytes (Bytes)
open NativeVoteBytes (ascii parseDecimal)
open NativeShardPartition (Entry)
open NativeShardPlanBytes (Wire EntryWire)

def entry (w : EntryWire) : Option Entry := do
  let c ← parseDecimal w.count
  let s ← parseDecimal w.start
  let o ← parseDecimal w.ordinal
  let p ← parseDecimal w.payload
  let f ← parseDecimal w.offset
  some ⟨c,s,o,p,w.name,f⟩

def EntrySource (w : EntryWire) (e : Entry) : Prop :=
  parseDecimal w.count = some e.count ∧ parseDecimal w.start = some e.start ∧
  parseDecimal w.ordinal = some e.ordinal ∧ parseDecimal w.payload = some e.payload ∧
  parseDecimal w.offset = some e.offset ∧ e.name = w.name

theorem entrySource {w e} (h : entry w = some e) : EntrySource w e := by
  simp only [entry,bind,Option.bind_eq_some_iff] at h
  obtain ⟨c,hc,s,hs,o,ho,p,hp,f,hf,last⟩ := h
  cases Option.some.inj last
  exact ⟨hc,hs,ho,hp,hf,rfl⟩

def entries : List EntryWire → Option (List Entry)
  | [] => some []
  | w::ws => do
      let e ← entry w
      let es ← entries ws
      some (e::es)

theorem entriesSource {ws es} (h : entries ws = some es) :
    ws.length = es.length ∧ ∀ (i : Nat) w, ws[i]? = some w → ∃ e, es[i]? = some e ∧ EntrySource w e := by
  induction ws generalizing es with
  | nil => simp [entries] at h; subst es; exact ⟨rfl,by simp⟩
  | cons w ws ih =>
    simp only [entries,bind,Option.bind_eq_some_iff] at h
    obtain ⟨e,he,tail,ht,last⟩ := h
    cases Option.some.inj last
    have rest := ih ht
    refine ⟨by simpa using rest.1,?_⟩
    intro i x hx
    cases i with
    | zero => simp at hx; subst x; exact ⟨e,by simp,entrySource he⟩
    | succ i => simpa using rest.2 i x (by simpa using hx)

structure Plan where
  wire : Wire
  entries : List Entry
  target : Nat
  total : Nat
  deriving DecidableEq, Repr

def interpret (w : Wire) : Option Plan := do
  let es ← entries w.entries
  let target ← parseDecimal w.target
  let total ← parseDecimal w.total
  some ⟨w,es,target,total⟩

structure PlanSource (w : Wire) (p : Plan) : Prop where
  original : p.wire = w
  entries : entries w.entries = some p.entries
  target : parseDecimal w.target = some p.target
  total : parseDecimal w.total = some p.total

theorem interpreted {w p} (h : interpret w = some p) : PlanSource w p := by
  simp only [interpret,bind,Option.bind_eq_some_iff] at h
  obtain ⟨es,he,t,ht,n,hn,last⟩ := h
  cases Option.some.inj last
  exact ⟨rfl,he,ht,hn⟩

def hashInput (raw : Bytes) := ascii "deltareduce.004.shard-plan.v1" ++ [0] ++ raw

def Links (hash : Bytes → Bytes) (scaleRaw : Bytes)
    (s : NativeSchemaBinding.Bound) (p : Plan) : Prop :=
  p.wire.version = ascii "1.0.0" ∧ p.wire.kind = ascii "SHARD_PLAN" ∧
  p.wire.semantics = s.scale.wire.semantics ∧ p.wire.profile = s.scale.wire.profile ∧
  p.wire.schema = s.scale.wire.schema ∧
  p.wire.scale = hash (NativeScaleBinding.hashInput scaleRaw) ∧ p.total = s.schema.total ∧
  NativeVoteBytes.ContentId p.wire.scale
instance (hash raw s p) : Decidable (Links hash raw s p) := by unfold Links; infer_instance

structure Bound where
  inputs : NativeSchemaBinding.Bound
  plan : Plan
  deriving DecidableEq, Repr

def bind (hash : Bytes → Bytes) (schemaRaw scaleRaw planRaw : Bytes) : Option Bound := do
  let s ← NativeSchemaBinding.bind hash schemaRaw scaleRaw
  let w ← NativeShardPlanBytes.decode planRaw
  let p ← interpret w
  let computed ← NativeShardPartition.build s.schema p.target
  if Links hash scaleRaw s p ∧ computed = p.entries then some ⟨s,p⟩ else none

structure Source (hash : Bytes → Bytes) (schemaRaw scaleRaw planRaw : Bytes) (b : Bound) : Prop where
  inputs : NativeSchemaBinding.bind hash schemaRaw scaleRaw = some b.inputs
  wire : NativeShardPlanBytes.decode planRaw = some b.plan.wire
  plan : interpret b.plan.wire = some b.plan
  computed : NativeShardPartition.build b.inputs.schema b.plan.target = some b.plan.entries
  links : Links hash scaleRaw b.inputs b.plan

theorem boundSource {hash schemaRaw scaleRaw planRaw b}
    (h : bind hash schemaRaw scaleRaw planRaw = some b) : Source hash schemaRaw scaleRaw planRaw b := by
  unfold bind at h
  simp only [Bind.bind,Option.bind_eq_some_iff] at h
  obtain ⟨s,hs,w,hw,p,hp,computed,hc,last⟩ := h
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  have src := interpreted hp
  exact ⟨hs,by rw [src.original]; exact hw,by rw [src.original]; exact hp,
    by rw [← checks.2]; exact hc,checks.1⟩

theorem bindFromSource {hash schemaRaw scaleRaw planRaw b}
    (h : Source hash schemaRaw scaleRaw planRaw b) : bind hash schemaRaw scaleRaw planRaw = some b := by
  simp only [bind,h.inputs,h.wire,h.plan,h.computed,Bind.bind,Option.bind]
  have eq : Bound.mk b.inputs b.plan = b := by cases b; rfl
  rw [if_pos ⟨h.links,True.intro⟩,eq]

theorem exactPreimage {hash schemaRaw scaleRaw planRaw b}
    (h : bind hash schemaRaw scaleRaw planRaw = some b) : NativeShardPlanBytes.encode b.plan.wire = planRaw :=
  (NativeShardPlanBytes.decoded (boundSource h).wire).2.2.2

theorem originalEntries {hash schemaRaw scaleRaw planRaw b}
    (h : bind hash schemaRaw scaleRaw planRaw = some b) :
    b.plan.wire.entries.length = b.plan.entries.length ∧
    ∀ (i : Nat) w, b.plan.wire.entries[i]? = some w → ∃ e, b.plan.entries[i]? = some e ∧ EntrySource w e :=
  entriesSource (interpreted (boundSource h).plan).entries

theorem completePartition {hash schemaRaw scaleRaw planRaw b}
    (h : bind hash schemaRaw scaleRaw planRaw = some b) :
    NativeShardPartition.Target b.plan.target ∧ b.plan.entries.length ≤ 4096 ∧
    NativeShardPartition.Span 0 0 b.plan.entries b.inputs.schema.total :=
  NativeShardPartition.builtPartition (boundSource h).computed

theorem completeCoverage {hash schemaRaw scaleRaw planRaw b}
    (h : bind hash schemaRaw scaleRaw planRaw = some b) (c : Nat) (inside : c < b.inputs.schema.total) :
    ∃ e ∈ b.plan.entries, e.start ≤ c ∧ c < e.start+e.count :=
  NativeShardPartition.builtComplete (boundSource h).computed c inside

theorem noOverlap {hash schemaRaw scaleRaw planRaw b}
    (h : bind hash schemaRaw scaleRaw planRaw = some b) :
    b.plan.entries.Pairwise (fun x y => x.start+x.count ≤ y.start ∧ x.ordinal < y.ordinal) :=
  NativeShardPartition.builtNoOverlap (boundSource h).computed

theorem exactPayloadBounds {hash schemaRaw scaleRaw planRaw b}
    (h : bind hash schemaRaw scaleRaw planRaw = some b) (e : Entry) (member : e ∈ b.plan.entries) :
    0 < e.count ∧ e.count ≤ 524288 ∧ e.payload = 2*e.count ∧ e.payload ≤ b.plan.target ∧
    e.payload ≤ 1048576 := NativeShardPartition.builtPayload (boundSource h).computed e member

def headerEntry (h : NativeQHeader.Header) : Entry :=
  ⟨h.count,h.start,h.ordinal,2*h.count,h.wire.segment,h.offset⟩

structure QBound where
  plan : Bound
  q : NativeScaleBinding.Bound
  deriving DecidableEq, Repr

def QLinks (hash : Bytes → Bytes) (planRaw : Bytes) (p : Bound) (q : NativeScaleBinding.Bound) : Prop :=
  q.table = p.inputs.scale ∧ q.block.header.wire.plan = hash (hashInput planRaw) ∧
  p.plan.entries[q.block.header.ordinal]? = some (headerEntry q.block.header)
instance (hash raw p q) : Decidable (QLinks hash raw p q) := by unfold QLinks; infer_instance

def bindQ (hash : Bytes → Bytes) (schemaRaw scaleRaw planRaw qRaw : Bytes) : Option QBound := do
  let p ← bind hash schemaRaw scaleRaw planRaw
  let q ← NativeScaleBinding.bind hash scaleRaw qRaw
  if QLinks hash planRaw p q then some ⟨p,q⟩ else none

structure QSource (hash : Bytes → Bytes) (schemaRaw scaleRaw planRaw qRaw : Bytes) (b : QBound) : Prop where
  plan : bind hash schemaRaw scaleRaw planRaw = some b.plan
  q : NativeScaleBinding.bind hash scaleRaw qRaw = some b.q
  links : QLinks hash planRaw b.plan b.q

theorem qSource {hash schemaRaw scaleRaw planRaw qRaw b}
    (h : bindQ hash schemaRaw scaleRaw planRaw qRaw = some b) : QSource hash schemaRaw scaleRaw planRaw qRaw b := by
  unfold bindQ at h
  simp only [Bind.bind,Option.bind_eq_some_iff] at h
  obtain ⟨p,hp,q,hq,last⟩ := h
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  exact ⟨hp,hq,checks⟩

theorem qFromSource {hash schemaRaw scaleRaw planRaw qRaw b}
    (h : QSource hash schemaRaw scaleRaw planRaw qRaw b) : bindQ hash schemaRaw scaleRaw planRaw qRaw = some b := by
  simp only [bindQ,h.plan,h.q,Bind.bind,Option.bind]
  have eq : QBound.mk b.plan b.q = b := by cases b; rfl
  rw [if_pos h.links,eq]

theorem qExactSlot {hash schemaRaw scaleRaw planRaw qRaw b}
    (h : bindQ hash schemaRaw scaleRaw planRaw qRaw = some b) :
    b.plan.plan.entries[b.q.block.header.ordinal]? = some (headerEntry b.q.block.header) :=
  (qSource h).links.2.2

theorem qCompletePlan {hash schemaRaw scaleRaw planRaw qRaw b}
    (h : bindQ hash schemaRaw scaleRaw planRaw qRaw = some b) :
    NativeShardPartition.Span 0 0 b.plan.plan.entries b.plan.inputs.schema.total :=
  (completePartition (qSource h).plan).2.2

end DeltaReduce.NativeShardPlanBinding
