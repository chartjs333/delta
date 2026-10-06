# ADR0017 addendum: existing storage producer / observation audit

6 October 2026. T047/T053. **E ABSENT IN THE AVAILABLE CORPUS.**
**F NOT SELECTED; O NOT SELECTED; STOP / R2.3 OPEN / Formal NO_GO.**

This answers the user's subsequent instruction to exhaust E before making any
trust/model choice. It is a documentary audit, not a new contract, source-domain
predicate, proof layer or implementation. ADR0016's approved byte/key contract
and the closed R2.1/R2.2 domains remain unchanged.

## Result and boundary of the finding

No inspected immutable contract together with its original evidence establishes
**physical availability at the original attestation and AC-finalization cuts**.
Existing ownership requirements, signatures, local I/O, immutable content IDs,
retained source bytes and model-generated traces each cover part of the path.
None provides the missing factual, complete per-location history and ordering
at those cuts. This is the same source-origin obligation identified in ADR0017,
not an additional requirement.

The finding covers the enumerated accessible repository history, all currently
advertised remote refs, attached worktree HEADs, supplied project evidence paths
and current official nginx-qa input. It does **not** assert that an undisclosed
external implementation or an unreachable/unprovided artifact cannot exist.
Such an artifact would be new evidence requiring its own applicability check;
it cannot be presumed into the current theorem.

## Corpus and reproducibility

The discovery snapshot began at `2026-10-06T14:06:37Z`, checkout
`14c78004910eb166bf41f379fb0eb4b10c5bba6f`, branch
`agent/isc-s16-continuous-sprint`.

- Enumerated 248 local refs, 182 advertised `origin` refs including PR refs,
  and worktree HEADs. Traversed their reachable history: 1,014 commits and
  22,126 distinct blobs. These counts describe search coverage, not R2 progress.
- Searched the full bytes of 22,059 text blobs (no excerpt/size cutoff) for
  availability actions/admission, source authority, retention, storage/artifact
  producers, observations, journals and physical fault events. Retained all
  1,114 matching blob identities and exact SHA-256 values.
- Followed the actual producer/caller and evidence-generator paths below.
  Search hits alone are not the basis for rejecting E. `rev-list` paths can be
  representative aliases, so actual `commit:path` versions were checked separately.
- Classified 67 binary blobs: decompressed the seven relevant TLC log/graph
  archives; inspected archive text in presentations and demo static content.
  Crypto-library archives, signatures/keyrings, images and unrelated dataset
  binaries are not original storage-event evidence. No new native/formal runs
  were performed or inferred from these historical outputs.
- The only advertised object initially absent locally was PR50 merge
  `db2b90ba5fbccfbcde83d1e938efc46a5af47c45`. Fetched that object with
  `--no-tags --no-write-fetch-head`; no ref changed. Its native/docs/specs/formal
  trees add no difference over N for this audit.
- Searched the supplied `D:/delta-data` and `D:/delta-presentation` evidence
  paths and relevant untracked candidate filenames without modifying them.
  The seven demo validator bootstrap files do not enroll a storage observation
  authority; they explicitly do not authorize execution. The presentation
  continuation file contains earlier documentary checkpoints, not a producer.
  Private credentials, nginx backend state/queues and unrelated personal data
  were not used as authority or evidence.

The exact ref roots, search expressions, candidate blob inventory and exclusions
are in [the corpus index](evidence/0017-existing-producer-corpus.json).
[The source audit](evidence/0017-existing-producer-audit.json) records immutable
`commit:path`, Git blob IDs, SHA-256, historical versions and binary/external-path
classification. To reproduce discovery, traverse the **recorded object roots**
with `git rev-list --objects`, inspect blobs with `git cat-file --batch`, apply
the recorded expressions, then inspect the pinned source/evidence paths below.
Do not substitute future branch tips or treat generated evidence as observation.

## Candidate-by-candidate disposition

Pins used in this table:

| Pin | Exact commit |
|---|---|
| N — native/model source | `60c692f6e391f839829dfc64e93380db54cd507b` |
| P — Snapshot Provenance Profile v1 | `26eb02d0632435c9aa0d8ef44eb496b6fa73dd13` |
| S — approved ADR0016 storage bytes/keys | `1438fa3d78ec99291475cf4660fd8c190ac01bb3` |
| H — saved coordinator evidence | `14c78004910eb166bf41f379fb0eb4b10c5bba6f` |
| M — benchmark producer path | `437558d886d4fc7aac4d8a72f2e4d69696fab7f7` |
| D — MNIST native demo | `79293c1a2cac5721c5cc9609af621c83d317520b` |

Every path below is relative to its pinned commit, not necessarily the current
checkout. Exact bytes and hashes are retained in the audit JSON.

