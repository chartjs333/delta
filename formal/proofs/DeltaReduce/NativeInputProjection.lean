import DeltaReduce.NativeScalarProjection

/-! Source-derived scalar arithmetic inputs, before result computation.
Loading does not require a later aggregate or successful PARAMETER/APPLY result.
Representability restrictions belong to the scalar model, not native admission. -/
namespace DeltaReduce.NativeInputProjection
open NativeBinding

structure Cell where
  contribution : Contribution
  value : Int
  deriving DecidableEq, Repr

inductive ScalarRows : List Contribution → List ParameterKernel.Row → List Cell → Prop where
  | nil : ScalarRows [] [] []
  | cons {c cs r rs value cells}
      (shape : r.values = [value])
      (weight : r.numerator = c.weight.numerator ∧ r.denominator = c.weight.denominator)
      (tail : ScalarRows cs rs cells) : ScalarRows (c :: cs) (r :: rs) (⟨c,value⟩ :: cells)

def scalarRows : (contributions : List Contribution) → (rows : List ParameterKernel.Row) →
    Option {cells : List Cell // ScalarRows contributions rows cells}
  | [], [] => some ⟨[], .nil⟩
  | c :: cs, r :: rs =>
      match shape : r.values with
      | [value] => do
          if weight : r.numerator = c.weight.numerator ∧ r.denominator = c.weight.denominator then
            let tail ← scalarRows cs rs
            some ⟨⟨c,value⟩ :: tail.val, .cons shape weight tail.property⟩
          else none
      | _ => none
  | _, _ => none

theorem scalarRowsContributions {contributions rows cells} (h : ScalarRows contributions rows cells) :
    cells.map Cell.contribution = contributions ∧ cells.length = rows.length := by
  induction h with
  | nil => exact ⟨rfl,rfl⟩
  | cons shape weight tail ih => simp [ih.1,ih.2]

theorem scalarRowAt {contributions rows cells} (h : ScalarRows contributions rows cells)
    (index : Nat) (cell : Cell) (atCell : cells[index]? = some cell) :
    ∃ row, rows[index]? = some row ∧ contributions[index]? = some cell.contribution ∧
      row.values = [cell.value] ∧ row.numerator = cell.contribution.weight.numerator ∧
      row.denominator = cell.contribution.weight.denominator := by
  induction h generalizing index cell with
  | nil => simp at atCell
  | cons shape weight tail ih =>
      cases index with
      | zero => simp only [List.getElem?_cons_zero] at atCell; cases atCell
                exact ⟨_,rfl,rfl,shape,weight⟩
      | succ index => exact ih index cell atCell

structure Block (codec : Codec) (store : Store) (authority : Authority) (frame : ParameterFrame)
    (assignment : Assignment) where
  ordered : assignment.contributions.map (·.ticket) = eligibleDomainTickets frame assignment.domain
  rows : List ParameterKernel.Row
  bound : RowsBound codec store authority.schema frame assignment 1 assignment.contributions rows
  cells : List Cell
  scalar : ScalarRows assignment.contributions rows cells
  fractions : ∀ c ∈ cells,
    ParameterKernel.ReducedNonnegative minInput maxInput c.contribution.weight.numerator c.contribution.weight.denominator ∧
    assignment.denominator % c.contribution.weight.denominator = 0 ∧ Fits minInput maxInput c.value

def loadBlock (codec : Codec) (store : Store) (authority : Authority) (frame : ParameterFrame)
    (assignment : Assignment) : Option (Block codec store authority frame assignment) := do
  if ordered : assignment.contributions.map (·.ticket) = eligibleDomainTickets frame assignment.domain then
    let rows ← loadRows codec store authority.schema frame assignment 1 assignment.contributions
    let cells ← scalarRows assignment.contributions rows.val
    if fractions : ∀ c ∈ cells.val,
        ParameterKernel.ReducedNonnegative minInput maxInput c.contribution.weight.numerator c.contribution.weight.denominator ∧
        assignment.denominator % c.contribution.weight.denominator = 0 ∧ Fits minInput maxInput c.value then
      some ⟨ordered,rows.val,rows.property,cells.val,cells.property,fractions⟩
    else none
  else none

theorem blockExactEligibleOrder {codec store authority frame assignment}
    (block : Block codec store authority frame assignment) :
    block.cells.map (fun c => c.contribution.ticket) = eligibleDomainTickets frame assignment.domain := by
  have h := congrArg (List.map Contribution.ticket) (scalarRowsContributions block.scalar).1
  simpa only [List.map_map,Function.comp_def] using h.trans block.ordered

theorem blockCellFromCommittedBytes {codec store authority frame assignment}
    (block : Block codec store authority frame assignment) (index : Nat) (cell : Cell)
    (atCell : block.cells[index]? = some cell) :
    ∃ loaded : LoadedRow codec store authority.schema frame assignment 1 cell.contribution,
      loaded.q.values = [cell.value] ∧ loaded.q.quantum = assignment.quantum ∧
      committedQ frame cell.contribution.ticket assignment.shard = some cell.contribution.q := by
  obtain ⟨row, atRow, atContribution, shape, _⟩ := scalarRowAt block.scalar index cell atCell
  obtain ⟨c, hc, loaded, same⟩ := rowsBoundAt block.bound index row atRow
  have eq : c = cell.contribution := Option.some.inj (hc.symm.trans atContribution)
  subst c
  exact ⟨loaded,by simpa only [same, LoadedRow.row] using shape,loaded.quantum,loaded.committed⟩

structure BlockEntry (codec : Codec) (store : Store) (authority : Authority) (frame : ParameterFrame) where
  assignment : Assignment
  data : Block codec store authority frame assignment

inductive BlocksFor (codec : Codec) (store : Store) (authority : Authority) (frame : ParameterFrame) :
    List Assignment → List (BlockEntry codec store authority frame) → Prop where
  | nil : BlocksFor codec store authority frame [] []
  | cons (entry : BlockEntry codec store authority frame) {assignments entries}
      (tail : BlocksFor codec store authority frame assignments entries) :
      BlocksFor codec store authority frame (entry.assignment :: assignments) (entry :: entries)

def loadBlocks (codec : Codec) (store : Store) (authority : Authority) (frame : ParameterFrame) :
    (assignments : List Assignment) → Option {entries : List (BlockEntry codec store authority frame) //
      BlocksFor codec store authority frame assignments entries}
  | [] => some ⟨[],.nil⟩
  | assignment :: rest => do
      let block ← loadBlock codec store authority frame assignment
      let tail ← loadBlocks codec store authority frame rest
      let entry := BlockEntry.mk assignment block
      some ⟨entry :: tail.val,.cons entry tail.property⟩

theorem blocksForAssignments {codec store authority frame assignments entries}
    (h : BlocksFor codec store authority frame assignments entries) :
    entries.map BlockEntry.assignment = assignments := by
  induction h with
  | nil => rfl
  | cons entry tail ih => simp [ih]

structure Corpus {codec store trust anchor} (binding : Binding codec trust anchor store) where
  frame : ParameterFrame
  origin : FrameOrigin codec store binding.authority frame
  valid : ParameterFrameValid binding.authority binding.profile binding.model binding.optimizer frame
  layout : NativeScalarProjection.Layout
  layoutLoaded : NativeScalarProjection.layout frame = some layout
  blocks : List (BlockEntry codec store binding.authority frame)
  bound : BlocksFor codec store binding.authority frame frame.plan.assignments blocks

def loadCorpus {codec store trust anchor} (binding : Binding codec trust anchor store) : Option (Corpus binding) := do
  let source ← loadParameterFrame codec store binding.authority
  if valid : ParameterFrameValid binding.authority binding.profile binding.model binding.optimizer source.val then
    match hl : NativeScalarProjection.layout source.val with
    | none => none
    | some layout =>
        let blocks ← loadBlocks codec store binding.authority source.val source.val.plan.assignments
        some ⟨source.val,source.property,valid,layout,hl,blocks.val,blocks.property⟩
  else none

theorem corpusRetainsAllAssignments {codec store trust anchor binding}
    (c : Corpus (codec := codec) (store := store) (trust := trust) (anchor := anchor) binding) :
    c.blocks.map BlockEntry.assignment = c.frame.plan.assignments := blocksForAssignments c.bound

structure AssignmentInput where
  domain : String
  shard : String
  denominator : Int
  quantum : Rational
  cells : List Cell
  deriving DecidableEq, Repr

def BlockEntry.input {codec store authority frame} (entry : BlockEntry codec store authority frame) : AssignmentInput :=
  ⟨entry.assignment.domain,entry.assignment.shard,entry.assignment.denominator,entry.assignment.quantum,entry.data.cells⟩

def Corpus.inputs {codec store trust anchor binding}
    (c : Corpus (codec := codec) (store := store) (trust := trust) (anchor := anchor) binding) : List AssignmentInput :=
  c.blocks.map BlockEntry.input

theorem inputOrigin {codec store trust anchor binding}
    (c : Corpus (codec := codec) (store := store) (trust := trust) (anchor := anchor) binding)
    {input} (member : input ∈ c.inputs) :
    ∃ entry ∈ c.blocks, input = entry.input ∧ entry.assignment ∈ c.frame.plan.assignments := by
  obtain ⟨entry,he,hi⟩ := List.mem_map.mp member
  refine ⟨entry,he,hi.symm,?_⟩
  rw [← corpusRetainsAllAssignments c]
  exact List.mem_map.mpr ⟨entry,he,rfl⟩

/- These small selection functions never invent defaults or resolve conflicts
by first arrival. A uniform value is returned only after checking every copy. -/
def only {α : Type} (values : List α) : Option α := match values with
  | [value] => some value
  | _ => none

theorem onlyExact {α : Type} {values : List α} {value} (h : only values = some value) : values = [value] := by
  cases values with
  | nil => simp [only] at h
  | cons head tail => cases tail with
    | nil => cases h; rfl
    | cons a as => simp [only] at h

def uniform {α : Type} [DecidableEq α] (values : List α) : Option α := match values with
  | [] => none
  | value :: rest => if ∀ x ∈ rest, x = value then some value else none

theorem uniformSound {α : Type} [DecidableEq α] {values : List α} {value}
    (h : uniform values = some value) : values ≠ [] ∧ ∀ x ∈ values, x = value := by
  cases values with
  | nil => simp [uniform] at h
  | cons head tail =>
      simp only [uniform] at h
      split at h
      · rename_i same; cases h
        exact ⟨by simp,by intro x hx; rcases List.mem_cons.mp hx with h | h; exact h; exact same x h⟩
      · contradiction

def ticketCells (inputs : List AssignmentInput) (ticket : String) : List Cell :=
  inputs.flatMap (fun a => a.cells.filter (fun c => c.contribution.ticket == ticket))

def ticketWeight (inputs : List AssignmentInput) (ticket : String) : Option Rational :=
  uniform ((ticketCells inputs ticket).map (fun c => c.contribution.weight))

theorem ticketWeightAgreesWithEveryShard {inputs ticket weight} (h : ticketWeight inputs ticket = some weight)
    {cell} (member : cell ∈ ticketCells inputs ticket) : cell.contribution.weight = weight :=
  (uniformSound h).2 _ (List.mem_map.mpr ⟨cell,member,rfl⟩)

def domainDenominator (inputs : List AssignmentInput) (domain : String) : Option Int :=
  uniform ((inputs.filter (fun a => a.domain == domain)).map (·.denominator))

theorem domainDenominatorAgreesWithEveryShard {inputs domain denominator}
    (h : domainDenominator inputs domain = some denominator) {a}
    (member : a ∈ inputs) (same : a.domain = domain) : a.denominator = denominator :=
  (uniformSound h).2 _ (List.mem_map.mpr ⟨a,List.mem_filter.mpr ⟨member,by simp [same]⟩,rfl⟩)

def assignmentAt (inputs : List AssignmentInput) (domain shard : String) : Option AssignmentInput :=
  only (inputs.filter (fun a => a.domain == domain && a.shard == shard))

def qAt (inputs : List AssignmentInput) (ticket domain shard : String) : Option Int := do
  let assignment ← assignmentAt inputs domain shard
  let cell ← only (assignment.cells.filter (fun c => c.contribution.ticket == ticket))
  some cell.value

theorem qAtHasExactSource {inputs ticket domain shard value} (h : qAt inputs ticket domain shard = some value) :
    ∃ a ∈ inputs, a.domain = domain ∧ a.shard = shard ∧
      ∃ cell ∈ a.cells, cell.contribution.ticket = ticket ∧ cell.value = value := by
  unfold qAt at h
  cases ha : assignmentAt inputs domain shard with
  | none => simp [ha] at h
  | some a =>
      have ae := onlyExact ha
      have am := List.mem_filter.mp (by rw [ae]; exact List.mem_cons_self : a ∈ inputs.filter (fun a => a.domain == domain && a.shard == shard))
      cases hc : only (a.cells.filter (fun c => c.contribution.ticket == ticket)) with
      | none => simp [ha,hc] at h
      | some cell =>
          have ce := onlyExact hc
          have cm := List.mem_filter.mp (by rw [ce]; exact List.mem_cons_self : cell ∈ a.cells.filter (fun c => c.contribution.ticket == ticket))
          simp only [ha,hc,Bind.bind,Option.bind,Option.some.injEq] at h
          have ak : a.domain = domain ∧ a.shard = shard := by simpa using am.2
          exact ⟨a,am.1,ak.1,ak.2,cell,cm.1,beq_iff_eq.mp cm.2,h⟩

def collect {α β : Type} (f : α → Option β) : List α → Option (List β)
  | [] => some []
  | x :: xs => do
      let head ← f x
      let tail ← collect f xs
      some (head :: tail)

theorem collectAt {α β : Type} {f : α → Option β} {xs ys} (h : collect f xs = some ys)
    (i : Nat) (y : β) (found : ys[i]? = some y) :
    ∃ x, xs[i]? = some x ∧ f x = some y := by
  induction xs generalizing ys i with
  | nil => simp [collect] at h; subst ys; simp at found
  | cons x xs ih =>
      cases hx : f x with
      | none => simp [collect,hx] at h
      | some head =>
          cases ht : collect f xs with
          | none => simp [collect,hx,ht] at h
          | some tail =>
              simp only [collect,hx,ht,Bind.bind,Option.bind,Option.some.injEq] at h
              subst ys
              cases i with
              | zero => simp only [List.getElem?_cons_zero,Option.some.injEq] at found
                        subst y; exact ⟨x,rfl,hx⟩
              | succ i => exact ih ht i found

theorem collectLength {α β : Type} {f : α → Option β} {xs ys} (h : collect f xs = some ys) :
    ys.length = xs.length := by
  induction xs generalizing ys with
  | nil => simp [collect] at h; subst ys; rfl
  | cons x xs ih =>
      cases hx : f x with
      | none => simp [collect,hx] at h
      | some head =>
          cases ht : collect f xs with
          | none => simp [collect,hx,ht] at h
          | some tail =>
              simp only [collect,hx,ht,Bind.bind,Option.bind,Option.some.injEq] at h
              subst ys; simp [ih ht]

structure TicketData where
  ticket : String
  domain : String
  weight : Rational
  q : List Int
  deriving DecidableEq, Repr

def deriveTicket (inputs : List AssignmentInput) (shards : List String) (ticket : Ticket) : Option TicketData := do
  let weight ← ticketWeight inputs ticket.id
  let q ← collect (qAt inputs ticket.id ticket.domain) shards
  some ⟨ticket.id,ticket.domain,weight,q⟩

theorem derivedTicketSource {inputs shards ticket row} (h : deriveTicket inputs shards ticket = some row) :
    row.ticket = ticket.id ∧ row.domain = ticket.domain ∧
    ticketWeight inputs ticket.id = some row.weight ∧
    collect (qAt inputs ticket.id ticket.domain) shards = some row.q := by
  unfold deriveTicket at h
  cases hw : ticketWeight inputs ticket.id with
  | none => simp [hw] at h
  | some weight =>
      cases hq : collect (qAt inputs ticket.id ticket.domain) shards with
      | none => simp [hw,hq] at h
      | some q => simp only [hw,hq,Bind.bind,Option.bind,Option.some.injEq] at h
                  subst row; exact ⟨rfl,rfl,rfl,rfl⟩

structure DomainData where
  domain : String
  denominator : Int
  quantum : List Rational
  deriving DecidableEq, Repr

def quantumAt (inputs : List AssignmentInput) (domain shard : String) : Option Rational :=
  (assignmentAt inputs domain shard).map (·.quantum)

def deriveDomain (inputs : List AssignmentInput) (shards : List String) (domain : String) : Option DomainData := do
  let denominator ← domainDenominator inputs domain
  let quantum ← collect (quantumAt inputs domain) shards
  some ⟨domain,denominator,quantum⟩

theorem quantumAtHasExactSource {inputs domain shard quantum}
    (h : quantumAt inputs domain shard = some quantum) :
    ∃ a ∈ inputs, a.domain = domain ∧ a.shard = shard ∧ a.quantum = quantum := by
  unfold quantumAt at h
  cases ha : assignmentAt inputs domain shard with
  | none => simp [ha] at h
  | some a =>
      have ae := onlyExact ha
      have am := List.mem_filter.mp (by rw [ae]; exact List.mem_cons_self : a ∈ inputs.filter (fun a => a.domain == domain && a.shard == shard))
      have ak : a.domain = domain ∧ a.shard = shard := by simpa using am.2
      simp only [ha,Option.map_some,Option.some.injEq] at h
      exact ⟨a,am.1,ak.1,ak.2,h⟩

theorem derivedDomainSource {inputs shards domain row} (h : deriveDomain inputs shards domain = some row) :
    row.domain = domain ∧ domainDenominator inputs domain = some row.denominator ∧
    collect (quantumAt inputs domain) shards = some row.quantum := by
  unfold deriveDomain at h
  cases hd : domainDenominator inputs domain with
  | none => simp [hd] at h
  | some denominator =>
      cases hq : collect (quantumAt inputs domain) shards with
      | none => simp [hd,hq] at h
      | some q => simp only [hd,hq,Bind.bind,Option.bind,Option.some.injEq] at h
                  subst row; exact ⟨rfl,rfl,rfl⟩

structure ModelLimit where
  value : Int
  positive : 0 < value
  bounded : value ≤ maxInput

def modelLimit (value : Int) : Option ModelLimit :=
  if h : 0 < value ∧ value ≤ maxInput then some ⟨value,h.1,h.2⟩ else none

/- The same bounded TLA input range applies to its Q/current cells. This is a
finite-model restriction; it does not equate its action guards with native widths. -/
structure Projected {codec store trust anchor} {binding : Binding codec trust anchor store}
    (corpus : Corpus binding) (limit : ModelLimit) where
  tickets : List TicketData
  ticketsLoaded : collect (deriveTicket corpus.inputs (shardIds corpus.frame)) corpus.frame.plan.tickets = some tickets
  domains : List DomainData
  domainsLoaded : collect (deriveDomain corpus.inputs (shardIds corpus.frame)) (NativeBinding.domains binding.profile) = some domains
  weights : ApplyKernel.WeightPlan minInput maxInput (binding.profile.domainWeights.map (fun d => d.weight.kernelWeight))
  model : NativeScalarProjection.Projected corpus.layout binding.model.values
  optimizer : NativeScalarProjection.Projected corpus.layout binding.optimizer.values
  ranges : ∀ v ∈ tickets.flatMap (·.q) ++ binding.model.values ++ binding.optimizer.values,
    Fits (-limit.value - 1) limit.value v

def projectInputs {codec store trust anchor} {binding : Binding codec trust anchor store}
    (corpus : Corpus binding) (limit : ModelLimit) : Option (Projected corpus limit) := do
  match ht : collect (deriveTicket corpus.inputs (shardIds corpus.frame)) corpus.frame.plan.tickets,
      hd : collect (deriveDomain corpus.inputs (shardIds corpus.frame)) (NativeBinding.domains binding.profile) with
  | some tickets, some domains =>
      let weights ← ApplyKernel.deriveWeightPlan minInput maxInput (binding.profile.domainWeights.map (fun d => d.weight.kernelWeight))
      let model ← NativeScalarProjection.project corpus.layout binding.model.values
      let optimizer ← NativeScalarProjection.project corpus.layout binding.optimizer.values
      if ranges : ∀ v ∈ tickets.flatMap (·.q) ++ binding.model.values ++ binding.optimizer.values,
          Fits (-limit.value - 1) limit.value v then
        some ⟨tickets,ht,domains,hd,weights,model,optimizer,ranges⟩
      else none
  | _, _ => none

theorem projectedTicketCount {codec store trust anchor binding corpus limit}
    (p : Projected (codec := codec) (store := store) (trust := trust) (anchor := anchor) (binding := binding) corpus limit) :
    p.tickets.length = corpus.frame.plan.tickets.length := collectLength p.ticketsLoaded

theorem projectedQFromNativeInput {codec store trust anchor binding corpus limit}
    (p : Projected (codec := codec) (store := store) (trust := trust) (anchor := anchor) (binding := binding) corpus limit)
    (ti si : Nat) (row : TicketData) (value : Int)
    (atTicket : p.tickets[ti]? = some row) (atQ : row.q[si]? = some value) :
    ∃ ticket, corpus.frame.plan.tickets[ti]? = some ticket ∧
      ∃ shard, (shardIds corpus.frame)[si]? = some shard ∧
        ∃ a ∈ corpus.inputs, a.domain = ticket.domain ∧ a.shard = shard ∧
          ∃ cell ∈ a.cells, cell.contribution.ticket = ticket.id ∧ cell.value = value := by
  obtain ⟨ticket,ht,derived⟩ := collectAt p.ticketsLoaded ti row atTicket
  obtain ⟨shard,hs,hq⟩ := collectAt (derivedTicketSource derived).2.2.2 si value atQ
  exact ⟨ticket,ht,shard,hs,qAtHasExactSource hq⟩

theorem projectedDomainCount {codec store trust anchor binding corpus limit}
    (p : Projected (codec := codec) (store := store) (trust := trust) (anchor := anchor) (binding := binding) corpus limit) :
    p.domains.length = (NativeBinding.domains binding.profile).length := collectLength p.domainsLoaded

theorem projectedQHasCanonicalArtifact {codec store trust anchor binding corpus limit}
    (p : Projected (codec := codec) (store := store) (trust := trust) (anchor := anchor) (binding := binding) corpus limit)
    (ti si : Nat) (row : TicketData) (value : Int)
    (atTicket : p.tickets[ti]? = some row) (atQ : row.q[si]? = some value) :
    ∃ entry ∈ corpus.blocks, ∃ cell ∈ entry.data.cells,
      ∃ loaded : LoadedRow codec store binding.authority.schema corpus.frame entry.assignment 1 cell.contribution,
        loaded.q.values = [value] ∧ loaded.q.quantum = entry.assignment.quantum ∧
        committedQ corpus.frame cell.contribution.ticket entry.assignment.shard = some cell.contribution.q := by
  obtain ⟨ticket,_,shard,_,a,member,_,_,cell,hcell,_,hv⟩ := projectedQFromNativeInput p ti si row value atTicket atQ
  obtain ⟨entry,he,same,_⟩ := inputOrigin corpus member
  subst a
  have inCells : cell ∈ entry.data.cells := hcell
  obtain ⟨index,atCell⟩ := List.mem_iff_getElem?.mp inCells
  obtain ⟨loaded,hq,hquantum,hcommit⟩ := blockCellFromCommittedBytes entry.data index cell atCell
  exact ⟨entry,he,cell,inCells,loaded,by simpa only [hv] using hq,hquantum,hcommit⟩

theorem projectedTicketWeightFromAllShards {codec store trust anchor binding corpus limit}
    (p : Projected (codec := codec) (store := store) (trust := trust) (anchor := anchor) (binding := binding) corpus limit)
    (i : Nat) (row : TicketData) (atTicket : p.tickets[i]? = some row)
    {cell} (member : cell ∈ ticketCells corpus.inputs row.ticket) :
    cell.contribution.weight = row.weight := by
  obtain ⟨ticket,_,derived⟩ := collectAt p.ticketsLoaded i row atTicket
  obtain ⟨ht,_,hw,_⟩ := derivedTicketSource derived
  rw [ht] at member
  exact ticketWeightAgreesWithEveryShard hw member

theorem projectedQuantumFromAssignment {codec store trust anchor binding corpus limit}
    (p : Projected (codec := codec) (store := store) (trust := trust) (anchor := anchor) (binding := binding) corpus limit)
    (di si : Nat) (row : DomainData) (quantum : Rational)
    (atDomain : p.domains[di]? = some row) (atQuantum : row.quantum[si]? = some quantum) :
    ∃ domain, (NativeBinding.domains binding.profile)[di]? = some domain ∧
      ∃ shard, (shardIds corpus.frame)[si]? = some shard ∧
        ∃ a ∈ corpus.inputs, a.domain = domain ∧ a.shard = shard ∧ a.quantum = quantum := by
  obtain ⟨domain,hd,derived⟩ := collectAt p.domainsLoaded di row atDomain
  obtain ⟨shard,hs,hq⟩ := collectAt (derivedDomainSource derived).2.2 si quantum atQuantum
  exact ⟨domain,hd,shard,hs,quantumAtHasExactSource hq⟩

theorem projectedDenominatorFromAllAssignments {codec store trust anchor binding corpus limit}
    (p : Projected (codec := codec) (store := store) (trust := trust) (anchor := anchor) (binding := binding) corpus limit)
    (i : Nat) (row : DomainData) (atDomain : p.domains[i]? = some row)
    {a} (member : a ∈ corpus.inputs) (domain : a.domain = row.domain) : a.denominator = row.denominator := by
  obtain ⟨name,_,derived⟩ := collectAt p.domainsLoaded i row atDomain
  obtain ⟨hn,hd,_⟩ := derivedDomainSource derived
  exact domainDenominatorAgreesWithEveryShard hd member (domain.trans hn)

theorem projectedMixtureIsLeastCommonMultiple {codec store trust anchor binding corpus limit}
    (p : Projected (codec := codec) (store := store) (trust := trust) (anchor := anchor) (binding := binding) corpus limit) :
    ∀ multiple, (∀ weight ∈ binding.profile.domainWeights.map (fun d => d.weight.kernelWeight),
      weight.denominator.toNat ∣ multiple) → p.weights.denominator ∣ multiple :=
  (ApplyKernel.weightPlanLeast minInput maxInput _ p.weights).2.2.2

end DeltaReduce.NativeInputProjection
