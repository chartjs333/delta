# ADR-0014 — ISC Producer Integration v1

**Status: DRAFT / ARCHITECTURE CHECKPOINT. Not approved for implementation.**

30 September 2026. Existing tasks: feature-008 T016, HR008-002/003/015/018;
feature-000 T053. Documentation only; R2.3 and R3 remain stopped.

Source base: `ce63d3eca0175b5b82726a1994402dc14d3be1b5`.
Native source reference: `60c692f6e391f839829dfc64e93380db54cd507b` (PR50).
The latter is an inspected implementation reference, **not** a merged formal authority.
Exact inspected blobs are recorded in
[the source inventory](evidence/0014-isc-producer-integration-source-audit.json).

## 0. Decision boundary and result

The accepted ownership is unchanged: C++ core computes the certificate and candidate
protocol state; native runtime alone owns the single-writer transaction, WAL,
durability barrier, commit and exposure. Java carries opaque messages. No new authority.

The intended transaction is:

```text
durable, authenticated and delivered matching ISC votes
+ previously closed/frozen ordered inputs + exact round context
→ validate and construct one canonical ISC candidate in pure core
→ append one complete native transaction to the existing WAL
→ durability barrier
→ commit certificate membership, finalized index and replay receipt together
→ expose the original canonical ISC/effect
```

**A complete, executable integration contract cannot yet be declared specified.**
The audit found a missing concrete binding for an existing obligation, feature-008
**FR-004: the ISC contains the ordered input array and its Merkle root**.
Neither the inspected contracts nor the native implementation specify how an ISC
tuple becomes a Merkle leaf: its exact bytes, leaf hash domain and the selection
of the existing Merkle construction for this particular object.

`InputLedger::freeze` returns ordered ticket/commitment/AC references, not that root.
`ChainVerifier::verify_input_set` validates context/signers and obtains the canonical
certificate ID, but does not establish that `input_root` commits to `tuples`.
The fixture generator supplies `cid("input-root")`, independent of the tuple array.
An existing generic Merkle helper is not an ISC leaf contract.

**STOP at this architecture checkpoint: CANONICAL ISC INPUT-ROOT BINDING MISSING.**
No leaf encoding/domain, replacement root, new predicate or producer implementation
is introduced here. This is an unresolved concretization of FR-004, not a new DoD
item. It does not reopen the accepted R2.1/R2.2 structural/arithmetic results.

It has **not** been established that production `Init/Next`, the existing QC ID
formula or old WAL identities must change. It *has* been established that simply
connecting the existing helpers does not verify the required root binding. Choosing
the missing certificate-byte interpretation, or silently treating the root as an
opaque label, would exceed a claim of an already fixed integration contract.
The sections below preserve the determined transaction requirements and identify
the exact blocked precondition; they are not an implementation authorization.

## 1. Exact inputs and their owners

All values come from the native reactor's verified source cut. A caller-supplied
snapshot, a hash-shaped string, or a Java boolean does not establish their authority.
This ADR consumes the approved provenance profile; it neither implements its importer
nor declares the full source state admissible for R2.

| Input | Existing fields/type and required binding |
|---|---|
| Round | `round_id`, `height`, `view`, `validator_epoch_id`; exact equality with the admitted round and proposal context |
| Parent | `RoundConfig.parent_checkpoint_id`, `RoundState.parent_checkpoint_id` and the issued WorkTicket parent bindings agree. Do not add a new parent field to ISC or substitute a model label for the existing checkpoint identity |
| Configuration | Exact canonical `RoundConfig` bytes and existing content ID; finalized configuration authority; ticket plan, close policy, schema/arithmetic profile, logical deadlines and round bindings. Preserve the existing normalized configuration association where a field is outside the 003 byte object |
| Validator set | Independently authorized epoch and original ordered validator IDs, role/key bindings from existing enrollment/authentication contracts. Never derive membership from the votes being checked |
| Quorum profile | Existing `QuorumPolicy`/`ValidatorPolicy`: `n=3f+1`, `q=2f+1`; configured threshold, certificate threshold and epoch agree. No arrival-dependent threshold |
| Frozen inputs | The prior `InputLedger::freeze()` result: original `ticket_id`, `commitment_id`, `certificate_id`. Bind `domain_id` from the original ticket; construct the existing `InputTuple` fields `availability_certificate_id`, `commitment_id`, `domain_id`, `ticket_id`. Preserve strict `(ticket_id, commitment_id)` order and uniqueness |
| Closed body | Existing `VoteInputSetBody`: full `Context`, `input_root`, `tuples`. Its content ID is `vote_input_set_body_id`. It is already a closed proposal, not a caller-created alternate input set. **Root-to-tuple verification is the blocked binding in §12** |
| Original envelopes | Canonical original `Vote` bytes, original signature/authentication material and signer/epoch binding, `vote_id`, and the existing persist/send/delivery lineage. All original `durable_sequence`, `signature_id`, context/body hashes and signer IDs remain intact |
| Reactor cut | Complete delivered-vote inventory at the serialized finalization point, existing local durable-prefix position, current finalized-per-round index, complete prior certificate collections, exact request bytes/ID and immutable policy/source bindings |

