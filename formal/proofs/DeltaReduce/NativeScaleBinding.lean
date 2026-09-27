import DeltaReduce.NativeScaleBytes
import DeltaReduce.ArithmeticBinding

/-! Parse original scale metadata before extracting quantum. Hash is an explicit
unverified adapter; neither schema/plan coverage nor source authority is assumed
to follow from a syntactically valid identifier or an adapter equality. -/
namespace DeltaReduce.NativeScaleBinding
open NativeReceiptBytes (Bytes)
open NativeVoteBytes (ascii parseDecimal ContentId)
open NativeScaleBytes (SegmentWire Wire)

structure Segment where
  wire : SegmentWire
  count : Nat
  start : Nat
  numerator : Nat
  denominator : Nat
  ordinal : Nat
  deriving DecidableEq, Repr

def SegmentValid (s : Segment) : Prop :=
  parseDecimal s.wire.count = some s.count ∧ parseDecimal s.wire.start = some s.start ∧
  parseDecimal s.wire.numerator = some s.numerator ∧
  parseDecimal s.wire.denominator = some s.denominator ∧
  parseDecimal s.wire.ordinal = some s.ordinal ∧ NativeQHeader.Token s.wire.name ∧
  0 < s.count ∧ s.start + s.count ≤ 1073741824 ∧ s.ordinal < 65536 ∧
  0 < s.numerator ∧ s.numerator < 2^32 ∧ 0 < s.denominator ∧
  s.denominator < 2^32 ∧ Nat.gcd s.numerator s.denominator = 1
instance (s) : Decidable (SegmentValid s) := by unfold SegmentValid; infer_instance

def interpretSegment (w : SegmentWire) : Option Segment := do
  let count ← parseDecimal w.count
  let start ← parseDecimal w.start
  let numerator ← parseDecimal w.numerator
  let denominator ← parseDecimal w.denominator
  let ordinal ← parseDecimal w.ordinal
  let s := Segment.mk w count start numerator denominator ordinal
  if SegmentValid s then some s else none

theorem segmentInterpreted {w s} (h : interpretSegment w = some s) :
    s.wire = w ∧ SegmentValid s := by
  unfold interpretSegment at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨c,_,a,_,n,_,d,_,o,_,last⟩ := h
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  exact ⟨rfl,checks⟩

theorem interpretValidSegment (s : Segment) (valid : SegmentValid s) :
    interpretSegment s.wire = some s := by
  rcases valid with ⟨a,b,c,d,e,rest⟩
  simp only [interpretSegment,a,b,c,d,e,bind,Option.bind]
  cases s
  exact if_pos ⟨a,b,c,d,e,rest⟩

def loadSegments : List SegmentWire → Option (List Segment)
  | [] => some []
  | w :: ws => do
      let s ← interpretSegment w
      let ss ← loadSegments ws
      some (s::ss)

theorem segmentListSource {ws ss} (h : loadSegments ws = some ss) :
    ss.map Segment.wire = ws ∧ ∀ s ∈ ss, SegmentValid s := by
  induction ws generalizing ss with
  | nil => simp [loadSegments] at h; subst ss; simp
  | cons w ws ih =>
    simp only [loadSegments,bind,Option.bind_eq_some_iff] at h
    obtain ⟨s,hs,tail,ht,last⟩ := h
    cases Option.some.inj last
    have head := segmentInterpreted hs
    have rest := ih ht
    exact ⟨by simp [head.1,rest.1], by simpa using And.intro head.2 rest.2⟩

theorem loadValidSegments (ss : List Segment) (valid : ∀ s ∈ ss, SegmentValid s) :
    loadSegments (ss.map Segment.wire) = some ss := by
  induction ss with
  | nil => rfl
  | cons s ss ih =>
    have tail : ∀ x ∈ ss, SegmentValid x := by intro x hx; exact valid x (by simp [hx])
    simp [loadSegments,interpretValidSegment s (valid s (by simp)),ih tail]

def layout : Nat → Nat → List Segment → Option Nat
  | _, cursor, [] => some cursor
  | ordinal, cursor, s::ss =>
      if s.ordinal = ordinal ∧ s.start = cursor then
        layout (ordinal+1) (cursor+s.count) ss else none

theorem layoutSum {ordinal cursor ss total} (h : layout ordinal cursor ss = some total) :
    total = cursor + (ss.map Segment.count).sum := by
  induction ss generalizing ordinal cursor with
  | nil => simpa [layout] using (Option.some.inj h).symm
  | cons s ss ih =>
    unfold layout at h
    split at h <;> try contradiction
    have tail := ih h
    simpa [Nat.add_assoc] using tail

