import DeltaReduce.NativeVectorJoin

/-! Constructive source-to-PARAMETER composition. Store resolution and actual
checked original arithmetic imply draft extraction; the extracted result is
not supplied as a premise. Codec, anchor authentication and source/authority
identity remain explicit boundaries, not native execution or recovery. -/
namespace DeltaReduce.NativeVectorDerivation
open NativeBinding
open NativeVectorArtifacts (RowsImage)

theorem payloadComplete {codec store ref bytes payload}
    (resolved : Resolves codec store ref bytes payload) :
    loadPayload codec store ref = some ⟨bytes,payload,resolved⟩ := by
  unfold loadPayload
  split
  · rename_i absent
    rw [resolved.present] at absent
    contradiction
  · rename_i b present
    cases Option.some.inj (present.symm.trans resolved.present)
    split
    · rename_i absent
      rw [resolved.decoded] at absent
      contradiction
    · rename_i p decoded
      cases Option.some.inj (decoded.symm.trans resolved.decoded)
      rw [dif_pos ⟨resolved.content,resolved.length,resolved.canonical,resolved.kind,resolved.typed⟩]

theorem rowComplete {codec store schema frame assignment width contribution}
    (r : LoadedRow codec store schema frame assignment width contribution) :
    loadRow codec store schema frame assignment width contribution = some r := by
  cases r with
  | mk bytes q resolved committed ticket domain shard parameterSchema quantum shape =>
    simp only [loadRow,payloadComplete resolved,Bind.bind,Option.bind]
    rw [dif_pos ⟨committed,ticket,domain,shard,parameterSchema,quantum,shape⟩]

theorem rowsComplete {codec store schema frame assignment width contributions rows}
    (bound : RowsBound codec store schema frame assignment width contributions rows) :
    loadRows codec store schema frame assignment width contributions = some ⟨rows,bound⟩ := by
  induction bound with
  | nil => rfl
  | cons loaded tail ih => simp only [loadRows,rowComplete loaded,ih,Bind.bind,Option.bind]

theorem frameComplete {codec store authority frame}
    (origin : FrameOrigin codec store authority frame) :
    loadParameterFrame codec store authority = some ⟨frame,origin⟩ := by
  obtain ⟨sb,hs⟩ := origin.schema
  obtain ⟨pb,hp⟩ := origin.plan
  obtain ⟨ib,hi⟩ := origin.isc
  obtain ⟨eb,he⟩ := origin.ec
  obtain ⟨ab,ha⟩ := origin.apc
  simp only [loadParameterFrame,payloadComplete hs,payloadComplete hp,payloadComplete hi,
    payloadComplete he,payloadComplete ha,Bind.bind,Option.bind]

theorem parameterComplete {codec store trust anchor domain shard}
    {binding : Binding codec trust anchor store} (d : DerivedParameter binding domain shard) :
    deriveParameter binding domain shard = some d := by
  cases d with
  | mk frame origin validated assignment planned assignmentFound key partition partitionMember
      partitionFound partitionKey orderedCoverage rows boundRows numerators computed =>
    simp only [deriveParameter,frameComplete origin,Bind.bind,Option.bind]
    rw [dif_pos validated]
    split
    · rename_i absent
      rw [assignmentFound] at absent
      contradiction
    · rename_i a found
      cases Option.some.inj (found.symm.trans assignmentFound)
      split
      · rename_i absent
        rw [partitionFound] at absent
        contradiction
      · rename_i p found
        cases Option.some.inj (found.symm.trans partitionFound)
        rw [dif_pos orderedCoverage]
        simp only [rowsComplete boundRows]
        split
        · rename_i absent
          rw [computed] at absent
          contradiction
        · rename_i ns evaluated
          cases Option.some.inj (evaluated.symm.trans computed)
          rfl

