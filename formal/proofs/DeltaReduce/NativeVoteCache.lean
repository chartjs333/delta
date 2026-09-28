import DeltaReduce.NativeArithmeticHistory

/-! Source-preserving images of every original cached vote. Ordinary native
candidates remain typed original candidates, not invented public bodies. -/
namespace DeltaReduce.NativeVoteCache
open NativeBinding
open NativeConfigReplay (Machine Stored facts)
open NativeArithmeticJournal (Input Source Arithmetic)

variable {codec : Codec} {store : Store} {trust : Trust} (adapter : HashAdapter codec)

inductive Payload where
  | ordinary (selected : NativeSelectedVote.Checked) (id : Bytes)
  | arithmetic (source : Source codec store trust adapter.sha256) (result : Arithmetic adapter source)

structure Row where
  ordinal : Nat
  entry : NativeWalBytes.Entry
  beforeState : Bytes
  payload : Payload (store := store) (trust := trust) adapter

def native (row : Row (store := store) (trust := trust) adapter) : Stored :=
  match row.payload with
  | .ordinary selected id =>
    ⟨selected.vote,NativeConfigReplay.voteReceipt .whole selected row.entry selected.vote id,
      selected.admitted.selected.original.parents⟩
  | .arithmetic _ result => NativeArithmeticJournal.stored adapter row.entry result

structure Result where
  after : Machine
  rows : List (Row (store := store) (trust := trust) adapter)

def ordinaryRow (m : Machine) (e : NativeWalBytes.Entry) (b : NativeSelectedVote.Checked) (id : Bytes) :
    Row (store := store) (trust := trust) adapter := ⟨m.votes.length+1,e,m.core.state,.ordinary b id⟩

def arithmeticRow (m : Machine) (e : NativeWalBytes.Entry)
    (s : Source codec store trust adapter.sha256) (x : Arithmetic adapter s) : Row (store := store) (trust := trust) adapter :=
  ⟨m.votes.length+1,e,m.core.state,.arithmetic s x⟩

/-- Execute the original candidate step, then retain its computed source. The
ordinary parser is the same closed whole parser, not a supplied lookup table. -/
def capture (policy : Bytes) (snap : Option NativeCommandReplay.Snapshot) (m : Machine)
    (input : Input (store := store) (trust := trust) adapter) : Option (Result (store := store) (trust := trust) adapter) := do
  let out ← NativeArithmeticJournal.step adapter policy snap m input
  match out.arithmetic with
  | some record => some ⟨out.after,[arithmeticRow (store := store) (trust := trust) adapter m input.entry record.source record.result]⟩
  | none =>
    if input.entry.kind = 1 then some ⟨out.after,[]⟩ else do
      let selected ← NativeSelectedVote.fromBytes adapter.sha256 policy m.core.state input.entry.command (facts m input.entry)
      let id ← NativeVoteBytes.voteId adapter.sha256 input.entry.command
      some ⟨out.after,[ordinaryRow (store := store) (trust := trust) adapter m input.entry selected id]⟩

def RowSource (policy : Bytes) (snap : Option NativeCommandReplay.Snapshot) (m : Machine)
    (input : Input (store := store) (trust := trust) adapter) (row : Row (store := store) (trust := trust) adapter) : Prop :=
  row.ordinal = m.votes.length+1 ∧ row.entry = input.entry ∧ row.beforeState = m.core.state ∧
  match row.payload with
  | .ordinary b id => input.source = none ∧
    NativeConfigReplay.VoteEntry .whole adapter.sha256 policy snap m input.entry b b.vote id
  | .arithmetic s x => input.source = some s ∧
    NativeArithmeticJournal.arithmetic adapter policy snap m input.entry s = some x

variable {input : Input (store := store) (trust := trust) adapter}

theorem commandCapture {policy snap m core} (source : input.source = none) (kind : input.entry.kind = 1)
    (executed : NativeCommandReplay.step adapter.sha256 (some 0) snap m.core input.entry = some core) :
    capture adapter policy snap m input = some ⟨⟨core,m.votes⟩,[]⟩ := by
  have old := NativeConfigReplay.commandFromComponents (mode := .whole) (policy := policy) kind executed
  simp only [capture,NativeArithmeticJournal.step,source,old,Option.map_some,bind,Option.bind,if_pos kind]

