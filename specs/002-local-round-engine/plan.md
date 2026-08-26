# Implementation Plan: Локальный worker round и нормализованный contribution

**Branch**: `002-local-round-engine` | **Date**: 2026-08-26 | **Spec**: `spec.md`

## Summary

After independently verifying the merged feature-001 exit evidence and exact Formal GO, extend
the Python/PyTorch baseline with `LocalRoundEngine`. Runtime-neutral contracts define an immutable
`DomainPureWorkTicket`, terminal `LocalRoundCompletion` and complete-only
`NormalizedContributionCandidate`. The engine executes exactly the ticket data, `B` and `H`,
builds internal `LocalDelta = parent - final`, proves reconstruction under the worker-local FP32
contract and publishes `LocalDelta/A_j` only when `A_j=H`.

No package or production task begins before T000/HR002-001 passes. Feature 002 introduces no
quantization, validator state, global reduction, C++/Java production logic or P2P publication.

## Technical Context

- **Mandatory predecessor**: merge commit `7795d3209fb5e3093cc4450c4d49701137d4aab4`
  and independently verified feature-001 exit evidence.
- **Formal binding**:
  `sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.
- **Runtime**: Python 3.12 + PyTorch worker; reuse the locked feature-001 workspace.
- **Canonical contracts**: runtime-neutral JSON Schemas/fixtures under `delta-protocol` before
  Python orchestration.
- **Tensor formats**: safetensors; canonical FP32 order from `ParameterSchema`; no pickle.
- **State persistence**: atomic ticket claim, immutable completion/candidate refs and manifest-last
  filesystem publication.
- **Accounting**: `A_j` is committed optimizer updates; non-padding tokens/cursor commit at the same
  optimizer boundary.
- **Cancellation/faults**: injected monotonic clock, cancellation token and deterministic fault
  points.
- **Validation**: ticket bindings, exact tensor set/shape/schema, finite scan, reconstruction,
  `A_j=H`, per-tensor/global norm limits.
- **Concurrency**: one canonical claim/outcome per `ticket_id`; exact replay is idempotent and
  conflicting reuse fails closed.

## Pre-implementation Constitution Check

| Principle | Design response | Gate |
| --- | --- | --- |
| Scientific correctness | Direct reference, exact data range, `H`, optimizer-boundary token ledger and reconstruction are explicit | parity/accounting suite |
| Formal before code | T000/HR002-001 verifies merged 001 evidence, Formal GO and exact semantics before T001 | predecessor gate |
| Domain-pure fixed work | Ticket immutably binds domain/data/`B`/`H`/parent/schema/profiles; no adaptive mutation | contract/boundary tests |
| Integer consensus boundary | Feature emits normalized FP32 reference only; fixed-point/quantization remains feature 004 | architecture fixture gate |
| Reduce/distribution separation | Worker-local media cannot enter P2P/global distribution | architecture test |
| Safe boundaries | strict canonical schemas, safetensors, hash-before-use and no native/JVM dependency | validation/static gates |
| Explicit failure/recovery | incomplete paths publish terminal evidence and never an eligible candidate | failure/idempotency suite |
| WAN/observability/reversibility | structured ticket metrics, timeout-bounded injected faults, atomic outcome and rollback path | integration/exit gate |
| Replaceable interfaces | protocol schemas/bytes are independent of Python object layout and artifact backend | canonical fixture tests |

**Pre-implementation result**: PASS. T000/HR002-001 verified merge commit `7795d320`, all four
feature-001 exit evidence artifacts, the 13-schema/13-media protocol registry, the exact Formal GO,
two distinct human reviewers and all 24 semantic artifacts. The same formal semantics ID was
rederived with no new public action/failure/durability outcome. Canonical evidence is recorded in
`evidence/predecessor-gate.json`. Any later incompatible drift remains a STOP and cannot be waived
by Python tests.

## Architecture and data flow

```text
DomainPureWorkTicket + parent/data refs
                 │
                 ▼
        immutable binding validator
                 │
           atomic ticket claim
                 │
                 ▼
         LocalRoundEngine
      ┌──────────┴──────────┐
      ▼                     ▼
reused AdamW step core   committed token/data ledger
      │                     │
      └──── final state ─────┘
                 │
                 ▼
     LocalDelta = parent - final
                 │
       reconstruct/finite/norm checks
                 │
          require A_j = H
                 │
                 ▼
 NormalizedContributionCandidate = LocalDelta / A_j
                 │
                 ▼
 safe tensor publish → terminal completion → candidate manifest last
