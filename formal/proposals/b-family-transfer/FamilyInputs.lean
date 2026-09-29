import StateFamily
import ManifestFamily
import DeltaReduce.NativeStateArtifacts
import DeltaReduce.NativeStateProjection
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

instance (i : PublicArithmeticInputs.Image) : Decidable (InputNumericGuards i) := by
  unfold InputNumericGuards Fits
  infer_instance

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

/- R2.1: total configured-ticket image. An excluded ticket's arithmetic cells
are latent in the public model: ABMembers selects the APC member set before
reading them. The deterministic neutral completion below is explicitly NOT a
claim about unavailable original Q bytes or an invented contribution. Original
commitments/ISC/EC members remain separate and unchanged. Active rows are copied
exactly, and source/configuration correspondence is still checked separately. -/
def activeNames (active : List TicketData) : List String := active.map (·.ticket)

def completeTicket (width : Nat) (active : List TicketData) (ticket : Ticket) : TicketData :=
  match active.find? (fun t => t.ticket == ticket.id) with
  | some row => row
  | none => ⟨ticket.id,ticket.domain,⟨0,1⟩,List.replicate width 0⟩

def completeTickets (width : Nat) (configured : List Ticket) (active : List TicketData) : List TicketData :=
  configured.map (completeTicket width active)

theorem completionKeepsTicket (width : Nat) (active : List TicketData) (ticket : Ticket) :
    (completeTicket width active ticket).ticket = ticket.id := by
  unfold completeTicket
  split
  · rename_i row found
    simpa only [beq_iff_eq] using List.find?_some found
  · rfl

theorem completionExactUniverse (width : Nat) (configured : List Ticket) (active : List TicketData) :
    (completeTickets width configured active).map (·.ticket) = configured.map (·.id) := by
  simp only [completeTickets,List.map_map,Function.comp_def,completionKeepsTicket]

theorem completionRetainsActive (width : Nat) {active : List TicketData}
    (unique : (activeNames active).Nodup) {row : TicketData} (member : row ∈ active)
    (ticket : Ticket) (same : ticket.id = row.ticket) :
    completeTicket width active ticket = row := by
  have found : active.find? (fun t => t.ticket == ticket.id) = some row := by
    cases h : active.find? (fun t => t.ticket == ticket.id) with
    | none =>
      have absent := List.find?_eq_none.mp h row member
      simp only [same,beq_self_eq_true] at absent
      contradiction
    | some other =>
      have equal : other = row := List.inj_on_of_nodup_map unique
        (List.mem_of_find?_eq_some h) member (by simpa only [beq_iff_eq,same] using List.find?_some h)
      subst other
      rfl
  simp only [completeTicket,found]

theorem completionInactiveIsLatent (width : Nat) (active : List TicketData) (ticket : Ticket)
    (absent : ticket.id ∉ activeNames active) :
    completeTicket width active ticket = ⟨ticket.id,ticket.domain,⟨0,1⟩,List.replicate width 0⟩ := by
  have missing : active.find? (fun t => t.ticket == ticket.id) = none := by
    apply List.find?_eq_none.mpr
    intro row member
    have different : row.ticket ≠ ticket.id := by
      intro equal
      exact absent (List.mem_map.mpr ⟨row,member,equal⟩)
    simpa only [Bool.not_eq_true,beq_iff_eq] using different
  simp only [completeTicket,missing]

def memberTickets (members : List String) (tickets : List TicketData) : List TicketData :=
  tickets.filter (fun t => members.contains t.ticket)

theorem completionSelection (width : Nat) (configured : List Ticket) (active : List TicketData) :
    memberTickets (activeNames active) (completeTickets width configured active) =
      (configured.filter (fun t => (activeNames active).contains t.id)).map (completeTicket width active) := by
  simp only [memberTickets,completeTickets,List.filter_map,Function.comp_def,completionKeepsTicket]

theorem completionSelectedRowsExact (width : Nat) (configured : List Ticket) (active : List TicketData)
    (unique : (activeNames active).Nodup)
    (order : (configured.filter (fun t => (activeNames active).contains t.id)).map (·.id) = activeNames active) :
    memberTickets (activeNames active) (completeTickets width configured active) = active := by
  rw [completionSelection]
  have same := collectPaired (f := fun t : Ticket => some (completeTicket width active t))
    (g := id) order (by
      intro ticket _ row member key
      exact congrArg some (completionRetainsActive width unique member ticket key))
  have total : ∀ xs : List Ticket, collect (fun t => some (completeTicket width active t)) xs =
      some (xs.map (completeTicket width active)) := by
    intro xs
    induction xs with
    | nil => rfl
    | cons t ts ih => simp only [collect,List.map_cons,bind,Option.bind,ih]
  rw [total,List.map_id] at same
  exact Option.some.inj same

def completedImage (base : PublicArithmeticInputs.Image) (configured : List Ticket) : PublicArithmeticInputs.Image :=
  { base with tickets := completeTickets base.shards.length configured base.tickets }

def memberImageRows (i : PublicArithmeticInputs.Image) (members : List String)
    (domain : String) (coordinate : Nat) : Option (List ParameterKernel.Row) :=
  collect (readImageRow coordinate) ((memberTickets members i.tickets).filter (fun t => t.domain == domain))

theorem completedImageComputesSameRows (base : PublicArithmeticInputs.Image) (configured : List Ticket)
    (unique : (activeNames base.tickets).Nodup)
    (order : (configured.filter (fun t => (activeNames base.tickets).contains t.id)).map (·.id) = activeNames base.tickets)
    (domain : String) (coordinate : Nat) :
    memberImageRows (completedImage base configured) (activeNames base.tickets) domain coordinate =
      imageRows base domain coordinate := by
  unfold memberImageRows completedImage
  rw [completionSelectedRowsExact _ _ _ unique order]
  rfl

theorem completedImageNumericGuards (base : PublicArithmeticInputs.Image) (configured : List Ticket)
    (safe : InputNumericGuards base)
    (domains : ∀ ticket ∈ configured, ticket.domain ∈ base.domains.map (·.domain)) :
    InputNumericGuards (completedImage base configured) := by
  refine ⟨safe.1,safe.2.1,?_,safe.2.2.2⟩
  intro row member
  obtain ⟨ticket,configuredTicket,rfl⟩ := List.mem_map.mp member
  unfold completeTicket
  split
  · rename_i actual found
    exact safe.2.2.1 actual (List.mem_of_find?_eq_some found)
  · refine ⟨domains ticket configuredTicket,by simp [completedImage],
      by change (0 : Int) ≤ 0; decide,by change (0 : Int) < 1; decide,
      by change Int.gcd 0 1 = 1; decide,?_,?_⟩
    · intro q member
      have equal : q = 0 := List.eq_of_mem_replicate member
      subst q
      have positive := safe.1
      change Fits (-base.limit-1) base.limit 0
      constructor <;> omega
    · intro d _ _
      exact Int.emod_one d.denominator

/- The configuration supplies only existing ticket/domain identities. It does
not supply an expected translated body or an assertion of arithmetic success. -/
def CompletionCoverage (base : PublicArithmeticInputs.Image) (configured : List Ticket) : Prop :=
  (configured.map (·.id)).Nodup ∧ (activeNames base.tickets).Nodup ∧
  (configured.filter (fun t => (activeNames base.tickets).contains t.id)).map (·.id) = activeNames base.tickets ∧
  (∀ ticket ∈ configured, ticket.domain ∈ base.domains.map (·.domain)) ∧
  ∀ ticket ∈ configured, ∀ row ∈ base.tickets, ticket.id = row.ticket → ticket.domain = row.domain
instance (base configured) : Decidable (CompletionCoverage base configured) := by
  unfold CompletionCoverage
  infer_instance

structure Completed (base : PublicArithmeticInputs.Image) where
  configured : List Ticket
  coverage : CompletionCoverage base configured

def complete (base : PublicArithmeticInputs.Image) (configured : List Ticket) : Option (Completed base) :=
  if valid : CompletionCoverage base configured then some ⟨configured,valid⟩ else none

theorem completionCheckedExactly {base configured out} (accepted : complete base configured = some out) :
    out.configured = configured ∧ CompletionCoverage base configured := by
  unfold complete at accepted
  split at accepted <;> try contradiction
  cases Option.some.inj accepted
  exact ⟨rfl,by assumption⟩

theorem completeFromSource {base} (source : Completed base) :
    complete base source.configured = some source := by
  cases source with
  | mk configured coverage => exact dif_pos coverage

theorem completedTicketDomain {base} (completion : Completed base) {ticket : Ticket}
    (member : ticket ∈ completion.configured) :
    (completeTicket base.shards.length base.tickets ticket).domain = ticket.domain := by
  unfold completeTicket
  split
  · rename_i row found
    have same : row.ticket = ticket.id := by
      simpa only [beq_iff_eq] using List.find?_some found
    exact (completion.coverage.2.2.2.2 ticket member row (List.mem_of_find?_eq_some found)
      same.symm).symm
  · rfl

theorem completedHasNoDuplicateTickets {base} (completion : Completed base) :
    ((completedImage base completion.configured).tickets.map (·.ticket)).Nodup := by
  rw [show (completedImage base completion.configured).tickets =
    completeTickets base.shards.length completion.configured base.tickets from rfl,completionExactUniverse]
  exact completion.coverage.1

theorem excludedCellsNeverEnterParameter {base} (completion : Completed base) (domain : String) (coordinate : Nat) :
    memberImageRows (completedImage base completion.configured) (activeNames base.tickets) domain coordinate =
      imageRows base domain coordinate :=
  completedImageComputesSameRows base completion.configured completion.coverage.2.1 completion.coverage.2.2.1 domain coordinate

