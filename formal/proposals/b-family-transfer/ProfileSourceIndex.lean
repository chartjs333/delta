import ProfileControl
import ProfileConfigurationQC

/-! T047/T053. Original source-index materialization before producer checking.
Actor/action/input/dependency positions are decoded from the whole original
control descriptor. Hash equality establishes byte binding, not event legality,
signature truth, physical availability or a complete R2 relation. -/
namespace DeltaReduce.ProfileSource.Index
open NativeReceiptBytes (Bytes)
open NativeVoteBytes (ascii ContentId)
open Control (Node Nodes Fields)

def nodes : Nodes → List Node
  | .nil => []
  | .cons n ns => n :: nodes ns

def object : Node → Option Fields
  | .object fs => some fs
  | _ => none

def text : Option Node → Option Bytes
  | some (.text s) => some s
  | _ => none

def array : Option Node → Option (List Node)
  | some (.array ns) => some (nodes ns)
  | _ => none

def field (fs : Fields) (name : String) : Option Node := Control.lookup fs (ascii name)

def collect {α β} (f : α → Option β) : List α → Option (List β)
  | [] => some []
  | x::xs => do
    let value ← f x
    let rest ← collect f xs
    some (value::rest)

theorem collectPosition {α β} {f : α → Option β} {xs ys x} {n : Nat}
    (ok : collect f xs = some ys) (atSource : xs[n]? = some x) :
    ∃ y, ys[n]? = some y ∧ f x = some y := by
  induction xs generalizing ys n with
  | nil => simp at atSource
  | cons head tail ih =>
    simp only [collect,bind,Option.bind_eq_some_iff] at ok
    obtain ⟨v,hv,vs,hs,last⟩ := ok
    cases Option.some.inj last
    cases n with
    | zero =>
      have same : head = x := by simpa using atSource
      subst x
      exact ⟨v,rfl,hv⟩
    | succ n =>
      obtain ⟨y,hy,fy⟩ := ih hs (by simpa using atSource)
      exact ⟨y,by simpa using hy,fy⟩

theorem collectLength {α β} {f : α → Option β} {xs ys}
    (ok : collect f xs = some ys) : ys.length = xs.length := by
  induction xs generalizing ys with
  | nil => cases Option.some.inj ok; rfl
  | cons head tail ih =>
    simp only [collect,bind,Option.bind_eq_some_iff] at ok
    obtain ⟨v,_,vs,hs,last⟩ := ok
    cases Option.some.inj last
    simpa using congrArg Nat.succ (ih hs)

def decimal (n : Node) : Option Nat := match n with
  | .text raw => NativeVoteBytes.parseDecimal raw
  | _ => none

def digit (b : UInt8) : Bool := decide (48 ≤ b.toNat ∧ b.toNat ≤ 57)
def upper (b : UInt8) : Bool := decide (65 ≤ b.toNat ∧ b.toNat ≤ 90)
def lower (b : UInt8) : Bool := decide (97 ≤ b.toNat ∧ b.toNat ≤ 122)

def schemaName (raw : Bytes) : Bool :=
  raw.take 7 == ascii "SCHEMA-" && (List.range raw.length).any (fun i =>
    decide (7 < i) && (raw.drop i).take 2 == ascii "-V" &&
    ((raw.drop 7).take (i-7)).all (fun b => upper b || digit b || b == 45) &&
    !(raw.drop (i+2)).isEmpty && (raw.drop (i+2)).all digit)

def pathParts : Bytes → List Bytes
  | [] => [[]]
  | x::xs =>
    if x = 47 then []::pathParts xs
    else match pathParts xs with
      | [] => [[x]]
      | p::ps => (x::p)::ps

def locator (raw : Bytes) : Bool :=
  raw.all (fun b => upper b || lower b || digit b || [46,95,45,47].contains b) &&
  (pathParts raw).all (fun p => !p.isEmpty && p != [46] && p != [46,46])

structure Ref where
  original : Node
  length : Nat
  id : Bytes
  deriving DecidableEq, Repr

def reference (original : Node) : Option Ref := do
  let fs ← object original
  let length ← field fs "byte_length" >>= decimal
  let id ← text (field fs "content_id")
  let location ← text (field fs "locator")
  let media ← text (field fs "media_type")
  let schema ← text (field fs "schema_id")
  let version ← text (field fs "schema_version")
  if Control.names fs = (["byte_length","content_id","locator","media_type","schema_id","schema_version"].map ascii) ∧
      Control.canonicalFields fs = true ∧ ContentId id ∧
      locator location = true ∧ schemaName schema = true ∧
      0 < media.length ∧ media.length ≤ 255 ∧ version = ascii "1.0.0" then
    some ⟨original,length,id⟩ else none