Vote fields are unchanged: `body_hash`, `context_id`, `durable_sequence`,
`formal_semantics_id`, `height`, `kind`, `round_id`, `schema_version`, `signature_id`,
`type_name`, `validator_epoch_id`, `validator_id`, `view`.

`signature_id` alone is not signature verification. A transport receipt alone is not
proof of remote disk persistence. Existing honest-validator persist-before-send and
Byzantine-threshold assumptions remain explicit; this transition adds no remote
disk attestation certificate. Received remote votes must not be rewritten as local
votes or renumbered into the receiving validator's own `VoteJournal`.

## 2. Preconditions and existing TLA actions

The following are **requirements for the future implementation**, not newly proved
predicates. No production TLA action is changed by this document.

| Existing action | Required concrete correspondence |
|---|---|
| `CloseInput(round, config)` | Finalized configuration; certificate progress open; exact eligible availability entries from the ticket plan. `OMIT_UNAVAILABLE` and `ABORT_ON_INCOMPLETE` retain their existing meanings. Reuse the previously frozen result; do not re-freeze on receipt of late inputs |
| `VoteISC(validator, body)` | Body is closed, no round abort, correct validator/round/epoch/context; existing local durable vote guard and no conflicting honest vote. Vote persistence precedes exposure. The finalizer does not manufacture another vote |
| `SendVoteEnvelope` | Only a previously persisted/exposable original vote is sent. A vote sitting in the journal is not automatically delivered |
| `DeliverVoteEnvelope` | The original envelope has passed the existing authentication/transport boundary and is in the serialized received inventory. Mere presence in an input file is insufficient |
| `FinalizeISC(body)` | The body is closed; `ISCSigners(body)` at this cut reaches quorum; `FinalizedISCBodiesFor(body.round)={}`. Global `OrdinaryNext` guards remain active: ACTIVE phase, before hard deadline, no pending abort. Commit exactly one new certificate membership |
| `GenerateSeed(isc)` | A separate action after the ISC is durably committed. Finalization itself does not create/reveal a seed |

The abstract `FinalizeISC` preserves `QuorumVariables`, including per-validator
durable vote sequences. Its native durable transaction must not be projected as a
new `VoteISC` or as an extra per-validator vote sequence increment.

Existing native representation bounds are retained and checked before allocation
and append: fixed-width counters, canonical certificate bounds, codec size limits,
sequence exhaustion and configured ticket/committee bounds. This ADR does not add
a smaller source-domain cap or claim that whole-state R2 bounds have been closed.
In particular, the existing native nonempty-input guard must not be described as
a newly proved universal consequence of public `OMIT_UNAVAILABLE`.

## 3. Grouping and quorum algorithm

For a **previously closed** body B, pure core performs the following finite work:

1. Read the complete received inventory at one reactor cut. Preserve the source
   inventory and journal multiplicity; do not let Java choose a quorum subset.
2. Decode each original canonical vote and verify its enrolled signer/epoch/role
   and existing authentication evidence. Check ISC kind and full proposal binding.
   A generic `validate_quorum` success does not replace these per-vote checks.
3. Group by the *comparison tuple*: formal/schema version, ISC kind, round, height,
   view, epoch, exact configuration and parent binding, parameter/arithmetic profile,
   and exact canonical B bytes (root and ordered tuples). Hash equality is accompanied
   by source-byte equality. This tuple is a grouping/checking key, **not a new vote ID**.
4. Require each contributing vote's existing `context_id` to equal
   `vote_context_id(input_set, ...)`, and `body_hash = vote_input_set_body_id(B)`.
   The existing ISC vote context hash is round-scoped; do **not** replace it with
   a newly hashed full-context tuple. The full tuple checks supplement that ID.
