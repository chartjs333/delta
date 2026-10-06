# Delta: ACK restored, reviewed source checkpoint, pending non-ISC decision

T047/T053. 2026-10-06, Europe/Berlin. **R2.3 OPEN / Formal NO_GO**.

## Verified continuation

The user reported the disk blocker resolved. Read-only HTTP confirmed the saved
sprint and reviewer assignment; no previously accepted worker result was resubmitted.
The exact reviewer scope was fetched and verified before ACK, then fetched again
to confirm `acknowledged=true` for the same complete context.

| Step | Assignment | Exact ACK |
|---|---|---|
| Architecture review, role 2791 | `a20ea0d7-474d-4a8e-824c-67f64a554d13` | `scope-ack-ebfbe2ed0446353ac0b94ef571d0b9ef` |
| Evidence review, role 2792 | `ad0e59f9-9e82-4c1c-9cb7-eb8f4150d4fa` | `scope-ack-eae244d4fa2009df7c7f9cf9930ed14d` |
| Coordinator, role 2750 | `e34133ee-83e7-4b4c-959f-913dc109cbf0` | `scope-ack-bc80438ceccdaf10650b6e2aab522456` |

Both reviewers accepted the exact source result
`4c99272e9e9f4640ed51cf34bef81516630329a5` (`agent/isc-s16-formal-linkage`),
after checking the narrow fingerprint rework from `7dc4b546`.
All advertised source/audit Git-blob hashes and Lean/axiom log hashes match.
The old rejected receipt and review remain historical; signed/protocol/binary
bytes were not normalized or migrated.

The service applied transition `027b52b8-841c-43ea-a2f3-764ed835266f`:
`formal-linkage --NEED_DECISION--> continuity-coordinator`, and the next official
whoami delivered the coordinator assignment above. These are sequential reviews
by the same executor, **not independent Formal GO attestations**. They approve
the checkpoint and decision route, not a new signing contract or R2.3 closure.

## Current API checkpoint and pending decision

- Endpoint `http://127.0.0.1:18025`, project `9000`.
- Existing sprint `sprint-0001-783ef52c`, execution revision **128**, effective scope **3**.
- Execution **active**, phase **node**, current coordinator assignment as above,
  `requires_scope_ack=false`. This is not a terminal graph state.
- Scope workflow revision **9**; new request persisted without a human decision.
- Request **scope-request-a96d54e8001fef83987ff5350604b0bc**.
- Idempotency key `delta-isc-s16-r23-nonisc-authority-decision-20261006`.
- Immutable request source:
  `4cb065008d2f50bf02b83c7177bc53a4acd8aeff:orchestration/sprints/isc-s16-continuous/scope-requests/ISC-S16-R23-NON-ISC-AUTHORITY-DECISION.json`.
- UI: `http://127.0.0.1:18025/execution`, Pending decisions for this project/sprint.

The request seeks one consolidated **specification-only** decision document for
the missing non-ISC signed-byte/artifact/key-role binding in the existing Profile-v1
chain. ApplyQC is the minimum anchor. Its existing non-ISC dependencies must be
inventoried together, with reusable exact contracts and compatibility consequences.
An already approved applicable immutable contract may instead be supplied.
It does not request full R2.3 permission again and does not select new signing
bytes by assertion. Approving this request permits the finite document, **not**
implementation of its eventual semantic choice. No human approval, amendment or
new effective scope was fabricated by the executor.

## Residual and why the boundary is real

The reviewed boundary and pinned evidence are at the worker source above:
`orchestration/sprints/isc-s16-continuous/handoffs/ISC-S16-R23-NON-ISC-AUTHORITY-BOUNDARY.md`
and `formal/proposals/evidence/isc-source-v2/authority-boundary.json`.

Approved exact ADR0014 explicitly covers ISC signatures only, while Profile v1
requires authenticated ApplyQC even for the provisioned initial anchor. The
pinned native `verify_apply` accepts typed objects and signer IDs, not original
signatures/keys. Treating its structural success as authentication would bypass
the frozen provenance requirement. This is an API/source-binding insufficiency,
not a claimed production-reachable forged snapshot or a new trust requirement.

Isolated components establish successor ISC bytes/identity/parent binding,
structural policy inventory, ISC authentication, W1/output budget implications
and preservation of other policy fields with nonempty lineage. The full producing
origin, concrete Profile-v1 authority and complete public-family applicability
still need one composition proof. The three frozen R2.3 residuals remain OPEN;
no new DoD or hidden source cap is introduced. R1/R2.1/R2.2 remain CLOSED for their
original domain. Recovery theorem/full R3/production integration remain unstarted.

## Resume discipline

Wait for the actual human decision via the ordinary v2 API/UI. Do not send a
RESUME outcome just to leave this waiting point. On a decision, read live identity
and effective scope, verify source/hash/precedence, ACK its exact context if needed
and confirm persistence through GET. Follow the actual resulting boundaries and
normal graph/review gates; ACK alone never advances the graph. Rejection is not
permission to recreate the same request repeatedly.

No new sprint/import/reset, manual nginx mutation/restart, new trust root, profile
expansion, legacy object/QC/WAL changes, concrete sigma, guard removal, hidden
assumptions or GO relabel. No subagents. Idle time is excluded from active work.

The former ACK-500 handoff is historical; the infrastructure blocker is resolved.
Read-only checks confirm demo 8870/8865/8872 HTTP 200, Controller READY at exact
`c8aea64972f741060d1e527ebbb6f9a5a168a075`. No healthy service was restarted.
The machine-readable checkpoint next to this handoff records only HTTP evidence;
the live service remains authoritative for resumption.
