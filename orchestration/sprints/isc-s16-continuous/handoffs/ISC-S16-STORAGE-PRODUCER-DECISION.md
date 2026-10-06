# Storage producing-history boundary — existing sprint handoff

6 October 2026. T047/T053. **R2.3 OPEN; Formal NO_GO.**

The accepted storage byte/authority decision is retained: scope7, human decision
`scope-decision-614a7db8512f59e36720131917827d4c`, ADR0016 §§3–7 at
`1438fa3d78ec99291475cf4660fd8c190ac01bb3`. It authorizes that future reference
binding but explicitly requires STOP if original producer/evidence is missing.
Full R2.3 permission is not being requested again.

Worker `a2fd17259240be0a7721512e7a12fe972587f3bf` on
`agent/isc-s16-formal-linkage` checked that boundary before implementing storage
bytes. Its `formal/proposals/storage-producer-checkpoint.md` and
`formal/proposals/evidence/storage-producer-boundary.json` are the review source.
Evidence SHA256: `cc55c075c42a3b3e36abfd16301d346695acd134780b00fa8f765b80ebd1c6d6`.
The evidence was reproduced byte-for-byte from the commit; source hashes match.

## Concrete blocker

**MISSING_STORAGE_PRODUCING_HISTORY_BINDING.** At native pin
`60c692f6e391f839829dfc64e93380db54cd507b`, the ledger receives an aggregate
AvailabilityProof; the coarse ACCEPT_AVAILABILITY transition checks phase/count.
Local artifact I/O and opaque transport do not provide the original per-storage,
per-shard upload/loss/corruption/repair history at attestation/finalization.
No applicable independent source-producing/observation contract was identified
in those pinned boundaries. An external one may exist; its immutable contract
and original evidence must be supplied rather than guessed.

Minimal distinction: three original attestations satisfy historical coverage.
Lose one original shard location **before** finalization: signatures still verify,
but available-attester coverage falls to two and the existing TLA finalization
guard fails. A legal finalization **before** that loss retains its AC/ISC lineage.
No perpetual availability or deletion of old certificates is required.

This is a source-information/guard diagnostic, not a production exploit, TLC
trace or counterexample that passed the full snapshot profile. It does not prove
R2 impossible. A signature codec alone cannot discharge the missing cut binding.

## Process checkpoint

- Existing sprint: `sprint-0001-783ef52c`, project9000 on18025.
- Worker assignment `b52fcd71-2a71-456e-86a0-f5c1691f58c9` returned
  `NEED_DECISION` once; transition `e37078b0-3101-40da-bcaa-2b980d0fb90a` received
  both ordinary APPROVE reviews.
- Review assignments: `3271a2b7-90d5-4164-af81-8a1273eec017` and
  `ea38860c-3565-4cbc-9d4e-8b8ec502deb1`. Same sequential executor: these are
  process reviews, **not independent Formal GO attestations**.
- Current coordinator assignment: `4824b8d9-2e13-4a6f-89d1-917696ff8a43`, branch
  `agent/isc-s16-continuous-sprint`; fresh scope7 ACK
  `scope-ack-73db8f79427b8715f3b6d3b19377e7cf` is GET-confirmed.
- No new graph outcome is justified while this semantic boundary is unresolved.
  The assignment stays active. Pending-decision attention is distinct from the
  graph's execution state; do not invent a terminal blocked transition.

## Requested decision, not implementation permission

The structured request is
`../scope-requests/ISC-S16-R23-STORAGE-PRODUCER-DECISION.json`.
An operator may identify an already applicable immutable storage producer and
original evidence, or authorize **one bounded specification-only decision memo**
for this missing producer/observation binding. That memo must state ownership,
exact source events and cuts, observation/completeness authority, and compatibility
with the unchanged public guards. It must distinguish a local write, a signed
statement, and actual retrievability; preserve post-finalization lineage and the
approved Rs/Ks/A/Gs/D/ac contract.

Approval of this request would permit that document only. It would not approve
an unspecified producer, observer, stronger storage-honesty assumption, new
authority, model change, source-domain narrowing or code. If such a semantic
change is unavoidable, the document must state the exact choice for a separate
decision. Stop after the document. Rejection or unchanged pending grants no
permission to repeat the request or resume proof work.

Use [Pending decisions](http://127.0.0.1:18025/execution); no manual amendment,
token transfer, graph reset or sprint reimport. A later actual decision requires
fresh actual-role effective scope and exact ACK; ACK alone advances no graph.
The adjacent `ISC-S16-STORAGE-PRODUCER-CHECKPOINT.json` records the registered
request and latest read-only persistence check once available.

R1/R2.1/R2.2 remain CLOSED in their original domain. R2.3 source/configuration,
collections and incomplete/ABORT correspondence remains OPEN; storage bytes and
complete bounds/composition are not qualified by this audit. Existing ISC and
non-ISC components are preserved. No named recovery theorem/full R3, production
integration, guard removal, new semantics ID, object/signature/QC/WAL relabeling,
new trust root, hidden caps or lineage truncation. Healthy demos remain untouched.
