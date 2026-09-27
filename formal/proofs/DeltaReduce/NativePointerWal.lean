import DeltaReduce.NativeCurrentPointer

/-! The pointer store uses text lines, not DRW1. This pure observed-byte model
retains a torn suffix; it does not perform or authenticate physical truncation.
Recovery checks stored hashes/parent/height, and does not reload an ApplyQC. -/
namespace DeltaReduce.NativePointerWal
open NativeReceiptBytes NativeCurrentPointer
open NativeVoteBytes (ContentId)

structure Record where
  height : Nat
  parent : Bytes
  checkpoint : Bytes
  optimizer : Bytes
  qc : Bytes
  deriving DecidableEq, Repr
def record (p : Prepared) : Record :=
  ⟨p.command.context.height,p.command.parent,p.command.checkpoint,p.command.optimizer,p.qcId⟩
def result (r : Record) : State := ⟨r.checkpoint,r.optimizer,r.qc,r.height⟩
def joined (h p c o q : Bytes) : Bytes := h ++ [124] ++ p ++ [124] ++ c ++ [124] ++ o ++ [124] ++ q
def payload (r : Record) : Bytes := joined (NativeIscCertificate.number r.height) r.parent r.checkpoint r.optimizer r.qc
def checksum (sha : Bytes → Bytes) (raw : Bytes) : Option Bytes :=
  let digest := sha raw
  if digest.length = 32 then some (NativeVoteBytes.hexBytes digest) else none
def line (sha : Bytes → Bytes) (r : Record) : Option Bytes := do
  let sum ← checksum sha (payload r)
  some (payload r ++ [124] ++ sum ++ [10])

-- Computable split retaining empty fields, including the final unterminated part.
def split (separator : UInt8) : Bytes → List Bytes
  | [] => [[]]
  | b::bs =>
    let rest := split separator bs
    if b = separator then []::rest else
      match rest with | [] => [[b]] | head::tail => (b::head)::tail

def RowValid (r : Record) : Prop :=
  r.height < 256^8 ∧ ContentId r.checkpoint ∧ ContentId r.optimizer ∧ ContentId r.qc
instance (r) : Decidable (RowValid r) := by unfold RowValid; infer_instance

def readFields (sha : Bytes → Bytes) : List Bytes → Option Record
  | [height,parent,checkpoint,optimizer,qc,sum] => do
    let actual ← checksum sha (joined height parent checkpoint optimizer qc)
    if actual = sum then
      let h ← NativeVoteBytes.parseDecimal height
      let r := Record.mk h parent checkpoint optimizer qc
      if RowValid r then some r else none
    else none
  | _ => none
def readLine (sha : Bytes → Bytes) (raw : Bytes) := readFields sha (split 124 raw)

theorem readFieldsSource {sha fields r} (h : readFields sha fields = some r) :
    ∃ height sum, fields = [height,r.parent,r.checkpoint,r.optimizer,r.qc,sum] ∧
    NativeVoteBytes.parseDecimal height = some r.height ∧
    checksum sha (joined height r.parent r.checkpoint r.optimizer r.qc) = some sum ∧ RowValid r := by
  unfold readFields at h
  split at h <;> try contradiction
  rename_i height parent checkpoint optimizer qc sum
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨actual,ha,last⟩ := h
  split at last <;> try contradiction
  rename_i eq
  subst actual
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨n,hn,last⟩ := last
  split at last <;> try contradiction
  rename_i valid
  cases Option.some.inj last
  exact ⟨height,sum,rfl,hn,ha,valid⟩

def Extend (s : State) (r : Record) : Prop :=
  s.height < r.height ∧ r.parent = s.checkpoint ∧ RowValid r
instance (s r) : Decidable (Extend s r) := by unfold Extend; infer_instance
def step (s : State) (r : Record) : Option State := if Extend s r then some (result r) else none
theorem stepExact {s r n} (h : step s r = some n) : Extend s r ∧ n = result r := by
  unfold step at h
  split at h <;> try contradiction
  exact ⟨by assumption,(Option.some.inj h).symm⟩
theorem stepValid {s r n} (h : step s r = some n) : StateValid n := by
  obtain ⟨valid,rfl⟩ := stepExact h
  exact ⟨valid.2.2.2.1,valid.2.2.2.2.1,Or.inr valid.2.2.2.2.2,valid.2.2.1⟩
theorem heightIncreases {s r n} (h : step s r = some n) : s.height < n.height := by
  obtain ⟨valid,rfl⟩ := stepExact h
  exact valid.1

structure Recovered where
  state : State
  records : List Record
  tail : Bytes
  deriving DecidableEq, Repr

def replay (sha : Bytes → Bytes) (s : State) : List Bytes → Option Recovered
  | [] => none
  | [tail] => some ⟨s,[],tail⟩
  | raw::nextRaw::rest => do
    let r ← readLine sha raw
    let n ← step s r
    let out ← replay sha n (nextRaw::rest)
    some ⟨out.state,r::out.records,out.tail⟩

inductive History (sha : Bytes → Bytes) : State → List Bytes → Recovered → Prop where
  | done (s tail) : History sha s [tail] ⟨s,[],tail⟩
  | more {s raw r n rest out}
      (parsed : readLine sha raw = some r) (extended : step s r = some n)
      (later : History sha n rest out) :
      History sha s (raw::rest) ⟨out.state,r::out.records,out.tail⟩

