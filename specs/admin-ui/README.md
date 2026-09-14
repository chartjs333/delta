# Delta Admin UI Spec Kit

Status: Draft specification for an optional administrative tool.

This directory defines an extensible visual shell over public Delta contracts,
documents, observations, and sourced assessments. It does not add a protocol
transition, alter DeltaReduce semantics, or make the UI a runtime dependency.

## Scope at a glance

- PR #29 is a non-normative MVP input, not the product architecture.
- The first MVP opens, edits, structurally validates, views, and exports local
  JSON documents.
- Governance assessments and protocol results are displayed only when a source
  explicitly provides them with authority and provenance metadata.
- Domain views depend on a stable data-source port, with local JSON first and a
  future public Delta API adapter later.
- UI technology selection is deferred to a separate ADR.

## Artifacts

- [Feature specification](spec.md)
- [Implementation plan](plan.md)
- [Tasks](tasks.md)
- [Architecture](architecture.md)
- [Logical data model](data-model.md)
- [Data-source port](contracts/data-source-port.md)
- [Security boundaries](security-boundaries.md)
- [Runtime profile](runtime-profile.md)
- [Runtime tasks](runtime-tasks.md)
- [Requirements checklist](checklists/requirements.md)
- [Hybrid-runtime checklist](checklists/hybrid-runtime.md)
- [Reviewed baseline](evidence/spec-baseline.json)
- [Spec Kit manifest](evidence/spec-kit-manifest.json)

## Branching

The specification is intended for `feature/admin-ui-spec`, based directly on
`main`. Implementation belongs in a later branch after specification review.