| Candidate / exact source or original evidence path | What it establishes | Why it is not E |
|---|---|---|
| N `.specify/memory/constitution.md` IX/X; `specs/003-bft-round-state-machine/spec.md` US2, FR-014/015/019; `specs/000-formal-tla-spec/failure-semantics.md` storage rows and safety/liveness scope | Enrolled role-bound identities; full-shard retrievability requirement; repair/fault behavior; conditional liveness assumptions | Requirements assign responsibility but do not supply an independently observed complete physical history. Liveness's availability assumption is not a safety proof that no pre-finalization loss occurred |
| N `formal/tla/DeltaReduceAvailability.tla`: `AttestAvailability`, `HasCompleteAvailability`, `FinalizeAvailability`, loss/corruption/repair actions | Exact abstract physical guards, with legal later loss preserving accepted lineage | Model state is the fact the native source must justify. Replaying that model or constructing a successful public projection cannot authenticate the original physical facts |
| N `delta-core-cpp/include/delta/core/consensus.hpp`, `src/consensus.cpp`: `AvailabilityProof`, `InputLedger::record_availability`; `src/transition.cpp`: `ACCEPT_AVAILABILITY` | Aggregate content/leaf/attester/threshold checks; context/idempotency; coarse phase/count transition | Six-field admission has no original per-location event/cut evidence. Across all three core versions and both transition versions no alternative physical observer was found. Existing checked call inventory is test-only at N |
| N `delta-runtime-cpp/include/delta/runtime/runtime.hpp`; ADR0010 artifact-state-journal ownership | Native WAL persistence/replay and runtime ownership of durable state | No implemented complete original storage-event producer was found. A durable command is evidence of persisting that command, not of the truth/completeness of its remote physical inputs |
| N Java `distribution/DownloadJournal.java`, `PeerPlane.java`, `CasStore.java` | Hash/length-verified local pieces, durable local publication, bounded retry history, discovery and repair | `DownloadJournal` atomically rewrites the current verified-piece map; reverify removes invalid pieces. It is not an immutable inventory of original loss/corruption cuts. `PeerPlane` explicitly declares discovery non-authoritative. A read, lease or repair receipt lacks the required no-unobserved-loss/cut guarantee |
| N `delta-core-cpp/src/distribution/certification_policy.cpp`; `specs/005-content-addressed-p2p-distribution/formal-refinement.md` | Certified aggregate/checkpoint distribution and repair | This plane excludes worker Q shards, commitments and AC fragments from global publication. Its immutable manifests cannot be substituted for the AC-producing storage contract |
| N feature005 `evidence/native-execution.json`, `evidence/distribution-refinement.json`, `evidence/traces/legal/multi-peer-repair.json`; `scripts/capture_native_execution.py`, `scripts/generate_refinement_traces.py` | Source-bound CI qualification and generated distribution refinement traces | The native evidence explicitly says `semantic_completeness_claimed:false`. CI source is `01f200b193733a1b474ad755c5c0c739b3189a96`. The trace generator copies/edits formal fixtures; it does not capture original storage observations. CI URLs in the manifest were not reclassified as storage evidence or freshly rerun |
| N Java `apply/ArtifactEffectAdapter.java`; Python `artifacts/filesystem.py` | Local artifact write/repair or immutable hash/length-checked publication | Local I/O success does not establish another enrolled storage location at the original finalization cut. The adapter authorization boundary supplies no complete physical observer |
| M Java `benchmark/MeasuredStageCTransport.java:causalMessages`; native `benchmark/fault_execution.cpp:parse_causal_schedule`, `execute_storage_crash`, `execute_storage_restart` | Actual loopback delivery and native/WAL execution for supplied fault scenarios | Java creates `STORAGE_SIGNAL` from the requested CRASH/RESTART scenario with delivery false/true. Native code consumes that schedule and coarse availability admission. This is measured execution of a constructed scenario, not independently captured physical shard history. All seven native fault-execution versions were considered |
| D `integration/mnist-delta/native/mnist_delta_node.cpp` | Native computation and WAL demo path | `availability_id` is derived using `deltareduce.demo.mnist.availability.v1`; the demo submits coarse availability commands. None of its four versions supplies original enrolled storage observations at AC cuts. This finding does not deny the demo's actual computation/WAL evidence |
| H `formal/proposals/native-available-q.md`, `native-available-q-lean-proof.md`, `native-source-artifacts.md`; `formal/scripts/public_state_storage.py` | Typed source-byte/arithmetic/projection results and lossless evidence pooling | The AvailableQ work explicitly retains `UNAUTHENTICATED_COMPONENT_INPUT` and excludes physical availability. Raw preimages/root matching do not establish source authority. `public_state_storage.py` is field pooling, not an artifact-state journal |
| P Profile v1; S `docs/adr/0016-storage-availability-source-binding-v1.md`; reviewed audit `a2fd17259240be0a7721512e7a12fe972587f3bf:formal/proposals/evidence/storage-producer-boundary.json` | Independent checkpoint/bootstrap authority, faithful retained bytes/source index, exact storage statement authentication; prior missing-producer finding | T authenticates/retains its designated objects; Rs/Ks/SAG1 authenticate statements. Neither certifies that all physical faults were observed and correctly ordered at original cuts. The previous audit is evidence of the gap, not a producer filling it |

