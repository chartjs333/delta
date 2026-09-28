# Repeated source-checked candidate arithmetic journal

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
Evidence: `formal/proposals/evidence/native-arithmetic-history.json`.

NativeArithmeticJournal defines a separate candidate mixed step. Each arithmetic
input supplies actual primitive source bytes, Q inputs/permission, application
root/profile where relevant, and an independently premised Binding. Its Source
contains a proof that NativeVectorContext.bind actually loads those inputs.
The step compares the entire policy bytes and preceding canonical state bytes
with that source. It then executes NativeArithmeticPrefix.compute, including
original whole-policy selection, parent/body identity, phase/deadline checks and
the actual DerivedParameter or NativeApply computation, and derives the complete
NativeVoteMetadata image. No arithmetic admission callback, Boolean approval
table, whole body translation or arbitrary expected-state equality is supplied.
The loader equality is the actual existing executable graph relation, not an
external assertion that two translated states match. Independent Binding,
HashAdapter, aggregate, source availability and custody premises remain explicit.

The original VOTE, all original parent slots and exact receipt/frame/context
identity accompany each checked arithmetic result. The candidate cache uses the
original native Stored representation; the distinct projected image and source
are retained at the executed step, not mistaken for an original Stored body.
Every record checks the original global sequence, exact policy ID, vote key
freshness, empty vote state/effects and snapshotGuard on the actual preceding
state. Commands and non-arithmetic votes execute unchanged NativeConfigReplay
whole steps. An arithmetic input without a source remains subject to its
original rejection guard. An extra source on a command rejects. Invalidation is
monotone; supplying another Source cannot reset it or invent an authority refresh.
The original guarded checker and production runtime are unchanged.

NativeArithmeticHistory folds this step over an arbitrary finite input list.
Its closed History records only executed steps. General theorems derive sequence,
command-plus-vote counts, unique request/vote keys, monotone time/invalidation,
and actual executable pre/step/suffix provenance for every stored vote. Every
arithmetic input has its actual checked source computation at its exact prefix
position; the API has no first-arithmetic-only restriction. This is a conditional
general relation, not a claim that any desired sequence or phase is reachable.
Recovery starts from complete original prepareWhole and initialMachine, checks
full snapshot coverage and returns only a completely executed history. Exact
retry uses the existing read-only historical cache lookup and preserves its
original position rather than re-running current first-vote admission.

Snapshot position zero has an additional explicit candidate restriction:
snapshot.state must equal the initial canonical state bytes. The existing
NativeCommandReplay.initialMachine marks zero matched without comparing those
bytes itself. This new check is not a change to, or an equivalence claim about,
the original guarded replay/runtime contract. Positive snapshots have an actual
prefix/step/suffix witness with the matching full state, not just a sequence.

The byte front end requires a known observation, complete NativeWalScan.check,
no torn flag or tail, and an exact-length positional alignment with sources.
Both complete entry and source lists are retained; zip truncation is impossible.
Original checked frame partitions and global positions are retained unchanged.
UNKNOWN rejects even with an empty source list. Corrupt/incomplete observations
cannot be interpreted as an empty durable journal or authorize repair/truncation.
The caller's observation and initial-state physical provenance are still open.

Kernel cases lift the previously checked original ISC1/freeze2 execution through
the new no-source branch, using its component lemmas and an explicit adapter-SHA
equality. Other small cases cover source shape/position, invalidation, reorder,
duplicate, unknown and zero-snapshot mismatch. There is no new successful joined
multi-arithmetic raw fixture, authenticated source capture or physical native
write. Original diagnostic arithmetic bytes/sequences5/6/8 and historical cc98
semantics stay unchanged. Python checks use the already retained original mixed
WAL observation and reject altered order, missing prefix, duplicate, torn and
corrupt frames; these are scanner checks, not an arithmetic-admission oracle.

Recovery-scan images still have ready=false/recovery=true/recovered=false and
cannot pass prepareNativeFirst, even with a separately supplied authentication
premise. No NativeVoteTrust instance or live-ready completion is invented. Full
prior draft/public durable contents, original mixed-position versus draft-vote
position correspondence, authenticated completed recovery/live events and the
lossless NativePrepared bridge remain open. This typed finite replay does not
prove arbitrary production snapshots, full phase/send/delivery/QC/current,
crash/unknown/torn/repair, physical persist-before-expose or absence/exposure
semantics. Concrete bounded codec/hash/exporter/full graph resources, native
decimal -00/-01 and FULL_SIGNED_INT64 compatibility, missing original008 captures,
amendment freeze, clean offline reproduction and independent review remain.
This layer does not prove nativeArithmeticRecoveryRefines or authorize native
guard changes, local acceptance PASS, BenchmarkResultQC or formal GO.
