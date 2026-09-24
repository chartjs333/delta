# DeltaReduce v1 Formal Trace and Refinement Contract

## 1. Purpose

The formal model is useful only if later implementations can demonstrate that their externally visible behavior is an allowed formal behavior. This contract defines a stable event vocabulary and projection boundary.

**Pending amendment 0001 — arithmetic witness**: `ACT-PARAM-VOTE` and
`ACT-APPLY-VOTE` must bind independently authenticated native pre-state, exact
canonical input bytes/IDs and the recomputed expected result. Current-state and
certificate parentage cannot come solely from the candidate command. Recovery
must reconstruct the same relation. The candidate public trace schema/checker
now incorporates a first-vote arithmetic witness as described below. This is
scoped candidate evidence and cannot close amendment 0001 or authorize runtime.

The required witness must describe the recovered current checkpoint at the vote
persist boundary, not only the checkpoint used to create a candidate. A first
PARAMETER/APPLY vote after current advances must fail admission when its parent
is stale. A replay of an already durable identical vote is distinguished from a
new append and retains its original receipt/sequence. The focused current-binding
TLC suffix covers this model rule before and after journal recovery; it is not
proof of complete arithmetic/recovery refinement.

### Candidate native witness boundary (T053/T054/T056)

Every event has `arithmetic_witness`, explicitly null where absent. Each accepted
PARAMETER/APPLY first vote requires `{snapshot_id, command_ascii}`. The command
is exact ASCII canonical draft JSON, with no whitespace, duplicate keys,
floating-point values or alternative encodings. Its complete expected body is
recomputed by the amendment oracle; its domain-separated hash must equal the
public event body hash. Other actions retain their existing projection rules.

The checker requires a separate `--native-evidence` file and independently
supplied `--native-evidence-sha256`. It never reads a trusted source path or hash
from the trace, nor synthesizes a native anchor from the command. Evidence uses
`{schema_version,snapshots,artifacts,operations}` at evidence version `1.2.0`. Snapshot IDs hash the canonical object
under `deltareduce.native-snapshot-witness.v1` plus NUL. The public trace schema
defines `nativeSnapshot`, `nativeAnchor` and `nativeArtifactRef`. Artifact values
are exact canonical ASCII strings indexed by the amendment draft content ID.
Bounds, kinds, byte lengths, IDs and graph edges are checked again on resolution.

The snapshot binds actor, action, prior state root, immutable round-contract ID,
vote context, native durable sequence, current checkpoint, recovered anchor,
authority reference and certificate-to-projection mapping. Context, role,
logical deadline, assignment coverage and current model/optimizer value hashes
are checked independently of the request. The parent certificate must already
be finalized in the trace. Newly accepted arithmetic votes cannot reuse an
observed sequence or occur after current advances in this single-round trace.

**Trust premise:** an actual exporter must authenticate the recovered snapshot
and certificate/projection mapping outside the request. A digest proves bytes,
not provenance, signatures, independent custody or durable recovery. The
checked-in `formal/fixtures/traces/native/manifest.json` is a test registry only.
`native_trace_fixture.py` constructs synthetic test snapshots; it is never called
by the verifier for a supplied trace. Rehashing the whole input graph still must
not override the separate current model/optimizer value hashes.

**Remaining scope:** native snapshot/observation production and authentication,
unbounded vector proofs, concrete tensor/adapter/frozen-base decoding, actual
native WAL/receipt serialization, initial journal snapshots, pre-admission
rejections and all physical crash cuts remain open. The draft journal projection
below checks first-persist and exact retry identities without claiming native
conformance. Four PO-AB1 proofs remain mandatory. Synthetic fixture success is
neither a qualifying Feature010 gate nor independent attestation.

### Candidate durable retry projection (T053/T054/T056)

Every event also has `durability_witness`, a nullable content ID of an observation
in the separately pinned native evidence `operations` map. An operation hashes
canonical ASCII JSON under `deltareduce.native-durability-observation.draft1`
plus NUL. It includes every public event field except the witness references,
the arithmetic snapshot ID and command bytes, sequence and journal roots before
and after, receipt/effect ASCII bytes (or explicit null), and ordered stages.
IDs and the whole evidence digest are independently checked, including when
an attacker recomputes all altered observation IDs.

This **diagnostic encoding is not a production C ABI, WAL or receipt format**.
Its canonical effect is `{projection_version:"draft1",vote:envelope}`. Its
receipt contains that version, envelope, original sequence, command ID and
effect ID, under the same canonical JSON and draft content-ID rules as the
arithmetic oracle. The envelope binds actor/action/round/height/epoch/formal
vote context, parent certificate hashes and body hash. Transport request IDs,
fresh observation time and leader view do not alter an already persisted
receipt; they remain bound in the observation. A new arithmetic vote still
undergoes every original native admission check before persistence.