The Java download/discovery/CAS components, artifact adapter and production
availability module each have one source version in the enumerated history.
The corpus therefore does not hide a second implementation of those candidates
behind a different branch name. Exact first-version commits are in the audit JSON.

## Distinction no discovered candidate resolves

For one original leaf and configured threshold 3, upload and attest at three
original storage locations. Before AC finalization, lose one location using the
existing `LoseArtifactPreFreeze` action. Historical attestation coverage remains
3; currently available attesters become 2. The original `HasCompleteAvailability`
guard becomes false while the same authentic statements remain available.

This is the existing guard distinction, **not** a newly proved production attack,
full valid-snapshot counterexample or impossibility theorem. None of the candidate
evidence above independently rules out that original ordering. A later probe
cannot reconstruct it merely by finding the bytes now. Conversely, loss *after*
lawful finalization does not invalidate or erase original AC/ISC lineage.

## F — additional factual-history trust, not selected

**Trust consequence.** Add an explicit guarantee that a designated observation
boundary truthfully and completely records the original materialization,
attestation-producing observation, physical loss/corruption and repair facts,
with their order relative to each relevant cut. The guarantee must be independent
of public-state construction and R2 acceptance. No inspected component already
has it. Extending faithful T to provide it changes Profile v1's trust model;
assuming an external observer leaves its realization unqualified.

**Theorem consequence.** The prospective statement becomes conditional:
given the already frozen premises **and a truthful, complete, correctly cut
physical history**, its source binding and the existing R2.1/R2.2 relation yield
the required public representation. A later recovery theorem would inherit the
same explicit premise. This paragraph states a possible claim shape; it does not
define a new predicate or prove the conditional theorem. The premise concerns
physical facts and ordering, not the desired refinement conclusion, so it need
not be circular; its truth still cannot be proved by signing its own assertions.

Production `Init/Next` and original QC/WAL bytes can remain unchanged, but the
qualified environment/domain and the production/article claim change. The old
results do not discharge this new premise. R2 source composition would still
need proof. Assuming F alone cannot close the currently selected production GO
or justify claiming verified physical provenance. Complete evidence may itself
be unavailable; F supplies no new liveness guarantee.

## O — authenticated/observed availability claim, not selected

**Trust consequence.** Make the protocol's state mean authenticated statements
or bounded observations, with explicitly decided fault, retention and observation
rules. This can avoid assuming an omniscient physical-history observer for that
weaker claim. It does not establish physical availability; any implication from
statements to actual retrievability still needs separately justified assumptions.

**Theorem consequence.** The prospective theorem relates native histories to a
revised observed/certified model, not to the present physical-cut model. Replacing
`HasCompleteAvailability` with `HasAttestationCoverage` alone would permit the
pre-finalization-loss example above. That illustrates a concrete semantic change,
not an approved safe implementation. Exact new guards and failure/repair behavior
remain undecided; O cannot be executed as a relabeling exercise.

`AvailabilityNext` and its production `Next` composition, availability/freeze/
lineage/repair/abort invariants, liveness assumptions, mutants and refinement
fixtures would need requalification. `Init` changes depend on the eventual state
representation. Dependent Lean public-state constructors/source/refinement claims
and the recovery theorem would need review against the changed model. Existing
R2.1/R2.2 mathematics remains closed for its original domain; reuse in a new
composition is not automatic qualification. Existing evidence remains historical,
not false merely because O was discussed. No old certificate/signature/QC/WAL may
be migrated or reinterpreted under new semantics. No new semantics ID is assigned.

The article/GO claim would say **authenticated/observed availability under the
decided rules**, not verified physical availability at the original cut.
Authentication alone proves neither retrieval nor progress. This change requires
an explicit protocol/claim decision and a subsequent scope, not general R2.3
implementation authority.

## Checkpoint

The E search is complete for the recorded corpus. No sufficient existing E
references were found, so no new Pending decision was created purporting to
contain them. Existing request `scope-request-09adbfc8a16275064414fca2743101b1`
is preserved; it does not select F/O. Neither alternative has been adopted.

No graph RESUME/result, duplicate review, ACK, amendment, runtime/schema/proof
change or new source-domain restriction was made by this audit. The existing
scope8 ACK was GET-confirmed. The final API snapshot and document hashes are
recorded in the audit evidence. The outstanding decision is exactly whether to
accept F's changed trust/conditional claim or O's changed protocol/model claim,
unless genuinely new E evidence is supplied. **STOP remains in force.**
