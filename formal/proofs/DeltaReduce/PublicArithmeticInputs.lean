import DeltaReduce.NativeInputProjection
import DeltaReduce.PublicScalarNumbers

/-! Complete 23-field scalar NativeArithmeticInputs encoding from checked native
inputs. Vocabulary is separately configured; aliases do not supply numbers.
This does not authenticate the configuration or prove parent/QC/action recovery. -/
namespace DeltaReduce.PublicArithmeticInputs
open NativeBinding PublicState NativeInputProjection

structure Image where
  tickets : List TicketData
  domains : List DomainData
  shards : List String
  profile : Profile
  mixtureDenominator : Nat
  model : List (String × Int)
  optimizer : List (String × Int)
  limit : Int
  deriving DecidableEq, Repr

def image {codec store trust anchor binding corpus limit}
    (p : Projected (codec := codec) (store := store) (trust := trust) (anchor := anchor) (binding := binding) corpus limit) : Image :=
  ⟨p.tickets,p.domains,shardIds corpus.frame,binding.profile,p.weights.denominator,p.model.cells,p.optimizer.cells,limit.value⟩

structure Vocabulary where
  ticket : String → Option String
  domain : String → Option String
  shard : String → Option String
  tickets : List String
  domains : List String
  shards : List String
  models : List String

def entries : List (Value × Value) → Entries
  | [] => .nil
  | (k,v) :: rest => .cons k v (entries rest)

def insertEntry (row : Value × Value) : List (Value × Value) → List (Value × Value)
  | [] => [row]
  | first :: rest => if byteLess (encode row.1) (encode first.1) then row :: first :: rest
      else first :: insertEntry row rest

def sortEntries : List (Value × Value) → List (Value × Value)
  | [] => []
  | row :: rest => insertEntry row (sortEntries rest)

theorem insertEntryPerm (row : Value × Value) (rows : List (Value × Value)) :
    (insertEntry row rows).Perm (row :: rows) := by
  induction rows with
  | nil => exact List.Perm.refl _
  | cons first rest ih =>
      simp only [insertEntry]
      split
      · exact List.Perm.refl _
      · exact (List.Perm.cons first ih).trans (List.Perm.swap _ _ _)

theorem sortEntriesPerm (rows : List (Value × Value)) : (sortEntries rows).Perm rows := by
  induction rows with
  | nil => exact List.Perm.refl _
  | cons row rest ih => exact (insertEntryPerm row _).trans (List.Perm.cons row ih)

def function (rows : List (Value × Value)) : Value := .function (entries (sortEntries rows))

theorem entriesInverse (rows : List (Value × Value)) : PublicScalarNumbers.entriesList (entries rows) = rows := by
  induction rows with
  | nil => rfl
  | cons row rows ih => cases row; simp [entries,PublicScalarNumbers.entriesList,ih]

theorem functionPreservesAllPairs (rows : List (Value × Value)) :
    ∃ e, function rows = .function e ∧ (PublicScalarNumbers.entriesList e).Perm rows := by
  refine ⟨_,rfl,?_⟩
  rw [entriesInverse]
  exact sortEntriesPerm _

def sequence (values : List Value) : Value :=
  function ((List.range values.length).zip values |>.map (fun (i,v) => (.integer (Int.ofNat (i+1)),v)))

def named {α : Type} (alias : String → Option String) (key : α → String) (value : α → Option Value) (rows : List α) : Option Value := do
  let pairs ← collect (fun row => do
    let name ← alias (key row)
    let v ← value row
    some (.model name,v)) rows
  some (function pairs)

-- Zip only after exact shape comparison. No extra coordinate may disappear.
def vectorTable (alias : String → Option String) (shards : List String) (values : List Int) : Option Value :=
  if values.length = shards.length then
    named alias Prod.fst (fun p => some (.integer p.2)) (shards.zip values)
  else none

def ticketDomains (v : Vocabulary) (i : Image) : Option Value :=
  named v.ticket (·.ticket) (fun t => (v.domain t.domain).map Value.model) i.tickets

def qTable (v : Vocabulary) (i : Image) : Option Value :=
  named v.ticket (·.ticket) (fun t => vectorTable v.shard i.shards t.q) i.tickets

def weightTable (part : Rational → Int) (v : Vocabulary) (i : Image) : Option Value :=
  named v.ticket (·.ticket) (fun t => some (.integer (part t.weight))) i.tickets

def denominatorTable (v : Vocabulary) (i : Image) : Option Value :=
  named v.domain (·.domain) (fun d => some (.integer d.denominator)) i.domains

def quantumTable (part : Rational → Int) (v : Vocabulary) (i : Image) : Option Value :=
  named v.domain (·.domain) (fun d => vectorTable v.shard i.shards (d.quantum.map part)) i.domains

def mixtureTable (part : Rational → Int) (v : Vocabulary) (i : Image) : Option Value :=
  named v.domain (·.domain) (fun d => some (.integer (part d.weight))) i.profile.domainWeights

