import DeltaReduce.NativeConfigAdmission

/-! Native proposed ISC body from the full DVPOL tree. No finalized certificate,
cryptographic signatures, ledger freeze, root preimage or availability is inferred. -/
namespace DeltaReduce.NativeInputSetBody
open NativeReceiptBytes NativePolicyCodec NativePolicySchema
open NativeConfigAdmission (ascii Label)
open NativeVoteBytes (ContentId)

structure Context where
  arithmetic : Bytes
  height : Nat
  schema : Bytes
  config : Bytes
  round : Bytes
  epoch : Bytes
  view : Nat
  deriving DecidableEq, Repr
structure Tuple where
  availability : Bytes
  commitment : Bytes
  domain : Bytes
  ticket : Bytes
  deriving DecidableEq, Repr
structure Body where
  context : Context
  root : Bytes
  tuples : List Tuple
  deriving DecidableEq, Repr

def contextValue (c : Context) : Value :=
  .pair (.text c.arithmetic) (.pair (.number c.height) (.pair (.text c.schema)
    (.pair (.text c.config) (.pair (.text c.round) (.pair (.text c.epoch)
      (.pair (.number c.view) .end))))))
def tupleValue (t : Tuple) : Value :=
  .pair (.text t.availability) (.pair (.text t.commitment)
    (.pair (.text t.domain) (.pair (.text t.ticket) .end)))
def bodyValue (b : Body) : Value :=
  .pair (contextValue b.context) (.pair (.text b.root)
    (.pair (.items (b.tuples.map tupleValue)) .end))

def readContext : Value → Option Context
  | .pair (.text a) (.pair (.number h) (.pair (.text s) (.pair (.text c)
      (.pair (.text r) (.pair (.text e) (.pair (.number v) .end)))))) => some ⟨a,h,s,c,r,e,v⟩
  | _ => none
def readTuple : Value → Option Tuple
  | .pair (.text a) (.pair (.text c) (.pair (.text d) (.pair (.text t) .end))) => some ⟨a,c,d,t⟩
  | _ => none
def readTuples : List Value → Option (List Tuple)
  | [] => some []
  | v::vs => do let t ← readTuple v; let ts ← readTuples vs; some (t::ts)
def readBody : Value → Option Body
  | .pair context (.pair (.text root) (.pair (.items tuples) .end)) => do
    let c ← readContext context
    let ts ← readTuples tuples
    some ⟨c,root,ts⟩
  | _ => none

theorem contextRead (c) : readContext (contextValue c) = some c := by cases c; rfl
theorem tupleRead (t) : readTuple (tupleValue t) = some t := by cases t; rfl
theorem tuplesRead (ts) : readTuples (ts.map tupleValue) = some ts := by
  induction ts with
  | nil => rfl
  | cons t ts ih => simp only [List.map_cons,readTuples,tupleRead,ih,bind,Option.bind]
theorem bodyRead (b) : readBody (bodyValue b) = some b := by
  cases b; simp only [bodyValue,readBody,contextRead,tuplesRead,bind,Option.bind]
theorem contextOriginal {v c} (h : readContext v = some c) : v = contextValue c := by
  unfold readContext at h; split at h <;> try contradiction
  cases Option.some.inj h; rfl
theorem tupleOriginal {v t} (h : readTuple v = some t) : v = tupleValue t := by
  unfold readTuple at h; split at h <;> try contradiction
  cases Option.some.inj h; rfl
theorem tuplesOriginal {vs ts} (h : readTuples vs = some ts) : vs = ts.map tupleValue := by
  induction vs generalizing ts with
  | nil => simp [readTuples] at h; subst ts; rfl
  | cons v vs ih =>
    simp only [readTuples,bind,Option.bind_eq_some_iff] at h
    obtain ⟨t,ht,rest,hr,eq⟩ := h
    cases Option.some.inj eq
    simp only [List.map_cons,← tupleOriginal ht,← ih hr]
theorem bodyOriginal {v b} (h : readBody v = some b) : v = bodyValue b := by
  unfold readBody at h
  split at h <;> try contradiction
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨c,hc,ts,ht,eq⟩ := h
  cases Option.some.inj eq
  simp only [bodyValue,← contextOriginal hc,← tuplesOriginal ht]

def text64 (b : Bytes) : Bytes := be 8 b.length ++ b
def contextBytes (c : Context) : Bytes :=
  text64 c.arithmetic ++ be 8 c.height ++ text64 c.schema ++ text64 c.config ++
  text64 c.round ++ text64 c.epoch ++ be 8 c.view
def tupleBytes (t : Tuple) : Bytes :=
  text64 t.availability ++ text64 t.commitment ++ text64 t.domain ++ text64 t.ticket