5. Count distinct original validators in the matching delivered group, never
   message copies or repeated vote frames. Preserve conflicting Byzantine evidence;
   do not pretend that a local honest `VoteJournal` is a global journal rejecting
   every Byzantine history. A vote for another body contributes nothing to B.
6. Select the **entire** matching delivered signer set at this cut, sorted by the
   existing canonical signer order, with cardinality at least q. This matches
   `ISCSigners(body)`; taking an arbitrary first-q subset would not implement that
   action at this cut. Later arrivals do not rewrite an already finalized ISC.
7. Construct the existing `InputSetCertificate{B.context, B.input_root, q, signers,
   B.tuples}`. Run `verify_input_set` as a structural/context/signer back-check,
   in addition to the lineage, authentication and root checks above.
8. Construct a candidate state by preserving all prior collections and adding
   precisely this ISC and its finalized membership. No deletion of downstream
   lineage, re-keying or coordinate-level objects. Return an internal candidate,
   not externally sendable bytes.

`ISCBuilder/QC` names the existing feature-008 plan node. No such complete producer
was found in code; its future implementation must perform these steps.
`as_input_certificate(body, policy)` currently inserts **all configured validators**
for proposal validation; it must not be reused as the actual quorum builder.

The same body and the same received cut produce identical bytes. Different legal
cuts may have different signer sets and therefore different existing QC IDs.
This ADR does not add a new global minimum-quorum-selection rule or promise identical
QC bytes across unequal signer cuts. Round finalization and retry preserve the first
locally committed certificate under the existing safety contract.

## 4. Canonical identity and helper reuse

For an existing typed ISC C:

```text
ISC_ID(C) = "sha256:" + lowerhex(SHA256(
  ASCII("deltareduce.008.input-set-certificate.v1") || 00 || canonical_json(C)))
```

Keep the existing field order, versions, context, ordered tuples and sorted unique
`signer_ids`. The body ID (`deltareduce.vote.input-set-body.v1`) is a different ID;
it excludes quorum-only signer/threshold data. Neither is the generic type-004 QC
envelope's content ID. Do not alias these three identities.

Original Vote IDs use the existing type-003 vote domain over the original complete
canonical envelope. Association with typed ISC is retained as native evidence,
without inserting vote IDs, new signatures or a new certificate type into ISC bytes.
All old vote/QC bytes and their hashes remain unchanged.

| Existing helper | Reuse; limit of its current guarantee |
|---|---|
| `InputLedger::freeze` | Existing ordered references, stable repeated freeze; lacks ISC root production and quorum assembly |
| `VoteJournal::record` | Local original vote uniqueness/replay; not a delivered-vote collector or signature verifier |
| `validate_quorum` | Existing threshold, canonical signer membership and supplied vote-ID cardinality checks; not a received-vote assembler |
| `ChainVerifier::verify_input_set` | Existing context/signer/encoding back-check; no Merkle derivation or producer proof |
| `canonical_json` / `content_id` | Exact existing typed ISC identity; never serialize structs or reconstruct a different signed body |
| Runtime WAL/receipt cache | Existing single writer, durable directory binding, append/barrier and exact receipt replay; requires the missing transaction integration described below |

## 5. Durable transaction contract and unresolved storage binding

The existing `FINALIZE_INPUT_FREEZE` handler is **not** renamed or reinterpreted:
it only changes coarse `RoundState` phase/counts. The new producer must have a
distinct command dispatch path for the already existing abstract `FinalizeISC`.
It is not a new public protocol action.

The required state transaction is:

1. **Validate:** verify all inputs, finalized-round conflict and request replay;
   build candidate on a private copy; preflight bounded receipt/effect buffers and
   counter exhaustion. No mutation of frozen inputs or committed collections.
2. **Append:** append one self-contained finalization transaction to the same
   native-owned consensus WAL. It must bind prior source/policy, exact original
   request, closed body, full received cut used, original envelope bytes, candidate
   ISC bytes/ID, next certificate membership and exact effect/receipt. A hash without
   recoverable bytes is insufficient. No parallel ISC authority journal.
3. **Barrier:** complete the existing fsync/durability and directory-binding checks.
   Until successful, no sendable ISC/seed effect or success receipt escapes.
