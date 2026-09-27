import DeltaReduce.NativeSchemaBytes
import DeltaReduce.NativeScaleBinding

/-! Original schema shapes/omission/aliases and exact scale-segment coverage.
The supplied hash adapter is unverified. No plan/manifest/admission authority. -/
namespace DeltaReduce.NativeSchemaBinding
open NativeReceiptBytes (Bytes)
open NativeVoteBytes (ascii parseDecimal)

def nameFirst (b : UInt8) : Bool :=
  (65 ≤ b.toNat && b.toNat ≤ 90) || (97 ≤ b.toNat && b.toNat ≤ 122) ||
  (48 ≤ b.toNat && b.toNat ≤ 57) || b == 95
def nameRest (b : UInt8) : Bool := nameFirst b || b == 46 || b == 45
def NameValid (s : Bytes) : Prop :=
  0 < s.length ∧ s.length ≤ 256 ∧ s.head?.any nameFirst = true ∧ s.all nameRest = true
instance (s) : Decidable (NameValid s) := by unfold NameValid; infer_instance

def less : Bytes → Bytes → Bool
  | [], [] => false
  | [], _::_ => true
  | _::_, [] => false
  | a::xs,b::ys => if a = b then less xs ys else a.toNat < b.toNat

def Ordered (names : List Bytes) : Prop := names.Pairwise (fun a b => less a b = true)
instance (names) : Decidable (Ordered names) := by unfold Ordered; infer_instance

def dimensions : List Bytes → Option (List Nat)
  | [] => some []
  | x::xs => do
      let n ← parseDecimal x
      let ns ← dimensions xs
      some (n::ns)

theorem dimensionsRetained {raw ns} (h : dimensions raw = some ns) :
    raw.length = ns.length ∧ ∀ (i : Nat) (x : Bytes), raw[i]? = some x → ∃ n, ns[i]? = some n ∧
      parseDecimal x = some n := by
  induction raw generalizing ns with
  | nil =>
    simp [dimensions] at h; subst ns
    exact ⟨rfl,by simp⟩
  | cons x xs ih =>
    simp only [dimensions,bind,Option.bind_eq_some_iff] at h
    obtain ⟨n,hn,tail,ht,last⟩ := h
    cases Option.some.inj last
    have rest := ih ht
    refine ⟨by simpa using rest.1,?_⟩
    intro i y hy
    cases i with
    | zero => simp at hy; subst y; exact ⟨n,by simp,hn⟩
    | succ i => simpa using rest.2 i y (by simpa using hy)

structure Tensor where
  wire : NativeSchemaBytes.Parameter
  dims : List Nat
  deriving DecidableEq, Repr

def Tensor.count (p : Tensor) := p.dims.prod

def TensorChecks (p : Tensor) : Prop :=
  dimensions p.wire.shape = some p.dims ∧ NameValid p.wire.name ∧
  p.wire.dtype ∈ [ascii "bfloat16",ascii "float16",ascii "float32",ascii "float64"] ∧
  p.dims.length ≤ 32 ∧ (∀ d ∈ p.dims, 0 < d ∧ d ≤ 1073741824) ∧
  p.count ≤ 1073741824
instance (p) : Decidable (TensorChecks p) := by unfold TensorChecks; infer_instance

def tensor (w : NativeSchemaBytes.Parameter) : Option Tensor := do
  let dims ← dimensions w.shape
  let p := Tensor.mk w dims
  if TensorChecks p then some p else none

theorem tensorSource {w p} (h : tensor w = some p) :
    p.wire = w ∧ TensorChecks p := by
  unfold tensor at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨dims,_,last⟩ := h
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  exact ⟨rfl,checks⟩

theorem tensorFromChecks (p : Tensor) (h : TensorChecks p) : tensor p.wire = some p := by
  simp only [tensor,h.1,bind,Option.bind]
  cases p
  exact if_pos h

def tensors : List NativeSchemaBytes.Parameter → Option (List Tensor)
  | [] => some []
  | p::ps => do
      let x ← tensor p
      let xs ← tensors ps
      some (x::xs)

theorem tensorsSource {raw ps} (h : tensors raw = some ps) :
    ps.map Tensor.wire = raw ∧ ∀ p ∈ ps, TensorChecks p := by
  induction raw generalizing ps with
  | nil => simp [tensors] at h; subst ps; simp
  | cons w ws ih =>
    simp only [tensors,bind,Option.bind_eq_some_iff] at h
    obtain ⟨p,hp,tail,ht,last⟩ := h
    cases Option.some.inj last
    have head := tensorSource hp
    have rest := ih ht
    exact ⟨by simp [head.1,rest.1],by simpa using And.intro head.2 rest.2⟩