/-- These are source input relations. No expected output, supplied body, or
successful draft deriveParameter equation occurs in this structure. -/
structure Inputs {codec store trust anchor} (binding : Binding codec trust anchor store)
    (b : NativeVectorContext.Bound) (domain : NativeReceiptBytes.Bytes) (index : Nat) where
  layout : NativeVectorLayout.Layout
  layoutComputed : NativeVectorLayout.construct b.first.corpus.manifest.plan = some layout
  schema : NativeVectorArtifacts.Artifact
  schemaComputed : NativeVectorArtifacts.schema codec.hash layout = some schema
  authoritySchema : binding.authority.schema = schema.ref
  frame : ParameterFrame
  origin : FrameOrigin codec store binding.authority frame
  validated : ParameterFrameValid binding.authority binding.profile binding.model binding.optimizer frame
  coordinates : frame.coordinates = layout.coordinates
  shards : frame.shards = layout.shards
  assignment : Assignment
  found : frame.plan.assignments.find?
    (fun a => a.domain == NativeVectorLayout.text domain && a.shard == NativeVectorLayout.shardName index)
      = some assignment
  partition : Shard
  partitionFound : frame.shards.find? (fun s => s.id == NativeVectorLayout.shardName index) = some partition
  ordered : assignment.contributions.map (·.ticket) = eligibleDomainTickets frame (NativeVectorLayout.text domain)
  out : NativeVectorArithmetic.Result
  calculated : NativeVectorArithmetic.reduce b domain index = some out
  images : RowsImage codec store schema.ref frame assignment
    (NativeVectorContext.shape out.first).entry.count out.slices
  imagesLoaded : NativeVectorArtifacts.loadImages codec store schema.ref frame assignment
    (NativeVectorContext.shape out.first).entry.count out.slices = some images
  contributions : assignment.contributions = images.contributions
  denominator : assignment.denominator = b.source.plan.accumulator.numbers.denominator
  bits : binding.profile.accumulatorBits = b.source.plan.accumulator.numbers.accumulatorBits
  width : partition.length = (NativeVectorContext.shape out.first).entry.count
  cells : layout.positions.length * b.source.rows.length ≤ 65536
  keys : (NativeVectorArithmetic.domains b).length * layout.shards.length ≤ 4096
  schemaPresent : store schema.ref.id = some schema.raw
  byteBound : schema.raw.length + (images.sources.map (fun a => a.raw.length)).sum ≤ 8388608

theorem originalComputation {codec store trust anchor binding b domain index}
    (i : @Inputs codec store trust anchor binding b domain index) :
    ParameterKernel.checkedParameter (accumulatorLo binding.profile) (accumulatorHi binding.profile)
      minInput maxInput i.assignment.denominator i.partition.length
      (i.out.slices.map NativeVectorArithmetic.kernelRow) = some i.out.values := by
  simpa only [NativeVectorArithmetic.compute,NativeVectorArithmetic.lo,NativeVectorArithmetic.hi,
    accumulatorLo,accumulatorHi,i.denominator,i.bits,i.width]
    using (NativeVectorArithmetic.reduced i.calculated).2.2.2.2

def derive {codec store trust anchor binding b domain index}
    (i : @Inputs codec store trust anchor binding b domain index) :
    DerivedParameter binding (NativeVectorLayout.text domain) (NativeVectorLayout.shardName index) :=
  ⟨i.frame,i.origin,i.validated,i.assignment,List.mem_of_find?_eq_some i.found,i.found,
    by simpa using List.find?_some i.found,
    i.partition,List.mem_of_find?_eq_some i.partitionFound,i.partitionFound,
    by simpa using List.find?_some i.partitionFound,
    i.ordered,i.out.slices.map NativeVectorArithmetic.kernelRow,
    by simpa only [i.authoritySchema,i.width,i.contributions] using i.images.bound,
    i.out.values,originalComputation i⟩

theorem actualExtraction {codec store trust anchor binding b domain index}
    (i : @Inputs codec store trust anchor binding b domain index) :
    deriveParameter binding (NativeVectorLayout.text domain) (NativeVectorLayout.shardName index) =
      some (derive i) := parameterComplete (derive i)

theorem bodyComputed {codec store trust anchor binding b domain index}
    (i : @Inputs codec store trust anchor binding b domain index) :
    (derive i).body =
      { kind := "PARAMETER_EXPECTED", authorityId := anchor.authority.id,
        context := i.assignment.context, domain := NativeVectorLayout.text domain,
        shard := NativeVectorLayout.shardName index, denominator := i.assignment.denominator,
        numerators := i.out.values, inputLeafIds := i.images.contributions.map (fun c => c.q.id) } := by
  simp only [DerivedParameter.body,derive,i.contributions]

