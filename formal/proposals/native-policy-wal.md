# Native policy identity and local WAL recovery (candidate)

T044/T048/T049/T053/T057/T060; amendment 0001. NO_GO.

This stage executes the unchanged Windows native Runtime, operational policy/
receipt codec and WAL from PR50 source
60c692f6e391f839829dfc64e93380db54cd507b. Twelve complete translation units,
including the original synthetic vote fixture, are compiled with MSVC C++20.
No runtime source or arithmetic guard is edited; no DELTA mutant macro is set.
NOMINMAX is only a Windows header macro. Twenty-eight exact Git blobs are pinned.

The runs create separate fresh directories under ignored formal/build/native-policy-wal.
They never open presentation data or restart any demo. No directory is deleted
or moved. Native Windows fflush/_commit and snapshot replacement code executes.
This is real local runtime/file I/O with injected exceptions, not physical
power-loss/OS-process-kill testing, POSIX descriptor/custody qualification,
FFM/sidecar/network execution or Feature010 acceptance.

## Full policy versus state identity

The native operational policy format is DVPOL001. Runtime retains the policy
by value, serializes it with encode_vote_policy_v1, hashes the full bytes with
SHA-256, and stores the 64 ASCII lowercase digest characters in the vote WAL
entry's wal_record_bytes section. This digest has no added hash-domain prefix.
It is distinct from snapshot.state_id, which binds native DRC1 RoundState bytes.
The previous component counterchecks do not bypass this separate durable policy
binding: eight valid changed policies are rejected against an existing WAL.

An inventory checks all 33 VoteAdmissionSnapshot fields, in header/encoder/
decoder order. This is a syntactic coverage check, not general encoding
injectivity. Nine original native action fixtures encode, parse and re-encode
exactly. All 1,920 truncated prefixes of the ISC policy reject in the actual
native parser, as do five malformed header/version/reserved/trailing/oversized
cases. These finite cases are not parser fuzzing or a complete decoder proof.
The fixture does not populate every optional nested field at once.

Mutations cover soft/hard deadlines, initial time, finalized config assertion,
ISC root/commitment/AC identity and rebound native state root. They retain valid
policy shapes. Each altered policy can open its own empty directory, but cannot
open the original vote WAL. Original WAL bytes remain unchanged after rejection.
Opening a durable vote WAL without a policy also rejects.
Caller mutation after Runtime construction leaves the retained policy unchanged.

## Actual receipt and recovery observations

The complete output contains 62 codec/runtime observations. A fresh ISC vote is
appended at sequence 1, syncs, then returns a native VoteReceipt. Exact retry
does not append. Same-context conflict rejects before another append.
A native snapshot is written and checked; reopen reconstructs the original
vote/frame/admission and returns the identical canonical DVREC001 receipt.
Operational replay=true is returned separately: the receipt's reserved replay
byte is always zero. Retry is not allowed to change the durable proof bytes.

A separate two-entry history persists ISC, then applies the existing
FINALIZE_INPUT_FREEZE state command. Historical retry still returns the original
receipt, including after reopen, while a fresh configured vote rejects without
append. The state command's sequence becomes 1 while the all-entry WAL sequence
is 2; these counters are not equated. This is not an ApplyQC current-pointer
advance or the old public eight-vote trace. Its separate native fixture sequence
1 does not replace original public arithmetic sequences 5/6/8.

Six existing native crash hooks run through exception/reopen/retry:

| Hook | Observed WAL before reopen | Recovered vote count |
|---|---|---|
| before_wal_append | empty | 0 |
| during_wal_append | exact half-frame, subsequently truncated by native recovery | 0 |
| after_wal_append_before_durability | empty | 0 |
| after_durability_before_commit | complete synchronized frame, no receipt returned | 1 |
| after_commit_before_effect_return | complete frame, no receipt returned | 1 |
| after_effect_copy_before_return | complete frame, no receipt returned | 1 |

The names do not define the executed I/O: after_wal_append_before_durability
currently throws BEFORE append_and_sync. It is not evidence of an ambiguous
append/barrier outcome. The two final hooks share a branch before returning the
vote receipt; the second does not newly test a physical copy/transport failure.
No response/receipt at the durable-before-commit cut coexists with a complete
recoverable vote. The harness never infers absence from the missing receipt.
Its diagnostic reader rejects partial WAL input as incomplete; only the actual
subsequent native scan/truncation produces the tested empty recovered prefix.

Checksum-corrupt WAL and snapshot files reject open. PARAMETER and APPLY
record_vote calls reject at the unchanged authoritative-input guard with no WAL
append. Native arithmetic is not executed by these runs.

## Independent byte checks and scope

The proposal reads exact DRW1 frame lengths/sequence/checksums/sections, DRS1
snapshot/state checksums and DVREC001 frame/context/sequence/ID. Every observed
vote WAL entry is bound to the SHA-256 of its full startup policy and to the
original canonical DRC1 vote. Receipt and snapshot preimages are checked.
These bounded 1 MiB diagnostic readers are not the general production parsers.
The policy helper only hashes bytes; native parse/re-encode provides the
observed codec validation. A rehashed wrong policy digest in a WAL frame still
fails the expected-policy relation. Exact raw bytes are retained in evidence.

Read-only source inspection traces the remaining producer boundary:

- delta_abi.cpp copies caller policy bytes, parses them, then opens Runtime.
- sidecar_server.cpp receives an opaque policy field and parses it at OPEN.
- SidecarSupervisor.java copies configured opaque bytes into that OPEN field.
- vote_fixture_exporter.cpp creates test policies from the synthetic fixture.

These routes bind/copy/validate data but do not establish its derivation from a
complete authenticated public state in this proof. They were inspected, not
executed as a joined FFM/sidecar profile. No independent producer or source-to-
public-state authority is fabricated from a hash or from successful empty open.
The native source still carries accepted old cc98f15a... semantics; the candidate
formal amendment is not thereby merged or GO.

## Reproduction and remaining work

Run python formal/scripts/generate_native_policy_wal_vectors.py, adding --vcvars
with the VS2019 vcvars64.bat path for compile/run. Run unittest discovery with
-s formal/tests -p test_native_policy_wal.py. Eleven new tests validate complete
observations, policy/WAL/receipt/snapshot relations, crash-cut distinctions,
corruption, mutation rejection, raw source pins and byte-exact reproduction.
Evidence is formal/proposals/evidence/native-policy-wal.json and its directory.
No generated executable or private key is committed.

Next connect this exact policy/WAL/receipt relation to the mandatory Lean/public
recovery relation using explicit adapters for DVPOL001/DRW1/DVREC001 and the full
state/action projection. Begin with the durable policy identity and original
canonical receipt binding; do not relabel JSON proposal receipts as native bytes.
The trusted initial policy producer, complete public CloseInput/configuration/
commitment-content-availability/root projection, all-vote phase/send/delivery/QC/
current composition, arbitrary failures/snapshots/repair and actual unknown
outcomes remain open. The finite local runs do not discharge
nativeArithmeticRecoveryRefines (mandatory audit still 44/45). Native arithmetic
guard removal still requires exact merged formal GO. Contract freeze, offline
clean reproduction, independent reviews and joined profile/GPU/Docker evidence
remain mandatory; no local PASS or qualifying GO is issued.
