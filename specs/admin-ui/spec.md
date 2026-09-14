# Feature Specification: Extensible Delta Admin UI

**Feature Branch**: `feature/admin-ui-spec`  
**Created**: 2026-09-14  
**Status**: MVP implemented; UX Amendment 001 reviewed  
**Depends on**: `main`; PR #29 is a non-normative MVP input

## Summary

Delta needs an optional administrative interface that can grow from a local
schema-valid document editor into a coherent console for controllers,
campaigns, nodes, artifacts, audit events, and system visualizations. The UI is
a one-way consumer of public contracts and sourced results. It never becomes a
protocol authority or a dependency of Delta core/runtime.

JSON remains the internal/import/export representation. The default non-technical
workflow is a guided form over a single document draft; raw JSON is advanced and
read-only. Controller-independence, governance readiness, signing
readiness, and other semantic outcomes are not computed by the UI. They appear
only when a declared source supplies an attributable result.

The controller governance register and the canonical bootstrap validator set are
different documents. A governance workflow may explicitly relate exact revisions,
but the UI never converts one into the other or treats register review as protocol
authorization.

## User Scenarios & Testing

### US1 — Create a controller register without editing JSON (Priority: P1)

An operator opens or creates a controller register, completes understandable guided
fields for a dynamic controller list, receives field-level structural feedback, and
explicitly downloads a new JSON document without needing to view or edit JSON and
without changing the original file, protocol state, or governance state.

**Independent Test**: Run with only the local JSON adapter and no Delta runtime,
network service, validator, key, or credential.

**Acceptance Scenarios**:

1. **Given** a valid document and matching schema, **When** it is opened, **Then**
   all controller entries are shown and the document is reported structurally valid.
2. **Given** a document with zero, one, four, or more controllers, **When** it is
   edited, **Then** no fixed four-slot assumption affects behavior or layout.
3. **Given** an invalid field, **When** validation runs, **Then** the error names
   the violated schema rule and machine-readable document path.
4. **Given** valid unknown fields allowed by the schema, **When** the document is
   exported, **Then** those fields survive the round trip.
5. **Given** the PR #29 governance worksheet and the canonical bootstrap validator-set
   schema, **When** validation is requested, **Then** the UI rejects the document-type
   mismatch rather than treating the worksheet as a protocol document.
6. **Given** a downloaded export, **When** the workflow completes, **Then** the
   originally selected file has not been overwritten by the UI.
7. **Given** schema-allowed fields unknown to the form, **When** known fields are
   changed and exported, **Then** the unknown fields remain byte-value equivalent.
8. **Given** the default controller workflow, **When** a non-technical user completes
   it, **Then** no raw JSON editing action is required or presented as primary.

### US5 — Record pairwise answers without creating a verdict (Priority: P1)

An operator answers three understandable questions for each dynamically derived
unordered controller pair, attaches evidence references, and sees structural
completion without the UI deciding whether the controllers are independent.

**Independent Test**: Use 0, 1, 2, 4, and 100 controller drafts with no sourced
governance results and verify pair counts, language, and lifecycle behavior.

**Acceptance Scenarios**:

1. **Given** four current controller drafts, **When** the pairwise step opens,
   **Then** six unordered pairwise records are offered without a hard-coded slot model.
2. **Given** `YES`, `NO`, or `UNKNOWN` for every question in a pair record, **When**
   summary is shown, **Then** it says the pairwise record is filled and does not say
   the pair is verified, confirmed, independent, passed, or failed.
3. **Given** an editable controller ID changes, **When** an existing record references
   that controller's stable draft key, **Then** the record becomes `STALE` and evidence
   is not silently retargeted.
4. **Given** a controller is removed, **When** its pair records remain in draft state,
   **Then** they become `ORPHANED` and cannot be silently exported as active records.
5. **Given** an external independence result with matching subject and provenance,
   **When** it is displayed, **Then** its supplied verdict is visually separate from
   locally entered answers and completion counts.

### US2 — Distinguish unavailable outcomes from failed outcomes (Priority: P1)

An operator can tell whether a check failed, has not run, is unsupported by the
current source, or is merely present as untrusted local data.

**Independent Test**: Supply adapters with different capability sets and verify
that the UI does not manufacture or upgrade results.

