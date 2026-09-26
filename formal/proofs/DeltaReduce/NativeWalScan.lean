import DeltaReduce.NativeWalBytes

/-! Complete observed-byte scan. A torn suffix is retained, never converted into
authenticated absence, successful truncation, native admission or readiness. -/
namespace DeltaReduce.NativeWalScan
open NativeReceiptBytes NativeWalBytes

structure Piece where
  entry : Entry
  bytes : Bytes
  deriving DecidableEq, Repr

structure Result where
  pieces : List Piece
  tail : Bytes
  torn : Bool
  deriving DecidableEq, Repr

def joined : List Piece → Bytes
  | [] => []
  | p::rest => p.bytes ++ joined rest

def entries (r : Result) : List Entry := r.pieces.map Piece.entry
def consumed (r : Result) : Nat := (joined r.pieces).length

def run (sha : Bytes → Bytes) : Nat → Bytes → Option Result
  | 0, _ => none
  | fuel+1, raw => match scanHead sha raw with
    | .done => some ⟨[],[],false⟩
    | .torn => some ⟨[],raw,true⟩
    | .corrupt => none
    | .frame e size rest => do
      let r ← run sha fuel rest
      some ⟨⟨e,raw.take size⟩::r.pieces,r.tail,r.torn⟩

def scan (sha : Bytes → Bytes) (raw : Bytes) : Option Result := run sha (raw.length+1) raw

inductive Trace (sha : Bytes → Bytes) : Bytes → Result → Prop where
  | done : Trace sha [] ⟨[],[],false⟩
  | torn (raw : Bytes) (head : scanHead sha raw = .torn) : Trace sha raw ⟨[],raw,true⟩
  | step (raw rest : Bytes) (e : Entry) (size : Nat) (r : Result)
      (head : scanHead sha raw = .frame e size rest) (tail : Trace sha rest r) :
      Trace sha raw ⟨⟨e,raw.take size⟩::r.pieces,r.tail,r.torn⟩

theorem doneIsEmpty (sha : Bytes → Bytes) (raw : Bytes)
    (h : scanHead sha raw = .done) : raw = [] := by
  unfold scanHead at h
  split at h
  · assumption
  · split at h
    · contradiction
    · cases a : consume NativeWalBytes.header raw with
      | none => simp [a] at h
      | some rest =>
        simp only [a] at h
        cases b : readNat 4 rest with
        | none => simp [b] at h
        | some pair =>
          obtain ⟨size,tail⟩ := pair
          simp only [b] at h
          split at h
          · split at h
            · contradiction
            · cases d : decode sha (raw.take size) <;> simp [d] at h
          · contradiction

theorem frameDecreases (sha : Bytes → Bytes) (raw rest : Bytes) (e : Entry) (size : Nat)
    (h : scanHead sha raw = .frame e size rest) : rest.length < raw.length := by
  have f := scannedFrameSound sha raw rest e size h
  have lengths := congrArg List.length f.2.2.2.2
  simp only [List.length_append, List.length_take, Nat.min_eq_left f.2.2.1] at lengths
  omega

theorem runTrace (sha : Bytes → Bytes) (fuel : Nat) (raw : Bytes) (r : Result)
    (ok : run sha fuel raw = some r) : Trace sha raw r := by
  induction fuel generalizing raw r with
  | zero => simp [run] at ok
  | succ fuel ih =>
    unfold run at ok
    cases h : scanHead sha raw with
    | done =>
      have empty := doneIsEmpty sha raw h
      simp only [h] at ok
      cases Option.some.inj ok
      subst raw
      exact Trace.done
    | torn =>
      simp only [h] at ok
      cases Option.some.inj ok
      exact Trace.torn raw h
    | corrupt => simp [h] at ok
    | frame e size rest =>
      simp only [h, bind, Option.bind] at ok
      cases tail : run sha fuel rest with
      | none => simp [tail] at ok
      | some next =>
        simp only [tail] at ok
        cases Option.some.inj ok
        exact Trace.step raw rest e size next h (ih rest next tail)

theorem traceRun (sha : Bytes → Bytes) (raw : Bytes) (r : Result)
    (trace : Trace sha raw r) (fuel : Nat) (enough : raw.length < fuel) :
    run sha fuel raw = some r := by
  induction trace generalizing fuel with
  | done =>
    cases fuel with
    | zero => simp at enough
    | succ fuel => simp [run, scanHead]
  | torn raw head =>
    cases fuel with
    | zero => omega
    | succ fuel => simp [run, head]
  | step raw rest e size r head tail ih =>
    cases fuel with
    | zero => omega
    | succ fuel =>
      have decrease := frameDecreases sha raw rest e size head
      have bound : rest.length < fuel := by omega
      simp only [run, head, ih fuel bound, bind, Option.bind]

