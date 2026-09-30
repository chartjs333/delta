# ADR-0014 — ISC Producer Integration v1

**Status: integration DRAFT; I-B/S-RANK APPROVED; W1 APPROVED as a local byte/storage contract.
Not approved for implementation.**

30 September 2026 documentary amendment: the FR-004 commitment profile and the
[I-B/S-RANK decisions](0014-isc-identity-sequence-amendment.md) are approved.
The [WAL Capsule](0014-isc-finalization-wal-capsule-v1.md) now incorporates these
rules and is now approved as a local byte/storage contract. This does not approve
production integration or establish the three remaining gates. No code,
schema, proof, production fixture or R2.3/R3 work is authorized.

30 September 2026. Existing tasks: feature-008 T016, HR008-002/003/015/018;
feature-000 T053. Documentation only; R2.3 and R3 remain stopped.

Source base: `ce63d3eca0175b5b82726a1994402dc14d3be1b5`.
Native source reference: `60c692f6e391f839829dfc64e93380db54cd507b` (PR50).
The latter is an inspected implementation reference, **not** a merged formal authority.
Exact inspected blobs are recorded in
[the historical source inventory](evidence/0014-isc-producer-integration-source-audit.json).
Its report hash records the pre-amendment document; this amendment has its own Git commit.

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

**The original FR-004 byte-contract gap is resolved at the specification level** by
[ISC Commitment Profile v1, A](0014-isc-commitment-profile-v1.md). This does not mean
`InputLedger::freeze` or `verify_input_set` already implements that check. The original
native source observations in §12 remain historical evidence, not new qualification.

The normative integration identities are now I-B/S-RANK. All changed parent-reference
meanings apply only to a future independently pinned, qualified semantics version
`σ_next` (notation, not a newly assigned version/hash or wire field). Existing
accepted/candidate semantics IDs are not authority for this change. Explicit parent/context completeness and source/bounds qualification remain open
after local W1 approval.
No new parent field or alternative provenance mechanism is introduced.

### Normative terminology and compatibility boundary

| Symbol | Meaning and use in σ_next |
|---|---|
| `B`, `b` | Full `VoteInputSetBody`; `b=vote_input_set_body_id(B)` is the **consensus body identity** in seed/assignment, every downstream ISC parent-reference, logical finalized index and semantic replay |
| `C`, `c` | Original typed ISC witness; `c=content_id(C)` is its **certificate artifact identity**, including original signers. Witness bytes, signatures and source lineage are retained; different c values may certify the same b |
| `s` | Original **physical WAL slot**, including kinds 1/2/3. Native signed Vote.durable_sequence and native receipt sequence retain s |
| `V_a(s)` | **Public vote ordinal/count** = number of original actor-a kind-2 records in the verified prefix through s. At a vote slot it is that vote's public ordinal; kinds 1/3 do not increment it |

Finalized lookup is `(round context)→b`; artifact lookup is `c→exact C`; semantic
replay is `(round context,b)→original result/C/c/s`. A common b is not permission
to merge witness bytes/identities or erase votes. Native `input_set_certificate_id`
in seed/EC/APC/PARAMETER/ROOT changes from historical c to b **only in σ_next**;
IFR1 and publish-artifact references remain c. Typed source resolution enforces each
role; digest string grammar cannot distinguish them. Full-context comparison remains
mandatory; none of these IDs supplies authority without the admitted source/quorum.

This is an approved native certificate-reference semantic change. It changes new
downstream signed bodies/QC IDs; no old object, signature, QC, WAL or receipt is
migrated, resigned, repaired or relabelled. No old history is made σ_next-compatible
by changing its references. Current production Init/Next is already body-based and
vote-count-based; no change to it is selected. Qualification of the concrete relation
is still required. Coarse RoundState.durable_sequence is a separate command counter.

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
| Closed body | Existing `VoteInputSetBody`: full `Context`, `input_root`, `tuples`. Its content ID is `vote_input_set_body_id`. It is already a closed proposal, not a caller-created alternate input set. Root-to-tuple verification MUST use approved Commitment Profile A; current helpers alone do not establish it |
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
   precisely original C in the witness collection and b in finalized membership of
   the same σ_next generation. Preserve other retained C variants and their c IDs;
   already-finalized b is replay, not another insertion/finalization. No deletion of
   downstream lineage, historical re-keying or coordinate-level objects. Return an internal candidate,
   not externally sendable bytes.