**Acceptance Scenarios**:

1. **Given** a source without an independence-assessment capability, **When** the
   controller view opens, **Then** the UI reports the assessment as unavailable,
   not failed or passed.
2. **Given** a sourced governance assessment, **When** it is displayed, **Then**
   its authority class, subject, timestamp, and provenance reference are visible.
3. **Given** arbitrary JSON containing a `PASS` string, **When** no trusted result
   envelope or capability exists, **Then** the UI does not present it as a
   canonical governance or protocol verdict.

### US3 — Add a domain view through defined extension points (Priority: P2)

A developer adds a future campaign, node, artifact, audit, topology, timeline, or
diagnostic view through a documented composition point without changing Delta
core or rewriting the controller module.

**Independent Test**: Register a placeholder domain module and one alternate
entity view using only the documented extension contracts.

**Acceptance Scenarios**:

1. **Given** a new module descriptor, **When** it is registered at the composition
   root, **Then** its route and navigation entry appear without controller-module changes.
2. **Given** a visualization whose data capability is absent, **When** its page is
   opened, **Then** an explicit unavailable state is shown without application failure.

### US4 — Replace local files with a future API source (Priority: P2)

An operator can select a future public Delta API adapter without requiring domain
views to understand transport, credentials, or runtime-internal types.

**Independent Test**: Run contract tests against two in-memory adapters with
different capabilities and equivalent controller documents.

**Acceptance Scenarios**:

1. **Given** equivalent local and API documents, **When** adapters are switched,
   **Then** the controller list/detail views retain the same presentation behavior.
2. **Given** an unavailable API, **When** data is requested, **Then** the UI enters
   a degraded or stale state and Delta runtime remains unaffected.

## Edge Cases

- Empty documents, empty controller arrays, and very large controller arrays.
- Missing, unknown, incompatible, or superseded schema versions.
- Structurally invalid JSON that must remain editable without data loss.
- Unknown fields permitted by the selected schema.
- An adapter that advertises a capability but returns a malformed response.
- A result whose subject does not match the displayed document revision.
- Conflicting governance and protocol results from different authorities.
- Offline, stale, partial, or access-denied sources.
- Routes or widgets that require capabilities unavailable from the active adapter.
- Oversized, deeply nested, high-node-count, or giant-string JSON documents.
- HTML/script/template text, suspicious URLs, huge Base64-like strings, and external `$ref` values.
- Controller IDs that are blank, duplicated, edited after pair entry, or deleted.
- Pair records whose members are stale, orphaned, reordered, or re-added with a new draft key.
- Explicit `UNKNOWN` answers versus questions that have not been answered.
- Historical PR #29 slot pairs whose shape cannot define the dynamic product model.

## Requirements

### Functional Requirements

- **FR-001**: The MVP MUST open, create, edit, structurally validate, view, and
  export local JSON documents.
- **FR-002**: Every selectable schema MUST use a `SchemaDescriptor` containing
  `schemaId`, `version`, `authorityClass`, `documentType`, and immutable/digested `source`.
- **FR-003**: Structural errors MUST include a machine-readable document path and
  the violated schema constraint.
- **FR-004**: Controller collections MUST be dynamic; the UI MUST NOT encode four
  slots or six pair checks as a general product rule.
- **FR-005**: A valid import/export round trip MUST preserve fields that the schema
  permits even when the current UI has no specialized control for them.
- **FR-006**: Domain modules MUST obtain data and capabilities through the
  `DataSourcePort`, not from Delta runtime internals.
- **FR-007**: The active adapter MUST declare supported capabilities.
- **FR-008**: A capability-dependent function MUST be unavailable or hidden when
  the active adapter does not declare its capability.
- **FR-009**: The UI MUST distinguish structural validation, governance assessment,
  protocol result, observation, and local draft data.
- **FR-010**: A sourced assessment/result MUST retain authority class, subject
  reference, source reference, retrieval time, and available verification metadata.
- **FR-011**: The UI and any administrative backend MUST NOT compute quorum,
  controller independence, signing eligibility/readiness, custody compliance,
  campaign transitions, aggregation, contribution meaning, or other Delta semantics.