theorem referenceOriginal {original r} (ok : reference original = some r) : r.original = original := by
  unfold reference at ok
  simp only [bind,Option.bind_eq_some_iff] at ok
  repeat (obtain ⟨_,_,ok⟩ := ok)
  split at ok <;> try contradiction
  cases Option.some.inj ok
  rfl

def rawId (sha : Bytes → Bytes) (raw : Bytes) : Bytes :=
  ascii "sha256:" ++ NativeVoteBytes.hexBytes (sha raw)

def resolve (sha : Bytes → Bytes) (declared : List Node) (store : List Bytes)
    (original : Node) : Option Bytes := do
  let r ← reference original
  if original ∈ declared then
    let raw ← store.find? (fun raw => rawId sha raw == r.id)
    if raw.length = r.length ∧ (sha raw).length = 32 then some raw else none
  else none

theorem resolved {sha declared store original raw}
    (ok : resolve sha declared store original = some raw) :
    original ∈ declared ∧ raw ∈ store ∧ ∃ r,
      reference original = some r ∧ r.original = original ∧
      raw.length = r.length ∧ rawId sha raw = r.id ∧ (sha raw).length = 32 := by
  unfold resolve at ok
  simp only [bind,Option.bind_eq_some_iff] at ok
  obtain ⟨r,hr,ok⟩ := ok
  split at ok <;> try contradiction
  rename_i declaredSource
  simp only [Option.bind_eq_some_iff] at ok
  obtain ⟨bytes,hb,ok⟩ := ok
  split at ok <;> try contradiction
  rename_i sizes
  cases Option.some.inj ok
  exact ⟨declaredSource,List.mem_of_find?_eq_some hb,r,hr,referenceOriginal hr,
    sizes.1,by simpa using List.find?_some hb,sizes.2⟩

structure Event where
  position : Nat
  descriptor : Node
  actor : Bytes
  action : Bytes
  original : Bytes
  inputs : List Bytes
  dependencies : List Nat
  deriving DecidableEq, Repr

def event (sha : Bytes → Bytes) (declared : List Node) (store : List Bytes)
    (position : Nat) (descriptor : Node) : Option Event := do
  let fs ← object descriptor
  let actor ← text (field fs "actor_id")
  let action ← text (field fs "action_id")
  let sourceRef ← field fs "original_ref"
  let inputRefs ← array (field fs "input_refs")
  let dependencies ← array (field fs "dependencies") >>= collect decimal
  let original ← resolve sha declared store sourceRef
  let inputs ← collect (resolve sha declared store) inputRefs
  if Control.names fs = (["action_id","actor_id","dependencies","input_refs","original_ref"].map ascii) ∧
      Control.canonicalFields fs = true ∧ actor ≠ [] ∧ action ≠ [] ∧
      dependencies.Pairwise (· < ·) ∧ (∀ dep ∈ dependencies, dep < position) then
    some ⟨position,descriptor,actor,action,original,inputs,dependencies⟩ else none

structure EventSource (sha : Bytes → Bytes) (declared : List Node) (store : List Bytes)
    (position : Nat) (descriptor : Node) (out : Event) : Prop where
  index : out.position = position
  originalDescriptor : out.descriptor = descriptor
  fields : ∃ fs sourceRef inputRefs,
    descriptor = .object fs ∧
    Control.names fs = (["action_id","actor_id","dependencies","input_refs","original_ref"].map ascii) ∧
    Control.canonicalFields fs = true ∧
    text (field fs "actor_id") = some out.actor ∧
    text (field fs "action_id") = some out.action ∧
    field fs "original_ref" = some sourceRef ∧
    array (field fs "input_refs") = some inputRefs ∧
    (array (field fs "dependencies") >>= collect decimal) = some out.dependencies ∧
    resolve sha declared store sourceRef = some out.original ∧
    collect (resolve sha declared store) inputRefs = some out.inputs
  nonempty : out.actor ≠ [] ∧ out.action ≠ []
  ordered : out.dependencies.Pairwise (· < ·)
  backward : ∀ dep ∈ out.dependencies, dep < position

