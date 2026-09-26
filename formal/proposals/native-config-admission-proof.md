# CONFIG admission from complete native policy bytes (candidate)

T044/T048/T049/T053/T057/T060; amendment 0001. NO_GO.

`NativeConfigAdmission` adds a computed startup and vote gate over the prior
DVPOL001, DRC1 ROUND_STATE and VOTE codecs. It supports exactly one CONFIG
candidate with an empty certificate graph. This is an explicit strict subset
of native policies, not completeness for all native CONFIG policies and not
admission for the other eight actions. Native source and guards are unchanged.

## Computed relation

`prepare` decodes the complete policy and initial state. `bindConfig` extracts
all relevant values from that same policy tree. It checks validator shape,
nonempty identifiers, 3f+1/local membership, role and configured reason,
strict deadlines, round/config equality, the certificate context's positive
height and bounded round label. It computes the snapshot content ID from the
exact canonical ROUND_STATE bytes using the native domain-separated preimage.
Schema/arithmetic/optional-accumulator content IDs are validated. Proposed and
finalized config sets retain strict ordering and the exact current config.

The supported graph requires all 27 snapshot vectors after the four primitive
fields and two configuration sets to be empty. Thus no certificate/body/timeout/
abort request is implicitly approved or ignored. Nonempty graphs fail closed;
the general certificate loops, signer authentication and non-CONFIG admission
remain separate work. The required accumulator ID is optional here exactly as
in native CONFIG policy validation; no accumulator certificate is invented.

The only candidate must use CONFIG, the actual proposed config body, current
height/view and the computed native CONFIG context. All 15 parent fields are
consumed: config/checkpoint must be content IDs, config must match, and the
remaining 13 must be empty. The context preimage uses the original domain,
height and 8-byte epoch length. It intentionally contains neither round nor
view; these coordinates are checked separately. No public symbol is treated
as a native hash and no whole-body translation or arithmetic approval is input.

`SourceChecks` is a conclusion of successful executable binding. It records
actual lookup results, exact source policy/state/candidate, snapshot hash,
parent tuple, computed context and startup checks. It is not supplied as an
assumption to `prepare`. Successful `fromBytes` derives these facts along with
original policy payload, state bytes and vote bytes. Small codec composition
lemmas avoid reducing an entire byte tree inside a single proof.

`checkVote` is the low-level typed vote guard; alone it does not prove startup
validity. `fromBytes` first executes `prepare`, then decodes and checks the vote.
It retains original actor, epoch, round, height/view, body/context and sequence.
The candidate checkpoint must now equal the state's current parent. This
check belongs to vote admission, not CONFIG startup: a well-formed policy with
a different checkpoint can initialize but cannot admit that vote.

Runtime facts are primitive tick, expected sequence, ready, invalidated and
live/recovery mode. Live admission requires readiness; recovery does not.
Both require non-invalidated authority, TICKETING_OPEN and tick strictly below
the hard deadline. Native uint64 bounds apply. No stored vote, effect or receipt
is exposed and this module does not mark a recovering runtime ready.

## Evidence and limits

A fresh isolated harness compiles the same 12 unchanged native translation
units and 28 pinned source blobs at
`60c692f6e391f839829dfc64e93380db54cd507b`, using MSVC 19.29.30146 and strict
existing flags. It decodes actual policy/state/vote bytes and invokes both
native startup and live/recovery admission. It opens no Runtime handle,
writes no WAL, runs no native arithmetic and does not touch a demo service.

There are 54 finite observations. The 53 supported cases compare startup and
vote acceptance against the computed Python checker. A separately labelled
nonempty abort graph is accepted at native startup but rejected by this
strict subset; this demonstrates the completeness boundary. Cases include
stale/rehashed state, malformed policy primitives, committee/deadline/config
errors, proposed membership, exact parents, candidate and vote substitutions,
live/recovery readiness, invalidation, expiry and original sequence.

Changing the summary state root and recomputing its exact snapshot content ID
can pass this relation. That establishes consistency of the supplied bytes,
not independent initialization/exporter provenance or the complete 64-field
public state. Initial policy time is not silently equated with current runtime
time. A changed view with rebound state and candidate still has the same CONFIG
context; a stale candidate view rejects. These deliberate positive cases
preserve native behavior rather than strengthening it without authority.

Lean examples reuse the original native CONFIG vote and construct its complete
policy/initial-state decoding through checked encoding components. Two finite
SHA samples (snapshot and CONFIG context) are explicit; SHA implementation,
cryptographic signature verification, exporter trust and native implementation
refinement are not proved. Python's DRC1 reader retains its smaller diagnostic
resource scope; the mandatory Lean reader uses the existing native bounds.

General native admission for nonempty graphs, mixed command/vote history,
request/receipt caches, DRS1 snapshot bytes, physical scan/repair/unknown-outcome
provenance and complete public/native recovery remain open. This layer cannot
discharge `nativeArithmeticRecoveryRefines`. Contract freeze, clean offline
reproduction, independent reviews and runtime/profile/GPU/Docker acceptance
remain mandatory. No Formal GO, local acceptance PASS or BenchmarkResultQC.

Reproduce the finite native comparison with
`python formal/scripts/check_native_config_admission.py --vcvars <vcvars64.bat>`;
without that option the script verifies retained inputs/source hashes/results.
`generate_native_config_admission.py` deterministically regenerates the Lean
component examples. Build the mandatory Lean project and run the formal tooling
tests; scoped checks do not replace unavailable aggregate `make formal-check`.
