# R2 / ADR-0011 B — bounded feasibility spike

Tasks T044/T047/T053–T057. **Result: FEASIBLE, within the PoC scope below.**
B remains a conditional architectural option, not an accepted final design.
The user authorized at most eight active hours and an immediate stop after this
checkpoint. No continuation into full R2/R3 is authorized by this result.

## Central relation and result

An original carrier `O` holds the original shard layout, coordinate labels,
complete canonical command, vote event, certificate event/identity, and diagnostic
durability record **once**. A shared control state `C` has one journal, sequence
and current pointer. For width `n`, the representation is

`F(O,C,x) = (O,C, k ↦ x[k]), k : Fin n`.

`k` is an index of the representation. It is absent from every protocol identity,
vote context, certificate identity and durable sequence. Reconstruction uses
`List.ofFn` in original index order. In the executable witness the cell contains
the original coordinate label, Q input, PARAMETER result, model and optimizer
coordinate. This is a **fixed computed PARAMETER object and its parent vectors**;
the spike does not implement an APPLY/current-state update.

The isolated Lean module proves both round trips, joint injectivity, exact ordered
coverage and equality of all identity observations between views. It also proves
commutation with the **existing** `RecoveryKernel.step`, retaining its admission,
receipt/effect and authentication premises. A successful original vote appends the
same original record exactly once, regardless of width; rejection yields no family
result. The history lemma preserves the exact list of original vote records.
These are conditional mathematical journal lemmas, not physical WAL theorems.

`checked_parameter_family` reuses the existing checked PARAMETER computation to
derive every scalar result at the same bounds and original row order. Its result
is not supplied as a translation assumption. The generic relation works for any
payload type and length; it contains no `length = 1` restriction. Existing
`VectorShardRepresentation` proofs for widths 4/8/8/8/8 remain unchanged.

The `Synchronized` lemma is explicitly a lifting rule: its scalar-transition
premises must be established. It is **not** advertised as an independent proof of
production/native transition equivalence. The concrete TLA experiment below
checks those production actions for the selected finite suffix.

## Original source used, including its limits

The selected object is the existing `native-coordinate-matrix` trace's complete
`d00/s01` shard, length **3**, offset **2**, coordinates `p0002/p0003/p0004`:

| Item | Preserved value |
|---|---|
| Q / computed PARAMETER | `[3,-4,5]` / `[3,-4,5]` |
| Parent model / optimizer slice | `[20,-20,20]` / `[2,-2,2]` |
| Original vote | event 22, validator-1, `PARAM:d00:s01:round-1` |
| Durable sequence | **5 → 6**, one original selected record |
| Whole body ID | `sha256:ac5ef1d07377f6e1f2f528d6c56c25377d1e7e4799c324bdc126189280d5200f` |
| Original QC trace identity | `sha256:27e20cab65cf621e5cdca37f7d9dec2224332509ba0d5c77ae0a28e24d77dfcc` |

The original source and trace raw SHA-256 values are hard-pinned in the runner.
The existing `Witness.expected_parameter`, `NativeEvidence.check` and
`check_durability_trace` recompute/check the original body and original diagnostic
prefix. Reconstructing the family produces **exactly the original command bytes**;
receipt/effect, complete event records and QC label remain byte-for-byte unchanged.
No coordinate body is rehashed into a vote/certificate.

This source is a **synthetic diagnostic fixture**. Its QC result is a retained
trace identity; it does not provide an authenticated signed native QC preimage.
Its receipt/effect/journal encoding is the existing diagnostic projection, not the
production WAL format or a physical fsync observation. Preserving these objects
does not authenticate them. The 4/8/8/8/8 Q/manifest fixture has no joined original
vector vote/QC/WAL capture; a scalar native certificate was **not** substituted for
it. This is why the concrete synchronized experiment uses the existing width-3
object while the lossless and arithmetic lemmas remain length-parametric.

## Unchanged production predicates exercised

`BFamilySpike.tla` is generated only under `formal/build/b-feasibility` and copied
into proposal evidence. It instantiates the unchanged `DeltaReducePhase6Harness`
and `DeltaReduce` three times, one for each target coordinate, with **one scheduler**.
All three instances take the same event, actor and lifecycle step together:

`ProposeParameterResult → VoteParameter → SendVoteEnvelope → DeliverVoteEnvelope
→ FinalizeParameterQC`.

The source has three domains and two original shards. All input values, ticket
weights, denominators, quantum and parent-vector coordinates come from the pinned
source. The selector for non-target `s00` is coordinate zero in every view;
the selector for target `s01` covers all three coordinates, without padding.
The preceding `s00` PARAMETER sequence is executed so selected `s01` retains
sequence 6. The target's three signers remain validator-1/2/3 in every view;
coordinates never increase signer power.