The checker starts from an **empty per-actor journal**, tracks all accepted
vote kinds and requires each first append to consume exactly the next sequence.
Repeated envelopes cannot allocate another sequence. Ordered envelope content
IDs form a canonical JSON list hashed under
`deltareduce.vote-journal-projection.draft1` plus NUL. Before/after roots and
sequences must equal these reconstructed prefixes, not caller-selected values.
This is a projected durable-vote journal, not a claim that every physical WAL
record is a vote or that production WAL offsets equal this abstract sequence.

- First arithmetic persist with immediate output requires ordered stages
  `VALIDATED,APPENDED,DURABLE,COMMITTED,EXPOSED`, exact projected receipt/effect
  bytes and an admitted arithmetic witness. This refines
  `CanPersistVoteEnvelope` / `PersistVoteEnvelopeChanges` and
  `DurableSequenceExact` under the existing persist-before-expose contract.
- A persisted but unexposed first vote may instead stop at `DURABLE` or
  `COMMITTED`. Receipt/effect observations are null; the accepted event projects
  the internal durable action, not a returned command response. The original
  admitted command still determines the saved diagnostic receipt and sequence.
  The next observed action of that validator must be a successful crash; after
  restart and verified full-prefix recovery, only exact replay can expose it.
- For an unacknowledged complete append, stages may be
  `VALIDATED,APPENDED,SURVIVED_UNACKNOWLEDGED` or
  `VALIDATED,APPENDED,BARRIER_FAILED,SURVIVED_UNACKNOWLEDGED`. These are retrospective
  projections: a later verified recovery of that full prefix is mandatory before
  the trace can pass. The missing response or failed barrier alone establishes
  neither presence nor absence. No new protocol action, error or round outcome
  is introduced by these internal observation markers.
- Unexposed PARAMETER/APPLY votes provide no quorum power in the public checker.
  A validated exact `NO_OP` replay with `LOOKUP,EXPOSED` makes the original vote
  available for its matching QC once; repeated replays do not add signer power.
  Delivery and certificate authentication remain explicit abstraction premises.
- Identical canonical retry is `NO_OP`, with `LOOKUP,EXPOSED`, unchanged abstract
  state/journal/tip, original receipt/effect bytes and original receipt sequence.
  It resolves the prior admitted snapshot rather than re-admitting the old
  parent against the new current pointer. Neither a fresh request ID nor a
  changed current checkpoint permits a second append.
- Different canonical bytes in an already persisted actor/formal-context key
  require the existing `REJECTED` outcome, `LOOKUP,REJECTED`, unchanged state
  and journal, and no new receipt/effect/result/artifact. No new failure code or
  terminal is introduced. The next identical retry still resolves the old record.
- Successful journal recovery after an arithmetic persist requires
  `READ,VERIFIED,RECOVERED` and the unchanged complete projected prefix. Crash
  and restart preserve that durable prefix. Both first votes and retries remain
  disabled until successful recovery. `RecoverJournal` changes readiness. Conflict
  rejections stutter. A replay creates no new durable vote; the first exposure of
  an unsent recovered vote maps to `SendVoteEnvelope`. Subsequent identical output
  uses the existing replay/stuttering relation. The public state root covers
  replicated state, while the observation separately binds transport exposure.

The legal traces exercise retry before current advance and both PARAMETER/APPLY
retry after advance, crash/restart/recovery, an intervening conflict and another
successful identical retry. Negative traces separately mutate ordering,
receipt/effect bytes, prior/next journal prefixes, sequence, recovery readiness,
state stutter and canonical encoding. Three Python guard-removal counterchecks
admit the intended otherwise-consistent mutants; these are not TLA mutants.

Observation ordering is an authenticated-export **premise**, not proof of actual
fsync completion or write durability. No native exporter is supplied here.
Torn writes, unsuccessful barriers, persist-without-expose cuts, arbitrary
initial recovered snapshots and non-conflict first-admission failures still
need concrete refinement. This schema/checker checkpoint leaves TLA/Lean
transition and proof source bytes unchanged and does not discharge PO-AB1.

### Candidate coordinate projection (T053/T054/T056)

The hash-bound `parameter_schema` now includes `coordinates` and `ranges` in
addition to `parameter_ids`. `coordinates` is the exact sorted unique ASCII
sequence of scalar coordinate identifiers. Each range fixes one public parameter
obligation ID and its `(offset,length)` into that sequence. The parameter IDs in
this trace projection name domain/shard obligations; scalar coordinate IDs are
separate and shared across domains. Range rows follow parameter-ID order and
must cover exactly the immutable parameter-ID set.