4. **Commit:** atomically install ISC collection/index and immutable source-policy
   generation, source cut and exact replay cache entry. Keep previous generations
   for interpreting original vote records; never rebind them to a later policy.
5. **Expose:** return the committed canonical ISC effect and its original transaction
   receipt. Java may now send; network duplicates carry the same effect identity.

The current record shape is `DRW1(sequence, kind, command_or_vote_bytes,
next_state_bytes, effect_batch_bytes, wal_record_bytes, checksum)`.
Current kinds are 1=transition and 2=vote; recovery of kind 1 only understands the
coarse `RoundState` command handler, while kind 2 binds a startup policy identity.
Thus simply passing a hash-only `Command` to `Runtime::submit` loses the required
producer evidence and certificate state. Resetting `vote_authority_invalidated_`
or replacing the startup snapshot by caller data would not solve this.

**The exact new capsule/discriminator is not selected after the checkpoint in §0.**
It is a remaining concrete integration decision, not an existing implemented format.
Any subsequently proposed additive encoding must preserve all original DRW1 record
bytes/checksums, original sequence positions, 003 hash domains/type codes and old
record interpretations; old readers must reject unsupported extensions. It must
also define how the full certificate state is reconstructed from the WAL even though
the legacy `RoundState`/snapshot cache does not contain it. Rewriting old v1 records
or reinterpreting `FINALIZE_INPUT_FREEZE` is not permitted by this ADR.

Three counters/identities must stay distinct: original signer `Vote.durable_sequence`,
native transition-state bookkeeping, and physical `JournalEntry.sequence`. One
successful finalization consumes one new local WAL position, no vote position.
An exact replay consumes none. Existing votes retain their original policy digest
and sequence even when a later, independently derived policy generation is committed.

## 6. Crash behavior required at every boundary

This table specifies the transaction's acceptance contract. It is not a recovery
implementation or a proof of R3, and does not authorize general snapshot recovery work.

| Crash/failure point | Required recovery and visibility |
|---|---|
| Before/during validation; after candidate but before append | Old committed state; no final ISC, receipt or seed exposure; retry may attempt one transaction |
| During append, torn final record | No exposure. Reconcile the tail under existing durability/provenance rules. An authenticated trusted floor cannot be silently rolled back to discard it. Ambiguity blocks readiness |
| Complete append before barrier, or failed barrier | Do not assume the record is absent: complete bytes can survive. No success/effect on the failed call. Recovery verifies the actual durable prefix and source binding before deciding absence or replay |
| Barrier succeeded, before in-memory commit | Recover the complete original transaction, derive the same ISC and membership, restore its original sequence/receipt; do not append a replacement |
| During in-memory publication | Readers observe either old or complete new generation, never a partial index/collection/cache combination. On process failure, replay resolves from durable bytes |
| After commit, before receipt/effect return | Restore/reuse the original receipt/effect and sequence; caller timeout does not authorize another finalization |
| After copying/returning effect, before/after Java sends | Retransmission uses identical effect/ISC IDs. Transport delivery may repeat; no additional protocol vote or WAL append |
| Complete record corrupt or inconsistent with source/recomputed result | Fail closed before READY or exposure; no invented signers, repaired body or replacement QC |

A conflict is rejected before append. A device failure during an otherwise valid
append may leave a torn record; these are different cases and must not be conflated
into a false promise that failed I/O writes zero bytes.

## 7. Idempotency and conflicts

- Same original request ID and same canonical command/evidence: return the stored
  result before recomputing a quorum from later arrivals. Preserve exact certificate,
  vote frames, receipt, effect and original WAL sequence.
- Same request ID with different bytes: conflict, no append or state mutation.
- A request for a round already finalized to the same full body/context may return
  the original finalized object/receipt as an already-finalized result. Do not issue
  a new QC merely to include an additional signer or a different request nonce.
- A different full body/context for the same finalized round: fail closed before
  append. No partial policy installation or replacement of a finalized certificate.
- Process restart reconstructs both exact-request and finalized-round indexes from
  durable source transactions; a memory-only cache is insufficient.

The rejection result need not fabricate a durable `RejectConflictingISC` event.
If no protocol rejection record is committed, it projects as unchanged protocol
state with a local rejection, not as an invented public action. Existing modeled
rejection/replay collections cannot be silently populated or erased.

## 8. Seed release and Java boundary

