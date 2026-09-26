import DeltaReduce.NativeSeedTranscript
import DeltaReduce.NativeFinalizedIscSection

/-! Whole original seed vector with computed finalized ISC parent witnesses.
This checks these two sections only, not the later graph or complete admission. -/
namespace DeltaReduce.NativeSeedSection
open NativeReceiptBytes NativePolicyCodec NativePolicySchema
open NativePolicyBytes (Policy)
open NativeStateBytes (State)
open NativeSeedTranscript (Checked)

structure Bound where
  isc : NativeFinalizedIscSection.Bound
  trees : List Value
  seeds : List Checked

def Ordered (seeds : List Checked) : Prop :=
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (seeds.map Checked.id) = true
instance (seeds) : Decidable (Ordered seeds) := by unfold Ordered; infer_instance

def bindSection (sha : Bytes → Bytes) (p : Policy) (s : State) : Option Bound := do
  let isc ← NativeFinalizedIscSection.bindSection sha p s
  let trees ← lookup fmtSnapshot p.snapshot "seed_transcripts" >>= NativePolicyBytes.items
  let seeds ← NativeSeedTranscript.checkAll sha
    (NativeIscAdmission.expected p s isc.schema isc.arithmetic) isc.finalized trees
  if Ordered seeds then some ⟨isc,trees,seeds⟩ else none

def Source (sha : Bytes → Bytes) (p : Policy) (s : State) (b : Bound) : Prop :=
  NativeFinalizedIscSection.bindSection sha p s = some b.isc ∧
  (lookup fmtSnapshot p.snapshot "seed_transcripts" >>= NativePolicyBytes.items) = some b.trees ∧
  NativeSeedTranscript.checkAll sha (NativeIscAdmission.expected p s b.isc.schema b.isc.arithmetic)
    b.isc.finalized b.trees = some b.seeds ∧ Ordered b.seeds

theorem checkedSource {sha p s b} (h : bindSection sha p s = some b) : Source sha p s b := by
  unfold bindSection at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨isc,hi,trees,ht,seeds,hs,last⟩ := h
  split at last <;> try contradiction
  rename_i ordered
  cases Option.some.inj last
  exact ⟨hi,by simpa only [bind,Option.bind_eq_some_iff] using ht,hs,ordered⟩

theorem fromComponents {sha p s b} (h : Source sha p s b) : bindSection sha p s = some b := by
  rcases h with ⟨isc,trees,seeds,ordered⟩
  unfold bindSection
  rw [isc,trees]
  dsimp only [bind,Option.bind]
  rw [seeds]
  exact if_pos ordered

theorem originalSeedList {sha p s b} (h : bindSection sha p s = some b) :
    b.seeds.map Checked.source = b.trees := NativeSeedTranscript.allSources (checkedSource h).2.2.1

theorem seedCount {sha p s b} (h : bindSection sha p s = some b) :
    b.seeds.length = b.trees.length := by
  have eq := congrArg List.length (originalSeedList h); simpa using eq

theorem seedSource {sha p s b seed} (h : bindSection sha p s = some b) (mem : seed ∈ b.seeds) :
    NativeSeedTranscript.Source sha (NativeIscAdmission.expected p s b.isc.schema b.isc.arithmetic)
      b.isc.finalized seed.source seed :=
  NativeSeedTranscript.allChecked (checkedSource h).2.2.1 seed mem

theorem finalizedParent {sha p s b seed} (h : bindSection sha p s = some b) (mem : seed ∈ b.seeds) :
    seed.transcript.isc ∈ b.isc.finalized ∧
    ∃ c ∈ b.isc.certificates, c.qcId = seed.transcript.isc ∧
      NativeIscCertificate.Source sha (NativeIscAdmission.expected p s b.isc.schema b.isc.arithmetic)
        p.validators c.source c := by
  have parent := (seedSource h mem).2.2.2.2.1
  exact ⟨parent,NativeFinalizedIscSection.finalizedCertificate (checkedSource h).1 parent⟩

theorem noUnfinalizedParent {sha p s b seed} (h : bindSection sha p s = some b)
    (absent : seed.transcript.isc ∉ b.isc.finalized) : seed ∉ b.seeds := by
  intro mem
  exact absent (finalizedParent h mem).1

def prepare (sha : Bytes → Bytes) (policyRaw stateRaw : Bytes) : Option Bound := do
  let (_,p) ← NativePolicyBytes.decodePolicy policyRaw
  let s ← NativeStateBytes.decodeState stateRaw
  bindSection sha p s

theorem preparedSource {sha policyRaw stateRaw b} (h : prepare sha policyRaw stateRaw = some b) :
    ∃ tree p s, NativePolicyBytes.decodePolicy policyRaw = some (tree,p) ∧
    NativeStateBytes.decodeState stateRaw = some s ∧ Source sha p s b := by
  unfold prepare at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨⟨tree,p⟩,hp,s,hs,hb⟩ := h
  exact ⟨tree,p,s,hp,hs,checkedSource hb⟩

end DeltaReduce.NativeSeedSection