/- Direct input-side transfer from the original manifest. In particular it
never passes through NativeVectorLayout.Small, generated coordinate labels or
a packed draft Q artifact. Every selected cell still belongs to its original
block and the common carrier retains that manifest and all its original bytes. -/

/- The old member adapter imposed a 4096-ticket bound unrelated to the native
certificate limit. Keep every source/context/member check, but let the original
certificate decoder enforce its own existing bounds. This is a projection
adapter only; no native validator or production transition changes. -/
def OriginalPlanParents (e : NativePlanLineage.Edge) : Prop :=
  e.parent.certificate.body.context = e.certificate.common.context ∧
  e.ec.certificate.common.context = e.certificate.common.context ∧
  e.seed.transcript.context = e.certificate.common.context ∧
  e.ec.norm.evidence.context = e.certificate.common.context ∧
  e.certificate.common.isc = e.parent.qcId ∧
  e.ec.certificate.common.isc = e.parent.qcId ∧
  e.seed.transcript.isc = e.parent.qcId ∧ e.ec.norm.evidence.isc = e.parent.qcId ∧
  e.certificate.common.ec = e.ec.id ∧ e.certificate.common.seed = e.seed.id ∧
  e.ec.seedId = e.seed.id ∧ e.ec.norm.id = e.ec.certificate.common.norm ∧
  (e.parent.certificate.body.tuples.map NativeInputSetBody.Tuple.ticket).Nodup ∧
  e.ec.norm.evidence.entries.map NativeNormEvidence.Entry.ticket =
    e.parent.certificate.body.tuples.map NativeInputSetBody.Tuple.ticket
instance (e) : Decidable (OriginalPlanParents e) := by unfold OriginalPlanParents; infer_instance

theorem originalParentsFromOld {e} (parents : NativePlanMembers.CrossParents e) : OriginalPlanParents e := by
  unfold NativePlanMembers.CrossParents at parents
  unfold OriginalPlanParents
  tauto

def deriveOriginalPlanRows (e : NativePlanLineage.Edge) : Option (List NativePlanMembers.Row) := do
  if OriginalPlanParents e then
    let all ← NativePlanMembers.align e.parent.certificate.body.tuples e.ec.certificate.common.entries
    NativePlanMembers.attach (NativePlanMembers.eligible all) e.certificate.common.weights e.certificate.common.buckets
  else none

theorem originalPlanRowsFromComponents {e all rows} (parents : OriginalPlanParents e)
    (members : NativePlanMembers.align e.parent.certificate.body.tuples e.ec.certificate.common.entries = some all)
    (eligible : NativePlanMembers.attach (NativePlanMembers.eligible all) e.certificate.common.weights e.certificate.common.buckets = some rows) :
    deriveOriginalPlanRows e = some rows := by
  simp only [deriveOriginalPlanRows,if_pos parents,members,bind,Option.bind,eligible]

structure OriginalPlanSource (sha : Bytes → Bytes) (policyRaw stateRaw apcId : Bytes)
    (b : NativePlanMembers.Bound) : Prop where
  plans : NativePlanSection.prepare sha policyRaw stateRaw = some b.plans
  edge : b.plans.certificates.find? (fun e => e.id == apcId) = some b.edge
  finalized : apcId ∈ b.plans.finalized
  rows : deriveOriginalPlanRows b.edge = some b.rows

def prepareOriginalMembers (sha : Bytes → Bytes) (policyRaw stateRaw apcId : Bytes) :
    Option (NativePlanMembers.Bound) := do
  let plans ← NativePlanSection.prepare sha policyRaw stateRaw
  let edge ← plans.certificates.find? (fun e => e.id == apcId)
  if apcId ∈ plans.finalized then
    let rows ← deriveOriginalPlanRows edge
    some ⟨plans,edge,rows⟩
  else none

theorem originalPlanPrepared {sha policyRaw stateRaw apcId b}
    (loaded : prepareOriginalMembers sha policyRaw stateRaw apcId = some b) :
    OriginalPlanSource sha policyRaw stateRaw apcId b := by
  simp only [prepareOriginalMembers,bind,Option.bind_eq_some_iff] at loaded
  obtain ⟨plans,hp,edge,he,last⟩ := loaded
  split at last <;> try contradiction
  rename_i finalized
  obtain ⟨rows,hr,last⟩ := Option.bind_eq_some_iff.mp last
  cases Option.some.inj last
  exact ⟨hp,he,finalized,hr⟩

theorem originalPlanPreparedFromSource {sha policyRaw stateRaw apcId b}
    (p : OriginalPlanSource sha policyRaw stateRaw apcId b) :
    prepareOriginalMembers sha policyRaw stateRaw apcId = some b := by
  simp only [prepareOriginalMembers,p.plans,p.edge,bind,Option.bind,if_pos p.finalized,p.rows]

theorem originalPlanExactMembers {e rows} (loaded : deriveOriginalPlanRows e = some rows) :
    OriginalPlanParents e ∧ ∃ all, all.map NativePlanMembers.Member.input = e.parent.certificate.body.tuples ∧
      all.map NativePlanMembers.Member.eligibility = e.ec.certificate.common.entries ∧
      rows.map NativePlanMembers.Row.member = NativePlanMembers.eligible all ∧
      rows.map NativePlanMembers.Row.weight = e.certificate.common.weights ∧
      rows.map NativePlanMembers.Row.bucket = e.certificate.common.buckets ∧
      ∀ r ∈ rows, NativePlanMembers.RowValid r := by
  unfold deriveOriginalPlanRows at loaded
  split at loaded <;> try contradiction
  rename_i parents
  obtain ⟨all,ha,hr⟩ := Option.bind_eq_some_iff.mp loaded
  exact ⟨parents,all,(NativePlanMembers.alignedSource ha).1,(NativePlanMembers.alignedSource ha).2.1,
    (NativePlanMembers.attachedSource hr).1,(NativePlanMembers.attachedSource hr).2⟩

structure OriginalCoefficientSource (sha : Bytes → Bytes)
    (policyRaw stateRaw apcId configRaw proofRaw profileRaw : Bytes) (b : NativePlanCoefficients.Bound) : Prop where
  members : OriginalPlanSource sha policyRaw stateRaw apcId b.members
  accumulator : NativeAccumulatorBinding.load (NativePlanCoefficients.contentHash sha) configRaw proofRaw profileRaw
    b.members.edge.certificate.common.accumulator = some b.accumulator
  links : NativePlanCoefficients.ConfigLinks b.members b.accumulator
  coefficients : NativePlanCoefficients.check b.accumulator.numbers b.members.rows = some b.coefficients

def prepareOriginalCoefficients (sha : Bytes → Bytes)
    (policyRaw stateRaw apcId configRaw proofRaw profileRaw : Bytes) : Option NativePlanCoefficients.Bound := do
  let members ← prepareOriginalMembers sha policyRaw stateRaw apcId
  let accumulator ← NativeAccumulatorBinding.load (NativePlanCoefficients.contentHash sha) configRaw proofRaw profileRaw
    members.edge.certificate.common.accumulator
  if NativePlanCoefficients.ConfigLinks members accumulator then
    let terms ← NativePlanCoefficients.check accumulator.numbers members.rows
    some ⟨members,accumulator,terms⟩
  else none

theorem originalCoefficientsPrepared {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw b}
    (loaded : prepareOriginalCoefficients sha policyRaw stateRaw apcId configRaw proofRaw profileRaw = some b) :
    OriginalCoefficientSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw b := by
  simp only [prepareOriginalCoefficients,bind,Option.bind_eq_some_iff] at loaded
  obtain ⟨members,hm,accumulator,ha,last⟩ := loaded
  split at last <;> try contradiction
  rename_i links
  obtain ⟨terms,ht,last⟩ := Option.bind_eq_some_iff.mp last
  cases Option.some.inj last
  exact ⟨originalPlanPrepared hm,ha,links,ht⟩

theorem originalCoefficientsFromSource {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw b}
    (p : OriginalCoefficientSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw b) :
    prepareOriginalCoefficients sha policyRaw stateRaw apcId configRaw proofRaw profileRaw = some b := by
  simp only [prepareOriginalCoefficients,originalPlanPreparedFromSource p.members,p.accumulator,
    bind,Option.bind,if_pos p.links,p.coefficients]

structure OriginalRowsSource (sha : Bytes → Bytes) (policyRaw stateRaw apcId configRaw proofRaw profileRaw : Bytes)
    (permission : NativeAvailableQ.Permission) (inputs : List NativeAvailableQ.Input) (source : NativePlanQCorpus.Bound) : Prop where
  plan : OriginalCoefficientSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw source.plan
  rows : NativePlanQCorpus.Rows sha configRaw proofRaw profileRaw source.plan permission source.plan.coefficients inputs source.rows

structure OriginalVectorSource (sha : Bytes → Bytes) (policyRaw stateRaw apcId configRaw proofRaw profileRaw : Bytes)
    (permission : NativeAvailableQ.Permission) (inputs : List NativeAvailableQ.Input) (source : NativeVectorContext.Bound) : Prop where
  corpus : OriginalRowsSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source.source
  first : source.source.rows.head? = some source.first
  compatible : ∀ r ∈ source.source.rows, NativeVectorContext.Compatible source.first.corpus.manifest r.corpus.manifest