The complete finite suffix satisfies `[][DeltaReduce.Next]` in every view,
production type predicates, common control and exact whole-record constraints.
Common control compares the 56 fields not containing projected arithmetic bodies,
plus complete actor/kind/context vote footprints, message copies, PARAMETER result
keys, vote keys and QC signer sets. Full arithmetic body validity is checked by
the unchanged production actions, rather than a count-only equality.

The harness's `originalJournal` is a **register of the selected diagnostic receipt**,
stored once. It is not a replacement production journal or a claim that earlier
five records are absent. The full original diagnostic prefix is checked separately;
the Lean append lemma quantifies over an arbitrary existing journal prefix.

`Phase6Init` supplies a certified upstream state, including ready nodes and available
inputs. This is not a derivation from empty production `Init`, not the original
complete trace's authenticated public-state projection, and not an R3 recovery
proof. Production `Init`, `Next` and every imported predicate are unchanged.
The harness retains their existing finite bounds (limit127); it adds no native
admission restriction.

The meaningful negative results are:

- A persist in only two of the three views violates `CommonControl` immediately.
- Finalization with only two delivered original signers has no successor under
  `FinalizeParameterQC`; three coordinates do not supply the missing third signer.
- Missing/extra/reordered/duplicate coordinates, changed input/result/model/optimizer,
  a per-coordinate vote identity, changed coordinate label, or a changed original
  sequence/QC carrier are rejected by exact reconstruction.

No production predicate change was needed for this central finite construction.
This demonstrates a representation-only path for B; it does not establish B's
general sufficiency for every remaining R2/R3 obligation.

## Assumptions and obligations this PoC does not close

1. Authenticated source/exporter, alias/configuration/metadata provenance, signatures
   and complete native QC/certificate preimages. The diagnostic carrier's origins
   remain named trust boundaries, not proved authority.
2. A fully joined original 4/8/8/8/8 vote/QC/WAL capture. The existing manifest and
   component arithmetic proofs are preserved; this spike does not invent that join.
3. Full public body/authority construction for every domain/shard, all vector lengths,
   complete arbitrary prior durable sets, and the general lifting of every reachable
   production action from actual native admission. The executable witness is one
   existing complete shard and a certified-prefix suffix.
4. Native INT64/INT128 coverage, `INT64_MIN`, the symmetric public result guard,
   narrow versus wide guard compatibility, and APPLY/conversion/mixture/optimizer
   transitions. The numeric example passes the existing limit127 predicates;
   wide success is not assumed to imply narrow acceptance.
5. Physical WAL/fsync/crash execution, scan authentication/exact absence, unknown or
   corrupt recovery, arbitrary starting snapshots, failures and repair, global
   public state roots, and native/public recovery refinement. These remain R3.
6. R4–R7 qualification, frozen final evidence/reproduction and independent review.
   This is self-reviewed local evidence; there is no new FormalVerificationReport(GO).

These are existing residual boundaries, not new DoD requirements. **R1 stays CLOSED;
R2/R3 stay OPEN; R4–R7 are untouched.** The completed subquestion is that a complete
synchronized scalar family can preserve a single original object and reassemble
its ordered vector data without adding coordinate protocol identities.

## Reproduction and evidence

Run from the candidate root with the existing pinned tools:

```powershell
$env:JAVA = 'D:/formal-tools-20260920/java/bin/java.exe'
$env:TLA2TOOLS_JAR = 'D:/formal-tools-20260920/tla/tla2tools.jar'
$env:SPIKE_LAKE = 'D:/formal-tools-20260920/lean/bin/lake.exe'
C:/Python312/python.exe -X utf8 formal/proposals/b-feasibility/check_spike.py
```

The runner checks original bytes, reconstruction negatives, fresh proposal kernels
and axiom inventory, then actual production TLA instances. TLC uses the locked
JVM/jar plus explicit `-Xss16m` for three complete state instances; this isolated
option is recorded in evidence and does not modify the toolchain lock. An initial
run with the default stack exhausted the evaluator stack; rerunning with the
recorded stack size completed. Negative full TLC traces remain in the ignored
build directory; committed logs explicitly identify their excerpts and raw hashes.
The reused dependency build reports existing unused-simp warnings in
`NativeConfigAdmission.lean`; new spike kernels have no warnings or `sorryAx`.

Evidence is in `formal/proposals/evidence/b-feasibility/` and its companion source
manifest. No mandatory module/schema/fixture, protocol/runtime source, semantic
registry, report, accepted DoD or frozen demo ref is changed. Demos were read-only
health-checked and not restarted. **STOP after this checkpoint.**
