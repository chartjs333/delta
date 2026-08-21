# Tasks: Permissioned trust, signed artifacts и resilience

**Input**: `spec.md`, `plan.md`, constitution и завершённые `001–007`.

## Phase 1: Threat model and contracts

- [ ] T001 Документировать assets/actors/trust boundaries/attacks/non-goals в `docs/security-model.md`.
- [ ] T002 Определить enrollment/signed-envelope/revocation/audit/screening models в `src/deltatorrent/domain/security.py`.
- [ ] T003 Создать security protobuf contract в `proto/deltatorrent/security/v1/security.proto`.
- [ ] T004 [P] Добавить canonical signed/trust fixtures в `tests/fixtures/contracts/security/`.
- [ ] T005 Добавить contract/canonicalization tests в `tests/contract/test_security_contract.py`.

## Phase 2: PKI, secrets and trust foundation

- [ ] T006 Реализовать development CA issue/renew/revoke tools в `src/deltatorrent/security/pki.py`.
- [ ] T007 Реализовать enrollment/trust-store/history в `src/deltatorrent/security/enrollment.py` и `trust_store.py`.
- [ ] T008 Реализовать restrictive/redacted secret loader в `src/deltatorrent/security/secrets.py`.
- [ ] T009 Реализовать Ed25519 canonical sign/verify в `src/deltatorrent/security/signatures.py`.
- [ ] T010 Реализовать signed revocation snapshots/cache policy в `src/deltatorrent/security/revocation.py`.
- [ ] T011 [P] Добавить key/permission/redaction tests в `tests/security/test_secret_hygiene.py`.
- [ ] T012 Добавить signature/key-rotation/history tests в `tests/security/test_signed_envelopes.py`.

## Phase 3: US1 — mTLS and authorization

- [ ] T013 [US1] Реализовать deny-by-default authorization policy в `src/deltatorrent/security/authorization.py`.
- [ ] T014 [US1] Реализовать gRPC mTLS/authn/authz interceptors в `src/deltatorrent/adapters/grpc/security.py`.
- [ ] T015 [US1] Подключить security middleware к coordinator/reduce/swarm servers.
- [ ] T016 [US1] Реализовать identity CLI в `src/deltatorrent/cli/identity.py`.
- [ ] T017 [US1] Добавить issuer/expiry/revocation/role/scope matrix в `tests/security/test_mtls_authorization.py`.

## Phase 4: US2 — Signed lineage and replay protection

- [ ] T018 [US2] Добавить signed envelopes к worker updates/regional partials/round results/object manifests.
- [ ] T019 [US2] Реализовать durable context-bound replay store в `src/deltatorrent/security/replay.py`.
- [ ] T020 [US2] Интегрировать verify-before-decode во все intake/download paths.
- [ ] T021 [US2] Реализовать `security verify-artifact` CLI в `src/deltatorrent/cli/security.py`.
- [ ] T022 [US2] Добавить mutation/context/retry/restart tests в `tests/security/test_replay_revocation.py`.
- [ ] T023 [US2] Добавить signed P2P integration suite в `tests/integration/test_signed_swarm.py`.

## Phase 5: Audit chain

- [ ] T024 Реализовать append-only hash-chained audit segments в `src/deltatorrent/security/audit.py`.
- [ ] T025 Реализовать signed rotation checkpoints и streaming verifier.
- [ ] T026 Реализовать `audit verify` CLI в `src/deltatorrent/cli/audit.py`.
- [ ] T027 Добавить mutation/deletion/reorder/restart/disk tests в `tests/security/test_audit_chain.py`.

## Phase 6: US3 — Update screening

- [ ] T028 [US3] Реализовать structural/finite/token/absolute norm screening в `src/deltatorrent/security/screening.py`.
- [ ] T029 [US3] Реализовать minimum-cohort median/MAD/cosine policy в `src/deltatorrent/security/screening.py`.
- [ ] T030 [US3] Реализовать deterministic hidden validation adapter в `src/deltatorrent/security/validation_probe.py`.
- [ ] T031 [US3] Интегрировать ACCEPT/REJECT/QUARANTINE и audit evidence в coordinator intake.
- [ ] T032 [US3] Добавить clean/malicious/insufficient-cohort/probe tests в `tests/security/test_screening.py`.

## Phase 7: US4 — Reducer failover and churn

- [ ] T033 [US4] Реализовать signed reducer lease/epoch state в `src/deltatorrent/resilience/leases.py`.
- [ ] T034 [US4] Реализовать deterministic standby failover в `src/deltatorrent/resilience/failover.py`.
- [ ] T035 [US4] Реализовать worker churn/quorum evaluator в `src/deltatorrent/resilience/churn.py`.
- [ ] T036 [US4] Интегрировать replica same-hash idempotency/different-hash conflict в global intake.
- [ ] T037 [US4] Добавить primary/standby/conflict suite в `tests/integration/test_reducer_failover.py`.
- [ ] T038 [US4] Добавить deterministic 10% worker-loss scenario в `tests/integration/test_churn_resilience.py`.

## Final Phase: Validation and operations

- [ ] T039 Написать incident/revocation/key-rotation runbook в `docs/incident-response.md`.
- [ ] T040 Добавить test-only PKI/resilience configs без private keys в `configs/security/`.
- [ ] T041 Добавить repository/log secret scan в `.github/workflows/security.yml`.
- [ ] T042 Записать security/resilience evidence в `specs/008-permissioned-trust-and-resilience/evidence.md`.
- [ ] T043 Выполнить cross-artifact, architecture, full quality и final Constitution gates.

## Dependencies

- T001–T005 блокируют security-persisted artifacts.
- T006–T012 блокируют external enforcement.
- T013–T023 должны пройти до non-loopback testing.
- T024–T027 блокируют enforcement evidence.
- T028–T032 должны пройти observe-only до reject policy.
- T033–T038 требуют signed deterministic reducers.
- T039–T043 завершают branch.

## Implementation Strategy

Сначала test PKI/canonical signatures, затем mTLS/authz и replay, после — audit. Screening вводится observe-only до прохождения clean-reference gate. Resilience строится на immutable signed inputs; security нельзя «временно» отключить для non-loopback path.

## Exit Gate

Все T001–T043 выполнены; security matrices, audit, clean/malicious screening, signed swarm, 10% churn и reducer failover/conflict suites зелёные; secret scan чист; evidence/quality/Constitution gates завершены.
