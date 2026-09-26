import DeltaReduce.NativeWalScan

/-! Concrete native COMMAND/ROUND_STATE byte readers. The native summary state
is not the complete public state. Parsing a stored next state does not prove
the command transition, policy admission, snapshot provenance or recovery. -/
namespace DeltaReduce.NativeStateBytes
open NativeReceiptBytes NativeVoteBytes

inductive Scalar where
  | text (bytes : Bytes)
  | uint (value : Nat)
  deriving DecidableEq, Repr

inductive Kind where
  | text | uint
  deriving DecidableEq, Repr

def kind : Scalar → Kind
  | .text _ => .text | .uint _ => .uint

def scalarBytes : Scalar → Bytes
  | .text b => textBytes b
  | .uint n => [16] ++ be 8 n

def ScalarValid : Scalar → Prop
  | .text b => TextValid b
  | .uint n => n < 256^8
instance (v : Scalar) : Decidable (ScalarValid v) := by cases v <;> unfold ScalarValid <;> infer_instance

def readScalar : Kind → Bytes → Option (Scalar × Bytes)
  | .text, raw => do
    let (b,rest) ← readText raw
    some (.text b,rest)
  | .uint, raw => do
    let rest ← consume [16] raw
    let (n,rest) ← readNat 8 rest
    some (.uint n,rest)

theorem scalarEncoded (v : Scalar) (tail : Bytes) (valid : ScalarValid v) :
    readScalar (kind v) (scalarBytes v ++ tail) = some (v,tail) := by
  cases v with
  | text b => simp [kind, scalarBytes, readScalar, readTextEncoded b tail valid]
  | uint n =>
    simp only [kind, scalarBytes, List.append_assoc, readScalar, consumeAppend, bind, Option.bind]
    rw [readNatEncoded 8 n tail valid]

def encodeFields : List (Bytes × Scalar) → Bytes
  | [] => []
  | (key,value)::rest => textBytes key ++ scalarBytes value ++ encodeFields rest

def schema (fields : List (Bytes × Scalar)) : List (Bytes × Kind) :=
  fields.map (fun p => (p.1,kind p.2))

def readFields : List (Bytes × Kind) → Bytes → Option (List Scalar × Bytes)
  | [], raw => some ([],raw)
  | (key,k)::rest, raw => do
    let raw ← consume (textBytes key) raw
    let (v,raw) ← readScalar k raw
    let (vs,raw) ← readFields rest raw
    some (v::vs,raw)

theorem fieldsEncoded (fields : List (Bytes × Scalar)) (tail : Bytes)
    (valid : ∀ p ∈ fields, ScalarValid p.2) :
    readFields (schema fields) (encodeFields fields ++ tail) =
      some (fields.map Prod.snd,tail) := by
  induction fields with
  | nil => rfl
  | cons p rest ih =>
    simp only [schema, List.map_cons, encodeFields, List.append_assoc, readFields,
      consumeAppend, bind, Option.bind]
    rw [scalarEncoded p.2 _ (valid p (by simp))]
    dsimp only
    simp only [schema] at ih
    rw [ih (by intro q member; exact valid q (by simp [member]))]

def header (code : Nat) : Bytes := [68,82,67,49,1,0] ++ be 2 code
def mapHeader (count : Nat) : Bytes := [49] ++ be 4 count
def payload (fields : List (Bytes × Scalar)) : Bytes := mapHeader fields.length ++ encodeFields fields
def encodeEnvelope (code : Nat) (fields : List (Bytes × Scalar)) : Bytes :=
  header code ++ sizedBytes (payload fields)

def EnvelopeValid (code : Nat) (fields : List (Bytes × Scalar)) : Prop :=
  (∀ p ∈ fields, ScalarValid p.2) ∧ (encodeEnvelope code fields).length ≤ maxEnvelope
instance (code : Nat) (fields : List (Bytes × Scalar)) : Decidable (EnvelopeValid code fields) := by
  unfold EnvelopeValid; infer_instance

def readEnvelope (code : Nat) (shape : List (Bytes × Kind)) (raw : Bytes) : Option (List Scalar) := do
  if raw.length ≤ maxEnvelope then
    let rest ← consume (header code) raw
    let (body,rest) ← readSection maxEnvelope rest
    if rest = [] then
      let body ← consume (mapHeader shape.length) body
      let (values,rest) ← readFields shape body
      if rest = [] then some values else none
    else none
  else none

theorem envelopeLength (code : Nat) (fields : List (Bytes × Scalar)) :
    (encodeEnvelope code fields).length = 12 + (payload fields).length := by
  simp [encodeEnvelope, header, sizedBytes, beLength]; omega