theorem scanExact (sha : Bytes → Bytes) (raw : Bytes) (r : Result) :
    scan sha raw = some r ↔ Trace sha raw r := by
  constructor
  · exact runTrace sha (raw.length+1) raw r
  · intro h; exact traceRun sha raw r h (raw.length+1) (by omega)

theorem tracePartition (sha : Bytes → Bytes) (raw : Bytes) (r : Result)
    (trace : Trace sha raw r) : raw = joined r.pieces ++ r.tail := by
  induction trace with
  | done => rfl
  | torn raw head => rfl
  | step raw rest e size r head tail ih =>
    have f := scannedFrameSound sha raw rest e size head
    change raw = (raw.take size ++ joined r.pieces) ++ r.tail
    rw [List.append_assoc, ← ih]
    exact f.2.2.2.2

theorem tracePieces (sha : Bytes → Bytes) (raw : Bytes) (r : Result)
    (trace : Trace sha raw r) : ∀ p ∈ r.pieces,
    decode sha p.bytes = some p.entry ∧ 72 ≤ p.bytes.length ∧ p.bytes.length ≤ 64*1024*1024 := by
  induction trace with
  | done => simp
  | torn raw head => simp
  | step raw rest e size r head tail ih =>
    intro p member
    simp only [List.mem_cons] at member
    rcases member with same | old
    · subst p
      have f := scannedFrameSound sha raw rest e size head
      have len : (raw.take size).length = size := by simp [List.length_take, f.2.2.1]
      exact ⟨f.2.2.2.1, by simpa only [len] using f.1, by simpa only [len] using f.2.1⟩
    · exact ih p old

theorem traceTerminal (sha : Bytes → Bytes) (raw : Bytes) (r : Result)
    (trace : Trace sha raw r) :
    if r.torn then scanHead sha r.tail = .torn else r.tail = [] := by
  induction trace with
  | done => rfl
  | torn raw head => exact head
  | step raw rest e size r head tail ih => exact ih

theorem scannedPrefix (sha : Bytes → Bytes) (raw : Bytes) (r : Result)
    (ok : scan sha raw = some r) : raw.take (consumed r) = joined r.pieces := by
  have h := tracePartition sha raw r ((scanExact sha raw r).mp ok)
  rw [h]; simp [consumed]

theorem scannedTail (sha : Bytes → Bytes) (raw : Bytes) (r : Result)
    (ok : scan sha raw = some r) : raw.drop (consumed r) = r.tail := by
  have h := tracePartition sha raw r ((scanExact sha raw r).mp ok)
  rw [h]; simp [consumed]

theorem scannedCanonical (sha : Bytes → Bytes) (raw : Bytes) (r : Result)
    (ok : scan sha raw = some r) : ∀ p ∈ r.pieces,
    Valid p.entry ∧ encode sha p.entry = p.bytes := by
  intro p member
  have h := (tracePieces sha raw r ((scanExact sha raw r).mp ok) p member).1
  exact ⟨(decodedSound sha p.bytes p.entry h).1, decodedCanonical sha p.bytes p.entry h⟩

theorem traceUnique (sha : Bytes → Bytes) (raw : Bytes) (a b : Result)
    (ha : Trace sha raw a) (hb : Trace sha raw b) : a = b := by
  have ea := (scanExact sha raw a).mpr ha
  have eb := (scanExact sha raw b).mpr hb
  rw [ea] at eb
  exact Option.some.inj eb

def check (sha : Bytes → Bytes) (raw : Bytes) : Option Result := do
  let r ← scan sha raw
  if orderedFrom 1 (entries r) then some r else none

theorem checkedSound (sha : Bytes → Bytes) (raw : Bytes) (r : Result)
    (ok : check sha raw = some r) : scan sha raw = some r ∧ orderedFrom 1 (entries r) = true := by
  unfold check at ok
  cases h : scan sha raw with
  | none => simp [h] at ok
  | some value =>
    simp only [h, bind, Option.bind] at ok
    split at ok
    · cases Option.some.inj ok; exact ⟨rfl,‹_›⟩
    · contradiction

theorem checkedPosition (sha : Bytes → Bytes) (raw : Bytes) (r : Result)
    (ok : check sha raw = some r) (i : Nat) (e : Entry) (atIndex : (entries r)[i]? = some e) :
    e.sequence = 1+i := orderedPosition 1 (entries r) i e (checkedSound sha raw r ok).2 atIndex

theorem checkedFromScan (sha : Bytes → Bytes) (raw : Bytes) (r : Result)
    (ok : scan sha raw = some r) (order : orderedFrom 1 (entries r) = true) :
    check sha raw = some r := by simp [check, ok, order]

theorem checkedPartition (sha : Bytes → Bytes) (raw : Bytes) (r : Result)
    (ok : check sha raw = some r) : raw = joined r.pieces ++ r.tail :=
  tracePartition sha raw r ((scanExact sha raw r).mp (checkedSound sha raw r ok).1)

