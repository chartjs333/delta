import DeltaReduce.PublicArithmeticInputs

/-! Conditional construction of the complete public arithmetic authority.
Primitive configuration/seed/content names come from a separately authenticated
metadata source. It supplies no public certificate or authority body. Actual
phase/QC admission, exporter authentication and native recovery remain separate. -/
namespace DeltaReduce.PublicAuthority
open NativeBinding NativeInputProjection PublicState PublicArithmeticInputs

inductive AtomKey where
  | height (height : Nat)
  | epoch (epoch : String)
  | parent (checkpoint : String)
  | schema (ref : Ref)
  | profile (ref : Ref)
  | applyProfile (ref : Ref)
  | config (authority : Ref) (context : Context)
  | seed (isc : Ref) (epoch : String)
  | norm (ec : Ref)
  | coefficient (apc plan : Ref)
  | content (isc : Ref) (commitment : Commitment)
  deriving DecidableEq, Repr

inductive ClosePolicy where
  | omitUnavailable | abortOnIncomplete
  deriving DecidableEq, Repr

def ClosePolicy.text : ClosePolicy → String
  | .omitUnavailable => "OMIT_UNAVAILABLE"
  | .abortOnIncomplete => "ABORT_ON_INCOMPLETE"

structure MetadataTrust where
  atom : AtomKey → String → Prop
  policy : Ref → Context → ClosePolicy → Prop

-- This named premise is deliberately not an authentication algorithm. A native
-- producer must establish it independently; fixture instantiations are synthetic.
structure Metadata (trust : MetadataTrust) where
  atom : AtomKey → Option String
  policy : Ref → Context → Option ClosePolicy
  atomAuthentic : ∀ key name, atom key = some name → trust.atom key name
  policyAuthentic : ∀ ref context value, policy ref context = some value → trust.policy ref context value

structure Atom {trust} (source : Metadata trust) (key : AtomKey) where
  name : String
  selected : source.atom key = some name

def loadAtom {trust} (source : Metadata trust) (key : AtomKey) : Option (Atom source key) :=
  match selected : source.atom key with
  | none => none
  | some name => some ⟨name,selected⟩

def Atom.value {trust source key} (atom : Atom (trust := trust) source key) : Value := .model atom.name

theorem atomHasIndependentSource {trust source key} (atom : Atom (trust := trust) source key) :
    trust.atom key atom.name := source.atomAuthentic key atom.name atom.selected

structure Header {codec store trust anchor} (binding : Binding codec trust anchor store)
    {metadataTrust} (source : Metadata metadataTrust) where
  height : Atom source (.height binding.authority.context.height)
  epoch : Atom source (.epoch binding.authority.context.epoch)
  parent : Atom source (.parent binding.authority.context.parentCheckpoint)
  schema : Atom source (.schema binding.authority.schema)
  profile : Atom source (.profile binding.authority.profile)
  applyProfile : Atom source (.applyProfile binding.authority.profile)
  config : Atom source (.config anchor.authority binding.authority.context)
  seed : Atom source (.seed binding.authority.isc binding.authority.context.epoch)
  norm : Atom source (.norm binding.authority.ec)
  coefficient : Atom source (.coefficient binding.authority.apc binding.authority.plan)
  policy : ClosePolicy
  policySelected : source.policy anchor.authority binding.authority.context = some policy

def loadHeader {codec store trust anchor} (binding : Binding codec trust anchor store)
    {metadataTrust} (source : Metadata metadataTrust) : Option (Header binding source) := do
  let height ← loadAtom source (.height binding.authority.context.height)
  let epoch ← loadAtom source (.epoch binding.authority.context.epoch)
  let parent ← loadAtom source (.parent binding.authority.context.parentCheckpoint)
  let schema ← loadAtom source (.schema binding.authority.schema)
  let profile ← loadAtom source (.profile binding.authority.profile)
  let applyProfile ← loadAtom source (.applyProfile binding.authority.profile)
  let config ← loadAtom source (.config anchor.authority binding.authority.context)
  let seed ← loadAtom source (.seed binding.authority.isc binding.authority.context.epoch)
  let norm ← loadAtom source (.norm binding.authority.ec)
  let coefficient ← loadAtom source (.coefficient binding.authority.apc binding.authority.plan)
  match hp : source.policy anchor.authority binding.authority.context with
  | none => none
  | some policy => some ⟨height,epoch,parent,schema,profile,applyProfile,config,seed,norm,coefficient,policy,hp⟩