`ISCBuilder/QC` names the existing feature-008 plan node. No such complete producer
was found in code; its future implementation must perform these steps.
`as_input_certificate(body, policy)` currently inserts **all configured validators**
for proposal validation; it must not be reused as the actual quorum builder.

The same body and the same received cut produce identical bytes. Different legal
cuts may have different signer sets and therefore different existing QC IDs.
This ADR does not add a new global minimum-quorum-selection rule or promise identical
QC bytes across unequal signer cuts. Each cut produces the same consensus b for
that B, even with different c. Finalization/retry preserve the first locally committed
C/c/receipt; another valid witness is not a conflicting body and does not create a
second finalization. No globally unique signer witness is required for seed/ISC-parent
identity. This removes the ISC-witness-induced context split, not all liveness obligations.

## 4. Canonical identity and helper reuse

For an existing typed ISC C:

```text
c = content_id(C) = "sha256:" + lowerhex(SHA256(
  ASCII("deltareduce.008.input-set-certificate.v1") || 00 || canonical_json(C)))
```

Keep the existing field order, versions, context, ordered tuples and sorted unique
`signer_ids`. The consensus body ID b (`deltareduce.vote.input-set-body.v1`) is different;
it excludes quorum-only signer/threshold data. b is the ISC parent, c is the witness
artifact. Neither is the generic type-004 QC envelope's content ID. Do not alias
these identities or use c as a fallback when b lookup fails. For identical full
C bytes, the old content-ID formula still gives the same c; a changed semantics
context changes bytes and resulting IDs.

Original Vote IDs use the existing type-003 vote domain over the original complete
canonical envelope. Association with typed ISC is retained as native evidence,
without inserting vote IDs, new signatures or a new certificate type into ISC bytes.
All old vote/QC bytes and their hashes remain unchanged under their original
profile. This preservation is not interoperability: new σ_next parent references,
semantics-tagged signed payloads and dependent QC IDs differ. Original envelope
bytes are never regenerated under σ_next merely to match its parent terminology.

| Existing helper | Reuse; limit of its current guarantee |
|---|---|
| `InputLedger::freeze` | Existing ordered references, stable repeated freeze; lacks ISC root production and quorum assembly |
| `VoteJournal::record` | Local original vote uniqueness/replay; not a delivered-vote collector or signature verifier |
| `validate_quorum` | Existing threshold, canonical signer membership and supplied vote-ID cardinality checks; not a received-vote assembler |
| `ChainVerifier::verify_input_set` | Existing context/signer/encoding back-check; no Merkle derivation or producer proof |
| `canonical_json` / `content_id` | Exact witness C/c encoding; consensus b separately uses vote_input_set_body_id. Preserve old objects; no struct serialization or signing-byte reconstruction |
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
   ISC bytes/c plus the b binding, next consensus membership and exact effect/receipt. A hash without
   recoverable bytes is insufficient. No parallel ISC authority journal.
3. **Barrier:** complete the existing fsync/durability and directory-binding checks.
   Until successful, no sendable ISC/seed effect or success receipt escapes.
4. **Commit:** atomically install C/c witness collection, round→b index and immutable source-policy
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

The separately proposed W1 capsule uses additive **kind 3** and four typed sections
in the existing DRW1 frame. It is approved as a local byte/storage contract; approved I-B/S-RANK
are now normative within it. Original kinds 1/2, frame checksum algorithm and source
positions are not rewritten. The layout's reuse does not reuse old c-based policy
semantics: P0/P1 must already belong to independently selected σ_next. Old readers
reject unsupported kind/profile; no reinterpretation of FINALIZE_INPUT_FREEZE or
automatic import/relabel of legacy policy is allowed. Full state/index/cache must be
reconstructed from verified retained prefix/capsules, not the coarse legacy snapshot.

