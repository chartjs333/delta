import DeltaReduce.NativeEligibilitySection

/-! Exact APC payload components. Alpha/buckets/transcript and accumulator IDs
are checked primitives, not a proof of robust aggregation or authenticated QC. -/
namespace DeltaReduce.NativePlan
open NativeReceiptBytes NativePolicyCodec NativePolicySchema
open NativeInputSetBody (Context contextValue readContext ContextValid contextBytes text64)
open NativeIscCertificate (quoted array object number readTexts)

structure Bucket where
  bucket : Bytes
  ticket : Bytes
  deriving DecidableEq, Repr
structure Weight where
  numerator : Nat
  denominator : Nat
  ticket : Bytes
  deriving DecidableEq, Repr
structure Common where
  context : Context
  accumulator : Bytes
  buckets : List Bucket
  ec : Bytes
  isc : Bytes
  iterations : Nat
  seed : Bytes
  root : Bytes
  weights : List Weight
  deriving DecidableEq, Repr
structure Certificate where
  common : Common
  threshold : Nat
  signers : List Bytes
  deriving DecidableEq, Repr

def bucketValue (b : Bucket) : Value := .pair (.text b.bucket) (.pair (.text b.ticket) .end)
def readBucket : Value → Option Bucket
  | .pair (.text bucket) (.pair (.text ticket) .end) => some ⟨bucket,ticket⟩
  | _ => none
def weightValue (w : Weight) : Value := .pair
  (.pair (.number w.numerator) (.pair (.number w.denominator) .end)) (.pair (.text w.ticket) .end)
def readWeight : Value → Option Weight
  | .pair (.pair (.number numerator) (.pair (.number denominator) .end))
      (.pair (.text ticket) .end) => some ⟨numerator,denominator,ticket⟩
  | _ => none

def readBuckets : List Value → Option (List Bucket)
  | [] => some []
  | v::vs => do let e ← readBucket v; let es ← readBuckets vs; some (e::es)
theorem bucketRead (e) : readBucket (bucketValue e) = some e := by cases e; rfl
theorem bucketsRead (es) : readBuckets (es.map bucketValue) = some es := by
  induction es with
  | nil => rfl
  | cons e es ih => simp only [List.map_cons,readBuckets,bucketRead,ih,bind,Option.bind]
theorem bucketOriginal {v e} (h : readBucket v = some e) : v = bucketValue e := by
  unfold readBucket at h; split at h <;> try contradiction
  cases Option.some.inj h; rfl
theorem bucketsOriginal {vs es} (h : readBuckets vs = some es) : vs = es.map bucketValue := by
  induction vs generalizing es with
  | nil => simp [readBuckets] at h; subst es; rfl
  | cons v vs ih =>
    simp only [readBuckets,bind,Option.bind_eq_some_iff] at h
    obtain ⟨e,he,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,← bucketOriginal he,← ih hr]

def readWeights : List Value → Option (List Weight)
  | [] => some []
  | v::vs => do let e ← readWeight v; let es ← readWeights vs; some (e::es)
theorem weightRead (e) : readWeight (weightValue e) = some e := by cases e; rfl
theorem weightsRead (es) : readWeights (es.map weightValue) = some es := by
  induction es with
  | nil => rfl
  | cons e es ih => simp only [List.map_cons,readWeights,weightRead,ih,bind,Option.bind]
theorem weightOriginal {v e} (h : readWeight v = some e) : v = weightValue e := by
  unfold readWeight at h; split at h <;> try contradiction
  cases Option.some.inj h; rfl
theorem weightsOriginal {vs es} (h : readWeights vs = some es) : vs = es.map weightValue := by
  induction vs generalizing es with
  | nil => simp [readWeights] at h; subst es; rfl
  | cons v vs ih =>
    simp only [readWeights,bind,Option.bind_eq_some_iff] at h
    obtain ⟨e,he,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,← weightOriginal he,← ih hr]

def value (cert : Certificate) : Value :=
  let c := cert.common
  (.pair (contextValue c.context) (.pair (.text c.accumulator) (.pair (.items (c.buckets.map bucketValue)) (.pair (.text c.ec) (.pair (.text c.isc) (.pair (.number c.iterations) (.pair (.number cert.threshold) (.pair (.text c.seed) (.pair (.items (cert.signers.map Value.text)) (.pair (.text c.root) (.pair (.items (c.weights.map weightValue)) .end)))))))))))
