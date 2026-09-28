import DeltaReduce.NativeCacheHistory

/-! Original CONFIG/ISC source bodies loaded at their actual historical state.
No public aliases, future arithmetic Binding or signer authentication is supplied. -/
namespace DeltaReduce.NativeEarlySource
open NativeBinding
open NativeSelectedVote (Checked)

structure Loaded (sha : Bytes → Bytes) (policy state vote : Bytes) (facts : NativeConfigAdmission.RuntimeFacts) where
  original : Checked
  computed : NativeSelectedVote.fromBytes sha policy state vote facts = some original

def load (sha : Bytes → Bytes) (policy state vote : Bytes) (facts : NativeConfigAdmission.RuntimeFacts) :
    Option (Loaded sha policy state vote facts) :=
  match h : NativeSelectedVote.fromBytes sha policy state vote facts with
  | none => none
  | some x => some ⟨x,h⟩

def expected (x : Checked) : NativeInputSetBody.Context :=
  NativeIscAdmission.expected x.policy x.state x.admitted.checked.snapshot.base.schema
    x.admitted.checked.snapshot.base.arithmetic

def iscMatches (x : Checked) : List NativeProposedIsc.Checked :=
  x.admitted.checked.snapshot.base.inputs.filter (fun b => b.body.id == x.admitted.selected.original.body)

def BodyChecked (sha : Bytes → Bytes) (x : Checked) (b : NativeProposedIsc.Checked) : Prop :=
  NativeInputSetBody.readBody b.body.source = some b.body.body ∧
  NativeInputSetBody.bodyId sha b.body.body = some b.body.id ∧
  NativeInputSetBody.BodyValid (expected x) b.body.body
instance (sha x b) : Decidable (BodyChecked sha x b) := by unfold BodyChecked; infer_instance

structure Isc (sha : Bytes → Bytes) (x : Checked) where
  original : NativeProposedIsc.Checked
  selected : iscMatches x = [original]
  kind : x.admitted.selected.original.action = 2
  recomputed : BodyChecked sha x original

def loadIsc (sha : Bytes → Bytes) (x : Checked) : Option (Isc sha x) :=
  if kind : x.admitted.selected.original.action = 2 then
    match selected : iscMatches x with
    | [b] =>
      if computed : BodyChecked sha x b then
        some ⟨b,selected,kind,computed⟩ else none
    | _ => none
  else none

structure Config (x : Checked) : Prop where
  kind : x.admitted.selected.original.action = 1
  same : x.admitted.selected.original.body = x.policy.config
  proposed : x.policy.config ∈ x.admitted.checked.snapshot.base.proposedConfigs

instance (x) : Decidable (Config x) :=
  decidable_of_iff (x.admitted.selected.original.action = 1 ∧
    x.admitted.selected.original.body = x.policy.config ∧
    x.policy.config ∈ x.admitted.checked.snapshot.base.proposedConfigs)
    ⟨fun h => ⟨h.1,h.2.1,h.2.2⟩, fun h => ⟨h.kind,h.same,h.proposed⟩⟩

theorem loadedOriginal {sha policy state vote facts} (x : Loaded sha policy state vote facts) :
    NativeSelectedVote.Source sha policy state vote facts x.original :=
  NativeSelectedVote.fromBytesSource x.computed

theorem loadedBytes {sha policy state vote facts} (x : Loaded sha policy state vote facts) :
    NativeVoteBytes.encodeFrame x.original.vote.wire = vote ∧
    NativeStateBytes.encodeState x.original.state.wire = state :=
  ⟨(NativeSelectedVote.originalBytes x.computed).1,(NativeSelectedVote.originalBytes x.computed).2.1⟩

theorem loadedAuthority {sha policy state vote facts} (x : Loaded sha policy state vote facts) :
    NativeCandidateAuthority.check sha x.original.policy x.original.state
      x.original.admitted.checked.snapshot x.original.admitted.selected.original = some x.original.admitted.selected :=
  (NativeSelectedVote.admittedOriginal (loadedOriginal x).admitted).2

