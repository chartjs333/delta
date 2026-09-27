import DeltaReduce.NativeIscCorpus

/-! Computed ISC/EC projections from every original member manifest. This does
not derive the original commitment hash preimage or the complete PLAN/APC graph.
No rejected member is filtered from the ISC Q corpus. -/
namespace DeltaReduce.NativeIscProjection
open NativeBinding
open NativeVectorArtifacts (Artifact pack encodeQ)
open NativeVectorLayout (text shardName)

def qValue (schema : Ref) (t : NativeInputSetBody.Tuple) (q : NativeScaleBinding.Bound) : QShard :=
  ⟨text t.ticket,text t.domain,shardName q.block.header.ordinal,schema,q.quantum,q.block.frame.values⟩

def QChecks (schema : Ref) (t : NativeInputSetBody.Tuple) (q : NativeScaleBinding.Bound) : Prop :=
  schema.kind = .schema ∧ schema.id.length = 32 ∧ 0 < schema.length ∧ schema.length ≤ 4194304 ∧
  (∀ id ∈ [t.ticket,t.domain], asciiBytes (text id) = id ∧ validIdentifier (text id) = true) ∧
  q.block.header.ordinal < 4096 ∧ 0 < q.block.frame.values.length ∧ q.block.frame.values.length ≤ 4096 ∧
  positiveQuantum q.quantum ∧ ∀ v ∈ q.block.frame.values, Fits minInput maxInput v
instance (s t q) : Decidable (QChecks s t q) := by unfold QChecks; infer_instance

def qArtifact (hash : Bytes → ContentId) (schema : Ref) (t : NativeInputSetBody.Tuple)
    (q : NativeScaleBinding.Bound) : Option Artifact :=
  if QChecks schema t q then pack hash (encodeQ (qValue schema t q)) (.qShard (qValue schema t q)) else none

theorem qEncoded {hash schema t q a} (h : qArtifact hash schema t q = some a) :
    QChecks schema t q ∧ a.raw = encodeQ (qValue schema t q) ∧ a.payload = .qShard (qValue schema t q) ∧
    a.ref = ⟨hash (encodeQ (qValue schema t q)),.qShard,(encodeQ (qValue schema t q)).length⟩ := by
  by_cases checks : QChecks schema t q
  · rw [qArtifact,if_pos checks] at h
    have p := @NativeVectorArtifacts.packed hash (encodeQ (qValue schema t q))
      (.qShard (qValue schema t q)) a h
    exact ⟨checks,p.1,p.2.1,p.2.2.1⟩
  · simp only [qArtifact,if_neg checks] at h
    contradiction

theorem sameEligibleEncoding (schema : Ref) (s : NativeVectorContext.Slice) :
    qValue schema s.source.term.source.member.input s.block = NativeVectorArtifacts.qValue schema s := rfl

theorem sameEligibleArtifact (hash : Bytes → ContentId) (schema : Ref) (s : NativeVectorContext.Slice) :
    qArtifact hash schema s.source.term.source.member.input s.block =
      NativeVectorArtifacts.qArtifact hash schema s := rfl

structure LeafImage where
  original : NativeManifestBinding.Ref
  block : NativeScaleBinding.Bound
  artifact : Artifact

def leaf (hash : Bytes → ContentId) (schema : Ref) (t : NativeInputSetBody.Tuple)
    (original : NativeManifestBinding.Ref) (q : NativeScaleBinding.Bound) : Option LeafImage := do
  if original.entry = NativeShardPlanBinding.headerEntry q.block.header then
    let a ← qArtifact hash schema t q
    some ⟨original,q,a⟩
  else none

theorem leafSource {hash schema t ref q out} (h : leaf hash schema t ref q = some out) :
    out.original = ref ∧ out.block = q ∧ ref.entry = NativeShardPlanBinding.headerEntry q.block.header ∧
    qArtifact hash schema t q = some out.artifact := by
  unfold leaf at h
  split at h <;> try contradiction
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨a,ha,last⟩ := h
  cases Option.some.inj last
  exact ⟨rfl,rfl,by assumption,ha⟩

def leaves (hash : Bytes → ContentId) (schema : Ref) (t : NativeInputSetBody.Tuple) :
    List NativeManifestBinding.Ref → List NativeScaleBinding.Bound → Option (List LeafImage)
  | [],[] => some []
  | r::rs,q::qs => do
    let a ← leaf hash schema t r q
    let rest ← leaves hash schema t rs qs
    some (a::rest)
  | _,_ => none

