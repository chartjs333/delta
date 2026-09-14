# Security Boundaries

## Trust model

The admin UI is not a trusted Delta protocol component. Its display helps an
operator inspect data but is not proof of validity, appointment, signing authority,
governance approval, or current checkpoint state.

## Client-visible exclusions

The client must never receive private keys, signing secrets, HSM/KMS credentials,
recovery material, service credentials, or restricted evidence outside the user's role.

## MVP actions

Local import, editing, structural validation, save, and export do not appoint a
controller, authorize execution, create a signature, or record governance approval.
The UI must not label those actions as such.

## Validation boundary

- Client-side validation is feedback, not authority.
- Data sent to an external service must be revalidated at a trusted boundary.
- Structural schema success does not imply protocol validity or governance readiness.
- Semantic protocol validation remains in the canonical Delta owner.
- Governance assessments remain attributable to their governance authority.

## Provenance

A displayed sourced result should preserve result type, subject, source, authority
class, issued/retrieved times, applicable schema/policy/verifier revision, and
evidence/signature references when available.

Insufficient provenance is displayed as unverified/insufficient, never as canonical.

## Failure behavior

Missing API, validator, authority, or partial data produces degraded/read-only
behavior. UI failure never changes Delta runtime state. State-changing operations
require a later threat model, authorization design, formal-impact review, and
separate scope approval.
