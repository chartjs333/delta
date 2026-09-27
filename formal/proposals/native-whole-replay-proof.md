# Whole original-policy WAL replay (T044/T048/T049/T053/T057/T060)

This Feature000 amendment0001 proposal composes the complete original policy
checker with the existing computed command/VOTE journal fold. It grants no
runtime authority and does not discharge `nativeArithmeticRecoveryRefines`.
The current PARAMETER/APPLY refusal remains in every accepted native-source mode.

## Computed boundary

`NativeReplayAdmission.Mode.whole` is a closed implementation, not a supplied
admission callback. `prepareWhole` decodes the original policy and initial state,
executes `NativeCandidateAuthority.bindPolicy`, and retains that original policy's
initial logical tick. Selection calls `NativeSelectedVote.fromBytes` against the
actual current state of the fold. All original snapshot sections and ALL original
candidates are checked. The older `.config` and `.proposals` modes retain their
restricted domains; `actionMatches` explicitly requires one of those modes.
`guardedActionMatches` describes all three modes, retaining exact kind and the
seven currently allowed non-arithmetic actions.

The existing fold supplies tick, invalidation and expected sequence from its
actual machine and WAL entry, with readiness=false and recovery=true. A caller
cannot pass an admission Boolean or choose an unrelated previous state. The
new `historyVotePosition` and `recoveredPosition` lemmas derive an executable
prefix and suffix for each retained vote. `globalPosition` relates its sequence
to the length of that prefix, including command records. `entryWholeSource` and
`entryWholeAuthority` retain original canonical policy/state/VOTE bytes, exact
first candidate, complete source snapshot, parent fields, guarded kind, receipt
sequence and original policy ID.

The generic history preserves exact command recomputation, unique request/vote
keys, cached receipts, monotone logical time, positive snapshot position checks
and all original votes. Commands invalidate further fresh votes under the actual
pinned runtime convention. Duplicate scan entries reject independently of the
position check. Successful historical retry consults the original cache before
fresh admission: no new current-parent, deadline or readiness check is imposed
on the original receipt. `retryWholeOrigin` traces a retry back to its historical
whole-policy computation. It neither appends a second record nor rewrites parents.

Reference native source is `60c692f6e391f839829dfc64e93380db54cd507b`.
The preserved scan order is policy identity, recovered-state admission, then
fresh journal classification. The preserved live order is canonical vote and
journal classification, original-cache retry, then fresh admission and append.
No production file is changed.

## Concrete composition

`NativeWholeReplayVectors` reuses the original native two-candidate CONFIG/ISC
policy and original ISC-at-position1/freeze-at-position2 records: the exact
two-record prefix of the four-record no-snapshot capture, also retained as its
own earlier native WAL/receipt observation. No full four-record example is claimed. Unlike the
previous synthetic mixed bound, its entire snapshot is computed from the SAME
original policy. All empty sections are checked, the nonempty proposed ISC body
is rederived, the all-configured-validator expansion obeys the separate 4MiB
JSON bound, and the closed body plus both original candidate contexts are checked.
Eleven finite SHA samples extend the previous ten-sample mixed replay adapter
with the already independently derived expanded-ISC certificate preimage/hash.
They are named finite hash premises, not a general SHA proof or authentication.

Component lemmas compose original decoding, whole policy and vote admission,
actual freeze transition, original vote/command receipts, final state and exact
cache retries. No original byte, body, envelope, receipt or position is replaced.
The resulting state and caches are definitionally the previous original mixed
replay result, now reached through the complete policy checker. Negatives reject
missing/reordered/repeated positions, substituted policy IDs, duplicate vote keys
and fresh admission after command invalidation. Positive snapshot comparison
uses current recovered state, not the empty state field of a vote WAL entry.
An arbitrary core change cannot change the original exact retry result.

The generic `recoverObserved` composition checks the actual byte scanner before
recovery. The new concrete example starts with the two original typed WAL entries;
their byte-decoder fixtures remain separately checked. It does not newly compose
one outer-WAL-checksum adapter with the eleven-sample admission/transition adapter.
No fresh native execution, TLC replay or production mutant is claimed.

## Remaining limits

A successful complete byte scan is not evidence of physical completeness, fsync,
source authenticity or exposure. This proposal refuses torn/nonempty-tail scans;
the pinned native source instead truncates a recognized torn tail before replay.
That narrower complete-scan domain is explicit and is not full failure/repair
refinement. Corruption, ambiguous/unknown presence, repair and arbitrary initial
snapshots still require the authenticated concrete observation relation. A typed
sequence-zero snapshot follows the original scan convention; it is not treated
as an independent authenticated source of the initial state.

The native cryptographic, bounded codec/SHA/exporter, directory custody and
physical WAL premises remain open. Original signature bytes are retained but
not cryptographically authenticated. Native decimal canonicality for -00/-01
still fails; no silent normalization or runtime fix is made. This work models
the currently guarded source, not future arithmetic admission. The missing
arithmetic recovery theorem cannot be proved by the fact that this source
rejects arithmetic. CurrentPointerCommand, actual arithmetic input admission,
complete 64-variable public/native phase/send/delivery/QC/current/recovery,
availability/failures/repair, contract freeze, clean offline reproduction and
independent reviews remain required. Self-review is not independent attestation.
Formal report remains NO_GO; runtime guard and healthy demonstrations are retained.

## Reproduction

Build the full Lean project and AxiomAudit, run the formal Python and oracle suites,
regenerate the existing source fixtures byte-exact, and verify the final report.
Machine-readable evidence is `formal/proposals/evidence/native-whole-replay.json`.
GNU make is unavailable; these checks do not claim aggregate `make formal-check`.