Seed generation/reveal, EC and APC admission must resolve their parent against the
**committed durable ISC index**. A temporary candidate, a structural `verify_input_set`
success, an unbarriered WAL append or Java's receipt of quorum messages does not
open this gate. Finalization returns no seed material. Later seed work remains its
existing separate transition; no seed algorithm is redesigned here.

Java/Netty retains authentication/framing, bounded queues, opaque envelope transport,
backpressure and transmission of already returned native effects. It does not select
signers, compute the ISC root, choose a quorum, construct a certificate, mutate the
finalized index, or decide whether the barrier succeeded. It submits bounded bytes to
the dedicated native reactor; FFM/WAL work never runs on an event loop. Native keeps
no Java pointer after a downcall; bounded-copy paths have equal outputs.

## 9. File-level impact inventory — conditional, no edits authorized

The following is the bounded integration footprint identified so far. Existing paths
refer to PR50 or the candidate source pin; `NEW` entries are proposed file names,
**not files created by this ADR**. Since the root and durable capsule are not fixed,
this is not presented as a finalized coding checklist or a closed proof plan.

| Area | Exact files and intended role |
|---|---|
| Core producer | NEW `delta-core-cpp/include/delta/certificates/isc_producer.hpp`, NEW `delta-core-cpp/src/certificates/isc_producer.cpp`: pure received-cut validation, grouping, candidate/receipt plan. Reuse `delta-core-cpp/include/delta/core/consensus.hpp`, `delta-core-cpp/src/consensus.cpp`; no change to existing vote hash/context algorithms |
| Certificate bytes | `delta-core-cpp/include/delta/certificates/contracts.hpp`, `delta-core-cpp/src/certificates/contracts.cpp`, `delta-core-cpp/src/certificates/verifier.cpp`: preserve existing ISC bytes/ID and structural verifier. Any new root helper/binding is **not authorized**, pending §12 |
| Native integration | `delta-runtime-cpp/include/delta/runtime/runtime.hpp`, `delta-runtime-cpp/src/runtime.cpp`, `delta-runtime-cpp/include/delta/runtime/certificate_runtime.hpp`, `delta-runtime-cpp/src/certificate_runtime.cpp`: reactor operation, atomic full-state/index commit, seed guard, exact replay and policy generations |
| Durable bytes | `delta-runtime-cpp/src/wal.hpp`, `delta-runtime-cpp/src/wal.cpp`; NEW `delta-runtime-cpp/src/isc_finalize_codec.hpp`, NEW `delta-runtime-cpp/src/isc_finalize_codec.cpp`: complete transaction binding and decoder dispatch, once the additive format is approved. `delta-runtime-cpp/src/vote_codec.cpp` old DVPOL001/vote encodings must remain byte-identical |
| FFI | `delta-ffi/include/delta_abi.h`, `delta-ffi/src/certificates_abi.cpp`, `delta-ffi/src/delta_abi.cpp`: one bounded command/effect operation and version/capability checks; no fine-grained Java setters. `noexcept`, size/error behavior and replay receipts remain explicit |
| Schema/format | NEW `delta-protocol/schemas/008/isc-finalization-command-v1.json`, NEW `delta-protocol/schemas/008/isc-finalization-durability-v1.md`; `delta-protocol/schemas/003/delta-abi-v1.json` for an additive ABI capability only. Existing `008/input-set-certificate-v1.json`, `003/protocol-types-v1.json`, `003/hash-domains-v1.json`, `003/canonical-binary-v1.md`: identity/old-format compatibility baselines, **not permission to rewrite** |
| Sidecar | `delta-runtime-cpp/include/delta/runtime/sidecar_protocol.hpp`, `delta-runtime-cpp/src/sidecar_protocol.cpp`, `delta-runtime-cpp/src/sidecar_server.cpp`, `delta-node-java/src/main/java/io/deltareduce/node/sidecar/LocalSidecarClient.java`: transport dispatch for the bounded operation only |
| Java certificate adapter | `delta-node-java/src/main/java/io/deltareduce/node/certificates/AuthenticatedCertificateTransport.java`, `NativeCertificateVerifier.java` in the same directory: native sink/FFM wiring, not semantic logic |
| TLA refinement | NEW `formal/tla/refinement/IscProducerIntegration.tla` and `.cfg`: candidate/persist/commit/expose implementation phases projected to existing actions/stuttering. Existing `formal/tla/DeltaReduce.tla`, `DeltaReduceCertificates.tla`, `DeltaReduceQuorums.tla` remain unchanged |
| Lean targets | NEW `formal/proofs/DeltaReduce/NativeIscProducer.lean`, NEW `NativeIscFinalizeBytes.lean`, NEW `NativeIscFinalizeReplay.lean` in that directory; import registration in `formal/proofs/DeltaReduce.lean`. These would establish this producer/codec/retry contract, **not** complete R2.3 or R3 |
| Reused Lean results | `NativeInputSetBody.lean`; `NativeIscCertificate.lean` (`valueRead`, `checkedQuorum`, `checkedContext`, `checkedBody`, `bodyIgnoresSigners`, `bytesSource`); `NativeIscAdmission.lean` (`bindSource`, `prepareSource`); `NativeVoteBytes.lean`, `NativePolicyBytes.lean`, `NativePolicyCodec.lean`, `NativeWalBytes.lean`, `NativeWalScan.lean`, `NativeConfigReplay.lean`, `NativeReplayAdmission.lean` — all under `formal/proofs/DeltaReduce/`. Keep exact old statements; new transaction dispatch must not be claimed covered by old v1-only replay theorems |
| Trace/checker | NEW `formal/scripts/check_isc_producer.py`, NEW `formal/tests/test_isc_producer.py`; targeted integration with `formal/scripts/check-refinement.py` after the format is fixed. Preserve raw native evidence and source pins; no summary-only ACT-ISC-FINALIZE assertion |
| Core/runtime/ABI tests | NEW `delta-core-cpp/tests/isc_producer_test.cpp`, NEW `delta-runtime-cpp/tests/isc_finalize_test.cpp`; extend `delta-core-cpp/tests/consensus_test.cpp`, `delta-runtime-cpp/tests/native_exit_test.cpp`, `delta-runtime-cpp/tests/native_mutant_test.cpp`, `delta-runtime-cpp/tests/trace_exporter.cpp`, `delta-ffi/tests/certificates_abi_test.cpp` |
| Transport tests | `delta-node-java/src/test/java/io/deltareduce/node/certificates/CertificatesConformance.java`, `delta-node-java/src/test/java/io/deltareduce/node/NativeRuntimeFfmConformance.java`, `delta-node-java/src/test/java/io/deltareduce/node/sidecar/NativeSidecarConformance.java`; `delta-runtime-cpp/tests/sidecar_protocol_test.cpp` |
| Fixtures/build/evidence | NEW `delta-protocol/fixtures/008/isc-producer-v1.json`; NEW `specs/008-certificates-and-consensus/evidence/isc-producer-integration-v1.json`; `CMakeLists.txt`, `Makefile` for targeted registration. Existing 003/008 golden fixtures and prior evidence remain immutable comparison inputs |

