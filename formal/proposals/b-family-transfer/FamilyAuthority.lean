import FamilyInputs
import DeltaReduce.PublicAuthority
import DeltaReduce.PublicPlanningBody

/-! R2 family input/body integration. Reuses the existing primitive metadata
boundary and full public constructors; no new certificates or identities. -/
namespace DeltaReduce.FamilyAuthority
open NativeBinding NativeInputProjection PublicState PublicArithmeticInputs PublicAuthority

theorem configuredAlias {nameMap names configured name}
    (checked : checkNamespace nameMap names configured = true) (member : name ∈ names) :
    ∃ publicName, nameMap name = some publicName ∧ publicName ∈ configured := by
  obtain ⟨projected,computed,permutation,_⟩ := namespaceCheckSound checked
  obtain ⟨i,atName⟩ := List.mem_iff_getElem?.mp member
  have inside : i < projected.length := by
    rw [collectLength computed]; exact (List.getElem?_eq_some_iff.mp atName).1
  obtain ⟨source,atSource,aliased⟩ := collectAt computed i projected[i] (List.getElem?_eq_getElem inside)
  have same := Option.some.inj (atSource.symm.trans atName)
  exact ⟨projected[i],by simpa only [same] using aliased,
    permutation.mem_iff.mp (List.getElem_mem inside)⟩

theorem collectedValueSource {α β} {f : α → Option β} {xs ys}
    (h : collect f xs = some ys) {y} (member : y ∈ ys) : ∃ x ∈ xs, f x = some y := by
  obtain ⟨index,atValue⟩ := List.mem_iff_getElem?.mp member
  obtain ⟨x,atSource,computed⟩ := collectAt h index y atValue
  exact ⟨x,List.mem_of_getElem? atSource,computed⟩

structure Projection {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : FamilyInputs.Corpus binding} {choice : FamilyInputs.Choice corpus.frame} {limit : Int} (input : FamilyInputs.Projected corpus choice limit)
    (vocabulary : Vocabulary) {metadataTrust} (source : Metadata metadataTrust) where
  completion : FamilyInputs.Completed (FamilyInputs.image input)
  encoded : Encoded vocabulary (FamilyInputs.completedImage (FamilyInputs.image input) completion.configured)
  header : Header binding source
  entryValues : List Value
  entryOrigin : EntriesFor source binding.authority.isc vocabulary corpus.frame.commitments entryValues
  memberNames : List String
  members : collect vocabulary.ticket corpus.frame.members = some memberNames
  memberUnique : memberNames.Nodup
  memberConfigured : ∀ name ∈ memberNames, name ∈ vocabulary.tickets
  memberSources : ∀ ticket ∈ corpus.frame.members, ticket ∈ completion.configured.map (·.id)
  eligibleNames : List String
  eligible : collect vocabulary.ticket corpus.frame.eligible = some eligibleNames
  eligibleUnique : eligibleNames.Nodup

