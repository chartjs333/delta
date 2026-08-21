# Feature Specification: Permissioned trust, signed artifacts и resilience

**Feature Branch**: `008-permissioned-trust-and-resilience`  
**Created**: 2026-08-21  
**Status**: Planned — ready for implementation  
**Depends on**: `007-adaptive-heterogeneous-scheduling`

## Summary

До выхода за локальный test network все node-to-node связи, update manifests и published swarm objects должны иметь проверяемое происхождение. Функция вводит operator-managed enrollment, mTLS, Ed25519 artifact signatures, role authorization, revocation/rotation, replay protection, append-only audit chain и conservative update screening.

Функция также добавляет availability-механизмы для permissioned pilot: redundant reducer assignments, deterministic failover и round completion при потере примерно 10% workers при условии сохранения configured quorum/capacity. Это не Byzantine consensus и не доказательство честного выполнения удалённого обучения; система проверяет identity, целостность, lineage и явные sanity/quality signals.

## User Scenarios & Testing

### US1 — Подключить только зарегистрированный узел с разрешённой ролью (Priority: P1)

Оператор выпускает enrollment для worker/reducer/coordinator/peer, узел устанавливает mTLS и вызывает только разрешённые методы.

**Independent Test**: локальный PKI fixture проверяет valid, expired, revoked, wrong-role и unknown certificates на coordinator, reduce и swarm endpoints.

**Acceptance Scenarios**:

1. **Given** active enrollment и сертификат worker role, **When** worker подключается к coordinator по mTLS, **Then** authenticated node ID из certificate binding совпадает с request identity.
2. **Given** worker certificate, **When** клиент пытается выполнить reducer/admin method, **Then** request отвергается `PERMISSION_DENIED` и audit-ится.
3. **Given** expired/revoked certificate или unknown issuer, **When** handshake/request выполняется, **Then** соединение/операция отвергается до обработки payload.
4. **Given** key rotation overlap window, **When** узел использует новый active key, **Then** запрос принимается; старый key после cutoff отвергается.

### US2 — Проверить подпись, lineage и replay каждого update/artifact (Priority: P1)

Worker подписывает canonical update envelope, reducer подписывает partial, coordinator подписывает round/object manifest; получатель проверяет их до доверия content hashes.

**Independent Test**: изменение любого signed field, payload hash, signer identity, round/assignment/role или signature bytes приводит к reject; exact retry возвращает идемпотентный receipt, а replay в другом context отвергается.

**Acceptance Scenarios**:

1. **Given** canonical local update envelope и active worker signing key, **When** update подан для matching assignment, **Then** signature, key validity, role, round/parent/schema/content hash и nonce проверяются до decode.
2. **Given** valid bytes/signature уже приняты, **When** тот же command повторён, **Then** coordinator возвращает исходный receipt без второго применения.
3. **Given** тот же signed update переотправлен в другой round/assignment или после replay window, **When** intake выполняется, **Then** request отвергается как replay/context mismatch.
4. **Given** P2P object manifest, **When** peer получает его, **Then** он доверяет object ID только после проверки coordinator/publisher signature и authorization scope.

### US3 — Отфильтровать явно опасный update и сохранить диагностику (Priority: P1)

Coordinator выполняет deterministic pre-aggregation screening: structural/finite/norm rules, relative outlier rules при достаточной выборке и optional hidden validation probe.

**Independent Test**: fixture updates с NaN, excessive norm, invalid token claim и сильным validation regression отвергаются/карантинируются по policy; нормальные updates сохраняют reference result.

**Acceptance Scenarios**:

1. **Given** non-finite/wrong-schema/excessive absolute norm update, **When** screening выполняется, **Then** update hard-reject-ится до accepted set.
2. **Given** достаточное число candidate updates, **When** relative norm/cosine outlier превышает configured robust threshold, **Then** update получает deterministic `REJECT` или `QUARANTINE` согласно policy.
3. **Given** hidden validation probe включён, **When** decoded candidate ухудшает probe loss выше signed policy threshold, **Then** result и агрегированные probe metrics audit-ятся без раскрытия hidden samples worker-у.
4. **Given** screening evidence недостаточно, **When** relative rule не применима, **Then** система использует только absolute guards и отмечает `INSUFFICIENT_COHORT`, а не выдумывает норму.

### US4 — Завершить раунд при контролируемом churn (Priority: P1)

Часть workers/reducers отключается, но spare capacity и quorum достаточны.

**Independent Test**: deterministic scenario теряет 10% workers и primary reducer processes; standby replicas берут authoritative sealed inputs, round публикуется один раз и совпадает с reference accepted survivors.

**Acceptance Scenarios**:

