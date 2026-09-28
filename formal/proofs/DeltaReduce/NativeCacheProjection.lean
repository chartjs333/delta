import DeltaReduce.NativeCacheHistory

/-! Historical diagnostic projection from executed cache images. This is not
NativePrepared, an authenticated resolver or an exposure/recovery transition.
Unsupported ordinary rows reject the whole projection rather than disappear. -/
namespace DeltaReduce.NativeCacheProjection
open NativeBinding NativeVoteCache
variable {codec : Codec} {store : Store} {trust : Trust} (adapter : HashAdapter codec)

def project (row : Row (store := store) (trust := trust) adapter) : Option RecoveryKernel.Record := do
  match row.payload with
  | .ordinary _ _ => none
  | .arithmetic s x =>
    let expected ← deriveExpectedNativeVote s.binding x.image.metadata
    if expected.data = x.image.expected.data ∧ expected.envelope = x.image.expected.envelope ∧
        expected.effect = x.image.expected.effect ∧ expected.command.length ≤ 4194304 then
      let receipt ← encodeDiagnosticReceipt codec expected.command expected.envelope expected.effect row.ordinal
      some ⟨expected.data,row.ordinal,receipt,expected.effect⟩
    else none

theorem projected {row : Row (store := store) (trust := trust) adapter} {record}
    (h : project adapter row = some record) :
    ∃ s x expected receipt,
      row.payload = .arithmetic s x ∧ deriveExpectedNativeVote s.binding x.image.metadata = some expected ∧
      expected.data = x.image.expected.data ∧ expected.envelope = x.image.expected.envelope ∧
      expected.effect = x.image.expected.effect ∧ expected.command.length ≤ 4194304 ∧
      encodeDiagnosticReceipt codec expected.command expected.envelope expected.effect row.ordinal = some receipt ∧
      record = ⟨expected.data,row.ordinal,receipt,expected.effect⟩ := by
  unfold project at h
  cases hp : row.payload with
  | ordinary _ _ => simp [hp] at h
  | arithmetic s x =>
    simp only [hp,bind,Option.bind_eq_some_iff] at h
    obtain ⟨expected,he,last⟩ := h
    split at last <;> try contradiction
    rename_i checks
    simp only [Option.bind_eq_some_iff] at last
    obtain ⟨receipt,hr,last⟩ := last
    exact ⟨s,x,expected,receipt,rfl,he,checks.1,checks.2.1,checks.2.2.1,checks.2.2.2,hr,(Option.some.inj last).symm⟩

theorem recordOrdinal {row : Row (store := store) (trust := trust) adapter} {record}
    (h : project adapter row = some record) : record.sequence = row.ordinal := by
  obtain ⟨_,_,_,_,_,_,_,_,_,_,_,rfl⟩ := projected adapter h
  rfl

theorem ordinaryRejects {row : Row (store := store) (trust := trust) adapter} {b id}
    (h : row.payload = .ordinary b id) : project adapter row = none := by simp [project,h]

theorem projectFromComponents {row : Row (store := store) (trust := trust) adapter} {s x expected receipt}
    (payload : row.payload = .arithmetic s x)
    (derived : deriveExpectedNativeVote s.binding x.image.metadata = some expected)
    (checked : expected.data = x.image.expected.data ∧ expected.envelope = x.image.expected.envelope ∧
      expected.effect = x.image.expected.effect ∧ expected.command.length ≤ 4194304)
    (encoded : encodeDiagnosticReceipt codec expected.command expected.envelope expected.effect row.ordinal = some receipt) :
    project adapter row = some ⟨expected.data,row.ordinal,receipt,expected.effect⟩ := by
  simp only [project,payload,derived,bind,Option.bind,if_pos checked,encoded]

def all : List (Row (store := store) (trust := trust) adapter) → Option (List RecoveryKernel.Record)
  | [] => some []
  | row::rest => do
    let record ← project adapter row
    let records ← all rest
    some (record::records)

variable {rows : List (Row (store := store) (trust := trust) adapter)}

theorem allPairs {records} (h : all adapter rows = some records) :
    List.Forall₂ (fun row record => project adapter row = some record) rows records := by
  induction rows generalizing records with
  | nil => cases Option.some.inj h; exact .nil
  | cons row rest ih =>
    simp only [all,bind,Option.bind_eq_some_iff] at h
    obtain ⟨record,hp,tail,ht,last⟩ := h
    cases Option.some.inj last
    exact .cons hp (ih ht)

theorem pairsComplete {records}
    (h : List.Forall₂ (fun row record => project adapter row = some record) rows records) :
    all adapter rows = some records := by
  induction h with
  | nil => rfl
  | cons hp _ ih => simp only [all,hp,ih,bind,Option.bind]