theorem envelopeEncoded (code : Nat) (fields : List (Bytes × Scalar))
    (valid : EnvelopeValid code fields) :
    readEnvelope code (schema fields) (encodeEnvelope code fields) = some (fields.map Prod.snd) := by
  have small : (payload fields).length ≤ maxEnvelope := by
    have h := valid.2; rw [envelopeLength] at h; omega
  have bounded : (payload fields).length < 256^4 := by unfold maxEnvelope at small; omega
  unfold readEnvelope
  rw [if_pos valid.2]
  simp only [encodeEnvelope, consumeAppend, bind, Option.bind]
  rw [← List.append_nil (sizedBytes (payload fields)), readSectionEncoded _ _ _ bounded small]
  have length : (schema fields).length = fields.length := by simp [schema]
  simp only [↓reduceIte, payload, length, consumeAppend]
  rw [← List.append_nil (encodeFields fields), fieldsEncoded _ _ valid.1]
  rfl

structure WireCommand where
  actor : Bytes
  body : Bytes
  commandKind : Bytes
  height : Bytes
  tick : Bytes
  request : Bytes
  round : Bytes
  view : Bytes
  deriving DecidableEq, Repr

def commandFields (w : WireCommand) : List (Bytes × Scalar) :=
  [(ascii "actor_id",.text w.actor),(ascii "body_hash",.text w.body),
   (ascii "command_kind",.text w.commandKind),(ascii "formal_semantics_id",.text nativeSemantics),
   (ascii "height",.text w.height),(ascii "logical_tick",.text w.tick),
   (ascii "request_id",.text w.request),(ascii "round_id",.text w.round),
   (ascii "schema_version",.text (ascii "1.0.0")),(ascii "type_name",.text (ascii "COMMAND")),
   (ascii "view",.text w.view)]

def commandSchema := schema (commandFields ⟨[],[],[],[],[],[],[],[]⟩)
def encodeCommand (w : WireCommand) := encodeEnvelope 6 (commandFields w)

def commandValues : List Scalar → Option WireCommand
  | [.text actor,.text body,.text name,.text semantics,.text height,.text tick,
     .text request,.text round,.text version,.text typ,.text view] =>
    if semantics = nativeSemantics ∧ version = ascii "1.0.0" ∧ typ = ascii "COMMAND" then
      some ⟨actor,body,name,height,tick,request,round,view⟩ else none
  | _ => none

theorem commandFieldsRetained (w : WireCommand) :
    commandValues ((commandFields w).map Prod.snd) = some w := by simp [commandValues, commandFields]

def readCommand (raw : Bytes) : Option WireCommand := do
  let values ← readEnvelope 6 commandSchema raw
  commandValues values

theorem readCommandEncoded (w : WireCommand) (valid : EnvelopeValid 6 (commandFields w)) :
    readCommand (encodeCommand w) = some w := by
  have shape : commandSchema = schema (commandFields w) := rfl
  simp only [readCommand, encodeCommand, shape, envelopeEncoded 6 _ valid, bind, Option.bind]
  exact commandFieldsRetained w

structure Command where
  wire : WireCommand
  height : Nat
  tick : Nat
  view : Nat
  deriving DecidableEq, Repr

def CommandValid (c : Command) : Prop :=
  EnvelopeValid 6 (commandFields c.wire) ∧ ContentId c.wire.body ∧
  c.wire.actor ≠ [] ∧ c.wire.commandKind ≠ [] ∧ c.wire.request ≠ [] ∧ c.wire.round ≠ [] ∧
  parseDecimal c.wire.height = some c.height ∧ parseDecimal c.wire.tick = some c.tick ∧
  parseDecimal c.wire.view = some c.view
instance (c : Command) : Decidable (CommandValid c) := by unfold CommandValid; infer_instance

def interpretCommand (w : WireCommand) : Option Command := do
  let height ← parseDecimal w.height
  let tick ← parseDecimal w.tick
  let view ← parseDecimal w.view
  let c := Command.mk w height tick view
  if CommandValid c then some c else none

theorem commandInterpreted (c : Command) (valid : CommandValid c) :
    interpretCommand c.wire = some c := by
  have retained := valid
  obtain ⟨_,_,_,_,_,_,a,b,d⟩ := valid
  simp only [interpretCommand, a,b,d, bind, Option.bind]
  cases c
  exact if_pos retained