theorem headerUsesOriginalAuthority {codec store trust anchor metadataTrust source}
    {binding : Binding codec trust anchor store} (h : Header binding (metadataTrust := metadataTrust) source) :
    metadataTrust.atom (.config anchor.authority anchor.context) h.config.name ∧
    metadataTrust.policy anchor.authority anchor.context h.policy := by
  rw [← binding.contextMatches]
  exact ⟨atomHasIndependentSource h.config,source.policyAuthentic _ _ _ h.policySelected⟩

-- Source references and complete commitments, including Q leaf references,
-- occur in keys. A content alias cannot be looked up by ticket name alone.
structure Entry {metadataTrust} (source : Metadata metadataTrust) (isc : Ref)
    (vocabulary : Vocabulary) (commitment : Commitment) where
  ticket : String
  ticketSelected : vocabulary.ticket commitment.ticket = some ticket
  content : Atom source (.content isc commitment)

def loadEntry {metadataTrust} (source : Metadata metadataTrust) (isc : Ref)
    (vocabulary : Vocabulary) (commitment : Commitment) : Option (Entry source isc vocabulary commitment) := do
  match ht : vocabulary.ticket commitment.ticket with
  | none => none
  | some ticket =>
      let content ← loadAtom source (.content isc commitment)
      some ⟨ticket,ht,content⟩

def record (fields : List (String × Value)) : Value :=
  .function (PublicArithmeticInputs.entries (fields.map (fun (k,v) => (.text k,v))))

def Entry.value {metadataTrust source isc vocabulary commitment}
    (entry : Entry (metadataTrust := metadataTrust) source isc vocabulary commitment) : Value :=
  record [("content",entry.content.value),("ticket",.model entry.ticket)]

inductive EntriesFor {metadataTrust} (source : Metadata metadataTrust) (isc : Ref) (vocabulary : Vocabulary) :
    List Commitment → List Value → Prop where
  | nil : EntriesFor source isc vocabulary [] []
  | cons {commitment commitments values} (entry : Entry source isc vocabulary commitment)
      (tail : EntriesFor source isc vocabulary commitments values) :
      EntriesFor source isc vocabulary (commitment :: commitments) (entry.value :: values)