def prepareOriginalVector (sha : Bytes → Bytes) (policyRaw stateRaw apcId configRaw proofRaw profileRaw : Bytes)
    (permission : NativeAvailableQ.Permission) (inputs : List NativeAvailableQ.Input) : Option NativeVectorContext.Bound := do
  let plan ← prepareOriginalCoefficients sha policyRaw stateRaw apcId configRaw proofRaw profileRaw
  let rows ← NativePlanQCorpus.loadRows sha configRaw proofRaw profileRaw plan permission plan.coefficients inputs
  NativeVectorContext.align ⟨plan,rows⟩

theorem originalVectorPrepared {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source}
    (loaded : prepareOriginalVector sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs = some source) :
    OriginalVectorSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source := by
  simp only [prepareOriginalVector,bind,Option.bind_eq_some_iff] at loaded
  obtain ⟨plan,hp,rows,hr,ha⟩ := loaded
  have aligned := NativeVectorContext.aligned ha
  refine ⟨?_,?_,?_⟩
  · rw [aligned.1]
    exact ⟨originalCoefficientsPrepared hp,NativePlanQCorpus.rowsSource hr⟩
  · rw [aligned.1]; exact aligned.2.1
  · rw [aligned.1]; exact aligned.2.2

theorem originalVectorPreparedFromSource {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source}
    (p : OriginalVectorSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source) :
    prepareOriginalVector sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs = some source := by
  simp only [prepareOriginalVector,originalCoefficientsFromSource p.corpus.plan,
    NativePlanQCorpus.rowsFromSources p.corpus.rows,bind,Option.bind]
  have computed := NativeVectorContext.alignFromSources p.first p.compatible
  simpa only [show NativeVectorContext.Bound.mk source.source source.first = source from by cases source; rfl] using computed

theorem originalRowsFromOld {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source}
    (loaded : NativePlanQCorpus.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs = some source) :
    OriginalRowsSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source := by
  have original := NativePlanQCorpus.boundSource loaded
  have plan := NativePlanCoefficients.boundSource original.1
  have members := NativePlanMembers.preparedSource plan.members
  have derived := NativePlanMembers.derivedSource members.rows
  have rows : deriveOriginalPlanRows source.plan.members.edge = some source.plan.members.rows := by
    unfold deriveOriginalPlanRows
    rw [if_pos (originalParentsFromOld derived.parents)]
    obtain ⟨all,ha,hr⟩ := derived.members
    simp only [ha,bind,Option.bind,hr]
  exact ⟨⟨⟨members.plans,members.edge,members.finalized,rows⟩,plan.accumulator,plan.links,plan.coefficients⟩,original.2⟩

theorem originalVectorFromOld {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source}
    (loaded : NativeVectorContext.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs = some source) :
    OriginalVectorSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source := by
  have src := NativeVectorContext.boundSource loaded
  exact ⟨originalRowsFromOld src.1,src.2.1,src.2.2⟩

theorem originalVectorSourceParts {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source}
    (p : OriginalVectorSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source) :
    OriginalRowsSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source.source ∧
    source.source.rows.head? = some source.first ∧
    ∀ r ∈ source.source.rows, NativeVectorContext.Compatible source.first.corpus.manifest r.corpus.manifest :=
  ⟨p.corpus,p.first,p.compatible⟩

theorem originalRowsSourceParts {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source}
    (p : OriginalRowsSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source) :
    OriginalCoefficientSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw source.plan ∧
    NativePlanQCorpus.Rows sha configRaw proofRaw profileRaw source.plan permission source.plan.coefficients inputs source.rows :=
  ⟨p.plan,p.rows⟩

theorem originalSourceRows {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source}
    (p : OriginalVectorSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source) :
    source.source.rows.map (fun r => r.term.source) = source.source.plan.members.rows ∧
    source.source.rows.length = inputs.length := by
  have rows := NativePlanQCorpus.completeRows p.corpus.rows
  have coefficients := (NativePlanCoefficients.checked p.corpus.plan.coefficients).2
  refine ⟨?_,rows.2⟩
  have mapped := congrArg (List.map NativePlanCoefficients.Term.source) rows.1
  simpa only [List.map_map,Function.comp_def,coefficients,NativePlanCoefficients.sourceRows] using mapped

theorem originalCoefficientIdentity {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw b term}
    (source : OriginalCoefficientSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw b)
    (member : term ∈ b.coefficients) :
    term.source ∈ b.members.rows ∧ term.coefficient = NativePlanCoefficients.coefficient b.accumulator.numbers term.source := by
  rw [(NativePlanCoefficients.checked source.coefficients).2] at member
  exact NativePlanCoefficients.termSource member

theorem originalCoordinateRange {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source}
    (loaded : OriginalRowsSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source)
    (r : NativePlanQCorpus.Row) (member : r ∈ source.rows) {block coordinate value}
    (atValue : NativeAvailableQ.coordinate r.corpus.manifest block coordinate = some value) : |value| ≤ 32767 := by
  obtain ⟨_,_,_,_,row⟩ := NativePlanQCorpus.rowMember loaded.rows r member
  exact NativeAvailableQ.coordinateRange (NativePlanQCorpus.rowSource row).2.1 atValue

section OriginalManifest
variable {hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws manifest}
    (loaded : NativeManifestBinding.bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws = some manifest)
    (selection : ShardFamily.Selector (ManifestFamily.layout loaded))
    (weight : Rational)

def manifestTicket : TicketData :=
  ⟨NativeVectorLayout.text manifest.manifest.wire.ticket,
    NativeVectorLayout.text manifest.manifest.wire.domain,weight,
    List.ofFn (fun s => (ManifestFamily.family loaded ()).view selection s)⟩

theorem manifestTicketShape : (manifestTicket loaded selection weight).q.length = manifest.blocks.length :=
  List.length_ofFn

theorem manifestTicketCoordinate (s : Fin manifest.blocks.length) :
    (manifestTicket loaded selection weight).q[s.val]? =
      manifest.blocks[s.val].block.frame.values[(selection s).val]? := by
  have shape := ManifestFamily.corpusShapes (NativeManifestBinding.fullOrderedCorpus loaded)
    manifest.blocks[s.val] (List.getElem_mem s.isLt)
  have inside : (selection s).val < manifest.blocks[s.val].block.frame.values.length := by
    rw [shape]; exact (selection s).isLt
  have slot : s.val < (ManifestFamily.layout loaded).count := s.isLt
  simp only [manifestTicket,List.getElem?_ofFn,dif_pos slot,List.getElem?_eq_getElem inside]
  rfl

theorem manifestTicketRange : ∀ value ∈ (manifestTicket loaded selection weight).q, |value| ≤ 32767 := by
  intro value member
  obtain ⟨s,rfl⟩ := List.mem_ofFn.mp member
  have shape := ManifestFamily.corpusShapes (NativeManifestBinding.fullOrderedCorpus loaded)
    manifest.blocks[s.val] (List.getElem_mem s.isLt)
  have inside : (selection s).val < manifest.blocks[s.val].block.frame.values.length := by
    rw [shape]; exact (selection s).isLt
  exact NativeAvailableQ.originalRange loaded manifest.blocks[s.val] (List.getElem_mem s.isLt) _
    (List.getElem_mem inside)

theorem manifestTicketRetainsOriginal (control : Control) :
    (ShardFamily.scalarView (ManifestFamily.family loaded control) selection).1 = (manifest,raws,control) ∧
    (manifestTicket loaded selection weight).ticket = NativeVectorLayout.text manifest.manifest.wire.ticket ∧
    (manifestTicket loaded selection weight).domain = NativeVectorLayout.text manifest.manifest.wire.domain ∧
    (manifestTicket loaded selection weight).weight = weight := ⟨rfl,rfl,rfl,rfl⟩

theorem manifestTicketAllPublicRanges (limit : Int) (large : 32767 ≤ limit) :
    ∀ value ∈ (manifestTicket loaded selection weight).q, Fits (-limit-1) limit value := by
  intro value member
  have range := abs_le.mp (manifestTicketRange loaded selection weight value member)
  constructor <;> omega

end OriginalManifest

