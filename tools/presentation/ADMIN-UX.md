# Guided Admin UI — T051 / HR010-001

Pre-implementation Constitution Check: presentation-only change, formal impact
NONE. The accepted baseline report verifies as GO with SHA-256
`3e2e2344a038b2c902b06d275fb3e3820f95e5a780c2750e5c1a367dd82936d7`
and semantics `cc98f15a…`. This does not authorize the separate arithmetic candidate.

The guided view uses the existing intent builder and LiveExecutionPort for a
user-triggered synthetic CPU TRAIN_TICKET. It changes no admission, canonical
payload rules, role authority, transport, native state, certificate or durability
semantics. Status and receipt come from the existing adapter. Missing/failed
responses must never render a verified result. A schematic protocol explanation
is separate from observed local execution; no ISC/ApplyQC/checkpoint is fabricated.

The existing technical views remain available. Both languages share the same
controls and data; display translation cannot rewrite evidence. Controller JSON
remains a local worksheet; guided execution does not make it live configuration.

Validation: meaningful UI tests for submission, result gating, read failures,
language changes and request lifetime; existing Admin check and live boundary
audit; browser execution and bilingual layout review.

Final Constitution Check: PASS within UI-only scope. No formal, protocol, native,
FFI, Java or Worker files changed. The installed source is
`4f6682451882358a6af26786982e81fa7b56728d`. All 249 tests in 40 files, the offline
build/audit and live build/audit pass. Browser review confirmed English/Russian,
automatic status and receipt retrieval, six interactive explanatory stages, and
the primary action visible at the laptop's normal viewport. No responsive-device
qualification is claimed. The Controller was not restarted.

Browser execution `04729563-03b7-4c13-a969-fbdbc8101ede` completed using source
`3ea3430` (the final change only repositioned controls). The downloaded JSON's
SHA-256 equals the Controller's receipt digest:
`165fa93ab5f3609f518ea320ab65f03d40bd5ddd2688502ccc7f6e3a054e87cb`.
Acceptance and original result records are retained in
`specs/010-wan-benchmark-and-quality/evidence/presentation-local/20260923/admin-guided/`.
Review is self-review; Feature010 qualification remains open.


## Shared local profile and field help — 2026-09-24

T051 / HR010-001. Pre-implementation Constitution Check: presentation metadata
and UI only; semantic impact NONE. The accepted baseline FormalVerificationReport
was reverified as GO (report SHA-256 `3e2e2344a038b2c902b06d275fb3e3820f95e5a780c2750e5c1a367dd82936d7`).
This does not authorize the arithmetic candidate or native runtime work.

The presentation host serves the Admin build at `/admin/` and forwards only the
fixed existing readiness/intent/status/receipt/cancel HTTP routes to the baseline
Controller. The browser keeps same-origin CSP and the original write marker.
The old 8865 UI entry redirects to this shared workspace, preserving language,
route and execution ID. Controller source and process remain unchanged.

`panel/workspace.json` stores a bounded local profile: language, profile name,
controller-register document, campaigns, selected supported workload, and actual
intent/execution bindings. Atomic replacement and revision comparison reject
lost updates. A failed save blocks a new submission. A corrupt profile is not
silently reset. This is a local workstation profile, not authentication or
independent governance. Pairwise review worksheets still require explicit export.

Campaigns link actual runs. Admin and Presentation fetch status/receipts from
the same Controller and check lineage/digest before offering a verified receipt.
Presentation downloads canonical receipt bytes. Saved run metadata cannot assert
success if the Controller is unavailable. Only the baseline's supported synthetic
10-gene PLUGIN_BOUNDARY workload is enabled in the shared profile; other catalog
entries remain browsable with an explicit unsupported message.

Every editable form field and read-only input has a clickable help control,
including profile/campaign forms and advanced intent fields. English/Russian hints
explain purpose, constraints and examples without changing data. Keyboard Enter,
Escape, focus restoration and outside-click dismissal are supported. Help buttons
sit outside labels, so clicking help cannot toggle checkboxes or change input names.

Self-review validation before installation: 257 tests / 42 files, TypeScript,
offline build/audit, live build/audit; 15 Python presentation tests; Ruff and JS
syntax check. Python tests cover disk restore, conflicting revisions, failed
atomic replacement, corrupted files, origin/write headers, fixed proxy routes,
receipt digest/lineage mismatch and canonical downloads. Windows rejected-body
handling drains only a bounded declared body so a 403 is not lost to socket reset.
Browser acceptance and installed-source identities are recorded separately.