def Projection.round {codec store trust anchor binding corpus choice limit input vocabulary metadataTrust source}
    (p : Projection (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (corpus := corpus) (choice := choice) (limit := limit) input vocabulary (metadataTrust := metadataTrust) source) : Value :=
  roundValue p.header.height.value p.header.epoch.value

def Projection.isc {codec store trust anchor binding corpus choice limit input vocabulary metadataTrust source}
    (p : Projection (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (corpus := corpus) (choice := choice) (limit := limit) input vocabulary (metadataTrust := metadataTrust) source) : Value :=
  iscValue p.round p.header.config.value p.header.policy (setValue p.entryValues)

def Projection.seed {codec store trust anchor binding corpus choice limit input vocabulary metadataTrust source}
    (p : Projection (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (corpus := corpus) (choice := choice) (limit := limit) input vocabulary (metadataTrust := metadataTrust) source) : Value :=
  seedValue p.isc p.header.epoch.value p.header.seed.value

def Projection.ec {codec store trust anchor binding corpus choice limit input vocabulary metadataTrust source}
    (p : Projection (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (corpus := corpus) (choice := choice) (limit := limit) input vocabulary (metadataTrust := metadataTrust) source) : Value :=
  ecValue p.isc p.seed (setValue (p.eligibleNames.map Value.model)) p.header.norm.value

def Projection.apc {codec store trust anchor binding corpus choice limit input vocabulary metadataTrust source}
    (p : Projection (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (corpus := corpus) (choice := choice) (limit := limit) input vocabulary (metadataTrust := metadataTrust) source) : Value :=
  apcValue p.isc p.seed p.ec (setValue (p.eligibleNames.map Value.model)) p.header.coefficient.value

def Projection.fields {codec store trust anchor binding corpus choice limit input vocabulary metadataTrust source}
    (p : Projection (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (corpus := corpus) (choice := choice) (limit := limit) input vocabulary (metadataTrust := metadataTrust) source) : List (String × Value) := [
  ("apc",p.apc),("applyProfile",p.header.applyProfile.value),("ec",p.ec),("inputs",p.encoded.value),("isc",p.isc),
  ("model",vectorValue "MODEL" p.header.schema.value (p.encoded.components.at 9)),
  ("optimizer",vectorValue "OPTIMIZER" p.header.schema.value (p.encoded.components.at 10)),
  ("parent",p.header.parent.value),("profile",p.header.profile.value),("schema",p.header.schema.value)]

def Projection.value {codec store trust anchor binding corpus choice limit input vocabulary metadataTrust source}
    (p : Projection (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (corpus := corpus) (choice := choice) (limit := limit) input vocabulary (metadataTrust := metadataTrust) source) : Value := record p.fields

def project {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : FamilyInputs.Corpus binding} {choice : FamilyInputs.Choice corpus.frame} {limit : Int} (input : FamilyInputs.Projected corpus choice limit)
    (vocabulary : Vocabulary) {metadataTrust} (source : Metadata metadataTrust)
    (configured : List Ticket := corpus.frame.plan.tickets) :
    Option (Projection input vocabulary source) := do
  let completion ← FamilyInputs.complete (FamilyInputs.image input) configured
  let encoded ← encodeImage vocabulary (FamilyInputs.completedImage (FamilyInputs.image input) completion.configured)
  let header ← loadHeader binding source
  let entryValues ← PublicAuthority.loadEntries source binding.authority.isc vocabulary corpus.frame.commitments
  match hm : collect vocabulary.ticket corpus.frame.members, he : collect vocabulary.ticket corpus.frame.eligible with
  | some members, some eligible =>
      if valid : members.Nodup ∧ (∀ name ∈ members, name ∈ vocabulary.tickets) ∧
          (∀ ticket ∈ corpus.frame.members, ticket ∈ completion.configured.map (·.id)) ∧ eligible.Nodup then
        some ⟨completion,encoded,header,entryValues.val,entryValues.property,members,hm,valid.1,valid.2.1,
          valid.2.2.1,eligible,he,valid.2.2.2⟩
      else none
  | _,_ => none

theorem projectedConfiguration {codec store trust anchor binding corpus choice limit input vocabulary metadataTrust source configured out}
    (accepted : project (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (corpus := corpus) (choice := choice) (limit := limit) input vocabulary
      (metadataTrust := metadataTrust) source configured = some out) :
    out.completion.configured = configured := by
  simp only [project,bind,Option.bind_eq_some_iff] at accepted
  obtain ⟨completion,hc,encoded,_,header,_,entryValues,_,last⟩ := accepted
  split at last <;> try contradiction
  split at last <;> try contradiction
  cases Option.some.inj last
  exact (FamilyInputs.completionCheckedExactly hc).1

structure Checked {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : FamilyInputs.Corpus binding} {choice : FamilyInputs.Choice corpus.frame} {limit : Int} (input : FamilyInputs.Projected corpus choice limit)
    (vocabulary : Vocabulary) {metadataTrust} (source : Metadata metadataTrust) where
  projection : Projection input vocabulary source
  canonical : PublicState.canonical vocabulary.models projection.value = true

def check {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : FamilyInputs.Corpus binding} {choice : FamilyInputs.Choice corpus.frame} {limit : Int} (input : FamilyInputs.Projected corpus choice limit)
    (vocabulary : Vocabulary) {metadataTrust} (source : Metadata metadataTrust) (candidate : Value)
    (configured : List Ticket := corpus.frame.plan.tickets) :
    Option (Checked input vocabulary source) := do
  let p ← project input vocabulary source configured
  if valid : PublicState.canonical vocabulary.models p.value = true ∧ candidate = p.value then
    some ⟨p,valid.1⟩
  else none

theorem checkedWholeAuthority {codec store trust anchor binding corpus choice limit input vocabulary metadataTrust source candidate checked}
    (h : check (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (corpus := corpus) (choice := choice) (limit := limit) input vocabulary
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
    {corpus : FamilyInputs.Corpus binding} {choice : FamilyInputs.Choice corpus.frame} {limit : Int} {input : FamilyInputs.Projected corpus choice limit}
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

include p in
theorem domainAliasComplete {domain : String} (member : domain ∈ NativeBinding.domains binding.profile) :
    ∃ name, vocabulary.domain domain = some name ∧ name ∈ vocabulary.domains :=
  configuredAlias p.encoded.components.domainSet member

include p in
theorem shardAliasComplete {shard : String} (member : shard ∈ shardIds corpus.frame) :
    ∃ name, vocabulary.shard shard = some name ∧ name ∈ vocabulary.shards :=
  configuredAlias p.encoded.components.shardSet member

include p in
theorem currentTableTotal (values : List Int) (shape : values.length = corpus.frame.coordinates.length) :
    ∃ cells table, FamilyInputs.selectedCurrent corpus.frame choice values = some cells ∧
      currentTable vocabulary.shard cells = some table := by
  let layout := StateFamily.ofValidated corpus.valid
  let cells := (List.finRange corpus.frame.shards.length).map (fun s =>
    (corpus.frame.shards[s.val].id,(StateFamily.family layout () values shape).view choice s))
  have selected : FamilyInputs.selectedCurrent corpus.frame choice values = some cells :=
    FamilyInputs.selectedCurrentIsFamily layout choice values shape ()
  have total : ∀ c ∈ cells, ∃ name, vocabulary.shard c.1 = some name := by
    intro c hc
    obtain ⟨s,_,same⟩ := List.mem_map.mp hc
    subst c
    obtain ⟨name,hn,_⟩ := shardAliasComplete p (List.mem_map.mpr ⟨_,List.getElem_mem s.isLt,rfl⟩)
    exact ⟨name,hn⟩
  have possible : ∀ c ∈ cells, ∃ pair : Value × Value,
      (do let name ← vocabulary.shard c.1; pure (.model name,.integer c.2)) = some pair := by
    intro c hc
    obtain ⟨name,hn⟩ := total c hc
    exact ⟨(.model name,.integer c.2),by simp [hn]⟩
  obtain ⟨pairs,hpairs⟩ := FamilyInputs.collectExists _ cells possible
  exact ⟨cells,function pairs,selected,by
    change (collect (fun c => do let name ← vocabulary.shard c.1; pure (.model name,.integer c.2)) cells >>=
      fun ps => some (function ps)) = some (function pairs)
    rw [hpairs]; rfl⟩

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

/- Exact remaining coverage boundary of this constructor, not a new protocol
guard. Its input image currently contains eligible tickets. A committed but
omitted ticket cannot disappear by being renamed to another eligible ticket.
Supporting OMIT_UNAVAILABLE therefore requires full configured ticket inputs
(or the existing contract's justified latent-input completion), not an alias
collision or a certificate with a changed member set. -/
include p in
theorem omittedMemberRequiresInputCompletion {ticket}
    (member : ticket ∈ corpus.frame.members) (omitted : ticket ∉ corpus.frame.eligible)
    (eligibleOnly : p.completion.configured = corpus.frame.plan.tickets)
    (distinct : ∀ a ∈ corpus.frame.members, ∀ b ∈ corpus.frame.members,
      vocabulary.ticket a = vocabulary.ticket b → a = b) : False := by
  obtain ⟨index,atTicket⟩ := List.mem_iff_getElem?.mp member
  have inside : index < p.memberNames.length := by
    rw [collectLength p.members]; exact (List.getElem?_eq_some_iff.mp atTicket).1
  obtain ⟨original,atOriginal,aliased⟩ := collectAt p.members index p.memberNames[index]
    (List.getElem?_eq_getElem inside)
  have originalSame := Option.some.inj (atOriginal.symm.trans atTicket)
  subst original
  obtain ⟨names,encoded,permutation,_⟩ := namespaceCheckSound p.encoded.components.ticketSet
  have configured := p.memberConfigured p.memberNames[index] (List.getElem_mem inside)
  have inNames := permutation.mem_iff.mpr configured
  obtain ⟨eligible,inEligible,sameAlias⟩ := collectedValueSource encoded inNames
  change eligible ∈ (FamilyInputs.completeTickets _ p.completion.configured input.tickets).map (·.ticket) at inEligible
  rw [FamilyInputs.completionExactUniverse,eligibleOnly] at inEligible
  have eligibleOrder := input.ticketsLoaded
  have names : corpus.frame.plan.tickets.map (·.id) = corpus.frame.eligible := by
    rw [← FamilyInputs.projectedTicketNames input]
    exact (FamilyInputs.collectedKeys eligibleOrder (fun _ _ h => (derivedTicketSource h).1)).symm
  rw [names] at inEligible
  have inMembers := corpus.valid.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.1 eligible inEligible
  have same := distinct ticket member eligible inMembers (aliased.trans sameAlias.symm)
  exact omitted (same ▸ inEligible)

theorem eligibleSetsAreIdentical : readField p.ec "members" = readField p.apc "members" := rfl

theorem currentTablesFromBoundVectors :
    currentTable vocabulary.shard input.model = some (p.encoded.components.at 9) ∧
    currentTable vocabulary.shard input.optimizer = some (p.encoded.components.at 10) := by
  have model := componentIsComputed p.encoded.components 9
  have optimizer := componentIsComputed p.encoded.components 10
  constructor
  · change some (currentTable vocabulary.shard input.model) =
      some (some (p.encoded.components.at 9)) at model
    exact Option.some.inj model
  · change some (currentTable vocabulary.shard input.optimizer) =
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


theorem canonicalLookup {models key value xs}
    (safe : canonicalEntries models xs = true) (found : functionLookup key xs = some value) :
    canonical models value = true := by
  cases xs with
  | nil => simp [functionLookup] at found
  | cons k v xs =>
    simp only [canonicalEntries,Bool.and_eq_true] at safe
    simp only [functionLookup] at found
    split at found
    · cases Option.some.inj found; exact safe.1.2
    · exact canonicalLookup safe.2 found

theorem canonicalField {models body name value}
    (safe : canonical models body = true) (found : readField body name = some value) :
    canonical models value = true := by
  cases body <;> simp only [readField,readFunction] at found
  all_goals try contradiction
  rename_i xs
  have parts : canonicalEntries models xs = true ∧ ordered (keys xs) = true := by
    simpa only [canonical,Bool.and_eq_true] using safe
  exact canonicalLookup parts.1 found

theorem recordKeys (fields : List (String × Value)) :
    keys (entries (fields.map (fun (k,v) => (.text k,v)))) = fields.map (fun p => encode (.text p.1)) := by
  induction fields with
  | nil => rfl
  | cons p ps ih => cases p; simp only [List.map_cons,entries,keys,ih]

theorem canonicalRecord (models : List String) (fields : List (String × Value))
    (safe : ∀ f ∈ fields, canonical models (.text f.1) = true ∧ canonical models f.2 = true)
    (orderedKeys : ordered (fields.map (fun p => encode (.text p.1))) = true) :
    canonical models (record fields) = true := by
  change (canonicalEntries models (entries (fields.map (fun (k,v) => (.text k,v)))) &&
    ordered (keys (entries (fields.map (fun (k,v) => (.text k,v)))))) = true
  rw [recordKeys,orderedKeys,Bool.and_true]
  clear orderedKeys
  induction fields with
  | nil => rfl
  | cons p ps ih =>
    have head := safe p List.mem_cons_self
    have tail := ih (fun f hf => safe f (List.mem_cons_of_mem _ hf))
    cases p
    simp only [List.map_cons,entries,canonicalEntries,head.1,head.2,tail,Bool.and_self]


def encodedKey (p : Value × Value) := encode p.1

theorem insertKeysOrdered (row : Value × Value) (rows : List (Value × Value))
    (sorted : rows.Pairwise (fun a b => encodedKey a < encodedKey b))
    (fresh : ∀ r ∈ rows, encodedKey row ≠ encodedKey r) :
    (insertEntry row rows).Pairwise (fun a b => encodedKey a < encodedKey b) := by
  induction rows with
  | nil => simp [insertEntry]
  | cons first rest ih =>
    have head := List.pairwise_cons.mp sorted
    unfold insertEntry
    split
    · rename_i less
      have lt : encodedKey row < encodedKey first := (byteLessCorrect _ _).mp less
      apply List.pairwise_cons.mpr
      refine ⟨?_,sorted⟩
      intro r member
      rcases List.mem_cons.mp member with same | member
      · subst r; exact lt
      · exact List.lex_trans (fun a b => UInt8.lt_trans a b) lt (head.1 r member)
    · rename_i notLess
      have greater : encodedKey first < encodedKey row := by
        by_contra rejected
        have same : encodedKey row = encodedKey first := Std.Trichotomous.trichotomous _ _
          (fun h => notLess ((byteLessCorrect _ _).mpr h)) rejected
        exact fresh first List.mem_cons_self same
      apply List.pairwise_cons.mpr
      refine ⟨?_,ih head.2 (fun r hr => fresh r (List.mem_cons_of_mem _ hr))⟩
      intro r member
      have original := (insertEntryPerm row rest).mem_iff.mp member
      rcases List.mem_cons.mp original with same | member
      · subst r; exact greater
      · exact head.1 r member

theorem sortedKeysOrdered (rows : List (Value × Value)) (unique : (rows.map encodedKey).Nodup) :
    (sortEntries rows).Pairwise (fun a b => encodedKey a < encodedKey b) := by
  induction rows with
  | nil => simp [sortEntries]
  | cons row rest ih =>
    have nodup : encodedKey row ∉ rest.map encodedKey ∧ (rest.map encodedKey).Nodup := by simpa using unique
    apply insertKeysOrdered row (sortEntries rest) (ih nodup.2)
    intro r member same
    exact nodup.1 (List.mem_map.mpr ⟨r,(sortEntriesPerm rest).mem_iff.mp member,same.symm⟩)

theorem canonicalSet (models : List String) (xs : List Value)
    (safe : ∀ x ∈ xs, canonical models x = true) (unique : (xs.map encode).Nodup) :
    canonical models (setValue xs) = true := by
  let rows := sortEntries (xs.map (fun x => (x,x)))
  have same : (rows.map Prod.fst).Perm xs := by
    have h := (sortEntriesPerm (xs.map (fun x => (x,x)))).map Prod.fst
    have identity : (xs.map (fun x => (x,x))).map Prod.fst = xs := by
      rw [List.map_map]
      change xs.map id = xs
      exact List.map_id xs
    rw [identity] at h
    exact h
  have orderedRows : rows.Pairwise (fun a b => encodedKey a < encodedKey b) := by
    apply sortedKeysOrdered
    simpa only [List.map_map,encodedKey,Function.comp_def] using unique
  change (canonicalValues models (PublicAuthority.values (rows.map Prod.fst)) &&
    ordered (encodeValues (PublicAuthority.values (rows.map Prod.fst)))) = true
  have canonicalList : ∀ vs : List Value, (∀ v ∈ vs, canonical models v = true) →
      canonicalValues models (PublicAuthority.values vs) = true := by
    intro vs hs
    induction vs with
    | nil => rfl
    | cons v vs ih =>
      simp only [PublicAuthority.values,canonicalValues,hs v List.mem_cons_self,
        ih (fun x hx => hs x (List.mem_cons_of_mem _ hx)),Bool.and_self]
  have listEncoding : ∀ vs : List Value, encodeValues (PublicAuthority.values vs) = vs.map encode := by
    intro vs
    induction vs with
    | nil => rfl
    | cons v vs ih => simp only [PublicAuthority.values,encodeValues,List.map_cons,ih]
  rw [canonicalList _ (fun v hv => safe v (same.mem_iff.mp hv)),listEncoding,Bool.true_and,orderedCorrect]
  simpa only [List.pairwise_map,encodedKey] using orderedRows

theorem pairKeys (rows : List (Value × Value)) :
    keys (entries rows) = rows.map encodedKey := by
  induction rows with
  | nil => rfl
  | cons p ps ih => cases p; simp only [entries,keys,List.map_cons,encodedKey,ih]

theorem pairCanonical (models : List String) (rows : List (Value × Value)) :
    canonicalEntries models (entries rows) = true ↔
      ∀ row ∈ rows, canonical models row.1 = true ∧ canonical models row.2 = true := by
  induction rows with
  | nil => simp [entries,canonicalEntries]
  | cons p ps ih => cases p; simp [entries,canonicalEntries,ih,Bool.and_eq_true]

theorem functionCanonicalParts {models rows}
    (h : canonical models (function rows) = true) :
    (∀ row ∈ rows, canonical models row.1 = true ∧ canonical models row.2 = true) ∧
    (rows.map encodedKey).Nodup := by
  change (canonicalEntries models (entries (sortEntries rows)) && ordered (keys (entries (sortEntries rows)))) = true at h
  have both : canonicalEntries models (entries (sortEntries rows)) = true ∧ ordered (keys (entries (sortEntries rows))) = true := by simpa only [Bool.and_eq_true] using h
  have pairs := (pairCanonical models (sortEntries rows)).mp both.1
  have order := (orderedCorrect _).mp (by simpa only [pairKeys] using both.2)
  refine ⟨fun r hr => pairs r ((sortEntriesPerm rows).mem_iff.mpr hr),?_⟩
  have unique : (List.map encodedKey (sortEntries rows)).Nodup := order.imp (fun {a b} less eq => by subst b; exact List.lex_irrefl UInt8.lt_irrefl a less)
  exact ((sortEntriesPerm rows).map encodedKey).nodup_iff.mp unique

theorem functionCanonicalFromParts (models : List String) (rows : List (Value × Value))
    (safe : ∀ row ∈ rows, canonical models row.1 = true ∧ canonical models row.2 = true)
    (unique : (rows.map encodedKey).Nodup) : canonical models (function rows) = true := by
  change (canonicalEntries models (entries (sortEntries rows)) && ordered (keys (entries (sortEntries rows)))) = true
  rw [Bool.and_eq_true]
  constructor
  · exact (pairCanonical models _).mpr (fun r hr => safe r ((sortEntriesPerm rows).mem_iff.mp hr))
  · rw [pairKeys,orderedCorrect]
    simpa only [List.pairwise_map] using sortedKeysOrdered rows unique

/- Canonicality is derived from primitive aliases and computed cells, rather
than supplied for a translated table or the complete input image. The byte-key
condition is the existing public-schema uniqueness condition on that namespace. -/
theorem collectProjection {α β γ : Type} {f : α → Option β} {g : α → Option γ}
    {h : β → γ} {xs ys} (loaded : collect f xs = some ys)
    (same : ∀ x ∈ xs, ∀ y, f x = some y → g x = some (h y)) :
    collect g xs = some (ys.map h) := by
  induction xs generalizing ys with
  | nil => simp only [collect,Option.some.injEq] at loaded; subst ys; rfl
  | cons x xs ih =>
    simp only [collect,bind,Option.bind_eq_some_iff] at loaded
    obtain ⟨y,head,tail,rest,last⟩ := loaded
    cases Option.some.inj last
    simp only [collect,same x List.mem_cons_self y head,
      ih rest (fun a ha => same a (List.mem_cons_of_mem _ ha)),bind,Option.bind,List.map_cons]

def CanonicalAliases (models : List String) (nameMap : String → Option String) (names : List String) : Prop :=
  (∀ name ∈ names, ∃ publicName, nameMap name = some publicName ∧ canonical models (.model publicName) = true) ∧
  ∃ keys, collect (fun name => (nameMap name).map (fun s => encode (.model s))) names = some keys ∧ keys.Nodup

theorem namedCanonicalTotal {α : Type} (models : List String) (nameMap : String → Option String)
    (key : α → String) (value : α → Option Value) (rows : List α)
    (aliases : CanonicalAliases models nameMap (rows.map key))
    (cells : ∀ row ∈ rows, ∃ v, value row = some v ∧ canonical models v = true) :
    ∃ out, named nameMap key value rows = some out ∧ canonical models out = true := by
  obtain ⟨pairs,loaded⟩ := FamilyInputs.collectExists
    (fun row => do let name ← nameMap (key row); let v ← value row; some (Value.model name,v)) rows (by
      intro row member
      obtain ⟨name,ha,_⟩ := aliases.1 _ (List.mem_map.mpr ⟨row,member,rfl⟩)
      obtain ⟨v,hv,_⟩ := cells row member
      exact ⟨(.model name,v),by simp only [ha,hv,bind,Option.bind]⟩)
  refine ⟨function pairs,?_,?_⟩
  · unfold named
    change (collect (fun row => (nameMap (key row)).bind (fun name =>
      (value row).bind (fun v => some (Value.model name,v)))) rows).bind
      (fun ps => some (function ps)) = some (function pairs)
    exact congrArg (fun output => output.bind (fun ps => some (function ps))) loaded
  apply functionCanonicalFromParts
  · intro pair member
    obtain ⟨row,hr,source⟩ := collectedValueSource loaded member
    obtain ⟨name,ha,ca⟩ := aliases.1 _ (List.mem_map.mpr ⟨row,hr,rfl⟩)
    obtain ⟨v,hv,cv⟩ := cells row hr
    simp only [ha,hv,bind,Option.bind,Option.some.injEq] at source
    cases source
    exact ⟨ca,cv⟩
  · obtain ⟨keys,computed,unique⟩ := aliases.2
    have projected := collectProjection (h := encodedKey) loaded (g := fun row =>
      (nameMap (key row)).map (fun name => encode (.model name))) (by
        intro row _ pair source
        simp only [bind,Option.bind_eq_some_iff] at source
        obtain ⟨name,ha,v,_,last⟩ := source
        cases Option.some.inj last
        simp only [ha,Option.map_some,encodedKey])
    have mapped : ∀ xs : List α, collect (fun row => (nameMap (key row)).map (fun name => encode (.model name))) xs =
        collect (fun name => (nameMap name).map (fun s => encode (.model s))) (xs.map key) := by
      intro xs
      induction xs with
      | nil => rfl
      | cons x xs ih => simp only [collect,List.map_cons,ih]
    rw [mapped,computed] at projected
    exact (Option.some.inj projected) ▸ unique

theorem canonicalAliasesCongr {models nameMap left right}
    (same : left = right) (valid : CanonicalAliases models nameMap left) :
    CanonicalAliases models nameMap right := same ▸ valid

theorem currentTableCanonicalTotal (models : List String) (nameMap : String → Option String)
    (cells : List (String × Int)) (aliases : CanonicalAliases models nameMap (cells.map Prod.fst)) :
    ∃ value, currentTable nameMap cells = some value ∧ canonical models value = true :=
  namedCanonicalTotal models nameMap Prod.fst (fun p => some (.integer p.2)) cells aliases
    (fun row _ => ⟨.integer row.2,rfl,rfl⟩)

theorem vectorTableCanonicalTotal (models : List String) (nameMap : String → Option String)
    (shards : List String) (cells : List Int) (shape : cells.length = shards.length)
    (aliases : CanonicalAliases models nameMap shards) :
    ∃ value, vectorTable nameMap shards cells = some value ∧ canonical models value = true := by
  have names : (shards.zip cells).map Prod.fst = shards := List.map_fst_zip (by omega)
  obtain ⟨value,computed,safe⟩ := namedCanonicalTotal models nameMap Prod.fst
    (fun p : String × Int => some (.integer p.2)) (shards.zip cells)
    (by rw [names]; exact aliases) (fun row _ => ⟨.integer row.2,rfl,rfl⟩)
  exact ⟨value,by simp only [vectorTable,if_pos shape,computed],safe⟩

theorem decimalCharsBound (n : Nat) (c : Char) (member : c ∈ Nat.toDigits 10 n) :
    48 ≤ c.toNat ∧ c.toNat ≤ 57 := by
  have digit := Nat.isDigit_of_mem_toDigits (by decide : 0 < 10) (by decide : 10 ≤ 10) member
  simpa only [Char.reduceToNat] using Char.isDigit_iff_toNat.mp digit

theorem decimalQuoted (n : Nat) :
    quoted (toString n) = [34] ++ ((Nat.toDigits 10 n).map (fun c => UInt8.ofNat c.toNat)) ++ [34] := by
  have flat : (Nat.toDigits 10 n).flatMap (fun c => escapedASCII c.toNat) =
      (Nat.toDigits 10 n).map (fun c => UInt8.ofNat c.toNat) := by
    rw [List.map_eq_flatMap]
    apply List.flatMap_congr
    intro c member
    have bound := decimalCharsBound n c member
    simp only [escapedASCII,if_neg (by omega : c.toNat ≠ 34),if_neg (by omega : c.toNat ≠ 92),
      if_neg (by omega : c.toNat ≠ 8),if_neg (by omega : c.toNat ≠ 12),if_neg (by omega : c.toNat ≠ 10),
      if_neg (by omega : c.toNat ≠ 13),if_neg (by omega : c.toNat ≠ 9),if_neg (by omega : ¬ (c.toNat < 32 ∨ c.toNat = 127))]
  simp only [quoted,Nat.toString_eq_ofList_toDigits,String.toList_ofList,flat,quotedBytes]

theorem decimalByteRecovery (n : Nat) :
    (((Nat.toDigits 10 n).map (fun c => UInt8.ofNat c.toNat)).map (fun b => Char.ofNat b.toNat)) = Nat.toDigits 10 n := by
  rw [List.map_map]
  conv_rhs => rw [← List.map_id (Nat.toDigits 10 n)]
  apply List.map_congr_left
  intro c member
  have bound := decimalCharsBound n c member
  simp only [Function.comp_def,UInt8.toNat_ofNat_of_lt' (by change c.toNat < 256; omega),Char.ofNat_toNat,id_eq]

theorem encodedNatInjective (a b : Nat) (same : encode (.integer (Int.ofNat a)) = encode (.integer (Int.ofNat b))) : a = b := by
  change array [quoted "int",quoted (toString a)] = array [quoted "int",quoted (toString b)] at same
  have raw : (Nat.toDigits 10 a).map (fun c => UInt8.ofNat c.toNat) = (Nat.toDigits 10 b).map (fun c => UInt8.ofNat c.toNat) := by
    simpa only [array,List.intercalate_cons_cons,List.intercalate_singleton,decimalQuoted,List.append_assoc,
      List.cons_append,List.nil_append,List.cons.injEq,true_and,List.append_cancel_left_eq,List.append_cancel_right_eq] using same
  have digits := congrArg (List.map (fun b : UInt8 => Char.ofNat b.toNat)) raw
  rw [decimalByteRecovery,decimalByteRecovery] at digits
  have decoded := congrArg (fun cs => Nat.ofDigitChars 10 cs 0) digits
  simpa only [Nat.ofDigitChars_ten_toDigits] using decoded

theorem sequenceIndexKeysUnique (n : Nat) :
    ((List.range n).map (fun k => encode (.integer (Int.ofNat (k+1))))).Nodup := by
  apply List.Nodup.map _ (List.nodup_range (n := n))
  intro a b same
  have equal := encodedNatInjective (a+1) (b+1) same
  omega

theorem sequenceCanonicalFromPrimitiveKeys (models : List String) (values : List Value)
    (safe : ∀ v ∈ values, canonical models v = true)
    (unique : ((List.range values.length).map (fun i => encode (.integer (Int.ofNat (i+1))))).Nodup) :
    canonical models (sequence values) = true := by
  apply functionCanonicalFromParts
  · intro row member
    obtain ⟨pair,hp,rfl⟩ := List.mem_map.mp member
    exact ⟨rfl,safe pair.2 (List.of_mem_zip hp).2⟩
  · have names : ((List.range values.length).zip values).map Prod.fst = List.range values.length :=
      List.map_fst_zip (by simp)
    have same : (((List.range values.length).zip values).map
        (fun (i,v) => (Value.integer (Int.ofNat (i+1)),v))).map encodedKey =
        (((List.range values.length).zip values).map Prod.fst).map
          (fun i => encode (.integer (Int.ofNat (i+1)))) := by
      simp only [List.map_map]
      congr 1
    rw [same,names]
    exact unique

theorem currentRowsKeys {nameMap : String → Option String} {cells rows}
    (computed : collect (fun c : String × Int => do
      let name ← nameMap c.1
      pure (Value.model name,Value.integer c.2)) cells = some rows) :
    collect (fun s => (nameMap s).map Value.model) (cells.map Prod.fst) = some (rows.map Prod.fst) ∧
    ∀ row ∈ rows, ∃ n, row.2 = .integer n := by
  induction cells generalizing rows with
  | nil => simp [collect] at computed; subst rows; simp [collect]
  | cons c cs ih =>
    simp only [collect,bind,Option.bind_eq_some_iff] at computed
    obtain ⟨pair,head,tail,ht,last⟩ := computed

    obtain ⟨name,hn,same⟩ := head
    cases Option.some.inj same
    cases Option.some.inj last
    have rest := ih ht
    refine ⟨?_,?_⟩
    · simp only [List.map_cons,collect,hn,Option.map_some,rest.1,bind,Option.bind]
    · intro row member
      rcases List.mem_cons.mp member with same | member
      · subst row; exact ⟨c.2,rfl⟩
      · exact rest.2 row member

theorem currentTableCanonicalSameKeys {nameMap before after prior next models}
    (sameKeys : before.map Prod.fst = after.map Prod.fst)
    (old : currentTable nameMap before = some prior)
    (new : currentTable nameMap after = some next)
    (safe : canonical models prior = true) : canonical models next = true := by
  simp only [currentTable,named,bind,Option.bind_eq_some_iff] at old new
  obtain ⟨oldRows,oldComputed,oldValue⟩ := old
  obtain ⟨newRows,newComputed,newValue⟩ := new
  cases Option.some.inj oldValue
  cases Option.some.inj newValue
  have oldSource := currentRowsKeys oldComputed
  have newSource := currentRowsKeys newComputed
  rw [sameKeys] at oldSource
  have keysSame := Option.some.inj (oldSource.1.symm.trans newSource.1)
  have oldParts := functionCanonicalParts safe
  apply functionCanonicalFromParts
  · intro row member
    have inOld : row.1 ∈ oldRows.map Prod.fst := by rw [keysSame]; exact List.mem_map.mpr ⟨row,member,rfl⟩
    obtain ⟨oldRow,oldMember,key⟩ := List.mem_map.mp inOld
    obtain ⟨n,value⟩ := newSource.2 row member
    exact ⟨by rw [← key]; exact (oldParts.1 oldRow oldMember).1,by rw [value]; rfl⟩
  · have encodeSame := congrArg (List.map PublicState.encode) keysSame
    simp only [List.map_map,Function.comp_def] at encodeSame
    change oldRows.map encodedKey = newRows.map encodedKey at encodeSame
    exact encodeSame ▸ oldParts.2

theorem atomLoaderComplete {metadataTrust source key} (a : Atom (trust := metadataTrust) source key) :
    loadAtom source key = some a := by
  unfold loadAtom
  split
  · rename_i absent; simp [a.selected] at absent
  · rename_i name selected
    have same := Option.some.inj (selected.symm.trans a.selected)
    subst name
    rfl

theorem headerLoaderComplete {codec store trust anchor metadataTrust source}
    {binding : Binding codec trust anchor store} (h : Header binding (metadataTrust := metadataTrust) source) :
    loadHeader binding source = some h := by
  simp only [loadHeader,atomLoaderComplete h.height,atomLoaderComplete h.epoch,
    atomLoaderComplete h.parent,atomLoaderComplete h.schema,atomLoaderComplete h.profile,
    atomLoaderComplete h.applyProfile,atomLoaderComplete h.config,atomLoaderComplete h.seed,
    atomLoaderComplete h.norm,atomLoaderComplete h.coefficient,bind,Option.bind]
  split
  · rename_i absent; simp [h.policySelected] at absent
  · rename_i policy selected
    have same := Option.some.inj (selected.symm.trans h.policySelected)
    subst policy
    rfl

theorem entryLoaderComplete {metadataTrust source isc vocabulary commitment}
    (e : Entry (metadataTrust := metadataTrust) source isc vocabulary commitment) :
    loadEntry source isc vocabulary commitment = some e := by
  simp only [loadEntry,atomLoaderComplete e.content,bind,Option.bind]
  split
  · rename_i absent; simp [e.ticketSelected] at absent
  · rename_i ticket selected
    have same := Option.some.inj (selected.symm.trans e.ticketSelected)
    subst ticket
    rfl

theorem entriesLoaderComplete {metadataTrust source isc vocabulary commitments values}
    (h : EntriesFor (metadataTrust := metadataTrust) source isc vocabulary commitments values) :
    PublicAuthority.loadEntries source isc vocabulary commitments = some ⟨values,h⟩ := by
  induction h with
  | nil => rfl
  | cons entry tail ih => simp only [PublicAuthority.loadEntries,entryLoaderComplete entry,ih,bind,Option.bind]

theorem projectFromComputed {codec store trust anchor binding corpus choice limit input vocabulary metadataTrust source}
    (p : Projection (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (corpus := corpus) (choice := choice) (limit := limit) input vocabulary
      (metadataTrust := metadataTrust) source) : project input vocabulary source p.completion.configured = some p := by
  unfold project
  rw [FamilyInputs.completeFromSource p.completion]
  simp only [bind,Option.bind]
  rw [encodeImageFromComputed p.encoded]
  simp only [headerLoaderComplete p.header,entriesLoaderComplete p.entryOrigin]
  split
  · rename_i members eligible hm he
    have sameMembers := Option.some.inj (hm.symm.trans p.members)
    have sameEligible := Option.some.inj (he.symm.trans p.eligible)
    subst members; subst eligible
    rw [dif_pos ⟨p.memberUnique,p.memberConfigured,p.memberSources,p.eligibleUnique⟩]
  · simp_all [p.members,p.eligible]

/- Canonicality of the complete authority is assembled from the independently
bound primitive atoms and the computed input image. No complete public parent
or authority body is accepted as a canonicality premise. -/
section CanonicalAuthority
variable {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : FamilyInputs.Corpus binding} {choice : FamilyInputs.Choice corpus.frame}
    {limit : Int} {input : FamilyInputs.Projected corpus choice limit}
    {vocabulary : Vocabulary} {metadataTrust} {source : Metadata metadataTrust}
    (p : Projection input vocabulary source)

set_option maxHeartbeats 600000 in
theorem constructedAuthorityCanonical
    (header : ∀ value ∈ [p.header.height.value,p.header.epoch.value,p.header.parent.value,
      p.header.schema.value,p.header.profile.value,p.header.applyProfile.value,
      p.header.config.value,p.header.seed.value,p.header.norm.value,p.header.coefficient.value],
      canonical vocabulary.models value = true)
    (entryAtoms : ∀ commitment (entry : Entry source binding.authority.isc vocabulary commitment),
      entry.value ∈ p.entryValues → canonical vocabulary.models entry.content.value = true ∧
        canonical vocabulary.models (.model entry.ticket) = true)
    (eligibleAtoms : ∀ name ∈ p.eligibleNames, canonical vocabulary.models (.model name) = true)
    (entryUnique : (p.entryValues.map encode).Nodup)
    (eligibleUnique : ((p.eligibleNames.map Value.model).map encode).Nodup) :
    canonical vocabulary.models p.value = true := by
  have height : canonical vocabulary.models p.header.height.value = true := header _ (by simp)
  have epoch : canonical vocabulary.models p.header.epoch.value = true := header _ (by simp)
  have parent : canonical vocabulary.models p.header.parent.value = true := header _ (by simp)
  have schema : canonical vocabulary.models p.header.schema.value = true := header _ (by simp)
  have profile : canonical vocabulary.models p.header.profile.value = true := header _ (by simp)
  have applyProfile : canonical vocabulary.models p.header.applyProfile.value = true := header _ (by simp)
  have config : canonical vocabulary.models p.header.config.value = true := header _ (by simp)
  have seedAtom : canonical vocabulary.models p.header.seed.value = true := header _ (by simp)
  have norm : canonical vocabulary.models p.header.norm.value = true := header _ (by simp)
  have coefficient : canonical vocabulary.models p.header.coefficient.value = true := header _ (by simp)
  have round : canonical vocabulary.models p.round = true := by
    apply canonicalRecord
    · intro field member
      simp only [List.mem_cons,List.not_mem_nil,or_false] at member
      rcases member with h|h
      all_goals subst field
      all_goals constructor
      all_goals first | assumption | (simp only [canonical]; decide +kernel)
    · change ordered (["epoch","height"].map (fun s => encode (.text s))) = true
      decide +kernel
  have entriesSafe : ∀ value ∈ p.entryValues, canonical vocabulary.models value = true := by
    intro value member
    obtain ⟨i,atValue⟩ := List.mem_iff_getElem?.mp member
    obtain ⟨commitment,_,entry,same,_⟩ := authorityEntriesPreserveSource p i value atValue
    have atoms := entryAtoms commitment entry (same ▸ member)
    rw [same]
    apply canonicalRecord
    · intro field member
      simp only [List.mem_cons,List.not_mem_nil,or_false] at member
      rcases member with h|h
      all_goals subst field
      all_goals constructor
      all_goals first | exact atoms.1 | exact atoms.2 | (simp only [canonical]; decide +kernel)
    · change ordered (["content","ticket"].map (fun s => encode (.text s))) = true
      decide +kernel
  have entrySet := canonicalSet vocabulary.models p.entryValues entriesSafe entryUnique
  have members := canonicalSet vocabulary.models (p.eligibleNames.map Value.model)
    (by intro value member; obtain ⟨name,hn,same⟩ := List.mem_map.mp member; subst value; exact eligibleAtoms name hn)
    eligibleUnique
  have policy : canonical vocabulary.models (.text p.header.policy.text) = true := by
    cases p.header.policy <;> simp only [ClosePolicy.text,canonical] <;> decide +kernel
  have isc : canonical vocabulary.models p.isc = true := by
    apply canonicalRecord
    · intro field member
      simp only [List.mem_cons,List.not_mem_nil,or_false] at member
      rcases member with h|h|h|h|h
      all_goals subst field
      all_goals constructor
      all_goals first | assumption | (simp only [canonical]; decide +kernel)
    · change ordered (["canonicalRoot","config","entries","policy","round"].map (fun s => encode (.text s))) = true
      decide +kernel
  have seed : canonical vocabulary.models p.seed = true := by
    apply canonicalRecord
    · intro field member
      simp only [List.mem_cons,List.not_mem_nil,or_false] at member
      rcases member with h|h|h
      all_goals subst field
      all_goals constructor
      all_goals first | assumption | (simp only [canonical]; decide +kernel)
    · change ordered (["epoch","isc","value"].map (fun s => encode (.text s))) = true
      decide +kernel
  have ec : canonical vocabulary.models p.ec = true := by
    apply canonicalRecord
    · intro field member
      simp only [List.mem_cons,List.not_mem_nil,or_false] at member
      rcases member with h|h|h|h
      all_goals subst field
      all_goals constructor
      all_goals first | assumption | (simp only [canonical]; decide +kernel)
    · change ordered (["isc","members","normEvidence","seed"].map (fun s => encode (.text s))) = true
      decide +kernel
  have apc : canonical vocabulary.models p.apc = true := by
    apply canonicalRecord
    · intro field member
      simp only [List.mem_cons,List.not_mem_nil,or_false] at member
      rcases member with h|h|h|h|h
      all_goals subst field
      all_goals constructor
      all_goals first | assumption | (simp only [canonical]; decide +kernel)
    · change ordered (["coefficientProfile","ec","isc","members","seed"].map (fun s => encode (.text s))) = true
      decide +kernel
  have modelTable := canonicalField p.encoded.canonical
    (show readField p.encoded.value "model" = some (p.encoded.components.at 9) from rfl)
  have optimizerTable := canonicalField p.encoded.canonical
    (show readField p.encoded.value "optimizer" = some (p.encoded.components.at 10) from rfl)
  have vector (kind : String) (kindSafe : canonical vocabulary.models (.text kind) = true)
      (value : Value) (valueSafe : canonical vocabulary.models value = true) :
      canonical vocabulary.models (vectorValue kind p.header.schema.value value) = true := by
    apply canonicalRecord
    · intro field member
      simp only [List.mem_cons,List.not_mem_nil,or_false] at member
      rcases member with h|h|h
      all_goals subst field
      all_goals constructor
      all_goals first | assumption | (simp only [canonical]; decide +kernel)
    · change ordered (["kind","schema","values"].map (fun s => encode (.text s))) = true
      decide +kernel
  have model := vector "MODEL" (by simp only [canonical]; decide +kernel) _ modelTable
  have optimizer := vector "OPTIMIZER" (by simp only [canonical]; decide +kernel) _ optimizerTable
  have inputs := p.encoded.canonical
  apply canonicalRecord
  · intro field member
    simp only [Projection.fields,List.mem_cons,List.not_mem_nil,or_false] at member
    rcases member with h|h|h|h|h|h|h|h|h|h
    all_goals subst field
    all_goals constructor
    all_goals first | assumption | (simp only [canonical]; decide +kernel)
  · change ordered (authorityFieldNames.map (fun s => encode (.text s))) = true
    decide +kernel

theorem checkedAuthorityFromConstructed
    (header : ∀ value ∈ [p.header.height.value,p.header.epoch.value,p.header.parent.value,
      p.header.schema.value,p.header.profile.value,p.header.applyProfile.value,
      p.header.config.value,p.header.seed.value,p.header.norm.value,p.header.coefficient.value],
      canonical vocabulary.models value = true)
    (entryAtoms : ∀ commitment (entry : Entry source binding.authority.isc vocabulary commitment),
      entry.value ∈ p.entryValues → canonical vocabulary.models entry.content.value = true ∧
        canonical vocabulary.models (.model entry.ticket) = true)
    (eligibleAtoms : ∀ name ∈ p.eligibleNames, canonical vocabulary.models (.model name) = true)
    (entryUnique : (p.entryValues.map encode).Nodup)
    (eligibleUnique : ((p.eligibleNames.map Value.model).map encode).Nodup) :
    ∃ checked, check input vocabulary source p.value p.completion.configured = some checked ∧ checked.projection = p := by
  have safe := constructedAuthorityCanonical p header entryAtoms eligibleAtoms entryUnique eligibleUnique
  unfold check
  rw [projectFromComputed p]
  simp only [bind,Option.bind]
  rw [dif_pos ⟨safe,by trivial⟩]
  exact ⟨_,rfl,rfl⟩

end CanonicalAuthority
def readPublicEscapes : Bytes → List Char
  | [] => []
  | first :: rest => if first = 92 then
      match rest with
      | [] => []
      | escaped :: tail => Char.ofNat escaped.toNat :: readPublicEscapes tail
    else Char.ofNat first.toNat :: readPublicEscapes rest

theorem publicEscapesRoundtrip (cs : List Char)
    (safe : ∀ c ∈ cs, 32 ≤ c.toNat ∧ c.toNat ≤ 126) :
    readPublicEscapes (cs.flatMap (fun c => escapedASCII c.toNat)) = cs := by
  induction cs with
  | nil => rfl
  | cons c cs ih =>
    have bound := safe c List.mem_cons_self
    have tail := ih (fun x hx => safe x (List.mem_cons_of_mem _ hx))
    rw [List.flatMap_cons]
    by_cases quote : c.toNat = 34
    · have equal : c = '"' := Char.toNat_inj.mp quote
      subst c
      exact congrArg (List.cons '"') tail
    · by_cases slash : c.toNat = 92
      · have equal : c = '\\' := Char.toNat_inj.mp slash
        subst c
        exact congrArg (List.cons '\\') tail
      · have one : escapedASCII c.toNat = [UInt8.ofNat c.toNat] := by
          simp only [escapedASCII,if_neg quote,if_neg slash,
            if_neg (by omega : c.toNat ≠ 8),if_neg (by omega : c.toNat ≠ 12),if_neg (by omega : c.toNat ≠ 10),
            if_neg (by omega : c.toNat ≠ 13),if_neg (by omega : c.toNat ≠ 9),if_neg (by omega : ¬ (c.toNat < 32 ∨ c.toNat = 127))]
        have notEscape : UInt8.ofNat c.toNat ≠ 92 := by
          intro equal
          have same := congrArg UInt8.toNat equal
          simp only [UInt8.toNat_ofNat_of_lt' (by change c.toNat < 256; omega)] at same
          exact slash same
        rw [one]
        rw [List.singleton_append,readPublicEscapes.eq_def]
        simp only [if_neg notEscape,UInt8.toNat_ofNat_of_lt' (by change c.toNat < 256; omega),Char.ofNat_toNat]
        exact congrArg (List.cons c) tail

theorem modelEncodedInjective {models : List String} {a b : String}
    (safeA : canonical models (.model a) = true) (safeB : canonical models (.model b) = true)
    (same : encode (.model a) = encode (.model b)) : a = b := by
  have charsA : ∀ c ∈ a.toList, 32 ≤ c.toNat ∧ c.toNat ≤ 126 := by
    have parts : models.contains a = true ∧ (∀ c ∈ a.toList, 32 ≤ c.toNat ∧ c.toNat ≤ 126) := by
      simpa only [canonical,Bool.and_eq_true,List.all_eq_true,decide_eq_true_eq] using safeA
    exact parts.2
  have charsB : ∀ c ∈ b.toList, 32 ≤ c.toNat ∧ c.toNat ≤ 126 := by
    have parts : models.contains b = true ∧ (∀ c ∈ b.toList, 32 ≤ c.toNat ∧ c.toNat ≤ 126) := by
      simpa only [canonical,Bool.and_eq_true,List.all_eq_true,decide_eq_true_eq] using safeB
    exact parts.2
  have raw : a.toList.flatMap (fun c => escapedASCII c.toNat) = b.toList.flatMap (fun c => escapedASCII c.toNat) := by
    simpa only [encode,array,quoted,quotedBytes,List.intercalate_cons_cons,List.intercalate_singleton,List.append_assoc,
      List.cons_append,List.nil_append,List.cons.injEq,true_and,List.append_cancel_left_eq,List.append_cancel_right_eq] using same
  have decoded := congrArg readPublicEscapes raw
  rw [publicEscapesRoundtrip _ charsA,publicEscapesRoundtrip _ charsB] at decoded
  exact String.toList_inj.mp decoded
theorem canonicalAliasesFromNamespace {models nameMap names configured}
    (checked : checkNamespace nameMap names configured = true)
    (atoms : ∀ name ∈ configured, canonical models (.model name) = true) :
    CanonicalAliases models nameMap names := by
  obtain ⟨rendered,computed,permutation,unique⟩ := namespaceCheckSound checked
  constructor
  · intro name member
    obtain ⟨out,hm,selected⟩ := FamilyInputs.collectInputHasOutput computed member
    exact ⟨out,selected,atoms out (permutation.mem_iff.mp hm)⟩
  · refine ⟨rendered.map (fun name => encode (.model name)),?_,?_⟩
    · exact collectProjection computed (fun name _ out selected => by simp only [selected,Option.map_some])
    · exact List.Nodup.map_on (fun a ha b hb same =>
        modelEncodedInjective (atoms a (permutation.mem_iff.mp ha))
          (atoms b (permutation.mem_iff.mp hb)) same) unique

/- These are checks of primitive namespace/configuration cells, not a supplied
translation or canonicality assumption for a whole input body. -/
structure InputEncodingPrimitives (v : Vocabulary) (i : Image) : Prop where
  ticketAtoms : ∀ name ∈ v.tickets, canonical v.models (.model name) = true
  domainAtoms : ∀ name ∈ v.domains, canonical v.models (.model name) = true
  shardAtoms : ∀ name ∈ v.shards, canonical v.models (.model name) = true
  ticketNamespace : checkNamespace v.ticket (i.tickets.map (·.ticket)) v.tickets = true
  domainNamespace : checkNamespace v.domain (NativeBinding.domains i.profile) v.domains = true
  shardNamespace : checkNamespace v.shard i.shards v.shards = true

theorem InputEncodingPrimitives.ticketAliases {v i} (p : InputEncodingPrimitives v i) :
    CanonicalAliases v.models v.ticket (i.tickets.map (·.ticket)) :=
  canonicalAliasesFromNamespace p.ticketNamespace p.ticketAtoms

theorem InputEncodingPrimitives.domainAliases {v i} (p : InputEncodingPrimitives v i) :
    CanonicalAliases v.models v.domain (NativeBinding.domains i.profile) :=
  canonicalAliasesFromNamespace p.domainNamespace p.domainAtoms

theorem InputEncodingPrimitives.shardAliases {v i} (p : InputEncodingPrimitives v i) :
    CanonicalAliases v.models v.shard i.shards :=
  canonicalAliasesFromNamespace p.shardNamespace p.shardAtoms

theorem inputTablesCanonicalTotal {v : Vocabulary} {i : Image}
    (numeric : FamilyInputs.InputNumericGuards i) (primitive : InputEncodingPrimitives v i) :
    ∀ operation ∈ [ticketDomains v i,qTable v i,
      weightTable Rational.numerator v i,weightTable Rational.denominator v i,
      denominatorTable v i,quantumTable Rational.numerator v i,quantumTable Rational.denominator v i,
      mixtureTable Rational.numerator v i,mixtureTable Rational.denominator v i,
      currentTable v.shard i.model,currentTable v.shard i.optimizer],
    ∃ value, operation = some value ∧ canonical v.models value = true := by
  obtain ⟨_,domainNames,tickets,domains,_,_,_,_,_,_,_,_,modelNames,optimizerNames,_,_⟩ := numeric
  have domainAliases : CanonicalAliases v.models v.domain (i.domains.map (·.domain)) := by
    rw [domainNames]; exact primitive.domainAliases
  have ticketDomainTable : ∃ value, ticketDomains v i = some value ∧ canonical v.models value = true := by
    apply namedCanonicalTotal _ _ _ _ _ primitive.ticketAliases
    intro ticket member
    obtain ⟨name,computed,safe⟩ := domainAliases.1 _ (tickets ticket member).1
    exact ⟨.model name,by simp only [computed,Option.map_some],safe⟩
  have q : ∃ value, qTable v i = some value ∧ canonical v.models value = true := by
    apply namedCanonicalTotal _ _ _ _ _ primitive.ticketAliases
    intro ticket member
    exact vectorTableCanonicalTotal _ _ _ _ (tickets ticket member).2.1 primitive.shardAliases
  have weight : ∀ part, ∃ value, weightTable part v i = some value ∧ canonical v.models value = true := by
    intro part
    exact namedCanonicalTotal _ _ _ _ _ primitive.ticketAliases (fun row _ => ⟨.integer (part row.weight),rfl,rfl⟩)
  have denominator : ∃ value, denominatorTable v i = some value ∧ canonical v.models value = true :=
    namedCanonicalTotal _ _ _ _ _ domainAliases (fun row _ => ⟨.integer row.denominator,rfl,rfl⟩)
  have quantum : ∀ part, ∃ value, quantumTable part v i = some value ∧ canonical v.models value = true := by
    intro part
    apply namedCanonicalTotal _ _ _ _ _ domainAliases
    intro domain member
    exact vectorTableCanonicalTotal _ _ _ _ (by rw [List.length_map]; exact (domains domain member).2.1)
      primitive.shardAliases
  have mixture : ∀ part, ∃ value, mixtureTable part v i = some value ∧ canonical v.models value = true := by
    intro part
    exact namedCanonicalTotal _ _ _ _ _ primitive.domainAliases (fun row _ => ⟨.integer (part row.weight),rfl,rfl⟩)
  have model := currentTableCanonicalTotal v.models v.shard i.model (by rw [modelNames]; exact primitive.shardAliases)
  have optimizer := currentTableCanonicalTotal v.models v.shard i.optimizer (by rw [optimizerNames]; exact primitive.shardAliases)
  intro operation member
  simp only [List.mem_cons,List.not_mem_nil,or_false] at member
  rcases member with rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl
  · exact ticketDomainTable
  · exact q
  · exact weight _
  · exact weight _
  · exact denominator
  · exact quantum _
  · exact quantum _
  · exact mixture _
  · exact mixture _
  · exact model
  · exact optimizer

theorem inputComponentsTotal {v : Vocabulary} {i : Image}
    (numeric : FamilyInputs.InputNumericGuards i) (primitive : InputEncodingPrimitives v i) :
    ∃ c, loadComponents v i = some c := by
  obtain ⟨ticketNames,tickets⟩ := FamilyInputs.collectExists v.ticket (i.tickets.map (·.ticket))
    (fun name member => by obtain ⟨out,computed,_⟩ := primitive.ticketAliases.1 name member; exact ⟨out,computed⟩)
  obtain ⟨domainNames,domains⟩ := FamilyInputs.collectExists v.domain (NativeBinding.domains i.profile)
    (fun name member => by obtain ⟨out,computed,_⟩ := primitive.domainAliases.1 name member; exact ⟨out,computed⟩)
  obtain ⟨values,computed⟩ := FamilyInputs.collectExists id _
    (fun operation member => by obtain ⟨out,computed,_⟩ := inputTablesCanonicalTotal numeric primitive operation member; exact ⟨out,computed⟩)
  have size : values.length = 11 := by simpa using collectLength computed
  let c : Components v i := ⟨ticketNames,tickets,domainNames,domains,values,computed,size,
    primitive.ticketNamespace,primitive.domainNamespace,primitive.shardNamespace⟩
  exact ⟨c,loadComponentsFromComputed c⟩

theorem inputComponentsCanonical {v : Vocabulary} {i : Image}
    (numeric : FamilyInputs.InputNumericGuards i) (primitive : InputEncodingPrimitives v i)
    (c : Components v i) : canonical v.models (record c.fields) = true := by
  have cells : ∀ k : Fin 11, canonical v.models (c.at k) = true := by
    intro k
    have source := componentIsComputed c k
    obtain ⟨out,computed,safe⟩ := inputTablesCanonicalTotal numeric primitive (some (c.at k))
      (List.mem_of_getElem? source)
    cases Option.some.inj computed
    exact safe
  have ticketNames : ∀ name ∈ c.ticketNames, canonical v.models (.model name) = true := by
    intro name member
    obtain ⟨original,ho,selected⟩ := collectedValueSource c.tickets member
    obtain ⟨out,computed,safe⟩ := primitive.ticketAliases.1 original ho
    cases Option.some.inj (selected.symm.trans computed)
    exact safe
  have domainNames : ∀ name ∈ c.domainNames, canonical v.models (.model name) = true := by
    intro name member
    obtain ⟨original,ho,selected⟩ := collectedValueSource c.domains member
    obtain ⟨out,computed,safe⟩ := primitive.domainAliases.1 original ho
    cases Option.some.inj (selected.symm.trans computed)
    exact safe
  have ticketSequence := sequenceCanonicalFromPrimitiveKeys v.models (c.ticketNames.map Value.model)
    (by intro value member; obtain ⟨name,hm,rfl⟩ := List.mem_map.mp member; exact ticketNames name hm)
    (sequenceIndexKeysUnique _)
  have domainSequence := sequenceCanonicalFromPrimitiveKeys v.models (c.domainNames.map Value.model)
    (by intro value member; obtain ⟨name,hm,rfl⟩ := List.mem_map.mp member; exact domainNames name hm)
    (sequenceIndexKeysUnique _)
  apply canonicalRecord
  · intro field member
    simp only [Components.fields,List.mem_cons,List.not_mem_nil,or_false] at member
    rcases member with rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl |
      rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl
    all_goals constructor
    all_goals first | assumption | exact cells _ | rfl | (simp only [canonical]; decide +kernel)
  · change ordered (PublicArithmeticInputs.fieldNames.map (fun s => encode (.text s))) = true
    decide +kernel

theorem inputEncoderTotal {v : Vocabulary} {i : Image}
    (numeric : FamilyInputs.InputNumericGuards i) (primitive : InputEncodingPrimitives v i) :
    ∃ encoded, encodeImage v i = some encoded := by
  obtain ⟨c,_⟩ := inputComponentsTotal numeric primitive
  let e : Encoded v i := ⟨c,inputComponentsCanonical numeric primitive c⟩
  exact ⟨e,encodeImageFromComputed e⟩

theorem collectedNamesAsMap {nameMap : String → Option String} {names rendered}
    (computed : collect nameMap names = some rendered) :
    rendered = names.map (fun name => (nameMap name).getD "") := by
  have same := FamilyInputs.collectedKeys (left := fun name => (nameMap name).getD "")
    (right := id) computed (fun name out selected => by simp only [selected,Option.getD_some,id_eq])
  simpa only [List.map_id] using same

theorem namespaceSubset {nameMap : String → Option String} {names configured selected}
    (checked : checkNamespace nameMap names configured = true)
    (included : ∀ name ∈ selected, name ∈ names) (unique : selected.Nodup) :
    ∃ rendered, collect nameMap selected = some rendered ∧ rendered.Nodup ∧
      ∀ name ∈ rendered, name ∈ configured := by
  obtain ⟨all,allComputed,permutation,allUnique⟩ := namespaceCheckSound checked
  obtain ⟨rendered,computed⟩ := FamilyInputs.collectExists nameMap selected (fun name member => by
    obtain ⟨out,source,_⟩ := configuredAlias checked (included name member)
    exact ⟨out,source⟩)
  refine ⟨rendered,computed,?_,?_⟩
  · have mappedUnique : (names.map (fun name => (nameMap name).getD "")).Nodup := by
      rw [← collectedNamesAsMap allComputed]; exact allUnique
    rw [collectedNamesAsMap computed]
    exact List.Nodup.map_on (fun a ha b hb same =>
      List.inj_on_of_nodup_map mappedUnique (included a ha) (included b hb) same) unique
  · intro name member
    obtain ⟨original,ho,source⟩ := collectedValueSource computed member
    obtain ⟨out,selected,inside⟩ := configuredAlias checked (included original ho)
    cases Option.some.inj (source.symm.trans selected)
    exact inside

theorem authorityConstructorTotal {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : FamilyInputs.Corpus binding} {choice : FamilyInputs.Choice corpus.frame} {limit : Int}
    (input : FamilyInputs.Projected corpus choice limit) (vocabulary : Vocabulary)
    {metadataTrust} (source : Metadata metadataTrust)
    (completion : FamilyInputs.Completed (FamilyInputs.image input))
    (primitive : InputEncodingPrimitives vocabulary
      (FamilyInputs.completedImage (FamilyInputs.image input) completion.configured))
    (header : Header binding source)
    (contents : ∀ commitment ∈ corpus.frame.commitments,
      ∃ name, source.atom (.content binding.authority.isc commitment) = some name)
    (members : ∀ name ∈ corpus.frame.members, name ∈ completion.configured.map (·.id)) :
    ∃ out, project input vocabulary source completion.configured = some out := by
  have numeric := FamilyInputs.completedImageNumericGuards _ _ (FamilyInputs.allInputNumericGuards input)
    completion.coverage.2.2.2.1
  obtain ⟨encoded,_⟩ := inputEncoderTotal numeric primitive
  have configuredNamespace : checkNamespace vocabulary.ticket (completion.configured.map (·.id)) vocabulary.tickets = true := by
    simpa only [FamilyInputs.completedImage,FamilyInputs.completionExactUniverse] using primitive.ticketNamespace
  have valid := corpus.valid
  simp only [ParameterFrameValid] at valid
  obtain ⟨_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,memberOrder,_,eligibleOrder,eligibleSubset,_,_,commitmentNames,_⟩ := valid
  have memberUnique : corpus.frame.members.Nodup :=
    memberOrder.imp (fun h equal => by subst equal; exact String.lt_irrefl _ h)
  have eligibleUnique : corpus.frame.eligible.Nodup :=
    eligibleOrder.imp (fun h equal => by subst equal; exact String.lt_irrefl _ h)
  obtain ⟨memberNames,hm,um,cm⟩ := namespaceSubset configuredNamespace members memberUnique
  obtain ⟨eligibleNames,he,ue,_⟩ := namespaceSubset configuredNamespace
    (fun name member => members name (eligibleSubset name member)) eligibleUnique
  have entrySources : ∀ commitments : List Commitment,
      (∀ c ∈ commitments, c ∈ corpus.frame.commitments) →
      ∃ entries, PublicAuthority.loadEntries source binding.authority.isc vocabulary commitments = some entries := by
    intro commitments
    induction commitments with
    | nil => exact fun _ => ⟨⟨[],.nil⟩,rfl⟩
    | cons commitment rest ih =>
      intro included
      have member := included commitment List.mem_cons_self
      have ticketMember : commitment.ticket ∈ corpus.frame.members := by
        rw [← commitmentNames]; exact List.mem_map.mpr ⟨commitment,member,rfl⟩
      obtain ⟨ticket,selected,_⟩ := configuredAlias configuredNamespace (members commitment.ticket ticketMember)
      obtain ⟨name,atom⟩ := contents commitment member
      let entry : PublicAuthority.Entry source binding.authority.isc vocabulary commitment :=
        ⟨ticket,selected,⟨name,atom⟩⟩
      obtain ⟨entries,computed⟩ := ih (fun c hc => included c (List.mem_cons_of_mem _ hc))
      exact ⟨⟨entry.value :: entries.val,.cons entry entries.property⟩,by
        simp only [PublicAuthority.loadEntries,entryLoaderComplete entry,computed,bind,Option.bind]⟩
  obtain ⟨entries,_⟩ := entrySources corpus.frame.commitments (fun _ h => h)
  let out : Projection input vocabulary source :=
    ⟨completion,encoded,header,entries.val,entries.property,memberNames,hm,um,cm,members,eligibleNames,he,ue⟩
  exact ⟨out,projectFromComputed out⟩


/- Completeness of the full original-source input encoder, including configured
nonmembers. Configuration/aliases remain explicit primitive source premises;
no successful whole-image check or translated body is a premise. -/
theorem originalInputEncoderTotal
    {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source indices
      profile applyQuantum current image candidate vocabulary configured}
    (loaded : FamilyInputs.OriginalVectorSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source)
    (computed : FamilyInputs.readOriginalImage source indices profile applyQuantum current = some image)
    (profileValid : NativeApplyProfile.Valid profile)
    (normalized : FamilyInputs.OriginalProfileNormalized profile)
    (quantum : 0 < applyQuantum.numerator ∧ 0 < applyQuantum.denominator ∧
      Int.gcd applyQuantum.numerator applyQuantum.denominator = 1)
    (domainCoverage : ∀ row ∈ source.source.rows,
      row.term.source.member.input.domain ∈ profile.weights.map (·.domain))
    (currentLoaded : NativeCurrentValues.load sha candidate = some current)
    (coverage : FamilyInputs.CompletionCoverage image configured)
    (primitive : InputEncodingPrimitives vocabulary (FamilyInputs.completedImage image configured)) :
    ∃ encoded, encodeImage vocabulary (FamilyInputs.completedImage image configured) = some encoded := by
  have original := FamilyInputs.originalImageNumericGuards loaded computed profileValid normalized
    quantum domainCoverage currentLoaded
  exact inputEncoderTotal (FamilyInputs.completedImageNumericGuards image configured original
    coverage.2.2.2.1) primitive


/- The direct input gate retains the original source and the complete configured
image. It deliberately does not manufacture a draft graph artifact or identifier. -/
structure OriginalInput (source : NativeVectorContext.Bound) (indices : List Nat)
    (profile : NativeApplyProfile.Profile) (quantum : Rational) (current : NativeCurrentValues.Image)
    (vocabulary : Vocabulary) (configured : List Ticket) where
  image : Image
  computed : FamilyInputs.readOriginalImage source indices profile quantum current = some image
  coverage : FamilyInputs.CompletionCoverage image configured
  numeric : FamilyInputs.InputNumericGuards image
  encoded : Encoded vocabulary (FamilyInputs.completedImage image configured)

def loadOriginalInput (source : NativeVectorContext.Bound) (indices : List Nat)
    (profile : NativeApplyProfile.Profile) (quantum : Rational) (current : NativeCurrentValues.Image)
    (vocabulary : Vocabulary) (configured : List Ticket) :
    Option (OriginalInput source indices profile quantum current vocabulary configured) := do
  match computed : FamilyInputs.readOriginalImage source indices profile quantum current with
  | none => none
  | some image =>
    if valid : FamilyInputs.CompletionCoverage image configured ∧ FamilyInputs.InputNumericGuards image then
      let encoded ← encodeImage vocabulary (FamilyInputs.completedImage image configured)
      some ⟨image,computed,valid.1,valid.2,encoded⟩
    else none

theorem originalInputFromComponents {source indices profile quantum current vocabulary configured}
    (p : OriginalInput source indices profile quantum current vocabulary configured) :
    loadOriginalInput source indices profile quantum current vocabulary configured = some p := by
  unfold loadOriginalInput
  split
  · rename_i absent; simp [p.computed] at absent
  · rename_i image computed
    have same := Option.some.inj (computed.symm.trans p.computed)
    subst image
    rw [dif_pos ⟨p.coverage,p.numeric⟩,encodeImageFromComputed p.encoded]
    rfl

theorem originalInputFullNumeric {source indices profile quantum current vocabulary configured}
    (p : OriginalInput source indices profile quantum current vocabulary configured) :
    FamilyInputs.InputNumericGuards (FamilyInputs.completedImage p.image configured) :=
  FamilyInputs.completedImageNumericGuards _ _ p.numeric p.coverage.2.2.2.1

theorem originalInputFullCoverage {source indices profile quantum current vocabulary configured}
    (p : OriginalInput source indices profile quantum current vocabulary configured) :
    ((FamilyInputs.completedImage p.image configured).tickets.map (·.ticket)) = configured.map (·.id) ∧
    FamilyInputs.memberTickets (FamilyInputs.activeNames p.image.tickets)
      (FamilyInputs.completedImage p.image configured).tickets = p.image.tickets := by
  refine ⟨FamilyInputs.completionExactUniverse _ _ _,?_⟩
  exact FamilyInputs.completionSelectedRowsExact p.image.shards.length configured p.image.tickets
    p.coverage.2.1 p.coverage.2.2.1

/- Compose original source, the selected immutable numeric configuration and
primitive namespaces with the full executable encoder. Neither a whole input
image translation nor its canonicality is assumed. Namespace provenance and
coverage of the entire static state belong to the unified R2 relation. -/
theorem originalConfiguredInputLoaded
    {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source
      units profileId current indices image vocabulary configured}
    (bound : FamilyInputs.OriginalVectorSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source)
    (configuration : FamilyInputs.OriginalNumericConfiguration sha source units profileId current)
    (computed : FamilyInputs.readOriginalImage source indices configuration.profile.profile
      configuration.quantum current.last.values = some image)
    (coverage : FamilyInputs.CompletionCoverage image configured)
    (primitive : InputEncodingPrimitives vocabulary (FamilyInputs.completedImage image configured)) :
    ∃ result, loadOriginalInput source indices configuration.profile.profile configuration.quantum
      current.last.values vocabulary configured = some result ∧ result.image = image := by
  have numeric := FamilyInputs.originalConfiguredInputGuards bound configuration computed
  obtain ⟨encoded,_⟩ := inputEncoderTotal
    (FamilyInputs.completedImageNumericGuards image configured numeric coverage.2.2.2.1) primitive
  let result : OriginalInput source indices configuration.profile.profile configuration.quantum
      current.last.values vocabulary configured := ⟨image,computed,coverage,numeric,encoded⟩
  exact ⟨result,originalInputFromComponents result,rfl⟩

/- Four independently supplied primitive aliases of existing original content
identifiers. This is the existing configuration/alias boundary in R2, not an
identity constructor or an assertion of external authentication. -/
structure OriginalContentName (names : Bytes → Option String) (id : Bytes) where
  name : String
  selected : names id = some name

def OriginalContentName.value {names id} (n : OriginalContentName names id) : Value := .model n.name

def loadOriginalContentName (names : Bytes → Option String) (id : Bytes) : Option (OriginalContentName names id) :=
  match h : names id with | none => none | some name => some ⟨name,h⟩

structure OriginalHeader (source : NativeVectorContext.Bound) (profile : NativeApplyProfile.Checked)
    (names : Bytes → Option String) where
  parent : OriginalContentName names source.first.corpus.manifest.manifest.wire.parent
  schema : OriginalContentName names source.first.corpus.manifest.manifest.wire.schema
  arithmetic : OriginalContentName names source.first.corpus.manifest.manifest.wire.profile
  apply : OriginalContentName names profile.id

def loadOriginalHeader (source : NativeVectorContext.Bound) (profile : NativeApplyProfile.Checked)
    (names : Bytes → Option String) : Option (OriginalHeader source profile names) := do
  let parent ← loadOriginalContentName names source.first.corpus.manifest.manifest.wire.parent
  let schema ← loadOriginalContentName names source.first.corpus.manifest.manifest.wire.schema
  let arithmetic ← loadOriginalContentName names source.first.corpus.manifest.manifest.wire.profile
  let apply ← loadOriginalContentName names profile.id
  some ⟨parent,schema,arithmetic,apply⟩

theorem originalContentNameLoaded {names id} (n : OriginalContentName names id) :
    loadOriginalContentName names id = some n := by
  unfold loadOriginalContentName
  split
  · rename_i absent; simp [n.selected] at absent
  · rename_i name selected
    have same := Option.some.inj (selected.symm.trans n.selected)
    subst name; rfl

theorem originalHeaderLoaded {source profile names} (h : OriginalHeader source profile names) :
    loadOriginalHeader source profile names = some h := by
  simp only [loadOriginalHeader,originalContentNameLoaded h.parent,originalContentNameLoaded h.schema,
    originalContentNameLoaded h.arithmetic,originalContentNameLoaded h.apply,bind,Option.bind]

structure Original (source : NativeVectorContext.Bound) (indices : List Nat)
    (profile : NativeApplyProfile.Checked) (quantum : Rational) (current : NativeCurrentValues.Image)
    (vocabulary : Vocabulary) (configured : List Ticket) (names : Bytes → Option String)
    {earlyTrust planningTrust} (metadata : PublicPlanningBody.Metadata earlyTrust planningTrust)
    (selected : NativeSelectedVote.Checked) where
  input : OriginalInput source indices profile.profile quantum current vocabulary configured
  header : OriginalHeader source profile names
  parents : PublicPlanningBody.ApcBody metadata selected source.source.plan.members.edge

def Original.fields {source indices profile quantum current vocabulary configured names earlyTrust planningTrust metadata selected}
    (p : Original source indices profile quantum current vocabulary configured names
      (earlyTrust := earlyTrust) (planningTrust := planningTrust) metadata selected) : List (String × Value) := [
  ("apc",p.parents.value),("applyProfile",p.header.apply.value),("ec",p.parents.ec.value),
  ("inputs",p.input.encoded.value),("isc",p.parents.ec.parent.value),
  ("model",vectorValue "MODEL" p.header.schema.value (p.input.encoded.components.at 9)),
  ("optimizer",vectorValue "OPTIMIZER" p.header.schema.value (p.input.encoded.components.at 10)),
  ("parent",p.header.parent.value),("profile",p.header.arithmetic.value),("schema",p.header.schema.value)]

def Original.value {source indices profile quantum current vocabulary configured names earlyTrust planningTrust metadata selected}
    (p : Original source indices profile quantum current vocabulary configured names
      (earlyTrust := earlyTrust) (planningTrust := planningTrust) metadata selected) : Value := record p.fields

def loadOriginal (source : NativeVectorContext.Bound) (indices : List Nat)
    (profile : NativeApplyProfile.Checked) (quantum : Rational) (current : NativeCurrentValues.Image)
    (vocabulary : Vocabulary) (configured : List Ticket) (names : Bytes → Option String)
    {earlyTrust planningTrust} (metadata : PublicPlanningBody.Metadata earlyTrust planningTrust)
    (selected : NativeSelectedVote.Checked) :
    Option (Original source indices profile quantum current vocabulary configured names metadata selected) := do
  let input ← loadOriginalInput source indices profile.profile quantum current vocabulary configured
  let header ← loadOriginalHeader source profile names
  let parents ← PublicPlanningBody.loadApcBody metadata selected source.source.plan.members.edge
  some ⟨input,header,parents⟩

theorem originalAllInputs {source indices profile quantum current vocabulary configured names earlyTrust planningTrust metadata selected}
    (p : Original source indices profile quantum current vocabulary configured names
      (earlyTrust := earlyTrust) (planningTrust := planningTrust) metadata selected) :
    readField p.value "inputs" = some p.input.encoded.value ∧
    FamilyInputs.InputNumericGuards (FamilyInputs.completedImage p.input.image configured) :=
  ⟨rfl,originalInputFullNumeric p.input⟩

theorem originalAuthorityInventory {source indices profile quantum current vocabulary configured names earlyTrust planningTrust metadata selected}
    (p : Original source indices profile quantum current vocabulary configured names
      (earlyTrust := earlyTrust) (planningTrust := planningTrust) metadata selected) :
    p.fields.map Prod.fst = PublicAuthority.authorityFieldNames := rfl

theorem originalAuthorityRetainsParentObjects {source indices profile quantum current vocabulary configured names earlyTrust planningTrust metadata selected}
    (p : Original source indices profile quantum current vocabulary configured names
      (earlyTrust := earlyTrust) (planningTrust := planningTrust) metadata selected) :
    readField p.value "apc" = some p.parents.value ∧ readField p.value "ec" = some p.parents.ec.value ∧
    readField p.value "isc" = some p.parents.ec.parent.value := ⟨rfl,rfl,rfl⟩


/- Canonicality is assembled from primitive atoms, never supplied as a complete
translated authority/body. These helpers only reuse existing public constructors. -/
theorem originalRoundCanonical {models height epoch}
    (heightSafe : canonical models height = true) (epochSafe : canonical models epoch = true) :
    canonical models (roundValue height epoch) = true := by
  apply canonicalRecord
  · intro field member
    simp only [List.mem_cons,List.not_mem_nil,or_false] at member
    rcases member with rfl | rfl
    all_goals constructor
    all_goals first | assumption | (simp only [canonical]; decide +kernel)
  · simp only [List.map_cons,List.map_nil]
    decide +kernel

theorem originalIscCanonical {models round config policy entries}
    (roundSafe : canonical models round = true) (configSafe : canonical models config = true)
    (entrySafe : ∀ entry ∈ entries, canonical models entry = true)
    (unique : (entries.map encode).Nodup) :
    canonical models (iscValue round config policy (setValue entries)) = true := by
  have entrySet := canonicalSet models entries entrySafe unique
  have policySafe : canonical models (.text policy.text) = true := by
    cases policy <;> simp only [ClosePolicy.text,canonical] <;> decide +kernel
  apply canonicalRecord
  · intro field member
    simp only [List.mem_cons,List.not_mem_nil,or_false] at member
    rcases member with rfl | rfl | rfl | rfl | rfl
    all_goals constructor
    all_goals first | assumption | (simp only [canonical]; decide +kernel)
  · simp only [List.map_cons,List.map_nil]
    decide +kernel

theorem originalSeedCanonical {models isc epoch seed}
    (iscSafe : canonical models isc = true) (epochSafe : canonical models epoch = true)
    (seedSafe : canonical models seed = true) : canonical models (seedValue isc epoch seed) = true := by
  apply canonicalRecord
  · intro field member
    simp only [List.mem_cons,List.not_mem_nil,or_false] at member
    rcases member with rfl | rfl | rfl
    all_goals constructor
    all_goals first | assumption | (simp only [canonical]; decide +kernel)
  · simp only [List.map_cons,List.map_nil]
    decide +kernel

theorem originalEcCanonical {models isc seed members norm}
    (iscSafe : canonical models isc = true) (seedSafe : canonical models seed = true)
    (memberSafe : ∀ member ∈ members, canonical models member = true)
    (unique : (members.map encode).Nodup) (normSafe : canonical models norm = true) :
    canonical models (ecValue isc seed (setValue members) norm) = true := by
  have memberSet := canonicalSet models members memberSafe unique
  apply canonicalRecord
  · intro field member
    simp only [List.mem_cons,List.not_mem_nil,or_false] at member
    rcases member with rfl | rfl | rfl | rfl
    all_goals constructor
    all_goals first | assumption | (simp only [canonical]; decide +kernel)
  · simp only [List.map_cons,List.map_nil]
    decide +kernel

theorem originalApcCanonical {models isc seed ec members coefficient}
    (iscSafe : canonical models isc = true) (seedSafe : canonical models seed = true)
    (ecSafe : canonical models ec = true)
    (memberSafe : ∀ member ∈ members, canonical models member = true)
    (unique : (members.map encode).Nodup) (coefficientSafe : canonical models coefficient = true) :
    canonical models (apcValue isc seed ec (setValue members) coefficient) = true := by
  have memberSet := canonicalSet models members memberSafe unique
  apply canonicalRecord
  · intro field member
    simp only [List.mem_cons,List.not_mem_nil,or_false] at member
    rcases member with rfl | rfl | rfl | rfl | rfl
    all_goals constructor
    all_goals first | assumption | (simp only [canonical]; decide +kernel)
  · simp only [List.map_cons,List.map_nil]
    decide +kernel

theorem originalPlanningParentsCanonical {earlyTrust planningTrust metadata selected native models}
    (p : PublicPlanningBody.ApcBody (earlyTrust := earlyTrust) (trust := planningTrust) metadata selected native)
    (header : ∀ value ∈ [p.ec.parent.header.height.value,p.ec.parent.header.epoch.value,
      p.ec.parent.header.config.value,p.ec.seed.value,p.ec.norm.value,p.coefficient.value],
      canonical models value = true)
    (entryAtoms : ∀ entry ∈ p.ec.parent.entries,
      canonical models entry.ticket.value = true ∧ canonical models entry.content.value = true)
    (entryUnique : ((p.ec.parent.entries.map PublicEarlyBody.Entry.value).map encode).Nodup)
    (memberAtoms : ∀ member ∈ p.ec.members, canonical models member.value = true)
    (memberUnique : ((p.ec.members.map PublicPlanningBody.Member.value).map encode).Nodup) :
    canonical models p.ec.parent.value = true ∧ canonical models p.ec.seedValue = true ∧
    canonical models p.ec.value = true ∧ canonical models p.value = true := by
  have round := originalRoundCanonical (header p.ec.parent.header.height.value (by simp))
    (header p.ec.parent.header.epoch.value (by simp))
  have entries : ∀ value ∈ p.ec.parent.entries.map PublicEarlyBody.Entry.value,
      canonical models value = true := by
    intro value member
    obtain ⟨entry,inEntries,rfl⟩ := List.mem_map.mp member
    have atoms := entryAtoms entry inEntries
    apply canonicalRecord
    · intro field member
      simp only [List.mem_cons,List.not_mem_nil,or_false] at member
      rcases member with rfl | rfl
      all_goals constructor
      all_goals first | exact atoms.1 | exact atoms.2 | (simp only [canonical]; decide +kernel)
    · simp only [List.map_cons,List.map_nil]
      decide +kernel
  have isc := originalIscCanonical (policy := p.ec.parent.policy) round (header p.ec.parent.header.config.value (by simp)) entries entryUnique
  have seed := originalSeedCanonical isc (header p.ec.parent.header.epoch.value (by simp)) (header p.ec.seed.value (by simp))
  have members : ∀ value ∈ p.ec.members.map PublicPlanningBody.Member.value, canonical models value = true := by
    intro value member
    obtain ⟨original,hm,rfl⟩ := List.mem_map.mp member
    exact memberAtoms original hm
  have ec := originalEcCanonical isc seed members memberUnique (header p.ec.norm.value (by simp))
  have apc := originalApcCanonical isc seed ec members memberUnique (header p.coefficient.value (by simp))
  exact ⟨isc,seed,ec,by simpa only [PublicPlanningBody.ApcBody.value,PublicPlanningBody.EcBody.value,
    PublicPlanningBody.EcBody.seedValue,PublicPlanningBody.IscBody.value,PublicEarlyBody.Header.round,p.sameMembers] using apc⟩

section OriginalCanonical
variable {source indices profile quantum current vocabulary configured names earlyTrust planningTrust metadata selected}
    (p : Original source indices profile quantum current vocabulary configured names
      (earlyTrust := earlyTrust) (planningTrust := planningTrust) metadata selected)

theorem originalAuthorityCanonical
    (header : ∀ value ∈ [p.header.parent.value,p.header.schema.value,p.header.arithmetic.value,p.header.apply.value],
      canonical vocabulary.models value = true)
    (parents : canonical vocabulary.models p.parents.ec.parent.value = true ∧
      canonical vocabulary.models p.parents.ec.value = true ∧ canonical vocabulary.models p.parents.value = true) :
    canonical vocabulary.models p.value = true := by
  have parent := header p.header.parent.value (by simp)
  have schema := header p.header.schema.value (by simp)
  have arithmetic := header p.header.arithmetic.value (by simp)
  have applyProfile := header p.header.apply.value (by simp)
  have modelTable := canonicalField p.input.encoded.canonical
    (show readField p.input.encoded.value "model" = some (p.input.encoded.components.at 9) from rfl)
  have optimizerTable := canonicalField p.input.encoded.canonical
    (show readField p.input.encoded.value "optimizer" = some (p.input.encoded.components.at 10) from rfl)
  have vector (kind : String) (table : Value) (tableSafe : canonical vocabulary.models table = true)
      (kindSafe : canonical vocabulary.models (.text kind) = true) :
      canonical vocabulary.models (vectorValue kind p.header.schema.value table) = true := by
    apply canonicalRecord
    · intro field member
      simp only [List.mem_cons,List.not_mem_nil,or_false] at member
      rcases member with rfl | rfl | rfl
      all_goals constructor
      all_goals first | assumption | (simp only [canonical]; decide +kernel)
    · simp only [List.map_cons,List.map_nil]
      decide +kernel
  have model := vector "MODEL" _ modelTable (by simp only [canonical]; decide +kernel)
  have optimizer := vector "OPTIMIZER" _ optimizerTable (by simp only [canonical]; decide +kernel)
  apply canonicalRecord
  · intro field member
    simp only [Original.fields,List.mem_cons,List.not_mem_nil,or_false] at member
    rcases member with rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl
    all_goals constructor
    all_goals first | assumption | exact parents.1 | exact parents.2.1 | exact parents.2.2 |
      exact p.input.encoded.canonical | (simp only [canonical]; decide +kernel)
  · change ordered (PublicAuthority.authorityFieldNames.map (fun s => encode (.text s))) = true
    decide +kernel

end OriginalCanonical

theorem originalEarlyNameLoaded {trust source key}
    (n : PublicEarlyBody.Name (trust := trust) source key) :
    PublicEarlyBody.loadName source key = some n := by
  unfold PublicEarlyBody.loadName
  split
  · rename_i absent; simp [n.selected] at absent
  · rename_i name selected
    have same := Option.some.inj (selected.symm.trans n.selected)
    subst name; rfl

theorem originalPlanningNameLoaded {earlyTrust trust source key}
    (n : PublicPlanningBody.Name (earlyTrust := earlyTrust) (trust := trust) source key) :
    PublicPlanningBody.loadName source key = some n := by
  unfold PublicPlanningBody.loadName
  split
  · rename_i absent; simp [n.selected] at absent
  · rename_i name selected
    have same := Option.some.inj (selected.symm.trans n.selected)
    subst name; rfl

theorem originalEarlyHeaderLoaded {trust source x}
    (h : PublicEarlyBody.Header (trust := trust) source x) :
    PublicEarlyBody.loadHeader source x = some h := by
  simp only [PublicEarlyBody.loadHeader,originalEarlyNameLoaded h.actor,
    originalEarlyNameLoaded h.height,originalEarlyNameLoaded h.epoch,
    originalEarlyNameLoaded h.config,bind,Option.bind]

theorem originalIscLoaded {earlyTrust trust source x native}
    (p : PublicPlanningBody.IscBody (earlyTrust := earlyTrust) (trust := trust) source x native) :
    PublicPlanningBody.loadIscBody source x native = some p := by
  unfold PublicPlanningBody.loadIscBody
  rw [originalEarlyHeaderLoaded p.header]
  simp only [bind,Option.bind]
  split
  · rename_i absent; simp [p.policySelected] at absent
  · rename_i policy selected
    have same := Option.some.inj (selected.symm.trans p.policySelected)
    subst policy
    split
    · rename_i absent; simp [p.computed] at absent
    · rename_i entries computed
      have same := Option.some.inj (computed.symm.trans p.computed)
      subst entries; rfl

theorem originalEcLoaded {earlyTrust trust source x native}
    (p : PublicPlanningBody.EcBody (earlyTrust := earlyTrust) (trust := trust) source x native) :
    PublicPlanningBody.loadEcBody source x native = some p := by
  unfold PublicPlanningBody.loadEcBody
  rw [originalIscLoaded p.parent]
  simp only [bind,Option.bind,originalPlanningNameLoaded p.seed,originalPlanningNameLoaded p.norm]
  split
  · rename_i absent; simp [p.computed] at absent
  · rename_i members computed
    have same := Option.some.inj (computed.symm.trans p.computed)
    subst members; rfl

theorem originalApcLoaded {earlyTrust trust source x native}
    (p : PublicPlanningBody.ApcBody (earlyTrust := earlyTrust) (trust := trust) source x native) :
    PublicPlanningBody.loadApcBody source x native = some p :=
  PublicPlanningBody.loadApcFromComponents p (originalEcLoaded p.ec) (originalPlanningNameLoaded p.coefficient)

theorem originalAuthorityLoaded {source indices profile quantum current vocabulary configured names earlyTrust planningTrust metadata selected}
    (p : Original source indices profile quantum current vocabulary configured names
      (earlyTrust := earlyTrust) (planningTrust := planningTrust) metadata selected) :
    loadOriginal source indices profile quantum current vocabulary configured names metadata selected = some p := by
  simp only [loadOriginal,originalInputFromComponents p.input,originalHeaderLoaded p.header,
    originalApcLoaded p.parents,bind,Option.bind]

end DeltaReduce.FamilyAuthority