theorem allLeaves {hash schema t refs qs out} (h : leaves hash schema t refs qs = some out) :
    out.map LeafImage.original = refs ∧ out.map LeafImage.block = qs := by
  induction refs generalizing qs out with
  | nil => cases qs <;> simp [leaves] at h; subst out; exact ⟨rfl,rfl⟩
  | cons r rs ih =>
    cases qs with
    | nil => simp [leaves] at h
    | cons q qs =>
      simp only [leaves,bind,Option.bind_eq_some_iff] at h
      obtain ⟨a,ha,rest,hr,last⟩ := h
      cases Option.some.inj last
      simp [(leafSource ha).1,(leafSource ha).2.1,(ih hr).1,(ih hr).2]

theorem leafAt {hash schema t refs qs out} (h : leaves hash schema t refs qs = some out)
    {n : Nat} {a : LeafImage} (position : out[n]? = some a) :
    ∃ r q, refs[n]? = some r ∧ qs[n]? = some q ∧ leaf hash schema t r q = some a := by
  induction refs generalizing qs out n with
  | nil => cases qs <;> simp [leaves] at h; subst out; simp at position
  | cons r rs ih =>
    cases qs with
    | nil => simp [leaves] at h
    | cons q qs =>
      simp only [leaves,bind,Option.bind_eq_some_iff] at h
      obtain ⟨a',ha,rest,hr,last⟩ := h
      cases Option.some.inj last
      cases n with
      | zero => simp at position; subst a; exact ⟨r,q,rfl,rfl,ha⟩
      | succ n => simpa using ih hr (by simpa using position)

def projectedLeaf (l : LeafImage) : Leaf := ⟨shardName l.block.block.header.ordinal,l.artifact.ref⟩
structure RowImage where
  source : NativeIscCorpus.Row
  leaves : List LeafImage

def commitment (r : RowImage) : Commitment :=
  ⟨text r.source.member.input.ticket,text r.source.member.input.domain,r.leaves.map projectedLeaf⟩

def projectRow (hash : Bytes → ContentId) (schema : Ref) (r : NativeIscCorpus.Row) : Option RowImage := do
  let ls ← leaves hash schema r.member.input r.corpus.manifest.refs r.corpus.blocks
  some ⟨r,ls⟩

theorem rowSource {hash schema r out} (h : projectRow hash schema r = some out) :
    out.source = r ∧ leaves hash schema r.member.input r.corpus.manifest.refs r.corpus.blocks = some out.leaves := by
  simp only [projectRow,bind,Option.bind_eq_some_iff] at h
  obtain ⟨ls,hl,last⟩ := h
  cases Option.some.inj last
  exact ⟨rfl,hl⟩

theorem fullCommitment {hash schema r out} (h : projectRow hash schema r = some out) :
    (commitment out).ticket = text r.member.input.ticket ∧
    (commitment out).domain = text r.member.input.domain ∧
    (commitment out).leaves.length = r.corpus.manifest.refs.length ∧
    out.leaves.map (fun l => l.original.wire.leaf) = r.corpus.manifest.refs.map (fun r => r.wire.leaf) := by
  have src := rowSource h
  have originals := (allLeaves src.2).1
  refine ⟨by simp [commitment,src.1],by simp [commitment,src.1],?_,?_⟩
  · simpa [commitment] using congrArg List.length originals
  · rw [← originals,List.map_map]; rfl

def projectRows (hash : Bytes → ContentId) (schema : Ref) : List NativeIscCorpus.Row → Option (List RowImage)
  | [] => some []
  | r::rs => do
    let out ← projectRow hash schema r
    let rest ← projectRows hash schema rs
    some (out::rest)

theorem everyRow {hash schema rs out} (h : projectRows hash schema rs = some out) :
    out.map RowImage.source = rs := by
  induction rs generalizing out with
  | nil => simp [projectRows] at h; subst out; rfl
  | cons r rs ih =>
    simp only [projectRows,bind,Option.bind_eq_some_iff] at h
    obtain ⟨a,ha,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp [(rowSource ha).1,ih hr]

