# Whole CONFIG/ISC proposal admission and original mixed-journal comparison

T044/T048/T049/T053/T057/T060; amendment0001. Candidate only, **NO_GO**.

The original retained `after-state-command-retry` journal is NOT governed by
the preceding singleton ISC policy. Its complete DVPOL policy has two candidates,
CONFIG and ISC, in the original native order. Replacing it with a singleton would
change the policy identity recorded in the WAL. This stage keeps the original
policy bytes, initial state, ISC sequence1 and freeze sequence2 without filtering
or renumbering. A Python regression compares the fresh native first-two-entry
journal byte-for-byte with the earlier native-policy-wal observation.

## General Lean admission

`NativeProposalAdmission` parses the complete policy/state/vote through existing
checked decoders. `bindGraph` computes all proposed ISC bodies and their IDs,
the original state ID, configuration sets, whole policy canonicality, current
coordinates, profile references and closed-list membership. `checkCandidates`
validates every original candidate, including an unselected CONFIG candidate.
It derives action-specific context bytes, exact parents, body membership and
height/view. Only CONFIG and ISC are supported; finalized ISC and later graph
fields remain rejected.

List induction retains the exact original candidate list and order, length and
per-candidate source checks. `prepareSource` ties this to the original decoded
policy, not a policy rewritten to contain the selected candidate. Fresh vote
selection checks all original fields, current parent, phase, time, original
sequence, readiness/recovery and invalidation. Successful selection derives
original canonical vote bytes and, for ISC, the actual checked original body.
The checker takes no arithmetic/certificate approval callback or finite table.

All validators are constrained to native certificate labels in this subdomain,
including a CONFIG-only policy. This retains the previous ISC projection's
restriction; it is not a claim that every broader native CONFIG policy has these
restrictions. Native `State` is a typed intermediate; the public complete-byte
entry point runs the actual decoders before the graph check.

The small Lean vector module reuses actual original CONFIG/ISC candidate fields
and the previously checked ISC graph, with four finite SHA samples inherited
through a branch on the CONFIG context preimage. It checks both candidates,
selection of the second candidate, canonical ordering and fail-closed mutations.
These are component examples, NOT a new full-policy byte proof or Lean execution
of the complete mixed WAL. SHA remains a named function, not a general SHA proof.

## Executable mixed replay and native comparison

The Python ISC reader now exposes its common graph preparation. The old singleton
ISC and empty-graph CONFIG APIs keep their earlier scope. The shared Python WAL
fold has a closed choice of those CONFIG-only checks or the computed CONFIG/ISC
proposal gate; it accepts no external admission function. Every vote still binds
the whole original policy digest. Cached parents come from the actual selected
candidate, not the first candidate in the policy.

Native receipt action is derived from the vote kind: CONFIG1 versus ISC2. An
early expanded-checker draft retained the CONFIG-only receipt tag; fresh native
comparison detected the byte19 mismatch. It was corrected before final evidence.
The old CONFIG receipt bytes remain unchanged. A repeated freeze reaches native
core's AVAILABLE guard before the duplicate-command check, so its recorded error
category differs from the earlier CONFIG-only example; rejection is still exact.

The fresh harness compiles the same12unchanged native translation units and
28pinned source blobs at60c692f6e391f839829dfc64e93380db54cd507b. It exports both
actual vote and command receipts, then retries them after view/abort movement
and reopening. Its first two entries are exactly the earlier ISC/freeze journal;
subsequent view/abort entries are explicit additions at3/4, not a renumbering.
This fresh journal contains an ISC vote plus commands. CONFIG is an independently
checked, unselected policy candidate; no CONFIG vote is added in AVAILABLE phase.
The earlier CONFIG-vote journal retains its separate tests/evidence, not a claim
that both vote kinds executed in this one fresh journal.
Snapshot-position checks, backward clock, duplicate/conflicting identities,
policy substitution and altered state/effect/record bytes are checked. Native
runtime and WAL execute here in isolated temporary directories; no running demo
or implementation source changes, arithmetic guard override, network or power
loss is involved. Machine evidence records32finite cases, not universal native
equivalence or a new production-mutant suite.

Historical retry is a lookup of the original exact frame/request before fresh
admission. It returns the original sequence and receipt after current movement.
Fresh old authority remains rejected. Complete observed-byte scans reject torn
or corrupt tails; this establishes neither physical completeness nor verified
absence after a missing response. Zero-position snapshots retain the native
parse-only scope documented in NativeConfigReplay; they do not establish an
authenticated initial-state equality.

## Remaining boundary

This stage does **not** extend `NativeConfigReplay.lean` to the new admission
result. General mixed CONFIG/ISC Lean histories and a kernel-composed original
ISC1/freeze2 trace remain the next step. Reuse a single typed replay fold; do not
duplicate hundreds of history lemmas or replace computed checks with callbacks.
The Python/native finite comparison does not fill this missing theorem.

Snapshot/ledger availability and root origin, primitive authority provenance,
finalized certificate graphs and other actions, general DRS1 decoding, physical
scan/snapshot authentication, unknown outcomes, repair, full public-state/action
refinement and `nativeArithmeticRecoveryRefines` remain open. The complete-byte
diagnostic Python readers retain smaller resource bounds than native/Lean.
No full admission completeness, native authentication, READY/exposure/quorum,
formal GO or Feature010 local acceptance is established. Contract freeze,
offline reproduction, independent review and subsequent runtime/profile/GPU/
Docker gates remain required.

Reproduce component evidence with `python formal/scripts/check_native_proposal_replay.py`;
pass `--vcvars <vcvars64.bat>` for a fresh unchanged C++ run. Targeted tests:
`python -m unittest discover -s formal/tests -p test_native_proposal_replay.py -v`.
Build the full mandatory Lean project and audit; the existing mandatory44/45
failure and unfrozen phase0 remain explicit, not waived.

Final evidence assembly caught a missing explicit `bind` audit line: the earlier
inventory test matched the prefix of `bindGraph`. The audit now includes `bind`
itself and the inventory test compares complete lines. Final audit output must
contain all58exact declaration names; only the corrected-source checks count.
