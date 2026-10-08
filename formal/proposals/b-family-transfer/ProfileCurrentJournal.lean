import ProfileCurrent

/-! T047/T053. The complete original pointer journal is the source of the row
inventory, not a caller-selected list of successful rows. Profile v1's cold
handover requires a complete journal: an unterminated tail cannot be removed.
This joins original bytes to the static current relation; it does not establish
initial authority, fsync/custody, a producing prefix or production recovery. -/
namespace DeltaReduce.ProfileSource.CurrentJournal
open NativeReceiptBytes (Bytes)
open NativeCurrentPointer (State)

def align : List Bytes → List Current.Input → Option (List (Bytes × Current.Input))
  | [[]],[] => some []
  | line::next::rest,input::inputs => do
      let tail ← align (next::rest) inputs
      some ((line,input)::tail)
  | _,_ => none

theorem aligned {lines inputs pairs} (ok : align lines inputs = some pairs) :
    pairs.map Prod.fst ++ [[]] = lines ∧ pairs.map Prod.snd = inputs := by
  induction inputs generalizing lines pairs with
  | nil =>
    cases lines with
    | nil => simp [align] at ok
    | cons line rest =>
      cases line <;> cases rest <;> simp [align] at ok
      cases ok
      exact ⟨rfl,rfl⟩
  | cons input inputs ih =>
    cases lines with
    | nil => simp [align] at ok
    | cons line rest =>
      cases rest with
      | nil => cases line <;> simp [align] at ok
      | cons next rest =>
        simp only [align] at ok
        obtain ⟨tail,ht,last⟩ := Option.bind_eq_some_iff.mp ok
        cases Option.some.inj last
        have h := ih ht
        exact ⟨by simp only [List.map_cons,List.cons_append,h.1],
          by simp only [List.map_cons,h.2]⟩

theorem alignComplete (pairs : List (Bytes × Current.Input)) :
    align (pairs.map Prod.fst ++ [[]]) (pairs.map Prod.snd) = some pairs := by
  induction pairs with
  | nil => rfl
  | cons pair rest ih =>
    rcases pair with ⟨line,input⟩
    cases rest with
    | nil => cases line <;> rfl
    | cons next rest =>
      simp only [List.map_cons,List.cons_append] at ih ⊢
      simp only [align,Bind.bind,Option.bind,ih]

theorem exactPointerScan {sha enrolled actor before pairs chain}
    (history : Current.History sha enrolled actor before pairs chain) :
    NativePointerWal.replay sha before (pairs.map Prod.fst ++ [[]]) =
      some ⟨chain.current,chain.rows.map Current.Row.record,[]⟩ := by
  induction history with
  | nil => rfl
  | @cons s line input row rest tail one later ih =>
    have h := Current.boundSource one
    have expand : NativePointerWal.replay sha s (line::(rest.map Prod.fst ++ [[]])) =
        (do
          let r ← NativePointerWal.readLine sha line
          let n ← NativePointerWal.step s r
          let out ← NativePointerWal.replay sha n (rest.map Prod.fst ++ [[]])
          some ⟨out.state,r::out.records,out.tail⟩) := by cases rest <;> rfl
    simp only [List.map_cons,List.cons_append]
    rw [expand,h.parsed]
    dsimp only [Bind.bind,Option.bind]
    rw [h.step]
    dsimp only [Bind.bind,Option.bind]
    rw [ih]

structure Bound where
  original : Bytes
  inputs : List Current.Input
  pairs : List (Bytes × Current.Input)
  chain : Current.Chain

def bind (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment) (actor : Bytes)
    (initial : State) (observation : NativePointerWal.Observation)
    (inputs : List Current.Input) : Option Bound := do
  match observation with
  | .unknown => none
  | .bytes original =>
    if NativeCurrentPointer.StateValid initial then
      let pairs ← align (NativePointerWal.split 10 original) inputs
      let chain ← Current.run sha enrolled actor initial pairs
      some ⟨original,inputs,pairs,chain⟩
    else none