def read : Value → Option Certificate
  | (.pair ctx (.pair (.text accumulator) (.pair (.items buckets) (.pair (.text ec) (.pair (.text isc) (.pair (.number iterations) (.pair (.number threshold) (.pair (.text seed) (.pair (.items signers) (.pair (.text root) (.pair (.items weights) .end))))))))))) => do
    let context ← readContext ctx
    let bs ← readBuckets buckets
    let ws ← readWeights weights
    let ss ← readTexts signers
    some ⟨⟨context,accumulator,bs,ec,isc,iterations,seed,root,ws⟩,threshold,ss⟩
  | _ => none

theorem valueRead (c) : read (value c) = some c := by
  cases c
  simp only [value,read,NativeInputSetBody.contextRead,bucketsRead,weightsRead,
    NativeIscCertificate.textsRead,bind,Option.bind]
theorem readOriginal {v c} (h : read v = some c) : v = value c := by
  unfold read at h; split at h <;> try contradiction
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨c,hc,bs,hb,ws,hw,ss,hs,last⟩ := h
  cases Option.some.inj last
  simp only [value,← NativeInputSetBody.contextOriginal hc,← bucketsOriginal hb,
    ← weightsOriginal hw,← NativeIscCertificate.textsOriginal hs]

def bodyValue (c : Common) : Value :=
  (.pair (contextValue c.context) (.pair (.text c.accumulator) (.pair (.items (c.buckets.map bucketValue)) (.pair (.text c.ec) (.pair (.text c.isc) (.pair (.number c.iterations) (.pair (.text c.seed) (.pair (.text c.root) (.pair (.items (c.weights.map weightValue)) .end)))))))))
def readBody : Value → Option Common
  | (.pair ctx (.pair (.text accumulator) (.pair (.items buckets) (.pair (.text ec) (.pair (.text isc) (.pair (.number iterations) (.pair (.text seed) (.pair (.text root) (.pair (.items weights) .end))))))))) => do
    let context ← readContext ctx
    let bs ← readBuckets buckets
    let ws ← readWeights weights
    some ⟨context,accumulator,bs,ec,isc,iterations,seed,root,ws⟩
  | _ => none

theorem bodyRead (c) : readBody (bodyValue c) = some c := by
  cases c
  simp only [bodyValue,readBody,NativeInputSetBody.contextRead,bucketsRead,weightsRead,bind,Option.bind]
theorem bodyOriginal {v c} (h : readBody v = some c) : v = bodyValue c := by
  unfold readBody at h; split at h <;> try contradiction
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨c,hc,bs,hb,ws,hw,last⟩ := h
  cases Option.some.inj last
  simp only [bodyValue,← NativeInputSetBody.contextOriginal hc,← bucketsOriginal hb,
    ← weightsOriginal hw]

def BucketValid (b : Bucket) : Prop := NativeConfigAdmission.Label b.bucket ∧ NativeConfigAdmission.Label b.ticket
instance (b) : Decidable (BucketValid b) := by unfold BucketValid; infer_instance
def WeightValid (w : Weight) : Prop := w.numerator < 2^63 ∧ 0 < w.denominator ∧
  w.denominator < 256^8 ∧ Nat.gcd w.numerator w.denominator = 1 ∧ NativeConfigAdmission.Label w.ticket
instance (w) : Decidable (WeightValid w) := by unfold WeightValid; infer_instance
def CommonValid (expected : Context) (c : Common) : Prop :=
  ContextValid c.context ∧ c.context = expected ∧
  NativeVoteBytes.ContentId c.accumulator ∧ NativeVoteBytes.ContentId c.ec ∧
  NativeVoteBytes.ContentId c.isc ∧ NativeVoteBytes.ContentId c.seed ∧ NativeVoteBytes.ContentId c.root ∧
  0 < c.iterations ∧ c.iterations < 256^4 ∧
  0 < c.buckets.length ∧ c.buckets.length ≤ 100000 ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (c.buckets.map Bucket.ticket) = true ∧
  (∀ b ∈ c.buckets, BucketValid b) ∧
  0 < c.weights.length ∧ c.weights.length ≤ 100000 ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (c.weights.map Weight.ticket) = true ∧
  ∀ w ∈ c.weights, WeightValid w
