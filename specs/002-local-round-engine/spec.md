# Feature Specification: Локальный worker round и нормализованный contribution

**Feature Branch**: `002-local-round-engine`

**Created**: 2026-08-21

**Last amended**: 2026-08-26

**Status**: Phase 0 PASS — T001 may begin

**Depends on**: merged `001-reproducible-training-baseline`

## Formal and predecessor prerequisite

Before T001 or production code, this branch MUST independently verify the merged feature-001 exit
evidence, protocol registry, exact feature-000 Formal GO and
`sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.
Any missing evidence, altered formal artifact, new public action/failure/durability outcome or
non-`REFINEMENT_ONLY` impact is an unconditional STOP and returns to feature 000/001 as owned.

## Summary

Каждый Python/PyTorch worker получает один immutable `DomainPureWorkTicket`, загружает точную
родительскую модель и data range, выполняет ровно фиксированные `B` и `H` без межмашинной
синхронизации и формирует worker-local вклад. Тикет фиксирует domain, parent, parameter schema,
optimizer и arithmetic profiles; его значения не адаптируются по скорости, памяти или времени
завершения worker.

Два артефакта имеют разные роли:

- `LocalDelta = parent - final` — внутренний FP32 reconstruction/reference artifact;
- `NormalizedContributionCandidate = LocalDelta / A_j` — единственный потенциально
  commit-eligible worker output, причём публикация разрешена только при `A_j = H`.

При `A_j != H`, OOM, cancellation, data exhaustion, deadline или non-finite state eligible
candidate отсутствует; публикуется только immutable terminal `LocalRoundCompletion` evidence.
Feature 002 не выполняет quantization, consensus acceptance, global reduce или P2P distribution.

## User Scenarios & Testing

### US1 — Выполнить один фиксированный domain-pure ticket (Priority: P1)

Worker получает `DomainPureWorkTicket`, проверяет его parent/data/schema/profile bindings и
выполняет локальный AdamW до точной optimizer boundary `H`.

**Independent Test**: на fixture model/data ticket local engine выдаёт тот же final state,
processed range, optimizer steps и non-padding token count, что direct single-process reference.

**Acceptance Scenarios**:

1. **Given** валидный ticket и доступные immutable inputs, **When** worker выполняет его,
   **Then** lifecycle проходит `ACCEPTED → RUNNING → COMPLETED`, `A_j=H`, а completion evidence
   и normalized candidate публикуются manifest-last.
2. **Given** fixed `H`, **When** gradient accumulation используется, **Then** ровно `H`
   optimizer updates считаются effective steps; microsteps не увеличивают `A_j`.
3. **Given** deadline, cancellation, OOM или data exhaustion до `H`, **When** execution
   завершается, **Then** terminal evidence содержит фактические counters/reason, а eligible
   candidate не существует.

### US2 — Проверить reconstruction и normalization (Priority: P1)

Ревьюер восстанавливает финальные worker weights из parent и внутреннего `LocalDelta`, а затем
проверяет, что published contribution равен `LocalDelta / A_j` при `A_j=H`.

**Independent Test**: для каждого canonical tensor выполняются
`final = parent - LocalDelta` и `candidate = LocalDelta / H` в заявленном worker-local FP32
contract/tolerance.

**Acceptance Scenarios**:

1. **Given** parent `θ_t` и final `θ_{j,H}`, **When** строится `LocalDelta`, **Then** используется
   только соглашение `θ_t - θ_{j,H}`.
2. **Given** complete execution, **When** строится candidate, **Then** metadata связывает exact
   ticket/domain/parent/schema/profile, `A_j=H` и normalized safe-tensor content ID.
3. **Given** wrong schema, tensor set/shape, non-finite value, unsafe norm или `A_j != H`,
   **When** output валидируется, **Then** candidate отвергается до commit point.

### US3 — Безопасно повторить, конкурировать или прервать ticket (Priority: P2)

Оператор повторно отправляет тот же ticket либо worker останавливается до publication.

**Independent Test**: exact retry возвращает тот же immutable result; conflicting reuse и
concurrent claim отвергаются; каждый incomplete path оставляет terminal evidence без candidate.

**Acceptance Scenarios**:

1. **Given** завершённый ticket, **When** повторён exact canonical input fingerprint, **Then**
   worker возвращает существующие refs без повторного training/publication.
2. **Given** тот же `ticket_id` с другим parent/data/schema/profile/deadline, **When** он принят,
   **Then** stable idempotency conflict не меняет существующий результат.
3. **Given** crash/cancellation до или после tensor candidate staging, **When** recovery
   выполняется, **Then** partial bytes не становятся eligible, а manifest-last outcome
   идемпотентен.

## Edge Cases

- Dataset заканчивается до `H` или range не соответствует ticket.
- Batch содержит только padding tokens.
- Gradient accumulation прерывается до optimizer boundary.
- Parent содержит buffers, frozen или tied parameters.
- Параметр не получил gradient.
- Mixed-precision local training требует canonical FP32 reference output.
- Crash между tensor publication и completion/candidate manifest.
- Conflicting reuse отличается только deadline или profile.
- Cancellation конкурирует с final atomic commit.
- OOM, слишком большой norm или NaN/Inf loss/gradient/parameter/candidate.
- `H=0`, `B=0`, `A_j<H`, `A_j>H` или mutation ticket после claim.

## Requirements

### Functional Requirements

- **FR-000**: Before T001, the branch MUST verify the exact merged feature-001 exit evidence,
  protocol registry, Formal GO and formal semantics ID and persist content-addressed Phase-0
  evidence.
- **FR-001**: `DomainPureWorkTicket` MUST be versioned and immutable and bind `ticket_id`,
  `domain_id`, immutable data range, `B`, `H`, parent model, parameter schema, optimizer profile,
  arithmetic profile and deterministic seed material.
- **FR-002**: Worker MUST verify every referenced artifact hash/schema and every ticket binding
  before allocating training resources; post-claim mutation MUST fail closed.
- **FR-003**: One local/effective step MUST mean one successful optimizer update. Microbatch and
  backward operations are separate counters, and `A_j` is the committed optimizer-step count.
- **FR-004**: Worker MUST reuse feature-001 local AdamW/reproducibility/checkpoint primitives
  without changing baseline semantics.
- **FR-005**: Token/data accounting MUST commit only at successful optimizer boundaries and record
  non-padding tokens and exact ticket cursor/range. Partial accumulation MUST NOT enter counters.
- **FR-006**: Complete eligibility MUST require `A_j=H` and exact fixed ticket inputs. Deadline,
  cancellation, OOM, data exhaustion and non-finite state are terminal incomplete outcomes.
- **FR-007**: Worker MUST compute internal `LocalDelta = θ_parent - θ_local_final` over canonical
  ordered FP32 tensors.
- **FR-008**: The only commit-eligible worker output MUST be
  `NormalizedContributionCandidate = LocalDelta / A_j`, with `A_j=H` explicitly bound in
  canonical metadata.
- **FR-009**: Parameter schema MUST include ordered names, shapes, logical dtypes, trainable flags,
  omission policy and tied-parameter aliases with a stable fingerprint.
- **FR-010**: `LocalRoundCompletion` MUST record ticket/domain/worker IDs, exact input bindings,
  actual optimizer/micro steps, processed non-padding tokens, cursor/range, terminal reason,
  numerical/resource summaries and producer version.
- **FR-011**: Complete candidate metadata MUST reference parent/schema/ticket/completion and safe
  normalized tensor artifacts by media/schema version, byte length and SHA-256.
- **FR-012**: Tensor payloads MUST use safetensors and MUST NOT use pickle or Python memory-layout
  serialization.
- **FR-013**: Worker MUST validate exact tensor set/shapes, finite values and configured norm
  ceiling before candidate publication.
- **FR-014**: Execution MUST be idempotent by `ticket_id` plus canonical input fingerprint; exact
  replay returns the original outcome, conflicting reuse returns a stable error.
- **FR-015**: Cancellation/deadline MUST be checked at least at each microbatch boundary and MUST
  publish no eligible partial candidate.
- **FR-016**: Artifact publication MUST be atomic and manifest-last. Candidate eligibility exists
  only after the complete candidate manifest is durable.
- **FR-017**: Local round API MUST be transport-independent. CLI/in-process adapters MAY invoke it,
  but network/native/JVM validator behavior MUST NOT enter the domain layer.
- **FR-018**: Worker MUST emit structured lifecycle/step/resource metrics and terminal evidence
  bound to ticket/domain IDs.
- **FR-019**: Worker-local media types MUST be rejected by any distribution/P2P global-object
  interface.
- **FR-020**: Feature 002 fixtures MAY expose normalized FP32 inputs for independent feature-004
  encoders but MUST NOT define accepted INT16 q-bytes or consensus quantization.

### Non-Functional Requirements

- **NFR-001**: Required CPU fixture MUST finish within 10 minutes on a typical 4-core CI runner.
- **NFR-002**: Delta creation SHOULD use at most one documented extra full FP32 model copy;
  measured memory is evidence, not a hard-coded claim.
- **NFR-003**: Cancellation/failure paths MUST be timeout-bounded and testable with injected clock,
  cancellation and fault points.
- **NFR-004**: Domain contracts MUST not depend on gRPC, HTTP, native/JVM APIs or a concrete
  artifact backend.
- **NFR-005**: Numerical comparisons MUST use explicit per-dtype/per-operation worker-local
  tolerances; consensus-level exactness is not claimed here.
- **NFR-006**: Worker MUST NOT claim remote-compute honesty; evidence records observed execution,
  not cryptographic proof of correct training.

### Key Entities

- **DomainPureWorkTicket**: immutable domain/data/`B`/`H`/parent/schema/profile contract.
- **ParameterSchema**: canonical parameter ordering, shape/dtype/trainability/alias contract.
- **LocalRoundState**: `RECEIVED/ACCEPTED/RUNNING/COMPLETED/FAILED/CANCELLED` lifecycle.
- **TokenAccountingRecord**: optimizer-boundary `A_j`, non-padding tokens and data cursor ledger.
- **LocalDelta**: internal ordered FP32 `parent - final` reconstruction artifact.
- **LocalRoundCompletion**: immutable complete or incomplete terminal execution evidence.
- **NormalizedContributionCandidate**: complete-only FP32 `LocalDelta/A_j` worker output.

## Success Criteria

- **SC-001**: Engine matches direct reference by final weights, exact ticket data, `H` steps and
  token ledger on the deterministic CPU fixture.
- **SC-002**: Reconstruction and normalization tests satisfy the explicit worker-local tolerance
  for every canonical tensor.
- **SC-003**: Wrong parent/schema/range, malformed/non-finite/unsafe tensor and every `A_j != H`
  case yields no candidate.
- **SC-004**: Exact retry returns identical content IDs; conflict/concurrency does not mutate the
  durable original.
- **SC-005**: Every incomplete/fault race publishes terminal evidence and no partial candidate.
- **SC-006**: Architecture tests reject worker-local contribution media at distribution and prove
  no native/JVM validator dependency.
- **SC-007**: Feature-004 fixture inputs are canonical, runtime-neutral and contain no accepted
  quantization implementation.

## Out of Scope

- Multi-worker collection, consensus, global reduce and outer optimizer.
- RPC/service discovery, enrollment, authentication, C++ or Java production code.
- INT16 quantization, sharding, residual error feedback and P2P distribution.
- Adaptive `H_i`, stale contribution acceptance, speed/memory mathematical weights.
- Mid-ticket migration and permissionless proof of worker computation.