theorem originalRows {codec store trust anchor binding b domain index}
    (i : @Inputs codec store trust anchor binding b domain index) :
    i.out.slices.map NativeVectorContext.Slice.source = NativePlanQCorpus.inDomain domain b.source.rows ∧
    i.assignment.contributions.length = i.out.slices.length :=
  ⟨NativeVectorArithmetic.allEligibleRows i.calculated,by
    rw [i.contributions]; exact (NativeVectorArtifacts.allRowsBound i.images).2⟩

theorem bodyLeafCount {codec store trust anchor binding b domain index}
    (i : @Inputs codec store trust anchor binding b domain index) :
    (derive i).body.inputLeafIds.length = i.out.slices.length := by
  simpa only [DerivedParameter.body,derive,List.length_map] using (originalRows i).2

theorem bodyLeafAt {codec store trust anchor binding b domain index}
    (i : @Inputs codec store trust anchor binding b domain index)
    (position : Nat) (s : NativeVectorContext.Slice) (atPosition : i.out.slices[position]? = some s) :
    ∃ a, i.images.sources[position]? = some a ∧
      (derive i).body.inputLeafIds[position]? = some a.ref.id ∧
      NativeVectorArtifacts.qArtifact codec.hash i.schema.ref s = some a ∧
      a.raw = NativeVectorArtifacts.encodeQ (NativeVectorArtifacts.qValue i.schema.ref s) ∧
      store a.ref.id = some a.raw ∧
      i.assignment.contributions[position]? = some (NativeVectorArtifacts.contribution s a.ref) := by
  obtain ⟨a,positioned,generated,contributed,present⟩ := i.images.original position s atPosition
  refine ⟨a,positioned,?_,generated,(NativeVectorArtifacts.qEncoded generated).2.1,present,?_⟩
  · simp only [DerivedParameter.body,derive,i.contributions,List.getElem?_map,contributed,
      Option.map_some,NativeVectorArtifacts.contribution]
  · rw [i.contributions]; exact contributed

theorem noMissingBodyLeaf {codec store trust anchor binding b domain index}
    (i : @Inputs codec store trust anchor binding b domain index)
    (position : Nat) (s : NativeVectorContext.Slice) (atPosition : i.out.slices[position]? = some s)
    (a : NativeVectorArtifacts.Artifact)
    (generated : NativeVectorArtifacts.qArtifact codec.hash i.schema.ref s = some a) :
    store a.ref.id ≠ none := by
  obtain ⟨other,_,_,gen,_,present,_⟩ := bodyLeafAt i position s atPosition
  cases Option.some.inj (gen.symm.trans generated)
  rw [present]
  intro impossible
  cases impossible

theorem noOmittedContribution {codec store trust anchor binding b domain index}
    (i : @Inputs codec store trust anchor binding b domain index) :
    i.assignment.contributions.length = (NativePlanQCorpus.inDomain domain b.source.rows).length := by
  have count := congrArg List.length (originalRows i).1
  simp only [List.length_map] at count
  exact (originalRows i).2.trans count

theorem wrongDecodedQuantumRejected {codec store schema frame assignment width s a}
    (generated : NativeVectorArtifacts.qArtifact codec.hash schema s = some a)
    (row : LoadedRow codec store schema frame assignment width (NativeVectorArtifacts.contribution s a.ref))
    (loaded : loadRow codec store schema frame assignment width
      (NativeVectorArtifacts.contribution s a.ref) = some row)
    (different : row.q.quantum ≠ s.block.quantum) :
    NativeVectorArtifacts.loadImage codec store schema frame assignment width s = none := by
  have wrong : row.q ≠ NativeVectorArtifacts.qValue schema s := by
    intro equal
    exact different (congrArg QShard.quantum equal)
  unfold NativeVectorArtifacts.loadImage
  split
  · rfl
  · rename_i other computed
    cases Option.some.inj (computed.symm.trans generated)
    simp only [loaded,Bind.bind,Option.bind]
    rw [dif_neg (by intro checks; exact wrong checks.2)]

