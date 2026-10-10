# EC source step: scope 17 checkpoint

**Historical checkpoint.** Scope 18 subsequently selected and authorized an
isolated formal/reference EC companion. See `ec-durable-binding-checkpoint.md`.
The storage STOP below records the scope-17 result and is not a current
permission blocker. Its original computation claims and limitations remain.

T047/T053 / ISC-S16-D01. 9 October 2026. **R2.3 OPEN; Formal NO_GO.**
Worker 2753, assignment `0a98cefa-5b31-42a4-b709-fa0ec58bb932`, branch
`agent/isc-s16-formal-linkage`, publication base
`e389e1869ddac63c7d529a1e83d3b153d1669f36`.

The applied decision `scope-decision-1eec5f953a9929960b8403c0a8c563e9`
selects EC-SOURCE-STEP-v1 at `f1a9963eabb5cb61f936ad1ad41f45e870acd43e`.
The exact role ACK `scope-ack-d18f627d61b99ae211f38bf8a99f8652` was confirmed
by GET. This replaces the proposal's historical unselected status for this
assignment without modifying its immutable bytes or any old objects.

## Reduction of the existing residual

`ProfileEcFinalization.lean` and the reference interpreter now compute E/e
from a full decoded native P0, the original body and the original admitted cut.
`assembled`, `assembleComplete` and `exactComputedWitness` establish the
explicit computation and all-cut signers. `firstAtOriginalKey` excludes a
second finalization for the same original ISC b, irrespective of later
seed/view/witness. Unknown finalized IDs cannot count as absence.

`wholeNativeStateChecked` binds both complete native static states; the
successor policy is computed, never supplied or accepted because public
refinement succeeded. `allOriginalLineageRetained`, `unchangedLineage` and
the outer-field theorem preserve all old ECs and every unrelated field.
Equal e with a different seed/witness fails. Existing nonfinalized identical
E/seed is reused. No original vote or delivery is collapsed.

`originalEventChecked` checks the six ordered original inputs and exact
dependency union, including repeated deliveries and a fourth signer if already
present. Either original retained C/c for the same b can be the event's C
reference; it is not replaced by the first C found. `replayOriginalCut` and
`replayExactSeedAndWitness` recompute the old cut and preserve the complete
current state, including later lineage/ABORT, with no new ID or WAL slot.

These conclusions are conditional on explicitly listed native inputs, **not**
on public success. They do not establish the origin of P0, body/seed/norm,
the full admitted inventory, original prerequisite positions or durable
production. The generator deliberately labels its data synthetic; its signed
NSG1 examples use public synthetic keys and the pinned strict Ed25519 backend.
No fixture is asserted to be a complete lawful production/import history.

## Exact remaining architecture boundary

The selected rule changes `eligibility_certificates` and
`finalized_eligibility_ids` while preserving RoundState. A source event and a
valid E/seed therefore specify the **logical** P0-to-P1 result; they do not
identify a durable local EC commit or its crash cut.

At pinned N=`60c692f6e391f839829dfc64e93380db54cd507b`:

- `delta-runtime-cpp/src/runtime.cpp` uses an immutable startup vote policy.
  Kind 1 replays a coarse command/RoundState transition; its payload is not a
  full EC policy update. Kind 2 records a Vote and the startup-policy hash.
  Neither is an independently specified first-EC policy commit.
- `CertificateVoteRuntime::persist_and_expose` persists **votes**, not
  finalized ECs. `CurrentPointerStore` persists the APPLY/current transition;
  its authority check does not reconstruct an earlier EC finalization cut.
- Approved W1 at P=`26eb02d0632435c9aa0d8ef44eb496b6fa73dd13` is ISC-only.
  Treating EC as kind 3, reinterpreting kind 1, or using an ApplyQC/artifact hash
  in place of the missing local barrier would change the selected contract.
- EC-SOURCE-STEP-v1 §§5–7 explicitly exclude a concrete EC storage encoding
  and forbid inferring durable success from source hashes or `durable=true`.

The minimum missing binding is: **which existing or explicitly selected
persisted object commits this exact E/seed, original event/cut and complete
P0/P1; what is its barrier/commit point; how replay distinguishes a pending
attempt from that committed update while preserving original sequences.**
No answer is selected here. No new kind, capsule, producer/storage authority,
policy reset or domain restriction is introduced.

This is a contract-coverage finding, not an executed attack, a TLC
counterexample, or a fully admitted production snapshot that violates a
theorem. In particular this report does **not** claim two valid production
histories with identical complete evidence. The absent binding prevents
establishing validity in the first place. Immutable source hashes and narrow
excerpts are in `evidence/profile-ec-finalization/durability-boundary.json`.

## Unchanged R2.3 obligations

The same three obligations remain: derive the full source/configuration/
aliases/units from the independent prefix; compose all original collections/
current/environment into the public relation; handle initial/incomplete and
sufficient ABORT snapshots without erasing lineage. The component above
reduces the EC computation portion of these obligations. Their origin fold
and universal public composition are **not** declared complete. The concrete
storage binding blocks the recovered-state claim; it is not an excuse to
assume the other origin premises or to reopen R2.1/R2.2.

Scope 17 expressly requires STOP if that storage premise is unavailable.
The named recovery theorem and full R3 have not been started. No production
Init/Next, certificate bytes, existing QC/WAL IDs, runtime guard, trust model,
Profile bounds or deployed services changed.

## Evidence and review

`evidence/profile-ec-finalization/receipt.json` records the exact fresh Lean
source closure, kernel cases, axiom audit and profile-source regression after
successful qualification. The mandatory gate result is recorded separately;
component success never upgrades that gate or the missing recovery theorem.
Publication and the ordinary two-review outcome are reported through nginx-qa.
Sequential process reviews by this executor are not independent Formal GO
attestations. Neither this document nor a routing review closes R2.3.

The mandatory `formal-check` recipes were executed sequentially with the
existing pinned Java/TLA/Lean toolchain. Phase0, contracts, toolchain locks,
parse, safety and liveness passed. The proof gate stopped on the existing
missing `DeltaReduce.nativeArithmeticRecoveryRefines` and its missing axiom
dependency result. Mutants, refinement and report were not reached after this
failed prerequisite. `mandatory-gates.json` binds the full logs and records the
initial missing environment path and the interrupted desktop session honestly;
neither interruption was treated as a successful qualification.

The worker outcome is **NEED_DECISION** for
`EC_DURABLE_COMMIT_BINDING_NOT_SELECTED`, not GO for R2.3. Selecting or supplying
that exact storage binding requires the normal Pending decision workflow.
The source-step component and its tests do not authorize that selection.