theorem replayHistory {sha s lines out} (h : replay sha s lines = some out) : History sha s lines out := by
  induction lines generalizing s out with
  | nil => simp [replay] at h
  | cons raw rest ih =>
    cases rest with
    | nil => simp only [replay,Option.some.injEq] at h; subst out; exact .done s raw
    | cons head tail =>
      simp only [replay,bind,Option.bind_eq_some_iff] at h
      obtain ⟨r,hr,n,hn,later,hl,last⟩ := h
      cases Option.some.inj last
      exact .more hr hn (ih hl)

theorem historyPreservesValid {sha s lines out} (h : History sha s lines out) (valid : StateValid s) :
    StateValid out.state := by
  induction h with
  | done => exact valid
  | more _ step _ ih => exact ih (stepValid step)

theorem historyHeight {sha s lines out} (h : History sha s lines out) : s.height ≤ out.state.height := by
  induction h with
  | done => exact Nat.le_refl _
  | more _ step _ ih => exact Nat.le_trans (Nat.le_of_lt (heightIncreases step)) ih

theorem historyRecord {sha s lines out} (h : History sha s lines out) (r : Record) (mem : r ∈ out.records) :
    ∃ raw ∈ lines, readLine sha raw = some r ∧ ∃ before after, step before r = some after := by
  induction h with
  | done => simp at mem
  | more parsed extended later ih =>
    rcases List.mem_cons.mp mem with rfl | hr
    · exact ⟨_,List.mem_cons_self,parsed,_,_,extended⟩
    · obtain ⟨raw,hm,hp,b,a,hs⟩ := ih hr
      exact ⟨raw,List.mem_cons_of_mem _ hm,hp,b,a,hs⟩

-- Unknown is not an empty WAL. Physical source/completeness/authentication is
-- a separate obligation for either claimed complete or torn-byte observations.
inductive Observation where | bytes (raw : Bytes) | unknown deriving DecidableEq, Repr
def recover (sha : Bytes → Bytes) (s : State) (observation : Observation) : Option Recovered :=
  match observation with
  | .unknown => none
  | .bytes raw => if StateValid s then replay sha s (split 10 raw) else none
theorem unknownRejected (sha s) : recover sha s .unknown = none := rfl
theorem recoveredHistory {sha s raw out} (h : recover sha s (.bytes raw) = some out) :
    StateValid s ∧ History sha s (split 10 raw) out := by
  simp only [recover] at h
  split at h <;> try contradiction
  exact ⟨by assumption,replayHistory h⟩
theorem recoveredValid {sha s raw out} (h : recover sha s (.bytes raw) = some out) : StateValid out.state :=
  historyPreservesValid (recoveredHistory h).2 (recoveredHistory h).1

inductive Cut where
  | beforeAppend | afterAppendBeforeDurability | duringAppend | afterDurability
  | afterCommit | afterCopy | returned | unknown
  deriving DecidableEq, Repr
structure Outcome where
  memory : State
  appended : Bytes
  response : Option Disposition
  deriving DecidableEq, Repr
def commitCut (s : State) (p : Prepared) (bytes : Bytes) : Cut → Option Outcome
  | .unknown => none
  | .beforeAppend | .afterAppendBeforeDurability => some ⟨s,[],none⟩
  | .duringAppend => some ⟨s,NativeVoteBytes.ascii "truncated",none⟩
  | .afterDurability => some ⟨s,bytes,none⟩
  | .afterCommit | .afterCopy => some ⟨next p,bytes,none⟩
  | .returned => some ⟨next p,bytes,some .advanced⟩
def execute (sha : Bytes → Bytes) (s : State) (c : Command)
    (q : NativeApplyCertificate.Certificate) (cut : Cut) : Option Outcome := do
  let p ← prepare sha c q
  let d ← choose s p
  match d with
  | .replay => some ⟨s,[],some .replay⟩
  | .advanced => do
    let bytes ← line sha (record p)
    commitCut s p bytes cut

theorem returnedRequiresAppend {s p bytes cut out}
    (h : commitCut s p bytes cut = some out) (returned : out.response = some .advanced) :
    cut = .returned ∧ out.memory = next p ∧ out.appended = bytes := by
  cases cut <;> simp only [commitCut] at h <;> try contradiction
  all_goals cases Option.some.inj h
  all_goals simp_all
theorem exactReplayNoAppend {sha s c q p cut}
    (prepared : prepare sha c q = some p) (replayed : choose s p = some .replay) :
    execute sha s c q cut = some ⟨s,[],some .replay⟩ := by
  simp only [execute,prepared,replayed,bind,Option.bind]
theorem unacknowledgedDurable (s p bytes) :
    commitCut s p bytes .afterDurability = some ⟨s,bytes,none⟩ := rfl
theorem uncertainCut (s p bytes) : commitCut s p bytes .unknown = none := rfl
theorem freshRecordExtends {sha c q p s} (prepared : prepare sha c q = some p)
    (fresh : choose s p = some .advanced) : step s (record p) = some (next p) := by
  have valid := nextValid prepared
  have ext := (freshExact fresh).2
  apply if_pos
  exact ⟨ext.2,ext.1,valid.2.2.2,valid.1,valid.2.1,
    by
      change ContentId p.qcId
      rw [← (preparedSource prepared).links.1]
      exact (commandChecked (preparedSource prepared).commandHash).1.2.1⟩
theorem durableReplayRepair {sha c q p s}
    (prepared : prepare sha c q = some p) (fresh : choose s p = some .advanced) :
    step s (record p) = some (next p) ∧ choose (next p) p = some .replay :=
  ⟨freshRecordExtends prepared fresh,replayAfterAdvance p⟩
end DeltaReduce.NativePointerWal