theorem ordinaryCapture {policy snap m b id} (source : input.source = none)
    (checks : NativeConfigReplay.VoteEntry .whole adapter.sha256 policy snap m input.entry b b.vote id) :
    capture adapter policy snap m input = some ⟨NativeConfigReplay.added .whole snap m input.entry b b.vote id,
      [ordinaryRow (store := store) (trust := trust) adapter m input.entry b id]⟩ := by
  have old := NativeConfigReplay.voteFromComponents checks
  have selected := (NativeReplayAdmission.wholeExact (NativeConfigReplay.voteOriginalSource checks).1).1
  have kind := checks.1
  have hash := checks.2.2.2.2.2.2.2.1
  simp only [capture,NativeArithmeticJournal.step,source,old,Option.map_some,bind,Option.bind,
    if_neg (by omega : input.entry.kind ≠ 1),selected,hash]

theorem arithmeticCapture {policy snap m} {s : Source codec store trust adapter.sha256} {x}
    (source : input.source = some s)
    (checks : NativeArithmeticJournal.arithmetic adapter policy snap m input.entry s = some x) :
    capture adapter policy snap m input = some ⟨NativeArithmeticJournal.added adapter snap m input.entry x,
      [arithmeticRow (store := store) (trust := trust) adapter m input.entry s x]⟩ := by
  simp only [capture,NativeArithmeticJournal.step,source,checks,bind,Option.bind]

/-- Completeness as well as soundness: every successful old candidate step has
exactly its entire cache extension here. No ordinary or arithmetic vote drops. -/
theorem stepCapture {policy snap m out}
    (step : NativeArithmeticJournal.step adapter policy snap m input = some out) :
    ∃ result, capture adapter policy snap m input = some result ∧ result.after = out.after ∧
      result.after.votes = m.votes ++ result.rows.map (native adapter) ∧
      (∀ row ∈ result.rows, RowSource adapter policy snap m input row) ∧
      result.rows.length ≤ 1 := by
  rcases NativeArithmeticJournal.stepSource adapter step with ⟨source,legacy,_⟩ | ⟨s,x,source,computed,rfl⟩
  · rcases NativeConfigReplay.stepSound legacy with ⟨kind,executed,same⟩ | ⟨b,v,id,checks,after⟩
    · refine ⟨⟨⟨out.after.core,m.votes⟩,[]⟩,commandCapture adapter source kind executed,?_,by simp,by simp,by simp⟩
      rw [← same]
    · have eq := (NativeReplayAdmission.wholeExact (NativeConfigReplay.voteOriginalSource checks).1).2
      subst v
      refine ⟨_,ordinaryCapture adapter source checks,after.symm,rfl,?_,by simp⟩
      intro row mem
      simp only [List.mem_singleton] at mem
      subst row
      exact ⟨rfl,rfl,rfl,source,checks⟩
  · refine ⟨_,arithmeticCapture adapter source computed,rfl,rfl,?_,by simp⟩
    intro row mem
    simp only [List.mem_singleton] at mem
    subst row
    exact ⟨rfl,rfl,rfl,source,computed⟩

theorem captured {policy snap m result} (h : capture adapter policy snap m input = some result) :
    ∃ out, NativeArithmeticJournal.step adapter policy snap m input = some out ∧ result.after = out.after ∧
      result.after.votes = m.votes ++ result.rows.map (native adapter) ∧
      (∀ row ∈ result.rows, RowSource adapter policy snap m input row) ∧ result.rows.length ≤ 1 := by
  have raw := h
  unfold capture at raw
  simp only [bind,Option.bind_eq_some_iff] at raw
  obtain ⟨out,step,_⟩ := raw
  obtain ⟨actual,ha,eq,cache,source,len⟩ := stepCapture adapter step
  rw [h] at ha
  cases Option.some.inj ha
  exact ⟨out,step,eq,cache,source,len⟩