theorem tensorsFromChecks (ps : List Tensor) (h : ∀ p ∈ ps, TensorChecks p) :
    tensors (ps.map Tensor.wire) = some ps := by
  induction ps with
  | nil => rfl
  | cons p ps ih =>
    have tail : ∀ x ∈ ps, TensorChecks x := by intro x hx; exact h x (by simp [hx])
    simp [tensors,tensorFromChecks p (h p (by simp)),ih tail]

structure Row where
  name : Bytes
  start : Nat
  count : Nat
  ordinal : Nat
  deriving DecidableEq, Repr

def place (cursor ordinal : Nat) : List Tensor → List Row
  | [] => []
  | p::ps => ⟨p.wire.name,cursor,p.count,ordinal⟩ :: place (cursor+p.count) (ordinal+1) ps

theorem placedNames (ps : List Tensor) (cursor ordinal : Nat) :
    (place cursor ordinal ps).map Row.name = ps.map (fun p => p.wire.name) := by
  induction ps generalizing cursor ordinal with
  | nil => rfl
  | cons p ps ih => simp [place,ih]

theorem placedCounts (ps : List Tensor) (cursor ordinal : Nat) :
    (place cursor ordinal ps).map Row.count = ps.map Tensor.count := by
  induction ps generalizing cursor ordinal with
  | nil => rfl
  | cons p ps ih => simp [place,ih]

theorem placedLength (ps : List Tensor) (cursor ordinal : Nat) :
    (place cursor ordinal ps).length = ps.length := by
  have h := congrArg List.length (placedNames ps cursor ordinal)
  simpa using h

theorem placedAt {ps : List Tensor} {i : Nat} {p : Tensor} (h : ps[i]? = some p) (cursor ordinal : Nat) :
    (place cursor ordinal ps)[i]? = some
      ⟨p.wire.name,cursor+((ps.take i).map Tensor.count).sum,p.count,ordinal+i⟩ := by
  induction ps generalizing i cursor ordinal with
  | nil => simp at h
  | cons x xs ih =>
    cases i with
    | zero => simp at h; subst p; simp [place]
    | succ i =>
      have hp : xs[i]? = some p := by simpa using h
      simpa [place,Nat.add_assoc,Nat.add_comm,Nat.add_left_comm] using
        ih hp (cursor+x.count) (ordinal+1)

structure Schema where
  wire : NativeSchemaBytes.Wire
  parameters : List Tensor
  deriving DecidableEq, Repr

def Schema.included (s : Schema) : List Tensor :=
  s.parameters.filter (fun p => p.wire.trainable || s.wire.policy == ascii "INCLUDE_ALL")
def Schema.rows (s : Schema) := place 0 0 s.included
def Schema.total (s : Schema) := (s.included.map Tensor.count).sum
def Schema.names (s : Schema) := s.parameters.map (fun p => p.wire.name)

def Checks (s : Schema) : Prop :=
  s.wire.version = ascii "1.0.0" ∧
  s.wire.policy ∈ [ascii "INCLUDE_ALL",ascii "OMIT_FROZEN"] ∧
  s.parameters ≠ [] ∧ Ordered s.names ∧ s.names.Nodup ∧
  Ordered (s.wire.aliases.map Prod.fst) ∧ (s.wire.aliases.map Prod.fst).Nodup ∧
  (∀ a ∈ s.wire.aliases, NameValid a.1 ∧ a.1 ∉ s.names ∧ a.2 ∈ s.names) ∧
  s.included ≠ [] ∧ s.total ≤ 1073741824 ∧
  ∀ p ∈ s.included, NativeQHeader.Token p.wire.name
instance (s) : Decidable (Checks s) := by unfold Checks; infer_instance

def interpret (w : NativeSchemaBytes.Wire) : Option Schema := do
  let ps ← tensors w.parameters
  let s := Schema.mk w ps
  if Checks s then some s else none

structure Source (w : NativeSchemaBytes.Wire) (s : Schema) : Prop where
  original : s.wire = w
  parameters : tensors w.parameters = some s.parameters
  checks : Checks s

theorem interpreted {w s} (h : interpret w = some s) : Source w s := by
  unfold interpret at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨ps,hp,last⟩ := h
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  exact ⟨rfl,hp,checks⟩

theorem interpretFromSource {w s} (h : Source w s) : interpret w = some s := by
  simp only [interpret,h.parameters,bind,Option.bind]
  have eq : Schema.mk w s.parameters = s := by rw [← h.original]
  rw [eq]; exact if_pos h.checks

def decode (raw : Bytes) : Option Schema := do
  let w ← NativeSchemaBytes.decode raw
  interpret w