theorem eventSource {sha declared store position descriptor out}
    (ok : event sha declared store position descriptor = some out) :
    EventSource sha declared store position descriptor out := by
  unfold event at ok
  simp only [bind,Option.bind_eq_some_iff] at ok
  obtain ⟨fs,hfs,actor,ha,action,hact,sourceRef,hr,inputRefs,hi,deps,hd,
    original,ho,inputs,hins,ok⟩ := ok
  split at ok <;> try contradiction
  rename_i fields
  cases Option.some.inj ok
  have descriptorSource : descriptor = .object fs := by
    cases descriptor <;> simp_all [object]
  exact ⟨rfl,rfl,⟨fs,sourceRef,inputRefs,descriptorSource,fields.1,fields.2.1,
    ha,hact,hr,hi,Option.bind_eq_some_iff.mpr hd,ho,hins⟩,⟨fields.2.2.1,fields.2.2.2.1⟩,
    fields.2.2.2.2.1,fields.2.2.2.2.2⟩

theorem eventComplete {sha declared store position descriptor out}
    (source : EventSource sha declared store position descriptor out) :
    event sha declared store position descriptor = some out := by
  obtain ⟨fs,ref,refs,same,names,canonical,actor,action,originalRef,inputRefs,deps,raw,inputs⟩ := source.fields
  unfold event
  rw [same]
  simp only [object,bind,Option.bind]
  rw [actor,action,originalRef,inputRefs]
  simp only [bind,Option.bind] at deps
  simp only [deps,raw,inputs]
  rw [if_pos ⟨names,canonical,source.nonempty.1,source.nonempty.2,source.ordered,source.backward⟩]
  congr 1
  have ix := source.index
  have ds := source.originalDescriptor
  cases out
  simp_all

def events (sha : Bytes → Bytes) (declared : List Node) (store : List Bytes) :
    Nat → List Node → Option (List Event)
  | _,[] => some []
  | first,descriptor::rest => do
    let e ← event sha declared store first descriptor
    let es ← events sha declared store (first+1) rest
    some (e::es)

theorem eventsOriginal {sha declared store first descriptors out}
    (ok : events sha declared store first descriptors = some out) :
    out.map Event.descriptor = descriptors ∧ out.length = descriptors.length := by
  induction descriptors generalizing first out with
  | nil => cases Option.some.inj ok; exact ⟨rfl,rfl⟩
  | cons head tail ih =>
    simp only [events,bind,Option.bind_eq_some_iff] at ok
    obtain ⟨e,he,es,hs,last⟩ := ok
    cases Option.some.inj last
    obtain ⟨same,len⟩ := ih hs
    exact ⟨by simp [(eventSource he).originalDescriptor,same],by simp [len]⟩

theorem eventsPosition {sha declared store first descriptors out n descriptor}
    (ok : events sha declared store first descriptors = some out)
    (atSource : descriptors[n]? = some descriptor) :
    ∃ e, out[n]? = some e ∧ EventSource sha declared store (first+n) descriptor e := by
  induction descriptors generalizing first out n with
  | nil => simp at atSource
  | cons head tail ih =>
    simp only [events,bind,Option.bind_eq_some_iff] at ok
    obtain ⟨e,he,es,hs,last⟩ := ok
    cases Option.some.inj last
    cases n with
    | zero =>
      have same : head = descriptor := by simpa using atSource
      subst descriptor
      exact ⟨e,rfl,by simpa using eventSource he⟩
    | succ n =>
      obtain ⟨e,pos,src⟩ := ih hs (by simpa using atSource)
      exact ⟨e,by simpa using pos,by simpa [Nat.add_assoc,Nat.add_comm,Nat.add_left_comm] using src⟩

inductive OriginalEvents (sha : Bytes → Bytes) (declared : List Node) (store : List Bytes) :
    Nat → List Node → List Event → Prop
  | nil {first} : OriginalEvents sha declared store first [] []
  | cons {first descriptor rest e es}
      (head : EventSource sha declared store first descriptor e)
      (tail : OriginalEvents sha declared store (first+1) rest es) :
      OriginalEvents sha declared store first (descriptor::rest) (e::es)

theorem eventsSound {sha declared store first descriptors out}
    (ok : events sha declared store first descriptors = some out) :
    OriginalEvents sha declared store first descriptors out := by
  induction descriptors generalizing first out with
  | nil => cases Option.some.inj ok; exact .nil
  | cons descriptor rest ih =>
    simp only [events,bind,Option.bind_eq_some_iff] at ok
    obtain ⟨e,he,es,hs,last⟩ := ok
    cases Option.some.inj last
    exact .cons (eventSource he) (ih hs)

theorem eventsComplete {sha declared store first descriptors out}
    (source : OriginalEvents sha declared store first descriptors out) :
    events sha declared store first descriptors = some out := by
  induction source with
  | nil => rfl
  | cons head tail ih => simp [events,eventComplete head,ih]