- **FR-012**: The UI MAY sort, filter, group, and visualize data, but MUST identify
  derived presentation data and MUST NOT alter the canonical document silently.
- **FR-013**: The shell MUST define localized registration points for navigation,
  domain modules, entity views, dashboard widgets, data adapters, and visualizations.
- **FR-014**: Registering an extension MAY update the composition root; it MUST NOT
  require rewriting unrelated domain modules or modifying Delta core.
- **FR-015**: Loading, empty, invalid, error, degraded, stale, unsupported, and
  access-denied states MUST be distinguishable.
- **FR-016**: PR #29 artifacts MAY be used as fixtures only when their status and
  provenance are preserved; the four-slot worksheet MUST NOT become the generic model.
- **FR-017**: The UI MUST keep `CONTROLLER_GOVERNANCE_REGISTER` and
  `CAMPAIGN02_WORKFLOW_BOOTSTRAP_VALIDATOR_SET` as distinct document types and MUST
  reject schema/document authority or type mismatches.
- **FR-018**: Schema authority classes MUST include `GOVERNANCE_DOCUMENT`,
  `DELTA_CANONICAL`, and `LOCAL_FIXTURE`; validation MUST NOT promote document authority.
- **FR-019**: The UI MUST NOT derive a bootstrap validator set, governance approval,
  signing eligibility, or execution authorization from a governance register.
- **FR-020**: The MVP MUST persist changes only through an explicit new-file
  download/export and MUST NOT silently or automatically overwrite the input file.
- **FR-021**: The implementation MUST freeze the exact PR #29 fixture revision and
  SHA-256 in its own test data; it MUST NOT read the live PR as a contract or source of truth.
- **FR-022**: The MVP MUST treat all imported JSON and schema bytes as untrusted,
  enforce `threat-model.md` limits, and render input strings only as inert text.
- **FR-023**: The MVP MUST NOT automatically fetch URLs or external schema references.
- **FR-024**: The MVP MUST operate without a backend, login, authorization flow,
  network service, runtime, key, or credential.
- **FR-025**: The default controller workflow MUST be guided and form-first; users
  MUST NOT need to read or edit JSON to complete it.
- **FR-026**: Raw JSON MUST be hidden by default and read-only in this increment,
  and MUST project the same `DocumentDraft` used by forms, validation, and export.
- **FR-027**: Known-field form changes MUST patch `DocumentDraft` without rebuilding
  it from recognized fields or dropping schema-allowed unknown fields.
- **FR-028**: Pairwise records MUST be derived from unordered pairs of the dynamic
  controller draft set and MUST NOT assume four slots or six pairs.
- **FR-029**: A pairwise record MUST store answers and evidence references but MUST
  NOT contain, compute, or imply an independence verdict.
- **FR-030**: `YES`, `NO`, and `UNKNOWN` are completed answers; absence of an answer
  is incomplete. Summary language MUST say records are "filled" or "not filled".
- **FR-031**: "Verified", "confirmed", "approved", "pass", "fail", and equivalent
  verdict language MUST appear only for a matching external `SourcedResult` with provenance.
- **FR-032**: Controller identity edits and removal MUST produce explicit `STALE`
  or `ORPHANED` pair records; the UI MUST NOT silently retarget or delete evidence.
- **FR-033**: Friendly field errors MUST retain the original JSON path, schema path,
  and constraint in an accessible details view.
- **FR-034**: T032–T039 MUST NOT modify `DataSourcePort`, offline behavior, schema-
  validation authority, or explicit new-file export behavior.
- **FR-035**: The frozen PR #29 fixture MUST remain historical test input and MUST
  NOT become the normative structural model for dynamic controller pairs.
- **FR-036**: Active pairwise records MAY enter exported JSON only through an
  explicitly reviewed, versioned structural mapping supported by the selected schema.
  `STALE` and `ORPHANED` records MUST never be silently exported as active records.

### Non-Functional Requirements

- **NFR-001**: Delta core/runtime MUST build, test, start, and operate without the UI.
- **NFR-002**: Removing the UI module MUST NOT change Delta protocol behavior.
- **NFR-003**: The specification and MVP MUST have formal impact `NONE`.
- **NFR-004**: The interface MUST remain usable with keyboard navigation and
  expose semantic labels for primary controls and statuses.