theorem allOrdinals {records} (h : all adapter rows = some records) :
    records.map RecoveryKernel.Record.sequence = rows.map Row.ordinal := by
  have pairs := allPairs adapter h
  clear h
  induction pairs with
  | nil => rfl
  | cons hp _ ih => simp only [List.map_cons,recordOrdinal adapter hp,ih]

theorem everyOriginal {records} (h : all adapter rows = some records) {row} (mem : row ∈ rows) :
    ∃ record ∈ records, project adapter row = some record := by
  have pairs := allPairs adapter h
  clear h
  induction pairs with
  | nil => simp at mem
  | cons hp _ ih =>
    rcases List.mem_cons.mp mem with rfl | rest
    · exact ⟨_,List.mem_cons_self,hp⟩
    · obtain ⟨record,hm,hr⟩ := ih rest
      exact ⟨record,List.mem_cons_of_mem _ hm,hr⟩

theorem everyProjected {records} (h : all adapter rows = some records) {record} (mem : record ∈ records) :
    ∃ row ∈ rows, project adapter row = some record := by
  have pairs := allPairs adapter h
  clear h
  induction pairs with
  | nil => simp at mem
  | cons hp _ ih =>
    rcases List.mem_cons.mp mem with rfl | rest
    · exact ⟨_,List.mem_cons_self,hp⟩
    · obtain ⟨row,hm,hr⟩ := ih rest
      exact ⟨row,List.mem_cons_of_mem _ hm,hr⟩

theorem ordinaryBlocksAll {row} (mem : row ∈ rows) {b id} (ordinary : row.payload = .ordinary b id) :
    all adapter rows = none := by
  cases h : all adapter rows with
  | none => rfl
  | some records =>
    obtain ⟨record,_,hp⟩ := everyOriginal adapter h mem
    rw [ordinaryRejects adapter ordinary] at hp
    contradiction

structure Projection where
  cache : Result (store := store) (trust := trust) adapter
  records : List RecoveryKernel.Record

def recoverObserved (policy initial : Bytes) (snap : Option NativeCommandReplay.Snapshot)
    (observation : Option Bytes) (sources : List (Option (NativeArithmeticJournal.Source codec store trust adapter.sha256))) :
    Option (Projection (store := store) (trust := trust) adapter) := do
  let cache ← NativeCacheHistory.recoverObserved adapter policy initial snap observation sources
  let records ← all adapter cache.rows
  some ⟨cache,records⟩

theorem recoveryComputed {policy initial snap observation sources projection}
    (h : recoverObserved (store := store) (trust := trust) adapter policy initial snap observation sources = some projection) :
    NativeCacheHistory.recoverObserved adapter policy initial snap observation sources = some projection.cache ∧
    all adapter projection.cache.rows = some projection.records := by
  simp only [recoverObserved,bind,Option.bind_eq_some_iff] at h
  obtain ⟨cache,hc,records,hr,last⟩ := h
  cases Option.some.inj last
  exact ⟨hc,hr⟩

theorem recoveryCoverage {policy initial snap observation sources projection}
    (h : recoverObserved (store := store) (trust := trust) adapter policy initial snap observation sources = some projection) :
    projection.cache.after.votes = projection.cache.rows.map (native adapter) ∧
    List.Forall₂ (fun row record => project adapter row = some record) projection.cache.rows projection.records ∧
    projection.records.map RecoveryKernel.Record.sequence = List.range' 1 projection.cache.rows.length := by
  have checked := recoveryComputed adapter h
  obtain ⟨_,_,_,_,_,_,_,_,hr⟩ := NativeCacheHistory.observed adapter checked.1
  have cache := NativeCacheHistory.recoveredCache adapter hr
  exact ⟨cache.1,allPairs adapter checked.2,(allOrdinals adapter checked.2).trans cache.2.1⟩

theorem projectedScanNotFresh {policy snap m input} {row : Row (store := store) (trust := trust) adapter}
    (source : RowSource adapter policy snap m input row) {record}
    (projectedRecord : project adapter row = some record) :
    ∃ s x, row.payload = .arithmetic s x ∧ x.image.metadata.recovered = false ∧
      record.data = x.image.expected.data ∧ record.sequence = row.ordinal := by
  obtain ⟨s,x,expected,receipt,hp,_,data,_,_,_,_,rfl⟩ := projected adapter projectedRecord
  have original := arithmeticOriginalSource adapter source hp
  exact ⟨s,x,hp,original.2.2,data,rfl⟩

theorem unknownRejects (policy initial snap sources) :
    recoverObserved (store := store) (trust := trust) adapter policy initial snap none sources = none := rfl

end DeltaReduce.NativeCacheProjection