/-- Trust-side values are extracted from the independently pinned bootstrap.
They contain no assumed source legality or successful public projection. -/
structure Origin where
  id : Bytes
  epoch : Bytes
  actor : Bytes
  genesis : Node
  deriving DecidableEq, Repr

def OriginMatches (expected : Origin) (fs : Fields) : Prop :=
  text (field fs "origin_id") = some expected.id ∧
  text (field fs "validator_epoch_id") = some expected.epoch ∧
  text (field fs "local_validator_id") = some expected.actor ∧
  field fs "genesis_ref" = some expected.genesis ∧
  ContentId expected.id ∧ ContentId expected.epoch ∧ expected.actor ≠ []
instance (expected fs) : Decidable (OriginMatches expected fs) := by
  unfold OriginMatches; infer_instance

def Inventory (refs : List Ref) : Prop :=
  refs.length ≤ 65536 ∧ refs.Pairwise (fun a b => a.id < b.id) ∧
  (refs.map Ref.length).sum ≤ 64*1024^3
instance (refs) : Decidable (Inventory refs) := by unfold Inventory; infer_instance

structure Bound where
  original : Bytes
  descriptor : Fields
  declared : List Node
  references : List Ref
  artifacts : List Bytes
  genesis : Bytes
  eventDescriptors : List Node
  events : List Event

/-- Decode the original complete event and artifact inventory. Journal-range,
trusted-floor, bootstrap-key and native producer checks are separate conjuncts;
no claim of complete profile validity follows from this materialization. -/
def check (sha : Bytes → Bytes) (expected : Origin) (descriptor : Fields)
    (original : Bytes) (store : List Bytes) : Option Bound := do
  let fs ← Control.check .sourceIndex descriptor original
  if OriginMatches expected fs then
    let declared ← array (field fs "artifacts")
    let refs ← collect reference declared
    let artifacts ← collect (resolve sha declared store) declared
    let genesis ← resolve sha declared store expected.genesis
    let eventDescriptors ← array (field fs "events")
    if Inventory refs ∧ eventDescriptors.length ≤ 1000000 then
      let es ← events sha declared store 0 eventDescriptors
      some ⟨original,fs,declared,refs,artifacts,genesis,eventDescriptors,es⟩
    else none
  else none

theorem checked {sha expected descriptor original store out}
    (ok : check sha expected descriptor original store = some out) :
    out.original = original ∧ out.descriptor = descriptor ∧
    Control.check .sourceIndex descriptor original = some out.descriptor ∧
    OriginMatches expected out.descriptor ∧
    array (field out.descriptor "artifacts") = some out.declared ∧
    collect reference out.declared = some out.references ∧
    collect (resolve sha out.declared store) out.declared = some out.artifacts ∧
    resolve sha out.declared store expected.genesis = some out.genesis ∧
    array (field out.descriptor "events") = some out.eventDescriptors ∧
    Inventory out.references ∧ out.eventDescriptors.length ≤ 1000000 ∧
    events sha out.declared store 0 out.eventDescriptors = some out.events := by
  unfold check at ok
  simp only [bind,Option.bind_eq_some_iff] at ok
  obtain ⟨fs,hfs,ok⟩ := ok
  split at ok <;> try contradiction
  rename_i origin
  simp only [Option.bind_eq_some_iff] at ok
  obtain ⟨declared,hd,refs,hr,artifacts,ha,genesis,hg,descriptors,he,ok⟩ := ok
  split at ok <;> try contradiction
  rename_i limits
  obtain ⟨es,hes,last⟩ := Option.bind_eq_some_iff.mp ok
  cases Option.some.inj last
  exact ⟨rfl,(Control.checked hfs).1,hfs,origin,hd,hr,ha,hg,he,limits.1,limits.2,hes⟩

theorem wholeOriginalEvents {sha expected descriptor original store out}
    (ok : check sha expected descriptor original store = some out) :
    Control.encode (.object out.descriptor) = original ∧
    out.events.map Event.descriptor = out.eventDescriptors ∧
    out.events.length = out.eventDescriptors.length ∧
    OriginalEvents sha out.declared store 0 out.eventDescriptors out.events := by
  have h := checked ok
  have es := h.2.2.2.2.2.2.2.2.2.2.2
  exact ⟨(Control.checked h.2.2.1).2.2.1,(eventsOriginal es).1,
    (eventsOriginal es).2,eventsSound es⟩

