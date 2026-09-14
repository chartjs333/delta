# Architecture: Extensible Administrative Shell

## Dependency direction

The admin UI depends on public contracts and sources. Delta never depends on the UI.

```mermaid
flowchart TD
    A["Browser-local shell and modules"] --> B["DataSourcePort"]
    B --> C["LocalJsonAdapter — MVP"]
    B -. later .-> D["DeltaApiAdapter"]
    D --> E["Public Delta API"]
```

The UI must not call native C ABI/FFM entry points, inspect C++ runtime state, or
reconstruct protocol semantics from transport effects.

## Layers

### Shell

Owns layout, navigation, theme, global notifications, source selection, and shared
loading/error behavior. It contains no domain verdicts. Login, authorization, and
credential handling are absent from the browser-local MVP and enter scope only with
a separately reviewed remote adapter.

### Domain modules

Own routes and views for one area. Initial module: `controllers`. Reserved future
areas: `campaigns`, `nodes`, `artifacts`, and `audit`.

### Presentation models

Adapt source documents for display. Any derived value is presentation-only,
traceable to its inputs, and never exported as canonical data unless the governing
schema explicitly defines it.

### DataSourcePort

The only domain-facing data boundary. It exposes source descriptors, schema
descriptors, documents, capabilities, and sourced results through stable contracts.

### Adapters

`LocalJsonAdapter` enables the offline MVP. A future `DeltaApiAdapter` may consume
public APIs after those APIs have stable contracts. Adapters do not repair,
complete, or semantically reinterpret source data.

The MVP is browser-local and has no backend. It reads files selected by the user
and creates explicit downloads; it does not fetch live GitHub content, call Delta,
or silently overwrite the selected input file.

## Extension points

| Extension ID class | Purpose | Required descriptor fields |
| --- | --- | --- |
| `navigation` | Add a route/menu entry | stable ID, label, route, permission |
| `domain-module` | Add a bounded feature area | stable ID, routes, views, required capabilities |
| `entity-view` | Add table/card/graph/timeline views | entity type, view ID, input contract, fallback |
| `dashboard-widget` | Add an overview widget | stable ID, data requirements, empty/error behavior |
| `data-adapter` | Add a source | adapter ID, authority class, capabilities, lifecycle |
| `visualization` | Add a renderer | renderer ID, input contract, unsupported fallback |

Extensions are registered at a documented composition root. Editing that registry
is expected; editing unrelated modules is not.

## Authority classes

The presentation must keep these classes distinct:

1. `LOCAL_DRAFT`: operator-authored or imported bytes with no asserted authority.
2. `STRUCTURAL_VALIDATION`: schema conformance only.
3. `OBSERVATION`: sourced operational data without protocol finality.
4. `GOVERNANCE_ASSESSMENT`: a result attributed to an identified governance authority.
5. `PROTOCOL_RESULT`: a result provided by a canonical Delta validator/API/artifact.

The UI cannot promote data to a stronger authority class. A result can be displayed
only with its subject binding and provenance.

Schema authority is a separate, mandatory property of `SchemaDescriptor`:

1. `GOVERNANCE_DOCUMENT`: a schema owned by an identified governance authority.
2. `DELTA_CANONICAL`: a schema owned by the canonical Delta contract authority.
3. `LOCAL_FIXTURE`: a bundled or user-selected schema used only for local/test work.

An authority class describes the schema, not the validity or approval of a document
instance. In particular, validation against a `LOCAL_FIXTURE` never upgrades the
document to governance or protocol authority.

## Governance/protocol document separation

The first scenario contains two different document types:

```mermaid
flowchart TD
    G["Controller Governance Register"] --> R["External review / approval"]
    R --> V["Bootstrap Validator Set"]
    V --> C["Canonical Delta validation"]
```

The arrows describe a possible externally governed workflow, not UI transitions.
The UI may display explicit references between exact revisions, but it must never
derive a bootstrap validator set from the register, claim that approval occurred,
or infer that the register authorizes protocol execution.

The PR #29 worksheet is `CONTROLLER_GOVERNANCE_REGISTER`-class input for the UI.
Until a governance authority publishes and owns a schema for it, a companion schema
used by the implementation is classified `LOCAL_FIXTURE`. The existing
`CAMPAIGN02_WORKFLOW_BOOTSTRAP_VALIDATOR_SET` schema is `DELTA_CANONICAL` and must
not be used to validate that worksheet.

## Compatibility

- Canonical schemas are addressed by ID and version.
- Every schema is addressed by a descriptor containing `schemaId`, `version`,
  `authorityClass`, `documentType`, and `source`.
- Unsupported schema versions fail explicitly.
- Unknown allowed fields survive import/export.
- Unknown capabilities are ignored safely.
- Adapter errors are localized and mapped to typed presentation states.
- Visualization inputs retain source and retrieval metadata.
