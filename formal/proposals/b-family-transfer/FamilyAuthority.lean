import FamilyInputs
import DeltaReduce.PublicAuthority

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
  encoded : Encoded vocabulary (FamilyInputs.image input)
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
    (vocabulary : Vocabulary) {metadataTrust} (source : Metadata metadataTrust) :
    Option (Projection input vocabulary source) := do
  let encoded ← FamilyInputs.encode vocabulary input
  let header ← loadHeader binding source
  let entryValues ← PublicAuthority.loadEntries source binding.authority.isc vocabulary corpus.frame.commitments
  match hm : collect vocabulary.ticket corpus.frame.members, he : collect vocabulary.ticket corpus.frame.eligible with
  | some members, some eligible =>
      if valid : members.Nodup ∧ (∀ name ∈ members, name ∈ vocabulary.tickets) ∧ eligible.Nodup then
        some ⟨encoded,header,entryValues.val,entryValues.property,members,hm,valid.1,valid.2.1,eligible,he,valid.2.2⟩
      else none
  | _,_ => none

structure Checked {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : FamilyInputs.Corpus binding} {choice : FamilyInputs.Choice corpus.frame} {limit : Int} (input : FamilyInputs.Projected corpus choice limit)
    (vocabulary : Vocabulary) {metadataTrust} (source : Metadata metadataTrust) where
  projection : Projection input vocabulary source
  canonical : PublicState.canonical vocabulary.models projection.value = true

def check {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : FamilyInputs.Corpus binding} {choice : FamilyInputs.Choice corpus.frame} {limit : Int} (input : FamilyInputs.Projected corpus choice limit)
    (vocabulary : Vocabulary) {metadataTrust} (source : Metadata metadataTrust) (candidate : Value) :
    Option (Checked input vocabulary source) := do
  let p ← project input vocabulary source
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
  change eligible ∈ input.tickets.map (·.ticket) at inEligible
  rw [FamilyInputs.projectedTicketNames input] at inEligible
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
      (metadataTrust := metadataTrust) source) : project input vocabulary source = some p := by
  unfold project
  change (PublicArithmeticInputs.encodeImage vocabulary (FamilyInputs.image input) >>= _) = some p
  rw [encodeImageFromComputed p.encoded]
  simp only [bind,Option.bind,headerLoaderComplete p.header,entriesLoaderComplete p.entryOrigin]
  split
  · rename_i members eligible hm he
    have sameMembers := Option.some.inj (hm.symm.trans p.members)
    have sameEligible := Option.some.inj (he.symm.trans p.eligible)
    subst members; subst eligible
    rw [dif_pos ⟨p.memberUnique,p.memberConfigured,p.eligibleUnique⟩]
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
    ∃ checked, check input vocabulary source p.value = some checked ∧ checked.projection = p := by
  have safe := constructedAuthorityCanonical p header entryAtoms eligibleAtoms entryUnique eligibleUnique
  unfold check
  rw [projectFromComputed p]
  simp only [bind,Option.bind]
  rw [dif_pos ⟨safe,by trivial⟩]
  exact ⟨_,rfl,rfl⟩

end CanonicalAuthority
end DeltaReduce.FamilyAuthority