Every assignment resolves its range through its parameter ID. All ranges must
be positive, within the vector, and use exact integer offsets/lengths. For each
domain, sorting its intervals must form one contiguous partition from zero to
the complete coordinate count: gaps, overlaps and observed-subset coverage fail.
Every `(domain,shard)` occurs once; the same shard ID denotes the same interval
in all domains, and the domain/shard product is complete. No observed vote or QC
is used to derive these requirements.

This determines one native SCHEMA payload: the exact coordinate sequence plus
shards sorted by ID with their bound offsets/lengths. Its canonical bytes must
equal the SCHEMA artifact resolved from the native authority graph. That graph
in turn binds model, optimizer and q-shard schemas. Rehashing either the public
contract or the entire native graph and recomputing all candidates cannot make
different coordinate projections equivalent.

This candidate profile supports canonical flattened vectors up to the existing
4096-item witness bound, with contiguous shared shard intervals. The new positive
fixture uses three domains, two shards of lengths 2 and 3, and five coordinates;
its expected model/optimizer values are checked against an independent literal
arithmetic derivation. Eleven new negative public traces cover range/order/gap/
overlap/domain alias/substitution errors. Three guard-removal counterchecks prove
that otherwise fully self-consistent substituted graphs become accepted when
only the explicit cross-boundary schema check is disabled in that test.

These are executable projection checks, not an arbitrary-vector theorem or native
tensor/QLoRA adapter conformance. The production TLC model remains one coordinate
per shard; PO-AB1 must connect the byte projection and full vector operation graph
to the model/proofs before the candidate can grant runtime authority.

## 2. Canonical trace event

Every protocol-relevant implementation event MUST project to a canonical record containing:

```text
schema_version
action_id
round_id
height
view
validator_epoch
actor_id
actor_role
request_id
vote_context_id
parent_hashes
body_hash
result_hash
prior_state_root
next_state_root
durable_sequence
logical_time
outcome
error_code
artifact_refs
arithmetic_witness
```

Fields not relevant to an action use an explicit canonical absence value, never omission with ambiguous semantics.

Every trace also contains one top-level immutable `round_contract`. It binds the
round ID, content-addressed RoundConfig projection, parameter-schema payload and
exact shard-plan assignments. Each assignment fixes
`(parameter_id, domain_id, shard_id, vote_context_id)`. The schema, plan,
RoundConfig projection and complete contract each carry independently recomputed
canonical SHA-256 IDs; an implementation cannot derive the required key set from
the parameter events that happened to appear in the trace.

## 3. Projection rules

- One externally visible certified state change maps to exactly one formal action.
- Internal parsing, buffering, retries, transport handshakes, metrics and cache operations may map to stuttering when they do not change abstract state.
- Duplicate/replayed messages map to `ReplayMessage` or stuttering and cannot create a second transition.
- Crash/restart events map to `Crash`, `Restart` and `RecoverJournal` with durability sequence evidence.
- Artifact repair maps to `RepairArtifact` only when content identity is unchanged.
- An implementation action with no formal counterpart is a semantic change and blocks merge until the formal baseline is amended.
- The projection MUST not hide a protocol-visible parent/body hash, vote, certificate, artifact availability or current-pointer change.

Existing model guards apply to fixture validation as follows:

- Matching QC votes must share action kind, round ID, height, validator epoch,
  exact vote context and body. A finalizer cannot relabel a collected quorum's
  height or epoch. These are necessary checks, not certificate authentication.
- Leader `view` is not a universal addition to the vote context. For example,
  `ConfigContext` binds height/epoch and its durable votes survive view changes.
  Action-specific parent/view bindings remain part of the canonical body/context.
- `CanVote` requires `READY`; both `CRASHED` and `RECOVERING` disable new votes.
  `ACT-CRASH` with `FAULT` records the crash; rejected/stuttering/no-op crash
  attempts do not. Only successful restart and journal recovery advance recovery
  state. A rejected, blocked, no-op, stuttering or failed recovery cannot enable
  votes, and successful recovery does not erase durable vote conflicts.

These checks enforce `RoundContexts`, `ConfigContext`, `CanVote`, `Restart` and
`RecoverJournal` already present in the TLA model. They do not establish the
pending arithmetic witness or a complete concrete-state abstraction.

## 4. State abstraction

