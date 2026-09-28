import StateFamily
import DeltaReduce.PublicArithmeticInputs
import DeltaReduce.NativeVectorDerivation

/-! R2: select coordinates from the full original input corpus, before any
PARAMETER result or aggregate is available. Selection never creates a protocol
object. The existing complete 23-field public encoder is reused unchanged. -/
namespace DeltaReduce.FamilyInputs
open NativeBinding NativeInputProjection

abbrev Choice (frame : ParameterFrame) :=
  (s : Fin frame.shards.length) → Fin (frame.shards[s.val].length)

theorem collectExists {α β} (f : α → Option β) (xs : List α)
    (total : ∀ x ∈ xs, ∃ y, f x = some y) : ∃ ys, collect f xs = some ys := by
  induction xs with
  | nil => exact ⟨[],rfl⟩
  | cons x xs ih =>
    obtain ⟨y,hy⟩ := total x (List.mem_cons_self)
    obtain ⟨ys,hys⟩ := ih (fun a ha => total a (List.mem_cons_of_mem x ha))
    exact ⟨y::ys,by simp only [collect,hy,hys,bind,Option.bind]⟩

structure Block (codec : Codec) (store : Store) (authority : Authority)
    (frame : ParameterFrame) (assignment : Assignment) where
  slot : Fin frame.shards.length
  key : frame.shards[slot.val].id = assignment.shard
  ordered : assignment.contributions.map (·.ticket) = eligibleDomainTickets frame assignment.domain
  rows : List ParameterKernel.Row
  bound : RowsBound codec store authority.schema frame assignment frame.shards[slot.val].length
    assignment.contributions rows
  numbers : ∀ r ∈ rows,
    ParameterKernel.ReducedNonnegative minInput maxInput r.numerator r.denominator ∧
    assignment.denominator % r.denominator = 0 ∧ ∀ q ∈ r.values, Fits minInput maxInput q

def loadBlock (codec : Codec) (store : Store) (authority : Authority)
    (frame : ParameterFrame) (assignment : Assignment) : Option (Block codec store authority frame assignment) := do
  let slot ← (List.finRange frame.shards.length).find? (fun i => frame.shards[i.val].id == assignment.shard)
  if key : frame.shards[slot.val].id = assignment.shard then
    if ordered : assignment.contributions.map (·.ticket) = eligibleDomainTickets frame assignment.domain then
      let rows ← loadRows codec store authority.schema frame assignment frame.shards[slot.val].length assignment.contributions
      if numbers : ∀ r ∈ rows.val,
          ParameterKernel.ReducedNonnegative minInput maxInput r.numerator r.denominator ∧
          assignment.denominator % r.denominator = 0 ∧ ∀ q ∈ r.values, Fits minInput maxInput q then
        some ⟨slot,key,ordered,rows.val,rows.property,numbers⟩
      else none
    else none
  else none

structure Entry (codec : Codec) (store : Store) (authority : Authority) (frame : ParameterFrame) where
  assignment : Assignment
  block : Block codec store authority frame assignment

inductive Entries (codec : Codec) (store : Store) (authority : Authority) (frame : ParameterFrame) :
    List Assignment → List (Entry codec store authority frame) → Prop where
  | nil : Entries codec store authority frame [] []
  | cons (entry : Entry codec store authority frame) {assignments entries}
      (tail : Entries codec store authority frame assignments entries) :
      Entries codec store authority frame (entry.assignment :: assignments) (entry :: entries)

def loadEntries (codec : Codec) (store : Store) (authority : Authority) (frame : ParameterFrame) :
    (assignments : List Assignment) → Option {entries : List (Entry codec store authority frame) //
      Entries codec store authority frame assignments entries}
  | [] => some ⟨[],.nil⟩
  | assignment :: rest => do
      let block ← loadBlock codec store authority frame assignment
      let tail ← loadEntries codec store authority frame rest
      some ⟨⟨assignment,block⟩ :: tail.val,.cons ⟨assignment,block⟩ tail.property⟩

theorem entryAssignments {codec store authority frame assignments entries}
    (h : Entries codec store authority frame assignments entries) :
    entries.map Entry.assignment = assignments := by
  induction h with
  | nil => rfl
  | cons entry tail ih => simp [ih]

structure Corpus {codec store trust anchor} (binding : Binding codec trust anchor store) where
  frame : ParameterFrame
  origin : FrameOrigin codec store binding.authority frame
  valid : ParameterFrameValid binding.authority binding.profile binding.model binding.optimizer frame
  entries : List (Entry codec store binding.authority frame)
  bound : Entries codec store binding.authority frame frame.plan.assignments entries

def loadCorpus {codec store trust anchor} (binding : Binding codec trust anchor store) : Option (Corpus binding) := do
  let source ← loadParameterFrame codec store binding.authority
  if valid : ParameterFrameValid binding.authority binding.profile binding.model binding.optimizer source.val then
    let entries ← loadEntries codec store binding.authority source.val source.val.plan.assignments
    some ⟨source.val,source.property,valid,entries.val,entries.property⟩
  else none

/- Completeness of the executable source loader on the already bound corpus.
This is not an existence claim for missing source artifacts or omitted tickets. -/
theorem blockLoaderComplete {codec store authority frame assignment}
    (block : Block codec store authority frame assignment)
    (unique : (shardIds frame).Nodup) :
    loadBlock codec store authority frame assignment = some block := by
  have found : (List.finRange frame.shards.length).find?
      (fun i => frame.shards[i.val].id == assignment.shard) = some block.slot := by
    cases h : (List.finRange frame.shards.length).find?
        (fun i => frame.shards[i.val].id == assignment.shard) with
    | none =>
      have rejected := (List.find?_eq_none.mp h) block.slot (List.mem_finRange block.slot)
      simp [block.key] at rejected
    | some slot =>
      have same : frame.shards[slot.val].id = frame.shards[block.slot.val].id := by
        have accepted := List.find?_some h
        simpa only [beq_iff_eq,block.key] using accepted
      have indices : slot.val = block.slot.val :=
        (List.getElem_inj (h₀ := by simpa only [shardIds,List.length_map] using slot.isLt)
          (h₁ := by simpa only [shardIds,List.length_map] using block.slot.isLt) unique).mp
          (by simpa only [shardIds,List.getElem_map] using same)
      have equal : slot = block.slot := Fin.ext indices
      subst slot
      rfl
  cases block with
  | mk slot key ordered rows bound numbers =>
    simp only [loadBlock,found,bind,Option.bind,dif_pos key,dif_pos ordered,
      NativeVectorDerivation.rowsComplete bound,dif_pos numbers]

theorem entriesLoaderComplete {codec store authority frame assignments entries}
    (bound : Entries codec store authority frame assignments entries)
    (unique : (shardIds frame).Nodup) :
    loadEntries codec store authority frame assignments = some ⟨entries,bound⟩ := by
  induction bound with
  | nil => rfl
  | cons entry tail ih =>
    simp only [loadEntries,blockLoaderComplete entry.block unique,ih,bind,Option.bind]