structure Table where
  wire : Wire
  segments : List Segment
  total : Nat
  deriving DecidableEq, Repr

def TableChecks (t : Table) : Prop :=
  t.wire.semantics = NativeVoteBytes.nativeSemantics ∧
  t.wire.profile = NativeQHeader.nativeProfile ∧ ContentId t.wire.schema ∧
  t.wire.version = ascii "1.0.0" ∧ t.wire.kind = ascii "QUANTIZATION_SCALE_TABLE" ∧
  t.segments ≠ [] ∧ t.total ≤ 1073741824 ∧ layout 0 0 t.segments = some t.total ∧
  (t.segments.map (fun s => s.wire.name)).Nodup
instance (t) : Decidable (TableChecks t) := by unfold TableChecks; infer_instance

def interpret (w : Wire) : Option Table := do
  let segments ← loadSegments w.segments
  let total ← parseDecimal w.total
  let t := Table.mk w segments total
  if TableChecks t then some t else none

structure Source (w : Wire) (t : Table) : Prop where
  original : t.wire = w
  segments : loadSegments w.segments = some t.segments
  total : parseDecimal w.total = some t.total
  checks : TableChecks t

theorem interpreted {w t} (h : interpret w = some t) : Source w t := by
  unfold interpret at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨ss,hs,total,ht,last⟩ := h
  split at last <;> try contradiction
  rename_i checked
  cases Option.some.inj last
  exact ⟨rfl,hs,ht,checked⟩

theorem interpretFromSource {w t} (h : Source w t) : interpret w = some t := by
  simp only [interpret,h.segments,h.total,bind,Option.bind]
  have same : Table.mk w t.segments t.total = t := by rw [← h.original]
  rw [same]
  exact if_pos h.checks

def decode (raw : Bytes) : Option Table := do
  let w ← NativeScaleBytes.decode raw
  interpret w

theorem decodedSource {raw t} (h : decode raw = some t) :
    NativeScaleBytes.decode raw = some t.wire ∧ Source t.wire t := by
  unfold decode at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨w,hw,ht⟩ := h
  have source := interpreted ht
  exact ⟨by rw [source.original]; exact hw, by simpa only [source.original] using source⟩

theorem decodedFromComponents {raw w t} (parsed : NativeScaleBytes.decode raw = some w)
    (computed : interpret w = some t) : decode raw = some t := by
  simp [decode,parsed,computed]

theorem exactPreimage {raw t} (h : decode raw = some t) :
    NativeScaleBytes.encode t.wire = raw := (NativeScaleBytes.decoded (decodedSource h).1).2.2.2

theorem exactSegments {raw t} (h : decode raw = some t) :
    t.segments.map Segment.wire = t.wire.segments ∧ ∀ s ∈ t.segments, SegmentValid s :=
  segmentListSource (decodedSource h).2.segments

theorem exactTotal {raw t} (h : decode raw = some t) :
    t.total = (t.segments.map Segment.count).sum := by
  have checked := (decodedSource h).2.checks
  simpa using layoutSum checked.2.2.2.2.2.2.2.1

def hashInput (raw : Bytes) := ascii "deltareduce.004.scale-table.v1" ++ [0] ++ raw

def selected (t : Table) (q : NativeQHeader.Joined) : Option Segment :=
  t.segments.find? (fun s => s.wire.name == q.header.wire.segment)

def Links (hash : Bytes → Bytes) (raw : Bytes) (t : Table) (q : NativeQHeader.Joined)
    (s : Segment) : Prop :=
  hash (hashInput raw) = q.header.wire.scale ∧
  t.wire.semantics = q.header.wire.semantics ∧ t.wire.profile = q.header.wire.profile ∧
  t.wire.schema = q.header.wire.schema ∧ q.header.offset + q.header.count ≤ s.count ∧
  q.header.start = s.start + q.header.offset
instance (hash raw t q s) : Decidable (Links hash raw t q s) := by unfold Links; infer_instance

structure Bound where
  table : Table
  block : NativeQHeader.Joined
  segment : Segment
  deriving DecidableEq, Repr

def bind (hash : Bytes → Bytes) (scaleRaw qRaw : Bytes) : Option Bound := do
  let t ← decode scaleRaw
  let q ← NativeQHeader.join qRaw
  let s ← selected t q
  if Links hash scaleRaw t q s then some ⟨t,q,s⟩ else none

