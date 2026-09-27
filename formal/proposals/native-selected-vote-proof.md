# Selected native VOTE admission (T044/T048/T049/T053/T057/T060)

This amendment0001 proposal composes selected VOTE checks with the actual complete
`NativeCandidateAuthority.bindPolicy` on the original policy and state. It keeps
the current native arithmetic STOP. It does not discharge
`nativeArithmeticRecoveryRefines`, issue local PASS, or authorize runtime changes.

## Exact source boundary

Reference source is `60c692f6e391f839829dfc64e93380db54cd507b`, specifically
`delta-core-cpp/src/certificates/vote_admission.cpp` and
`delta-runtime-cpp/src/runtime.cpp`. The native source checks the whole policy,
the vote shape and kind, then rejects PARAMETER/APPLY because the current policy
lacks authoritative arithmetic input bytes. Only after that does it select the
first original candidate by action, height, view and exact context.

`NativeSelectedVote.checkAdmission` executes the existing complete snapshot and ALL
candidate authority checks, selects the first matching checked entry, and checks:

- original vote validity, action/kind and the production PARAMETER/APPLY guard;
- local validator, epoch, round, height, view, context and complete body ID;
- the candidate checkpoint equals the actual state parent;
- original vote sequence equals the expected WAL sequence;
- live readiness, no authority invalidation, exact action phase;
- VIEW has no abort requests and `soft <= tick < hard`;
- ABORT resolves its actual body, requires the configured reason and either the
  exact round/reason request or `tick >= hard`;
- ordinary actions have no abort requests at all and `tick < hard`;
- the runtime tick/expected sequence fit their native uint64 fields.

The phase relation covers all nine native actions and six native enum values.
Although the phase function describes PARAMETER/APPLY, the composed checker
rejects both in live AND recovery modes. Failure checks consume the same computed
original snapshot tail; no empty graph, replacement candidate policy, translated
body or approval callback is supplied. Original-list and first-find lemmas show
which original candidate was selected. The byte wrapper decodes original policy,
state and VOTE, retaining exact canonical re-encodings and original actor/context/
epoch/sequence. Raw `checkVote` and `checkSelected` are component APIs; they do not
authenticate a caller-constructed bound policy. Only `checkAdmission`/`fromBytes` execute
the whole snapshot. The Option interface establishes successful admission and
rejection, not native exception codes or precedence between malformed inputs.

## Recovery is not historical retry

In this predicate, recovery mode bypasses ONLY the readiness bit. General lemmas
retain all identity, arithmetic guard, current, phase, invalidation and deadline
checks. It models validation of a new record or a record encountered during a
scan with its original recovered state and expected sequence.

Actual `Runtime::process_vote` classifies an exact journal replay BEFORE fresh
admission. That branch returns saved frame, sequence and admission projection.
It must not be subjected to new current-parent/deadline checks. Actual startup
scan instead checks the original WAL policy identity, uses recovery-mode admission
on the recovered state, and then rejects duplicate journal records. This source
ordering is checked by the tooling tests but is not newly proved as a joined
journal/WAL theorem here. RuntimeFacts, scan completeness and original-state
provenance remain unresolved assumptions, not a Boolean recovery attestation.

## Evidence and limitations

Vectors reuse the nine original decoded VOTE records and the independently pinned
original policy observation. Seven non-arithmetic actions have positive component
checks; PARAMETER/APPLY have live and recovery rejections. Phase table, identity,
wrong current/sequence, readiness, invalidation, exact deadline boundaries, missing
abort body, configured reason and foreign/mismatched request cases are checked.
The original CONFIG policy/state/VOTE byte wrapper is composed end to end. Other
component state/tail assemblies are explicitly synthetic, not a newly executed
complete nonempty/mixed native policy. Request-only examples with altered abort
reasons establish just the enabling predicate, not rehashed/authenticated bodies.
A signature-substitution countercheck passes syntactic validity and deliberately
demonstrates the absence of cryptographic signature authentication.

Finite SHA adapters and synthetic fixture custody remain named premises. No
fresh native execution, TLC model run or production mutant suite is claimed.
Existing native decimal canonicality incompatibility for `-00`/`-01` stays open.
No existing native artifact, envelope or receipt is rewritten. CurrentPointerCommand,
actual arithmetic input admission, complete nonempty policy composition, physical
WAL, exact historical retry/recovery, unknown outcomes/repair, full 64-variable
public-state refinement, arbitrary snapshots/availability, exporter/SHA/signature
authentication, contract freeze, offline reproduction and independent reviews
remain required. Mandatory44/45 remains FAIL and the formal report remains NO_GO.

## Reproduction

Run `python formal/scripts/generate_native_selected_vote.py`, its unittest module,
the full Lean build and AxiomAudit. Machine-readable evidence is
`formal/proposals/evidence/native-selected-vote.json` and its adjacent directory.
GNU make is unavailable here; scoped checks do not claim aggregate `make formal-check`.