theorem corpusLoaderComplete {codec store trust anchor} {binding : Binding codec trust anchor store}
    (corpus : Corpus binding) : loadCorpus binding = some corpus := by
  have unique : (shardIds corpus.frame).Nodup :=
    corpus.valid.2.2.2.1.imp (fun {a b} less eq => by subst b; exact (String.lt_irrefl a) less)
  cases corpus with
  | mk frame origin valid entries bound =>
    simp only [loadCorpus,NativeVectorDerivation.frameComplete origin,bind,Option.bind,
      dif_pos valid,entriesLoaderComplete bound unique]

/- No default, padding or truncating zip: both full ordered lists must end
together, and every selected cell must exist in its original row. -/
def cellsAt (k : Nat) : List Contribution → List ParameterKernel.Row → Option (List Cell)
  | [], [] => some []
  | c :: cs, r :: rs => do
      let value ← r.values[k]?
      if r.numerator = c.weight.numerator ∧ r.denominator = c.weight.denominator then
        let tail ← cellsAt k cs rs
        some (⟨c,value⟩ :: tail)
      else none
  | _, _ => none

theorem cellSource {k contributions rows cells} (h : cellsAt k contributions rows = some cells)
    {i : Nat} {cell : Cell} (atCell : cells[i]? = some cell) :
    contributions[i]? = some cell.contribution ∧ ∃ row, rows[i]? = some row ∧
      row.values[k]? = some cell.value ∧ row.numerator = cell.contribution.weight.numerator ∧
      row.denominator = cell.contribution.weight.denominator := by
  induction contributions generalizing rows cells i with
  | nil => cases rows <;> simp [cellsAt] at h; subst cells; simp at atCell
  | cons c cs ih =>
    cases rows with
    | nil => simp [cellsAt] at h
    | cons r rs =>
      simp only [cellsAt,bind,Option.bind_eq_some_iff] at h
      obtain ⟨value,hv,last⟩ := h
      split at last <;> try contradiction
      rename_i weights
      simp only [Option.bind_eq_some_iff] at last
      obtain ⟨tail,ht,last⟩ := last
      cases Option.some.inj last
      cases i with
      | zero => simp only [List.getElem?_cons_zero,Option.some.injEq] at atCell
                subst cell; exact ⟨rfl,r,rfl,hv,weights⟩
      | succ i => exact ih ht atCell

theorem cellsComplete {codec store schema frame assignment width contributions rows}
    (h : RowsBound codec store schema frame assignment width contributions rows)
    (k : Nat) (inside : k < width) : ∃ cells, cellsAt k contributions rows = some cells := by
  induction h with
  | nil => exact ⟨[],rfl⟩
  | @cons contribution contributions rows loaded tail ih =>
    obtain ⟨cells,hc⟩ := ih
    have bound : k < loaded.q.values.length := by rw [loaded.shape]; exact inside
    refine ⟨⟨contribution,loaded.q.values[k]⟩ :: cells,?_⟩
    simp [cellsAt,LoadedRow.row,List.getElem?_eq_getElem bound,hc]

theorem cellsContributions {k contributions rows cells}
    (h : cellsAt k contributions rows = some cells) :
    cells.map Cell.contribution = contributions ∧ cells.length = rows.length := by
  induction contributions generalizing rows cells with
  | nil => cases rows <;> simp [cellsAt] at h; subst cells; exact ⟨rfl,rfl⟩
  | cons c cs ih =>
    cases rows with
    | nil => simp [cellsAt] at h
    | cons r rs =>
      simp only [cellsAt,bind,Option.bind_eq_some_iff] at h
      obtain ⟨value,_,last⟩ := h
      split at last <;> try contradiction
      simp only [Option.bind_eq_some_iff] at last
      obtain ⟨tail,ht,last⟩ := last
      cases Option.some.inj last
      exact ⟨by simp [(ih ht).1],by simp [(ih ht).2]⟩

def scalarRows (cells : List Cell) : List ParameterKernel.Row :=
  cells.map (fun c => ⟨c.contribution.weight.numerator,c.contribution.weight.denominator,[c.value]⟩)

theorem selectedRowsExact {k contributions rows cells}
    (h : cellsAt k contributions rows = some cells) :
    scalarRows cells = rows.map (VectorShardRepresentation.rowAt k) := by
  induction contributions generalizing rows cells with
  | nil => cases rows <;> simp [cellsAt] at h
           subst cells; rfl
  | cons c cs ih =>
    cases rows with
    | nil => simp [cellsAt] at h
    | cons r rs =>
      simp only [cellsAt,bind,Option.bind_eq_some_iff] at h
      obtain ⟨value,hv,last⟩ := h
      split at last <;> try contradiction
      rename_i weights
      simp only [Option.bind_eq_some_iff] at last
      obtain ⟨tail,ht,last⟩ := last
      cases Option.some.inj last
      simp only [scalarRows,List.map_cons,VectorShardRepresentation.rowAt,weights.1,weights.2,hv,
        Option.getD_some,← ih ht]

def entryInput {codec store authority frame} (entry : Entry codec store authority frame)
    (choice : Choice frame) : Option AssignmentInput := do
  let cells ← cellsAt (choice entry.block.slot).val entry.assignment.contributions entry.block.rows
  some ⟨entry.assignment.domain,entry.assignment.shard,entry.assignment.denominator,entry.assignment.quantum,cells⟩

theorem entryInputComplete {codec store authority frame}
    (entry : Entry codec store authority frame) (choice : Choice frame) :
    ∃ input, entryInput entry choice = some input := by
  obtain ⟨cells,h⟩ := cellsComplete entry.block.bound _ (choice entry.block.slot).isLt
  exact ⟨⟨entry.assignment.domain,entry.assignment.shard,entry.assignment.denominator,entry.assignment.quantum,cells⟩,
    by simp [entryInput,h]⟩

theorem entryInputLocality {codec store authority frame}
    (entry : Entry codec store authority frame) (a b : Choice frame)
    (same : a entry.block.slot = b entry.block.slot) : entryInput entry a = entryInput entry b := by
  simp only [entryInput,same]

theorem entryInputSource {codec store authority frame entry choice input}
    (h : entryInput (codec := codec) (store := store) (authority := authority) (frame := frame) entry choice = some input) :
    input.domain = entry.assignment.domain ∧ input.shard = entry.assignment.shard ∧
    input.denominator = entry.assignment.denominator ∧ input.quantum = entry.assignment.quantum ∧
    cellsAt (choice entry.block.slot).val entry.assignment.contributions entry.block.rows = some input.cells := by
  simp only [entryInput,bind,Option.bind_eq_some_iff] at h
  obtain ⟨cells,hc,last⟩ := h
  cases Option.some.inj last
  exact ⟨rfl,rfl,rfl,rfl,hc⟩

