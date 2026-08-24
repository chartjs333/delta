# DeltaReduce v1 Formal Trace and Refinement Contract

## 1. Purpose

The formal model is useful only if later implementations can demonstrate that their externally visible behavior is an allowed formal behavior. This contract defines a stable event vocabulary and projection boundary.

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
```

Fields not relevant to an action use an explicit canonical absence value, never omission with ambiguous semantics.

## 3. Projection rules

- One externally visible certified state change maps to exactly one formal action.
- Internal parsing, buffering, retries, transport handshakes, metrics and cache operations may map to stuttering when they do not change abstract state.
- Duplicate/replayed messages map to `ReplayMessage` or stuttering and cannot create a second transition.
- Crash/restart events map to `Crash`, `Restart` and `RecoverJournal` with durability sequence evidence.
- Artifact repair maps to `RepairArtifact` only when content identity is unchanged.
- An implementation action with no formal counterpart is a semantic change and blocks merge until the formal baseline is amended.
- The projection MUST not hide a protocol-visible parent/body hash, vote, certificate, artifact availability or current-pointer change.

## 4. State abstraction

Concrete bytes/tensors are abstracted by canonical content IDs plus exact metadata/bound predicates. Concrete network connections are abstracted to message multiset and partition/delivery actions. Concrete clocks are abstracted to logical deadline transitions. Persistent stores are abstracted to durable maps/journals and atomic visibility.

The abstraction function MUST be deterministic and versioned. It may not map two protocol-distinct concrete states to one formal state when that would hide an invariant violation.

## 5. Refinement acceptance

A trace passes when:

1. its initial projected state satisfies formal `Init`;
2. each adjacent state pair satisfies an allowed formal action or documented stuttering relation;
3. every projected invariant holds;
4. terminal outcome matches `APPLIED`, `ABORTED` or allowed blocked state;
5. exact canonical byte/hash conformance tests separately validate concrete serialization/arithmetic.

Trace refinement does not replace implementation tests, cryptographic verification or performance/quality benchmarks.

## 6. Mandatory negative fixtures

The checker MUST reject traces containing:

- conflicting durable votes for one context;
- commitment replacement for one ticket;
- seed event without finalized ISC parent;
- ISC membership mutation;
- EC/APC adding a non-ISC ticket;
- parameter QC with another parent view;
- incomplete/duplicate AggregateRoot coverage;
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
