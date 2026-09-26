# Native summary-command reconstruction (candidate)

T044/T048/T049/T053/T057/T060; amendment 0001. NO_GO.

NativeTransition.lean reconstructs the seven commands in the pinned native
transition.cpp from decoded COMMAND and ROUND_STATE inputs. It checks round,
height, view, phase, ticket/availability limits, nonempty freeze, terminal state
and uint64 increment bounds. FINALIZE_ROUND_CONFIG preserves the whole state
and its transition counter; every other accepted command increments that
counter. ADVANCE_VIEW requires the next view exactly. Aggregate updates only
the modeled root and phase; preserved fields are proved explicitly.

The result is constructed from inputs, not accepted by a caller-provided
predicate or next-state equality. The generated decimal counter is checked
against its mathematical value and StateValid before acceptance. A general
Nat-to-decimal completeness proof is not asserted; this executable validity
check cannot admit a mismatched encoding. This layer does not yet prove the
entire C++ implementation equivalent for all inputs or classify all native
error codes parametrically. The finite native cases compare exact error codes.

The model builds the ordered PERSIST_STATE and PUBLISH_CERTIFICATE effects,
all eight EFFECT_BATCH fields and all ten inner WAL_RECORD fields, including
original request/actor/round, prior/command/next/effect identities and transition
sequence. Encoding uses the actual nested array/map tags and original native
schema/semantics. The fixed shape is within native default collection/depth
limits; every dynamic text value and complete envelope has its default byte
bound checked. The two effect IDs share a prefix and use :01:persist then
:02:publish. This is construction of this exact pair, not a generic arbitrary
effect-batch parser or a theorem for custom native parser limits.

All five IDs are computed under the actual domain + NUL + complete bytes
preimages. SHA is still an explicit byte function, with finite actual samples
in examples. The build witness derives exact computed fields and ID preimages.
It is not a proof of SHA, hash collision resistance or exporter authentication.
The low-level build function is a constructor parameterized by a next state.
Only execute/fromBytes/replayEntry first compute that state with step; a
standalone build result supplies no transition authorization.

replayEntry independently decodes the prior state and original stored command,
executes the modeled transition, and compares ALL THREE stored state/effects/
inner-WAL outputs. Substitutions reject; parsed next-state validity alone is
not enough. scannedExecution composes this with NativeWalScan, retaining the
original all-entry position/sequence and exact outer DRW1 frame. The prior
state is an input here: there is not yet an inductive mixed vote/command
runtime history that derives it from configured initialization or a snapshot.
No readiness, physical persistence, receipt exposure or send follows.

A fresh isolated C++ harness compiles four unchanged units from pinned source
60c692f6e391f839829dfc64e93380db54cd507b (canonical, SHA, protocol, transition).
Its 59 cases produce 21 accepted results and 38 rejections; all ten existing
transition error categories are exercised. Exact next-state/effects/record
bytes and all five content IDs match the separate Python reconstruction.
The 42 phase/command combinations and bound/context cases are finite tests,
not production mutants, compiler-independent proof or arbitrary interleavings.
Source hashes, compiler and flags are retained. No fresh Runtime/WAL/crash run
or native PARAMETER/APPLY admission is claimed.

Lean vectors check the same command rules and reconstruct all three output
byte strings from the original native FINALIZE_INPUT_FREEZE journal entry.
The original WAL sequence remains 2, while the state's transition counter
becomes 1 from configured state 0. The previous vote stays sequence 1. The
separate diagnostic arithmetic 5/6/8 history is not renumbered. Byte/hash proofs
reuse checked components. Negative replay examples alter each output section.

Counterchecks intentionally retain the scope boundary: the pure core accepts
an older logical tick and a syntactically valid aggregate body without a QC
object. Monotonic time, request retry/cache behavior, native vote policy and
higher-level certificate authorization belong to runtime reconstruction, not
this summary transition. There is no claim that this RoundState represents all
64 public protocol fields or that computed effects are externally sendable.

Next compose actual command replay with request IDs, logical time, exact
receipt caches, authority invalidation, vote admission/policy and snapshot
checks from independently bound initialization. Authenticate complete scans;
unknown or incomplete observations do not prove absence, and corrupt/ambiguous
recovery stays blocked. Then connect the complete public action/send/QC/current
relation. nativeArithmeticRecoveryRefines, arbitrary failures/repair, contract
freeze, clean offline reproduction and independent review remain required.
No formal GO or separate local acceptance PASS is issued.
