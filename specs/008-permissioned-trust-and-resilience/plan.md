# Implementation Plan: Permissioned trust, signed artifacts и resilience

**Branch**: `008-permissioned-trust-and-resilience` | **Date**: 2026-08-21 | **Spec**: `spec.md`

## Summary

Добавить security ports/middleware вокруг существующих transport и artifact boundaries, не смешивая криптографию с training math. Internal CA выпускает mTLS credentials и отдельные Ed25519 artifact keys. Canonical signed envelopes проходят trust/revocation/authorization/replay pipeline до decode. Screening остаётся deterministic policy service. Reducer topology получает lease epochs/standbys; audit chain связывает все решения.

## Technical Context

- Cryptography: X.509 mTLS trust bundle и Ed25519 detached signatures через audited library.
- Canonicalization: existing canonical JSON/binary envelopes; signature covers exact bytes/hash/context.
- Secrets: file/env adapters, 0600-style permission checks where supported, redaction.
- Authorization: pure policy evaluator + gRPC interceptors/application guards.
- Revocation: signed monotonic snapshot/sequence, cache with bounded TTL.
- Audit: append-only filesystem reference segments + hash chain/signed checkpoints.
- Screening: FP32 summaries, deterministic held-out evaluation adapter.
- Resilience: reducer lease epoch/CAS and standby execution from immutable inputs.

## Constitution Check

| Principle | Design response | Gate |
| --- | --- | --- |
| Permissioned security | Enrollment, mTLS, signatures, roles, revocation, replay | Security matrix |
| Scientific correctness | Screening is explicit/evidenced; no hidden weight mutation | Clean-reference tests |
| Versioned state | Trust/policy/signature/audit/lease snapshots versioned | Contract tests |
| Plane separation | Signed local/partial/global media retain their plane restrictions | Architecture tests |
| Bounded resilience | Quorum, leases, failover deadline, conflict abort | Churn/failover suite |
| Observable/reversible | Audit chain, kill/revoke, deterministic policies | Audit/recovery gate |

**Pre-implementation result**: PASS.

## Architecture and Data Flow

```text
mTLS peer → AuthN(node/key) → AuthZ(role/scope) → Replay guard
                                                   │
Signed update bytes → signature/lineage/hash verify ┤
                                                   ▼
                                            Screening pipeline
                                                   │
                                          ACCEPT/REJECT/QUARANTINE
                                                   │
                                          existing reduce math

Reducer lease epoch: primary ─┐
                              ├─ same immutable inputs → signed partial
                     standby ─┘
All decisions ─▶ append-only hash-chained audit
```

## Project Structure

```text
src/deltatorrent/
  domain/security.py
  security/
    pki.py
    enrollment.py
    trust_store.py
    signatures.py
    authorization.py
    replay.py
    revocation.py
    secrets.py
    audit.py
    screening.py
    validation_probe.py
  resilience/
    leases.py
    failover.py
    churn.py
  adapters/grpc/security.py
  cli/identity.py
  cli/security.py
  cli/audit.py
proto/deltatorrent/security/v1/security.proto
tests/
  security/test_mtls_authorization.py
  security/test_signed_envelopes.py
  security/test_replay_revocation.py
  security/test_screening.py
  security/test_secret_hygiene.py
  integration/test_reducer_failover.py
  integration/test_churn_resilience.py
  integration/test_signed_swarm.py
docs/security-model.md
docs/incident-response.md
```

## Implementation Sequence

1. Утвердить threat model, enrollment/signed-envelope/revocation/audit schemas.
2. Реализовать test CA, secret loader, trust store и artifact signatures.
3. Добавить mTLS/authz middleware ко всем non-loopback transports.
4. Реализовать replay store, revocation refresh и exact retry semantics.
5. Реализовать audit chain/rotation/verifier.
6. Реализовать deterministic screening и optional validation probe.
7. Добавить reducer leases/standbys/conflict handling и churn policy.
8. Выполнить malicious corpus, signed P2P и 10% churn/failover gates.

## Test Strategy

- **PKI/auth**: issuer/expiry/revocation/role/scope/key rotation/clock skew.
- **Signature**: mutate each signed field/hash/context; historical key verification.
- **Replay**: exact retry, payload/context reuse, restart/retention.
- **Screening**: clean, NaN, norm, robust cohort, insufficient cohort, probe failure/regression.
- **Audit**: append/restart/rotate, mutation/deletion/reorder, disk failure.
- **Resilience**: worker dropout distributions, primary failure, same/different replica hashes.
- **Regression**: clean trusted round identical to pre-security reference; signed swarm exactness.
- **Secret hygiene**: repository scan and log/snapshot redaction.

## Observability

Auth/signature/replay/revocation/screening decisions by stable reason; trust snapshot age; audit tail/checkpoint health; reducer lease/failover/conflict; churn/quorum. IDs/hashes logged, private keys/raw hidden data/tensors never logged.

## Rollout and Rollback

Staged: test CA/local mTLS → required signatures in audit-only mode → enforce signatures/roles → screening observe-only → enforce absolute guards → cohort/probe selectively → standby failover. Production-like non-loopback cannot rollback to unauthenticated mode; rollback uses previous trusted policy/version, revoke/disable endpoints, or central safe mode.

## Risks and Mitigations

- **CA compromise**: offline/root separation documented, rotation/revocation; full HSM deferred.
- **Canonicalization mismatch**: golden signed envelopes across components.
- **Revocation staleness**: bounded TTL/fail closed for writes.
- **False-positive screening**: observe-only stage, quarantine option, explicit evidence.
- **Replica nondeterminism**: identical version/profile/input requirements; conflicts abort.
- **Audit unavailable**: fail-closed for critical mutation or explicit degraded read-only mode.

## Exit Gate

Threat model approved; PKI/auth/signature/replay/revocation/screening/audit suites pass; clean round unchanged; signed swarm works; 10% churn/primary failover scenario passes; conflicting replicas abort; secret scan clean; full quality and final Constitution Check complete.