theorem checkedTerminal (sha : Bytes → Bytes) (raw : Bytes) (r : Result)
    (ok : check sha raw = some r) :
    if r.torn then scanHead sha r.tail = .torn else r.tail = [] :=
  traceTerminal sha raw r ((scanExact sha raw r).mp (checkedSound sha raw r ok).1)

theorem corruptFirstRejected (sha : Bytes → Bytes) (raw : Bytes)
    (bad : scanHead sha raw = .corrupt) : scan sha raw = none := by simp [scan, run, bad]

theorem corruptionPropagates (sha : Bytes → Bytes) (fuel : Nat) (raw rest : Bytes)
    (e : Entry) (size : Nat) (head : scanHead sha raw = .frame e size rest)
    (bad : run sha fuel rest = none) : run sha (fuel+1) raw = none := by simp [run, head, bad]

theorem fuelStable (sha : Bytes → Bytes) (fuel other : Nat) (raw : Bytes)
    (a : raw.length < fuel) (b : raw.length < other) :
    run sha fuel raw = run sha other raw := by
  induction fuel generalizing raw other with
  | zero => omega
  | succ fuel ih =>
    cases other with
    | zero => omega
    | succ other =>
      simp only [run]
      cases h : scanHead sha raw with
      | done => rfl
      | torn => rfl
      | corrupt => rfl
      | frame e size rest =>
        have decrease := frameDecreases sha raw rest e size h
        dsimp only
        rw [ih other rest (by omega) (by omega)]

inductive CorruptTrace (sha : Bytes → Bytes) : Bytes → Prop where
  | bad (raw : Bytes) (head : scanHead sha raw = .corrupt) : CorruptTrace sha raw
  | step (raw rest : Bytes) (e : Entry) (size : Nat)
      (head : scanHead sha raw = .frame e size rest) (tail : CorruptTrace sha rest) :
      CorruptTrace sha raw

theorem runFailureIsCorrupt (sha : Bytes → Bytes) (fuel : Nat) (raw : Bytes)
    (enough : raw.length < fuel) (failed : run sha fuel raw = none) : CorruptTrace sha raw := by
  induction fuel generalizing raw with
  | zero => omega
  | succ fuel ih =>
    unfold run at failed
    cases h : scanHead sha raw with
    | done => simp [h] at failed
    | torn => simp [h] at failed
    | corrupt => exact CorruptTrace.bad raw h
    | frame e size rest =>
      have decrease := frameDecreases sha raw rest e size h
      simp only [h, bind, Option.bind] at failed
      cases tail : run sha fuel rest with
      | none => exact CorruptTrace.step raw rest e size h (ih rest (by omega) tail)
      | some r => simp [tail] at failed

theorem scanFailureIsCorrupt (sha : Bytes → Bytes) (raw : Bytes)
    (failed : scan sha raw = none) : CorruptTrace sha raw :=
  runFailureIsCorrupt sha (raw.length+1) raw (by omega) failed

theorem checkedSequenceUnique (sha : Bytes → Bytes) (raw : Bytes) (r : Result)
    (ok : check sha raw = some r) (i j : Nat) (a b : Entry)
    (ai : (entries r)[i]? = some a) (bj : (entries r)[j]? = some b)
    (same : a.sequence = b.sequence) : i = j := by
  have first := checkedPosition sha raw r ok i a ai
  have second := checkedPosition sha raw r ok j b bj
  omega

theorem checkedReceiptOrigin (sha : Bytes → Bytes) (policy raw receiptBytes : Bytes)
    (r : Result) (i : Nat) (p : Piece) (receipt : Receipt) (v : NativeVoteBytes.Vote)
    (ok : check sha raw = some r) (atIndex : r.pieces[i]? = some p)
    (bound : NativeWalBytes.bindReceipt sha policy p.bytes receiptBytes = some (p.entry,receipt,v)) :
    receipt.sequence = 1+i ∧ NativeReceiptBytes.encode receipt = receiptBytes ∧
    NativeVoteBytes.encodeFrame v.wire = p.entry.command ∧ encode sha p.entry = p.bytes := by
  have indexed : (entries r)[i]? = some p.entry := by
    simp only [entries, List.getElem?_map, atIndex, Option.map_some]
  have position := checkedPosition sha raw r ok i p.entry indexed
  have linked := NativeWalBytes.bindingSound sha policy p.bytes receiptBytes p.entry receipt v bound
  have original := boundOriginalBytes sha policy p.bytes receiptBytes p.entry receipt v bound
  exact ⟨linked.2.2.2.1.symm.trans position, original.2.1, original.2.2.1, original.1⟩

end DeltaReduce.NativeWalScan
