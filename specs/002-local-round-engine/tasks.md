# Tasks: Локальный worker round и нормализованный contribution

**Input**: `spec.md`, `plan.md`, Constitution 2.1.0, merged feature-001 exit evidence,
protocol registry and exact Formal GO.

## Format

`- [ ] T### [P?] [US#?] Action with exact path`

Каждый implementation commit указывает один или несколько `T*`/`HR002-*` IDs. Задача
отмечается `[x]` только после прохождения её acceptance evidence.

## Phase 0: Predecessor and formal compatibility STOP

- [x] T000 [HR002-001] Offline verify merged feature-001 exit evidence, protocol registry,
  Formal GO, exact `formal_semantics_id` and absence of semantic drift; record evidence in
  `specs/002-local-round-engine/evidence/predecessor-gate.json`. STOP all T001+ on failure.

## Phase 1: Runtime-neutral domain contracts

- [x] T001 Define strict `DomainPureWorkTicket` schema and Python model in
  `delta-protocol/schemas/domain-pure-work-ticket-v1.json` and
  `delta-worker-python/src/deltatorrent/domain/tickets.py`.
- [x] T002 Define canonical `ParameterSchema`, tied aliases and fingerprint contract in
  `delta-protocol/schemas/parameter-schema-v1.json` and
  `delta-worker-python/src/deltatorrent/domain/parameters.py`.
- [x] T003 Define `LocalRoundCompletion`, internal `LocalDelta` and commit-eligible
  `NormalizedContributionCandidate` contracts in
  `delta-protocol/schemas/local-round-completion-v1.json`,
  `delta-protocol/schemas/normalized-contribution-candidate-v1.json` and
  `delta-worker-python/src/deltatorrent/domain/updates.py`.
- [x] T004 [P] Define worker lifecycle and terminal state transitions in
  `delta-worker-python/src/deltatorrent/domain/worker_state.py`.
- [x] T005 [P] Add canonical positive/negative ticket, completion and contribution fixtures in
  `delta-protocol/fixtures/local-round/`.
- [x] T006 Add schema/canonical-bytes/state-machine tests in
  `delta-worker-python/tests/contract/test_local_round_contract.py`.

## Phase 2: Foundational math and accounting

- [x] T007 Implement canonical parameter traversal/fingerprint and tied-parameter handling in
  `delta-worker-python/src/deltatorrent/delta/schema.py`.
- [x] T008 Implement exact optimizer-boundary token ledger in
  `delta-worker-python/src/deltatorrent/training/token_accounting.py`.
- [x] T009 Refactor a reusable local AdamW step loop without changing baseline semantics in
  `delta-worker-python/src/deltatorrent/training/local_round.py`.
- [x] T010 Implement internal FP32 `LocalDelta = parent - final` builder in
  `delta-worker-python/src/deltatorrent/delta/builder.py`.
- [x] T011 [P] Implement `final = parent - LocalDelta` reconstruction helper in
  `delta-worker-python/src/deltatorrent/delta/reconstruction.py`.
- [x] T012 Implement exact `A_j = H` eligibility guard, `LocalDelta / A_j` normalization,
  tensor-set/finite/norm validation in
  `delta-worker-python/src/deltatorrent/delta/normalization.py` and
  `delta-worker-python/src/deltatorrent/delta/validation.py`.
- [x] T013 [P] Add property/reference reconstruction, normalization and validation tests in
  `delta-worker-python/tests/unit/test_delta_math.py`.
- [x] T014 [P] Add parameter-schema and committed-ledger tests in
  `delta-worker-python/tests/unit/test_parameter_schema.py` and
  `delta-worker-python/tests/unit/test_token_accounting.py`.

## Phase 3: US1 — Complete one fixed local ticket

- [x] T015 [US1] Implement ticket validator and immutable parent/data resolvers in
  `delta-worker-python/src/deltatorrent/worker/validation.py`.
- [x] T016 [US1] Implement `LocalRoundEngine` orchestration in
  `delta-worker-python/src/deltatorrent/worker/engine.py`.
- [x] T017 [US1] Connect lifecycle, terminal evidence and structured metrics in
  `delta-worker-python/src/deltatorrent/worker/telemetry.py`.
- [x] T018 [US1] Add `worker run-ticket` CLI in
  `delta-worker-python/src/deltatorrent/cli/worker.py`.
- [x] T019 [US1] Add direct-reference parity, exact data-range and `A_j=H` tests in
  `delta-worker-python/tests/integration/test_local_round_engine.py`.

## Phase 4: US2 — Reconstruct and publish an eligible contribution

- [x] T020 [US2] Integrate safe normalized FP32 contribution writer in
  `delta-worker-python/src/deltatorrent/worker/update_writer.py`.
- [x] T021 [US2] Add canonical metadata, reconstruction, wrong-schema and malformed-update tests
  in `delta-worker-python/tests/integration/test_local_update_reconstruction.py`.
- [x] T022 [P] [US2] Add optional mixed-precision CUDA-to-FP32 reference test in
  `delta-worker-python/tests/integration/test_local_round_cuda.py`.

## Phase 5: US3 — Failure, idempotency and cancellation

- [x] T023 [US3] Implement atomic ticket claim/result repository in
  `delta-worker-python/src/deltatorrent/worker/repository.py`.
- [x] T024 [US3] Implement injected cancellation/deadline checks at microbatch boundaries in
  `delta-worker-python/src/deltatorrent/worker/engine.py`.
- [x] T025 [US3] Add retry/conflict/crash/cancel/deadline/partial-accumulation/data-exhaustion/
  OOM/non-finite suite proving candidate absence and terminal-evidence presence in
  `delta-worker-python/tests/integration/test_worker_idempotency.py`.
- [x] T026 [P] [US3] Add concurrent-claim test for one `ticket_id` in
  `delta-worker-python/tests/integration/test_worker_concurrency.py`.

## Final Phase: Validation and documentation

- [ ] T027 Document `LocalDelta` sign, `A_j=H` guard and normalized contribution contract in
  `docs/local-round-contract.md`.
- [ ] T028 Add deterministic `DomainPureWorkTicket` in
  `configs/worker/smoke-ticket.json`.
- [ ] T029 Add architecture tests prohibiting local contributions in distribution and native/JVM
  validator dependencies in
  `delta-worker-python/tests/architecture/test_reduce_distribution_boundary.py`.
- [ ] T030 Run formal projection/cross-artifact analysis and record evidence in
  `specs/002-local-round-engine/evidence/final-compatibility.json`.
- [ ] T031 Run the full offline quality gate and final Constitution Check; record evidence in
  `specs/002-local-round-engine/evidence/exit-gate.md`.

## Supplemental mandatory runtime tasks

`HR002-002–HR002-009` in `runtime-tasks.md` are part of this exit gate. In particular,
`HR002-008` publishes runtime-neutral feature-004 encoder inputs but MUST NOT implement INT16
quantization, C++ or Java production code.

## Dependencies

- T000/HR002-001 is a hard prerequisite for every T001+ and HR002-002+ task.
- T001–T006 block persisted implementation.
- T007–T014 block contribution publication.
- T015–T021 form the first complete vertical slice.
- T023 must precede retry/concurrency tests.
- T029–T031 and HR002-009 execute after all user stories.

## Exit Gate

T000–T031 and HR002-001–HR002-009 complete; one deterministic fixed ticket matches the direct
reference, uses exactly its immutable data range, satisfies `A_j=H`, reconstructs final state and
publishes canonical normalized metadata. Every incomplete path publishes terminal evidence and no
eligible candidate. Formal compatibility, architecture boundaries and offline quality gates pass.