1. **Given** worker dropout до hard deadline и quorum всё ещё достигнут, **When** round seal-ится, **Then** отсутствующие workers исключаются, а token denominator использует только accepted survivors.
2. **Given** primary reducer недоступен, **When** failover lease истёк, **Then** eligible standby с тем же topology/accepted-set выполняет shard и публикует совместимый signed partial.
3. **Given** primary и standby публикуют один и тот же content hash, **When** global intake видит оба, **Then** один partial принимается идемпотентно.
4. **Given** replicas публикуют конфликтующие validly signed hashes, **When** conflict обнаружен, **Then** shard/round quarantine или abort-ится; система не выбирает результат молча.
5. **Given** churn превышает configured quorum/capacity, **When** hard deadline наступает, **Then** round abort-ится безопасно с полным incident evidence.

## Edge Cases

- Certificate valid по времени, но enrollment revoked минутой ранее.
- Clock skew у node; authority uses coordinator time and configured skew allowance.
- TLS key и artifact signing key различны либо один ротирован.
- Canonical envelope signature проверена, но referenced piece отсутствует/повреждён.
- Exact retry после coordinator restart и replay-store compaction.
- Node ID пытается подписать update за другой assignment/role.
- Signing key скомпрометирован в середине open round.
- Cohort слишком мал для median/MAD или все norms одинаковы.
- Hidden probe itself fails/non-finite.
- Malicious update проходит norm, но направлен плохо; система не обещает полную Byzantine protection.
- Primary и standby гонка/partition с conflicting outputs.
- 10% churn сосредоточен в одном регионе/shard committee.
- Audit disk full или hash-chain tail повреждён.
- Secret file имеет небезопасные permissions.

## Requirements

### Functional Requirements

- **FR-001**: Система MUST использовать permissioned `EnrollmentRecord` с immutable node ID, roles, TLS public key/certificate binding, artifact-signing public key, validity interval, project/region scopes, serial/version и status.
- **FR-002**: Operator CA/authority MUST поддерживать issue, inspect, renew/rotate, revoke и export trust bundle; private CA/signing keys MUST никогда не коммититься.
- **FR-003**: Все non-loopback coordinator/reduce/swarm control/data endpoints MUST требовать mTLS после включения этой feature; insecure override разрешён только explicit local development profile.
- **FR-004**: Auth middleware MUST выводить node ID/roles из verified credential, а не доверять request fields; mismatch отвергается.
- **FR-005**: Authorization policy MUST быть deny-by-default и проверять method, role, project, region и object/round scope.
- **FR-006**: Artifact signatures MUST использовать Ed25519 над canonical signed envelope, содержащим schema version, signer/key IDs, role, issued/expiry time, nonce/command ID, context IDs и content/manifest hashes.
- **FR-007**: Worker MUST подписывать local encoded update manifest; regional reducers — partial manifests; coordinator/global publisher — round result и distributable object manifests; tracker/peer advertisements MUST быть authenticated.
- **FR-008**: Verifier MUST проверить canonical bytes, signature, enrollment/key validity at accepted time, role/scope, context/lineage и all referenced hashes до semantic use.
- **FR-009**: Revocation MUST иметь monotonic authority sequence и bounded cache TTL; security-critical endpoints MUST support immediate refresh/deny on unknown status.
- **FR-010**: Key rotation MUST поддерживать explicit overlap/cutoff, key IDs и audit linkage; старые artifacts остаются проверяемыми по historical trust records.
- **FR-011**: Replay store MUST связывать signer, nonce/command/update ID, round/assignment/context и payload hash; exact retry идемпотентен, context/payload reuse отвергается.
- **FR-012**: Replay/audit persistence MUST переживать restart и не очищаться раньше retention, покрывающего active rounds и artifact verification window.
- **FR-013**: Screening pipeline MUST выполнять structural lineage/schema/hash checks, finite scan, token-bound checks, absolute per-tensor/global norm limits до cohort rules.
- **FR-014**: Optional cohort screening MUST использовать versioned robust policy (например median/MAD norm и cosine-to-centroid) только при minimum cohort; exact formula/threshold/action записываются в evidence.
- **FR-015**: Optional hidden validation probe MUST использовать coordinator-controlled content-addressed data/config, deterministic evaluation и threshold; raw hidden examples не отправляются worker-у.
- **FR-016**: Screening action MUST быть `ACCEPT`, `REJECT` или `QUARANTINE`; quarantined update не входит в reduce до explicit reviewed decision.
- **FR-017**: Token count остаётся bounded signed claim, сверяемой с assignment/data cursor; система MUST явно не утверждать cryptographic proof of honest compute.
- **FR-018**: Audit log MUST быть append-only hash-chained records с actor, action, target IDs/hashes, policy/version, decision, timestamp и previous-record hash; payload tensors/secrets не логируются.
- **FR-019**: Audit verifier MUST обнаруживать deletion, reordering и mutation records; log rotation связывается signed checkpoint/root.
- **FR-020**: Hierarchical topology MUST поддерживать primary + configurable standby reducer replicas per required shard с signed lease/epoch.
- **FR-021**: Failover MUST использовать same immutable topology, regional accepted set, inputs и reducer code/profile; standby result должен иметь same deterministic content hash.
- **FR-022**: Global intake MUST принимать первый valid authoritative result per epoch/hash; same-hash replica duplicate идемпотентен, different-hash conflict блокирует shard и audit-ится.
- **FR-023**: Worker churn policy MUST продолжать round только при predeclared minimum workers/tokens/region constraints; denominator включает только accepted screened updates.
- **FR-024**: Revoked/quarantined node MUST быть исключён из новых assignments/peer advertisements и active leases по policy; уже опубликованные artifacts остаются immutable, но trust status видим.
- **FR-025**: Secret loader MUST поддерживать environment/file/OS-secret adapters, проверять restrictive file permissions и redaction; sample configs содержат только placeholders.
- **FR-026**: Security/resilience metrics MUST включать auth failures, role denials, signature/replay/screening decisions, revocation freshness, failovers, conflicting replicas, churn/quorum и audit health.
- **FR-027**: CLI MUST предоставлять `identity init-ca/enroll/rotate/revoke/inspect`, `security verify-artifact`, `audit verify` и resilience smoke scenario.