A future exact root decision could change the proposed footprint; that must be
reported before coding, not silently absorbed into an open-ended task. No changes
to the frozen provenance profile or R1–R7 are authorized here.

## 10. Acceptance criteria and effect on evidence

Acceptance is blocked until the concrete root binding and complete durable transaction
format are approved. Thereafter the required outcomes are:

1. Original native envelopes and closed inputs produce the expected canonical ISC,
   with every signer justified by the complete delivered cut and all identities kept.
   Root validity is checked from source bytes, not a success flag or hash label.
2. A below-quorum/mixed-context/malformed/authentication-failed input cannot append
   a finalization; duplicates cannot increase quorum. Correct Byzantine multiplicity
   remains in source evidence, without renumbering or synthetic honest votes.
3. Exactly one committed certificate per round. Same request/restart retry returns
   original ISC/effect/sequence; conflicting finalization leaves the prior durable
   prefix and all committed collections unchanged.
4. At each §6 cut, no pre-barrier exposure and no lost/duplicated committed finalization.
   The actual complete-append/failed-barrier-survived case must be exercised; a fault
   hook that throws *before* append does not test this case. Root/receipt reconstruction
   must be compared to raw native execution, not fixture-created certificates.
5. Seed gate opens only on a committed durable ISC; candidate-only and structural
   verifier-only paths cannot release randomness or allow EC/APC.
6. New implementation phases refine the **unchanged** public actions and no-double-vote,
   context, quorum, input freeze and seed-order invariants. Existing raw bytes, vote/QC
   IDs, WAL prefix identities and signer sequences replay unchanged.
