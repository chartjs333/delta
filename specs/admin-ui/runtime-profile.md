# Runtime Profile: Delta Admin UI

## Classification

The admin UI is optional tooling outside the authoritative Delta runtime. This
specification and the local/offline MVP have formal impact `NONE`.

## Ownership boundaries

- C++ core/runtime remains the sole owner of protocol legality, deterministic
  transitions, durability, certificates, aggregation, apply, and current state.
- Java node remains the owner of transport and operations defined by ADR-0010.
- Python worker remains the owner of local ML and contribution construction.
- `delta-protocol` remains the owner of runtime-neutral canonical schemas/fixtures.
- Admin UI owns presentation, local draft-document workflow, source adaptation,
  and visualization only.
- The MVP is a browser-local static application with no backend, login, credential
  flow, automatic network request, or runtime service dependency.

## Forbidden runtime coupling

The UI must not:

- invoke C ABI/FFM transition commands directly;
- read WAL/native memory or reconstruct state from internal classes;
- emit formal trace events as if it were a protocol actor;
- reinterpret opaque contribution or aggregate bytes;
- make Java node, C++ core/runtime, or Python worker depend on UI code;
- become mandatory for node startup, worker execution, or conformance tests.
- treat a governance document as a Delta-canonical protocol document or derive one
  from the other.

## Future API boundary

A future adapter may consume public operations/observability endpoints. Any new
endpoint that exposes a new protocol-visible result or enables state change requires
formal-impact review before implementation. Transport wrappers do not authorize the
UI to choose transition legality.

## Failure behavior

UI or adapter failure is contained to the tool. It may show unavailable, degraded,
stale, or read-only state; it cannot change the protocol outcome or current checkpoint.
