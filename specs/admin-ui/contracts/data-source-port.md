# DataSourcePort Contract

## Purpose

`DataSourcePort` isolates domain views from local files, future network APIs,
credentials, and Delta runtime internals. This is a behavioral contract, not a
language-level API selection.

## Required MVP operations

| Operation | Required behavior |
| --- | --- |
| `describeSource()` | Return adapter ID, authority class, connection/freshness state, entity types, and capabilities |
| `listSchemas()` | Return available `SchemaDescriptor` values without filtering authority classes together |
| `loadSchema(descriptor)` | Return exact schema bytes matching every descriptor field or a typed mismatch/not-found/unsupported error |
| `openDocument()` | Return JSON bytes/value plus origin metadata |
| `validateStructure(document, schemaRef)` | Return structural errors with machine paths |
| `exportDocument(document, suggestedName)` | On explicit user action, create a new download preserving allowed unknown fields |
| `listSourcedResults(subjectRef)` | Return attributable results only when supported |

Every `SchemaDescriptor` contains exactly these required semantic fields:
`schemaId`, `version`, `authorityClass`, `documentType`, and `source`. The source
must bind the exact schema bytes through an immutable revision and/or digest.

Schema authority classes are `GOVERNANCE_DOCUMENT`, `DELTA_CANONICAL`, and
`LOCAL_FIXTURE`. Adapters must match both `documentType` and `authorityClass`;
schema ID/version equality alone is insufficient.

## Capability vocabulary

Initial UI-level names, subject to review before implementation:

| Capability | Meaning |
| --- | --- |
| `document.read` | Open a document |
| `document.export` | Explicitly download a new document; never overwrite the input |
| `schema.enumerate` | List available schemas |
| `schema.validate.structure` | Perform structural schema validation |
| `controller.list` | Present a controller collection |
| `governance.controller-independence.read` | Read an externally authored independence assessment |
| `governance.signing-readiness.read` | Read an externally authored signing-readiness assessment |
| `protocol.validation-result.read` | Read a canonical protocol validation result |
| `campaign.read` | Read campaigns |
| `node.read` | Read nodes |
| `artifact.read` | Read artifacts |
| `audit.read` | Read audit events |
| `events.subscribe` | Receive a source event stream |

Capability names describe UI availability; they do not add protocol feature bits
or change the C ABI.

## LocalJsonAdapter

The MVP adapter may declare document and structural-validation capabilities. It
may derive `controller.list` only after the selected document structurally matches
the corresponding schema.

It does not declare `document.write`, perform background persistence, read a live
GitHub PR, fetch external schema references, or send document bytes to a service.
Its controller-register fixture is copied from the exact pinned PR #29 revision
into the implementation branch with SHA-256 metadata and remains test data only.

The PR #29 worksheet and the Delta bootstrap validator set are distinct document
types. The adapter must reject a schema/document type mismatch and must not derive,
approve, or authorize one document from the other.

It must not declare governance/protocol result capabilities merely because arbitrary
local JSON contains a result-looking field. If a fixture includes a sourced-result
envelope, the UI preserves and displays its asserted provenance without independently
upgrading or confirming it.

## Future DeltaApiAdapter

The adapter declares only capabilities actually supported by a stable public API.
Missing endpoints, inaccessible authorities, or incompatible responses become typed
errors, not local fallback verdicts.

## Typed failures

- source unavailable;
- operation unsupported;
- access denied;
- schema not found;
- schema version unsupported;
- schema authority or document-type mismatch;
- document malformed;
- document structurally invalid;
- data stale;
- capability contract violated;
- subject/provenance mismatch.

Every failure maps to a non-crashing presentation state.