def bodyBytes (b : Body) : Bytes :=
  contextBytes b.context ++ text64 b.root ++ be 8 b.tuples.length ++
  (b.tuples.map tupleBytes).flatten
def bodyDomain : Bytes := ascii "deltareduce.vote.input-set-body.v1"
def bodyId (sha : Bytes → Bytes) (b : Body) : Option Bytes :=
  NativeStateBytes.contentId sha bodyDomain (bodyBytes b)

def tupleLT (a b : Tuple) : Bool :=
  if a.ticket = b.ticket then NativePolicyBytes.bytesLT a.commitment b.commitment
  else NativePolicyBytes.bytesLT a.ticket b.ticket
def ContextValid (c : Context) : Prop :=
  ContentId c.arithmetic ∧ 0 < c.height ∧ c.height < 256^8 ∧ ContentId c.schema ∧
  ContentId c.config ∧ Label c.round ∧ ContentId c.epoch ∧ c.view < 256^8
instance (c) : Decidable (ContextValid c) := by unfold ContextValid; infer_instance
def TupleValid (t : Tuple) : Prop :=
  ContentId t.availability ∧ ContentId t.commitment ∧ Label t.domain ∧ Label t.ticket
instance (t) : Decidable (TupleValid t) := by unfold TupleValid; infer_instance
def BodyValid (expected : Context) (b : Body) : Prop :=
  ContextValid b.context ∧ b.context = expected ∧ ContentId b.root ∧
  0 < b.tuples.length ∧ b.tuples.length ≤ 100000 ∧
  NativePolicyBytes.strictly tupleLT b.tuples = true ∧ ∀ t ∈ b.tuples, TupleValid t
instance (c b) : Decidable (BodyValid c b) := by unfold BodyValid; infer_instance

structure Checked where
  body : Body
  id : Bytes
  source : Value

def check (sha : Bytes → Bytes) (expected : Context) (source : Value) : Option Checked := do
  let b ← readBody source
  let id ← bodyId sha b
  if BodyValid expected b then some ⟨b,id,source⟩ else none

def CheckedSource (sha : Bytes → Bytes) (expected : Context) (source : Value)
    (out : Checked) : Prop :=
  out.source = source ∧ readBody source = some out.body ∧
  source = bodyValue out.body ∧ bodyId sha out.body = some out.id ∧ BodyValid expected out.body

theorem checkSource {sha expected source out} (h : check sha expected source = some out) :
    CheckedSource sha expected source out := by
  unfold check at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨b,hb,id,hi,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨rfl,hb,bodyOriginal hb,hi,‹BodyValid _ _›⟩

theorem checkFromComponents {sha expected source b id}
    (read : readBody source = some b) (hashed : bodyId sha b = some id)
    (valid : BodyValid expected b) : check sha expected source = some ⟨b,id,source⟩ := by
  simp [check,read,hashed,valid]

def checkAll (sha : Bytes → Bytes) (expected : Context) : List Value → Option (List Checked)
  | [] => some []
  | v::vs => do let c ← check sha expected v; let cs ← checkAll sha expected vs; some (c::cs)

theorem allSources {sha expected vs cs} (h : checkAll sha expected vs = some cs) :
    cs.map Checked.source = vs := by
  induction vs generalizing cs with
  | nil => simp [checkAll] at h; subst cs; rfl
  | cons v vs ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨c,hc,rest,hr,eq⟩ := h
    cases Option.some.inj eq
    simp only [List.map_cons,(checkSource hc).1,ih hr]

theorem allChecked {sha expected vs cs} (h : checkAll sha expected vs = some cs)
    (c : Checked) (mem : c ∈ cs) : CheckedSource sha expected c.source c := by
  induction vs generalizing cs with
  | nil => simp [checkAll] at h; subst cs; simp at mem
  | cons v vs ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨x,hx,rest,hr,eq⟩ := h
    cases Option.some.inj eq
    rcases List.mem_cons.mp mem with eq | mem
    · subst c; have source := checkSource hx; simpa only [source.1] using source
    · exact ih hr mem

theorem allCount {sha expected vs cs} (h : checkAll sha expected vs = some cs) :
    cs.length = vs.length := by have p := congrArg List.length (allSources h); simpa using p

theorem noTupleErasure {sha expected source out} (h : check sha expected source = some out) :
    readTuples (out.body.tuples.map tupleValue) = some out.body.tuples ∧
    (∀ t ∈ out.body.tuples, TupleValid t) :=
  ⟨tuplesRead _,(checkSource h).2.2.2.2.2.2.2.2.2.2⟩

end DeltaReduce.NativeInputSetBody
