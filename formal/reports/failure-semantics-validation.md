# Failure-semantics cross-branch validation

**Task**: T002  
**Result**: PASS — no unresolved quorum, timeout, close, repair or abort ambiguity remains  
**Formal semantics version**: `1.0.0`

## Authoritative inputs reviewed

Only the non-superseded feature refs named by `specs/ROADMAP.md` were used. The refs were inspected without importing implementation or specification artifacts into branch 000.

| Feature | Authoritative ref commit | Spec blob | Contract reviewed |
| --- | --- | --- | --- |
| 003 | `1032dd3a339d9014d7187ef2d0df8d99a23aefad` | `0a5ebbc066e903278969c461a36e8db7b7738835` | BFT round lifecycle, durable votes, quorum loss, input freeze and checked aggregation |
| 004 | `0ba1503abe0d280558d1818ddaa1551fea5bcf8f` | `e7e8c849958f158c93fc7e106a640f6b489b47ea` | fixed-point overflow, contribution loss/corruption and optional residual boundary |
| 005 | `cc764f3c220efc55a952796024002c0e01cb365c` | `e805fc2259ca5182b11f40a5ce2487a7bebac11e` | certified publication, piece loss/repair, restart and distribution blocking |
| 006 | `5ee3961389022c464183c44956f294698c042501` | `c327c6891ce17a25fbc4baf3b6fcc97603322f5f` | committee quorum loss/restart, exact topology and post-freeze region loss |
| 007 | `aed0e6cbd251162648a49cc40820ef5ee60c1d12` | `dd04ae8cc14ea8ea52a9ae81c4c4389f3096474d` | logical lease expiry, reassignment race, missing-ticket close/abort policy |
| 008 | `1d8109df660cb11b143f8f5ef92a29559fb5bb1f` | `1d896a3d1d71e6cb9859d7aaeee21c62271570db` | ISC/EC/APC lineage, shard/root/apply quorum, apply failure and pointer recovery |

Superseded refs `003-central-round-coordinator`, `007-adaptive-heterogeneous-scheduling` and `008-permissioned-trust-and-resilience` were excluded.

## Resolutions fixed before model coding

| ID | Ambiguity | Normative resolution | Affected formal IDs |
| --- | --- | --- | --- |
| SEM-RES-001 | A soft timeout was described as directly changing view, which would permit a single observation to mutate replicated state. | `SoftTimeout` records a durable context-bound timeout vote. `ViewChange` requires a `ViewChangeQC` of `2f+1` unique matching votes from the exact validator epoch. | `ACT-TIMEOUT-SOFT`, `ACT-VIEW-VOTE`, `ACT-VIEW-FINALIZE`, `INV-VIEW-CHANGE-CERTIFIED`, `PO-Q1`, `PO-Q2` |
| SEM-RES-002 | The prose promised a certified abort even when fewer than `2f+1` validators remained responsive. | The hard deadline disables all non-abort transitions and determines one canonical abort body. `ABORTED` requires an `AbortQC` with `2f+1` matching votes. Without that quorum the round is `BLOCKED`; if quorum later recovers, only that abort body may finalize. | `ACT-ABORT-VOTE`, `ACT-ABORT-FINALIZE`, `INV-ABORT-CERTIFIED`, `INV-ABORT-PRESERVES-PARENT`, `PO-Q1`, `PO-Q2`, `PO-R1` |
| SEM-RES-003 | “According to the frozen close policy” did not define the finite choices the model may execute. | `RoundConfig` selects `OMIT_UNAVAILABLE` or `ABORT_ON_INCOMPLETE` and binds exact required-ticket/domain predicates. Neither permits proposer discretion or arrival-order selection. | `ACT-INPUT-CLOSE`, `INV-AVAIL-BEFORE-ISC`, `INV-ISC-IMMUTABLE` |
| SEM-RES-004 | Repair was bounded but the identity of the budget and duplicate-response behavior were unstated. | Attempts are replicated counters keyed by exact content ID. Duplicate responses do not consume attempts; repair preserves content identity. Exhaustion enables only the canonical abort body. | `ACT-ARTIFACT-REPAIR`, `ACT-ABORT-VOTE`, `INV-ISC-IMMUTABLE`, `INV-RECOVERY-IDEMPOTENT` |
| SEM-RES-005 | Active-epoch compromise could be read as preserving formal safety after the Byzantine bound is exceeded. | Modeled compromise remains within the declared `f`-Byzantine bound. Evidence beyond the bound triggers operational emergency stop, but is explicitly outside the formal safety claim. | `FAULT-EPOCH-KEY-COMPROMISE`, report field `limitations` |

These resolutions clarify ADR-0000's existing “certified abort” and quorum requirements; they do not introduce a single-node timeout or abort authority.

## Cross-feature consistency result

| Feature | Failure/recovery paths checked | Result and abstraction boundary |
| --- | --- | --- |
| 003 | proposer crash/equivocation; validator crash before/after durable vote/send; insufficient quorum; AC shortfall; late input; arithmetic overflow; restart/replay | Consistent. The formal model uses the full certificate names while preserving feature-003's input-freeze and parameter-QC invariants. |
| 004 | unsafe configuration; runtime overflow; malformed/lost contribution; residual retry | Consistent. Overflow is modeled directly. Optional worker-local residual bookkeeping is outside the consensus state model and must refine to stuttering until its configured inclusion certificate changes durable worker-local state. |
| 005 | corrupt/missing pieces; seed loss; resumable restart; forbidden publication; certification downgrade | Consistent. Content loss/repair and publication policy are modeled; peer scheduling, backpressure and filesystem defenses remain concrete implementation obligations. `PIECE_UNAVAILABLE` cannot rewrite a certificate or current pointer. |
| 006 | regional/global proposer loss; committee quorum loss; conflicting partials; restart; post-freeze region loss | Consistent. Each committee uses its own valid `3f_c+1`/`2f_c+1` context; post-freeze membership is immutable and unrecoverable loss leads only to certified abort or blocking. |
| 007 | lease expiry/renewal/reassignment; old/new holder race; infeasible capacity; missing ticket/domain | Consistent. Lease time is logical/certified, reassignment is pre-commit only, and close behavior is one of the frozen policies. Capability measurement details are pre-round planning inputs, not failure-order authority. |
| 008 | missing seed transcript; EC/APC mismatch/overflow; mixed shard view; incomplete root; apply disagreement/quorum loss/overflow; crash around ApplyQC/current CAS | Consistent. Every retry preserves exact parentage; failed apply preserves the parent; an existing ApplyQC is replayed idempotently and can never authorize a different next state. |

## STOP assessment

- Unresolved quorum path: none.
- Unresolved timeout or view-change path: none.
- Unresolved input-close or repair path: none.
- Unresolved abort/current-pointer path: none.
- Contract imported from a superseded branch: none.

Model coding may begin after T000, T001 and T003 artifacts validate against these resolutions. Any later semantic change to these decisions reopens T002 and requires the affected formal gate to run again.