theorem selectedCellHasOriginalBytes {codec store authority frame entry choice input}
    (h : entryInput (codec := codec) (store := store) (authority := authority) (frame := frame) entry choice = some input)
    {i : Nat} {cell : Cell} (found : input.cells[i]? = some cell) :
    ∃ loaded : LoadedRow codec store authority.schema frame entry.assignment
      frame.shards[entry.block.slot.val].length cell.contribution,
      loaded.q.values[(choice entry.block.slot).val]? = some cell.value ∧
      loaded.q.quantum = input.quantum ∧
      committedQ frame cell.contribution.ticket input.shard = some cell.contribution.q := by
  have src := entryInputSource h
  obtain ⟨hc,row,hr,hv,_⟩ := cellSource src.2.2.2.2 found
  obtain ⟨c,atC,loaded,same⟩ := rowsBoundAt entry.block.bound i row hr
  have equal := Option.some.inj (atC.symm.trans hc)
  subst c
  exact ⟨loaded,by simpa only [same,LoadedRow.row] using hv,
    loaded.quantum.trans src.2.2.2.1.symm,by rw [src.2.1]; exact loaded.committed⟩

theorem selectedCellNumbers {codec store authority frame entry choice input}
    (h : entryInput (codec := codec) (store := store) (authority := authority) (frame := frame) entry choice = some input)
    {i : Nat} {cell : Cell} (found : input.cells[i]? = some cell) :
    ParameterKernel.ReducedNonnegative minInput maxInput cell.contribution.weight.numerator cell.contribution.weight.denominator ∧
    input.denominator % cell.contribution.weight.denominator = 0 ∧ Fits minInput maxInput cell.value := by
  have src := entryInputSource h
  obtain ⟨_,row,atRow,atValue,hn,hd⟩ := cellSource src.2.2.2.2 found
  have checked := entry.block.numbers row (List.mem_of_getElem? atRow)
  rw [hn,hd] at checked
  exact ⟨checked.1,by rw [src.2.2.1]; exact checked.2.1,
    checked.2.2 cell.value (List.mem_of_getElem? atValue)⟩

theorem inputRetainsEligibleOrder {codec store authority frame entry choice input}
    (h : entryInput (codec := codec) (store := store) (authority := authority) (frame := frame) entry choice = some input) :
    input.cells.map (fun c => c.contribution.ticket) = eligibleDomainTickets frame input.domain := by
  have src := entryInputSource h
  have cs := congrArg (List.map Contribution.ticket) (cellsContributions src.2.2.2.2).1
  simpa only [List.map_map,Function.comp_def,src.1] using cs.trans entry.block.ordered

def selectedCurrent (frame : ParameterFrame) (choice : Choice frame) (values : List Int) : Option (List (String × Int)) :=
  collect (fun s : Fin frame.shards.length =>
    (values[frame.shards[s.val].offset + (choice s).val]?).map (frame.shards[s.val].id,·))
    (List.finRange frame.shards.length)

theorem selectedCurrentIsFamily (layout : StateFamily.Layout) (choice : Choice layout.frame)
    (values : List Int) (shape : values.length = layout.frame.coordinates.length) (common : Common) :
    selectedCurrent layout.frame choice values = some
      ((List.finRange layout.frame.shards.length).map (fun s =>
        (layout.frame.shards[s.val].id,(StateFamily.family layout common values shape).view choice s))) := by
  apply StateFamily.collectExact
  intro s _
  have b := (StateFamily.globalIndex layout s (choice s)).isLt
  have inside : layout.frame.shards[s.val].offset + (choice s).val < values.length := by
    rw [shape]; exact b
  simp only [List.getElem?_eq_getElem inside,Option.map_some,StateFamily.family,ShardFamily.project,
    StateFamily.whole,List.getElem_ofFn,StateFamily.globalIndex]
  rfl

theorem selectedCurrentCellSource {frame choice values cells}
    (h : selectedCurrent frame choice values = some cells) {i : Nat} {cell : String × Int}
    (found : cells[i]? = some cell) :
    ∃ s : Fin frame.shards.length, s.val = i ∧ cell.1 = frame.shards[s.val].id ∧
      values[frame.shards[s.val].offset + (choice s).val]? = some cell.2 := by
  obtain ⟨s,hs,hc⟩ := collectAt h i cell found
  have pos : s.val = i := by
    have mapped : (List.range frame.shards.length)[i]? = some s.val := by
      rw [← List.map_coe_finRange_eq_range,List.getElem?_map,hs]
      rfl
    have inside : i < frame.shards.length := by
      simpa using (List.getElem?_eq_some_iff.mp hs).1
    simpa only [List.getElem?_range inside,Option.some.injEq] using mapped.symm
  cases hv : values[frame.shards[s.val].offset + (choice s).val]? with
  | none => simp [hv] at hc
  | some value =>
    simp only [hv,Option.map_some,Option.some.injEq] at hc
    cases hc
    exact ⟨s,pos,rfl,hv⟩

structure Projected {codec store trust anchor} {binding : Binding codec trust anchor store}
    (corpus : Corpus binding) (choice : Choice corpus.frame) (limit : Int) where
  inputs : List AssignmentInput
  source : collect (fun e => entryInput e choice) corpus.entries = some inputs
  tickets : List TicketData
  ticketsLoaded : collect (deriveTicket inputs (shardIds corpus.frame)) corpus.frame.plan.tickets = some tickets
  domains : List DomainData
  domainsLoaded : collect (deriveDomain inputs (shardIds corpus.frame)) (NativeBinding.domains binding.profile) = some domains
  weights : ApplyKernel.WeightPlan minInput maxInput (binding.profile.domainWeights.map (fun d => d.weight.kernelWeight))
  model : List (String × Int)
  modelLoaded : selectedCurrent corpus.frame choice binding.model.values = some model
  optimizer : List (String × Int)
  optimizerLoaded : selectedCurrent corpus.frame choice binding.optimizer.values = some optimizer
  positive : 0 < limit
  ranges : ∀ v ∈ tickets.flatMap (·.q) ++ binding.model.values ++ binding.optimizer.values, Fits (-limit-1) limit v

def project {codec store trust anchor} {binding : Binding codec trust anchor store}
    (corpus : Corpus binding) (choice : Choice corpus.frame) (limit : Int) : Option (Projected corpus choice limit) := do
  let inputs ← collect (fun e => entryInput e choice) corpus.entries
  match hs : collect (fun e => entryInput e choice) corpus.entries,
      ht : collect (deriveTicket inputs (shardIds corpus.frame)) corpus.frame.plan.tickets,
      hd : collect (deriveDomain inputs (shardIds corpus.frame)) (NativeBinding.domains binding.profile),
      hm : selectedCurrent corpus.frame choice binding.model.values,
      ho : selectedCurrent corpus.frame choice binding.optimizer.values with
  | some actual, some tickets, some domains, some model, some optimizer =>
    if equal : actual = inputs then
      let weights ← ApplyKernel.deriveWeightPlan minInput maxInput (binding.profile.domainWeights.map (fun d => d.weight.kernelWeight))
      if checked : 0 < limit ∧ ∀ v ∈ tickets.flatMap (·.q) ++ binding.model.values ++ binding.optimizer.values,
          Fits (-limit-1) limit v then
        some ⟨inputs,by simpa only [equal] using hs,tickets,ht,domains,hd,weights,
          model,hm,optimizer,ho,checked.1,checked.2⟩
      else none
    else none
  | _,_,_,_,_ => none