theorem commandInterpretSound {w c} (ok : interpretCommand w = some c) :
    c.wire = w ∧ CommandValid c := by
  unfold interpretCommand at ok
  cases a : parseDecimal w.height with
  | none => simp [a] at ok
  | some height =>
    simp only [a,bind,Option.bind] at ok
    cases b : parseDecimal w.tick with
    | none => simp [b] at ok
    | some tick =>
      simp only [b] at ok
      cases d : parseDecimal w.view with
      | none => simp [d] at ok
      | some view =>
        simp only [d] at ok
        split at ok
        · cases Option.some.inj ok; exact ⟨rfl,‹CommandValid _›⟩
        · contradiction

def decodeCommand (raw : Bytes) : Option Command := do
  let w ← readCommand raw
  let c ← interpretCommand w
  if encodeCommand w = raw then some c else none

theorem commandEncoded (c : Command) (valid : CommandValid c) :
    decodeCommand (encodeCommand c.wire) = some c := by
  simp [decodeCommand, readCommandEncoded _ valid.1, commandInterpreted _ valid]

theorem commandFromBytes (c : Command) (raw : Bytes) (valid : CommandValid c)
    (bytes : encodeCommand c.wire = raw) : decodeCommand raw = some c := by
  rw [← bytes]; exact commandEncoded c valid

theorem commandSound {raw c} (ok : decodeCommand raw = some c) :
    CommandValid c ∧ encodeCommand c.wire = raw := by
  unfold decodeCommand at ok
  cases a : readCommand raw with
  | none => simp [a] at ok
  | some w =>
    simp only [a,bind,Option.bind] at ok
    cases b : interpretCommand w with
    | none => simp [b] at ok
    | some value =>
      simp only [b] at ok
      split at ok
      · cases Option.some.inj ok
        have h := commandInterpretSound b
        exact ⟨h.2,h.1 ▸ ‹encodeCommand w = raw›⟩
      · contradiction

theorem commandEncodingInjective (a b : Command) (ha : CommandValid a) (hb : CommandValid b)
    (same : encodeCommand a.wire = encodeCommand b.wire) : a = b := by
  have h := congrArg decodeCommand same
  rw [commandEncoded a ha, commandEncoded b hb] at h
  exact Option.some.inj h

theorem commandNumbers {raw c} (ok : decodeCommand raw = some c) :
    c.height < 256^8 ∧ c.tick < 256^8 ∧ c.view < 256^8 := by
  obtain ⟨_,_,_,_,_,_,a,b,d⟩ := (commandSound ok).1
  have h := decimalSound a; have t := decimalSound b; have v := decimalSound d
  exact ⟨h.2 ▸ h.1.2.2.2,t.2 ▸ t.1.2.2.2,v.2 ▸ v.1.2.2.2⟩

structure WireState where
  available : Nat
  committed : Nat
  config : Bytes
  sequence : Bytes
  height : Bytes
  parent : Bytes
  phase : Bytes
  round : Bytes
  root : Bytes
  total : Nat
  view : Bytes
  deriving DecidableEq, Repr

def stateFields (w : WireState) : List (Bytes × Scalar) :=
  [(ascii "available_ticket_count",.uint w.available),(ascii "committed_ticket_count",.uint w.committed),
   (ascii "config_id",.text w.config),(ascii "durable_sequence",.text w.sequence),
   (ascii "formal_semantics_id",.text nativeSemantics),(ascii "height",.text w.height),
   (ascii "parent_checkpoint_id",.text w.parent),(ascii "phase",.text w.phase),
   (ascii "round_id",.text w.round),(ascii "schema_version",.text (ascii "1.0.0")),
   (ascii "state_root",.text w.root),(ascii "ticket_count",.uint w.total),
   (ascii "type_name",.text (ascii "ROUND_STATE")),(ascii "view",.text w.view)]

def stateSchema := schema (stateFields ⟨0,0,[],[],[],[],[],[],[],0,[]⟩)
def encodeState (w : WireState) := encodeEnvelope 5 (stateFields w)

def stateValues : List Scalar → Option WireState
  | [.uint available,.uint committed,.text config,.text sequence,.text semantics,.text height,
     .text parent,.text phase,.text round,.text version,.text root,.uint total,.text typ,.text view] =>
    if semantics = nativeSemantics ∧ version = ascii "1.0.0" ∧ typ = ascii "ROUND_STATE" then
      some ⟨available,committed,config,sequence,height,parent,phase,round,root,total,view⟩ else none
  | _ => none

theorem stateFieldsRetained (w : WireState) :
    stateValues ((stateFields w).map Prod.snd) = some w := by simp [stateValues, stateFields]

