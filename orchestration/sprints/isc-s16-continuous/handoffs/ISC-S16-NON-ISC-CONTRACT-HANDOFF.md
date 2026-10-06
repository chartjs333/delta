# Delta: proposed non-ISC contract, awaiting semantic decision

T047/T053. 2026-10-06. **R2.3 OPEN / Formal NO_GO**.

## Completed authorized work

Official whoami returned coordinator 2750, assignment
`e34133ee-83e7-4b4c-959f-913dc109cbf0`, branch
`agent/isc-s16-continuous-sprint`. The service had recorded actual human decision
`scope-decision-3a596d361b5328e1acaf48e2ac4699d1`, applying scope revision 4
from the previously pending specification-only request. Exact source/core hashes
and effective-over-issued precedence were checked. ACK
`scope-ack-591dddd4aac8c7b6a55e0d6a577c7262` was persisted and confirmed by GET.

That approval authorized **one document**, not the new semantic signing contract.
The resulting document is:

`bb9fce957dae329701a8cd473a7148e198e1ca12:docs/adr/0015-non-isc-authority-binding-v1.md`

Git-blob SHA-256:
`f2e988d26a28ff8cedf74cc2265c535057e7ae37dc152002a853c75a0614710d`.
Commit pushed and remote branch verified.

The proposal gives exact signable Vn/Mn/Gn, an explicit closed eight-kind
non-ISC dispatch alongside the approved ISC profile, and reuse of the original
fixed epoch/validator key table. It retains original vote bodies, Apply candidate
parent/optimizer binding, EC seed sidecar, signer sets and witness identities,
Parameter assignment context and S-RANK. It explicitly inventories other source
dependencies that these signatures do not authenticate. Derived per-object byte
bounds introduce no new retained-history or event cap. No new authority, QC type,
producer rule, implementation, schema, proof or qualification claim was created.

Validation was documentary: immutable source blob hashes, actual native symbol
names/layouts, finite inventory, framing-size arithmetic, JSON parsing and
Git whitespace checks. No fresh formal/native result is claimed. Original
R1/R2.1/R2.2 statements stay CLOSED; R2.3 composition remains OPEN. Prior sequential
reviewer receipts remain historical and are not independent Formal GO attestations.

## Persisted semantic request

The role-authenticated ordinary v2 API created exactly one new Pending request:

- **scope-request-4395b63c8605983a6adfde98805f76fa**;
- idempotency key `delta-isc-s16-nonisc-exact-contract-bb9fce95`;
- source `bb9fce957dae329701a8cd473a7148e198e1ca12:orchestration/sprints/isc-s16-continuous/scope-requests/ISC-S16-R23-NON-ISC-CONTRACT-APPROVAL.json`;
- source SHA `7ceedf63b51efdc09ada5a66e14a5c1368ea8d67bddea972814ac4e1a9837316`;
- requested decision: exact sections 3–7 of ADR0015 for isolated future
  formal/reference work within already authorized R2.3; full retained restrictions
  and ordinary review/qualification gates remain.

No authorization provenance was fabricated; this is a **new semantic decision**,
not technical redelivery of the existing full-R2.3 permission. POST returned
`status=pending`. Subsequent public state GET confirms the request and no matching
human decision. The operator acts in Pending decisions at
`http://127.0.0.1:18025/execution`; no manual amendment JSON or shell command is needed.

## Current checkpoint and STOP

Existing sprint `sprint-0001-783ef52c`, project 9000, execution revision **130**,
scope **4**, workflow revision **13**, coordinator assignment above, **active/node**.
GET still reports the same exact scope acknowledged. Request creation did not
change execution revision, assignment history, workflow graph, current node,
pending transition or last transition. It is not a graph terminal/completion.
Machine-readable HTTP evidence: `ISC-S16-NON-ISC-CONTRACT-CHECKPOINT.json` beside
this handoff. Live API remains authoritative for subsequent continuation.

**STOP after the document under scope4.** Do not implement or prove the proposed
contract, send RESUME to bypass the decision, resubmit the old accepted result,
create a duplicate request, self-approve, or apply a raw amendment. While pending
and unchanged, read-only polling stays quiet. A rejection does not authorize
recreating the request. After an actual new decision, obtain current identity and
effective scope through the official API, verify source/hash/precedence, exact
role ACK if needed, confirm it by GET, then follow only the approved boundaries
and normal graph/reviewer gates. An ACK alone does not advance the graph.

Full R2.3 permission is already valid; do not ask for it again. Named
`DeltaReduce.nativeArithmeticRecoveryRefines` follows substantive reviewed R2.3
closure, not this document; full R3 and production integration remain excluded.
No concrete sigma, legacy migration/relabel, guard removal, new trust root,
profile expansion, hidden assumptions/source caps, invariant weakening or GO.
No new sprint/reimport/reset/manual graph manipulation, nginx changes/restarts,
foreign-file changes or subagents. Preserve ACTIVE automation and exclude idle.

Read-only demo checks returned HTTP 200 at 8870, 8865 and
`8872/node-training/api/health` (`delta-node-training-example`, LOCAL_DEMO_ONLY).
Port 8872's root is not a page route; its 404 was not an outage. No service restarted.
