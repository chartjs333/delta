import SourceVote

/-! T047/T053. The original own VoteJournal key is validator/epoch/context.
For one independently selected actor/epoch, context alone indexes the cache.
The scan retains every physical entry and every original kind-2 intent; retry
does not allocate another slot. It does not establish candidate admission,
durability, signatures or legality of the other two WAL kinds. -/
namespace DeltaReduce.ProfileSource.Journal
open NativeReceiptBytes (Bytes)
open NativeWalBytes (Entry)

structure Intent where
  entry : Entry
  vote : Vote.Vote
  ordinal : Nat
  deriving DecidableEq, Repr

def scan (semantics epoch actor : Bytes) : List Bytes → Nat → List Entry → Option (List Intent)
  | _,_,[] => some []
  | seen,before,e::tail => do
      if e.kind = 2 then
        let v ← Vote.bindOwn semantics epoch actor e
        if v.wire.context ∉ seen then
          let rest ← scan semantics epoch actor (v.wire.context::seen) (before+1) tail
          some (⟨e,v,before+1⟩::rest)
        else none
      else if e.kind = 1 ∨ e.kind = 3 then scan semantics epoch actor seen before tail
      else none

inductive Source (semantics epoch actor : Bytes) :
    List Bytes → Nat → List Entry → List Intent → Prop where
  | nil (seen before) : Source semantics epoch actor seen before [] []
  | vote {seen before e tail v rest}
      (original : Vote.bindOwn semantics epoch actor e = some v)
      (fresh : v.wire.context ∉ seen)
      (next : Source semantics epoch actor (v.wire.context::seen) (before+1) tail rest) :
      Source semantics epoch actor seen before (e::tail) (⟨e,v,before+1⟩::rest)
  | other {seen before e tail rest} (kind : e.kind = 1 ∨ e.kind = 3)
      (next : Source semantics epoch actor seen before tail rest) :
      Source semantics epoch actor seen before (e::tail) rest

theorem sound {semantics epoch actor seen before entries intents}
    (ok : scan semantics epoch actor seen before entries = some intents) :
    Source semantics epoch actor seen before entries intents := by
  induction entries generalizing seen before intents with
  | nil =>
    have same : intents = [] := by simpa [scan] using ok.symm
    subst intents
    exact Source.nil seen before
  | cons e tail ih =>
    simp only [scan] at ok
    split at ok
    · simp only [bind,Option.bind_eq_some_iff] at ok
      obtain ⟨v,hv,ok⟩ := ok
      split at ok <;> try contradiction
      rename_i fresh
      obtain ⟨rest,hr,last⟩ := Option.bind_eq_some_iff.mp ok
      cases Option.some.inj last
      exact .vote hv fresh (ih hr)
    · split at ok <;> try contradiction
      exact .other (by assumption) (ih ok)

theorem complete {semantics epoch actor seen before entries intents}
    (source : Source semantics epoch actor seen before entries intents) :
    scan semantics epoch actor seen before entries = some intents := by
  induction source with
  | nil => rfl
  | vote original fresh next ih =>
    have kind := (Vote.ownSource original).2.2.1
    simp only [scan,if_pos kind,original,bind,Option.bind,if_pos fresh,ih]
  | @other seen before e tail rest kind next ih =>
    have different : e.kind ≠ 2 := by rcases kind with h | h <;> omega
    simp only [scan,if_neg different,if_pos kind,ih]

theorem originalEntries {semantics epoch actor seen before entries intents}
    (source : Source semantics epoch actor seen before entries intents) :
    intents.map Intent.entry = entries.filter (fun e => e.kind == 2) := by
  induction source with
  | nil => rfl
  | vote original fresh next ih =>
    have kind := (Vote.ownSource original).2.2.1
    simp [kind,ih]
  | other kind next ih =>
    rcases kind with h | h <;> simp [h,ih]

theorem everyOriginal {semantics epoch actor seen before entries intents}
    (source : Source semantics epoch actor seen before entries intents) :
    ∀ row ∈ intents, Vote.bindOwn semantics epoch actor row.entry = some row.vote ∧
      row.vote.wire.context ∉ seen := by
  induction source with
  | nil => simp
  | vote original fresh next ih =>
    intro row mem
    rcases List.mem_cons.mp mem with rfl | rest
    · exact ⟨original,fresh⟩
    · have h := ih row rest
      exact ⟨h.1,fun mem => h.2 (List.mem_cons_of_mem _ mem)⟩
  | other kind next ih => exact ih

