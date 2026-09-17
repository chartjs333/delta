# Pairwise Review Draft Contract

## Scope and authority

This is a presentation-layer structural contract for UX Amendment 001. It is not a
Delta protocol type, canonical schema, governance decision, validator result, or
independence rule. `DataSourcePort` is unchanged.

## Draft structures

```text
ControllerFormState
  draftControllerKey: opaque session-local stable ID
  controllerId: editable string or absent

PairwiseReviewDraft
  pairKey: canonical unordered key of two draftControllerKey values
  memberKeys: exactly two distinct draftControllerKey values
  controllerIdSnapshots: controller IDs shown when the record was last accepted
  answers:
    sharedPrivateKey: YES | NO | UNKNOWN | UNANSWERED
    sharedAdministrator: YES | NO | UNKNOWN | UNANSWERED
    sharedRecoveryOrBackupAccess: YES | NO | UNKNOWN | UNANSWERED
  evidenceReferences: ordered list of inert strings
  state: ACTIVE | STALE | ORPHANED
```

`draftControllerKey` and `pairKey` are presentation identifiers. They carry no
controller, signer, governance, or protocol authority and are not exported unless
an explicitly selected schema defines their representation.

## Pair formation

- Generate one record for each unordered pair of distinct active controller drafts.
- Pair cardinality is `n × (n − 1) / 2`; it is never hard-coded to six.
- Canonical `pairKey` ordering uses the two stable draft keys, not array index,
  display order, slot, display name, or editable controller ID.
- Reordering controllers does not change pair identity.
- Duplicate or blank controller IDs are structural attention items; they do not
  cause records to merge.

## Completion and language

- `YES`, `NO`, and `UNKNOWN` each count as an answered question.
- `UNANSWERED` does not count as answered.
- A record is filled only when all three questions are answered.
- Evidence references may be empty unless the selected structural schema requires them.
- Completion is not verification. The UI says "pairwise record filled", never
  "independence verified/confirmed", `PASS`, or `FAIL`.
- Any verdict display comes from a separate, matching external `SourcedResult` and
  includes authority, subject, time, and provenance.

## Lifecycle

| Event | Required state/behavior |
| --- | --- |
| Both members exist and ID snapshots match | `ACTIVE` |
| Either editable controller ID differs from its snapshot | `STALE`; retain answers/evidence; require explicit review |
| Either member draft is deleted | `ORPHANED`; retain answers/evidence; do not silently rebind |
| Controller is re-added with a new draft key | Old records remain `ORPHANED`; create new pairs |
| Controllers are reordered | State and pair key remain unchanged |
| User explicitly accepts current IDs | Refresh snapshots and return eligible record to `ACTIVE` |

Deleting, retargeting, or merging evidence requires an explicit user action. Array
position, historical slot number, or matching display text never authorizes rebinding.

## Projection and export

- Form changes patch the single `DocumentDraft`; they do not rebuild it from known fields.
- Unknown schema-allowed document fields survive unchanged.
- Pairwise records enter exported JSON only when a reviewed, versioned mapping is
  explicitly supported by the selected schema descriptor.
- `STALE` and `ORPHANED` records never serialize as active records. The UI blocks or
  omits their pairwise projection only with an explicit warning and user resolution;
  it never silently rewrites evidence.
- The historical PR #29 `slots` fixture may test import compatibility but cannot
  define dynamic pair identity, lifecycle, or cardinality.

## STOP condition

If correct projection requires a Delta-canonical schema, canonical validator,
protocol/runtime change, or semantic independence decision, implementation stops.
