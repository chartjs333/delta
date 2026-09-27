import DeltaReduce.NativeQJson

/-! Exact native-004 header byte interpretation, before SHA/source admission.
The historical semantics/profile IDs describe these original source bytes;
they do not grant current formal authority. -/
namespace DeltaReduce.NativeQHeader
open NativeReceiptBytes (Bytes)
open NativeVoteBytes (ascii ContentId DecimalValid parseDecimal)
open NativeQJson (Field Kind ValueValid)

structure Wire where
  countRaw : Bytes
  startRaw : Bytes
  semantics : Bytes
  ordinalRaw : Bytes
  schema : Bytes
  payloadHash : Bytes
  profile : Bytes
  proof : Bytes
  config : Bytes
  scale : Bytes
  segment : Bytes
  offsetRaw : Bytes
  plan : Bytes
  ticket : Bytes
  deriving DecidableEq, Repr

def fields (w : Wire) : List Field :=
  [⟨ascii "element_count", .natural, w.countRaw⟩,
   ⟨ascii "element_start", .natural, w.startRaw⟩,
   ⟨ascii "formal_semantics_id", .text, w.semantics⟩,
   ⟨ascii "ordinal", .natural, w.ordinalRaw⟩,
   ⟨ascii "parameter_schema_id", .text, w.schema⟩,
   ⟨ascii "payload_sha256", .text, w.payloadHash⟩,
   ⟨ascii "profile_id", .text, w.profile⟩,
   ⟨ascii "proof_instance_id", .text, w.proof⟩,
   ⟨ascii "round_config_id", .text, w.config⟩,
   ⟨ascii "scale_table_id", .text, w.scale⟩,
   ⟨ascii "schema_version", .text, ascii "1.0.0"⟩,
   ⟨ascii "segment_id", .text, w.segment⟩,
   ⟨ascii "segment_offset", .natural, w.offsetRaw⟩,
   ⟨ascii "shard_plan_id", .text, w.plan⟩,
   ⟨ascii "ticket_id", .text, w.ticket⟩,
   ⟨ascii "type_name", .text, ascii "ENCODED_INT16_SHARD"⟩]

def keys : List (Bytes × Kind) := NativeQJson.specifications (fields ⟨[],[],[],[],[],[],[],[],[],[],[],[],[],[]⟩)

theorem exactKeys (w : Wire) : NativeQJson.specifications (fields w) = keys := rfl

def fromValues : List Bytes → Option Wire
  | [countRaw,startRaw,semantics,ordinalRaw,schema,payloadHash,profile,proof,config,scale,version,segment,offsetRaw,plan,ticket,name] =>
    if version = ascii "1.0.0" ∧ name = ascii "ENCODED_INT16_SHARD" then
      some ⟨countRaw,startRaw,semantics,ordinalRaw,schema,payloadHash,profile,proof,config,scale,segment,offsetRaw,plan,ticket⟩ else none
  | _ => none

theorem allFieldsRetained (w : Wire) : fromValues ((fields w).map Field.value) = some w := by
  simp [fields, fromValues]

def nativeProfile : Bytes := ascii
  "sha256:17c8d23790047966e42f3204502623c74a0ff0383319d23e67ab15cf92fe3e61"

def tokenByte (b : UInt8) : Prop :=
  (48 ≤ b.toNat ∧ b.toNat ≤ 57) ∨ (65 ≤ b.toNat ∧ b.toNat ≤ 90) ∨
  (97 ≤ b.toNat ∧ b.toNat ≤ 122) ∨ b = 46 ∨ b = 95 ∨ b = 47 ∨ b = 45
instance (b) : Decidable (tokenByte b) := by unfold tokenByte; infer_instance

def Token (raw : Bytes) : Prop := 0 < raw.length ∧ raw.length ≤ 255 ∧ ∀ b ∈ raw, tokenByte b
instance (raw) : Decidable (Token raw) := by unfold Token; infer_instance

def encode (w : Wire) : Bytes := NativeQJson.encodeObject (fields w)

