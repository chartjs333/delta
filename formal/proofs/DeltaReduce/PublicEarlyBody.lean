import DeltaReduce.NativeEarlySource
import DeltaReduce.PublicAuthority

/-! Complete CONFIG/ISC public values from original selected artifacts and
independently keyed primitive names. No future arithmetic Binding is required. -/
namespace DeltaReduce.PublicEarlyBody
open NativeBinding PublicState
open PublicAuthority (record roundValue iscValue setValue ClosePolicy)
open NativeEarlySource (Loaded Isc Config)

inductive NameKey where
  | actor (validator epoch : Bytes)
  | height (height : Nat)
  | epoch (epoch : Bytes)
  | config (config : Bytes)
  | ticket (context : NativeInputSetBody.Context) (ticket : Bytes)
  | content (id : Bytes) (body : NativeInputSetBody.Body) (tuple : NativeInputSetBody.Tuple)
  deriving DecidableEq, Repr

structure Trust where
  atom : NameKey → String → Prop
  policy : Bytes → NativeInputSetBody.Body → ClosePolicy → Prop

structure Metadata (trust : Trust) where
  atom : NameKey → Option String
  policy : Bytes → NativeInputSetBody.Body → Option ClosePolicy
  atomAuthentic : ∀ k n, atom k = some n → trust.atom k n
  policyAuthentic : ∀ id b p, policy id b = some p → trust.policy id b p

structure Name {trust} (source : Metadata trust) (key : NameKey) where
  text : String
  selected : source.atom key = some text

def loadName {trust} (source : Metadata trust) (key : NameKey) : Option (Name source key) :=
  match h : source.atom key with
  | none => none
  | some n => some ⟨n,h⟩

def Name.value {trust source key} (name : Name (trust := trust) source key) : Value := .model name.text

theorem nameAuthentic {trust source key} (name : Name (trust := trust) source key) : trust.atom key name.text :=
  source.atomAuthentic key name.text name.selected

structure Header {trust} (source : Metadata trust) (x : NativeSelectedVote.Checked) where
  actor : Name source (.actor x.vote.wire.validator x.vote.wire.epoch)
  height : Name source (.height x.state.height)
  epoch : Name source (.epoch x.policy.epoch)
  config : Name source (.config x.policy.config)

def loadHeader {trust} (source : Metadata trust) (x : NativeSelectedVote.Checked) : Option (Header source x) := do
  let actor ← loadName source (.actor x.vote.wire.validator x.vote.wire.epoch)
  let height ← loadName source (.height x.state.height)
  let epoch ← loadName source (.epoch x.policy.epoch)
  let config ← loadName source (.config x.policy.config)
  some ⟨actor,height,epoch,config⟩

def Header.round {trust source x} (h : Header (trust := trust) source x) : Value := roundValue h.height.value h.epoch.value

def Header.configVote {trust source x} (h : Header (trust := trust) source x) : Vote :=
  ⟨h.actor.value,.text "ROUND_CONFIG",
    record [("epoch",h.epoch.value),("height",h.height.value),("kind",.text "ROUND_CONFIG")],h.config.value⟩

structure Entry {trust} (source : Metadata trust) (id : Bytes) (body : NativeInputSetBody.Body) where
  original : NativeInputSetBody.Tuple
  ticket : Name source (.ticket body.context original.ticket)
  content : Name source (.content id body original)

def Entry.value {trust source id body} (e : Entry (trust := trust) source id body) : Value :=
  record [("content",e.content.value),("ticket",e.ticket.value)]

def loadEntry {trust} (source : Metadata trust) (id : Bytes) (body : NativeInputSetBody.Body)
    (t : NativeInputSetBody.Tuple) : Option (Entry source id body) := do
  let ticket ← loadName source (.ticket body.context t.ticket)
  let content ← loadName source (.content id body t)
  some ⟨t,ticket,content⟩

def loadEntries {trust} (source : Metadata trust) (id : Bytes) (body : NativeInputSetBody.Body) :
    List NativeInputSetBody.Tuple → Option (List (Entry source id body))
  | [] => some []
  | t::ts => do let e ← loadEntry source id body t; let es ← loadEntries source id body ts; some (e::es)

theorem entryOriginal {trust source id body t e}
    (h : loadEntry (trust := trust) source id body t = some e) : e.original = t := by
  simp only [loadEntry,bind,Option.bind_eq_some_iff] at h
  obtain ⟨_,_,_,_,last⟩ := h
  cases Option.some.inj last
  rfl