instance (expected c) : Decidable (CommonValid expected c) := by unfold CommonValid; infer_instance
theorem iterationPositive {expected c} (h : CommonValid expected c) : 0 < c.iterations :=
  h.2.2.2.2.2.2.2.1
theorem iterationBound {expected c} (h : CommonValid expected c) : c.iterations < 256^4 :=
  h.2.2.2.2.2.2.2.2.1
theorem bucketsNonempty {expected c} (h : CommonValid expected c) : 0 < c.buckets.length :=
  h.2.2.2.2.2.2.2.2.2.1
theorem bucketsOrdered {expected c} (h : CommonValid expected c) :
    NativePolicyBytes.strictly NativePolicyBytes.bytesLT (c.buckets.map Bucket.ticket) = true :=
  h.2.2.2.2.2.2.2.2.2.2.2.1
theorem weightsNonempty {expected c} (h : CommonValid expected c) : 0 < c.weights.length :=
  h.2.2.2.2.2.2.2.2.2.2.2.2.2.1
theorem weightsOrdered {expected c} (h : CommonValid expected c) :
    NativePolicyBytes.strictly NativePolicyBytes.bytesLT (c.weights.map Weight.ticket) = true :=
  h.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.1
def signerView (c : Certificate) : NativeIscCertificate.Certificate :=
  ⟨⟨c.common.context,[],[]⟩,c.threshold,c.signers⟩
def Valid (expected : Context) (committee : List Bytes) (c : Certificate) : Prop :=
  CommonValid expected c.common ∧ NativeIscCertificate.CommitteeValid committee ∧
  NativeIscCertificate.SignersValid committee (signerView c)
instance (expected committee c) : Decidable (Valid expected committee c) := by unfold Valid; infer_instance

def acceptedTickets (c : NativeEligibility.Certificate) : List Bytes :=
  (c.common.entries.filter (fun e => e.accepted != 0)).map NativeEligibility.Entry.ticket
def insertTicket (x : Bytes) : List Bytes → List Bytes
  | [] => [x]
  | y::ys => if NativePolicyBytes.bytesLT x y then x::y::ys else y::insertTicket x ys
def sortTickets : List Bytes → List Bytes
  | [] => []
  | x::xs => insertTicket x (sortTickets xs)
theorem insertLength (x xs) : (insertTicket x xs).length = xs.length + 1 := by
  induction xs with
  | nil => rfl
  | cons y ys ih => simp only [insertTicket]; split <;> simp_all
theorem sortLength (xs) : (sortTickets xs).length = xs.length := by
  induction xs with
  | nil => rfl
  | cons x xs ih => simp only [sortTickets,insertLength,ih,List.length_cons]
theorem insertMembers (x xs y) : y ∈ insertTicket x xs ↔ y = x ∨ y ∈ xs := by
  induction xs with
  | nil => simp [insertTicket]
  | cons a as ih =>
    simp only [insertTicket]; split <;> simp_all [or_left_comm]
theorem sortMembers (xs y) : y ∈ sortTickets xs ↔ y ∈ xs := by
  induction xs with
  | nil => rfl
  | cons x xs ih => simp only [sortTickets,insertMembers,ih,List.mem_cons]
def assignmentTickets (c : Common) : List Bytes := sortTickets (c.buckets.map Bucket.ticket)
theorem sortedFixed (xs : List Bytes)
    (h : NativePolicyBytes.strictly NativePolicyBytes.bytesLT xs = true) : sortTickets xs = xs := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
    cases xs with
    | nil => rfl
    | cons y ys =>
      simp only [NativePolicyBytes.strictly,Bool.and_eq_true] at h
      rw [sortTickets,ih h.2]
      simp only [insertTicket,h.1,ite_true]
def Coverage (c : Common) (ec : NativeEligibility.Certificate) : Prop :=
  acceptedTickets ec = assignmentTickets c ∧ acceptedTickets ec = c.weights.map Weight.ticket
instance (c ec) : Decidable (Coverage c ec) := by unfold Coverage; infer_instance
theorem originalCoverage {expected c ec} (valid : CommonValid expected c) (h : Coverage c ec) :
    acceptedTickets ec = c.buckets.map Bucket.ticket ∧
    acceptedTickets ec = c.weights.map Weight.ticket := by
  have ordered := valid.2.2.2.2.2.2.2.2.2.2.2.1
  exact ⟨h.1.trans (sortedFixed _ ordered),h.2⟩

