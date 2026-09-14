# Implementation Plan: Extensible Delta Admin UI

**Branch**: `feature/admin-ui-spec` | **Date**: 2026-09-14 | **Spec**: `spec.md`

## Summary

Define and later implement an optional administrative shell whose offline MVP
supports local JSON controller documents and whose architecture can later consume
public Delta APIs and visualize campaigns, nodes, artifacts, and audit events.

## Technical Context

- Current repository boundary: C++ protocol/runtime, Java node/operations, Python worker.
- Reviewed `main` commit: `2197a0eeff6daafa031d002725e09e0cf465ce34`.
- Accepted formal semantics ID: `sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.
- Reviewed PR #29 head: `de3348fdcbd527046d5b66bc6d8c90df098d5aa8` (draft, non-normative input).
- Canonical schemas are owned by `delta-protocol`.
- MVP technology and packaging: TypeScript + React + Vite under `tools/admin-ui/`,
  accepted in `adr/0001-browser-local-react-vite.md`.
- MVP execution: browser-local, no backend, login, credentials, or network dependency.
- MVP validation: JSON Schema Draft 2020-12 using authority-classed schema descriptors.
- MVP data source: user-selected local JSON plus bundled/frozen or user-selected schemas.
- Future data source: stable public Delta API; not assumed to exist.
- Initial implementation root: `tools/admin-ui/`, isolated from mandatory core builds.

## Constitution Check

### Pre-implementation classification

- **Formal impact**: `NONE` for this specification and the read-only/offline MVP.
- No protocol action, vote, certificate, deadline, durability rule, current-state
  behavior, arithmetic precondition, or canonical serialization is changed.
- The UI consumes public contracts and never becomes an authority.
- Delta core/runtime has no reverse dependency on the UI.
- No secret, private key, restricted evidence, or signed artifact is added.

### STOP conditions

Reclassify and stop before implementation if work requires a new protocol-visible
action/result, changes a canonical schema, writes runtime state, creates signing or
governance authority, calls native transitions directly, or changes failure semantics.

### Final check

Review the final implementation diff against this classification and the accepted
formal semantics ID before promotion.

## Architecture and Data Flow

1. The shell composes domain modules and presentation extensions.
2. Domain modules call `DataSourcePort` only.
3. The local adapter supplies documents and structural schema validation in MVP.
4. Future API adapters expose only discovered stable capabilities.
5. Governance/protocol results retain authority and provenance metadata.
6. Missing capabilities produce explicit unavailable states.

See `architecture.md` and `contracts/data-source-port.md`.

## Project Structure

Specification artifacts live in `specs/admin-ui/`. A later implementation is
confined to `tools/admin-ui/` unless an approved ADR selects another isolated root.
No implementation directory is added by the specification branch.

## Implementation Sequence

1. Review and merge the spec-only branch.
2. Freeze the exact PR #29 fixture and its companion local schema with SHA-256 metadata.
3. Create the isolated browser shell and extension composition root.
4. Implement the data-source port and local JSON adapter with export-only persistence.
5. Implement controller list/detail and schema-valid editing.
6. Add untrusted-input limits, capability/provenance presentation, and contract tests.
7. Prove core/runtime build independence.
8. Defer API, authentication, live visualization, and commands to later scopes.

## Test Strategy

- Contract tests shared by adapter implementations.
- Round-trip tests for valid unknown fields.
- Negative schema and malformed-document tests.
- Adversarial size, depth, node-count, string, URL, and content-rendering tests.
- Tests proving no external schema references or URLs are fetched.
- Export-only tests proving the selected source file is never overwritten automatically.
- Capability matrix tests distinguishing unavailable, failed, stale, and unsupported.
- Provenance/subject mismatch tests.
- Extension registration tests.
- Accessibility checks for primary workflows.
- Dependency checks proving no core/runtime-to-UI edge.

## Observability

The MVP records local application errors and adapter state without emitting protocol
events. Future source observations remain distinguished from canonical trace events.
No telemetry claim is authoritative without source attribution.

## Rollout and Rollback

The UI is opt-in. Rollback removes or disables `tools/admin-ui/`; Delta operation
continues unchanged. API integration, if later added, must default to read-only and
degrade safely when unavailable.

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Four-slot PR #29 worksheet becomes the product model | Dynamic collections and non-normative fixture status |
| Structural validity is mistaken for approval | Authority classes and explicit UI language |
| Governance worksheet is validated as a protocol document | Mandatory schema authority and document-type match |
| Untrusted JSON exhausts or executes in the browser | Hard input limits, inert text rendering, no external references |
| Frontend duplicates protocol logic | Data-source port plus sourced-result-only rules |
| Future API requires view rewrites | Adapter contract and shared contract tests |
| Extension claims are unrealistic | Localized composition root, not zero-file-change promise |
| UI becomes a runtime prerequisite | Separate root, independent build, reverse-dependency checks |

## Exit Gate

The spec branch exits when requirements, formal impact, adapter contract, extension
points, security boundary, tasks, and checklists are reviewed, with no implementation
or runtime files changed.
