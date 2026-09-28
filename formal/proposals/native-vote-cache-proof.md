# Complete executed native vote cache and historical diagnostic projection

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
Evidence: `formal/proposals/evidence/native-vote-cache.json`.

NativeVoteCache.capture executes the previous candidate mixed-journal step and
retains one source-bearing row for every ordinary or arithmetic vote. Ordinary
rows retain the actual NativeSelectedVote.Checked, its complete checked original
snapshot, ordered candidates and exact selected parents. Arithmetic rows retain
the actual Source, NativeVectorContext.bind provenance, computed PARAMETER/APPLY
result and NativeVoteMetadata image. Both retain the entire original WAL entry,
preceding canonical state and a separate all-vote ordinal. The ordinary candidate
body ID is not itself a public body; the original typed snapshot supplies its
primitive artifacts. No caller-supplied translated body or approval table is used.

General soundness AND completeness show this capture has exactly the same
successful candidate steps and final native machine as NativeArithmeticJournal.
Its complete native cache extension is the ordered map of all retained rows,
not merely a membership or count assertion. Original VOTE frames, signatures,
semantics, context, parents and receipt/global sequences are preserved. Strict
lookup accepts only one matching original validator/epoch/context key; missing
and ambiguous keys cannot become first-match authority. Lookup alone grants no
source authority: callers must retain execution/recovery provenance.

NativeCacheHistory extends that relation to arbitrary finite runs, typed recovery
and complete observed-byte recovery in both directions. Commands execute through
the same original checker and remain part of the actual input execution. Every
row has an executable original prefix, its actual capture/RowSource and suffix.
Recovery derives exact equality of the ENTIRE final native vote cache with the
ordered row projection. All-vote ordinals are exactly 1 through the vote count.
At each actual row position, original WAL sequence equals its all-vote ordinal
plus the number of preceding commands. This is not per-actor public numbering,
and is not an arithmetic-only renumbering. Original sequence bytes are unchanged.
Known complete scanning, exact-length Source alignment, complete policy startup,
snapshot checks and the earlier stronger snapshot-zero identity check are reused.
This proves equivalence to the previous candidate, not the production runtime.

NativeCacheProjection re-executes deriveExpectedNativeVote from each retained
arithmetic Source and original scan metadata. It checks complete data, envelope
and effect equality with the actually computed image, then encodes a diagnostic
receipt at the separate all-vote ordinal. The result is RecoveryKernel.Record;
these newly encoded diagnostic bytes are NOT original DVREC/WAL receipts,
physical persistence evidence or an authenticated NativeReplay.Resolved value.
The complete list traversal has a proved pairwise relation in both directions,
retains every row and derives exact ordinal order. It cannot filter out an
unsupported row or silently keep a successful subset. Ordinary rows currently
have no public-body projection and therefore reject the ENTIRE projection,
including when they occur after arithmetic rows. UNKNOWN also rejects.

The low-level row and projection constructors are mathematical data operations;
only the executed cache/recovery relation establishes source provenance. No
NativeVoteTrust instance, arbitrary env.input map, NativePrepared, ready event,
first-vote freshness or completed-recovery fact is manufactured. In particular,
executed scan arithmetic still has recovered=false. A diagnostic projection
cannot change this fact or re-admit a historical retry at the current state.

Kernel cases reuse the actual prior ISC1/freeze2 components under the same named
adapter-SHA equality, show exact native cache/parents/receipt and the different
global/vote counters, and reject duplicate/altered-ordinal lookups and ordinary
rows anywhere in a projected list. There is no new successful nonempty joined
arithmetic projection, full raw multi-arithmetic source capture or native write.
Python cases inspect the retained original four-entry WAL observation, its one
vote and three commands, and demonstrate codec-valid changed bytes with the same
cache key but different original vote identity. They do not claim admission of
those changed bytes. Original diagnostic sequences5/6/8 and147native witnesses
remain unchanged; no fixture expansion or new physical custody is asserted.

This closes the complete native-cache retention and all-vote/mixed-position
relation. Full public/draft durable equality remains OPEN: typed non-arithmetic
public body/context/parent projections, all actors, public sequence abstraction,
source/configuration/alias authority and authenticated live/recovery resolution
are not supplied by this layer. MetadataTrust, IndependentBinding, UnitSource,
initial/current/export/signature/custody premises remain explicit. Missing
original008 captures remain missing. Full phase/send/delivery/QC/current,
crash/unknown/torn/repair, arbitrary production snapshots, physical
persist-before-expose, concrete bounded codec/hash/exporter/full-graph resources,
native -00/-01/FULL_SIGNED_INT64 compatibility, contract freeze, clean offline
reproduction and independent review remain required. This layer does not prove
nativeArithmeticRecoveryRefines or authorize runtime/guard changes, local PASS,
BenchmarkResultQC or formal GO.