theorem weightPlanLoaderComplete {lo hi weights} (plan : ApplyKernel.WeightPlan lo hi weights) :
    ApplyKernel.deriveWeightPlan lo hi weights = some plan := by
  unfold ApplyKernel.deriveWeightPlan
  split
  · rename_i absent
    rw [plan.computed] at absent
    contradiction
  · rename_i denominator found
    cases plan with
    | mk d computed nonempty normalized =>
      cases Option.some.inj (found.symm.trans computed)
      rw [dif_pos ⟨nonempty,normalized⟩]

theorem projectFromComputed {codec store trust anchor binding corpus choice limit}
    (p : Projected (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) corpus choice limit) : project corpus choice limit = some p := by
  cases p with
  | mk inputs source tickets ticketsLoaded domains domainsLoaded weights model modelLoaded optimizer optimizerLoaded positive ranges =>
    unfold project
    simp only [source,bind,Option.bind]
    split
    · rename_i actual ts ds ms os hs ht hd hm ho
      cases Option.some.inj (hs.symm.trans source)
      cases Option.some.inj (ht.symm.trans ticketsLoaded)
      cases Option.some.inj (hd.symm.trans domainsLoaded)
      cases Option.some.inj (hm.symm.trans modelLoaded)
      cases Option.some.inj (ho.symm.trans optimizerLoaded)
      simp only [dif_pos True.intro,weightPlanLoaderComplete weights,
        dif_pos (And.intro positive ranges)]
    · simp_all
      rename_i impossible
      exact impossible inputs tickets domains model optimizer rfl ticketsLoaded domainsLoaded rfl rfl

def image {codec store trust anchor binding corpus choice limit}
    (p : Projected (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) corpus choice limit) : PublicArithmeticInputs.Image :=
  ⟨p.tickets,p.domains,shardIds corpus.frame,binding.profile,p.weights.denominator,p.model,p.optimizer,limit⟩

def encode {codec store trust anchor binding corpus choice limit}
    (v : PublicArithmeticInputs.Vocabulary)
    (p : Projected (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) corpus choice limit) := PublicArithmeticInputs.encodeImage v (image p)

theorem completePublicFields {codec store trust anchor binding corpus choice limit v}
    {p : Projected (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) corpus choice limit} (e : PublicArithmeticInputs.Encoded v (image p)) :
    e.components.fields.map Prod.fst = PublicArithmeticInputs.fieldNames := rfl

theorem originalNamespaces {codec store trust anchor binding corpus choice limit}
    (p : Projected (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) corpus choice limit) :
    (image p).shards = shardIds corpus.frame ∧ (image p).profile = binding.profile ∧
    corpus.entries.map Entry.assignment = corpus.frame.plan.assignments := ⟨rfl,rfl,entryAssignments corpus.bound⟩

theorem projectedQSource {codec store trust anchor binding corpus choice limit}
    (p : Projected (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) corpus choice limit) {ti si : Nat} {ticket : TicketData} {value : Int}
    (atTicket : p.tickets[ti]? = some ticket) (atQ : ticket.q[si]? = some value) :
    ∃ entry ∈ corpus.entries, ∃ cell : Cell,
      ∃ loaded : LoadedRow codec store binding.authority.schema corpus.frame entry.assignment
        corpus.frame.shards[entry.block.slot.val].length cell.contribution,
        loaded.q.values[(choice entry.block.slot).val]? = some value ∧
        committedQ corpus.frame cell.contribution.ticket entry.assignment.shard = some cell.contribution.q := by
  obtain ⟨sourceTicket,_,derived⟩ := collectAt p.ticketsLoaded ti ticket atTicket
  obtain ⟨shard,_,q⟩ := collectAt (derivedTicketSource derived).2.2.2 si value atQ
  obtain ⟨input,mem,_,hs,cell,cm,_,cv⟩ := qAtHasExactSource q
  obtain ⟨i,atInput⟩ := List.mem_iff_getElem?.mp mem
  obtain ⟨entry,atEntry,he⟩ := collectAt p.source i input atInput
  obtain ⟨j,atCell⟩ := List.mem_iff_getElem?.mp cm
  obtain ⟨loaded,hv,_,hc⟩ := selectedCellHasOriginalBytes he atCell
  exact ⟨entry,List.mem_of_getElem? atEntry,cell,loaded,by simpa only [cv] using hv,
    by rw [← (entryInputSource he).2.1]; exact hc⟩

section InputGuards
variable {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : Corpus binding} {choice : Choice corpus.frame} {limit : Int}
    (p : Projected corpus choice limit)

theorem projectedInputOrigin {input} (member : input ∈ p.inputs) :
    ∃ entry ∈ corpus.entries, entryInput entry choice = some input ∧
      entry.assignment ∈ corpus.frame.plan.assignments := by
  obtain ⟨i,atInput⟩ := List.mem_iff_getElem?.mp member
  obtain ⟨entry,atEntry,he⟩ := collectAt p.source i input atInput
  have inEntries := List.mem_of_getElem? atEntry
  refine ⟨entry,inEntries,he,?_⟩
  rw [← entryAssignments corpus.bound]
  exact List.mem_map.mpr ⟨entry,inEntries,rfl⟩

theorem projectedTicketNames : p.tickets.map (·.ticket) = corpus.frame.eligible := by
  have names : p.tickets.map (·.ticket) = corpus.frame.plan.tickets.map (·.id) := by
    apply List.ext_getElem?
    intro i
    by_cases hi : i < p.tickets.length
    · obtain ⟨ticket,ht,derived⟩ := collectAt p.ticketsLoaded i p.tickets[i] (List.getElem?_eq_getElem hi)
      simp only [List.getElem?_map,List.getElem?_eq_getElem hi,ht,Option.map_some,
        (derivedTicketSource derived).1]
    · have hn : ¬ i < corpus.frame.plan.tickets.length := by rw [← collectLength p.ticketsLoaded]; exact hi
      simp [List.getElem?_eq_none_iff.mpr (Nat.le_of_not_gt hi),List.getElem?_eq_none_iff.mpr (Nat.le_of_not_gt hn)]
  exact names.trans corpus.valid.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.1

theorem projectedTicketHasExactShape {i : Nat} {ticket : TicketData} (atTicket : p.tickets[i]? = some ticket) :
    ticket.q.length = corpus.frame.shards.length := by
  obtain ⟨source,_,derived⟩ := collectAt p.ticketsLoaded i ticket atTicket
  simpa only [shardIds,List.length_map] using collectLength (derivedTicketSource derived).2.2.2