def readState (raw : Bytes) : Option WireState := do
  let values ← readEnvelope 5 stateSchema raw
  stateValues values

theorem readStateEncoded (w : WireState) (valid : EnvelopeValid 5 (stateFields w)) :
    readState (encodeState w) = some w := by
  have shape : stateSchema = schema (stateFields w) := rfl
  simp only [readState, encodeState, shape, envelopeEncoded 5 _ valid,bind,Option.bind]
  exact stateFieldsRetained w

def phases : List Bytes := [ascii "TICKETING_OPEN",ascii "COMMITTED",ascii "AVAILABLE",
  ascii "ELIGIBLE",ascii "AGGREGATED",ascii "ABORTED"]

structure State where
  wire : WireState
  sequence : Nat
  height : Nat
  view : Nat
  deriving DecidableEq, Repr

def StateValid (s : State) : Prop :=
  EnvelopeValid 5 (stateFields s.wire) ∧ ContentId s.wire.config ∧ ContentId s.wire.parent ∧
  ContentId s.wire.root ∧ s.wire.round ≠ [] ∧ s.wire.phase ∈ phases ∧
  s.wire.available ≤ s.wire.committed ∧ s.wire.committed ≤ s.wire.total ∧ s.wire.total < 256^4 ∧
  parseDecimal s.wire.sequence = some s.sequence ∧ parseDecimal s.wire.height = some s.height ∧
  parseDecimal s.wire.view = some s.view
instance (s : State) : Decidable (StateValid s) := by unfold StateValid; infer_instance

def interpretState (w : WireState) : Option State := do
  let sequence ← parseDecimal w.sequence
  let height ← parseDecimal w.height
  let view ← parseDecimal w.view
  let s := State.mk w sequence height view
  if StateValid s then some s else none

theorem stateInterpreted (s : State) (valid : StateValid s) : interpretState s.wire = some s := by
  have retained := valid
  obtain ⟨_,_,_,_,_,_,_,_,_,a,b,c⟩ := valid
  simp only [interpretState,a,b,c,bind,Option.bind]
  cases s
  exact if_pos retained

theorem stateInterpretSound {w s} (ok : interpretState w = some s) : s.wire = w ∧ StateValid s := by
  unfold interpretState at ok
  cases a : parseDecimal w.sequence with
  | none => simp [a] at ok
  | some sequence =>
    simp only [a,bind,Option.bind] at ok
    cases b : parseDecimal w.height with
    | none => simp [b] at ok
    | some height =>
      simp only [b] at ok
      cases c : parseDecimal w.view with
      | none => simp [c] at ok
      | some view =>
        simp only [c] at ok
        split at ok
        · cases Option.some.inj ok; exact ⟨rfl,‹StateValid _›⟩
        · contradiction

def decodeState (raw : Bytes) : Option State := do
  let w ← readState raw
  let s ← interpretState w
  if encodeState w = raw then some s else none

theorem stateEncoded (s : State) (valid : StateValid s) : decodeState (encodeState s.wire) = some s := by
  simp [decodeState,readStateEncoded _ valid.1,stateInterpreted _ valid]

theorem stateFromBytes (s : State) (raw : Bytes) (valid : StateValid s)
    (bytes : encodeState s.wire = raw) : decodeState raw = some s := by
  rw [← bytes]; exact stateEncoded s valid

theorem stateSound {raw s} (ok : decodeState raw = some s) : StateValid s ∧ encodeState s.wire = raw := by
  unfold decodeState at ok
  cases a : readState raw with
  | none => simp [a] at ok
  | some w =>
    simp only [a,bind,Option.bind] at ok
    cases b : interpretState w with
    | none => simp [b] at ok
    | some value =>
      simp only [b] at ok
      split at ok
      · cases Option.some.inj ok
        have h := stateInterpretSound b
        exact ⟨h.2,h.1 ▸ ‹encodeState w = raw›⟩
      · contradiction

theorem stateEncodingInjective (a b : State) (ha : StateValid a) (hb : StateValid b)
    (same : encodeState a.wire = encodeState b.wire) : a = b := by
  have h := congrArg decodeState same
  rw [stateEncoded a ha,stateEncoded b hb] at h
  exact Option.some.inj h

theorem stateNumbers {raw s} (ok : decodeState raw = some s) :
    s.wire.available ≤ s.wire.committed ∧ s.wire.committed ≤ s.wire.total ∧
    s.wire.total < 256^4 ∧ s.sequence < 256^8 ∧ s.height < 256^8 ∧ s.view < 256^8 := by
  obtain ⟨_,_,_,_,_,_,x,y,z,a,b,c⟩ := (stateSound ok).1
  have q := decimalSound a; have h := decimalSound b; have v := decimalSound c
  exact ⟨x,y,z,q.2 ▸ q.1.2.2.2,h.2 ▸ h.1.2.2.2,v.2 ▸ v.1.2.2.2⟩

