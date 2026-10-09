# EC durable commit binding: reviewed boundary

T047/T053 / ISC-S16-D01 / ISC-S16-CONTINUITY. 9 October 2026.
**R2.3 OPEN; Formal NO_GO. No storage contract is selected here.**

## What is complete

Scope 17 selected EC-SOURCE-STEP-v1 at
`f1a9963eabb5cb61f936ad1ad41f45e870acd43e`, decision
`scope-decision-1eec5f953a9929960b8403c0a8c563e9`.
Worker commit `47d75279d23441f5c10ed523bdea172b257e8bef` on
`agent/isc-s16-formal-linkage` implements and qualifies its bounded computation
in isolated feature000 formal/reference code. It derives the all-cut original
signer set, first finalization keyed by original ISC b, exact EC/seed and the
two-collection P0/P1 delta. Original witness identities, delivery multiplicity,
unrelated lineage and replay of the original event/cut are retained.

Read the immutable worker files at that commit:

- `formal/proposals/ec-source-step-checkpoint.md`;
- `formal/proposals/evidence/profile-ec-finalization/receipt.json`;
- `formal/proposals/evidence/profile-ec-finalization/durability-boundary.json`;
- `formal/proposals/evidence/profile-ec-finalization/mandatory-gates.json`.

These are computation and component evidence, not a complete lawful producer
history or a proof of the full source fold/public relation. Synthetic examples
are not authentic histories. Mandatory phase0/contracts/toolchain/parse/safety/
liveness passed; the proof gate failed on the missing named recovery theorem
and its axiom result. The later dependent gates were not reached.

The worker's `NEED_DECISION` result and both ordinary process reviews were
accepted by nginx-qa. Transition
`d48d2116-79da-49e0-bafe-eaf7b3ec4274` returned to the coordinator normally.
`ec-durable-commit-boundary/process-reviews.json` records the exact result,
review and new assignment identities. Both reviews approve this bounded
checkpoint and routing only. They are by the same sequential executor and
are **not independent Formal GO attestations or R2.3 closure**.

## Why this is a semantic boundary

The existing scope explicitly excludes a concrete EC storage/WAL encoding and
requires STOP if composition lacks an independently selected storage/producer
rule. This is not a new request for general R2.3 permission, a missing helper
lemma, or a new DoD item.

EC-SOURCE-STEP-v1 §§5–7, at the selected source commit above, specify logical
finalization but do not supply its durable commit encoding. Pinned native
`60c692f6e391f839829dfc64e93380db54cd507b` has coarse kind-1 state transitions
and kind-2 vote persistence under an immutable startup vote policy. Neither
independently specifies this full EC policy commit. Approved W1 at
`26eb02d0632435c9aa0d8ef44eb496b6fa73dd13` is ISC-only. The worker's
`durability-boundary.json` pins the exact source paths, hashes and excerpts.

The minimum missing binding is finite:

1. Which persisted object commits the exact E/seed, original event/cut and full
   P0/P1 produced by the already selected logical rule?
2. Which append/barrier/commit point makes that update durable and exposable?
3. How does replay distinguish an incomplete attempt from that committed
   update while retaining original physical slots, vote ordinals and lineage?

A source hash, supplied EC, successful public transition, ApplyQC, or a
`durable=true` flag cannot stand in for these missing semantics. Reinterpreting
kind 1 or treating EC as W1/kind 3 would select semantics excluded by scope 17.
No such selection or change is made here. This is a scoped contract-coverage
finding, not an executed attack, TLC counterexample, or two demonstrated valid
production histories with identical complete evidence.

## Requested Pending decision

**Approve one specification-only EC durable commit binding pass.** Its sole
output is a concrete reviewable minimal contract for the three points above,
with exact compatibility and crash/replay consequences, followed by STOP and
an exact proposal for a later human decision. Reuse selected Profile authority,
logical EC rule, original EC/seed and journal identities. Do not design a new
trust model, general storage framework or alternative provenance system.

Approval of this request would authorize writing that bounded specification;
it would **not** approve its eventual byte layout, a new WAL kind, W1 extension,
production transition, implementation, schema or proof changes. If an existing
independently selected immutable contract is supplied instead, verify its exact
applicability and expose the result without assuming authority from its hash.

The machine-readable proposal is
`../scope-requests/ISC-S16-EC-DURABLE-COMMIT-SPECIFICATION-REQUEST.json`.
No choice is inferred from general R2.3 authority, the current ACK or either
review. A rejected or unresolved request leaves the dependent STOP intact.
Only nginx-qa's normal human-decision workflow may select the next boundary.

## Preserved obligations and state

The same frozen R2.3 residual remains: full source/configuration/aliases/units;
complete certificate/candidate/current/environment relation; and initial,
incomplete and sufficient ABORT snapshots without lineage erasure. This EC
component reduces their computation burden but does not establish all remaining
origin premises or universal public composition. R1/R2.1/R2.2 stay CLOSED for
their original domains. Named recovery work still requires substantive reviewed
R2.3 closure. Full R3, production integration/recovery, guard removal, concrete
sigma, new trust, hidden bounds and old-object migration/relabeling remain out
of scope.

Coordinator assignment: `93868961-a78f-41db-93ec-06d4d6d3167d`, role 2750,
branch `agent/isc-s16-continuous-sprint`. Exact scope-17 ACK
`scope-ack-41eed42d41d1b3ad5ab12f97def989aa` was GET-confirmed. No fake
RESUME/START outcome is submitted for STOP; scope requests do not advance the
graph. This checkpoint adds only documentation/evidence/request material and
does not merge the formal worker branch into production.

## Pending receipt

The official request `scope-request-527969688fc11f69a0254e1f9532dc8e` was
GET-confirmed pending at 20:39 UTC. Its immutable source is
`9690a05296fb129012d6d03f3636abb2c365a09b`. Execution revision 236, scope 17,
the current assignment, all sixteen earlier requests, reviews and queue were
unchanged by request creation. The UI now reports `authorization_required`;
the graph execution state remains `active`. See
`ec-durable-commit-boundary/pending-receipt.json` for the exact source digest
and comparisons. No decision, new scope revision or dependent work is inferred.
