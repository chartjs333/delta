# Delta R2.3 — storage source contract decision

6 October 2026. T047/T053 / ISC-S16-D01. **R2.3 OPEN; Formal NO_GO.**

The existing sprint continues; this is a semantic attention point, not a new
sprint, graph reset or terminal completion. Full R2.3 remains authorized.

## Preserved result and reviews

- Human scope5 decision `scope-decision-dff5cf14af975d7da34f29cfdc4a55c1`
  approved exact ADR0015 sections 3–7 for isolated future reference work.
- Worker `e766ef98748504779a9a88d06ee3760594c4184d`, branch
  `agent/isc-s16-formal-linkage`, follows `4c99272e` and implements only a
  separate non-ISC Vn/Mn/Gn signature reference with pinned strict Ed25519.
  Tests and exact Git-blob source/log/vector/receipt hashes were checked.
- Assignment `91d05d0d-4fca-43e6-bd5e-7442d77e4ec0` returned NEED_DECISION.
  Transition `d90be72d-67da-4ed6-9fe1-4bba5620e1a6` received APPROVE from
  architecture assignment `e607625c-db3c-4e26-8123-42143abe564b` and evidence
  assignment `0babcee4-8bb0-4196-92d1-7579c8952848`.
- These sequential same-executor reviews approve the bounded checkpoint and
  routing. They do not attest R2 closure, complete qualification or Formal GO.
- Current coordinator assignment `6a4e2acb-444f-45dd-aa08-8b4c4741a39c`,
  execution revision152, scope5; exact ACK
  `scope-ack-135f9bc85ae47d69b5be53a94b751974` saved and GET-confirmed.
  Official whoami delivery was confirmed by public HTTP state after the client
  timed out; no local nginx runtime/queue was read.

The exact worker explanation and immutable audit are in that commit at
`formal/proposals/non-isc-source-checkpoint.md` and
`formal/proposals/evidence/non-isc-source-v1/availability-boundary.json`.
No old artifact or signature is relabeled. Body/certificate/producer-cut and
full source composition are still unproved; the reference does not assert them.

## Decision boundary

Original feature003 FR-014/015 requires valid storage attestations for exact
shards, lengths and retention epoch before input freeze. The native six-field
AvailabilityProof API checks IDs, coverage and threshold; it does not receive or
authenticate the missing original storage evidence. Equal API arguments cannot
distinguish genuine attestations from absent/stale ones. This is a source API
insufficiency argument, **not a proven production-reachable forged history**.

Profile v1 requires verified producing history from genesis. ADR0015 explicitly
preserves storage authority separately from validator vote signing. Neither the
trusted volume nor NSG1 can silently supply the missing contract. A new exact
source/authority/codec choice is outside ordinary proof engineering.

Register the structured request in
`scope-requests/ISC-S16-R23-STORAGE-AUTHORITY-DECISION.json` through the current
role's Pending decisions API. It requests one concrete specification document,
or an existing exact immutable contract/evidence reference. It **does not**
approve a new storage trust root, algorithm, byte format, producer rule,
implementation or proof assumption. A proposed document needs its own exact
semantic approval before use. No repeat consent for general R2.3 is requested.

Until a real decision is applied, retain this assignment, scope/ACK and review
history. No fabricated approval, admin fallback, raw amendment, RESUME to bypass
the pending decision, new sprint or graph reimport. After application, read the
actual role's effective scope, verify source/core hashes and precedence, exact
ACK and GET persistence before the newly authorized bounded work.

R1/R2.1/R2.2 stay CLOSED for their old domain. Recovery theorem/full R3,
production integration, guard removal and concrete sigma remain untouched.
Healthy demo8870,8865 and8872 `/node-training/api/health` returned HTTP200;
no service was restarted. Foreign D:/delta files and frozen refs are preserved.