- **NFR-005**: Large collections MUST not require rendering every item at once.
- **NFR-006**: A failure in one adapter or extension MUST not crash the entire shell.
- **NFR-007**: Client-visible data MUST exclude private keys, signing secrets,
  HSM/KMS credentials, recovery material, and service credentials.
- **NFR-008**: Technology selection MUST be recorded separately and MUST satisfy
  this specification rather than narrowing it.
- **NFR-009**: Rejecting hostile or over-limit input MUST not crash the shell or
  expose document contents through analytics, telemetry, or exception reporting.
- **NFR-010**: A non-technical usability test participant MUST be able to add
  controllers, complete pairwise records, understand attention items, and export a
  structurally valid file without opening the advanced JSON view.

### Key Entities

- **Controller**: An administrative view of a controller identity and public metadata.
- **Campaign**: A view of a coordinated process or round as exposed by a source.
- **Node**: A view of a participating runtime identity and observable status.
- **Artifact**: Content-addressed metadata, provenance, and verification references.
- **AuditEvent**: An immutable event view with actor, action, target, outcome, and correlation.
- **SourceDescriptor**: Adapter identity, connection status, authority, freshness,
  supported entity types, and capabilities.
- **SchemaDescriptor**: Exact schema ID, version, authority class, document type,
  and source binding.
- **SourcedResult**: An attributable result bound to an exact subject and authority class.
- **DocumentDraft**: The single in-memory source for form projection, validation,
  advanced preview, and export.
- **PairwiseReviewDraft**: A non-authoritative answer/evidence record with explicit
  active, stale, or orphaned lifecycle state and no verdict.

## Success Criteria

- **SC-001**: The MVP completes US1 and US2 while Delta runtime is absent.
- **SC-002**: Tests cover controller lists of 0, 1, 4, and at least 100 entries.
- **SC-003**: Contract tests run unchanged against at least two adapter implementations.
- **SC-004**: No code search hit outside the admin UI points from Delta core/runtime
  to the UI module.
- **SC-005**: No UI test claims an independence, governance, or signing verdict
  without a sourced result envelope and matching capability.
- **SC-006**: A placeholder module and alternate entity view are registered through
  documented extension points without controller-module edits.
- **SC-007**: Tests cover dynamic pair counts for 0, 1, 2, 4, and 100 controllers.
- **SC-008**: No locally derived summary uses verdict language; with four controllers
  and six filled records it states "6 of 6 pairwise records filled".
- **SC-009**: Production-browser tests cover supported desktop/mobile widths and CSP
  with no `unsafe-eval` requirement.
- **SC-010**: At least one non-technical usability path completes form-to-export
  without opening or editing raw JSON.

## Assumptions

- Existing canonical schemas remain owned by `delta-protocol` or another explicit
  project authority; the UI does not fork them.
- The canonical bootstrap validator-set schema is
  `urn:deltareduce:schema:010:campaign-02:workflow-bootstrap-validator-set-v1`,
  version `1.0.0`; it is not the schema of the PR #29 governance worksheet.
- Until an identified governance authority owns a controller-register schema, the
  MVP companion schema is `LOCAL_FIXTURE`, not `GOVERNANCE_DOCUMENT` or `DELTA_CANONICAL`.
- PR #29 remains governance documentation with formal impact `NONE`; it does not
  itself create appointments, signatures, or execution authority.
- Public Delta APIs needed for later phases may not exist yet.
- The accepted MVP technology ADR does not constrain later adapter or visualization ADRs.

## Out of Scope

- Modifying protocol schemas, formal models, validators, or signed artifacts.
- Computing or authoring governance/protocol verdicts.
- Signing, key generation, appointment, rotation, revocation, or HSM/KMS operations.
- Direct FFM/native-runtime access from the UI.
- Live runtime control, state-changing administrative commands, or campaign execution.
- Adding a canonical schema to `delta-protocol` solely for the UI.
- Authentication, authorization, remote persistence, backend services, and API integration.
- Selecting a form or visualization library; those require separate implementation decisions.
- Editing raw JSON in UX Amendment 001.
- Defining governance meaning for pairwise answers or evidence references.
- Treating completion counts as independence, readiness, approval, pass, or fail.