theorem boundSource {sha enrolled actor initial original inputs out}
    (ok : bind sha enrolled actor initial (.bytes original) inputs = some out) :
    NativeCurrentPointer.StateValid initial ∧ out.original = original ∧
    out.inputs = inputs ∧ align (NativePointerWal.split 10 original) inputs = some out.pairs ∧
    Current.run sha enrolled actor initial out.pairs = some out.chain := by
  simp only [bind] at ok
  split at ok <;> try contradiction
  rename_i valid
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨pairs,hp,chain,hc,last⟩ := ok
  cases Option.some.inj last
  exact ⟨valid,rfl,rfl,hp,hc⟩

theorem fullOriginalInventory {sha enrolled actor initial original inputs out}
    (ok : bind sha enrolled actor initial (.bytes original) inputs = some out) :
    out.chain.rows.map Current.Row.originalLine ++ [[]] = NativePointerWal.split 10 original ∧
    out.chain.rows.map Current.Row.input = inputs := by
  have h := boundSource ok
  have inv := aligned h.2.2.2.1
  have rows := Current.everyOriginal h.2.2.2.2
  have first := congrArg (List.map Prod.fst) rows
  have second := congrArg (List.map Prod.snd) rows
  simp only [List.map_map] at first second
  change out.chain.rows.map Current.Row.originalLine = out.pairs.map Prod.fst at first
  change out.chain.rows.map Current.Row.input = out.pairs.map Prod.snd at second
  exact ⟨by rw [first]; exact inv.1,second.trans inv.2⟩

theorem bindComplete {sha enrolled actor initial original pairs chain}
    (valid : NativeCurrentPointer.StateValid initial)
    (inventory : pairs.map Prod.fst ++ [[]] = NativePointerWal.split 10 original)
    (history : Current.History sha enrolled actor initial pairs chain) :
    bind sha enrolled actor initial (.bytes original) (pairs.map Prod.snd) =
      some ⟨original,pairs.map Prod.snd,pairs,chain⟩ := by
  simp only [bind,if_pos valid]
  rw [← inventory,alignComplete]
  dsimp only [Bind.bind,Option.bind]
  rw [Current.historyComplete history]

theorem nativeScanAgrees {sha enrolled actor initial original inputs out}
    (ok : bind sha enrolled actor initial (.bytes original) inputs = some out) :
    NativePointerWal.recover sha initial (.bytes original) =
      some ⟨out.chain.current,out.chain.rows.map Current.Row.record,[]⟩ := by
  have h := boundSource ok
  have scan := exactPointerScan (Current.runSound h.2.2.2.2)
  rw [(aligned h.2.2.2.1).1] at scan
  exact (if_pos h.1).trans scan

theorem noRecordOrInputErasure {sha enrolled actor initial original inputs out}
    (ok : bind sha enrolled actor initial (.bytes original) inputs = some out) :
    out.chain.rows.length = inputs.length ∧
    out.chain.rows.length+1 = (NativePointerWal.split 10 original).length := by
  have h := fullOriginalInventory ok
  have first := congrArg List.length h.1
  have second := congrArg List.length h.2
  simp only [List.length_append,List.length_map,List.length_cons,List.length_nil] at first second
  exact ⟨second,first⟩

theorem unknownRejected (sha enrolled actor initial inputs) :
    bind sha enrolled actor initial .unknown inputs = none := rfl

theorem incompleteRejected {sha enrolled actor initial original inputs recovered}
    (observed : NativePointerWal.recover sha initial (.bytes original) = some recovered)
    (incomplete : recovered.tail ≠ []) :
    bind sha enrolled actor initial (.bytes original) inputs = none := by
  cases result : bind sha enrolled actor initial (.bytes original) inputs with
  | none => rfl
  | some out =>
    have same := Option.some.inj (observed.symm.trans (nativeScanAgrees result))
    exact False.elim (incomplete (congrArg NativePointerWal.Recovered.tail same))

end DeltaReduce.ProfileSource.CurrentJournal
