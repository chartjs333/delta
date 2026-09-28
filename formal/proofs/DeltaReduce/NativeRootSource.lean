import DeltaReduce.NativePlanningSource
import DeltaReduce.NativeCertifiedCorpus

/-! The selected original ROOT proposal, before ROOT finalization or APPLY.
The prior PARAMETER QCs are resolved from the actual checked snapshot. -/
namespace DeltaReduce.NativeRootSource
open NativeBinding NativeEarlySource

def sectionOf (x : NativeSelectedVote.Checked) :=
  NativeCandidateAuthority.rootSection x.admitted.checked.snapshot
def rootMatches (x : NativeSelectedVote.Checked) :=
  (sectionOf x).bodies.filter (fun e => e.id == x.admitted.selected.original.body)

structure Root (x : NativeSelectedVote.Checked) where
  original : NativeAggregateLineage.Edge
  selected : rootMatches x = [original]
  kind : x.admitted.selected.original.action = 6

def loadRoot (x : NativeSelectedVote.Checked) : Option (Root x) :=
  if kind : x.admitted.selected.original.action = 6 then
    match selected : rootMatches x with
    | [e] => some ⟨e,selected,kind⟩
    | _ => none
  else none

theorem original {x} (e : Root x) :
    e.original ∈ (sectionOf x).bodies ∧ e.original.id = x.admitted.selected.original.body := by
  have mem : e.original ∈ rootMatches x := by rw [e.selected]; simp
  have pair := List.mem_filter.mp mem
  exact ⟨pair.1,by simpa using pair.2⟩

theorem fromComponents {x} (e : Root x) : loadRoot x = some e := by
  obtain ⟨e,selected,kind⟩ := e
  unfold loadRoot; simp only [dif_pos kind]
  split
  · rename_i found hf
    have same : found = e := by simpa only [selected,List.cons.injEq,and_true] using hf.symm
    subst found; rfl
  · rename_i hother; simp_all

theorem wrongAction {x} (bad : x.admitted.selected.original.action ≠ 6) : loadRoot x = none := by
  simp [loadRoot,bad]

theorem ambiguousRejected {x} (bad : 1 < (rootMatches x).length) : loadRoot x = none := by
  unfold loadRoot; split <;> try rfl
  split <;> try rfl
  rename_i e he; rw [he] at bad; simp at bad

theorem missingRejected {x} (bad : rootMatches x = []) : loadRoot x = none := by
  unfold loadRoot; split <;> try rfl
  split <;> try rfl
  rename_i e he; rw [bad] at he; contradiction

theorem checkedSection {sha policy state vote facts} (loaded : Loaded sha policy state vote facts) :
    NativeAggregateSection.bindSection sha loaded.original.policy loaded.original.state =
      some (sectionOf loaded.original) :=
  (NativeCandidateAuthority.sourceSections (NativeSelectedVote.originalByteAuthority loaded.computed).2.1).2.1

theorem checked {sha policy state vote facts} (loaded : Loaded sha policy state vote facts)
    (e : Root loaded.original) :
    NativeAggregateLineage.check sha .proposed
      (NativeParameterSection.expected loaded.original.policy loaded.original.state (sectionOf loaded.original).parameters.prior.plans)
      loaded.original.policy.validators
      (sectionOf loaded.original).parameters.prior.plans.eligibility.norms.isc.certificates
      (sectionOf loaded.original).parameters.prior.plans.eligibility.norms.isc.finalized
      (sectionOf loaded.original).parameters.prior.plans.eligibility.finalized
      (sectionOf loaded.original).parameters.prior.plans.finalized
      (sectionOf loaded.original).parameters.prior.finalized (sectionOf loaded.original).parameters.prior.keys
      (sectionOf loaded.original).parameters.prior.plans.eligibility.certificates
      (sectionOf loaded.original).parameters.prior.plans.certificates
      (sectionOf loaded.original).parameters.prior.certificates e.original.source = some e.original :=
  NativeAggregateSection.proposedChecked (checkedSection loaded) (original e).1

theorem originalShard {sha policy state vote facts} (loaded : Loaded sha policy state vote facts)
    (e : Root loaded.original) {shard} (mem : shard ∈ e.original.shards) :
    NativeParameterLineage.check sha .finalized
      (NativeParameterSection.expected loaded.original.policy loaded.original.state (sectionOf loaded.original).parameters.prior.plans)
      loaded.original.policy.validators
      (sectionOf loaded.original).parameters.prior.plans.eligibility.norms.isc.certificates
      (sectionOf loaded.original).parameters.prior.plans.eligibility.norms.isc.finalized
      (sectionOf loaded.original).parameters.prior.plans.eligibility.finalized
      (sectionOf loaded.original).parameters.prior.plans.finalized (sectionOf loaded.original).parameters.prior.keys
      (sectionOf loaded.original).parameters.prior.plans.eligibility.certificates
      (sectionOf loaded.original).parameters.prior.plans.certificates shard.source = some shard :=
  NativeAggregateSection.checkedShard (checkedSection loaded) (checked loaded e) mem

theorem finalizedContext {sha policy state vote facts} (loaded : Loaded sha policy state vote facts)
    (e : Root loaded.original) {shard} (mem : shard ∈ e.original.shards) : shard.voteContext = [] :=
  NativeFinalizedAssignment.originalContext (originalShard loaded e mem)

theorem completeLeaves {sha policy state vote facts} (loaded : Loaded sha policy state vote facts)
    (e : Root loaded.original) :
    e.original.shards.map NativeAggregateLineage.shardLeaf = e.original.certificate.common.leaves :=
  NativeAggregateLineage.resolvedLeaves (NativeAggregateLineage.checkedSource (checked loaded e)).selected

theorem identity {sha policy state vote facts} (loaded : Loaded sha policy state vote facts)
    (e : Root loaded.original) :
    loaded.original.vote.wire.bodyHash = e.original.id ∧
    NativeCandidateAuthority.parentContext sha "deltareduce.vote-context.root.v1"
      e.original.certificate.common.plan = some loaded.original.vote.wire.context := by
  obtain ⟨root,parent,hr,_,valid⟩ := NativeCandidateAuthority.rootWitness (loadedAuthority loaded) e.kind
  have find := NativePlanningSource.singletonFind e.selected
  have same : root = e.original := Option.some.inj (hr.symm.trans find)
  subst root
  have ident := loadedIdentity loaded
  exact ⟨ident.2.2.2.2.2.2.1.trans (original e).2.symm,ident.2.2.2.2.2.1 ▸ valid.2.2.2.2.2.2⟩

theorem originalPreimage {sha policy state vote facts} (loaded : Loaded sha policy state vote facts)
    (e : Root loaded.original) :
    NativeAggregateRoot.bodyId sha e.original.certificate.common = some loaded.original.vote.wire.bodyHash := by
  rw [(identity loaded e).1]
  exact (NativeAggregateLineage.checkedSource (checked loaded e)).identity

theorem leafFinalizedAndHashed {sha policy state vote facts} (loaded : Loaded sha policy state vote facts)
    (e : Root loaded.original) {shard} (mem : shard ∈ e.original.shards) :
    shard.id ∈ (sectionOf loaded.original).parameters.prior.finalized ∧
    NativeContractSize.contentId sha NativeParameter.domain (NativeParameter.json shard.certificate) = some shard.id := by
  have src := NativeAggregateLineage.everyShard (checked loaded e) mem
  exact ⟨src.2.1.1,src.2.2⟩

end DeltaReduce.NativeRootSource
