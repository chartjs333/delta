# Delta Admin UI Spec Kit

Status: Draft specification for an optional administrative tool.

This directory defines an extensible visual shell over public Delta contracts,
documents, observations, and sourced assessments. It does not add a protocol
transition, alter DeltaReduce semantics, or make the UI a runtime dependency.

## Scope at a glance

- PR #29 is a non-normative MVP input, not the product architecture.
- The first MVP opens, edits, structurally validates, views, and exports local
  JSON documents.
- Governance documents and Delta-canonical protocol documents use different
  schema descriptors and are never treated as interchangeable.
- Governance assessments and protocol results are displayed only when a source
  explicitly provides them with authority and provenance metadata.
- Domain views depend on a stable data-source port, with local JSON first and a
  future public Delta API adapter later.
- The accepted MVP ADR selects a browser-local TypeScript/React/Vite tool with
  no backend, login, credential flow, or automatic network access.
- Imported JSON is untrusted input and is subject to the limits in the threat model.

## Artifacts

- [Feature specification](spec.md)
- [Implementation plan](plan.md)
- [Tasks](tasks.md)
- [Architecture](architecture.md)
- [Logical data model](data-model.md)
- [Data-source port](contracts/data-source-port.md)
- [Security boundaries](security-boundaries.md)
- [Threat model](threat-model.md)
- [MVP technology ADR](adr/0001-browser-local-react-vite.md)
- [Runtime profile](runtime-profile.md)
- [Runtime tasks](runtime-tasks.md)
- [Requirements checklist](checklists/requirements.md)
- [Hybrid-runtime checklist](checklists/hybrid-runtime.md)
- [Reviewed baseline](evidence/spec-baseline.json)
- [Reviewed decisions](evidence/spec-decisions.json)
- [Spec Kit manifest](evidence/spec-kit-manifest.json)

## Branching

The specification is intended for `feature/admin-ui-spec`, based directly on
`main`. Implementation belongs in a later branch after specification review.