theorem projectedTicketWeightValid {i : Nat} {ticket} (atTicket : p.tickets[i]? = some ticket) :
    ParameterKernel.ReducedNonnegative minInput maxInput ticket.weight.numerator ticket.weight.denominator := by
  obtain ⟨source,_,derived⟩ := collectAt p.ticketsLoaded i ticket atTicket
  have nonempty : 0 < (shardIds corpus.frame).length := by
    have ne := corpus.valid.2.2.1
    simp only [shardIds,List.length_map]; exact List.length_pos_iff.mpr ne
  obtain ⟨shard,_,q⟩ := collectAt (derivedTicketSource derived).2.2.2 0
    (ticket.q[0]'(by rw [collectLength (derivedTicketSource derived).2.2.2]; exact nonempty))
    (List.getElem?_eq_getElem (by rw [collectLength (derivedTicketSource derived).2.2.2]; exact nonempty))
  obtain ⟨input,mem,_,_,cell,inCells,who,_⟩ := qAtHasExactSource q
  obtain ⟨entry,_,he,_⟩ := projectedInputOrigin p mem
  obtain ⟨j,atCell⟩ := List.mem_iff_getElem?.mp inCells
  have numbers := (selectedCellNumbers he atCell).1
  have inTicket : cell ∈ ticketCells p.inputs source.id := by
    apply List.mem_flatMap.mpr
    exact ⟨input,mem,List.mem_filter.mpr ⟨inCells,by simpa using who⟩⟩
  have same := ticketWeightAgreesWithEveryShard (derivedTicketSource derived).2.2.1 inTicket
  simpa only [same] using numbers

theorem projectedQuantumValid {i j : Nat} {domain quantum}
    (atDomain : p.domains[i]? = some domain) (atQuantum : domain.quantum[j]? = some quantum) :
    positiveQuantum quantum := by
  obtain ⟨name,_,derived⟩ := collectAt p.domainsLoaded i domain atDomain
  obtain ⟨shard,_,hq⟩ := collectAt (derivedDomainSource derived).2.2 j quantum atQuantum
  obtain ⟨input,mem,_,_,same⟩ := quantumAtHasExactSource hq
  obtain ⟨entry,_,he,planned⟩ := projectedInputOrigin p mem
  have assignments := corpus.valid
  simp only [ParameterFrameValid] at assignments
  obtain ⟨_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,safe,_⟩ := assignments
  have quantumSafe := (safe entry.assignment planned).2.2
  rw [← (entryInputSource he).2.2.2.1, same] at quantumSafe
  exact quantumSafe

theorem projectedCurrentRange :
    (∀ cell ∈ p.model, Fits (-limit-1) limit cell.2) ∧
    (∀ cell ∈ p.optimizer, Fits (-limit-1) limit cell.2) := by
  constructor
  · intro cell mem
    obtain ⟨i,atCell⟩ := List.mem_iff_getElem?.mp mem
    obtain ⟨_,_,_,value⟩ := selectedCurrentCellSource p.modelLoaded atCell
    exact p.ranges cell.2 (by simp only [List.mem_append]; exact Or.inl (Or.inr (List.mem_of_getElem? value)))
  · intro cell mem
    obtain ⟨i,atCell⟩ := List.mem_iff_getElem?.mp mem
    obtain ⟨_,_,_,value⟩ := selectedCurrentCellSource p.optimizerLoaded atCell
    exact p.ranges cell.2 (by simp only [List.mem_append]; exact Or.inr (List.mem_of_getElem? value))

end InputGuards
theorem collectedKeys {α β γ} {f : α → Option β} {xs ys} {left : α → γ} {right : β → γ}
    (loaded : collect f xs = some ys)
    (same : ∀ x y, f x = some y → right y = left x) : ys.map right = xs.map left := by
  induction xs generalizing ys with
  | nil => simp [collect] at loaded; subst ys; rfl
  | cons x xs ih =>
    simp only [collect,bind,Option.bind_eq_some_iff] at loaded
    obtain ⟨y,hy,rest,hr,last⟩ := loaded
    cases Option.some.inj last
    simp only [List.map_cons,same x y hy,ih hr]

section InputGuards
variable {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : Corpus binding} {choice : Choice corpus.frame} {limit : Int}
    (p : Projected corpus choice limit)

theorem projectedDomainNames : p.domains.map (·.domain) = NativeBinding.domains binding.profile := by
  have same := collectedKeys (left := fun x : String => x) (right := DomainData.domain)
    p.domainsLoaded (fun _ _ h => (derivedDomainSource h).1)
  simpa using same

theorem projectedDomainShape {i : Nat} {d : DomainData} (atDomain : p.domains[i]? = some d) :
    d.quantum.length = corpus.frame.shards.length := by
  obtain ⟨name,_,derived⟩ := collectAt p.domainsLoaded i d atDomain
  simpa only [shardIds,List.length_map] using collectLength (derivedDomainSource derived).2.2

theorem projectedDomainPositive {i : Nat} {d : DomainData} (atDomain : p.domains[i]? = some d) :
    0 < d.denominator := by
  obtain ⟨name,_,derived⟩ := collectAt p.domainsLoaded i d atDomain
  have nonempty : 0 < (shardIds corpus.frame).length := by
    simp only [shardIds,List.length_map]; exact List.length_pos_iff.mpr corpus.valid.2.2.1
  have inside : 0 < d.quantum.length := by rw [collectLength (derivedDomainSource derived).2.2]; exact nonempty
  obtain ⟨shard,_,hq⟩ := collectAt (derivedDomainSource derived).2.2 0 d.quantum[0]
    (List.getElem?_eq_getElem inside)
  obtain ⟨input,mem,sameDomain,_,_⟩ := quantumAtHasExactSource hq
  obtain ⟨entry,_,he,planned⟩ := projectedInputOrigin p mem
  have assignments := corpus.valid
  simp only [ParameterFrameValid] at assignments
  obtain ⟨_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,safe,_⟩ := assignments
  have pos := (safe entry.assignment planned).1
  have same := domainDenominatorAgreesWithEveryShard (derivedDomainSource derived).2.1 mem sameDomain
  rw [← (entryInputSource he).2.2.1,same] at pos
  exact pos

theorem projectedTicketDenominator {ti di : Nat} {ticket : TicketData} {domain : DomainData}
    (atTicket : p.tickets[ti]? = some ticket) (atDomain : p.domains[di]? = some domain)
    (sameDomain : ticket.domain = domain.domain) : domain.denominator % ticket.weight.denominator = 0 := by
  obtain ⟨sourceTicket,_,derivedTicket⟩ := collectAt p.ticketsLoaded ti ticket atTicket
  obtain ⟨sourceDomain,_,derivedDomain⟩ := collectAt p.domainsLoaded di domain atDomain
  have sourceEqual : sourceTicket.domain = sourceDomain := by
    rw [← (derivedTicketSource derivedTicket).2.1,← (derivedDomainSource derivedDomain).1]
    exact sameDomain
  have nonempty : 0 < (shardIds corpus.frame).length := by
    simp only [shardIds,List.length_map]; exact List.length_pos_iff.mpr corpus.valid.2.2.1
  have inside : 0 < ticket.q.length := by rw [collectLength (derivedTicketSource derivedTicket).2.2.2]; exact nonempty
  obtain ⟨shard,_,hq⟩ := collectAt (derivedTicketSource derivedTicket).2.2.2 0 ticket.q[0]
    (List.getElem?_eq_getElem inside)
  obtain ⟨input,mem,inputDomain,_,cell,inCells,who,_⟩ := qAtHasExactSource hq
  obtain ⟨entry,_,he,_⟩ := projectedInputOrigin p mem
  obtain ⟨ci,atCell⟩ := List.mem_iff_getElem?.mp inCells
  have divisible := (selectedCellNumbers he atCell).2.1
  have inTicket : cell ∈ ticketCells p.inputs sourceTicket.id := by
    apply List.mem_flatMap.mpr
    exact ⟨input,mem,List.mem_filter.mpr ⟨inCells,by simpa using who⟩⟩
  have weight := ticketWeightAgreesWithEveryShard (derivedTicketSource derivedTicket).2.2.1 inTicket
  have denominator := domainDenominatorAgreesWithEveryShard (derivedDomainSource derivedDomain).2.1 mem
    (inputDomain.trans sourceEqual)
  simpa only [weight,denominator] using divisible

theorem projectedTicketDomain {i : Nat} {ticket : TicketData} (atTicket : p.tickets[i]? = some ticket) :
    ticket.domain ∈ p.domains.map (·.domain) := by
  obtain ⟨source,atSource,derived⟩ := collectAt p.ticketsLoaded i ticket atTicket
  rw [projectedDomainNames p,(derivedTicketSource derived).2.1]
  have valid := corpus.valid
  simp only [ParameterFrameValid] at valid
  obtain ⟨_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,domains,_⟩ := valid
  exact domains source (List.mem_of_getElem? atSource)

theorem projectedMixtureGuard :
    0 < p.weights.denominator ∧
    p.weights.denominator = ApplyKernel.foldLcm 1
      (binding.profile.domainWeights.map (fun d => d.weight.denominator.toNat)) ∧
    (∀ d ∈ binding.profile.domainWeights,
      0 ≤ d.weight.numerator ∧ 0 < d.weight.denominator ∧ Int.gcd d.weight.numerator d.weight.denominator = 1 ∧
      (p.weights.denominator : Int) % d.weight.denominator = 0) ∧
    (binding.profile.domainWeights.map (fun d => d.weight.numerator *
      ((p.weights.denominator : Int) / d.weight.denominator))).sum = p.weights.denominator := by
  have source := ApplyKernel.checkedLcmSound _ _ _ _ _ p.weights.computed
  have least := ApplyKernel.weightPlanLeast _ _ _ p.weights
  have weights := ApplyKernel.lcmPrefixesWeights _ _ _ _ source.2.1
  refine ⟨source.2.2.1,?_,?_,?_⟩
  · simpa only [List.map_map,Function.comp_def,Rational.kernelWeight] using source.1
  · intro d hd
    have mem : d.weight.kernelWeight ∈ binding.profile.domainWeights.map (fun d => d.weight.kernelWeight) :=
      List.mem_map.mpr ⟨d,hd,rfl⟩
    have reduced := weights _ mem
    change ParameterKernel.ReducedNonnegative minInput maxInput d.weight.numerator d.weight.denominator at reduced
    have divides := least.2.2.1 _ mem
    have nonneg : 0 ≤ d.weight.denominator := le_of_lt reduced.2.2.1
    have cast : (d.weight.denominator.toNat : Int) = d.weight.denominator := Int.toNat_of_nonneg nonneg
    have intDivides : d.weight.denominator ∣ (p.weights.denominator : Int) := by
      rw [← cast]; exact_mod_cast divides
    exact ⟨reduced.2.1,reduced.2.2.1,reduced.2.2.2.2,Int.emod_eq_zero_of_dvd intDivides⟩
  · have same := p.weights.normalized
    simpa only [List.map_map,Function.comp_def,Rational.kernelWeight,Int.ofNat_eq_natCast] using same

theorem projectedCurrentNames : p.model.map Prod.fst = shardIds corpus.frame ∧
    p.optimizer.map Prod.fst = shardIds corpus.frame := by
  have one (values cells) (loaded : selectedCurrent corpus.frame choice values = some cells) :
      cells.map Prod.fst = shardIds corpus.frame := by
    have same := collectedKeys (left := fun s : Fin corpus.frame.shards.length => corpus.frame.shards[s.val].id)
      (right := Prod.fst) loaded (by
        intro s cell found
        cases value : values[corpus.frame.shards[s.val].offset+(choice s).val]? with
        | none => simp [value] at found
        | some n => simp only [value,Option.map_some,Option.some.injEq] at found
                    cases found; rfl)
    rw [same]
    rw [← List.ofFn_eq_map]
    exact List.ofFn_getElem_eq_map corpus.frame.shards (fun s => s.id)
  exact ⟨one _ _ p.modelLoaded,one _ _ p.optimizerLoaded⟩

/- Numeric clauses of existing ABInputsValid, on the source-derived image.
This is not the theorem that every original native source has such an image.
Namespace/canonical-value checks remain the existing complete encoder's checks. -/
def InputNumericGuards (i : PublicArithmeticInputs.Image) : Prop :=
  0 < i.limit ∧
  i.domains.map (·.domain) = NativeBinding.domains i.profile ∧
  (∀ t ∈ i.tickets,
    t.domain ∈ i.domains.map (·.domain) ∧ t.q.length = i.shards.length ∧
    0 ≤ t.weight.numerator ∧ 0 < t.weight.denominator ∧ Int.gcd t.weight.numerator t.weight.denominator = 1 ∧
    (∀ q ∈ t.q, Fits (-i.limit-1) i.limit q) ∧
    ∀ d ∈ i.domains, t.domain = d.domain → d.denominator % t.weight.denominator = 0) ∧
  (∀ d ∈ i.domains, 0 < d.denominator ∧ d.quantum.length = i.shards.length ∧
    ∀ q ∈ d.quantum, 0 < q.numerator ∧ 0 < q.denominator ∧ Int.gcd q.numerator q.denominator = 1) ∧
  0 < i.mixtureDenominator ∧
  i.mixtureDenominator = ApplyKernel.foldLcm 1 (i.profile.domainWeights.map (fun d => d.weight.denominator.toNat)) ∧
  (∀ d ∈ i.profile.domainWeights, 0 ≤ d.weight.numerator ∧ 0 < d.weight.denominator ∧
    Int.gcd d.weight.numerator d.weight.denominator = 1 ∧ (i.mixtureDenominator : Int) % d.weight.denominator = 0) ∧
  (i.profile.domainWeights.map (fun d => d.weight.numerator * ((i.mixtureDenominator : Int)/d.weight.denominator))).sum = i.mixtureDenominator ∧
  (∀ r ∈ [i.profile.learningRate,i.profile.momentum,i.profile.weightDecay],
    0 ≤ r.numerator ∧ 0 < r.denominator ∧ Int.gcd r.numerator r.denominator = 1) ∧
  0 < i.profile.applyQuantum.numerator ∧ 0 < i.profile.applyQuantum.denominator ∧
  Int.gcd i.profile.applyQuantum.numerator i.profile.applyQuantum.denominator = 1 ∧
  i.model.map Prod.fst = i.shards ∧ i.optimizer.map Prod.fst = i.shards ∧
  (∀ c ∈ i.model, Fits (-i.limit-1) i.limit c.2) ∧
  (∀ c ∈ i.optimizer, Fits (-i.limit-1) i.limit c.2)

theorem allInputNumericGuards : InputNumericGuards (image p) := by
  have valid := corpus.valid
  simp only [ParameterFrameValid] at valid
  obtain ⟨_,_,_,_,_,_,_,_,_,_,quantum,_,_,_,fractions,_⟩ := valid
  have mixture := projectedMixtureGuard p
  refine ⟨p.positive,projectedDomainNames p,?_,?_,mixture.1,mixture.2.1,mixture.2.2.1,
    mixture.2.2.2,?_,quantum.2,quantum.1.2.2.1,quantum.1.2.2.2.2,
    (projectedCurrentNames p).1,(projectedCurrentNames p).2,(projectedCurrentRange p).1,(projectedCurrentRange p).2⟩
  · intro t ht
    obtain ⟨n,atTicket⟩ := List.mem_iff_getElem?.mp ht
    have weight := projectedTicketWeightValid p atTicket
    refine ⟨projectedTicketDomain p atTicket,?_,weight.2.1,weight.2.2.1,weight.2.2.2.2,?_,?_⟩
    · simpa only [image,shardIds,List.length_map] using projectedTicketHasExactShape p atTicket
    · intro q hq
      exact p.ranges q (by simp only [List.mem_append]; exact Or.inl (Or.inl (List.mem_flatMap.mpr ⟨t,ht,hq⟩)))
    · intro d hd same
      obtain ⟨m,atDomain⟩ := List.mem_iff_getElem?.mp hd
      exact projectedTicketDenominator p atTicket atDomain same
  · intro d hd
    obtain ⟨m,atDomain⟩ := List.mem_iff_getElem?.mp hd
    refine ⟨projectedDomainPositive p atDomain,?_,?_⟩
    · simpa only [image,shardIds,List.length_map] using projectedDomainShape p atDomain
    · intro q hq
      obtain ⟨k,atQuantum⟩ := List.mem_iff_getElem?.mp hq
      have checked := projectedQuantumValid p atDomain atQuantum
      exact ⟨checked.2,checked.1.2.2.1,checked.1.2.2.2.2⟩
  · intro r hr
    have checked := fractions r hr
    exact ⟨checked.2.1,checked.2.2.1,checked.2.2.2.2⟩

end InputGuards


theorem onlyMember {α} {xs : List α} {x y} (selected : only xs = some x) (member : y ∈ xs) : y = x := by
  rw [onlyExact selected] at member
  exact List.mem_singleton.mp member

theorem qAtAgreesWithCell {inputs : List AssignmentInput} {input : AssignmentInput} {cell : Cell}
    (inInputs : input ∈ inputs) (inCells : cell ∈ input.cells) {value : Int}
    (computed : qAt inputs cell.contribution.ticket input.domain input.shard = some value) : value = cell.value := by
  simp only [qAt,bind,Option.bind_eq_some_iff] at computed
  obtain ⟨assignment,selected,c,hc,last⟩ := computed
  have sameA : input = assignment := onlyMember selected (List.mem_filter.mpr ⟨inInputs,by simp⟩)
  subst assignment
  have sameC : cell = c := onlyMember hc (List.mem_filter.mpr ⟨inCells,by simp⟩)
  subst c
  exact (Option.some.inj last).symm

theorem collectedAtInput {α β} {f : α → Option β} {xs ys} (loaded : collect f xs = some ys)
    {i : Nat} {x y} (atX : xs[i]? = some x) (selected : f x = some y) : ys[i]? = some y := by
  have inside : i < ys.length := by rw [collectLength loaded]; exact (List.getElem?_eq_some_iff.mp atX).1
  obtain ⟨x',atX',selected'⟩ := collectAt loaded i ys[i] (List.getElem?_eq_getElem inside)
  have sameX := Option.some.inj (atX'.symm.trans atX)
  subst x'
  have sameY := Option.some.inj (selected'.symm.trans selected)
  simpa only [sameY] using List.getElem?_eq_getElem inside

theorem collectInputHasOutput {α β} {f : α → Option β} {xs ys} (loaded : collect f xs = some ys)
    {x : α} (member : x ∈ xs) : ∃ y ∈ ys, f x = some y := by
  obtain ⟨i,atX⟩ := List.mem_iff_getElem?.mp member
  have inside : i < ys.length := by rw [collectLength loaded]; exact (List.getElem?_eq_some_iff.mp atX).1
  obtain ⟨x',atX',selected⟩ := collectAt loaded i ys[i] (List.getElem?_eq_getElem inside)
  have sameX := Option.some.inj (atX'.symm.trans atX)
  subst x'
  exact ⟨ys[i],List.getElem_mem inside,selected⟩

theorem derivedTicketFilterNames {inputs shards source tickets}
    (loaded : collect (deriveTicket inputs shards) source = some tickets) (domain : String) :
    (tickets.filter (fun t => t.domain == domain)).map (·.ticket) =
      (source.filter (fun t => t.domain == domain)).map (·.id) := by
  induction source generalizing tickets with
  | nil => simp [collect] at loaded; subst tickets; rfl
  | cons t ts ih =>
    simp only [collect,bind,Option.bind_eq_some_iff] at loaded
    obtain ⟨ticket,computed,tail,ht,last⟩ := loaded
    cases Option.some.inj last
    have same := derivedTicketSource computed
    by_cases selected : t.domain = domain
    · simp [same.2.1,selected,same.1,ih ht]
    · simp [same.2.1,selected,ih ht]

theorem collectPaired {α β γ κ} {xs : List α} {ys : List β}
    {left : α → κ} {right : β → κ} {f : α → Option γ} {g : β → γ}
    (keys : xs.map left = ys.map right)
    (computed : ∀ a ∈ xs, ∀ b ∈ ys, left a = right b → f a = some (g b)) :
    collect f xs = some (ys.map g) := by
  induction xs generalizing ys with
  | nil => cases ys <;> simp_all [collect]
  | cons a xs ih =>
    cases ys with
    | nil => simp at keys
    | cons b ys =>
      have same := List.cons.inj keys
      have head := computed a List.mem_cons_self b List.mem_cons_self same.1
      have tail := ih same.2 (fun x hx y hy => computed x (List.mem_cons_of_mem _ hx) y (List.mem_cons_of_mem _ hy))
      simp only [collect,head,tail,List.map_cons,bind,Option.bind]

def readImageRow (coordinate : Nat) (ticket : TicketData) : Option ParameterKernel.Row :=
  (ticket.q[coordinate]?).map (fun q => ⟨ticket.weight.numerator,ticket.weight.denominator,[q]⟩)

def imageRows (i : PublicArithmeticInputs.Image) (domain : String) (coordinate : Nat) : Option (List ParameterKernel.Row) :=
  collect (readImageRow coordinate) (i.tickets.filter (fun t => t.domain == domain))

section Image
variable {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : Corpus binding} {choice : Choice corpus.frame} {limit : Int}
    (p : Projected corpus choice limit)

theorem selectedInputIsExposed (entry : Entry codec store binding.authority corpus.frame)
    (member : entry ∈ corpus.entries) {input} (selected : entryInput entry choice = some input) : input ∈ p.inputs := by
  obtain ⟨output,mem,computed⟩ := collectInputHasOutput p.source member
  have same := Option.some.inj (computed.symm.trans selected)
  simpa only [same] using mem

theorem exposedTicketForCell {input : AssignmentInput} (inInputs : input ∈ p.inputs)
    {cell : Cell} (inCells : cell ∈ input.cells) :
    ∃ ticket ∈ p.tickets, ticket.ticket = cell.contribution.ticket ∧ ticket.domain = input.domain ∧
      ticket.weight = cell.contribution.weight ∧
      collect (qAt p.inputs cell.contribution.ticket input.domain) (shardIds corpus.frame) = some ticket.q := by
  obtain ⟨entry,_,selected,_⟩ := projectedInputOrigin p inInputs
  have order := inputRetainsEligibleOrder selected
  have member : cell.contribution.ticket ∈ eligibleDomainTickets corpus.frame input.domain := by
    rw [← order]; exact List.mem_map.mpr ⟨cell,inCells,rfl⟩
  obtain ⟨source,mem,who⟩ := List.mem_map.mp member
  have filtered := List.mem_filter.mp mem
  have domain : source.domain = input.domain := by simpa using filtered.2
  obtain ⟨ticket,inTickets,derived⟩ := collectInputHasOutput p.ticketsLoaded filtered.1
  have src := derivedTicketSource derived
  have cellMember : cell ∈ ticketCells p.inputs source.id := by
    apply List.mem_flatMap.mpr
    exact ⟨input,inInputs,List.mem_filter.mpr ⟨inCells,by simp [who]⟩⟩
  have weight := ticketWeightAgreesWithEveryShard src.2.2.1 cellMember
  refine ⟨ticket,inTickets,src.1.trans who,src.2.1.trans domain,weight.symm,?_⟩
  simpa only [who,domain] using src.2.2.2

theorem exposedCellValue {input : AssignmentInput} (inInputs : input ∈ p.inputs)
    {cell : Cell} (inCells : cell ∈ input.cells) (k : Nat)
    (shardAt : (shardIds corpus.frame)[k]? = some input.shard) :
    ∃ ticket ∈ p.tickets, ticket.ticket = cell.contribution.ticket ∧ ticket.domain = input.domain ∧
      ticket.weight = cell.contribution.weight ∧ ticket.q[k]? = some cell.value := by
  obtain ⟨ticket,mem,who,domain,weight,loaded⟩ := exposedTicketForCell p inInputs inCells
  have inside : k < ticket.q.length := by rw [collectLength loaded]; exact (List.getElem?_eq_some_iff.mp shardAt).1
  obtain ⟨s,atS,computed⟩ := collectAt loaded k ticket.q[k] (List.getElem?_eq_getElem inside)
  have same := Option.some.inj (atS.symm.trans shardAt)
  subst s
  have value := qAtAgreesWithCell inInputs inCells computed
  exact ⟨ticket,mem,who,domain,weight,by simpa only [value] using List.getElem?_eq_getElem inside⟩

theorem publicOrderIsNativeMemberOrder {input : AssignmentInput} (inInputs : input ∈ p.inputs) :
    (p.tickets.filter (fun t => t.domain == input.domain)).map (·.ticket) =
      input.cells.map (fun c => c.contribution.ticket) := by
  obtain ⟨_,_,selected,_⟩ := projectedInputOrigin p inInputs
  rw [derivedTicketFilterNames p.ticketsLoaded,inputRetainsEligibleOrder selected]
  rfl

theorem publicRowsAreSelectedNativeRows {input : AssignmentInput} (inInputs : input ∈ p.inputs)
    (k : Nat) (shardAt : (shardIds corpus.frame)[k]? = some input.shard) :
    imageRows (image p) input.domain k = some (scalarRows input.cells) := by
  have unique : (p.tickets.map (·.ticket)).Nodup := by
    rw [projectedTicketNames p]
    exact corpus.valid.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.1.imp
      (fun h eq => by subst eq; exact String.lt_irrefl _ h)
  apply collectPaired (left := TicketData.ticket) (right := fun c : Cell => c.contribution.ticket)
    (publicOrderIsNativeMemberOrder p inInputs)
  intro ticket inTickets cell inCells same
  obtain ⟨original,member,who,_,weight,value⟩ := exposedCellValue p inInputs inCells k shardAt
  have equal : ticket = original := List.inj_on_of_nodup_map unique
    (List.mem_of_mem_filter inTickets) member (same.trans who.symm)
  subst ticket
  simp only [readImageRow,value,Option.map_some,weight]

end Image

theorem selectedCurrentNames {frame : ParameterFrame} {choice : Choice frame} {values cells}
    (loaded : selectedCurrent frame choice values = some cells) :
    cells.map Prod.fst = shardIds frame := by
  have same := collectedKeys (left := fun s : Fin frame.shards.length => frame.shards[s.val].id)
    (right := Prod.fst) loaded (by
      intro s cell found
      cases value : values[frame.shards[s.val].offset+(choice s).val]? with
      | none => simp [value] at found
      | some n => simp only [value,Option.map_some,Option.some.injEq] at found
                  cases found; rfl)
  rw [same]
  rw [← List.ofFn_eq_map]
  exact List.ofFn_getElem_eq_map frame.shards (fun s => s.id)

theorem selectedCurrentAt {frame : ParameterFrame} {choice : Choice frame} {values cells}
    (loaded : selectedCurrent frame choice values = some cells) (s : Fin frame.shards.length) {v : Int}
    (atValue : values[frame.shards[s.val].offset+(choice s).val]? = some v) :
    cells[s.val]? = some (frame.shards[s.val].id,v) := by
  apply collectedAtInput loaded (x := s)
  · simp
  · simp only [atValue,Option.map_some]

end DeltaReduce.FamilyInputs
