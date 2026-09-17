# ADR 0001: Browser-local React MVP

- **Status**: Accepted
- **Date**: 2026-09-14
- **Scope**: Delta Admin UI MVP only
- **Formal impact**: `NONE`

## Context

Delta has no mandatory web stack. The first UI workflow opens untrusted local JSON,
validates and edits it, and downloads a new JSON file. It must work without Delta
runtime, a network service, credentials, or a server, while leaving room for richer
tables, graphs, timelines, topology, and diagnostics later.

## Decision

Implement the MVP in isolated `tools/admin-ui/` using:

- TypeScript;
- React;
- Vite;
- a JSON Schema Draft 2020-12 validator;
- browser file selection and explicit download/export APIs;
- `DataSourcePort` with `LocalJsonAdapter` as the only product adapter.

The MVP is a static browser application. It has no backend, login, authorization
flow, credential storage, server persistence, analytics payload, live GitHub read,
or automatic network request. Exact package/version selection belongs to the
implementation lockfile and must satisfy the repository's dependency/security review.

The original input file is never automatically overwritten. Every persistent output
is an explicit user-initiated download of a new file.

## Consequences

- Delta core/runtime remains unaware of and independent from the UI.
- Local governance/custody data need not leave the browser.
- `DeltaApiAdapter`, authentication, authorization, backend services, live events,
  commands, and remote persistence require later ADRs and security/formal-impact review.
- Form and visualization libraries are deliberately not selected by this ADR.
- The implementation must enforce `../threat-model.md` before parsing, validating,
  rendering, following references, or exporting untrusted data.

## Rejected alternatives

- A Java/Vaadin server for the MVP: introduces a server and runtime coupling without
  serving the offline document workflow.
- A Java backend plus React for the MVP: remains a valid later integration shape but
  adds credentials, deployment, and data-transfer surfaces before a public API exists.
- Adding UI-specific schemas to `delta-protocol`: reverses the intended dependency
  direction and misstates governance documents as protocol contracts.