def selectOriginalManifest (manifest : NativeManifestBinding.Bound) (indices : List Nat) : Option (List Int) :=
  if shape : indices.length = manifest.blocks.length then
    collect (fun s : Fin manifest.blocks.length =>
      manifest.blocks[s.val].block.frame.values[indices[s.val]'(by rw [shape]; exact s.isLt)]?)
      (List.finRange manifest.blocks.length)
  else none

theorem selectOriginalManifestFromFamily {hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws manifest}
    (loaded : NativeManifestBinding.bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws = some manifest)
    (selection : ShardFamily.Selector (ManifestFamily.layout loaded)) (weight : Rational) :
    selectOriginalManifest manifest (List.ofFn (fun s => (selection s).val)) =
      some (manifestTicket loaded selection weight).q := by
  unfold selectOriginalManifest
  rw [dif_pos (by simp only [List.length_ofFn]; rfl)]
  change collect _ (List.finRange manifest.blocks.length) = some (List.ofFn _)
  conv_rhs => rw [List.ofFn_eq_map]
  apply StateFamily.collectExact
  intro s _
  have shape := ManifestFamily.corpusShapes (NativeManifestBinding.fullOrderedCorpus loaded)
    manifest.blocks[s.val] (List.getElem_mem s.isLt)
  have inside : (selection s).val < manifest.blocks[s.val].block.frame.values.length := by
    rw [shape]; exact (selection s).isLt
  simp only [List.getElem_ofFn]
  change manifest.blocks[s.val].block.frame.values[(selection s).val]? =
    some (manifest.blocks[s.val].block.frame.values[(selection s).val]'inside)
  exact List.getElem?_eq_getElem inside

def readOriginalRowTicket (row : NativePlanQCorpus.Row) (indices : List Nat) : Option TicketData := do
  let cells ← selectOriginalManifest row.corpus.manifest indices
  some ⟨NativeVectorLayout.text row.corpus.manifest.manifest.wire.ticket,
    NativeVectorLayout.text row.corpus.manifest.manifest.wire.domain,
    ⟨row.term.source.weight.numerator,row.term.source.weight.denominator⟩,cells⟩

def loadOriginalRowTicket (sha : Bytes → Bytes) (configRaw proofRaw profileRaw : Bytes)
    (plan : NativePlanCoefficients.Bound) (permission : NativeAvailableQ.Permission)
    (term : NativePlanCoefficients.Term) (original : NativeAvailableQ.Input) (indices : List Nat) : Option TicketData := do
  let row ← NativePlanQCorpus.loadRow sha configRaw proofRaw profileRaw plan permission term original
  readOriginalRowTicket row indices

section OriginalRow
variable {sha configRaw proofRaw profileRaw plan permission term original row}
    (loaded : NativePlanQCorpus.loadRow sha configRaw proofRaw profileRaw plan permission term original = some row)

include loaded in
theorem rowManifestSource : NativeManifestBinding.bind (NativePlanCoefficients.contentHash sha)
    original.schemaRaw original.scaleRaw original.planRaw original.manifestRaw original.manifestId original.raws =
      some row.corpus.manifest :=
  NativeAvailableQ.manifestSource (NativePlanQCorpus.rowSource loaded).2.1

def originalRowTicket
    (selection : ShardFamily.Selector (ManifestFamily.layout (rowManifestSource loaded))) : TicketData :=
  manifestTicket (rowManifestSource loaded) selection
    ⟨row.term.source.weight.numerator,row.term.source.weight.denominator⟩

theorem originalRowIdentity
    (selection : ShardFamily.Selector (ManifestFamily.layout (rowManifestSource loaded))) :
    (originalRowTicket loaded selection).ticket = NativeVectorLayout.text term.source.member.input.ticket ∧
    (originalRowTicket loaded selection).domain = NativeVectorLayout.text term.source.member.input.domain ∧
    (originalRowTicket loaded selection).weight =
      ⟨term.source.weight.numerator,term.source.weight.denominator⟩ := by
  have source := NativePlanQCorpus.rowSource loaded
  have ticket : row.corpus.manifest.manifest.wire.ticket = term.source.member.input.ticket :=
    source.2.2.2.1.2.symm.trans source.2.2.2.2.1
  have domain := source.2.2.2.2.2.2.2.1
  exact ⟨congrArg NativeVectorLayout.text ticket,congrArg NativeVectorLayout.text domain,
    by simp only [originalRowTicket,manifestTicket,source.1]⟩

theorem originalRowFullPublicRanges
    (selection : ShardFamily.Selector (ManifestFamily.layout (rowManifestSource loaded)))
    (limit : Int) (large : 32767 ≤ limit) :
    ∀ value ∈ (originalRowTicket loaded selection).q, Fits (-limit-1) limit value :=
  manifestTicketAllPublicRanges (rowManifestSource loaded) selection _ limit large

theorem originalRowConstructorTotal
    (selection : ShardFamily.Selector (ManifestFamily.layout (rowManifestSource loaded))) :
    loadOriginalRowTicket sha configRaw proofRaw profileRaw plan permission term original
      (List.ofFn (fun s => (selection s).val)) = some (originalRowTicket loaded selection) := by
  simp only [loadOriginalRowTicket,loaded,bind,Option.bind,readOriginalRowTicket,
    selectOriginalManifestFromFamily (rowManifestSource loaded) selection
      ⟨row.term.source.weight.numerator,row.term.source.weight.denominator⟩]
  rfl

end OriginalRow

/- One common coordinate choice is checked against the original ordered shard
headers. Compatibility transports it to every original eligible ticket; this
does not allocate a shard, vote, certificate or WAL slot for a coordinate. -/
def OriginalSelectionFits (manifest : NativeManifestBinding.Bound) (indices : List Nat) : Prop :=
  indices.length = manifest.blocks.length ∧
  ∀ (i : Nat) (q : NativeScaleBinding.Bound), manifest.blocks[i]? = some q →
    ∃ k, indices[i]? = some k ∧ k < (NativeVectorContext.shape q).entry.count

theorem originalSelectionFromFamily {hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws manifest}
    (loaded : NativeManifestBinding.bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws = some manifest)
    (selection : ShardFamily.Selector (ManifestFamily.layout loaded)) :
    OriginalSelectionFits manifest (List.ofFn (fun s => (selection s).val)) := by
  refine ⟨List.length_ofFn,?_⟩
  intro i q found
  have inside := (List.getElem?_eq_some_iff.mp found).1
  have same : manifest.blocks[i] = q := (List.getElem?_eq_some_iff.mp found).2
  refine ⟨(selection ⟨i,inside⟩).val,?_,?_⟩
  · simp only [List.getElem?_ofFn]
    exact dif_pos (show i < (ManifestFamily.layout loaded).count from inside)
  · rw [← same]; exact (selection ⟨i,inside⟩).isLt

theorem originalSelectionCompatible {first other indices}
    (compatible : NativeVectorContext.Compatible first other)
    (selected : OriginalSelectionFits first indices) : OriginalSelectionFits other indices := by
  refine ⟨selected.1.trans (NativeVectorContext.sameBlockCount compatible).symm,?_⟩
  intro i q found
  have reverse : NativeVectorContext.Compatible other first :=
    ⟨compatible.1.symm,compatible.2.1.symm,compatible.2.2.symm⟩
  obtain ⟨original,atOriginal,same⟩ := NativeVectorContext.sameSlot reverse found
  obtain ⟨k,atIndex,inside⟩ := selected.2 i original atOriginal
  exact ⟨k,atIndex,by simpa only [same] using inside⟩

theorem originalManifestSelectionTotal {hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws manifest indices}
    (loaded : NativeManifestBinding.bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws = some manifest)
    (selected : OriginalSelectionFits manifest indices) :
    ∃ cells, selectOriginalManifest manifest indices = some cells := by
  unfold selectOriginalManifest
  rw [dif_pos selected.1]
  apply collectExists
  intro s _
  obtain ⟨k,atIndex,inside⟩ := selected.2 s.val manifest.blocks[s.val] (List.getElem?_eq_getElem s.isLt)
  have indexBound : s.val < indices.length := by rw [selected.1]; exact s.isLt
  have indexSame : indices[s.val] = k := (List.getElem?_eq_some_iff.mp atIndex).2
  have shape := ManifestFamily.corpusShapes (NativeManifestBinding.fullOrderedCorpus loaded)
    manifest.blocks[s.val] (List.getElem_mem s.isLt)
  have coordinateBound : indices[s.val] < manifest.blocks[s.val].block.frame.values.length := by
    rw [indexSame,shape]; exact inside
  exact ⟨_,List.getElem?_eq_getElem coordinateBound⟩

theorem originalRowSelectionTotal {sha configRaw proofRaw profileRaw plan permission term original row indices}
    (loaded : NativePlanQCorpus.loadRow sha configRaw proofRaw profileRaw plan permission term original = some row)
    (selected : OriginalSelectionFits row.corpus.manifest indices) :
    ∃ ticket, readOriginalRowTicket row indices = some ticket := by
  obtain ⟨cells,computed⟩ := originalManifestSelectionTotal (rowManifestSource loaded) selected
  exact ⟨_,by simp only [readOriginalRowTicket,computed,bind,Option.bind]; rfl⟩

def readOriginalTickets (source : NativeVectorContext.Bound) (indices : List Nat) : Option (List TicketData) :=
  collect (fun row => readOriginalRowTicket row indices) source.source.rows

theorem originalTicketsConstructorTotal
    {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source indices}
    (loaded : OriginalVectorSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source)
    (selected : OriginalSelectionFits source.first.corpus.manifest indices) :
    ∃ tickets, readOriginalTickets source indices = some tickets := by
  apply collectExists
  intro row member
  have context := originalVectorSourceParts loaded
  obtain ⟨term,_,original,_,rowSource⟩ := NativePlanQCorpus.rowMember
    (originalRowsSourceParts context.1).2 row member
  exact originalRowSelectionTotal rowSource
    (originalSelectionCompatible (context.2.2 row member) selected)

theorem readOriginalTicketIdentity {row indices ticket}
    (loaded : readOriginalRowTicket row indices = some ticket) :
    ticket.ticket = NativeVectorLayout.text row.corpus.manifest.manifest.wire.ticket ∧
    ticket.domain = NativeVectorLayout.text row.corpus.manifest.manifest.wire.domain ∧
    ticket.weight = ⟨row.term.source.weight.numerator,row.term.source.weight.denominator⟩ := by
  simp only [readOriginalRowTicket,bind,Option.bind_eq_some_iff] at loaded
  obtain ⟨_,_,last⟩ := loaded
  cases Option.some.inj last
  exact ⟨rfl,rfl,rfl⟩

theorem selectedManifestCellsSource {manifest indices cells}
    (selected : selectOriginalManifest manifest indices = some cells) :
    cells.length = manifest.blocks.length ∧ ∀ (i : Nat) (value : Int), cells[i]? = some value →
      ∃ q k, manifest.blocks[i]? = some q ∧ indices[i]? = some k ∧
        q.block.frame.values[k]? = some value := by
  unfold selectOriginalManifest at selected
  split at selected <;> try contradiction
  rename_i shape
  refine ⟨(collectLength selected).trans List.length_finRange,?_⟩
  intro i value atCell
  obtain ⟨s,atSlot,atValue⟩ := collectAt selected i value atCell
  have same : s.val = i := by
    have index : (List.range manifest.blocks.length)[i]? = some s.val := by
      rw [← List.map_coe_finRange_eq_range,List.getElem?_map,atSlot]
      rfl
    have inside : i < manifest.blocks.length := by
      simpa only [List.length_finRange] using (List.getElem?_eq_some_iff.mp atSlot).1
    simpa only [List.getElem?_range inside,Option.some.injEq] using index.symm
  subst i
  have inside : s.val < indices.length := by rw [shape]; exact s.isLt
  refine ⟨manifest.blocks[s.val],indices[s.val],?_,?_,atValue⟩
  · exact List.getElem?_eq_getElem s.isLt
  · exact List.getElem?_eq_getElem inside

theorem readOriginalTicketCells {row indices ticket}
    (loaded : readOriginalRowTicket row indices = some ticket) :
    selectOriginalManifest row.corpus.manifest indices = some ticket.q := by
  simp only [readOriginalRowTicket,bind,Option.bind_eq_some_iff] at loaded
  obtain ⟨_,cells,last⟩ := loaded
  cases Option.some.inj last
  exact cells

theorem originalTicketsPublicCells
    {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source indices tickets}
    (loaded : OriginalVectorSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source)
    (computed : readOriginalTickets source indices = some tickets) :
    ∀ ticket ∈ tickets, ticket.q.length = source.first.corpus.manifest.blocks.length ∧
      ∀ value ∈ ticket.q, |value| ≤ 32767 := by
  intro ticket member
  obtain ⟨position,atTicket⟩ := List.mem_iff_getElem?.mp member
  obtain ⟨row,atRow,derived⟩ := collectAt computed position ticket atTicket
  have rowMember := List.mem_of_getElem? atRow
  have context := originalVectorSourceParts loaded
  have cells := selectedManifestCellsSource (readOriginalTicketCells derived)
  refine ⟨cells.1.trans (NativeVectorContext.sameBlockCount (context.2.2 row rowMember)),?_⟩
  intro value memberValue
  obtain ⟨coordinate,atValue⟩ := List.mem_iff_getElem?.mp memberValue
  obtain ⟨q,k,atBlock,_,lookup⟩ := cells.2 coordinate value atValue
  apply originalCoordinateRange context.1 row rowMember
    (block := coordinate) (coordinate := k)
  simp only [NativeAvailableQ.coordinate,atBlock,bind,Option.bind,lookup]

theorem originalTicketsFullOrderedSource
    {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source indices tickets}
    (loaded : OriginalVectorSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source)
    (computed : readOriginalTickets source indices = some tickets) :
    tickets.length = inputs.length ∧
    tickets.map (fun t => (t.ticket,t.domain,t.weight)) =
      source.source.plan.members.rows.map (fun r =>
        (NativeVectorLayout.text r.member.input.ticket,NativeVectorLayout.text r.member.input.domain,
          (⟨r.weight.numerator,r.weight.denominator⟩ : Rational))) := by
  have context := originalVectorSourceParts loaded
  have sources := originalRowsSourceParts context.1
  refine ⟨(collectLength computed).trans (NativePlanQCorpus.completeRows sources.2).2,?_⟩
  have keys := collectedKeys computed (left := fun row : NativePlanQCorpus.Row =>
      (NativeVectorLayout.text row.corpus.manifest.manifest.wire.ticket,
        NativeVectorLayout.text row.corpus.manifest.manifest.wire.domain,
        (⟨row.term.source.weight.numerator,row.term.source.weight.denominator⟩ : Rational)))
    (right := fun t : TicketData => (t.ticket,t.domain,t.weight))
    (fun _ _ accepted => by
      have h := readOriginalTicketIdentity accepted
      exact congrArg₂ Prod.mk h.1 (congrArg₂ Prod.mk h.2.1 h.2.2))
  rw [keys,← (originalSourceRows loaded).1,List.map_map]
  apply List.map_congr_left
  intro row member
  obtain ⟨term,_,original,_,head⟩ := NativePlanQCorpus.rowMember sources.2 row member
  have bound := NativePlanQCorpus.rowSource head
  have ticket : row.corpus.manifest.manifest.wire.ticket = term.source.member.input.ticket :=
    bound.2.2.2.1.2.symm.trans bound.2.2.2.2.1
  have domain := bound.2.2.2.2.2.2.2.1
  simp only [Function.comp_def,bound.1,ticket,domain]

def originalShardNames (manifest : NativeManifestBinding.Bound) : List String :=
  manifest.blocks.map (fun q => NativeVectorLayout.shardName q.block.header.ordinal)

def selectOriginalCurrent (manifest : NativeManifestBinding.Bound) (indices : List Nat)
    (values : List Int) : Option (List (String × Int)) :=
  if shape : indices.length = manifest.blocks.length then
    collect (fun s : Fin manifest.blocks.length =>
      let q := manifest.blocks[s.val]
      (values[q.block.header.start + indices[s.val]'(by rw [shape]; exact s.isLt)]?).map
        (fun value => (NativeVectorLayout.shardName q.block.header.ordinal,value)))
      (List.finRange manifest.blocks.length)
  else none

theorem originalCurrentSelectionTotal {hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws manifest indices values}
    (loaded : NativeManifestBinding.bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws = some manifest)
    (selected : OriginalSelectionFits manifest indices)
    (shape : values.length = manifest.plan.inputs.schema.total) :
    ∃ cells, selectOriginalCurrent manifest indices values = some cells := by
  unfold selectOriginalCurrent
  rw [dif_pos selected.1]
  apply collectExists
  intro s _
  obtain ⟨k,atIndex,inside⟩ := selected.2 s.val manifest.blocks[s.val] (List.getElem?_eq_getElem s.isLt)
  have indexBound : s.val < indices.length := by rw [selected.1]; exact s.isLt
  have indexSame : indices[s.val] = k := (List.getElem?_eq_some_iff.mp atIndex).2
  have member : (NativeVectorContext.shape manifest.blocks[s.val]).entry ∈ manifest.plan.plan.entries := by
    rw [← NativeVectorContext.originalPlanSlots loaded]
    exact List.mem_map.mpr ⟨_,List.getElem_mem s.isLt,rfl⟩
  have bound := NativeShardPartition.spanBounds
    (NativeShardPlanBinding.completePartition (NativeManifestBinding.boundSource loaded).plan).2.2 member
  have global : manifest.blocks[s.val].block.header.start + indices[s.val] < values.length := by
    rw [shape,indexSame]
    dsimp only [NativeVectorContext.shape,NativeShardPlanBinding.headerEntry] at inside bound
    omega
  refine ⟨(NativeVectorLayout.shardName manifest.blocks[s.val].block.header.ordinal,
    values[manifest.blocks[s.val].block.header.start + indices[s.val]]),?_⟩
  dsimp only
  rw [List.getElem?_eq_getElem global]
  rfl

theorem originalCurrentKeys {manifest indices values cells}
    (loaded : selectOriginalCurrent manifest indices values = some cells) :
    cells.map Prod.fst = originalShardNames manifest := by
  unfold selectOriginalCurrent at loaded
  split at loaded <;> try contradiction
  have keys := collectedKeys loaded (left := fun s : Fin manifest.blocks.length =>
      NativeVectorLayout.shardName manifest.blocks[s.val].block.header.ordinal) (right := Prod.fst)
    (fun s cell accepted => by
      obtain ⟨_,_,same⟩ := Option.map_eq_some_iff.mp accepted
      cases same; rfl)
  rw [keys]
  simp only [originalShardNames,← List.ofFn_eq_map]
  exact List.ofFn_getElem_eq_map manifest.blocks (fun q => NativeVectorLayout.shardName q.block.header.ordinal)

theorem originalCurrentCellSource {manifest indices values cells}
    (loaded : selectOriginalCurrent manifest indices values = some cells) {cell}
    (member : cell ∈ cells) : cell.2 ∈ values := by
  unfold selectOriginalCurrent at loaded
  split at loaded <;> try contradiction
  obtain ⟨i,atCell⟩ := List.mem_iff_getElem?.mp member
  obtain ⟨s,_,read⟩ := collectAt loaded i cell atCell
  obtain ⟨value,lookup,same⟩ := Option.map_eq_some_iff.mp read
  cases same
  exact List.mem_of_getElem? lookup

theorem originalCurrentAt {manifest indices values cells}
    (loaded : selectOriginalCurrent manifest indices values = some cells)
    (s : Fin manifest.blocks.length) {coordinate value}
    (atIndex : indices[s.val]? = some coordinate)
    (atValue : values[manifest.blocks[s.val].block.header.start+coordinate]? = some value) :
    cells[s.val]? = some (NativeVectorLayout.shardName manifest.blocks[s.val].block.header.ordinal,value) := by
  unfold selectOriginalCurrent at loaded
  split at loaded <;> try contradiction
  rename_i shape
  have inside : s.val < indices.length := by rw [shape]; exact s.isLt
  have index : indices[s.val] = coordinate := (List.getElem?_eq_some_iff.mp atIndex).2
  apply collectedAtInput loaded (x := s)
  · simp
  · dsimp only
    rw [index,atValue]
    rfl

def originalImageValue (source : NativeVectorContext.Bound) (profile : NativeApplyProfile.Profile)
    (applyQuantum : Rational) (tickets : List TicketData) (model optimizer : List (String × Int)) :
    PublicArithmeticInputs.Image :=
  let manifest := source.first.corpus.manifest
  let publicProfile := NativeStateArtifacts.profileValue source.source.plan.accumulator.numbers.accumulatorBits applyQuantum profile
  { tickets := tickets
    domains := profile.weights.map (fun weight =>
      ⟨NativeVectorLayout.text weight.domain,source.source.plan.accumulator.numbers.denominator,
        manifest.blocks.map NativeScaleBinding.Bound.quantum⟩)
    shards := originalShardNames manifest
    profile := publicProfile
    mixtureDenominator := ApplyKernel.foldLcm 1 (profile.weights.map (·.fraction.denominator))
    model := model
    optimizer := optimizer
    limit := NativeAccumulatorBinding.limit source.source.plan.accumulator.numbers.accumulatorBits }

def readOriginalImage (source : NativeVectorContext.Bound) (indices : List Nat)
    (profile : NativeApplyProfile.Profile) (applyQuantum : Rational) (current : NativeCurrentValues.Image) :
    Option PublicArithmeticInputs.Image := do
  let tickets ← readOriginalTickets source indices
  let model ← selectOriginalCurrent source.first.corpus.manifest indices current.model
  let optimizer ← selectOriginalCurrent source.first.corpus.manifest indices current.optimizer
  some (originalImageValue source profile applyQuantum tickets model optimizer)

theorem originalImageConstructorTotal
    {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source indices}
    (loaded : OriginalVectorSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source)
    (selected : OriginalSelectionFits source.first.corpus.manifest indices)
    (profile : NativeApplyProfile.Profile) (applyQuantum : Rational) (current : NativeCurrentValues.Image)
    (shape : current.model.length = source.first.corpus.manifest.plan.inputs.schema.total ∧
      current.optimizer.length = current.model.length) :
    ∃ image, readOriginalImage source indices profile applyQuantum current = some image := by
  obtain ⟨tickets,ticketsComputed⟩ := originalTicketsConstructorTotal loaded selected
  have context := originalVectorSourceParts loaded
  have firstMember := List.mem_of_head? context.2.1
  obtain ⟨term,_,original,_,row⟩ := NativePlanQCorpus.rowMember
    (originalRowsSourceParts context.1).2 source.first firstMember
  obtain ⟨model,modelComputed⟩ := originalCurrentSelectionTotal (rowManifestSource row) selected shape.1
  obtain ⟨optimizer,optimizerComputed⟩ := originalCurrentSelectionTotal (rowManifestSource row) selected (shape.2.trans shape.1)
  exact ⟨_,by simp only [readOriginalImage,ticketsComputed,modelComputed,optimizerComputed,bind,Option.bind]; rfl⟩

theorem originalTicketNumericSource
    {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source indices tickets}
    (loaded : OriginalVectorSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source)
    (computed : readOriginalTickets source indices = some tickets) {ticket}
    (member : ticket ∈ tickets) :
    ∃ row ∈ source.source.rows,
      ticket.ticket = NativeVectorLayout.text row.term.source.member.input.ticket ∧
      ticket.domain = NativeVectorLayout.text row.term.source.member.input.domain ∧
      ticket.weight = ⟨row.term.source.weight.numerator,row.term.source.weight.denominator⟩ ∧
      0 ≤ ticket.weight.numerator ∧ 0 < ticket.weight.denominator ∧
      Int.gcd ticket.weight.numerator ticket.weight.denominator = 1 ∧
      (source.source.plan.accumulator.numbers.denominator : Int) % ticket.weight.denominator = 0 := by
  obtain ⟨position,atTicket⟩ := List.mem_iff_getElem?.mp member
  obtain ⟨row,atRow,derived⟩ := collectAt computed position ticket atTicket
  have inRows := List.mem_of_getElem? atRow
  have context := originalVectorSourceParts loaded
  have sources := originalRowsSourceParts context.1
  obtain ⟨term,_,original,_,boundRow⟩ := NativePlanQCorpus.rowMember sources.2 row inRows
  have identity := readOriginalTicketIdentity derived
  have rowSource := NativePlanQCorpus.rowSource boundRow
  have memberTerm : row.term ∈ source.source.plan.coefficients := by
    rw [← (NativePlanQCorpus.completeRows sources.2).1]
    exact List.mem_map.mpr ⟨row,inRows,rfl⟩
  have checked := NativePlanCoefficients.checked sources.1.coefficients
  rw [checked.2] at memberTerm
  have termSource := NativePlanCoefficients.termSource memberTerm
  have weight := (checked.1.2.2 _ termSource.1)
  have domain := rowSource.2.2.2.2.2.2.2.1
  have ticketName := rowSource.2.2.2.1.2.symm.trans rowSource.2.2.2.2.1
  refine ⟨row,inRows,?_,?_,identity.2.2,?_,?_,?_,?_⟩
  · rw [identity.1,rowSource.1,ticketName]
  · rw [identity.2.1,rowSource.1,domain]
  · rw [identity.2.2]; exact Int.natCast_nonneg _
  · rw [identity.2.2]
    change (0 : Int) < (row.term.source.weight.denominator : Int)
    exact_mod_cast weight.1.2.1
  · rw [identity.2.2]; exact weight.1.2.2.2.1
  · rw [identity.2.2]
    change (source.source.plan.accumulator.numbers.denominator : Int) % (row.term.source.weight.denominator : Int) = 0
    exact Int.emod_eq_zero_of_dvd (by exact_mod_cast weight.2.1)

theorem originalManifestQuantumGuards
    {hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws manifest}
    (loaded : NativeManifestBinding.bind hash schemaRaw scaleRaw planRaw manifestRaw manifestId raws = some manifest) :
    ∀ q ∈ manifest.blocks.map NativeScaleBinding.Bound.quantum,
      0 < q.numerator ∧ 0 < q.denominator ∧ Int.gcd q.numerator q.denominator = 1 := by
  intro quantum member
  obtain ⟨q,inBlocks,rfl⟩ := List.mem_map.mp member
  obtain ⟨index,atBlock⟩ := List.mem_iff_getElem?.mp inBlocks
  have corpus := NativeManifestBinding.fullOrderedCorpus loaded
  have counts := NativeManifestBinding.corpusLengths corpus
  have within : index < manifest.manifest.refs.length := by
    rw [counts.1,counts.2]
    exact (List.getElem?_eq_some_iff.mp atBlock).1
  obtain ⟨raw,block,_,atLoaded,leaf,_⟩ := NativeManifestBinding.corpusAt corpus index
    manifest.manifest.refs[index] (List.getElem?_eq_getElem within)
  cases Option.some.inj (atLoaded.symm.trans atBlock)
  have valid := NativeScaleBinding.boundQuantum leaf
  change (0 : Int) < (q.segment.numerator : Int) ∧ (0 : Int) < (q.segment.denominator : Int) ∧ _
  exact ⟨by exact_mod_cast valid.1,by exact_mod_cast valid.2.2.1,valid.2.2.2.2⟩

def originalMixtureDenominator (profile : NativeApplyProfile.Profile) : Nat :=
  ApplyKernel.foldLcm 1 (profile.weights.map (·.fraction.denominator))

/- This is the existing immutable normalized-mixture requirement from
ABInputsValid, not a claim that syntactic profile decoding enforces it. -/
def OriginalProfileNormalized (profile : NativeApplyProfile.Profile) : Prop :=
  (profile.weights.map (fun w => (w.fraction.numerator : Int) *
    ((originalMixtureDenominator profile : Int)/w.fraction.denominator))).sum =
      originalMixtureDenominator profile

theorem originalFractionPublic {fraction : NativeApplyProfile.Fraction}
    (valid : NativeApplyProfile.FractionValid fraction) :
    (0 : Int) ≤ fraction.numerator ∧ (0 : Int) < fraction.denominator ∧
      Int.gcd fraction.numerator fraction.denominator = 1 :=
  ⟨Int.natCast_nonneg _,by exact_mod_cast valid.2.1,valid.2.2.2⟩

theorem originalProfileMixture {profile : NativeApplyProfile.Profile}
    (valid : NativeApplyProfile.Valid profile) :
    0 < originalMixtureDenominator profile ∧ ∀ weight ∈ profile.weights,
      NativeApplyProfile.FractionValid weight.fraction ∧
      (originalMixtureDenominator profile : Int) % (weight.fraction.denominator : Int) = 0 := by
  have positive : ∀ value ∈ profile.weights.map (·.fraction.denominator), 0 < value := by
    intro value member
    obtain ⟨weight,inWeights,rfl⟩ := List.mem_map.mp member
    exact (valid.2.2.2.2.1 weight inWeights).2.2.1
  have lcm := ApplyKernel.foldLcmSpec 1 (profile.weights.map (·.fraction.denominator)) (by decide) positive
  refine ⟨lcm.1,?_⟩
  intro weight member
  refine ⟨(valid.2.2.2.2.1 weight member).2,Int.emod_eq_zero_of_dvd ?_⟩
  exact_mod_cast lcm.2.2.1 weight.fraction.denominator (List.mem_map.mpr ⟨weight,member,rfl⟩)

theorem originalLimitContainsCurrent {bits : Nat} (width : NativeAccumulatorBinding.Width bits) :
    (0 : Int) < NativeAccumulatorBinding.limit bits ∧
    -(NativeAccumulatorBinding.limit bits : Int)-1 ≤ minInput ∧
    maxInput ≤ (NativeAccumulatorBinding.limit bits : Int) := by
  rcases width with rfl | rfl <;> decide +kernel

theorem originalImageNumericGuards
    {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source indices
      profile applyQuantum current image candidate}
    (loaded : OriginalVectorSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source)
    (computed : readOriginalImage source indices profile applyQuantum current = some image)
    (profileValid : NativeApplyProfile.Valid profile)
    (normalized : OriginalProfileNormalized profile)
    (quantum : 0 < applyQuantum.numerator ∧ 0 < applyQuantum.denominator ∧
      Int.gcd applyQuantum.numerator applyQuantum.denominator = 1)
    (domainCoverage : ∀ row ∈ source.source.rows,
      row.term.source.member.input.domain ∈ profile.weights.map (·.domain))
    (currentLoaded : NativeCurrentValues.load sha candidate = some current) :
    InputNumericGuards image := by
  simp only [readOriginalImage,bind,Option.bind_eq_some_iff] at computed
  obtain ⟨tickets,ticketsLoaded,model,modelLoaded,optimizer,optimizerLoaded,last⟩ := computed
  cases Option.some.inj last
  have context := originalVectorSourceParts loaded
  have sources := originalRowsSourceParts context.1
  have numeric := (NativePlanCoefficients.checked sources.1.coefficients).1.1
  have width : NativeAccumulatorBinding.Width source.source.plan.accumulator.numbers.accumulatorBits :=
    numeric.2.2.2.2.2.2.2.1
  have limits := originalLimitContainsCurrent width
  have mixture := originalProfileMixture profileValid
  have currentSource := NativeCurrentValues.loaded currentLoaded
  have firstMember := List.mem_of_head? context.2.1
  obtain ⟨_,_,_,_,firstLoaded⟩ := NativePlanQCorpus.rowMember sources.2 source.first firstMember
  have quantums := originalManifestQuantumGuards (rowManifestSource firstLoaded)
  have frac (f : NativeApplyProfile.Fraction) (valid : NativeApplyProfile.FractionValid f) := originalFractionPublic valid
  unfold InputNumericGuards
  refine ⟨limits.1,?_,?_,?_,mixture.1,?_,?_,?_,?_,quantum.1,quantum.2.1,quantum.2.2,
    originalCurrentKeys modelLoaded,originalCurrentKeys optimizerLoaded,?_,?_⟩
  · simp only [originalImageValue,NativeBinding.domains,NativeStateArtifacts.profileValue,List.map_map]
    rfl
  · intro ticket member
    obtain ⟨row,rowMember,_,domain,_,nonnegative,positive,reduced,divides⟩ :=
      originalTicketNumericSource loaded ticketsLoaded member
    have cells := originalTicketsPublicCells loaded ticketsLoaded ticket member
    refine ⟨?_,?_,nonnegative,positive,reduced,?_,?_⟩
    · obtain ⟨weight,memberWeight,same⟩ := List.mem_map.mp (domainCoverage row rowMember)
      apply List.mem_map.mpr
      refine ⟨⟨NativeVectorLayout.text weight.domain,source.source.plan.accumulator.numbers.denominator,
        source.first.corpus.manifest.blocks.map NativeScaleBinding.Bound.quantum⟩,?_,?_⟩
      · exact List.mem_map.mpr ⟨weight,memberWeight,rfl⟩
      · exact (congrArg NativeVectorLayout.text same).trans domain.symm
    · simpa only [originalImageValue,originalShardNames,List.length_map] using cells.1
    · intro value memberValue
      have range := abs_le.mp (cells.2 value memberValue)
      have large : (32767 : Int) ≤ NativeAccumulatorBinding.limit source.source.plan.accumulator.numbers.accumulatorBits := by
        exact (show (32767 : Int) ≤ maxInput by decide).trans limits.2.2
      change -(NativeAccumulatorBinding.limit source.source.plan.accumulator.numbers.accumulatorBits : Int)-1 ≤ value ∧
        value ≤ (NativeAccumulatorBinding.limit source.source.plan.accumulator.numbers.accumulatorBits : Int)
      constructor <;> omega
    · intro domainValue memberDomain _
      obtain ⟨weight,_,rfl⟩ := List.mem_map.mp memberDomain
      exact divides
  · intro domain member
    obtain ⟨weight,_,rfl⟩ := List.mem_map.mp member
    refine ⟨?_,?_,quantums⟩
    · change (0 : Int) < (source.source.plan.accumulator.numbers.denominator : Int)
      exact_mod_cast numeric.2.2.2.2.1
    · simp only [originalImageValue,originalShardNames,List.length_map]
  · simp only [originalImageValue,NativeStateArtifacts.profileValue,List.map_map,NativeApplyResult.fraction]
    rfl
  · intro domain member
    obtain ⟨weight,inWeights,rfl⟩ := List.mem_map.mp member
    have valid := frac _ (mixture.2 weight inWeights).1
    exact ⟨valid.1,valid.2.1,valid.2.2,(mixture.2 weight inWeights).2⟩
  · simpa only [OriginalProfileNormalized,originalMixtureDenominator,originalImageValue,
      NativeStateArtifacts.profileValue,List.map_map,Function.comp_def,NativeApplyResult.fraction] using normalized
  · intro ratio member
    simp only [originalImageValue,NativeStateArtifacts.profileValue,List.mem_cons,List.not_mem_nil,or_false] at member
    rcases member with rfl | rfl | rfl
    · exact frac _ profileValid.2.2.2.2.2.1
    · exact frac _ profileValid.2.2.2.2.2.2.1
    · exact frac _ profileValid.2.2.2.2.2.2.2.1
  · intro cell member
    have range := (NativeCurrentValues.valuesSource currentSource.model).2 cell.2 (originalCurrentCellSource modelLoaded member)
    exact ⟨limits.2.1.trans range.1,range.2.trans limits.2.2⟩
  · intro cell member
    have range := (NativeCurrentValues.valuesSource currentSource.optimizer).2 cell.2 (originalCurrentCellSource optimizerLoaded member)
    exact ⟨limits.2.1.trans range.1,range.2.trans limits.2.2⟩


/- Native labels are carried bijectively before the separately checked public
alias lookup. Quotes, backslashes and long labels do not require draft grammar. -/
theorem byteCharacterRoundtrip (b : UInt8) : UInt8.ofNat (Char.ofNat b.toNat).toNat = b := by
  have small := b.toNat_lt
  have valid : b.toNat.isValidChar := by simp only [Nat.isValidChar]; omega
  simp only [Char.ofNat,dif_pos valid,Char.ofNatAux,Char.toNat,UInt32.toNat,
    BitVec.toNat_ofNatLT,UInt8.ofNat_toNat]

theorem originalLabelRoundtrip (bytes : Bytes) : asciiBytes (NativeVectorLayout.text bytes) = bytes := by
  simp only [asciiBytes,NativeVectorLayout.text,String.toList_ofList,List.map_map,Function.comp_def,
    byteCharacterRoundtrip]
  exact List.map_id bytes

theorem originalLabelInjective {a b : Bytes} (same : NativeVectorLayout.text a = NativeVectorLayout.text b) : a = b := by
  simpa only [originalLabelRoundtrip] using congrArg asciiBytes same

theorem collectFilter {α β} {f : α → Option β} {xs : List α} {ys : List β}
    (computed : collect f xs = some ys) (p : α → Bool) (q : β → Bool)
    (same : ∀ x ∈ xs, ∀ y, f x = some y → p x = q y) :
    collect f (xs.filter p) = some (ys.filter q) := by
  induction xs generalizing ys with
  | nil => cases Option.some.inj computed; rfl
  | cons x xs ih =>
    simp only [collect,bind,Option.bind_eq_some_iff] at computed
    obtain ⟨y,hy,rest,hr,last⟩ := computed
    cases Option.some.inj last
    have head := same x List.mem_cons_self y hy
    have tail := ih hr (fun a ha b hb => same a (List.mem_cons_of_mem _ ha) b hb)
    simp only [List.filter_cons,head]
    cases q y <;> simp only [Bool.false_eq_true,↓reduceIte,collect,hy,tail,bind,Option.bind]

theorem collectCompose {α β γ} {f : α → Option β} {g : β → Option γ} {xs : List α} {ys : List β}
    (computed : collect f xs = some ys) :
    collect g ys = collect (fun x => (f x).bind g) xs := by
  induction xs generalizing ys with
  | nil => cases Option.some.inj computed; rfl
  | cons x xs ih =>
    simp only [collect,bind,Option.bind_eq_some_iff] at computed
    obtain ⟨y,hy,rest,hr,last⟩ := computed
    cases Option.some.inj last
    simp only [collect,hy,bind,Option.bind_some]
    rw [ih hr]

theorem selectedManifestCoordinate {manifest indices cells block coordinate}
    (selected : selectOriginalManifest manifest indices = some cells)
    (atIndex : indices[block]? = some coordinate) :
    cells[block]? = NativeAvailableQ.coordinate manifest block coordinate := by
  have shape : indices.length = manifest.blocks.length := by
    unfold selectOriginalManifest at selected
    split at selected <;> try contradiction
    assumption
  have inCells : block < cells.length := by
    rw [(selectedManifestCellsSource selected).1,← shape]
    exact (List.getElem?_eq_some_iff.mp atIndex).1
  obtain ⟨q,k,atBlock,atK,atValue⟩ := (selectedManifestCellsSource selected).2 block cells[block]
    (List.getElem?_eq_getElem inCells)
  have same := Option.some.inj (atK.symm.trans atIndex)
  subst k
  simp only [NativeAvailableQ.coordinate,atBlock,bind,Option.bind,atValue,List.getElem?_eq_getElem inCells]

theorem readOriginalRowCoordinate {row indices ticket block coordinate}
    (loaded : readOriginalRowTicket row indices = some ticket) (atIndex : indices[block]? = some coordinate) :
    readImageRow block ticket = (NativeAvailableQ.coordinate row.corpus.manifest block coordinate).map
      (fun value => (⟨row.term.source.weight.numerator,row.term.source.weight.denominator,[value]⟩ : ParameterKernel.Row)) := by
  simp only [readImageRow,selectedManifestCoordinate (readOriginalTicketCells loaded) atIndex,
    (readOriginalTicketIdentity loaded).2.2]

theorem readOriginalRowDomain
    {sha configRaw proofRaw profileRaw plan permission term original row indices ticket}
    (rowSource : NativePlanQCorpus.loadRow sha configRaw proofRaw profileRaw plan permission term original = some row)
    (selected : readOriginalRowTicket row indices = some ticket) :
    ticket.domain = NativeVectorLayout.text row.term.source.member.input.domain := by
  have bound := NativePlanQCorpus.rowSource rowSource
  exact (readOriginalTicketIdentity selected).2.1.trans
    (congrArg NativeVectorLayout.text (by simpa only [bound.1] using bound.2.2.2.2.2.2.2.1))

def originalScalarRows (source : NativePlanQCorpus.Bound) (domain : Bytes) (block coordinate : Nat) :
    Option (List ParameterKernel.Row) :=
  collect (fun row => (NativeAvailableQ.coordinate row.corpus.manifest block coordinate).map
    (fun value => ⟨row.term.source.weight.numerator,row.term.source.weight.denominator,[value]⟩))
    (NativePlanQCorpus.inDomain domain source.rows)

theorem originalTicketsDomainSelection
    {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source indices tickets}
    (loaded : OriginalVectorSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source)
    (computed : readOriginalTickets source indices = some tickets) (domain : Bytes) :
    collect (fun row => readOriginalRowTicket row indices) (NativePlanQCorpus.inDomain domain source.source.rows) =
      some (tickets.filter (fun ticket => ticket.domain == NativeVectorLayout.text domain)) := by
  apply collectFilter computed
  intro row member ticket selected
  have rows := (originalRowsSourceParts (originalVectorSourceParts loaded).1).2
  obtain ⟨_,_,_,_,rowSource⟩ := NativePlanQCorpus.rowMember rows row member
  rw [readOriginalRowDomain rowSource selected]
  apply Bool.eq_iff_iff.mpr
  simp only [beq_iff_eq]
  exact ⟨fun equal => congrArg NativeVectorLayout.text equal,originalLabelInjective⟩

theorem collectOnEqual {α β} {f g : α → Option β} (xs : List α)
    (same : ∀ x ∈ xs, f x = g x) : collect f xs = collect g xs := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
    simp only [collect,same x List.mem_cons_self,
      ih (fun a ha => same a (List.mem_cons_of_mem _ ha))]

theorem originalInputRowsAreSourceRows
    {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source indices
      profile quantum current image block coordinate}
    (loaded : OriginalVectorSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source)
    (computed : readOriginalImage source indices profile quantum current = some image)
    (domain : Bytes) (atIndex : indices[block]? = some coordinate) :
    imageRows image (NativeVectorLayout.text domain) block = originalScalarRows source.source domain block coordinate := by
  simp only [readOriginalImage,bind,Option.bind_eq_some_iff] at computed
  obtain ⟨tickets,ticketSource,model,_,optimizer,_,last⟩ := computed
  cases Option.some.inj last
  have selected := originalTicketsDomainSelection loaded ticketSource domain
  have composed := collectCompose (g := readImageRow block) selected
  change collect (readImageRow block) (tickets.filter (fun ticket => ticket.domain == NativeVectorLayout.text domain)) = _
  rw [composed]
  unfold originalScalarRows
  apply collectOnEqual
  intro row member
  obtain ⟨position,atRow⟩ := List.mem_iff_getElem?.mp (List.mem_of_mem_filter member)
  have inTickets : position < tickets.length := by
    rw [collectLength ticketSource]
    exact (List.getElem?_eq_some_iff.mp atRow).1
  obtain ⟨original,atOriginal,derived⟩ := collectAt ticketSource position tickets[position]
    (List.getElem?_eq_getElem inTickets)
  have same := Option.some.inj (atOriginal.symm.trans atRow)
  subst original
  simp only [derived,Option.bind_some]
  exact readOriginalRowCoordinate derived atIndex

/- The numerical configuration is selected from the same original policy, not
accepted as an unrelated public profile. UnitSource is the pre-existing named
primitive boundary; its full context/APC/profile/accumulator/current key is kept.
This reads already checked current values and adds no recovery transition. -/
def OriginalNumericConfigurationChecks (source : NativeVectorContext.Bound)
    (profile : NativeApplyProfile.Checked) (current : NativeCurrentHistory.Current)
    (quantum : Rational) : Prop :=
  NativeStateProjection.Links source profile current ∧
  OriginalProfileNormalized profile.profile ∧
  (0 < quantum.numerator ∧ 0 < quantum.denominator ∧ Int.gcd quantum.numerator quantum.denominator = 1) ∧
  (∀ row ∈ source.source.rows, row.term.source.member.input.domain ∈ profile.profile.weights.map (·.domain)) ∧
  current.last.values.model.length = source.first.corpus.manifest.plan.inputs.schema.total ∧
  current.last.values.optimizer.length = current.last.values.model.length

instance (source profile current quantum) : Decidable (OriginalNumericConfigurationChecks source profile current quantum) := by
  unfold OriginalNumericConfigurationChecks OriginalProfileNormalized
  infer_instance

structure OriginalNumericConfiguration (sha : Bytes → Bytes) (source : NativeVectorContext.Bound)
    (units : NativeStateProjection.UnitSource) (profileId : Bytes) (current : NativeCurrentHistory.Current) where
  profile : NativeApplyProfile.Checked
  profileSource : NativeStateProjection.selectProfile sha source profileId = some profile
  quantum : Rational
  unitSource : units (NativeStateProjection.unitKey source profile current) = some quantum
  currentSource : NativeCurrentValues.load sha current.last.edge.decoded.candidate = some current.last.values
  checked : OriginalNumericConfigurationChecks source profile current quantum

def loadOriginalNumericConfiguration (sha : Bytes → Bytes) (source : NativeVectorContext.Bound)
    (units : NativeStateProjection.UnitSource) (profileId : Bytes) (current : NativeCurrentHistory.Current) :
    Option (OriginalNumericConfiguration sha source units profileId current) := do
  match profileSource : NativeStateProjection.selectProfile sha source profileId with
  | none => none
  | some profile =>
    match unitSource : units (NativeStateProjection.unitKey source profile current) with
    | none => none
    | some quantum =>
      if currentSource : NativeCurrentValues.load sha current.last.edge.decoded.candidate = some current.last.values then
        if checked : OriginalNumericConfigurationChecks source profile current quantum then
          some ⟨profile,profileSource,quantum,unitSource,currentSource,checked⟩ else none
      else none

theorem originalNumericConfigurationLoaded {sha source units profileId current}
    (c : OriginalNumericConfiguration sha source units profileId current) :
    loadOriginalNumericConfiguration sha source units profileId current = some c := by
  unfold loadOriginalNumericConfiguration
  split
  · rename_i absent; simp [c.profileSource] at absent
  · rename_i profile found
    have same := Option.some.inj (found.symm.trans c.profileSource)
    subst profile
    split
    · rename_i absent; simp [c.unitSource] at absent
    · rename_i quantum found
      have same := Option.some.inj (found.symm.trans c.unitSource)
      subst quantum
      rw [dif_pos c.currentSource,dif_pos c.checked]

theorem originalNumericConfigurationProfile {sha source units profileId current}
    (c : OriginalNumericConfiguration sha source units profileId current) :
    NativeApplyProfile.check sha c.profile.source = some c.profile ∧
      c.profile.id = profileId ∧ c.profile.profile.accumulator = source.source.plan.members.edge.certificate.common.accumulator ∧
      OriginalProfileNormalized c.profile.profile := by
  obtain ⟨_,_,_,_,_,id,checked⟩ := NativeStateProjection.selectedSource c.profileSource
  exact ⟨checked,id,c.checked.1.1,c.checked.2.1⟩

theorem originalConfiguredInputTotal {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source
    units profileId current indices}
    (bound : OriginalVectorSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source)
    (configuration : OriginalNumericConfiguration sha source units profileId current)
    (selection : OriginalSelectionFits source.first.corpus.manifest indices) :
    ∃ image, readOriginalImage source indices configuration.profile.profile configuration.quantum current.last.values = some image ∧
      InputNumericGuards image := by
  obtain ⟨image,computed⟩ := originalImageConstructorTotal bound selection configuration.profile.profile
    configuration.quantum current.last.values configuration.checked.2.2.2.2
  have profile := originalNumericConfigurationProfile configuration
  refine ⟨image,computed,originalImageNumericGuards bound computed
    (NativeApplyProfile.checkedSource profile.1).2.2.1 configuration.checked.2.1
    configuration.checked.2.2.1 configuration.checked.2.2.2.1 configuration.currentSource⟩

theorem originalConfiguredInputGuards {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source
    units profileId current indices image}
    (bound : OriginalVectorSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source)
    (configuration : OriginalNumericConfiguration sha source units profileId current)
    (computed : readOriginalImage source indices configuration.profile.profile configuration.quantum current.last.values = some image) :
    InputNumericGuards image :=
  originalImageNumericGuards bound computed
    (NativeApplyProfile.checkedSource (originalNumericConfigurationProfile configuration).1).2.2.1
    configuration.checked.2.1 configuration.checked.2.2.1 configuration.checked.2.2.2.1 configuration.currentSource

end DeltaReduce.FamilyInputs