7. Native/FFM/sidecar paths agree on canonical results and fail-closed behavior;
   Java contains no quorum/finalization logic. Source-specific evidence names its
   exact source/semantics/profile and declared cryptographic/storage assumptions.

No existing proof/evidence is invalidated by this documentation-only change. A future
new handler cannot inherit source qualification from the old binary. Old v1 codec,
quorum and static certificate results remain proofs of their original statements;
old fixed-policy replay is not a theorem about generation updates. R2.1/R2.2 stay
CLOSED; R2.3/R2 stay OPEN; none of these local acceptance criteria closes R3.

Formal-first ordering remains mandatory: after a separate approval, specify/check the
affected refinement and compatibility obligations in feature 000; production code
still requires the exact compatible merged `FormalVerificationReport(GO)`. This ADR
is not that report. Any required change to production `Init/Next`, certificate
meaning, original QC/WAL IDs or the approved provenance profile is a fresh STOP.

## 11. Conditional active-time estimate

This is a preliminary estimate **after** the missing binding/storage decisions are
approved and necessary source authority is available. It is not an estimate to R2
closure, R3 closure or full Formal GO, and not permission to start.

| Work | Active hours |
|---|---:|
| Final byte/capsule contract and identity compatibility fixtures | 4–8 |
| Producer and transaction refinement/Lean obligations | 14–22 |
| Pure C++ builder, received-cut/context checks, reuse of existing contracts | 6–10 |
| Native atomic state/policy/WAL/receipt integration and targeted replay | 12–20 |
| Bounded FFM/sidecar/Java forwarding | 4–8 |
| Failure injection, actual traces, mutants and source-specific qualification | 10–16 |
| **Total conditional integration work** | **50–84** |

External review/merged authority waits and general provenance import/recovery are
excluded. The observed fixed-policy replay and coarse RoundState are the main cost;
this is not merely connecting a serializer to `VoteJournal`. Until §12 is resolved,
this interval must not be presented as a committed execution budget.

## 12. Separate architecture checkpoint: the missing root binding

**Existing obligation:** feature-008 FR-004/FR-005, not a new requirement.

**Source evidence:**

- PR50 `delta-core-cpp/src/consensus.cpp:690–710`: freeze produces references only.
- PR50 `delta-core-cpp/src/certificates/contracts.cpp:240–275`: `input_root` is checked
  as a content ID and serialized, without derivation from tuples.
- PR50 `delta-core-cpp/src/certificates/verifier.cpp:181–185`: context/signers/content
  ID only; unlike AggregateRoot's explicit Merkle check in `contracts.cpp:498–500`.
- `specs/008-certificates-and-consensus/scripts/certificate_contracts.py:451–475`:
  `cid(label)=SHA256(label)`; ISC fixture uses the constant label `input-root`.
- Existing `delta-core-cpp/src/shards/envelope.cpp:127–162` defines a Merkle tree over
  already identified leaves. It does not say which bytes/IDs constitute ISC leaves.
  `aggregate_merkle_root` is for a different certificate and leaf type.

Minimal **structural**, not production-reachability, witness: hold one valid context,
one ordered tuple and one valid signer set fixed. Substitute two distinct well-formed
`sha256:...` strings for `input_root`. Inspection of the verifier/encoder shows neither
is checked against that tuple; both receive canonical, different body/certificate IDs.
For a deterministic canonical Merkle construction over that same tuple array, both
cannot be the required root. No native execution or new proof is claimed by this
source-derived witness, and it does not label either historical fixture a demonstrated
production-reachable bad certificate.

The missing decision is exactly the ISC leaf preimage/domain and Merkle construction
binding (including odd-leaf handling), with an authoritative vector. The order and
source tuple fields already exist. The choices must not be guessed from AC IDs,
aggregate leaves, generic JSON hashing or the fixture's constant root. No algorithm
is selected here and no old signed body/root is recalculated or repaired.

This may be resolved by locating an already authoritative concrete contract or by an
explicitly approved concretization of FR-004 followed by the formal compatibility
gate. It is not evidence that a new certificate type, authority or public `Init/Next`
is necessary. Until resolved, a claim of a **fully specified production ISC transition**
would hide an unchecked certificate-semantic premise.

**STOP after this ADR/checkpoint.** No implementation, new proofs, R2.3/R3 continuation,
scope expansion, new authority, schema file or root rule was created.