def currentTable (alias : String → Option String) (pairs : List (String × Int)) : Option Value :=
  named alias Prod.fst (fun p => some (.integer p.2)) pairs

def namespaceMatches (alias : String → Option String) (names configured : List String) : Prop :=
  ∃ projected, collect alias names = some projected ∧ projected.Perm configured ∧ projected.Nodup

-- Decidable finite namespace validation is performed by computation, not a
-- caller-supplied validity flag.
def checkNamespace (alias : String → Option String) (names configured : List String) : Bool :=
  match collect alias names with
  | none => false
  | some projected => decide (projected.Perm configured ∧ projected.Nodup)

theorem namespaceCheckSound {alias names configured} (h : checkNamespace alias names configured = true) :
    namespaceMatches alias names configured := by
  unfold checkNamespace at h
  split at h
  · contradiction
  · rename_i projected hc
    exact ⟨projected,hc,(of_decide_eq_true h).1,(of_decide_eq_true h).2⟩

def fieldNames : List String := [
  "applyD", "applyN", "denominator", "domainOrder", "limit", "lrD", "lrN",
  "mixtureD", "model", "muD", "muN", "optimizer", "piD", "piN", "q", "qD", "qN",
  "ticketDomain", "ticketOrder", "wdD", "wdN", "weightD", "weightN"]

structure Components (v : Vocabulary) (i : Image) where
  ticketNames : List String
  tickets : collect v.ticket (i.tickets.map (·.ticket)) = some ticketNames
  domainNames : List String
  domains : collect v.domain (i.profile.domainWeights.map (·.domain)) = some domainNames
  values : List Value
  computed : collect id [ticketDomains v i,qTable v i,
    weightTable Rational.numerator v i,weightTable Rational.denominator v i,
    denominatorTable v i,quantumTable Rational.numerator v i,quantumTable Rational.denominator v i,
    mixtureTable Rational.numerator v i,mixtureTable Rational.denominator v i,
    currentTable v.shard i.model,currentTable v.shard i.optimizer] = some values
  size : values.length = 11
  ticketSet : checkNamespace v.ticket (i.tickets.map (·.ticket)) v.tickets = true
  domainSet : checkNamespace v.domain (i.profile.domainWeights.map (·.domain)) v.domains = true
  shardSet : checkNamespace v.shard i.shards v.shards = true

def loadComponents (v : Vocabulary) (i : Image) : Option (Components v i) := do
  match ht : collect v.ticket (i.tickets.map (·.ticket)), hd : collect v.domain (i.profile.domainWeights.map (·.domain)),
    hc : collect id [ticketDomains v i,qTable v i,
      weightTable Rational.numerator v i,weightTable Rational.denominator v i,
      denominatorTable v i,quantumTable Rational.numerator v i,quantumTable Rational.denominator v i,
      mixtureTable Rational.numerator v i,mixtureTable Rational.denominator v i,
      currentTable v.shard i.model,currentTable v.shard i.optimizer] with
  | some ticketNames, some domainNames, some values =>
      if h : values.length = 11 ∧
          checkNamespace v.ticket (i.tickets.map (·.ticket)) v.tickets = true ∧
          checkNamespace v.domain (i.profile.domainWeights.map (·.domain)) v.domains = true ∧
          checkNamespace v.shard i.shards v.shards = true then
        some ⟨ticketNames,ht,domainNames,hd,values,hc,h.1,h.2.1,h.2.2.1,h.2.2.2⟩
      else none
  | _, _, _ => none

theorem loadComponentsFromComputed {v i} (c : Components v i) : loadComponents v i = some c := by
  unfold loadComponents
  cases c with
  | mk ticketNames ht domainNames hd values hc size tickets domains shards =>
    split
    · rename_i tn dn vs htn hdn hvs
      have et : tn = ticketNames := Option.some.inj (htn.symm.trans ht)
      have ed : dn = domainNames := Option.some.inj (hdn.symm.trans hd)
      have ev : vs = values := Option.some.inj (hvs.symm.trans hc)
      subst tn; subst dn; subst vs
      rw [dif_pos ⟨size,tickets,domains,shards⟩]
    · simp_all

def Components.at {v i} (c : Components v i) (index : Fin 11) : Value :=
  c.values[index.val]'(by rw [c.size]; exact index.isLt)

def Components.fields {v i} (c : Components v i) : List (String × Value) := [
  ("applyD",.integer i.profile.applyQuantum.denominator),
  ("applyN",.integer i.profile.applyQuantum.numerator),
  ("denominator",c.at 4),
  ("domainOrder",sequence (c.domainNames.map Value.model)),
  ("limit",.integer i.limit),
  ("lrD",.integer i.profile.learningRate.denominator),
  ("lrN",.integer i.profile.learningRate.numerator),
  ("mixtureD",.integer (Int.ofNat i.mixtureDenominator)),
  ("model",c.at 9),
  ("muD",.integer i.profile.momentum.denominator),
  ("muN",.integer i.profile.momentum.numerator),
  ("optimizer",c.at 10),
  ("piD",c.at 8), ("piN",c.at 7), ("q",c.at 1), ("qD",c.at 6), ("qN",c.at 5),
  ("ticketDomain",c.at 0), ("ticketOrder",sequence (c.ticketNames.map Value.model)),
  ("wdD",.integer i.profile.weightDecay.denominator), ("wdN",.integer i.profile.weightDecay.numerator),
  ("weightD",c.at 3), ("weightN",c.at 2)]