def WireValid (w : Wire) : Prop :=
  (∀ f ∈ fields w, ValueValid f.kind f.value) ∧ (encode w).length ≤ 65536 ∧
  (∀ b ∈ [w.semantics,w.schema,w.payloadHash,w.profile,w.proof,w.config,w.scale,w.plan], ContentId b) ∧
  w.semantics = NativeVoteBytes.nativeSemantics ∧ w.profile = nativeProfile ∧
  Token w.segment ∧ Token w.ticket
instance (w) : Decidable (WireValid w) := by unfold WireValid; infer_instance

structure Header where
  wire : Wire
  count : Nat
  start : Nat
  ordinal : Nat
  offset : Nat
  deriving DecidableEq, Repr

def Valid (h : Header) : Prop :=
  WireValid h.wire ∧ parseDecimal h.wire.countRaw = some h.count ∧
  parseDecimal h.wire.startRaw = some h.start ∧ parseDecimal h.wire.ordinalRaw = some h.ordinal ∧
  parseDecimal h.wire.offsetRaw = some h.offset ∧
  0 < h.count ∧ h.count ≤ 524288 ∧ h.start + h.count ≤ 1073741824 ∧ h.ordinal < 4096
instance (h) : Decidable (Valid h) := by unfold Valid; infer_instance

def interpret (wire : Wire) : Option Header := do
  let count ← parseDecimal wire.countRaw
  let start ← parseDecimal wire.startRaw
  let ordinal ← parseDecimal wire.ordinalRaw
  let offset ← parseDecimal wire.offsetRaw
  let h := Header.mk wire count start ordinal offset
  if Valid h then some h else none

theorem interpreted {wire h} (ok : interpret wire = some h) :
    h.wire = wire ∧ Valid h := by
  unfold interpret at ok
  cases a : parseDecimal wire.countRaw with
  | none => simp [a] at ok
  | some count =>
    simp only [a, bind, Option.bind] at ok
    cases b : parseDecimal wire.startRaw with
    | none => simp [b] at ok
    | some start =>
      simp only [b] at ok
      cases c : parseDecimal wire.ordinalRaw with
      | none => simp [c] at ok
      | some ordinal =>
        simp only [c] at ok
        cases d : parseDecimal wire.offsetRaw with
        | none => simp [d] at ok
        | some offset =>
          simp only [d] at ok
          split at ok
          · cases Option.some.inj ok; exact ⟨rfl, by assumption⟩
          · contradiction

theorem interpretValid (h : Header) (valid : Valid h) : interpret h.wire = some h := by
  rcases valid with ⟨w,a,b,c,d,rest⟩
  simp only [interpret,a,b,c,d,bind,Option.bind]
  cases h
  exact if_pos ⟨w,a,b,c,d,rest⟩

def readWire (raw : Bytes) : Option Wire := do
  let values ← NativeQJson.readObject keys raw
  fromValues values

theorem readWireEncoded (w : Wire) (valid : WireValid w) : readWire (encode w) = some w := by
  have nonempty : fields w ≠ [] := by simp [fields]
  unfold readWire encode
  rw [← exactKeys w, NativeQJson.readObjectEncoded (fields w) nonempty valid.2.1 valid.1]
  simpa only [bind, Option.bind] using allFieldsRetained w

def decode (raw : Bytes) : Option Header := do
  let wire ← readWire raw
  let h ← interpret wire
  if encode wire = raw then some h else none

theorem decoded {raw h} (ok : decode raw = some h) : Valid h ∧ encode h.wire = raw := by
  unfold decode at ok
  cases a : readWire raw with
  | none => simp [a] at ok
  | some w =>
    simp only [a, bind, Option.bind] at ok
    cases b : interpret w with
    | none => simp [b] at ok
    | some out =>
      simp only [b] at ok
      split at ok
      · cases Option.some.inj ok
        obtain ⟨eq, valid⟩ := interpreted b
        exact ⟨valid, by simpa only [eq] using ‹encode w = raw›⟩
      · contradiction

theorem decodedComputation {raw h} (ok : decode raw = some h) :
    readWire raw = some h.wire ∧ interpret h.wire = some h := by
  unfold decode at ok
  cases a : readWire raw with
  | none => simp [a] at ok
  | some w =>
    simp only [a,bind,Option.bind] at ok
    cases b : interpret w with
    | none => simp [b] at ok
    | some out =>
      simp only [b] at ok
      split at ok
      · cases Option.some.inj ok
        have same := (interpreted b).1
        exact ⟨by rw [same], by rw [same]; exact b⟩
      · contradiction

