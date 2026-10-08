import DeltaReduce.NativeIscCertificate
import DeltaReduce.NativeManifestMerkle

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

/-! The original successor policy tree and the *whole* separately retained C
must agree. There is no permissive JSON parser here: equality with the canonical
serialization rejects duplicate members, extra bytes and alternate encodings.
This join establishes byte/root/shape identity, not signatures or source history.
The hash remains an explicit primitive; no cryptographic axiom is introduced. -/
open NativeConfigAdmission (ascii)
open NativeVoteBytes (ContentId)

def rawHashId (sha : Bytes → Bytes) (raw : Bytes) : Bytes :=
  let digest := sha raw
  if digest.length = 32 then ascii "sha256:" ++ NativeVoteBytes.hexBytes digest else []

def inputLeaf (sha : Bytes → Bytes) (t : Tuple) : Bytes :=
  rawHashId sha (ascii "deltareduce.008.isc-input-leaf.v1" ++ [0] ++
    NativeIscCertificate.tupleJSON t)

/-- 17 pair reductions plus the singleton case covers the *existing* 100000
tuple bound. The 004 manifest helper's separate 4096-leaf cap is not imported. -/
def inputRoot (sha : Bytes → Bytes) (tuples : List Tuple) : Option Bytes :=
  NativeManifestMerkle.tree (rawHashId sha) 18 (tuples.map (inputLeaf sha))

def BodyShape (expected : Context) (parent : Bytes) (b : Body) : Prop :=
  NativeInputSetBody.BodyValid expected ⟨b.context,b.root,b.tuples⟩ ∧
  ContentId b.parent ∧ b.parent = parent ∧ (b.tuples.map Tuple.ticket).Nodup
instance (expected parent b) : Decidable (BodyShape expected parent b) := by
  unfold BodyShape; infer_instance

def CertificateShape (sigma : Bytes) (expected : Context) (parent : Bytes)
    (committee : List Bytes) (c : Certificate) : Prop :=
  ContentId sigma ∧ committee.length = 4 ∧ NativeIscCertificate.CommitteeValid committee ∧
  BodyShape expected parent c.body ∧
  NativeIscCertificate.SignersValid committee
    ⟨⟨c.body.context,c.body.root,c.body.tuples⟩,c.threshold,c.signers⟩
instance (sigma expected parent committee c) :
    Decidable (CertificateShape sigma expected parent committee c) := by
  unfold CertificateShape; infer_instance

def certificateFields (sigma : Bytes) (c : Certificate) : List (String × Bytes) :=
  let quoted := NativeIscCertificate.quoted
  let number := NativeIscCertificate.number
  let array := NativeIscCertificate.array
  [("arithmetic_profile_id",quoted c.body.context.arithmetic),
   ("formal_semantics_id",quoted sigma),
   ("height",number c.body.context.height),("input_root",quoted c.body.root),
   ("parameter_schema_id",quoted c.body.context.schema),
   ("parent_checkpoint_id",quoted c.body.parent),("quorum_threshold",number c.threshold),
   ("round_config_id",quoted c.body.context.config),("round_id",quoted c.body.context.round),
   ("schema_version",quoted (ascii "2.0.0")),("signer_ids",array (c.signers.map quoted)),
   ("tuples",array (c.body.tuples.map NativeIscCertificate.tupleJSON)),
   ("type_name",quoted (ascii "INPUT_SET_CERTIFICATE")),
   ("validator_epoch_id",quoted c.body.context.epoch),("view",number c.body.context.view)]

def certificateJSON (sigma : Bytes) (c : Certificate) : Bytes :=
  NativeIscCertificate.object (certificateFields sigma c)

def certificateId (sha : Bytes → Bytes) (sigma : Bytes) (c : Certificate) : Option Bytes :=
  NativeStateBytes.contentId sha (ascii "deltareduce.008.input-set-certificate.v2")
    (certificateJSON sigma c)

structure BoundCertificate where
  certificate : Certificate
  originalTree : Value
  originalBytes : Bytes
  consensusId : Bytes
  witnessId : Bytes

def bindCertificate (sha : Bytes → Bytes) (sigma : Bytes) (expected : Context)
    (parent : Bytes) (committee : List Bytes) (tree : Value) (raw : Bytes) :
    Option BoundCertificate := do
  let c ← readCertificate tree
  if CertificateShape sigma expected parent committee c ∧
      raw.length ≤ 4*1024*1024 ∧ raw = certificateJSON sigma c ∧
      inputRoot sha c.body.tuples = some c.body.root then
    let b ← bodyId sha sigma c.body
    let w ← certificateId sha sigma c
    some ⟨c,tree,raw,b,w⟩
  else none

structure CertificateSource (sha : Bytes → Bytes) (sigma : Bytes) (expected : Context)
    (parent : Bytes) (committee : List Bytes) (tree : Value) (raw : Bytes)
    (out : BoundCertificate) : Prop where
  treeExact : out.originalTree = tree
  bytesExact : out.originalBytes = raw
  parsed : readCertificate tree = some out.certificate
  fullTree : tree = certificateValue out.certificate
  shape : CertificateShape sigma expected parent committee out.certificate
  size : raw.length ≤ 4*1024*1024
  canonical : raw = certificateJSON sigma out.certificate
  root : inputRoot sha out.certificate.body.tuples = some out.certificate.body.root
  body : bodyId sha sigma out.certificate.body = some out.consensusId
  witness : certificateId sha sigma out.certificate = some out.witnessId