theorem projectedRowAt {hash schema rs out} (h : projectRows hash schema rs = some out)
    {n : Nat} {a : RowImage} (position : out[n]? = some a) :
    ∃ r, rs[n]? = some r ∧ projectRow hash schema r = some a := by
  induction rs generalizing out n with
  | nil => simp [projectRows] at h; subst out; simp at position
  | cons r rs ih =>
    simp only [projectRows,bind,Option.bind_eq_some_iff] at h
    obtain ⟨a',ha,rest,hr,last⟩ := h
    cases Option.some.inj last
    cases n with
    | zero => simp at position; subst a; exact ⟨r,rfl,ha⟩
    | succ n => simpa using ih hr (by simpa using position)

def encodeRef (kind : String) (r : Ref) : Bytes :=
  asciiBytes "{\"id\":" ++ quotedBytes (idBytes r.id) ++ asciiBytes ",\"kind\":" ++
  quotedBytes (asciiBytes kind) ++ asciiBytes ",\"length\":" ++ asciiBytes (toString r.length) ++ [125]
def encodeLeaf (l : Leaf) : Bytes :=
  asciiBytes "{\"q\":" ++ encodeRef "Q_SHARD" l.q ++
  asciiBytes ",\"shard\":" ++ quotedBytes (asciiBytes l.shard) ++ [125]
def encodeCommitment (c : Commitment) : Bytes :=
  asciiBytes "{\"domain\":" ++ quotedBytes (asciiBytes c.domain) ++
  asciiBytes ",\"leaves\":" ++ arrayBytes (c.leaves.map encodeLeaf) ++
  asciiBytes ",\"ticket\":" ++ quotedBytes (asciiBytes c.ticket) ++ [125]
def encodeIsc (members : List String) (cs : List Commitment) : Bytes :=
  asciiBytes "{\"kind\":\"ISC_PROJECTION\",\"payload\":{\"commitments\":" ++
  arrayBytes (cs.map encodeCommitment) ++ asciiBytes ",\"members\":" ++
  arrayBytes (members.map (quotedBytes ∘ asciiBytes)) ++ [125,125]
def encodeEc (isc : Ref) (eligible : List String) : Bytes :=
  asciiBytes "{\"kind\":\"EC_PROJECTION\",\"payload\":{\"eligible\":" ++
  arrayBytes (eligible.map (quotedBytes ∘ asciiBytes)) ++ asciiBytes ",\"isc\":" ++
  encodeRef "ISC_PROJECTION" isc ++ [125,125]

def memberIds (out : List RowImage) := out.map (fun r => (commitment r).ticket)
def eligibleIds (c : NativeIscCorpus.Complete) :=
  (NativePlanMembers.eligible c.members).map (fun m => text m.input.ticket)

structure Image where
  corpus : NativeIscCorpus.Complete
  layout : NativeVectorLayout.Layout
  schema : Artifact
  rows : List RowImage
  isc : Artifact
  ec : Artifact

def construct (sha : Bytes → Bytes) (hash : Bytes → ContentId) (b : NativeVectorContext.Bound)
    (p : NativeAvailableQ.Permission) (inputs : List NativeAvailableQ.Input) : Option Image := do
  let c ← NativeIscCorpus.collect sha b p inputs
  let layout ← NativeVectorLayout.construct b.first.corpus.manifest.plan
  let schema ← NativeVectorArtifacts.schema hash layout
  let rows ← projectRows hash schema.ref c.rows
  let isc ← pack hash (encodeIsc (memberIds rows) (rows.map commitment)) (.isc (memberIds rows) (rows.map commitment))
  let ec ← pack hash (encodeEc isc.ref (eligibleIds c)) (.ec isc.ref (eligibleIds c))
  some ⟨c,layout,schema,rows,isc,ec⟩

structure Source (sha : Bytes → Bytes) (hash : Bytes → ContentId) (b : NativeVectorContext.Bound)
    (p : NativeAvailableQ.Permission) (inputs : List NativeAvailableQ.Input) (out : Image) : Prop where
  corpus : NativeIscCorpus.collect sha b p inputs = some out.corpus
  layout : NativeVectorLayout.construct b.first.corpus.manifest.plan = some out.layout
  schema : NativeVectorArtifacts.schema hash out.layout = some out.schema
  rows : projectRows hash out.schema.ref out.corpus.rows = some out.rows
  isc : pack hash (encodeIsc (memberIds out.rows) (out.rows.map commitment))
    (.isc (memberIds out.rows) (out.rows.map commitment)) = some out.isc
  ec : pack hash (encodeEc out.isc.ref (eligibleIds out.corpus))
    (.ec out.isc.ref (eligibleIds out.corpus)) = some out.ec

