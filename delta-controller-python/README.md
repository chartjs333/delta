# Delta Controller & Authorization Gate (Step 5C)

This package implements the trusted Zone 2 Authorization Gate for Step 5C controlled live execution.

## Responsibilities

- Bounded input parsing and size validation
- Canonical JSON (RFC 8785 / JCS) recomputation and SHA-256 digest verification
- Draft 2020-12 schema validation against frozen contract schemas
- Independent caller authentication and governance policy evaluation
- Frozen catalog parity and capability matrix allowlist enforcement
- Durable append-only idempotency ledger keyed by `intent_id` (with `ERR_INTENT_COLLISION_DETECTED` fail-closed rejection)
- Resource grant calculation and concurrency/timeout control
- Asymmetric Ed25519 signing of `AdmissionRecord` over `AdmissionRecord \ {"authenticator.signature"}`
- Construction of immutable `AuthorizedExecution` bundles for Zone 3 worker dispatch
- Secret-redacted audit logging