theorem rowOriginal {policy snap m} {row : Row (store := store) (trust := trust) adapter}
    (h : RowSource adapter policy snap m input row) :
    (native adapter row).vote.sequence = input.entry.sequence ∧
    (native adapter row).receipt.sequence = input.entry.sequence ∧
    NativeVoteBytes.encodeFrame (native adapter row).vote.wire = input.entry.command := by
  obtain ⟨_,entry,_,source⟩ := h
  cases hp : row.payload with
  | ordinary b id =>
    simp only [hp] at source
    simp only [native,hp]
    have original := NativeConfigReplay.voteOriginalSource source.2
    exact ⟨NativeReplayAdmission.originalSequence original.1,entry ▸ rfl,original.2.1⟩
  | arithmetic s x =>
    simp only [hp] at source
    simp only [native,hp]
    have original := NativeArithmeticJournal.originalVote adapter (NativeArithmeticJournal.checked adapter source.2)
    exact ⟨original.2.1,entry ▸ rfl,original.1⟩

theorem ordinaryOriginalAuthority {policy snap m} {row : Row (store := store) (trust := trust) adapter}
    (h : RowSource adapter policy snap m input row) {b id} (p : row.payload = .ordinary b id) :
    NativeSelectedVote.Source adapter.sha256 policy row.beforeState row.entry.command (facts m row.entry) b ∧
    (native adapter row).parents = b.admitted.selected.original.parents ∧
    b.admitted.checked.entries.map NativeCandidateAuthority.Entry.original = b.policy.candidates := by
  obtain ⟨_,entry,state,source⟩ := h
  rw [p] at source
  have original := (NativeReplayAdmission.wholeExact (NativeConfigReplay.voteOriginalSource source.2).1).1
  exact ⟨by simpa only [entry,state] using NativeSelectedVote.fromBytesSource original,
    by simp only [native,p],(NativeSelectedVote.originalByteAuthority original).2.2.1⟩

theorem arithmeticOriginalSource {policy snap m} {row : Row (store := store) (trust := trust) adapter}
    (h : RowSource adapter policy snap m input row) {s x} (p : row.payload = .arithmetic s x) :
    NativeVectorContext.bind adapter.sha256 policy row.beforeState s.apc s.config s.proof s.profile
      s.permission s.inputs = some s.bound ∧
    x.image.original = (native adapter row).vote ∧ x.image.metadata.recovered = false := by
  obtain ⟨_,_,state,source⟩ := h
  rw [p] at source
  have checked := NativeArithmeticJournal.checked adapter source.2
  have original := NativeArithmeticJournal.originalVote adapter checked
  exact ⟨by simpa only [state] using NativeArithmeticJournal.actualPreparation adapter checked,
    by simpa only [native,p,NativeArithmeticJournal.stored] using original.2.2.1,original.2.2.2⟩

/-- A strict lookup never turns the first of several matching original keys
into authority. This can be applied only with a separately proved cache origin. -/
def lookup (key : Bytes × Bytes × Bytes) (rows : List (Row (store := store) (trust := trust) adapter)) : Option (Row (store := store) (trust := trust) adapter) :=
  match rows.filter (fun row => NativeConfigReplay.key (native adapter row).vote == key) with
  | [row] => some row
  | _ => none

theorem lookupExact {key rows} {row : Row (store := store) (trust := trust) adapter}
    (h : lookup adapter key rows = some row) :
    rows.filter (fun r => NativeConfigReplay.key (native adapter r).vote == key) = [row] ∧
    row ∈ rows ∧ NativeConfigReplay.key (native adapter row).vote = key := by
  unfold lookup at h
  split at h <;> try contradiction
  rename_i found eq
  cases Option.some.inj h
  have mem : row ∈ rows.filter (fun r => NativeConfigReplay.key (native adapter r).vote == key) := by rw [eq]; simp
  have src := List.mem_filter.mp mem
  exact ⟨eq,src.1,by simpa using src.2⟩

theorem ambiguousLookup {key rows}
    (many : 1 < (rows.filter (fun r => NativeConfigReplay.key (native adapter r).vote == key)).length) :
    lookup (store := store) (trust := trust) adapter key rows = none := by
  cases h : lookup adapter key rows with
  | none => rfl
  | some row => rw [(lookupExact adapter h).1] at many; simp at many

end DeltaReduce.NativeVoteCache