theorem loadedIdentity {sha policy state vote facts} (x : Loaded sha policy state vote facts) :
    NativeSelectedVote.Identity x.original.policy x.original.state x.original.admitted.selected facts x.original.vote :=
  (NativeSelectedVote.originalByteAuthority x.computed).2.2.2.2.2.2.2.1

theorem iscOriginal {sha x} (isc : Isc sha x) :
    isc.original ∈ x.admitted.checked.snapshot.base.inputs ∧
    isc.original.body.id = x.admitted.selected.original.body := by
  have mem : isc.original ∈ iscMatches x := by rw [isc.selected]; simp
  have pair := List.mem_filter.mp mem
  exact ⟨pair.1,by simpa using pair.2⟩

theorem iscWholeBody {sha x} (isc : Isc sha x) :
    NativeInputSetBody.CheckedSource sha (expected x) isc.original.body.source isc.original.body :=
  ⟨rfl,isc.recomputed.1,NativeInputSetBody.bodyOriginal isc.recomputed.1,isc.recomputed.2⟩

theorem iscExactContext {sha x} (isc : Isc sha x) : isc.original.body.body.context = expected x :=
  isc.recomputed.2.2.2.1

theorem iscNoTupleErasure {sha x} (isc : Isc sha x) :
    NativeInputSetBody.readTuples (isc.original.body.body.tuples.map NativeInputSetBody.tupleValue) =
      some isc.original.body.body.tuples := NativeInputSetBody.tuplesRead _

theorem iscParentContext {sha policy state vote facts} (x : Loaded sha policy state vote facts)
    (isc : Isc sha x.original) :
    isc.original.body.id ∈ x.original.admitted.checked.snapshot.base.closed ∧
    NativeIscAdmission.iscContext sha x.original.policy.round = some x.original.admitted.selected.original.context := by
  have authority := (NativeCandidateAuthority.checked (loadedAuthority x)).2.2.2.2
  simp only [NativeCandidateAuthority.Authority,isc.kind] at authority
  exact ⟨(iscOriginal isc).2 ▸ authority.1,authority.2.2⟩

theorem configParentContext {sha policy state vote facts} (x : Loaded sha policy state vote facts)
    (config : Config x.original) :
    NativeConfigAdmission.configContext sha x.original.state.height x.original.policy.epoch =
      some x.original.admitted.selected.original.context := by
  have authority := (NativeCandidateAuthority.checked (loadedAuthority x)).2.2.2.2
  simp only [NativeCandidateAuthority.Authority,config.kind] at authority
  exact authority.2

theorem loadFromComponents {sha policy state vote facts original}
    (h : NativeSelectedVote.fromBytes sha policy state vote facts = some original) :
    load sha policy state vote facts = some ⟨original,h⟩ := by
  unfold load
  split
  · rename_i missing; rw [h] at missing; contradiction
  · rename_i found computed
    have same := Option.some.inj (h.symm.trans computed)
    subst found
    rfl

theorem iscFromComponents {sha x original} (selected : iscMatches x = [original])
    (kind : x.admitted.selected.original.action = 2)
    (computed : BodyChecked sha x original) :
    loadIsc sha x = some ⟨original,selected,kind,computed⟩ := by
  unfold loadIsc
  simp only [dif_pos kind]
  split
  · rename_i b hb
    have same : b = original := by simpa only [selected,List.cons.injEq,and_true] using hb.symm
    subst b
    simp only [dif_pos computed]
  · rename_i hother
    simp_all

theorem ambiguousIscRejects {sha x} (many : 1 < (iscMatches x).length) : loadIsc sha x = none := by
  unfold loadIsc
  split <;> try rfl
  split <;> try rfl
  rename_i b h
  rw [h] at many
  simp at many

theorem missingIscRejects {sha x} (missing : iscMatches x = []) : loadIsc sha x = none := by
  unfold loadIsc
  split
  · split
    · rename_i b h; rw [missing] at h; contradiction
    · rfl
  · rfl

theorem unsupportedIscRejects {sha x} (kind : x.admitted.selected.original.action ≠ 2) :
    loadIsc sha x = none := by simp only [loadIsc,dif_neg kind]

end DeltaReduce.NativeEarlySource