theorem entriesOriginal {trust source id body ts es}
    (h : loadEntries (trust := trust) source id body ts = some es) : es.map Entry.original = ts := by
  induction ts generalizing es with
  | nil => cases Option.some.inj h; rfl
  | cons t ts ih =>
    simp only [loadEntries,bind,Option.bind_eq_some_iff] at h
    obtain ⟨e,he,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,entryOriginal he,ih hr]

theorem entriesCount {trust source id body ts es}
    (h : loadEntries (trust := trust) source id body ts = some es) : es.length = ts.length := by
  simpa only [List.length_map] using congrArg List.length (entriesOriginal h)

theorem entriesAt {trust source id body ts es}
    (h : loadEntries (trust := trust) source id body ts = some es) (i : Nat) :
    (es.map Entry.original)[i]? = ts[i]? := by rw [entriesOriginal h]

theorem entryPrimitiveAuthority {trust source id body} (e : Entry (trust := trust) source id body) :
    trust.atom (.ticket body.context e.original.ticket) e.ticket.text ∧
    trust.atom (.content id body e.original) e.content.text := ⟨nameAuthentic e.ticket,nameAuthentic e.content⟩

structure IscImage {sha x} (isc : Isc sha x) {trust} (source : Metadata trust) where
  header : Header source x
  policy : ClosePolicy
  policySelected : source.policy isc.original.body.id isc.original.body.body = some policy
  entries : List (Entry source isc.original.body.id isc.original.body.body)
  computed : loadEntries source isc.original.body.id isc.original.body.body isc.original.body.body.tuples = some entries

def iscVote {sha x isc trust source} (p : IscImage (sha := sha) (x := x) isc (trust := trust) source) : Vote :=
  ⟨p.header.actor.value,.text "ISC",p.header.round,
    iscValue p.header.round p.header.config.value p.policy (setValue (p.entries.map Entry.value))⟩

def loadIscImage {sha x} (isc : Isc sha x) {trust} (source : Metadata trust) : Option (IscImage isc source) := do
  let header ← loadHeader source x
  match selected : source.policy isc.original.body.id isc.original.body.body with
  | none => none
  | some policy =>
    match computed : loadEntries source isc.original.body.id isc.original.body.body isc.original.body.body.tuples with
    | none => none
    | some entries => some ⟨header,policy,selected,entries,computed⟩

inductive Image (sha : Bytes → Bytes) (x : NativeSelectedVote.Checked) {trust} (source : Metadata trust) where
  | config (checked : Config x) (header : Header source x)
  | isc (original : Isc sha x) (image : IscImage original source)

def Image.vote {sha x trust source} : Image sha x (trust := trust) source → Vote
  | .config _ header => header.configVote
  | .isc _ image => iscVote image

def project (sha : Bytes → Bytes) (x : NativeSelectedVote.Checked) {trust} (source : Metadata trust) :
    Option (Image sha x source) := do
  if config : Config x then
    let header ← loadHeader source x
    some (.config config header)
  else
    let isc ← NativeEarlySource.loadIsc sha x
    let image ← loadIscImage isc source
    some (.isc isc image)

def Image.Separated {sha x trust source} : Image sha x (trust := trust) source → Prop
  | .config _ _ => True
  | .isc _ image => (image.entries.map Entry.value).Nodup
instance {sha x trust source} (image : Image sha x (trust := trust) source) : Decidable image.Separated := by
  cases image <;> unfold Image.Separated <;> infer_instance

structure Checked {sha x trust source} (models : List String) (candidate : Vote) where
  image : Image sha x (trust := trust) source
  computed : project sha x source = some image
  entire : candidate = image.vote
  separated : image.Separated
  canonical : PublicState.canonical models (.function (voteEntries candidate)) = true

def check {sha x trust} (source : Metadata trust) (models : List String) (candidate : Vote) :
    Option (Checked (sha := sha) (x := x) (source := source) models candidate) :=
  match computed : project sha x source with
  | none => none
  | some image =>
    if valid : candidate = image.vote ∧ image.Separated ∧ PublicState.canonical models (.function (voteEntries candidate)) = true then
      some ⟨image,computed,valid.1,valid.2.1,valid.2.2⟩ else none

theorem checkedWholeVote {sha x trust source models candidate}
    (h : Checked (sha := sha) (x := x) (trust := trust) (source := source) models candidate) :
    candidate = h.image.vote ∧ PublicState.canonical models (.function (voteEntries candidate)) = true :=
  ⟨h.entire,h.canonical⟩