theorem constructed {sha hash b p inputs out} (h : construct sha hash b p inputs = some out) :
    Source sha hash b p inputs out := by
  simp only [construct,bind,Option.bind_eq_some_iff] at h
  obtain ⟨c,hc,l,hl,s,hs,rs,hr,i,hi,e,he,last⟩ := h
  cases Option.some.inj last
  exact ⟨hc,hl,hs,hr,hi,he⟩

theorem constructFromSource {sha hash b p inputs out} (h : Source sha hash b p inputs out) :
    construct sha hash b p inputs = some out := by
  simp only [construct,h.corpus,h.layout,h.schema,h.rows,h.isc,h.ec,bind,Option.bind]

theorem originalMembers {sha hash b p inputs out} (h : construct sha hash b p inputs = some out) :
    memberIds out.rows = NativeVectorAuthority.members b := by
  have rows := everyRow (constructed h).rows
  have original := (NativeIscCorpus.everyOriginalMember (constructed h).corpus).1
  change out.rows.map (fun r => text r.source.member.input.ticket) = _
  rw [NativeVectorAuthority.members,← original,← rows,List.map_map,List.map_map]
  rfl

theorem completeBodies {sha hash b p inputs out} (h : construct sha hash b p inputs = some out) :
    out.isc.raw = encodeIsc (memberIds out.rows) (out.rows.map commitment) ∧
    out.isc.payload = .isc (memberIds out.rows) (out.rows.map commitment) ∧
    out.ec.raw = encodeEc out.isc.ref (eligibleIds out.corpus) ∧
    out.ec.payload = .ec out.isc.ref (eligibleIds out.corpus) := by
  have i := NativeVectorArtifacts.packed (constructed h).isc
  have e := NativeVectorArtifacts.packed (constructed h).ec
  exact ⟨i.1,i.2.1,e.1,e.2.1⟩

def artifacts (out : Image) : List Artifact :=
  out.schema :: out.isc :: out.ec :: out.rows.flatMap (fun r => r.leaves.map LeafImage.artifact)

def Stored (codec : Codec) (store : Store) (a : Artifact) : Prop :=
  store a.ref.id = some a.raw ∧ codec.hash a.raw = a.ref.id ∧ a.raw.length = a.ref.length ∧
  codec.canonical a.raw = true ∧ codec.decode a.raw = some a.payload ∧
  a.payload.kind = a.ref.kind ∧ a.payload.wellTypedEdges
instance (codec store a) : Decidable (Stored codec store a) := by unfold Stored; infer_instance

theorem storedResolves {codec store a} (h : Stored codec store a) :
    Resolves codec store a.ref a.raw a.payload :=
  ⟨h.1,h.2.1,h.2.2.1,h.2.2.2.1,h.2.2.2.2.1,h.2.2.2.2.2.1,h.2.2.2.2.2.2⟩

def check (sha : Bytes → Bytes) (codec : Codec) (store : Store) (b : NativeVectorContext.Bound)
    (p : NativeAvailableQ.Permission) (inputs : List NativeAvailableQ.Input) : Option Image := do
  let out ← construct sha codec.hash b p inputs
  if ∀ a ∈ artifacts out, Stored codec store a then some out else none

theorem checked {sha codec store b p inputs out} (h : check sha codec store b p inputs = some out) :
    construct sha codec.hash b p inputs = some out ∧ ∀ a ∈ artifacts out, Stored codec store a := by
  simp only [check,bind,Option.bind_eq_some_iff] at h
  obtain ⟨a,ha,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨ha,by assumption⟩

theorem iscResolved {sha codec store b p inputs out} (h : check sha codec store b p inputs = some out) :
    Resolves codec store out.isc.ref out.isc.raw (.isc (memberIds out.rows) (out.rows.map commitment)) := by
  have r := storedResolves ((checked h).2 out.isc (by simp [artifacts]))
  rw [(completeBodies (checked h).1).2.1] at r
  exact r

theorem ecResolved {sha codec store b p inputs out} (h : check sha codec store b p inputs = some out) :
    Resolves codec store out.ec.ref out.ec.raw (.ec out.isc.ref (eligibleIds out.corpus)) := by
  have r := storedResolves ((checked h).2 out.ec (by simp [artifacts]))
  rw [(completeBodies (checked h).1).2.2.2] at r
  exact r

