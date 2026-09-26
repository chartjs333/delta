# Computed CONFIG/ISC admission through one native WAL fold

T044/T048/T049/T053/T057/T060; amendment0001. **NO_GO**. This stage
composes the proposed CONFIG/ISC subdomain with general typed Lean recovery.
It does not discharge `nativeArithmeticRecoveryRefines`.

## Shared executable relation

`NativeReplayAdmission.Mode` is a closed sum of `config` and `proposals`.
Each mode selects a fixed, computed startup and fresh-vote checker:
`NativeConfigAdmission` or `NativeProposalAdmission`. No admission callback,
approval flag or supplied recovered-state equality is an input. The latter
checks every original candidate, including candidates not selected by the vote.
Startup validates the entire policy even when the WAL is empty.

The existing `NativeConfigReplay` fold now takes this mode. It remains one
implementation and one inductive history, with shared position, policy-ID,
command replay, clock, uniqueness, cache provenance and snapshot checks. Vote
receipt action and cached parents come from the actual selected candidate;
CONFIG uses action1 and ISC action2. The original CONFIG-only vectors remain
checked in the explicit `config` mode.

Successful recovery derives the executable history from empty caches. Every
recovered proposal vote has an original log entry, checked policy candidate,
original canonical frame, sequence, parents and computed receipt. Every command
cache entry comes from checked native command replay. Positive snapshot positions
must match a computed step. Sequence-zero snapshots retain the prior parse-only
behavior; this is not authenticated initialization. `recoverObserved` composes
the actual WAL scanner and rejects a torn scan or unconsumed tail. An observed
byte string is not proof of physical scan completeness or absence after a lost
response.

## Original mixed example

The generated policy module proves the exact **two-candidate** original policy
bytes, using previously checked CONFIG/ISC byte components. It does not replace
the original policy with a singleton under the old policy hash. Ten finite SHA
preimages cover the original policy, vote, contexts, ISC body and command state/
effect/record identities. These are executable samples, not a general SHA proof
or native exporter authentication.

The kernel-composed example uses original `NativeWalVectors.entry2` (ISC at
outer sequence1) and `entry3` (freeze command at outer sequence2). It derives
startup, full policy admission, the vote step, native freeze outputs, the
complete replay and recovery result. Original vote receipt bytes and original
command receipt remain in separate caches and can be returned after freeze.
Fresh admission after invalidation rejects. Removing the first vote, repeating
it, reordering the entries or substituting the policy record rejects. There is
no renumbering and no new combined raw physical-scan example.

The prior native C++ comparison (32 cases, 14 accept/18 reject) and original
policy/WAL/receipt bytes are revalidated as retained evidence. **No new native
runtime run is claimed in this stage.** Its CONFIG candidate is checked but
unselected in this ISC/command journal; the actual CONFIG-vote journal remains
a separate example. Later view/abort entries remain prior evidence only.

Large draft reductions of concrete SHA bodies and the final recovery bind were
discarded. Final proofs apply small generic component lemmas to existing exact
byte identities. Draft resource failures are not successful verification logs. The first whole-bundle
build also caught three imports after a module doc comment; they were moved to
the import section before the final source-bound checks.

## Remaining limits

Finalized ISC/seed/EC/APC and other certificate graphs/actions still reject or
lack general admission. Native ledger availability, root preimages, current and
committee/configuration origins need independent binding. SHA and source trust
remain explicit premises; metadata, snapshots and physical scans are not
authenticated by these examples. The smaller diagnostic Python limits are
unchanged. Unknown/incomplete observations cannot establish absence, and corrupt
or ambiguous scans do not restore readiness.

General DRS1 decoding, arbitrary initialization/failures/repair, complete public
state/action/native recovery, contract freeze, clean offline reproduction and
independent review remain mandatory. Full Feature010, local acceptance and
qualifying GO are not complete. Runtime guards and demo services are unchanged.

Final check counts, source hashes and retained limits are recorded in
`evidence/native-mixed-replay.json`. No fresh TLC or production mutant suite is
claimed; previous bounded results keep their original scope.
