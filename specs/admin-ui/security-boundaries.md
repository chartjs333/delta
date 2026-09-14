# Security Boundaries

## Trust model

The admin UI is not a trusted Delta protocol component. Its display helps an
operator inspect data but is not proof of validity, appointment, signing authority,
governance approval, or current checkpoint state.

## Client-visible exclusions

The client must never receive private keys, signing secrets, HSM/KMS credentials,
recovery material, service credentials, or restricted evidence outside the user's role.

## MVP actions

Local import, editing, structural validation, and explicit export do not appoint a
controller, authorize execution, create a signature, or record governance approval.
The UI must not label those actions as such. The MVP does not silently overwrite
the selected input file; every persisted result is a user-initiated new download.

## Validation boundary

- Client-side validation is feedback, not authority.
- Data sent to an external service must be revalidated at a trusted boundary.
- Structural schema success does not imply protocol validity or governance readiness.
- Semantic protocol validation remains in the canonical Delta owner.
- Governance assessments remain attributable to their governance authority.
- Governance-register validation and bootstrap-validator-set validation use
  different `SchemaDescriptor.documentType` and authority classes.
- The UI never converts, promotes, or infers authorization from one to the other.
- Pairwise form answers and evidence references are local draft data. Their presence,
  completeness, or values never constitute an independence assessment or verdict.
- "Verified", "confirmed", "approved", and equivalent status language requires an
  external sourced result bound to the displayed subject and provenance.

## Browser-local MVP

- The MVP has no backend, login, authorization flow, or credential storage.
- It performs no automatic network requests, including external JSON Schema `$ref`
  resolution, URL previews, analytics, or live PR/branch reads.
- Input strings are inert text: never raw HTML, script, template source, or executable code.
- URLs are text by default and may open only after an explicit user action and
  allowlisted-scheme check.
- Exact hostile-input limits and validation behavior are defined in `threat-model.md`.
- The advanced JSON representation is read-only in UX Amendment 001, preventing a
  second unsynchronized editing path around guided controls.

## Provenance

A displayed sourced result should preserve result type, subject, source, authority
class, issued/retrieved times, applicable schema/policy/verifier revision, and
evidence/signature references when available.

Insufficient provenance is displayed as unverified/insufficient, never as canonical.

## Failure behavior

Missing API, validator, authority, or partial data produces degraded/read-only
behavior. UI failure never changes Delta runtime state. State-changing operations
require a later integration threat model, authorization design, formal-impact
review, and separate scope approval.