def loadEntries {metadataTrust} (source : Metadata metadataTrust) (isc : Ref) (vocabulary : Vocabulary) :
    (commitments : List Commitment) → Option {values : List Value // EntriesFor source isc vocabulary commitments values}
  | [] => some ⟨[],.nil⟩
  | commitment :: rest => do
      let entry ← loadEntry source isc vocabulary commitment
      let tail ← loadEntries source isc vocabulary rest
      some ⟨entry.value :: tail.val,.cons entry tail.property⟩

theorem entriesRetainCount {metadataTrust source isc vocabulary commitments values}
    (h : EntriesFor (metadataTrust := metadataTrust) source isc vocabulary commitments values) :
    values.length = commitments.length := by
  induction h with
  | nil => rfl
  | cons entry tail ih => simp [ih]

theorem entryAtHasFullCommitment {metadataTrust source isc vocabulary commitments values}
    (h : EntriesFor (metadataTrust := metadataTrust) source isc vocabulary commitments values)
    (index : Nat) (value : Value) (found : values[index]? = some value) :
    ∃ commitment, commitments[index]? = some commitment ∧
      ∃ entry : Entry source isc vocabulary commitment, value = entry.value ∧
        metadataTrust.atom (.content isc commitment) entry.content.name := by
  induction h generalizing index value with
  | nil => simp at found
  | cons entry tail ih =>
      cases index with
      | zero => simp only [List.getElem?_cons_zero,Option.some.injEq] at found
                exact ⟨_,rfl,entry,found.symm,atomHasIndependentSource entry.content⟩
      | succ index => exact ih index value found

def values : List Value → Values
  | [] => .nil
  | x :: xs => .cons x (values xs)

def valuesList : Values → List Value
  | .nil => []
  | .cons x xs => x :: valuesList xs

theorem valuesInverse (xs : List Value) : valuesList (values xs) = xs := by
  induction xs with
  | nil => rfl
  | cons x xs ih => simp [values,valuesList,ih]

def setValue (xs : List Value) : Value :=
  .set (values ((sortEntries (xs.map (fun x => (x,x)))).map Prod.fst))

theorem setRetainsAllValues (xs : List Value) :
    ∃ v, setValue xs = .set v ∧ (valuesList v).Perm xs := by
  refine ⟨_,rfl,?_⟩
  rw [valuesInverse]
  have h := (sortEntriesPerm (xs.map (fun x => (x,x)))).map Prod.fst
  have same : (xs.map (fun x => (x,x))).map Prod.fst = xs := by
    clear h
    induction xs with
    | nil => rfl
    | cons x xs ih => simp only [List.map_cons,ih]
  rw [same] at h
  exact h

def authorityFieldNames : List String :=
  ["apc","applyProfile","ec","inputs","isc","model","optimizer","parent","profile","schema"]

-- Pure constructors have no authentication claim by themselves. Their checked
-- source-bound use below computes every argument rather than accepting bodies.
def roundValue (height epoch : Value) : Value := record [("epoch",epoch),("height",height)]
def iscValue (round config : Value) (policy : ClosePolicy) (entries : Value) : Value :=
  record [("canonicalRoot",entries),("config",config),("entries",entries),("policy",.text policy.text),("round",round)]
def seedValue (isc epoch seed : Value) : Value := record [("epoch",epoch),("isc",isc),("value",seed)]
def ecValue (isc seed members norm : Value) : Value :=
  record [("isc",isc),("members",members),("normEvidence",norm),("seed",seed)]
def apcValue (isc seed ec members coefficient : Value) : Value :=
  record [("coefficientProfile",coefficient),("ec",ec),("isc",isc),("members",members),("seed",seed)]
def vectorValue (kind : String) (schema cells : Value) : Value :=
  record [("kind",.text kind),("schema",schema),("values",cells)]

structure Projection {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : Corpus binding} {limit : ModelLimit} (input : Projected corpus limit)
    (vocabulary : Vocabulary) {metadataTrust} (source : Metadata metadataTrust) where
  encoded : Encoded vocabulary (image input)
  header : Header binding source
  entryValues : List Value
  entryOrigin : EntriesFor source binding.authority.isc vocabulary corpus.frame.commitments entryValues
  memberNames : List String
  members : collect vocabulary.ticket corpus.frame.members = some memberNames
  memberUnique : memberNames.Nodup
  memberConfigured : ∀ name ∈ memberNames, name ∈ vocabulary.tickets
  eligibleNames : List String
  eligible : collect vocabulary.ticket corpus.frame.eligible = some eligibleNames
  eligibleUnique : eligibleNames.Nodup

def Projection.round {codec store trust anchor binding corpus limit input vocabulary metadataTrust source}
    (p : Projection (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (corpus := corpus) (limit := limit) input vocabulary (metadataTrust := metadataTrust) source) : Value :=
  roundValue p.header.height.value p.header.epoch.value

def Projection.isc {codec store trust anchor binding corpus limit input vocabulary metadataTrust source}
    (p : Projection (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (corpus := corpus) (limit := limit) input vocabulary (metadataTrust := metadataTrust) source) : Value :=
  iscValue p.round p.header.config.value p.header.policy (setValue p.entryValues)

def Projection.seed {codec store trust anchor binding corpus limit input vocabulary metadataTrust source}
    (p : Projection (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (corpus := corpus) (limit := limit) input vocabulary (metadataTrust := metadataTrust) source) : Value :=
  seedValue p.isc p.header.epoch.value p.header.seed.value

def Projection.ec {codec store trust anchor binding corpus limit input vocabulary metadataTrust source}
    (p : Projection (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (corpus := corpus) (limit := limit) input vocabulary (metadataTrust := metadataTrust) source) : Value :=
  ecValue p.isc p.seed (setValue (p.eligibleNames.map Value.model)) p.header.norm.value

def Projection.apc {codec store trust anchor binding corpus limit input vocabulary metadataTrust source}
    (p : Projection (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (corpus := corpus) (limit := limit) input vocabulary (metadataTrust := metadataTrust) source) : Value :=
  apcValue p.isc p.seed p.ec (setValue (p.eligibleNames.map Value.model)) p.header.coefficient.value

def Projection.fields {codec store trust anchor binding corpus limit input vocabulary metadataTrust source}
    (p : Projection (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (corpus := corpus) (limit := limit) input vocabulary (metadataTrust := metadataTrust) source) : List (String × Value) := [
  ("apc",p.apc),("applyProfile",p.header.applyProfile.value),("ec",p.ec),("inputs",p.encoded.value),("isc",p.isc),
  ("model",vectorValue "MODEL" p.header.schema.value (p.encoded.components.at 9)),
  ("optimizer",vectorValue "OPTIMIZER" p.header.schema.value (p.encoded.components.at 10)),
  ("parent",p.header.parent.value),("profile",p.header.profile.value),("schema",p.header.schema.value)]

def Projection.value {codec store trust anchor binding corpus limit input vocabulary metadataTrust source}
    (p : Projection (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (corpus := corpus) (limit := limit) input vocabulary (metadataTrust := metadataTrust) source) : Value := record p.fields

def project {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : Corpus binding} {limit : ModelLimit} (input : Projected corpus limit)
    (vocabulary : Vocabulary) {metadataTrust} (source : Metadata metadataTrust) :
    Option (Projection input vocabulary source) := do
  let encoded ← encodeProjected vocabulary input
  let header ← loadHeader binding source
  let entryValues ← loadEntries source binding.authority.isc vocabulary corpus.frame.commitments
  match hm : collect vocabulary.ticket corpus.frame.members, he : collect vocabulary.ticket corpus.frame.eligible with
  | some members, some eligible =>
      if valid : members.Nodup ∧ (∀ name ∈ members, name ∈ vocabulary.tickets) ∧ eligible.Nodup then
        some ⟨encoded,header,entryValues.val,entryValues.property,members,hm,valid.1,valid.2.1,eligible,he,valid.2.2⟩
      else none
  | _,_ => none

structure Checked {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : Corpus binding} {limit : ModelLimit} (input : Projected corpus limit)
    (vocabulary : Vocabulary) {metadataTrust} (source : Metadata metadataTrust) where
  projection : Projection input vocabulary source
  canonical : PublicState.canonical vocabulary.models projection.value = true

def check {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : Corpus binding} {limit : ModelLimit} (input : Projected corpus limit)
    (vocabulary : Vocabulary) {metadataTrust} (source : Metadata metadataTrust) (candidate : Value) :
    Option (Checked input vocabulary source) := do
  let p ← project input vocabulary source
  if valid : PublicState.canonical vocabulary.models p.value = true ∧ candidate = p.value then
    some ⟨p,valid.1⟩
  else none

theorem checkedWholeAuthority {codec store trust anchor binding corpus limit input vocabulary metadataTrust source candidate checked}
    (h : check (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (corpus := corpus) (limit := limit) input vocabulary
      (metadataTrust := metadataTrust) source candidate = some checked) : candidate = checked.projection.value := by
  unfold check at h
  cases hp : project input vocabulary source with
  | none => simp [hp] at h
  | some p =>
    simp only [hp,Bind.bind,Option.bind] at h
    split at h
    · rename_i valid; cases h; exact valid.2
    · contradiction

section SourceProperties
variable {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : Corpus binding} {limit : ModelLimit} {input : Projected corpus limit}
    {vocabulary : Vocabulary} {metadataTrust} {source : Metadata metadataTrust}
    (p : Projection input vocabulary source)

theorem completeAuthorityInventory : p.fields.map Prod.fst = authorityFieldNames := rfl

theorem authorityHasAllCheckedInputs : readField p.value "inputs" = some p.encoded.value := by rfl

theorem authorityHasOriginalParent : readField p.value "parent" = some p.header.parent.value ∧
    metadataTrust.atom (.parent anchor.context.parentCheckpoint) p.header.parent.name := by
  refine ⟨rfl,?_⟩
  rw [← binding.contextMatches]
  exact atomHasIndependentSource p.header.parent

theorem authorityHasBoundSchemaAndProfiles :
    metadataTrust.atom (.schema binding.authority.schema) p.header.schema.name ∧
    metadataTrust.atom (.profile binding.authority.profile) p.header.profile.name ∧
    metadataTrust.atom (.applyProfile binding.authority.profile) p.header.applyProfile.name :=
  ⟨atomHasIndependentSource p.header.schema,atomHasIndependentSource p.header.profile,
    atomHasIndependentSource p.header.applyProfile⟩

theorem coefficientUsesBothAPCAndPlan :
    metadataTrust.atom (.coefficient binding.authority.apc binding.authority.plan) p.header.coefficient.name :=
  atomHasIndependentSource p.header.coefficient

theorem seedAndNormUseNativeParents :
    metadataTrust.atom (.seed binding.authority.isc binding.authority.context.epoch) p.header.seed.name ∧
    metadataTrust.atom (.norm binding.authority.ec) p.header.norm.name :=
  ⟨atomHasIndependentSource p.header.seed,atomHasIndependentSource p.header.norm⟩

theorem exactConstructedParentChain :
    readField p.apc "ec" = some p.ec ∧ readField p.apc "isc" = some p.isc ∧
    readField p.ec "isc" = some p.isc ∧ readField p.seed "isc" = some p.isc ∧
    readField p.apc "seed" = some p.seed ∧ readField p.ec "seed" = some p.seed :=
  ⟨rfl,rfl,rfl,rfl,rfl,rfl⟩

theorem canonicalISCRootIsExactEntrySet :
    readField p.isc "canonicalRoot" = some (setValue p.entryValues) ∧
    readField p.isc "entries" = some (setValue p.entryValues) := ⟨rfl,rfl⟩

theorem allNativeCommitmentsRetained : p.entryValues.length = corpus.frame.commitments.length :=
  entriesRetainCount p.entryOrigin

theorem completeISCArtifactOrigin :
    ∃ bytes, Resolves codec store binding.authority.isc bytes
      (.isc corpus.frame.members corpus.frame.commitments) := corpus.origin.isc

theorem nativeParentEdgesChecked :
    corpus.frame.ecIsc = binding.authority.isc ∧ corpus.frame.apcEc = binding.authority.ec ∧
    corpus.frame.apcPlan = binding.authority.plan := by
  have valid := corpus.valid
  simp only [ParameterFrameValid] at valid
  rcases valid with ⟨_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,a,b,c,_⟩
  exact ⟨a,b,c⟩

theorem completeNativeParentPayloads :
    (∃ bytes, Resolves codec store binding.authority.ec bytes (.ec binding.authority.isc corpus.frame.eligible)) ∧
    (∃ bytes, Resolves codec store binding.authority.apc bytes (.apc binding.authority.ec binding.authority.plan)) := by
  obtain ⟨isc,ec,plan⟩ := nativeParentEdgesChecked (corpus := corpus)
  constructor
  · simpa only [isc] using corpus.origin.ec
  · simpa only [ec,plan] using corpus.origin.apc

theorem eligibleMemberSource (index : Nat) (name : String)
    (found : p.eligibleNames[index]? = some name) :
    ∃ ticket, corpus.frame.eligible[index]? = some ticket ∧ vocabulary.ticket ticket = some name :=
  collectAt p.eligible index name found

theorem committedMemberSource (index : Nat) (name : String)
    (found : p.memberNames[index]? = some name) :
    ∃ ticket, corpus.frame.members[index]? = some ticket ∧ vocabulary.ticket ticket = some name :=
  collectAt p.members index name found

theorem eligibleSetsAreIdentical : readField p.ec "members" = readField p.apc "members" := rfl

theorem currentTablesFromBoundVectors :
    currentTable vocabulary.shard input.model.cells = some (p.encoded.components.at 9) ∧
    currentTable vocabulary.shard input.optimizer.cells = some (p.encoded.components.at 10) := by
  have model := componentIsComputed p.encoded.components 9
  have optimizer := componentIsComputed p.encoded.components 10
  constructor
  · change some (currentTable vocabulary.shard input.model.cells) =
      some (some (p.encoded.components.at 9)) at model
    exact Option.some.inj model
  · change some (currentTable vocabulary.shard input.optimizer.cells) =
      some (some (p.encoded.components.at 10)) at optimizer
    exact Option.some.inj optimizer

theorem structuredCurrentValuesShareSchema :
    readField p.value "model" = some (vectorValue "MODEL" p.header.schema.value (p.encoded.components.at 9)) ∧
    readField p.value "optimizer" = some (vectorValue "OPTIMIZER" p.header.schema.value (p.encoded.components.at 10)) :=
  ⟨rfl,rfl⟩

theorem authorityEntriesPreserveSource (index : Nat) (value : Value)
    (found : p.entryValues[index]? = some value) :
    ∃ commitment, corpus.frame.commitments[index]? = some commitment ∧
      ∃ entry : Entry source binding.authority.isc vocabulary commitment,
        value = entry.value ∧ metadataTrust.atom (.content binding.authority.isc commitment) entry.content.name :=
  entryAtHasFullCommitment p.entryOrigin index value found

end SourceProperties

theorem contentKeyCannotEraseLeafSubstitution {isc : Ref} {first second : Commitment}
    (different : first.leaves ≠ second.leaves) : AtomKey.content isc first ≠ .content isc second := by
  intro same
  cases same
  exact different rfl

theorem contentKeyCannotEraseISCRoot {first second : Ref} (different : first ≠ second)
    (commitment : Commitment) : AtomKey.content first commitment ≠ .content second commitment := by
  intro same
  cases same
  exact different rfl

end DeltaReduce.PublicAuthority
