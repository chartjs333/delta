# DataSourcePort Contract

## Purpose

`DataSourcePort` isolates domain views from local files, future network APIs,
credentials, and Delta runtime internals. This is a behavioral contract, not a
language-level API selection.

## Required MVP operations

| Operation | Required behavior |
| --- | --- |
| `describeSource()` | Return adapter ID, authority class, connection/freshness state, entity types, and capabilities |
| `listSchemas()` | Return available canonical schema descriptors |
| `loadSchema(id, version)` | Return the exact schema or typed not-found/unsupported error |
| `openDocument()` | Return JSON bytes/value plus origin metadata |
| `validateStructure(document, schemaRef)` | Return structural errors with machine paths |
| `saveDocument(document)` | Save only when supported, without implying approval |
| `exportDocument(document)` | Produce JSON preserving allowed unknown fields |
| `listSourcedResults(subjectRef)` | Return attributable results only when supported |

## Capability vocabulary

Initial UI-level names, subject to review before implementation:

| Capability | Meaning |
| --- | --- |
| `document.read` | Open a document |
| `document.write` | Save a document |
| `document.export` | Export a document |
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
- document malformed;
- document structurally invalid;
- data stale;
- capability contract violated;
- subject/provenance mismatch.

Every failure maps to a non-crashing presentation state.