structure BoundSource (hash : Bytes → Bytes) (scaleRaw qRaw : Bytes) (b : Bound) : Prop where
  table : decode scaleRaw = some b.table
  block : NativeQHeader.join qRaw = some b.block
  selection : selected b.table b.block = some b.segment
  links : Links hash scaleRaw b.table b.block b.segment

theorem boundSource {hash scaleRaw qRaw b} (h : bind hash scaleRaw qRaw = some b) :
    BoundSource hash scaleRaw qRaw b := by
  unfold bind at h
  simp only [Bind.bind,Option.bind_eq_some_iff] at h
  obtain ⟨t,ht,q,hq,s,hs,last⟩ := h
  split at last <;> try contradiction
  rename_i checked
  cases Option.some.inj last
  exact ⟨ht,hq,hs,checked⟩

theorem bindFromSource {hash scaleRaw qRaw b} (h : BoundSource hash scaleRaw qRaw b) :
    bind hash scaleRaw qRaw = some b := by
  simp only [bind,h.table,h.block,h.selection,Bind.bind,Option.bind]
  have same : Bound.mk b.table b.block b.segment = b := by cases b; rfl
  rw [if_pos h.links,same]

theorem boundSegment {hash scaleRaw qRaw b} (h : bind hash scaleRaw qRaw = some b) :
    b.segment ∈ b.table.segments ∧ b.segment.wire.name = b.block.header.wire.segment ∧
    SegmentValid b.segment := by
  have src := boundSource h
  have member := List.mem_of_find?_eq_some src.selection
  exact ⟨member,by simpa [selected] using List.find?_some src.selection,
    (exactSegments src.table).2 b.segment member⟩

def Bound.quantum (b : Bound) : NativeBinding.Rational :=
  ⟨b.segment.numerator,b.segment.denominator⟩

theorem boundQuantum {hash scaleRaw qRaw b} (h : bind hash scaleRaw qRaw = some b) :
    0 < b.segment.numerator ∧ b.segment.numerator < 2^32 ∧
    0 < b.segment.denominator ∧ b.segment.denominator < 2^32 ∧
    Nat.gcd b.segment.numerator b.segment.denominator = 1 :=
  (boundSegment h).2.2.2.2.2.2.2.2.2.2.2

theorem boundOriginalSegment {hash scaleRaw qRaw b} (h : bind hash scaleRaw qRaw = some b) :
    b.segment.wire ∈ b.table.wire.segments := by
  rw [← (exactSegments (boundSource h).table).1]
  exact List.mem_map.mpr ⟨b.segment,(boundSegment h).1,rfl⟩

theorem boundParsedQuantum {hash scaleRaw qRaw b} (h : bind hash scaleRaw qRaw = some b) :
    parseDecimal b.segment.wire.numerator = some b.segment.numerator ∧
    parseDecimal b.segment.wire.denominator = some b.segment.denominator := by
  have valid := (boundSegment h).2.2
  exact ⟨valid.2.2.1,valid.2.2.2.1⟩

/-- Equality under the supplied adapter is not a SHA implementation/authentication proof. -/
theorem boundHashPreimage {hash scaleRaw qRaw b} (h : bind hash scaleRaw qRaw = some b) :
    hash (hashInput (NativeScaleBytes.encode b.table.wire)) = b.block.header.wire.scale := by
  rw [exactPreimage (boundSource h).table]
  exact (boundSource h).links.1

theorem boundCoordinates {hash scaleRaw qRaw b} (h : bind hash scaleRaw qRaw = some b)
    (i : Nat) (inside : i < b.block.frame.values.length) :
    b.block.header.offset + i < b.segment.count ∧
    b.block.header.start + i = b.segment.start + (b.block.header.offset + i) := by
  have src := boundSource h
  have count := (NativeQHeader.joined src.block).2.2
  have range := src.links.2.2.2.2.1
  have start := src.links.2.2.2.2.2
  omega

theorem boundPayload {hash scaleRaw qRaw b} (h : bind hash scaleRaw qRaw = some b) :
    NativeQBytes.PayloadRelation b.block.frame.payload b.block.frame.values ∧
    b.block.frame.payload.length = 2 * b.block.header.count :=
  NativeQHeader.joinedPayload (boundSource h).block

end DeltaReduce.NativeScaleBinding