theorem boundCertificateSource {sha sigma expected parent committee tree raw out}
    (h : bindCertificate sha sigma expected parent committee tree raw = some out) :
    CertificateSource sha sigma expected parent committee tree raw out := by
  simp only [bindCertificate,bind,Option.bind_eq_some_iff] at h
  obtain ⟨c,hc,last⟩ := h
  split at last <;> try contradiction
  rename_i guards
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨b,hb,w,hw,he⟩ := last
  cases Option.some.inj he
  exact ⟨rfl,rfl,hc,certificateOriginal hc,guards.1,guards.2.1,
    guards.2.2.1,guards.2.2.2,hb,hw⟩

theorem bindCertificateComplete {sha sigma expected parent committee tree raw c b w}
    (parsed : readCertificate tree = some c)
    (shape : CertificateShape sigma expected parent committee c)
    (size : raw.length ≤ 4*1024*1024) (canonical : raw = certificateJSON sigma c)
    (root : inputRoot sha c.body.tuples = some c.body.root)
    (body : bodyId sha sigma c.body = some b) (witness : certificateId sha sigma c = some w) :
    bindCertificate sha sigma expected parent committee tree raw = some ⟨c,tree,raw,b,w⟩ := by
  have guards : CertificateShape sigma expected parent committee c ∧
      raw.length ≤ 4*1024*1024 ∧ raw = certificateJSON sigma c ∧
      inputRoot sha c.body.tuples = some c.body.root := ⟨shape,size,canonical,root⟩
  simp only [bindCertificate,parsed,bind,Option.bind,if_pos guards,body,witness]

theorem boundOrderedMerkle {sha sigma expected parent committee tree raw out}
    (h : bindCertificate sha sigma expected parent committee tree raw = some out) :
    NativeManifestMerkle.Tree (rawHashId sha)
      (out.certificate.body.tuples.map (inputLeaf sha)) out.certificate.body.root :=
  NativeManifestMerkle.treeSource (boundCertificateSource h).root

theorem boundOriginalTuples {sha sigma expected parent committee tree raw out}
    (h : bindCertificate sha sigma expected parent committee tree raw = some out) :
    readCertificate tree = some out.certificate ∧
    (out.certificate.body.tuples.map Tuple.ticket).Nodup ∧
    NativePolicyBytes.strictly NativeInputSetBody.tupleLT out.certificate.body.tuples = true := by
  have s := boundCertificateSource h
  exact ⟨s.parsed,s.shape.2.2.2.1.2.2.2,s.shape.2.2.2.1.1.2.2.2.2.2.1⟩

theorem boundExplicitParent {sha sigma expected parent committee tree raw out}
    (h : bindCertificate sha sigma expected parent committee tree raw = some out) :
    out.certificate.body.parent = parent ∧ out.certificate.body.context = expected := by
  have shape := (boundCertificateSource h).shape.2.2.2.1
  exact ⟨shape.2.2.1,shape.1.2.1⟩

theorem boundSignerQuorum {sha sigma expected parent committee tree raw out}
    (h : bindCertificate sha sigma expected parent committee tree raw = some out) :
    out.certificate.threshold = 3 ∧ 3 ≤ out.certificate.signers.length ∧
    ∀ signer ∈ out.certificate.signers, signer ∈ committee := by
  have s := (boundCertificateSource h).shape
  have q := s.2.2.2.2
  have qt : NativeIscCertificate.quorum committee = 3 := by
    simp [NativeIscCertificate.quorum,s.2.1]
  exact ⟨q.2.2.1.trans qt,qt ▸ q.2.2.1 ▸ q.2.2.2.1,
    fun signer hs => (q.2.2.2.2.2.2 signer hs).2⟩

theorem noncanonicalCertificateRejected {sha sigma expected parent committee tree raw c}
    (parsed : readCertificate tree = some c) (different : raw ≠ certificateJSON sigma c) :
    bindCertificate sha sigma expected parent committee tree raw = none := by
  simp [bindCertificate,parsed,different]

theorem merkleLevelComplete {hash leaves next}
    (h : NativeManifestMerkle.Layer hash leaves next) :
    NativeManifestMerkle.level hash leaves = some next := by
  induction h with
  | nil => rfl
  | odd checked => simp [NativeManifestMerkle.level,checked]
  | cons checked remaining ih => simp [NativeManifestMerkle.level,checked,ih]

/-- Completeness with respect to the original duplicate-last recurrence;
the fuel parameter cannot silently exclude a valid tree in the approved bound. -/
theorem merkleFuelComplete {hash leaves root} (fuel : Nat)
    (h : NativeManifestMerkle.Tree hash leaves root) (bound : leaves.length ≤ 2^fuel) :
    NativeManifestMerkle.tree hash (fuel+1) leaves = some root := by
  induction fuel generalizing leaves root with
  | zero =>
    cases h with
    | leaf valid => simp [NativeManifestMerkle.tree,valid]
    | step layer remaining => simp only [List.length_cons,Nat.pow_zero] at bound; omega
  | succ fuel ih =>
    cases h with
    | leaf valid => simp [NativeManifestMerkle.tree,valid]
    | @step a b rest next root layer remaining =>
      have size := NativeManifestMerkle.levelLength layer
      have limit : next.length ≤ 2^fuel := by
        simp only [List.length_cons,Nat.pow_succ] at bound size
        omega
      simp only [NativeManifestMerkle.tree,merkleLevelComplete layer,bind,Option.bind]
      exact ih remaining limit

theorem approvedInputBoundComplete {sha tuples root}
    (bound : tuples.length ≤ 100000)
    (tree : NativeManifestMerkle.Tree (rawHashId sha) (tuples.map (inputLeaf sha)) root) :
    inputRoot sha tuples = some root := by
  apply merkleFuelComplete 17 tree
  simp only [List.length_map]
  exact Nat.le_trans bound (by decide)

end DeltaReduce.ISCSourceV2