def bucketJSON (b : Bucket) : Bytes := object [("bucket_id",quoted b.bucket),("ticket_id",quoted b.ticket)]
def weightJSON (w : Weight) : Bytes := object [("alpha",object [("denominator",number w.denominator),
  ("numerator",quoted (number w.numerator))]),("ticket_id",quoted w.ticket)]
def fields (c : Certificate) : List (String × Bytes) :=
  [("accumulator_proof_id",quoted c.common.accumulator),
   ("arithmetic_profile_id",quoted c.common.context.arithmetic),
   ("bucket_assignments",array (c.common.buckets.map bucketJSON)),
   ("eligibility_certificate_id",quoted c.common.ec),
   ("formal_semantics_id",quoted NativeVoteBytes.nativeSemantics),
   ("height",number c.common.context.height),("input_set_certificate_id",quoted c.common.isc),
   ("iteration_count",number c.common.iterations),("parameter_schema_id",quoted c.common.context.schema),
   ("quorum_threshold",number c.threshold),("round_config_id",quoted c.common.context.config),
   ("round_id",quoted c.common.context.round),("schema_version",quoted (NativeVoteBytes.ascii "1.0.0")),
   ("seed_transcript_id",quoted c.common.seed),("signer_ids",array (c.signers.map quoted)),
   ("transcript_root",quoted c.common.root),
   ("type_name",quoted (NativeVoteBytes.ascii "AGGREGATION_PLAN_CERTIFICATE")),
   ("validator_epoch_id",quoted c.common.context.epoch),("view",number c.common.context.view),
   ("weights",array (c.common.weights.map weightJSON))]
def json (c : Certificate) : Bytes := object (fields c)
def domain : Bytes := NativeVoteBytes.ascii "deltareduce.008.aggregation-plan-certificate.v1"
def id (sha : Bytes → Bytes) (c : Certificate) : Option Bytes := NativeStateBytes.contentId sha domain (json c)
def bucketBytes (b : Bucket) : Bytes := text64 b.bucket ++ text64 b.ticket
def weightBytes (w : Weight) : Bytes := be 8 w.numerator ++ be 8 w.denominator ++ text64 w.ticket
def bodyBytes (c : Common) : Bytes := contextBytes c.context ++ text64 c.accumulator ++
  be 8 c.buckets.length ++ (c.buckets.map bucketBytes).flatten ++ text64 c.ec ++
  text64 c.isc ++ be 8 c.iterations ++ text64 c.seed ++ text64 c.root ++
  be 8 c.weights.length ++ (c.weights.map weightBytes).flatten
def bodyDomain : Bytes := NativeVoteBytes.ascii "deltareduce.vote.aggregation-plan-body.v1"
def bodyId (sha : Bytes → Bytes) (c : Common) : Option Bytes := NativeStateBytes.contentId sha bodyDomain (bodyBytes c)
def proposedCertificate (committee : List Bytes) (c : Common) : Certificate :=
  ⟨c,NativeIscCertificate.quorum committee,committee⟩

theorem coveragePositions {c ec} (h : Coverage c ec) (i : Nat) :
    (acceptedTickets ec)[i]? = (assignmentTickets c)[i]? ∧
    (acceptedTickets ec)[i]? = (c.weights.map Weight.ticket)[i]? :=
  ⟨congrArg (fun xs => xs[i]?) h.1,congrArg (fun xs => xs[i]?) h.2⟩
theorem coverageCounts {c ec} (h : Coverage c ec) :
    (acceptedTickets ec).length = c.buckets.length ∧
    (acceptedTickets ec).length = c.weights.length := by
  have hb := congrArg List.length h.1
  have hw := congrArg List.length h.2
  exact ⟨by simpa [assignmentTickets,sortLength] using hb,by simpa using hw⟩
theorem emptyAcceptedImpossible {expected c ec} (valid : CommonValid expected c)
    (empty : acceptedTickets ec = []) : ¬ Coverage c ec := by
  intro h
  have counts := (coverageCounts h).1
  rw [empty] at counts
  have positive := valid.2.2.2.2.2.2.2.2.2.1
  simp only [List.length_nil] at counts
  omega
end DeltaReduce.NativePlan
