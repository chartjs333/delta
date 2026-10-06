import DeltaReduce.NativeIscCertificate

/-! ISC-S16-D01 successor source representation, scope revision 3.
No public-state/refinement imports. Sigma is a parameter; legacy definitions
remain unchanged. Structural preservation does not establish producing origin. -/
namespace DeltaReduce.ISCSourceV2
open NativeReceiptBytes NativePolicyCodec NativePolicySchema
open NativeInputSetBody (Context Tuple contextValue tupleValue readContext readTuples)

structure Body where
  context : Context
  parent : Bytes
  root : Bytes
  tuples : List Tuple
  deriving DecidableEq, Repr

structure Certificate where
  body : Body
  threshold : Nat
  signers : List Bytes
  deriving DecidableEq, Repr

def bodyValue (b : Body) : Value :=
  .pair (contextValue b.context) (.pair (.text b.parent)
    (.pair (.text b.root) (.pair (.items (b.tuples.map tupleValue)) .end)))

def readBody : Value → Option Body
  | .pair context (.pair (.text parent) (.pair (.text root) (.pair (.items tuples) .end))) => do
    let ctx ← readContext context
    let ts ← readTuples tuples
    some ⟨ctx,parent,root,ts⟩
  | _ => none

def certificateValue (c : Certificate) : Value :=
  .pair (contextValue c.body.context) (.pair (.text c.body.parent)
    (.pair (.text c.body.root) (.pair (.number c.threshold)
      (.pair (.items (c.signers.map Value.text))
        (.pair (.items (c.body.tuples.map tupleValue)) .end)))))

def readCertificate : Value → Option Certificate
  | .pair context (.pair (.text parent) (.pair (.text root) (.pair (.number threshold)
      (.pair (.items signers) (.pair (.items tuples) .end))))) => do
    let ctx ← readContext context
    let ss ← NativeIscCertificate.readTexts signers
    let ts ← readTuples tuples
    some ⟨⟨ctx,parent,root,ts⟩,threshold,ss⟩
  | _ => none

theorem bodyRead (b : Body) : readBody (bodyValue b) = some b := by
  cases b
  simp only [bodyValue,readBody,NativeInputSetBody.contextRead,
    NativeInputSetBody.tuplesRead,bind,Option.bind]

theorem bodyOriginal {source b} (h : readBody source = some b) : source = bodyValue b := by
  unfold readBody at h
  split at h <;> try contradiction
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨ctx,hc,ts,ht,last⟩ := h
  cases Option.some.inj last
  simp only [bodyValue,← NativeInputSetBody.contextOriginal hc,
    ← NativeInputSetBody.tuplesOriginal ht]

theorem certificateRead (c : Certificate) : readCertificate (certificateValue c) = some c := by
  cases c
  simp only [certificateValue,readCertificate,NativeInputSetBody.contextRead,
    NativeInputSetBody.tuplesRead,NativeIscCertificate.textsRead,bind,Option.bind]

theorem certificateOriginal {source c} (h : readCertificate source = some c) :
    source = certificateValue c := by
  unfold readCertificate at h
  split at h <;> try contradiction
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨ctx,hc,ss,hs,ts,ht,last⟩ := h
  cases Option.some.inj last
  simp only [certificateValue,← NativeInputSetBody.contextOriginal hc,
    ← NativeInputSetBody.tuplesOriginal ht,← NativeIscCertificate.textsOriginal hs]

def fmtBody : Format :=
  .field "context" fmtContext (.field "parent_checkpoint_id" .text
    (.field "input_root" .text (.field "tuples" (.vector 100000 fmtTuple) .end)))

def fmtCertificate : Format :=
  .field "context" fmtContext (.field "parent_checkpoint_id" .text
    (.field "input_root" .text (.field "quorum_threshold" (.uint 4)
      (.field "signer_ids" (.vector 100000 .text)
        (.field "tuples" (.vector 100000 fmtTuple) .end)))))

/-- Only the two approved record occurrences are replaced, preserving all other
native fields and vector bounds. This is not a conversion of legacy values. -/
def successor : Format → Format
  | .field "input_set_bodies" (.vector count _) tail =>
      .field "input_set_bodies" (.vector count fmtBody) (successor tail)
  | .field "input_set_certificates" (.vector count _) tail =>
      .field "input_set_certificates" (.vector count fmtCertificate) (successor tail)
  | .field name head tail => .field name (successor head) (successor tail)
  | .vector count item => .vector count (successor item)
  | f => f

def fields : Format → List String
  | .field name _ tail => name :: fields tail
  | _ => []

theorem completeSnapshotInventory :
    fields (successor fmtSnapshot) = fields fmtSnapshot ∧
    (fields (successor fmtSnapshot)).length = 33 := by decide