theorem checkComplete {sha expected descriptor original store declared refs artifacts genesis ds es}
    (control : Control.check .sourceIndex descriptor original = some descriptor)
    (origin : OriginMatches expected descriptor)
    (declaredSource : array (field descriptor "artifacts") = some declared)
    (refSources : collect reference declared = some refs)
    (allBytes : collect (resolve sha declared store) declared = some artifacts)
    (genesisSource : resolve sha declared store expected.genesis = some genesis)
    (eventDescriptors : array (field descriptor "events") = some ds)
    (limits : Inventory refs ∧ ds.length ≤ 1000000)
    (source : OriginalEvents sha declared store 0 ds es) :
    check sha expected descriptor original store =
      some ⟨original,descriptor,declared,refs,artifacts,genesis,ds,es⟩ := by
  simp only [check,control,bind,Option.bind,if_pos origin,declaredSource,refSources,
    allBytes,genesisSource,eventDescriptors,if_pos limits,eventsComplete source]

theorem originalInputPosition {sha declared store position descriptor out}
    (source : EventSource sha declared store position descriptor out) :
    ∃ fs refs, descriptor = .object fs ∧ array (field fs "input_refs") = some refs ∧
      out.inputs.length = refs.length ∧ ∀ (n : Nat) ref, refs[n]? = some ref →
        ∃ raw, out.inputs[n]? = some raw ∧ ref ∈ declared ∧ raw ∈ store ∧
          resolve sha declared store ref = some raw := by
  obtain ⟨fs,_,refs,same,_,_,_,_,_,inputRefs,_,_,inputBytes⟩ := source.fields
  refine ⟨fs,refs,same,inputRefs,collectLength inputBytes,?_⟩
  intro n ref atRef
  obtain ⟨raw,atRaw,loaded⟩ := collectPosition inputBytes atRef
  exact ⟨raw,atRaw,(resolved loaded).1,(resolved loaded).2.1,loaded⟩

theorem distinctOccurrences {sha declared store first ds es} {n m : Nat} {dn dm}
    (ok : events sha declared store first ds = some es)
    (left : ds[n]? = some dn) (right : ds[m]? = some dm) (different : n ≠ m) :
    ∃ a b, es[n]? = some a ∧ es[m]? = some b ∧ a.position ≠ b.position := by
  obtain ⟨a,ha,sa⟩ := eventsPosition ok left
  obtain ⟨b,hb,sb⟩ := eventsPosition ok right
  refine ⟨a,b,ha,hb,?_⟩
  rw [sa.index,sb.index]
  omega

/-- Lift the exact original delivery occurrence into the CONFIG/QC byte join.
This does not authenticate G or certify transport/durability. Failed or other
events stay in the enclosing complete event list, never disappear here. -/
def received (e : Event) (g : Vote.Artifact) : Option ConfigurationQC.Received := do
  if e.action = ascii "ACT-MESSAGE-DELIVER" then
    match bound : Vote.bindArtifact e.original g with
    | none => none
    | some v => some ⟨e.position,e.actor,e.original,g,v,bound⟩
  else none

theorem receivedOriginal {e g out} (ok : received e g = some out) :
    out.position = e.position ∧ out.receiver = e.actor ∧ out.originalG = e.original ∧
    out.artifact = g ∧ Vote.bindArtifact e.original g = some out.vote ∧
    e.action = ascii "ACT-MESSAGE-DELIVER" := by
  unfold received at ok
  split at ok <;> try contradiction
  rename_i action
  split at ok <;> try contradiction
  rename_i v bound
  cases Option.some.inj ok
  exact ⟨rfl,rfl,rfl,rfl,bound,action⟩

theorem receivedComplete {e g v}
    (action : e.action = ascii "ACT-MESSAGE-DELIVER")
    (bound : Vote.bindArtifact e.original g = some v) :
    received e g = some ⟨e.position,e.actor,e.original,g,v,bound⟩ := by
  simp only [received,if_pos action]
  split
  · rename_i absent; simp [bound] at absent
  · rename_i other found
    have same := Option.some.inj (found.symm.trans bound)
    subst other
    rfl

theorem receivedAtOriginalPosition {sha declared store first ds es n descriptor e g out}
    (whole : events sha declared store first ds = some es)
    (atDescriptor : ds[n]? = some descriptor) (atEvent : es[n]? = some e)
    (delivery : received e g = some out) :
    out.position = first+n ∧ out.receiver = e.actor ∧ out.originalG = e.original ∧
    EventSource sha declared store (first+n) descriptor e := by
  obtain ⟨source,atSource,fields⟩ := eventsPosition whole atDescriptor
  have same := Option.some.inj (atSource.symm.trans atEvent)
  subst source
  have delivered := receivedOriginal delivery
  exact ⟨delivered.1.trans fields.index,delivered.2.1,delivered.2.2.1,fields⟩

end DeltaReduce.ProfileSource.Index