theorem completeFieldInventory {v i} (c : Components v i) : c.fields.map Prod.fst = fieldNames := rfl

theorem componentIsComputed {v i} (c : Components v i) (index : Fin 11) :
    [ticketDomains v i,qTable v i,
      weightTable Rational.numerator v i,weightTable Rational.denominator v i,
      denominatorTable v i,quantumTable Rational.numerator v i,quantumTable Rational.denominator v i,
      mixtureTable Rational.numerator v i,mixtureTable Rational.denominator v i,
      currentTable v.shard i.model,currentTable v.shard i.optimizer][index.val]? = some (some (c.at index)) := by
  obtain ⟨value,hv,computed⟩ := collectAt c.computed index.val (c.at index) (by simp [Components.at])
  change value = some (c.at index) at computed
  rw [computed] at hv
  exact hv

structure Encoded (v : Vocabulary) (i : Image) where
  components : Components v i
  canonical : PublicState.canonical v.models (.function (entries (components.fields.map (fun (k,x) => (.text k,x))))) = true

def Encoded.value {v i} (e : Encoded v i) : Value :=
  .function (entries (e.components.fields.map (fun (k,x) => (.text k,x))))

def Encoded.preimage {v i} (e : Encoded v i) : Bytes := PublicState.encode e.value

def encodeImage (v : Vocabulary) (i : Image) : Option (Encoded v i) := do
  let components ← loadComponents v i
  if canonical : PublicState.canonical v.models (.function (entries (components.fields.map (fun (k,x) => (.text k,x))))) = true then
    some ⟨components,canonical⟩
  else none

theorem encodeImageFromComputed {v i} (e : Encoded v i) : encodeImage v i = some e := by
  unfold encodeImage
  rw [loadComponentsFromComputed e.components]
  simp only [Bind.bind,Option.bind]
  rw [dif_pos e.canonical]

def encodeProjected {codec store trust anchor binding corpus limit}
    (v : Vocabulary)
    (p : Projected (codec := codec) (store := store) (trust := trust) (anchor := anchor) (binding := binding) corpus limit) :
    Option (Encoded v (image p)) := encodeImage v (image p)

theorem encodedRetainsEveryField {v i} (e : Encoded v i) :
    ∃ entries, e.value = .function entries ∧
      (PublicScalarNumbers.entriesList entries).Perm (e.components.fields.map (fun (k,x) => (.text k,x))) :=
  ⟨_,rfl,by rw [entriesInverse]⟩

theorem encodedCanonical {v i} (e : Encoded v i) : PublicState.canonical v.models e.value = true := e.canonical

def checkProjected {codec store trust anchor binding corpus limit}
    (v : Vocabulary)
    (p : Projected (codec := codec) (store := store) (trust := trust) (anchor := anchor) (binding := binding) corpus limit)
    (candidate : Value) : Option (Encoded v (image p)) := do
  let encoded ← encodeProjected v p
  if candidate = encoded.value then some encoded else none

theorem checkedWholeInputs {codec store trust anchor binding corpus limit v p candidate encoded}
    (h : checkProjected (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (corpus := corpus) (limit := limit) v p candidate = some encoded) :
    candidate = encoded.value := by
  unfold checkProjected at h
  cases he : encodeProjected v p with
  | none => simp [he] at h
  | some e =>
      simp only [he,Bind.bind,Option.bind] at h
      split at h
      · rename_i same; cases h; exact same
      · contradiction

theorem imageProfileComesFromNative {codec store trust anchor binding corpus limit}
    (p : Projected (codec := codec) (store := store) (trust := trust) (anchor := anchor) (binding := binding) corpus limit) :
    (image p).profile = binding.profile ∧ (image p).limit = limit.value ∧
    (image p).mixtureDenominator = p.weights.denominator := ⟨rfl,rfl,rfl⟩

theorem sourceNamespacesComplete {codec store trust anchor binding corpus limit v}
    {p : Projected (codec := codec) (store := store) (trust := trust) (anchor := anchor) (binding := binding) corpus limit}
    (e : Encoded v (image p)) :
    namespaceMatches v.ticket (p.tickets.map (·.ticket)) v.tickets ∧
    namespaceMatches v.domain (binding.profile.domainWeights.map (·.domain)) v.domains ∧
    namespaceMatches v.shard (shardIds corpus.frame) v.shards :=
  ⟨namespaceCheckSound e.components.ticketSet,namespaceCheckSound e.components.domainSet,
    namespaceCheckSound e.components.shardSet⟩

end DeltaReduce.PublicArithmeticInputs