theorem decodedFromComputed {raw w h}
    (parsed : readWire raw = some w) (computed : interpret w = some h)
    (canonical : encode w = raw) : decode raw = some h := by
  simp [decode, parsed, computed, canonical]

theorem decodeEncoded (h : Header) (valid : Valid h) : decode (encode h.wire) = some h :=
  decodedFromComputed (readWireEncoded h.wire valid.1) (interpretValid h valid) rfl

theorem headerUnique {a b : Header} (va : Valid a) (vb : Valid b)
    (same : encode a.wire = encode b.wire) : a = b := by
  have ha := decodeEncoded a va
  rw [same, decodeEncoded b vb] at ha
  exact (Option.some.inj ha).symm

theorem decodedNumbers {raw h} (ok : decode raw = some h) :
    parseDecimal h.wire.countRaw = some h.count ∧ parseDecimal h.wire.startRaw = some h.start ∧
    parseDecimal h.wire.ordinalRaw = some h.ordinal ∧ parseDecimal h.wire.offsetRaw = some h.offset := by
  have v := (decoded ok).1
  exact ⟨v.2.1,v.2.2.1,v.2.2.2.1,v.2.2.2.2.1⟩

theorem decodedRanges {raw h} (ok : decode raw = some h) :
    0 < h.count ∧ h.count ≤ 524288 ∧ h.start + h.count ≤ 1073741824 ∧ h.ordinal < 4096 :=
  (decoded ok).1.2.2.2.2.2

theorem decodedOffsetWidth {raw h} (ok : decode raw = some h) : h.offset < 256^8 := by
  have parsed := NativeVoteBytes.decimalSound (decodedNumbers ok).2.2.2
  rw [parsed.2]
  exact parsed.1.2.2.2

structure Joined where
  frame : NativeQBytes.Frame
  header : Header
  deriving DecidableEq, Repr

def join (raw : Bytes) : Option Joined := do
  let frame ← NativeQBytes.decode raw
  let header ← decode frame.header
  if header.count = frame.values.length then some ⟨frame,header⟩ else none

theorem joined {raw out} (ok : join raw = some out) :
    NativeQBytes.decode raw = some out.frame ∧ decode out.frame.header = some out.header ∧
    out.header.count = out.frame.values.length := by
  unfold join at ok
  cases a : NativeQBytes.decode raw with
  | none => simp [a] at ok
  | some frame =>
    simp only [a,bind,Option.bind] at ok
    cases b : decode frame.header with
    | none => simp [b] at ok
    | some header =>
      simp only [b] at ok
      split at ok
      · cases Option.some.inj ok; exact ⟨rfl,b,by assumption⟩
      · contradiction

theorem joinFromComputed {raw frame header}
    (framed : NativeQBytes.decode raw = some frame) (parsed : decode frame.header = some header)
    (count : header.count = frame.values.length) : join raw = some ⟨frame,header⟩ := by
  simp [join,framed,parsed,count]

theorem joinedPayload {raw out} (ok : join raw = some out) :
    NativeQBytes.PayloadRelation out.frame.payload out.frame.values ∧
    out.frame.payload.length = 2 * out.header.count := by
  obtain ⟨framed,_,count⟩ := joined ok
  exact ⟨NativeQBytes.decodedPayload framed, by rw [NativeQBytes.decodedLength framed,count]⟩

theorem joinedHeaderPreimage {raw out} (ok : join raw = some out) :
    Valid out.header ∧ encode out.header.wire = out.frame.header := decoded (joined ok).2.1

theorem joinedGlobalCoordinate {raw out} (ok : join raw = some out)
    (i : Nat) (inside : i < out.frame.values.length) : out.header.start + i < 1073741824 := by
  have ranges := decodedRanges (joined ok).2.1
  have count := (joined ok).2.2
  omega

/-! Segment-offset addition, actual shard-plan intervals, quanta, payload SHA,
manifest/leaf identity and independent source authority are deliberately absent. -/

end DeltaReduce.NativeQHeader