theorem decodedSource {raw s} (h : decode raw = some s) :
    NativeSchemaBytes.decode raw = some s.wire ∧ Source s.wire s := by
  unfold decode at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨w,hw,hs⟩ := h
  have src := interpreted hs
  exact ⟨by rw [src.original]; exact hw, by simpa only [src.original] using src⟩

theorem decodedFromComponents {raw w s} (h : NativeSchemaBytes.decode raw = some w)
    (hs : interpret w = some s) : decode raw = some s := by simp [decode,h,hs]

theorem exactPreimage {raw s} (h : decode raw = some s) :
    NativeSchemaBytes.encode s.wire = raw := (NativeSchemaBytes.decoded (decodedSource h).1).2.2.2

theorem originalParameters {raw s} (h : decode raw = some s) :
    s.parameters.map Tensor.wire = s.wire.parameters ∧ ∀ p ∈ s.parameters, TensorChecks p :=
  tensorsSource (decodedSource h).2.parameters

theorem includedOriginal {s : Schema} {p : Tensor} (h : p ∈ s.included) : p ∈ s.parameters :=
  (List.mem_filter.mp h).1

theorem omitFrozen {s : Schema} {p : Tensor} (policy : s.wire.policy = ascii "OMIT_FROZEN")
    (frozen : p.wire.trainable = false) : p ∉ s.included := by
  simp [Schema.included,policy,frozen,ascii]

theorem includedAll {s : Schema} (policy : s.wire.policy = ascii "INCLUDE_ALL") :
    s.included = s.parameters := by simp [Schema.included,policy]

theorem aliasOwners {raw s} (h : decode raw = some s) :
    ∀ a ∈ s.wire.aliases, NameValid a.1 ∧ a.1 ∉ s.names ∧ a.2 ∈ s.names :=
  (decodedSource h).2.checks.2.2.2.2.2.2.2.1

theorem rowsRetainIncluded (s : Schema) :
    s.rows.map Row.name = s.included.map (fun p => p.wire.name) ∧
    s.rows.map Row.count = s.included.map Tensor.count ∧ s.rows.length = s.included.length :=
  ⟨placedNames _ 0 0,placedCounts _ 0 0,placedLength _ 0 0⟩

def scaleRow (s : NativeScaleBinding.Segment) : Row := ⟨s.wire.name,s.start,s.count,s.ordinal⟩

structure Bound where
  schema : Schema
  scale : NativeScaleBinding.Table
  deriving DecidableEq, Repr

def Links (hash : Bytes → Bytes) (raw : Bytes) (s : Schema) (t : NativeScaleBinding.Table) : Prop :=
  hash raw = t.wire.schema ∧ s.rows = t.segments.map scaleRow ∧ s.total = t.total
instance (hash raw s t) : Decidable (Links hash raw s t) := by unfold Links; infer_instance

def bind (hash : Bytes → Bytes) (schemaRaw scaleRaw : Bytes) : Option Bound := do
  let s ← decode schemaRaw
  let t ← NativeScaleBinding.decode scaleRaw
  if Links hash schemaRaw s t then some ⟨s,t⟩ else none

structure BoundSource (hash : Bytes → Bytes) (schemaRaw scaleRaw : Bytes) (b : Bound) : Prop where
  schema : decode schemaRaw = some b.schema
  scale : NativeScaleBinding.decode scaleRaw = some b.scale
  links : Links hash schemaRaw b.schema b.scale

theorem boundSource {hash schemaRaw scaleRaw b} (h : bind hash schemaRaw scaleRaw = some b) :
    BoundSource hash schemaRaw scaleRaw b := by
  unfold bind at h
  simp only [Bind.bind,Option.bind_eq_some_iff] at h
  obtain ⟨s,hs,t,ht,last⟩ := h
  split at last <;> try contradiction
  rename_i checked
  cases Option.some.inj last
  exact ⟨hs,ht,checked⟩

theorem bindFromSource {hash schemaRaw scaleRaw b} (h : BoundSource hash schemaRaw scaleRaw b) :
    bind hash schemaRaw scaleRaw = some b := by
  simp only [bind,h.schema,h.scale,Bind.bind,Option.bind]
  have eq : Bound.mk b.schema b.scale = b := by cases b; rfl
  rw [if_pos h.links,eq]

theorem boundExactRows {hash schemaRaw scaleRaw b} (h : bind hash schemaRaw scaleRaw = some b) :
    b.scale.segments.map scaleRow = b.schema.rows := (boundSource h).links.2.1.symm

