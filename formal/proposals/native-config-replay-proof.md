# Computed CONFIG/command native replay candidate

Historical stage scope: the current API selects this lane with explicit
`config` mode. The subsequent shared CONFIG/ISC fold and its separate evidence
are described in `native-mixed-replay-proof.md`; counts below retain this stage.

T044/T048/T049/T053/T057/T060; amendment0001. **NO_GO**. This is a
singleton CONFIG / empty certificate graph subdomain of the native runtime.
It does not discharge `nativeArithmeticRecoveryRefines` or authorize runtime edits.

## Checked computation

`NativeConfigReplay.recover` decodes and checks the entire original startup
policy and initial native state through `NativeConfigAdmission.prepare`, even
for an empty journal. It derives the initial tick from that policy, parses the
typed snapshot's state and starts both caches empty. Neither a caller-supplied
admission Boolean nor a recovered-state equality is accepted.

Each outer journal position must be exactly previous+1 and fit uint64. A command
calls `NativeCommandReplay.step`: the existing native transition computation
rederives all three output byte strings, checks monotonic logical time, rejects
duplicate request IDs, preserves its original receipt, and invalidates vote
authority. The active clock marker is `some 0`; its payload is not used as the
current time. Current time comes from the startup policy and then the actual
replayed commands.

A vote must have empty state/effect sections and the exact ASCII SHA-256 digest
of the complete startup policy in its record section. Actual state/policy/vote
decoders and computed CONFIG admission run on the preceding replay state in
recovery mode. The frame must retain the outer sequence, original actor/epoch/
context/body/parent and fit the receipt encoder. No existing context may be
appended again. The checked native parent record is retained beside the original
vote and internally constructed DVREC001 receipt. The cache follows journal
order; it is a representation of the native sorted VoteJournal, not a proof of
its container implementation or exception/error-code equivalence.

The vote leaves state, tick and command cache unchanged. Native state-local
`durable_sequence` and the outer command+vote journal sequence are distinct.
They are not silently equated. Successful histories prove outer position and
that command-cache count plus vote-cache count equals the number of records.
They also derive original command and vote provenance and uniqueness of both
cache keys. Command provenance includes actual recomputation of every output;
vote provenance includes computed admission and original canonical frame bytes.

## Snapshots and historical retry

A positive snapshot position compares against the state produced by actual
replay at that position. At a vote position this is the preceding state, **not
the empty state section of the vote WAL record**. The positive-position theorem
extracts an actual checked step and its computed state from the history.
Sequence-zero snapshot state is parsed but does not replace or have to equal
the initial state; this preserves the inspected native behavior. Snapshot
checks here take a typed position/state; DRS1 decoding in Lean is still open.

Command retry reuses the existing request cache. Vote retry checks its original
key, canonical frame and content ID before returning the stored receipt and
parent record. It does not reapply fresh admission, current-time or current-state
checks. General lemmas preserve retry across state/clock/sequence changes while
retaining the same cache. Different canonical bytes in the old context reject.
DVREC001's reserved bytes stay zero; the operational replay flag does not
rewrite receipt bytes. No successful replay function sends anything.

`recoverObserved` first checks actual DRW1 framing, ordering and checksums. It
accepts only an observation with no torn flag and no remaining tail. This says
nothing about whether an observed empty or complete prefix is the whole physical
file. It cannot establish durable absence, unknown-outcome resolution, readiness,
authenticated provenance or permission to truncate/repair a file.

## Executed evidence and scope

Two Lean modules provide 26 general helpers, 21 component/kernel/composition
proofs and 20 definitions, all included in the mandatory axiom audit. The
original CONFIG policy/state/frame/receipt are reused. Four finite actual hash
samples establish an actual CONFIG vote step, snapshot comparison and historical
retry. A separate general theorem composes the vote with an actually checked
next command; it is not a newly kernel-evaluated complete native mixed trace.
The earlier ISC1/freeze2 fixture remains unchanged and unsupported by this CONFIG
gate. Arithmetic sequences5/6/8 and all original native witnesses are unchanged.

The fresh C++ harness compiles twelve unchanged pinned units (28 source blobs)
from `60c692f6e391f839829dfc64e93380db54cd507b` under the recorded MSVC strict
flags. A separately executed native journal has CONFIG1, config-command2,
view-command3 and abort-command4. All32 cases compare computed Python outcomes
and exact native returned bytes:14accept/18reject. These include historical
vote/command retry after movement and reopen, positive snapshots at both kinds,
zero/ahead/wrong snapshots, policy changes, duplicate keys, order/sequence
changes, command output substitutions and backwards time. Failed operations
return no receipt; historical retry leaves the journal unchanged. These are
finite local Runtime/WAL executions, not production mutants, OS power-loss,
arithmetic execution, network delivery, cryptographic signer validation or an
authenticated exporter.

Python reader/resource limits remain diagnostic restrictions; they are not a
proof of all native allocation or admission bounds.

The eleven tooling tests also reject rehashed vote-section/output changes,
partial/corrupt observations, unsupported old ISC history, invalid empty-log
startup and report/source/receipt substitutions. Final stable-source build,
tests, axiom audit and regeneration results are in
`evidence/native-config-replay.json`. Compiler diagnostics normalize line endings and trailing whitespace; this does
not alter the compiled harness or compared outputs. Initial development compile/lint failures
are superseded by those final logs, not counted as passing evidence.

## Reproduction and remaining work

From the repository root, run Python with `formal/scripts` dependencies present:

```text
python -X utf8 formal/scripts/check_native_config_replay.py --vcvars <vcvars64.bat>
python -X utf8 formal/scripts/check_native_config_replay.py
python -X utf8 -m unittest discover -s formal/tests -p test_native_config_replay.py -v
```

From `formal/proofs`, use the pinned Lake/Lean toolchain:

```text
lake --no-cache build DeltaReduce
lake --no-cache env lean DeltaReduce/NativeConfigReplay.lean
lake --no-cache env lean DeltaReduce/AxiomAudit.lean
```

Self-review checked the distinction between startup/current state, vote/command
sequence, cached/fresh admission, vote-position snapshots and observed/physical
durability against the pinned runtime. It is not independent attestation.
Nonempty graph and other-action admission, all-policy completeness, DRS1 byte
decoding, independently authenticated initialization/scan/export, unknown
outcomes/repair, arbitrary failures and full public protocol refinement remain
open. Contract freeze, offline reproduction and independent review are still
required before formal authority, followed by runtime/profile/GPU/Docker gates.
No full recovery theorem, local acceptance PASS or Formal GO is claimed.
