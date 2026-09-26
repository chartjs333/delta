# Original native VIEW/ABORT candidate and selected-vote subrelation

T044/T048/T049/T053/T057/T060; amendment 0001. This proposal remains **NO_GO**.
It adds executable Lean checks after `NativeFailureSection`; it does not replace
whole native policy admission, journal retry classification or the mandatory
`nativeArithmeticRecoveryRefines` theorem.

## Source and computed checks

The read-only native reference is commit
`60c692f6e391f839829dfc64e93380db54cd507b`:
`delta-core-cpp/src/vote_admission.cpp`, `consensus.cpp`, `vote_codec.cpp` and the
existing certificate sources. No runtime/native guard source changes here.

`NativeFailureAuthority` reads all 15 original parent fields: config, checkpoint,
12 required-empty intermediate slots and reason. It computes VIEW/ABORT context
preimages from the original source convention, resolves the actual body by its
computed ID in the checked source list, and compares all candidate coordinates.
VIEW requires the original matching timeout, current height/from-view, checked
uint64 next-view increment and exact configured soft deadline. ABORT requires
its exact parent/reason and no finalized APPLY, as well as all 14 prior snapshot
body fields and all seven finalized lists. General lemmas retain original row
membership and the source reader/encoder/hash execution.

VIEW context is domain `deltareduce.vote-context.view.v1`, a NUL separator,
uint64-BE length-prefixed round bytes, then uint64-BE view. ABORT uses domain
`deltareduce.vote-context.abort.v1`, NUL and length-prefixed round only. **Neither
context includes height or epoch in the native source.** Envelope/current checks
bind those independently. Native body and context hashing have no invented
certificate-JSON size bound. Wire resource checks and uint64 bounds still apply.

`NativeFailureVote.fromBytes` executes the existing bounded policy, state and
original DRC1 VOTE decoders, performs original first-match candidate selection,
executes `bindCandidate` (which executes the prior section), then the selected
vote checks. Those compare action, actor, epoch, round, height, view, context,
body, current checkpoint and expected sequence. Live requires recovery readiness;
replay skips only that readiness check. Both reject invalidated authority and
terminal phases. VIEW requires **all** abort requests empty and
`soft <= tick < hard`. ABORT requires the exact configured round/reason request
or `tick >= hard`. A foreign request blocks VIEW but cannot enable early ABORT.
Successful decoding/checking retains the exact original vote bytes.

The raw component `checkVote` expects an entry; only `fromBytes` actually derives
that entry from the selected original policy candidate. Likewise candidate
`Common` alone does not bind its checkpoint to current state; the selected-vote
check does. Component counterchecks explicitly retain these boundaries. No
caller-supplied whole-body translation or finite approval list is an admission
premise. SHA and `RuntimeFacts` remain explicit executable/primitive boundaries,
not authenticated native observations or a proved journal scan.

## Correction to the preceding snapshot predicate

The preceding proposal used `NativeConfigAdmission.Label` for timeout/request
round IDs. That was stronger than this native source: `require_id` rejects only
empty strings, while the original policy wire separately restricts printable
ASCII and at most 4096 bytes. The new `WireId` combines those actual requirements
and replaces that use of `Label`. Spaces, punctuation and 129-character IDs
provide executable counterchecks against the old certificate-label restriction.
Empty/nonprintable/overlong wire values remain rejected.

This corrects a formal projection overrestriction, **not a native runtime defect**
and not a newly measured native acceptance test. Existing header/configuration
and certificate `Label` uses have not been globally relaxed: their individual
native contracts and joins still require review. Do not claim that this local
correction completes whole native admission equivalence.

## Evidence and reproduction

`generate_native_failure_authority.py` checks the complete prior original policy
observation SHA `d82c14dda8356bfebc1cc1febe3c2fd09c3393b467cc99bacd565b506a91d2ea`
and the original receipt/vote observation SHA
`788374b6bc1ce788b30a847fbcf6def0fb3804b4f9926304c4456430dd604c44` before deriving
context preimages. It independently rechecks original policy candidate and VOTE
body/context IDs. The vectors reuse actual `vote8`/`vote9` from the previous
kernel-checked original codec observations. Two additional context SHA samples
plus the two retained body samples form a **four-sample finite adapter**, not a
general SHA proof or producer authentication.

The generated module composes both original source tails, both selected
candidates and both original votes using existing component lemmas. It does not
claim a new complete `fromBytes`/`bindCandidate` fixture, native execution or
post-WAL result. The general wrapper proofs still require actual successful
execution of those functions. Mathematical negative cases cover every forbidden
parent slot, body/timeout/coordinate/deadline substitution, uint64 wrap,
finalized APPLY, live/replay readiness, invalidation, sequence, phase and deadline
endpoints, exact versus foreign request, unsupported actions and ID spelling.
Original arithmetic sequences 5/6/8 and all native source witness bytes are
unchanged.

Run from the repository root with Python 3.12 and the pinned Lean toolchain:

```text
python formal/scripts/generate_native_failure_authority.py
python -m unittest discover -s formal/tests -p test_native_failure_authority.py -v
cd formal/proofs
lake --no-cache build DeltaReduce
lake --no-cache env lean DeltaReduce/NativeFailureAuthority.lean
lake --no-cache env lean DeltaReduce/NativeFailureVote.lean
lake --no-cache env lean DeltaReduce/AxiomAudit.lean
```

The source-bound final evidence is `evidence/native-failure-authority.json` and
its sibling directory. It distinguishes updated prior payload declarations from
new authority/vote/vector declarations. All named definitions/theorems are axiom
audited. Only final stable-source logs count; failed draft context/tactic-layout
builds are superseded, not proof evidence. Regeneration must be byte exact and
must not run concurrently with builds/tests consuming those generated sources.

## Remaining boundaries

Whole shared policy validation is still open: original header/state/configuration
constraints, candidate set size/order/global context uniqueness, every candidate
kind, closed CONFIG/ISC integration and separate proposed ISC size. Current
pointer transitions, source arithmetic/model/optimizer authority, actual journal
retry classification and full public/native recovery are not proved here.
Historical idempotent retry must be classified before fresh admission; replay
mode here is not itself crash recovery. Unknown/incomplete durability remains
incomplete and cannot be inferred to be authenticated presence or absence.

Native decimal canonical spelling still has the retained -00/-01 compatibility
defect; no normalization or runtime repair is made. General parser/JSON/SHA and
exporter correspondence, physical WAL/scans/power loss, arbitrary snapshots,
availability/failure/repair, contract freeze, clean offline reproduction and
independent review remain mandatory. Earlier finite TLC/safety/liveness/mutant
results retain their old scope; no fresh native/TLC/production-mutant run is
claimed. GNU make is unavailable: scoped checks are not aggregate `formal-check`.
Mandatory Lean remains 44/45, Phase0 unfrozen. No local PASS, authenticated native
exporter, independent attestation, original GO or qualifying BenchmarkResultQC.