The candidate `DeltaReducePersistenceHarness` decomposes one arithmetic vote into
internal admission/append/barrier/commit/exposure stages. Admission, append and
commit map to protocol stuttering; the complete durable record maps to the
production PARAMETER/APPLY vote action. Exposure maps to `SendVoteEnvelope` or an
exact already-sent replay. Crash, restart and verified recovery use the production
failure actions. An unacknowledged complete write may therefore have a durable
vote even though no result was returned; an absent write has none. Both must be
distinguished during recovery. Corrupt recovery stutters without becoming READY.

The harness receipt is a tuple of vote and sequence, not a byte format. It is
bounded to one validator, one injected fault, one coordinate/shard and a serialized
certified suffix with no concurrent current change. Deadlock checking permits
explicit stuttering only at DONE/BLOCKED; these are local harness stages, not new
protocol outcomes. This model does not by itself bind concrete native operations
or extend the public diagnostic receipt checker to physical crash-cut evidence.

Concrete bytes/tensors are abstracted by canonical content IDs plus exact metadata/bound predicates. Concrete network connections are abstracted to message multiset and partition/delivery actions. Concrete clocks are abstracted to logical deadline transitions. Persistent stores are abstracted to durable maps/journals and atomic visibility.

The abstraction function MUST be deterministic and versioned. It may not map two protocol-distinct concrete states to one formal state when that would hide an invariant violation.

## 5. Refinement acceptance

A trace passes when:

1. its initial projected state satisfies formal `Init`;
2. each adjacent state pair satisfies an allowed formal action or documented stuttering relation;
3. every projected invariant holds;
4. terminal outcome matches `APPLIED`, `ABORTED` or allowed blocked state;
5. every accepted ParameterQC belongs to the immutable RoundConfig/schema/shard
   plan matrix and AggregateRoot assembly contains exactly one result for every
   required matrix key, even when a required key has no preceding trace event;
6. exact canonical byte/hash conformance tests separately validate concrete serialization/arithmetic.

Trace refinement does not replace implementation tests, cryptographic verification or performance/quality benchmarks.

## 6. Mandatory negative fixtures

The checker MUST reject traces containing:

- conflicting durable votes for one context;
- commitment replacement for one ticket;
- seed event without finalized ISC parent;
- ISC membership mutation;
- EC/APC adding a non-ISC ticket;
- parameter QC with another parent view;
- incomplete/duplicate AggregateRoot coverage relative to the immutable
  RoundConfig/schema/shard-plan matrix, not merely the observed ParameterQCs;
- unchecked overflow/saturation event accepted as result;
- current pointer transition without ApplyQC;
- local/partial artifact publication;
- restart voting before journal recovery.
- finalized view change without a valid `ViewChangeQC` quorum;
- terminal `ABORTED` state without a valid `AbortQC` quorum;
- non-abort progress after the immutable hard deadline.

## 7. Feature ownership matrix

| Feature | Formal actions/invariants refined | Mandatory refinement evidence |
| --- | --- | --- |
| `001` | artifact atomicity and deterministic failure evidence only; no BFT transitions | Formal GO prerequisite and artifact-state trace vocabulary compatibility |
| `002` | local ticket completion boundary; `A_j=H` eligibility handoff | complete/incomplete ticket trace fixtures |
| `003` | config/ticket/commit/AC/freeze/seed/basic shard QC/view/abort/recovery | full model-to-code trace suite and four-validator behaviors |
| `004` | fixed-point profile/bounds/q-shard validity | theorem-precondition and overflow trace evidence |
| `005` | certified publication, piece loss/repair, plane separation | distribution action refinement and forbidden-media negatives |
| `006` | regional/global parameter actions and exact partition | hierarchy theorem instantiation plus trace equality |
| `007` | deterministic plan/lease/expire/reassign/commit race | lease-state refinement and ticket immutability |
| `008` | ISC/EC/APC/shard/AggregateRoot/Apply/current chain | complete certificate/apply refinement and Frankenstein negatives |
| `009` | same chain over adapter schema with frozen base | mode/schema abstraction and no-base-mutation traces |
| `010` | no new protocol action; replays/attacks/evidence | regression of all formal gates at benchmark identity |
| `011` | deployment/recovery/epoch/stop actions without semantic change | real trace sampling/full verification according to PilotDefinition |

## 8. Compatibility

`FormalVerificationReport` publishes a `formal_semantics_id` derived from the complete sorted set of non-mutant TLA module hashes, mandatory Lean source hashes and the public trace-schema hash. The domain-separated canonical derivation is frozen in `formal/schemas/README.md` and independently implemented by `formal/scripts/formal_artifacts.py`. Every later feature report/run/pilot definition MUST bind a compatible ID. Any semantic change invalidates compatibility until a new formal report obtains GO. T057 publishes the first concrete ID only after the complete model, proof and trace artifact set exists.
