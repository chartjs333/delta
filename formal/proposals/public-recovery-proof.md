# All-vote journal persistence and recovery lifecycle

Candidate amendment 0001, T044/T048/T049/T057/T060. `PublicRecovery.lean`
extends `PublicJournal` with checked diagnostic stage sequences, readiness,
required crash/restart, historical retry and authenticated exact-prefix scans.
Twenty helper theorems and sixteen executable functions are axiom-audited.
This is not the complete `nativeArithmeticRecoveryRefines` obligation: public
event snapshots/state roots, other-action phase/QC admission and production
exporter/decoder/WAL refinement remain open. Mandatory coverage stays 44/45.

## Admission, persistence and output

The machine retains its original initial journal, ordered all-vote/ApplyQC log,
computed journal/current pointers, pending unknown slot, readiness and exposed
slots. A first arithmetic observation executes `PublicJournal.checkSlot`, hence
the real native arithmetic derivation and all original metadata/record checks.
Admission failure returns no next state or output. No arithmetic-admission flag
is accepted. Non-arithmetic votes use the prior explicit authorization premise;
their unprojected native receipts remain absent.

Exposure is derived from an exact stage list. Only
`VALIDATED,APPENDED,DURABLE,COMMITTED,EXPOSED` can expose the first receipt. The
general classifier theorem derives the complete list from an exposed
classification. Observed before/after roots and returned bytes pass the previous
native-backed `observedAppend` relation. Known unexposed cuts preserve the exact
record, allocate one all-vote sequence, return neither receipt nor effect and
enter `mustCrash`. They cannot vote, retry, advance current or restart before
crash. A successful crash preserves pending/log state; restart alone does not
make the machine ready.

For UNKNOWN/failed-barrier observations, the candidate is checked but its
presence is not decided. The last known journal/log/sent set remain unchanged,
the pending slot is retained, post-tip is null and crash is required. Neither a
missing response nor the retained candidate proves a durable append or absence.
The known surviving-unacknowledged branch is retrospective and must recover
before further progress. These are checked diagnostic observations, not an
implementation or proof of a filesystem write/barrier.

## Exact scans and replay

Scan authentication is a named adapter receiving the original initial journal,
exact previous log, pending slot and complete scan. Even a true authenticator
cannot bypass exact-log comparison or replay. Ordinary complete recovery must
retain the known full log. For an unknown append, verified presence must contain
exactly the prior log plus the original pending vote; verified absence must
retain exactly the prior log. An ordinary old-prefix scan cannot claim absence.
No renumbering, removed intervening vote or supplied recovered-state equality is
used. Replay recomputes native admission for every arithmetic record and checked
ApplyQC current advancement from the original input, retaining all other slots.

`readyRecoveryDerivesAllVoteHistory` extracts actual accepted replay and its
independent checked history from successful recovery, derives the entire slot
list and checks recomputed roots/sequence. Recovery exposes no receipt/effect
and does not add voting power. Only a subsequent exact historical retry can
return the original native record. Retry does not re-admit the old parent against
new current, allocate another sequence or rewrite the log. A different command
in the same saved key conflicts before output. The exposed-slot set is a local
exposure projection, not a full network delivery or quorum-counting proof.

Incomplete scans remain recovering; corrupt/ambiguous scans enter blocked.
Blocked state cannot restart or recover under this no-repair scope. Invalid or
unauthenticated scans return no accepted state change. Both roots in successful
recovery are computed from actual replay, and all recovery outputs are null.
Initial arbitrary snapshots and physical scan completeness remain external.
The accepted-operation lemmas do not yet establish a single reachable-machine
invariant tying every live state/log to an authenticated full public snapshot.
That composition and the complete public state-root relation remain mandatory.

## Examples and limits

`PublicRecoveryVectors.lean` executes 44 kernel-decide examples over the prior
eight original vote slots, with arithmetic receipts at 5/6/8. The generator first
validates fourteen entire public/native fixtures: normal apply, all eight known
PARAMETER/APPLY persistence cuts and five unknown/absent/blocked/incomplete
cases. Exact witness stage/root/output values are then embedded in Lean.
Examples construct the four-vote prefix and the full eight-vote journal from
empty state, check current advancement, all known cuts and unknown observations,
verified absence, corrupt/ambiguous blocking, exact surviving-record replay,
retry after current advance and fail-closed stage/root/output substitutions.

The general unknown-presence scan example is a separate mathematical case.
Current public witnesses represent complete surviving unacknowledged records
retrospectively as accepted unexposed votes; UNKNOWN/FAULT observations in the
pinned public traces resolve to verified absence or remain unresolved/blocked.
The example must not be described as a new public UNKNOWN-to-presence trace.
Likewise an explicit incomplete scan is an internal case; the incomplete public
fixture ends with an unresolved observation prefix.

The concrete scan authenticator is synthetic. Existing input decoding, native
metadata/QC trust, finite SHA samples and other-action authorization retain their
prior scope. The stage arrays are checked, not physically authenticated. Full
snapshot/event binding, canonical public state-root transition, SendVoteEnvelope
and global QC eligibility, arbitrary failures/repair and concrete bounded native
decoder/hash/exporter/WAL remain open. No new public action, production protocol
outcome, TLA rule, C ABI or runtime arithmetic guard changed.

Six generator tests check exact reproduction and rehashed mutations of early
exposure, invented output, ordinary scan mislabeled as absence, truncated prefix
and unknown post-root. They reject before producing Lean output. This is not
native execution, physical crash testing or fresh production-mutant evidence.
Validation and exact inputs are retained in
`formal/proposals/evidence/public-recovery.json`. Self-review is not independent
attestation. Formal authority remains NO_GO pending the complete mandatory gate.
