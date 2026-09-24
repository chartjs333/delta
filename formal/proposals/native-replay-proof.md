# Native arithmetic replay adapter

Candidate amendment 0001, T044/T048/T049/T057/T060. `NativeReplay.lean`
instantiates the checked journal kernel with actual native arithmetic extraction
and diagnostic encoding. It adds thirteen general helper theorems and six audited
functions. It does not yet discharge `nativeArithmeticRecoveryRefines`: the full
public trace bridge, other vote kinds and exporter provenance remain open.
Mandatory coverage stays 44/45; production runtime and arithmetic guards do not
change, and this is not Formal GO.

## Independent inputs and checked replay

`Environment.input` resolves historical native metadata and the available typed
graph by the formal actor/context key, independently of request/body bytes. Its
`Input` retains the separately authenticated anchor and metadata, exact store,
optional complete `Binding` and the named metadata-authentication premise.
Missing context or graph yields no admitted data or effect. `resolve` runs the
actual PARAMETER/APPLY derivation and compares the whole derived `VoteData`
(context, authority, command and body) with the record. It also enforces the
canonical request byte bound. The expected result is not supplied as an admission
flag or a record-table entry.

Admission checks the original native readiness, role, sampled deadline, integer/
identifier/hash bounds and all three then-current pointers. The replay kernel
separately checks native next sequence, context absence, exact effect and exact
receipt. `acceptedVoteHasPreparation` constructs a full `NativePrepared` witness
from these checks and proves that its entire record equals the stored record.
No recovered-state equality, row/result equality or arithmetic-admission axiom is
assumed. Historical retries use the original saved record and do not re-admit its
old parent after current advances. A fresh old-parent vote is rejected.

`checkApply` independently resolves the graph for a certificate, recomputes the
complete APPLY body and checks the parent plus computed next model/optimizer
hashes. Its authenticator receives the exact derived body, anchor and certificate
(including next checkpoint). Quorum/lineage authentication remains an explicit
premise; it is not inferred from body equality. Only that checked certificate can
drive the existing parent-to-next CAS or exact idempotent current replay.

The independent `NativeTransition`/`NativeHistory` relation contains actual
preparation or checked APPLY derivations at every step. `replayHasNativeHistory`
derives that history by induction over accepted sequential replay.
`genesisReplayHasNativeProvenance` starts from an empty arithmetic journal and
derives every retained record and its order. `preparedRecordRecovered` preserves
the complete original record through replayed prefix and suffix, including after
current advancement. Conflict does not replace it or allocate another sequence.

The presence/absence helpers use authenticated exact-prefix scans and replay
through this native adapter. A complete surviving record reconstructs the native
history and original retry receipt even when no response was observed. Verified
absence reconstructs only the exact preceding prefix. An ordinary old-prefix
scan does not prove absence; incomplete stays unknown, corrupt/ambiguous stays
blocked, and blocked recovery cannot silently resume. Actual scan authentication
and physical completeness remain named external premises.

## Explicit serialization failure

The generic `RecoveryKernel.Adapter.effect` and `.receipt` now return `Option
Bytes`. The old total-function interface could represent an encoder failure only
as some byte value. That was insufficient to instantiate real partial encoders:
an empty-byte fallback must not become a valid journal record. `validVote` now
requires successful encoding of both exact stored outputs; `prepare` rejects a
failed effect or receipt before producing a pending record. The native receipt
encoder also rejects zero/out-of-range sequence and a substituted effect.

This closes a gap in the proof adapter. It introduces no new protocol outcome,
production WAL format, public trace action or runtime implementation change.
All existing replay/provenance/retry theorems and 37 prior replay examples are
rechecked with the partial interface. New examples explicitly reject failed
encoders even when the stored effect/receipt is empty.

## Executed examples and limits

`NativeReplayVectors.lean` contains 42 kernel-decide examples. Unlike the earlier
finite admission table, the new adapter recomputes all arithmetic and receipt
bytes. It accepts the three exact pinned records at original sequences 5, 6 and
8 against explicitly supplied earlier prefixes. A separate three-vote arithmetic
journal uses sequences 1, 2 and 3, receipts independently encoded by Python, and
replays from empty state through APPLY/current advance. This is deliberately not
the complete public trace: its five other vote kinds still require their own
admission/provenance bridge. No original trace sequence is rewritten.

Negatives cover missing context/graph, substituted authority/body/command,
sequence/receipt/effect, receipt bounds, failed encoding, wrong QC parent/next
model/optimizer, missing graph and failed QC/scan authentication. Other cases
cover exact historical retry, conflict, stale fresh admission, persisted but
unexposed recovery, verified absence, truncated/ordinary-prefix scans and blocked
or incomplete recovery. Five generator tests require exact reproduction and
reject mutated receipt/body, wrong role or absent optimizer before output.

Input decoding and hashing still use the twelve pinned artifact strings and
finite output samples. Metadata/QC/scan trust is synthetic in examples. This is
not a general input decoder, SHA implementation, exporter, C++ execution or new
production TLA-mutant result. The initial current pointer and independently
resolved historical event metadata need authenticated provenance. Live-call
time/view/epoch sampling, public state roots/certificate exposure, all vote kinds,
exact full-public-journal prefix/root relations and physical WAL/snapshot/repair
remain additional work. The conditional arithmetic-only history must not be
advertised as the missing complete native/public recovery conjunct.