theorem boundRowAt {hash schemaRaw scaleRaw b} {i : Nat} {p : Tensor}
    (h : bind hash schemaRaw scaleRaw = some b) (hp : b.schema.included[i]? = some p) :
    (b.scale.segments.map scaleRow)[i]? = some
      ⟨p.wire.name,((b.schema.included.take i).map Tensor.count).sum,p.dims.prod,i⟩ := by
  rw [boundExactRows h]
  simpa [Schema.rows,Tensor.count] using placedAt hp 0 0

theorem boundHashPreimage {hash schemaRaw scaleRaw b} (h : bind hash schemaRaw scaleRaw = some b) :
    hash (NativeSchemaBytes.encode b.schema.wire) = b.scale.wire.schema := by
  rw [exactPreimage (boundSource h).schema]
  exact (boundSource h).links.1

structure QBound where
  schema : Schema
  q : NativeScaleBinding.Bound
  deriving DecidableEq, Repr

def bindQ (hash : Bytes → Bytes) (schemaRaw scaleRaw qRaw : Bytes) : Option QBound := do
  let s ← decode schemaRaw
  let q ← NativeScaleBinding.bind hash scaleRaw qRaw
  if Links hash schemaRaw s q.table then some ⟨s,q⟩ else none

structure QSource (hash : Bytes → Bytes) (schemaRaw scaleRaw qRaw : Bytes) (b : QBound) : Prop where
  schema : decode schemaRaw = some b.schema
  q : NativeScaleBinding.bind hash scaleRaw qRaw = some b.q
  links : Links hash schemaRaw b.schema b.q.table

theorem qSource {hash schemaRaw scaleRaw qRaw b}
    (h : bindQ hash schemaRaw scaleRaw qRaw = some b) : QSource hash schemaRaw scaleRaw qRaw b := by
  unfold bindQ at h
  simp only [Bind.bind,Option.bind_eq_some_iff] at h
  obtain ⟨s,hs,q,hq,last⟩ := h
  split at last <;> try contradiction
  rename_i checked
  cases Option.some.inj last
  exact ⟨hs,hq,checked⟩

theorem qFromSource {hash schemaRaw scaleRaw qRaw b}
    (h : QSource hash schemaRaw scaleRaw qRaw b) : bindQ hash schemaRaw scaleRaw qRaw = some b := by
  simp only [bindQ,h.schema,h.q,Bind.bind,Option.bind]
  have eq : QBound.mk b.schema b.q = b := by cases b; rfl
  rw [if_pos h.links,eq]

theorem qExactRows {hash schemaRaw scaleRaw qRaw b}
    (h : bindQ hash schemaRaw scaleRaw qRaw = some b) :
    b.q.table.segments.map scaleRow = b.schema.rows := (qSource h).links.2.1.symm

theorem qExactShape {hash schemaRaw scaleRaw qRaw b} {i : Nat} {p : Tensor}
    (h : bindQ hash schemaRaw scaleRaw qRaw = some b) (hp : b.schema.included[i]? = some p) :
    (b.q.table.segments.map scaleRow)[i]? = some
      ⟨p.wire.name,((b.schema.included.take i).map Tensor.count).sum,p.dims.prod,i⟩ := by
  rw [qExactRows h]
  simpa [Schema.rows,Tensor.count] using placedAt hp 0 0

theorem qSelectedSchemaRow {hash schemaRaw scaleRaw qRaw b}
    (h : bindQ hash schemaRaw scaleRaw qRaw = some b) : scaleRow b.q.segment ∈ b.schema.rows := by
  rw [← qExactRows h]
  exact List.mem_map.mpr ⟨b.q.segment,(NativeScaleBinding.boundSegment (qSource h).q).1,rfl⟩

theorem qCoordinateRange {hash schemaRaw scaleRaw qRaw b}
    (h : bindQ hash schemaRaw scaleRaw qRaw = some b) (i : Nat)
    (inside : i < b.q.block.frame.values.length) :
    b.q.block.header.offset + i < b.q.segment.count ∧
    b.q.block.header.start + i = b.q.segment.start + (b.q.block.header.offset + i) :=
  NativeScaleBinding.boundCoordinates (qSource h).q i inside

theorem qOriginalDimensions {hash schemaRaw scaleRaw qRaw b} {p : Tensor}
    (h : bindQ hash schemaRaw scaleRaw qRaw = some b) (member : p ∈ b.schema.included) :
    p.wire ∈ b.schema.wire.parameters ∧ dimensions p.wire.shape = some p.dims ∧
    TensorChecks p := by
  have source := originalParameters (qSource h).schema
  have original := includedOriginal member
  have checks := source.2 p original
  exact ⟨by rw [← source.1]; exact List.mem_map.mpr ⟨p,original,rfl⟩,checks.1,checks⟩

end DeltaReduce.NativeSchemaBinding