theorem unavailableRejected {sha codec store b p inputs out a}
    (built : construct sha codec.hash b p inputs = some out) (member : a ∈ artifacts out)
    (absent : store a.ref.id = none) : check sha codec store b p inputs = none := by
  have bad : ¬ ∀ x ∈ artifacts out, Stored codec store x := by
    intro all
    have present := (all a member).1
    rw [absent] at present
    contradiction
  simp [check,built,bad]

def FrameChecks {codec store trust anchor} (binding : Binding codec trust anchor store)
    (frame : ParameterFrame) (out : Image) : Prop :=
  binding.authority.schema = out.schema.ref ∧ binding.authority.isc = out.isc.ref ∧
  binding.authority.ec = out.ec.ref ∧ frame.members = memberIds out.rows ∧
  frame.commitments = out.rows.map commitment ∧ frame.ecIsc = out.isc.ref ∧
  frame.eligible = eligibleIds out.corpus
instance {codec store trust anchor} (binding : Binding codec trust anchor store) (frame out) :
    Decidable (FrameChecks binding frame out) := by unfold FrameChecks; infer_instance

def join {codec store trust anchor} (binding : Binding codec trust anchor store)
    (sha : Bytes → Bytes) (b : NativeVectorContext.Bound) (p : NativeAvailableQ.Permission)
    (inputs : List NativeAvailableQ.Input) (domain : Bytes) (index : Nat) := do
  let verified ← NativeVectorAuthority.verify binding sha b domain index
  let out ← check sha codec store b p inputs
  if FrameChecks binding verified.computation.native.frame out then some (verified,out) else none

theorem joined {codec store trust anchor binding sha b p inputs domain index verified out}
    (h : @join codec store trust anchor binding sha b p inputs domain index = some (verified,out)) :
    NativeVectorAuthority.verify binding sha b domain index = some verified ∧
    check sha codec store b p inputs = some out ∧ FrameChecks binding verified.computation.native.frame out := by
  simp only [join,bind,Option.bind_eq_some_iff] at h
  obtain ⟨v,hv,o,ho,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨hv,ho,by assumption⟩

theorem joinedIscOrigin {codec store trust anchor binding sha b p inputs domain index verified out}
    (h : @join codec store trust anchor binding sha b p inputs domain index = some (verified,out)) :
    Resolves codec store binding.authority.isc out.isc.raw
      (.isc verified.computation.native.frame.members verified.computation.native.frame.commitments) := by
  have src := joined h
  rw [src.2.2.2.1,src.2.2.2.2.2.1,src.2.2.2.2.2.2.1]
  exact iscResolved src.2.1

theorem joinedEcOrigin {codec store trust anchor binding sha b p inputs domain index verified out}
    (h : @join codec store trust anchor binding sha b p inputs domain index = some (verified,out)) :
    Resolves codec store binding.authority.ec out.ec.raw
      (.ec verified.computation.native.frame.ecIsc verified.computation.native.frame.eligible) := by
  have src := joined h
  rw [src.2.2.2.2.1,src.2.2.2.2.2.2.2.1,src.2.2.2.2.2.2.2.2]
  exact ecResolved src.2.1

def run {codec store trust anchor} (binding : Binding codec trust anchor store)
    (sha : Bytes → Bytes) (policyRaw stateRaw apcId configRaw proofRaw profileRaw : Bytes)
    (p : NativeAvailableQ.Permission) (eligibleInputs allInputs : List NativeAvailableQ.Input)
    (domain : Bytes) (index : Nat) := do
  let b ← NativeVectorContext.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw p eligibleInputs
  let (verified,out) ← join binding sha b p allInputs domain index
  some ((⟨b,verified⟩ : (b : NativeVectorContext.Bound) × NativeVectorAuthority.Verified binding b domain index),out)

theorem runSource {codec store trust anchor binding sha policyRaw stateRaw apcId configRaw proofRaw profileRaw
    p eligibleInputs allInputs domain index b verified out}
    (h : @run codec store trust anchor binding sha policyRaw stateRaw apcId configRaw proofRaw profileRaw
      p eligibleInputs allInputs domain index = some (⟨b,verified⟩,out)) :
    NativeVectorContext.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw p eligibleInputs = some b ∧
    join binding sha b p allInputs domain index = some (verified,out) := by
  simp only [run,bind,Option.bind_eq_some_iff] at h
  obtain ⟨b',hb,⟨v,o⟩,hj,last⟩ := h
  cases Option.some.inj last
  exact ⟨hb,hj⟩
end DeltaReduce.NativeIscProjection