theorem iscAllFields {sha x isc trust source} (p : IscImage (sha := sha) (x := x) isc (trust := trust) source) :
    readField (iscVote p).body "round" = some p.header.round ∧
    readField (iscVote p).body "config" = some p.header.config.value ∧
    readField (iscVote p).body "policy" = some (.text p.policy.text) ∧
    readField (iscVote p).body "entries" = some (setValue (p.entries.map Entry.value)) ∧
    readField (iscVote p).body "canonicalRoot" = some (setValue (p.entries.map Entry.value)) := ⟨rfl,rfl,rfl,rfl,rfl⟩

theorem iscCompleteOriginalList {sha x isc trust source} (p : IscImage (sha := sha) (x := x) isc (trust := trust) source) :
    p.entries.map Entry.original = isc.original.body.body.tuples := entriesOriginal p.computed

theorem iscFullSetCoverage {sha x isc trust source} (p : IscImage (sha := sha) (x := x) isc (trust := trust) source) :
    ∃ values, setValue (p.entries.map Entry.value) = .set values ∧
      (PublicAuthority.valuesList values).Perm (p.entries.map Entry.value) := PublicAuthority.setRetainsAllValues _

theorem iscPolicyIndependent {sha x isc trust source} (p : IscImage (sha := sha) (x := x) isc (trust := trust) source) :
    trust.policy isc.original.body.id isc.original.body.body p.policy :=
  source.policyAuthentic _ _ _ p.policySelected

theorem contentKeyRetainsAvailability {id body a b}
    (changed : a.availability ≠ b.availability) : NameKey.content id body a ≠ .content id body b := by
  intro h; cases h; exact changed rfl

theorem contentKeyRetainsRoot {id a b t} (changed : a.root ≠ b.root) :
    NameKey.content id a t ≠ .content id b t := by intro h; cases h; exact changed rfl

theorem unsupportedProject {sha x trust source}
    (config : ¬ Config x) (isc : x.admitted.selected.original.action ≠ 2) :
    project sha x (trust := trust) source = none := by
  simp only [project,dif_neg config,NativeEarlySource.unsupportedIscRejects isc,bind,Option.bind]

theorem projectConfigFromComponents {sha x trust source} (config : Config x)
    {header : Header (trust := trust) source x} (h : loadHeader source x = some header) :
    project sha x source = some (.config config header) := by
  simp only [project,dif_pos config,h,bind,Option.bind]

theorem projectIscFromComponents {sha x trust source} (config : ¬ Config x)
    {isc : Isc sha x} (native : NativeEarlySource.loadIsc sha x = some isc)
    {p : IscImage isc (trust := trust) source} (image : loadIscImage isc source = some p) :
    project sha x source = some (.isc isc p) := by
  simp only [project,dif_neg config,native,bind,Option.bind,image]

theorem checkFromComponents {sha x trust source models candidate}
    (image : Image sha x (trust := trust) source) (computed : project sha x source = some image)
    (entire : candidate = image.vote) (separated : image.Separated)
    (canonical : PublicState.canonical models (.function (voteEntries candidate)) = true) :
    check source models candidate = some (Checked.mk image computed entire separated canonical) := by
  unfold check
  split
  · rename_i missing; rw [computed] at missing; contradiction
  · rename_i found hf
    have same := Option.some.inj (computed.symm.trans hf)
    subst found
    simp only [dif_pos (And.intro entire (And.intro separated canonical))]

theorem changedVoteRejects {sha x trust source models candidate image}
    (computed : project sha x (trust := trust) source = some image) (changed : candidate ≠ image.vote) :
    check (sha := sha) (x := x) source models candidate = none := by
  unfold check
  split
  · rfl
  · rename_i found hf
    have same := Option.some.inj (computed.symm.trans hf)
    subst found
    split
    · rename_i valid; exact False.elim (changed valid.1)
    · rfl

theorem collapsedEntriesReject {sha x trust source models candidate image}
    (computed : project sha x (trust := trust) source = some image) (collapsed : ¬ image.Separated) :
    check (sha := sha) (x := x) source models candidate = none := by
  unfold check
  split
  · rfl
  · rename_i found hf
    have same := Option.some.inj (computed.symm.trans hf)
    subst found
    split
    · rename_i valid; exact False.elim (collapsed valid.2.1)
    · rfl

end DeltaReduce.PublicEarlyBody