theorem originalCoordinate {codec store trust anchor binding b domain index}
    (i : @Inputs codec store trust anchor binding b domain index)
    {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs}
    (loaded : NativeVectorContext.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw
      permission inputs = some b) (coordinate : Nat) (within : coordinate < i.partition.length) :
    ∃ v, (derive i).body.numerators[coordinate]? = some v ∧
      checkedAccumulate (NativeVectorArithmetic.lo b.source.plan.accumulator.numbers)
        (NativeVectorArithmetic.hi b.source.plan.accumulator.numbers)
        (NativeVectorArithmetic.lo b.source.plan.accumulator.numbers)
        (NativeVectorArithmetic.hi b.source.plan.accumulator.numbers) 0
        (i.out.slices.map (fun s => ((s.source.term.coefficient : Int),
          (s.block.block.frame.values[coordinate]?).getD 0))) = some v := by
  exact NativeVectorArithmetic.originalCoordinateRefines loaded i.calculated coordinate
    (by simpa only [i.width] using within)

theorem joinFromParts {codec store trust anchor} {binding : Binding codec trust anchor store}
    {b domain index l a d out images}
    (layout : NativeVectorLayout.construct b.first.corpus.manifest.plan = some l)
    (schema : NativeVectorArtifacts.schema codec.hash l = some a)
    (derived : deriveParameter binding (NativeVectorLayout.text domain)
      (NativeVectorLayout.shardName index) = some d)
    (calculated : NativeVectorArithmetic.reduce b domain index = some out)
    (loaded : NativeVectorArtifacts.loadImages codec store a.ref d.frame d.assignment
      (NativeVectorContext.shape out.first).entry.count out.slices = some images)
    (checked : NativeVectorJoin.Checks binding b l a d out images.contributions)
    (bounded : a.raw.length + (images.sources.map (fun a => a.raw.length)).sum ≤ 8388608) :
    ∃ j, NativeVectorJoin.join binding b domain index = some j ∧ j.native = d ∧ j.out = out := by
  unfold NativeVectorJoin.join
  split
  · rename_i absent
    rw [layout] at absent
    contradiction
  · rename_i l' found
    cases Option.some.inj (found.symm.trans layout)
    split
    · rename_i absent
      rw [schema] at absent
      contradiction
    · rename_i a' found
      cases Option.some.inj (found.symm.trans schema)
      split
      · rename_i absent
        rw [derived] at absent
        contradiction
      · rename_i d' found
        cases Option.some.inj (found.symm.trans derived)
        split
        · rename_i absent
          rw [calculated] at absent
          contradiction
        · rename_i out' found
          cases Option.some.inj (found.symm.trans calculated)
          simp only [loaded,Bind.bind,Option.bind]
          rw [dif_pos checked,dif_pos bounded]
          exact ⟨_,rfl,rfl,rfl⟩

theorem joinChecks {codec store trust anchor binding b domain index}
    (i : @Inputs codec store trust anchor binding b domain index) :
    NativeVectorJoin.Checks binding b i.layout i.schema (derive i) i.out i.images.contributions :=
  ⟨i.authoritySchema,i.coordinates,i.shards,i.contributions,rfl,i.denominator,
    i.bits,i.width,i.cells,i.keys,i.schemaPresent⟩

theorem actualJoin {codec store trust anchor binding b domain index}
    (i : @Inputs codec store trust anchor binding b domain index) :
    ∃ j, NativeVectorJoin.join binding b domain index = some j ∧
      j.native = derive i ∧ j.out = i.out :=
  joinFromParts i.layoutComputed i.schemaComputed (actualExtraction i) i.calculated
    i.imagesLoaded (joinChecks i) i.byteBound

theorem actualRawRun {codec store trust anchor binding b domain index}
    (i : @Inputs codec store trust anchor binding b domain index)
    {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs}
    (loaded : NativeVectorContext.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw
      permission inputs = some b) :
    ∃ j, NativeVectorJoin.run binding sha policyRaw stateRaw apcId configRaw proofRaw profileRaw
      permission inputs domain index = some ⟨b,j⟩ ∧ j.native = derive i ∧ j.out = i.out := by
  obtain ⟨j,hj,hd,ho⟩ := actualJoin i
  refine ⟨j,?_,hd,ho⟩
  rw [NativeVectorJoin.runFromContext binding loaded,hj]
  rfl

end DeltaReduce.NativeVectorDerivation