theorem uniqueKeys {semantics epoch actor seen before entries intents}
    (source : Source semantics epoch actor seen before entries intents) :
    (intents.map (fun row => row.vote.wire.context)).Nodup := by
  induction source with
  | nil => simp
  | vote original fresh next ih =>
    simp only [List.map_cons,List.nodup_cons]
    refine ⟨?_,ih⟩
    intro member
    obtain ⟨row,mem,same⟩ := List.mem_map.mp member
    have absent := (everyOriginal next row mem).2
    exact absent (by simp [same])
  | other kind next ih => exact ih

theorem exactOriginalVote {semantics epoch actor seen before entries intents row}
    (ok : scan semantics epoch actor seen before entries = some intents) (mem : row ∈ intents) :
    row.entry ∈ entries ∧ Vote.encodeFrame row.vote.wire = row.entry.command ∧
      row.vote.sequence = row.entry.sequence ∧
      row.vote.wire.validator = actor ∧ row.vote.wire.epoch = epoch := by
  have source := sound ok
  have bound := (everyOriginal source row mem).1
  have own := Vote.ownSource bound
  have present : row.entry ∈ intents.map Intent.entry := List.mem_map.mpr ⟨row,mem,rfl⟩
  rw [originalEntries source] at present
  exact ⟨(List.mem_filter.mp present).1,own.2.1,Vote.physicalSlotRetained bound,
    own.2.2.2.2.2.2.2.1,own.2.2.2.2.2.2.1⟩

theorem equalOfKey {intents : List Intent} {a b : Intent}
    (unique : (intents.map (fun row => row.vote.wire.context)).Nodup)
    (left : a ∈ intents) (right : b ∈ intents)
    (context : a.vote.wire.context = b.vote.wire.context) : a = b := by
  induction intents with
  | nil => simp at left
  | cons head tail ih =>
    obtain ⟨fresh,unique⟩ := List.nodup_cons.mp unique
    rcases List.mem_cons.mp left with rfl | ha
    · rcases List.mem_cons.mp right with rfl | hb
      · rfl
      · exact False.elim (fresh (List.mem_map.mpr ⟨b,hb,context.symm⟩))
    · rcases List.mem_cons.mp right with rfl | hb
      · exact False.elim (fresh (List.mem_map.mpr ⟨a,ha,context⟩))
      · exact ih unique ha hb

theorem noSameContextSlots {semantics epoch actor seen before entries intents a b}
    (ok : scan semantics epoch actor seen before entries = some intents)
    (left : a ∈ intents) (right : b ∈ intents)
    (context : a.vote.wire.context = b.vote.wire.context) : a = b :=
  equalOfKey (uniqueKeys (sound ok)) left right context

theorem count {semantics epoch actor seen before entries intents}
    (ok : scan semantics epoch actor seen before entries = some intents) :
    intents.length = (entries.filter (fun e => e.kind == 2)).length := by
  simpa using congrArg List.length (originalEntries (sound ok))

theorem ordinalAt {semantics epoch actor seen before entries intents n row}
    (source : Source semantics epoch actor seen before entries intents)
    (found : intents[n]? = some row) : row.ordinal = before+n+1 := by
  induction source generalizing n with
  | nil => simp at found
  | vote original fresh next ih =>
    cases n with
    | zero => cases Option.some.inj found; rfl
    | succ n => have h := ih found; omega
  | other kind next ih => exact ih found

structure Bound where
  originals : List Entry
  intents : List Intent

def check (semantics epoch actor : Bytes) (entries : List Entry) : Option Bound := do
  let intents ← scan semantics epoch actor [] 0 entries
  some ⟨entries,intents⟩

theorem checked {semantics epoch actor entries out}
    (ok : check semantics epoch actor entries = some out) :
    out.originals = entries ∧ Source semantics epoch actor [] 0 entries out.intents := by
  simp only [check,bind,Option.bind_eq_some_iff] at ok
  obtain ⟨rows,hr,last⟩ := ok
  cases Option.some.inj last
  exact ⟨rfl,sound hr⟩

end DeltaReduce.ProfileSource.Journal
