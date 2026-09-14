# Logical Data Model

This model supports navigation and presentation. It neither creates canonical
Delta types nor supersedes schemas in `delta-protocol`.

## Controller

Potential source fields include canonical ID, display label, identity type,
public-key identifiers, public custody metadata, evidence references, sourced
statuses, timestamps, and document version. Exact fields come from the selected schema.

The collection is unbounded by the UI. A four-controller `f_b=1` worksheet from
PR #29 is one fixture, not the generic cardinality.

## DocumentDraft

The sole in-memory document state used by guided forms, structural validation,
advanced JSON preview, and export. Known-field edits patch this draft while retaining
schema-allowed unknown fields. The advanced JSON projection is not a second editor.

## ControllerFormState

A presentation projection with a stable, session-local `draftControllerKey` plus
labels and field paths for one controller. The stable key is not protocol identity
and is not exported unless an explicitly selected document schema defines it.

## PairwiseReviewDraft

A presentation-only record for one unordered pair of stable controller draft keys.
It contains three independently entered `YES`, `NO`, or `UNKNOWN` answers, zero or
more evidence references, controller-ID snapshots, and lifecycle state `ACTIVE`,
`STALE`, or `ORPHANED`. It contains no independence verdict. See
`contracts/pairwise-review-draft.md`.

## Campaign

A source-defined view of a coordinated process or round. Relationships may include
nodes, contributions, aggregate artifacts, status history, and audit events.

## Node

A source-defined view of a participant and observable status. The UI does not infer
trust, eligibility, or validator membership from labels or connectivity.

## Artifact

A content-addressed or externally referenced result. Presentation distinguishes
metadata, content reference, provenance, availability observation, and verification result.

## AuditEvent

An immutable event view with event ID, timestamp/logical time, actor, action,
target, outcome, correlation ID, and evidence/artifact references when supplied.

## SourceDescriptor

Identifies an adapter instance and its authority class, capabilities, connection
state, supported schemas/entity types, freshness, and retrieval metadata.

## SchemaDescriptor

Identifies a schema without collapsing governance and protocol authority:

| Field | Meaning |
| --- | --- |
| `schemaId` | Stable schema identifier within its declared authority |
| `version` | Exact schema version |
| `authorityClass` | `GOVERNANCE_DOCUMENT`, `DELTA_CANONICAL`, or `LOCAL_FIXTURE` |
| `documentType` | Exact type of document the schema validates |
| `source` | Immutable or version-bound provenance for the schema bytes |

For the first MVP, `CONTROLLER_GOVERNANCE_REGISTER` and
`CAMPAIGN02_WORKFLOW_BOOTSTRAP_VALIDATOR_SET` are different document types. The
latter's canonical schema cannot be reused for the former.

## SourcedResult

Contains result type, outcome, exact subject reference, authority class, source
reference, issued/retrieved times, verifier or policy revision when available,
and evidence/signature references when available.

## Relationships

```mermaid
flowchart TD
    C["Campaign"] --> N["Node"]
    C --> A["Artifact"]
    N --> A
    R["Controller"] --> A
    E["AuditEvent"] --> C
    E --> A
```

Relationships require explicit IDs/references. Display-name coincidence does not
establish a relationship.