def contentPreimage (domain raw : Bytes) : Bytes := domain ++ [0] ++ raw
def contentId (sha : Bytes → Bytes) (domain raw : Bytes) : Option Bytes :=
  let digest := sha (contentPreimage domain raw)
  if digest.length = 32 then some (ascii "sha256:" ++ hexBytes digest) else none
def commandDomain := ascii "deltareduce:003:command:v1"
def stateDomain := ascii "deltareduce:003:round-state:v1"

theorem contentIdPreimage {sha domain raw id} (ok : contentId sha domain raw = some id) :
    (sha (domain ++ [0] ++ raw)).length = 32 ∧
    id = ascii "sha256:" ++ hexBytes (sha (contentPreimage domain raw)) := by
  unfold contentId at ok
  dsimp only at ok
  split at ok
  · exact ⟨‹_›,(Option.some.inj ok).symm⟩
  · contradiction

theorem contentIdSize {sha domain raw id} (ok : contentId sha domain raw = some id) : id.length = 71 := by
  obtain ⟨width,bytes⟩ := contentIdPreimage ok
  rw [bytes,List.length_append,hexadecimalLength]
  change 7 + 2 * (sha (domain ++ [0] ++ raw)).length = 71
  omega

/- Only parses the two typed fields of a transition record. The effects/inner
WAL bytes remain exact in Entry but are not semantically decoded here. -/
def inspectEntry (e : NativeWalBytes.Entry) : Option (Command × State) := do
  if e.kind = 1 then
    let c ← decodeCommand e.command
    let s ← decodeState e.state
    some (c,s)
  else none

theorem entryFromComponents (e : NativeWalBytes.Entry) (c : Command) (s : State)
    (kind : e.kind = 1) (command : decodeCommand e.command = some c)
    (state : decodeState e.state = some s) : inspectEntry e = some (c,s) := by
  simp [inspectEntry,kind,command,state]

theorem entryParsed {e c s} (ok : inspectEntry e = some (c,s)) :
    e.kind = 1 ∧ decodeCommand e.command = some c ∧ decodeState e.state = some s := by
  unfold inspectEntry at ok
  split at ok
  · rename_i kind
    cases a : decodeCommand e.command with
    | none => simp [a] at ok
    | some cmd =>
      simp only [a,bind,Option.bind] at ok
      cases b : decodeState e.state with
      | none => simp [b] at ok
      | some st =>
        simp only [b] at ok
        cases Option.some.inj ok
        exact ⟨kind,rfl,rfl⟩
  · contradiction

theorem entryOriginalBytes {e c s} (ok : inspectEntry e = some (c,s)) :
    CommandValid c ∧ StateValid s ∧ encodeCommand c.wire = e.command ∧ encodeState s.wire = e.state := by
  have h := entryParsed ok
  exact ⟨(commandSound h.2.1).1,(stateSound h.2.2).1,(commandSound h.2.1).2,(stateSound h.2.2).2⟩

theorem scannedCommandOrigin (sha : Bytes → Bytes) (raw : Bytes) (r : NativeWalScan.Result)
    (i : Nat) (p : NativeWalScan.Piece) (c : Command) (s : State)
    (checked : NativeWalScan.check sha raw = some r) (atIndex : r.pieces[i]? = some p)
    (parsed : inspectEntry p.entry = some (c,s)) :
    p.entry.sequence = 1+i ∧ p.entry.kind = 1 ∧
    NativeWalBytes.encode sha p.entry = p.bytes ∧
    encodeCommand c.wire = p.entry.command ∧ encodeState s.wire = p.entry.state := by
  have indexed : (NativeWalScan.entries r)[i]? = some p.entry := by
    simp only [NativeWalScan.entries,List.getElem?_map,atIndex,Option.map_some]
  have member : p ∈ r.pieces := List.mem_of_getElem? atIndex
  have canonical := NativeWalScan.scannedCanonical sha raw r (NativeWalScan.checkedSound sha raw r checked).1 p member
  have bytes := entryOriginalBytes parsed
  exact ⟨NativeWalScan.checkedPosition sha raw r checked i p.entry indexed,
    (entryParsed parsed).1,canonical.2,bytes.2.2.1,bytes.2.2.2⟩

end DeltaReduce.NativeStateBytes
