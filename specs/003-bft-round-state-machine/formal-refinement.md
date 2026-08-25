# Formal Refinement Obligations: 003 BFT Round State Machine

This file is normative for implementation of `003-bft-round-state-machine` and supplements `spec.md`, `plan.md` and `tasks.md`.

## Bound formal baseline

Implementation MUST verify and record the exact compatible `formal_semantics_id` and `FormalVerificationReport(GO)` inherited from `000-formal-tla-spec`. A semantic mismatch is a hard STOP.

## Refined actions

The implementation must project at least:

- `Propose/Vote/FinalizeRoundConfig`;
- `IssueTicket`, `LeaseTicket`, `CommitTicket`;
- `Attest/FinalizeAvailability`;
- basic `CloseInput`, `FinalizeISC`, `GenerateSeed` gate;
- `Propose/Vote/FinalizeParameterQC`;
- `SoftTimeout`, `ViewChange`, `HardAbort`;
- `Crash`, `Restart`, `RecoverJournal`, `ReplayMessage`, `RepairArtifact`.

## Refined invariants

Mandatory trace/conformance evidence covers `TypeOK`, `ConfigUniqueness`, `TicketImmutability`, `CommitUniqueness`, `VoteUniqueness`, `QCUniqueness`, `AvailabilityBeforeISC`, `ISCImmutability`, `SeedAfterInputFreeze`, checked-integer-only reduce, `AbortPreservesParent`, `RecoveryIdempotence` and `PlaneSeparation`.

## Required evidence

1. Canonical implementation-event projection schema/version.
2. Legal normal/view-change/repair/abort/restart traces accepted by the 000 checker.
3. Illegal double-vote, commitment replacement, seed-before-ISC, post-ISC mutation, wrong-view shard and restart-before-journal traces rejected.
4. Four independent `f=1` processes over 100 tickets whose projected behavior is legal and whose concrete bytes/hashes agree exactly.
5. Counterexample regression: every 000 mutant relevant to 003 remains detectable.
6. Final formal-impact report binding source tree, implementation trace hashes and unchanged/updated formal semantics ID.

## Change rule

Any implementation discovery requiring a new transition, altered precondition, timeout/recovery behavior or different failure terminal must first amend branch 000, obtain a new Formal GO and update compatibility before code proceeds.