theorem completePolicyInventory : fields (successor fmtPolicy) = fields fmtPolicy := by decide

def parentOfBody (source : Value) : Option Bytes := do
  let body ← readBody source
  some body.parent

def parentOfCertificate (source : Value) : Option Bytes := do
  let certificate ← readCertificate source
  some certificate.body.parent

theorem bodyParentExact (b : Body) : parentOfBody (bodyValue b) = some b.parent := by
  simp [parentOfBody,bodyRead]

theorem certificateParentExact (c : Certificate) :
    parentOfCertificate (certificateValue c) = some c.body.parent := by
  simp [parentOfCertificate,certificateRead]

def bodyBytes (sigma : Bytes) (b : Body) : Bytes :=
  NativeInputSetBody.text64 sigma ++ NativeInputSetBody.text64 (NativeConfigAdmission.ascii "2.0.0") ++
  NativeInputSetBody.contextBytes b.context ++ NativeInputSetBody.text64 b.parent ++
  NativeInputSetBody.text64 b.root ++ be 8 b.tuples.length ++
  (b.tuples.map NativeInputSetBody.tupleBytes).flatten

def bodyId (sha : Bytes → Bytes) (sigma : Bytes) (b : Body) : Option Bytes :=
  NativeStateBytes.contentId sha (NativeConfigAdmission.ascii "deltareduce.vote.input-set-body.v2")
    (bodyBytes sigma b)

theorem bodyIgnoresWitness (sha sigma) (a b : Certificate) (same : a.body = b.body) :
    bodyId sha sigma a.body = bodyId sha sigma b.body := by rw [same]

def header : Bytes := [68,86,80,79,76,48,48,50,0,1,0,0,0,0,0,0]

theorem distinctLegacyHeader : header ≠ NativePolicyBytes.header := by decide

theorem fullPolicyRoundTrip {value raw}
    (encoded : encode (successor fmtPolicy) value = some raw) :
    decode (successor fmtPolicy) raw = some value := NativePolicyCodec.encoded encoded

theorem fullPolicyNoErasure {left right raw}
    (a : encode (successor fmtPolicy) left = some raw)
    (b : encode (successor fmtPolicy) right = some raw) : left = right :=
  NativePolicyCodec.encodingInjective a b

/-- W1 changes exactly two existing snapshot memberships. This field operation
does not decide source legality, quorum, durability or phase. -/
def replaceField : Format → Value → String → Value → Option Value
  | .field name _ tail, .pair head rest, key, replacement =>
    if key = name then some (.pair replacement rest)
    else (replaceField tail rest key replacement).map (.pair head)
  | _, _, _, _ => none

theorem replacedOther {fmt before after key replacement observed}
    (ok : replaceField fmt before key replacement = some after)
    (different : observed ≠ key) : lookup fmt after observed = lookup fmt before observed := by
  induction fmt generalizing before after with
  | field name head tail ihHead ihTail =>
    cases before <;> simp only [replaceField] at ok <;> try contradiction
    case pair a b =>
      by_cases same : key = name
      · simp only [same,ite_true] at ok
        cases Option.some.inj ok
        simp [lookup,← same,different]
      · simp only [same,ite_false,Option.map_eq_some_iff] at ok
        obtain ⟨rest,hr,he⟩ := ok
        cases he
        by_cases atHead : observed = name
        · simp [lookup,atHead]
        · simp only [lookup,atHead,ite_false]
          exact ihTail hr
  | _ => cases before <;> simp [replaceField] at ok

def snapshotDelta (before certificates finalized : Value) : Option Value := do
  let intermediate ← replaceField (successor fmtSnapshot) before
    "input_set_certificates" certificates
  replaceField (successor fmtSnapshot) intermediate "finalized_input_set_ids" finalized

theorem snapshotLineageRetained {before after certificates finalized field}
    (ok : snapshotDelta before certificates finalized = some after)
    (notWitness : field ≠ "input_set_certificates")
    (notIndex : field ≠ "finalized_input_set_ids") :
    lookup (successor fmtSnapshot) after field = lookup (successor fmtSnapshot) before field := by
  simp only [snapshotDelta,bind,Option.bind_eq_some_iff] at ok
  obtain ⟨middle,hm,ha⟩ := ok
  exact (replacedOther ha notIndex).trans (replacedOther hm notWitness)

theorem fullPolicyOutsideSnapshotRetained {before after snapshot field}
    (ok : replaceField (successor fmtPolicy) before "snapshot" snapshot = some after)
    (different : field ≠ "snapshot") :
    lookup (successor fmtPolicy) after field = lookup (successor fmtPolicy) before field :=
  replacedOther ok different

end DeltaReduce.ISCSourceV2