```

If any precondition or execution step is incomplete, the lower candidate branch is absent and the
engine publishes only `LocalRoundCompletion` with the stable terminal reason and observed counters.

## Project structure

```text
delta-protocol/
  schemas/
    domain-pure-work-ticket-v1.json
    local-round-completion-v1.json
    normalized-contribution-candidate-v1.json
  fixtures/local-round/

delta-worker-python/src/deltatorrent/
  domain/
    tickets.py
    parameters.py
    updates.py
    worker_state.py
  training/
    local_round.py
    token_accounting.py
  delta/
    schema.py
    builder.py
    reconstruction.py
    normalization.py
    validation.py
  worker/
    validation.py
    engine.py
    telemetry.py
    update_writer.py
    repository.py
  cli/worker.py

delta-worker-python/tests/
  unit/
  contract/
  integration/
  architecture/

configs/worker/smoke-ticket.json
docs/local-round-contract.md
specs/002-local-round-engine/evidence/
```

## Implementation sequence

0. Verify merged feature-001/Formal GO/protocol evidence and record T000/HR002-001.
1. Freeze canonical ticket, completion and normalized-candidate schemas/fixtures before Python
   orchestration.
2. Implement typed domain models, parameter schema and stable canonical fingerprints.
3. Add exact optimizer-boundary token/data ledger and reuse local AdamW without baseline drift.
4. Build internal `LocalDelta`, prove `final = parent - LocalDelta`, validate tensor/finite/norm
   conditions and normalize by `A_j` only after `A_j=H`.
5. Complete one deterministic vertical slice from ticket validation through recursive immutable
   bundle verification.
6. Add atomic claims, exact replay, conflict/concurrency and every incomplete terminal path.
7. Publish runtime-neutral positive/negative FP32 inputs for the later independent feature-004
   encoder; do not implement q-bytes.
8. Run final formal projection, cross-artifact, offline quality and Constitution gates.

## Test strategy

- **Prerequisite**: merged predecessor, missing/corrupt evidence, semantics/registry drift and
  non-refinement fail closed.
- **Contract**: strict schema, canonical bytes/hashes, immutable ticket fields, terminal/candidate
  exclusivity and backward-read policy.
- **Unit**: aliases/order, ledger boundaries, delta sign, reconstruction, normalization, finite and
  norm guards.
- **Integration**: direct parity, exact range/`H`, recursive bundle verification, exact retry,
  conflict/concurrency, deadline/cancel/OOM/data exhaustion/non-finite and crash points.
- **Architecture**: no native/JVM validator dependency; worker-local media rejected by distribution.
- **Platform**: CPU required; optional CUDA may test mixed-precision-to-FP32 conversion without a
  cross-platform bitwise claim.
- **Offline**: committed inputs only; public network blocked after dependency materialization.

## Observability

- canonical ticket claim and terminal completion records;
- optimizer/micro steps, `A_j`, non-padding tokens and exact cursor/range;
- loss, step time, measured peak memory and delta/candidate norm summaries;
- stable incomplete reason for cancellation, deadline, OOM, data exhaustion or non-finite state;
- candidate content IDs only for `COMPLETED` plus `A_j=H`.

## Rollout and rollback

The API is local/in-process and additive to the feature-001 baseline. Rollback removes worker
composition while retaining published schema IDs/fixtures so versions cannot be silently reused.
Temporary or staged candidate bytes remain non-eligible until the canonical candidate manifest is
atomically published. A formal incompatibility stops this branch instead of creating a local
exception.

## Risks and mitigations

- **Assignment/ticket ambiguity**: `DomainPureWorkTicket` is the sole protocol contract;
  application wrappers cannot redefine its fields.
- **Raw/normalized confusion**: distinct types/media/schema IDs and reconstruction/normalization
  tests enforce the boundary.
- **Partial eligibility**: `A_j=H` guard precedes candidate creation; terminal evidence is separate.
- **Token overcount**: ledger commits cursor/tokens only with optimizer update.
- **Tied parameter duplication**: canonical owner plus explicit alias table.
- **Race/replay**: atomic claim and immutable canonical input fingerprint/outcome.
- **Memory peak**: measure and document; streaming remains a later optimization.
- **Scope leak**: architecture tests prohibit distribution, native/JVM and accepted quantization.

## Exit gate

- T000–T031 and HR002-001–HR002-009 complete.
- Direct reference parity, exact ticket range/`H`, reconstruction and normalization tests pass.
- Incomplete paths have terminal evidence and no eligible candidate.
- Runtime-neutral bytes and feature-004 reference inputs are committed without q-byte acceptance.
- Formal compatibility, protocol conformance, offline Python quality and final Constitution Check
  pass with immutable evidence.