For a verified complete actor-a journal, physical p=length(L_a), and:

```text
V_a(s) = count(original kind-2 entries through physical slot s)
public durableSequence[a] = V_a(p)
native signed Vote.durable_sequence at a vote slot s = s
s = V_a(s) + count(kind 1 through s) + count(kind 3 through s)
```

A finalization increments p only. A new vote increments p and V; exact replay
increments neither and returns the original physical s and witness c. Remote
vote envelopes retained in a capsule are not new local votes. The public projection
must preserve all original votes injectively; collapsing them and counting a set
is rejected. Verify each kind-3 frame before excluding it from the vote count;
`kind != 1` is not a valid vote classifier. Counts across checkpoint boundaries come
from verified complete history, not caller metadata or a reset. Native policy digests
and signed sequences are retained. The normative positive/negative mixed-WAL controls
are in [WAL Capsule §10](0014-isc-finalization-wal-capsule-v1.md#нормативные-documentary-vectors-i-b--s-rank).

## 6. Crash behavior required at every boundary

This table specifies the transaction's acceptance contract. It is not a recovery
implementation or a proof of R3, and does not authorize general snapshot recovery work.

| Crash/failure point | Required recovery and visibility |
|---|---|
| Before/during validation; after candidate but before append | Old committed state; no final ISC, receipt or seed exposure; retry may attempt one transaction |
| During append, torn final record | No exposure or automatic tail repair/truncation. Required prefix ambiguity blocks READY under the approved profile; no rollback of trusted floor or skipping kind 3 |
| Complete append before barrier, or failed barrier | Do not assume the record is absent: complete bytes can survive. No success/effect on the failed call. Recovery verifies the actual durable prefix and source binding before deciding absence or replay |
| Barrier succeeded, before in-memory commit | Recover the original C/c, b membership and physical s/receipt once; kind 3 does not increase V. No replacement append |
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

For the same full B/context, a different valid C/c is an alternate witness, not a
body conflict. It cannot replace the original receipt c, create another physical s,
or change seed/assignment identity. Witness lookup preserves original C/c and source
multiplicity. Recovery reconstructs round→b and c→C bindings together with the
original result index. Public vote count is recomputed from all original kind-2
entries, never from witness/signature count.

The rejection result need not fabricate a durable `RejectConflictingISC` event.
If no protocol rejection record is committed, it projects as unchanged protocol
state with a local rejection, not as an invented public action. Existing modeled
rejection/replay collections cannot be silently populated or erased.

## 8. Seed release and Java boundary

Seed generation/reveal, EC and APC admission must resolve their parent against the
**committed durable round→b index**, backed by a verified witness C with that B.
The seed/assignment consensus identity is independent of the selected c/signers;
all downstream ISC parent references use b. A temporary candidate, a structural `verify_input_set`
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
**not files created by this ADR**. The root and I-B/S-RANK decisions are approved,
and W1 is approved as a local byte/storage contract. This is still a conditional impact inventory,
not a finalized coding checklist, new proof layer or closed R2/R3 proof plan.

| Area | Exact files and intended role |
|---|---|
| Core producer | NEW `delta-core-cpp/include/delta/certificates/isc_producer.hpp`, NEW `delta-core-cpp/src/certificates/isc_producer.cpp`: pure received-cut validation, grouping, candidate/receipt plan. Reuse `delta-core-cpp/include/delta/core/consensus.hpp`, `delta-core-cpp/src/consensus.cpp`; reuse hash domains/algorithms; σ_next ISC references/derived context inputs use b, so downstream IDs change |
| Certificate bytes | `delta-core-cpp/include/delta/certificates/contracts.hpp`, `delta-core-cpp/src/certificates/contracts.cpp`, `delta-core-cpp/src/certificates/verifier.cpp`: preserve historical ISC bytes/c and hash formulas; future approved A root check and σ_next b-parent lookup need qualification. `delta-core-cpp/src/certificates/vote_admission.cpp` and `src/robust/plan.cpp` references also require semantic dispatch; no implementation authorized |
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

Future W1 qualification beyond these approved I-B/S-RANK amendments must be reported
before coding, not silently absorbed into an open-ended task. No changes
to the frozen provenance profile or R1–R7 are authorized here.

## 10. Acceptance criteria and effect on evidence

Commitment A, I-B/S-RANK and local W1 are approved. Acceptance still requires
the three remaining gates and separately authorized qualification/implementation; the following outcomes are not
claimed achieved by this documentary amendment:

1. Original native envelopes and closed inputs produce the expected canonical ISC,
   with every signer justified by the complete delivered cut, b used as consensus identity and original c/vote identities retained.
   Root validity is checked from source bytes, not a success flag or hash label.
2. A below-quorum/mixed-context/malformed/authentication-failed input cannot append
   a finalization; duplicates cannot increase quorum. Correct Byzantine multiplicity
   remains in source evidence, without renumbering or synthetic honest votes.
3. Exactly one finalized consensus B/b per round context; distinct valid C/c witnesses
   for B are not new consensus values. Same request/restart retry returns original
   C/c/effect/physical s; conflicting B finalization leaves the prior durable
   prefix and all committed collections unchanged.
4. At each §6 cut, no pre-barrier exposure and no lost/duplicated committed finalization.
   The actual complete-append/failed-barrier-survived case must be exercised; a fault
   hook that throws *before* append does not test this case. Root/receipt reconstruction
   must be compared to raw native execution, not fixture-created certificates.
5. Seed gate opens only on a committed durable ISC; candidate-only and structural
   verifier-only paths cannot release randomness or allow EC/APC.
6. New implementation phases refine the **unchanged** public actions and no-double-vote,
   context, quorum, input freeze and seed-order invariants. Existing raw bytes, vote/QC
   IDs, WAL prefix identities and signer sequences replay under their original profile;
   they are not imported by relabel into σ_next. Mixed 1→2→3→2 projects to counts
   0→1→1→2; original vote slots remain 2 and 4. Role substitutions and vote collapse
   must fail as specified by the documentary vectors in WAL Capsule §10.
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
meaning beyond approved I-B, original QC/WAL identities or the approved provenance
profile is a fresh STOP. I-B authorizes future c→b reference semantics, not changing
already-existing objects. The requalification inventory in the identity/sequence memo
includes old parent.qcId proofs, mixed-WAL position/count proofs and full source loaders;
none is silently treated as a theorem about σ_next/kind 3.

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
this is not merely connecting a serializer to `VoteJournal`. The historical 50–84h
interval is **not approved or re-estimated** by the documentary
amendment and must not be presented as a committed execution budget.

## 12. Historical checkpoint and current STOP

The original source audit found that InputLedger::freeze returned references,
verify_input_set checked structural/context/signer validity, and the fixture used
`cid("input-root")`. Those observations concern the pinned old source, not the
current specification. Approved Commitment A now supplies the missing leaf/order/tree
byte contract for FR-004; no native implementation or existing fixture was changed.

Approved I-B supplies the common ISC consensus b while retaining witness c.
Approved S-RANK supplies physical-slot/public-vote-count terminology and mapping.
The corresponding negative vectors are normative documentary expectations for the
future semantics closure, not generated production fixtures or passing tests.

W1 is approved as a local byte/storage contract. Explicit parent/context completeness, independent
source authority and full-domain/bounds compatibility remain unqualified; no extra
fields, alternate provenance profile or old-history migration is selected here.
No new semantics version/hash is assigned by this ADR. Integration and the old
50–84h estimate remain unapproved for execution.

**STOP after this documentary amendment.** No code, schemas, proofs, R2.3/R3,
production recovery or further implementation work until a new explicit instruction
and the applicable exact compatible merged Formal GO gate.