### Non-Functional Requirements

- **NFR-001**: Private keys/tokens MUST не появляться в logs, manifests, fixtures, test snapshots или repository history.
- **NFR-002**: Signature/auth/replay checks MUST происходить до expensive decode/allocation whenever metadata permits.
- **NFR-003**: Verification policy MUST fail closed при unknown issuer/key/revocation status для mutating operations.
- **NFR-004**: Security tests MUST включать malicious corpus и be deterministic/offline with test CA.
- **NFR-005**: При 10% worker loss и достаточном configured quorum target resilience scenario MUST завершить round без manual intervention; это не гарантируется при concentrated loss beyond redundancy.
- **NFR-006**: Failover/retry MUST быть bounded; conflicting replica result никогда не разрешается случайным/arrival-order выбором.
- **NFR-007**: Audit chain verification SHOULD масштабироваться streaming и иметь documented retention/rotation behavior.
- **NFR-008**: Feature не заявляет Sybil resistance, permissionless trust или general Byzantine convergence.

### Key Entities

- **EnrollmentRecord / TrustBundle / RevocationSnapshot**: authoritative identity state.
- **SignedEnvelope**: canonical metadata/context/content hashes и Ed25519 signature.
- **ReplayRecord**: context-bound idempotency/reuse decision.
- **ScreeningPolicy / ScreeningEvidence**: deterministic guards и outcome.
- **AuditRecord / AuditCheckpoint**: hash-chained security/operation history.
- **ReducerLease**: primary/standby role, epoch, topology/accepted-set binding.
- **ResiliencePlan**: quorum, spare capacity и failure-injection expectations.

## Success Criteria

- **SC-001**: mTLS/authorization matrix принимает только active correctly scoped roles и отвергает unknown/expired/revoked/wrong-role credentials.
- **SC-002**: Signature mutation/context/replay corpus полностью отвергается; exact retries остаются идемпотентными после restart.
- **SC-003**: Structural/norm/cohort/probe screening fixtures дают deterministic documented decisions и не меняют clean reference results.
- **SC-004**: Audit verifier обнаруживает mutation/deletion/reordering и подтверждает signed rotation checkpoints.
- **SC-005**: 10% worker-loss + primary-reducer-loss scenario публикует exact survivor-reference result при достаточном quorum/spares.
- **SC-006**: Conflicting valid replica hashes блокируют publication и создают incident evidence.
- **SC-007**: P2P clients отвергают unsigned/unauthorized global manifests; signed verified objects продолжают exact download.
- **SC-008**: Secret scanning и repository test подтверждают отсутствие private keys/real credentials.

## Assumptions

- Operator/admin authority доверен и управляет enrollment/revocation.
- Узлы permissioned pilot имеют устойчивые logical identities.
- Hidden validation probe — дополнительный signal, не абсолютное доказательство качества.
- Redundant deterministic reducers используют совместимые software/profile versions.

## Out of Scope

- Public/permissionless enrollment, Sybil resistance, staking/reputation/economics.
- General Byzantine consensus, secure aggregation или zero-knowledge proof of training.
- Защита от полностью скомпрометированного trusted coordinator/CA.
- HSM/TPM remote attestation как обязательное требование.
- Гарантированное обнаружение всех poisoning/backdoor updates.
