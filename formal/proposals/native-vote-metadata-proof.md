# Source-derived metadata with lossless original vote retention

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
Evidence: `formal/proposals/evidence/native-vote-metadata.json`.

NativeVoteMetadata executes the prior original PARAMETER/APPLY selection and
source computation, then constructs the draft VoteMetadata and ExpectedNativeVote
from that actual VoteSource. No whole translated body, expected result, approval
table or authenticated metadata instance is supplied or invented. PARAMETER uses
the actual DerivedParameter, its exact domain/shard, APC projection and original
plan parent; APPLY uses actual NativeApply, its certified aggregate projection
and original ROOT parent. The complete body encoders operate on these results.
Original native body hash preimages and projected artifact hash preimages are
retained separately. They are different representations, not byte-equal IDs.

The actor and vote context have checked ASCII roundtrips. The original native
parent is decoded using the strict digest decoder, checked to be 32 bytes, and
re-encoded to the exact original 71-byte sha256 spelling. No finite alias map is
used. All six anchor context fields are compared with the original source
context, including checked original round/epoch/checkpoint byte spellings and
height/view. Source parameter context equality is checked by ExpectedNativeVote;
the APPLY context retains the original ROOT-derived preimage relation even though
the old low-level VoteSource.apply context predicate alone accepts any string.

The metadata time is the actual supplied event tick. Its validator flag computes
both local-validator equality and original policy membership. This is structural
membership, not signature verification or an authenticated committee export.
The conservative candidate recovered flag requires ready=true, recovery=false
and invalidated=false. It is explicitly not a proved interpretation of an
authenticated production event. Original selection already checks the actual
phase, deadline, invalidation and candidate parent chain. Existing runtime and
original guarded reference checker remain unchanged and reject arithmetic votes.

The result retains the complete original typed VOTE, every original parent slot,
and the separate draft envelope. The mixed-prefix wrapper additionally retains
the exact original DRW1 entry, signature, receipt container and original arithmetic
objects. It executes the prior whole original guarded prefix check, preserving
global command-plus-vote position and the exact original VOTE/DRW1 re-encodings.
The historical native semantics ID is not rewritten to the new draft semantics.
No old diagnostic arithmetic record at sequences5/6/8 is changed.

General rejection theorems show that these recovery-scan results cannot produce
NativePrepared even if a caller separately supplies authenticated metadata: the
actual prefix facts have recovery=true and ready=false, so recovered remains
false and NativeFresh fails. No mode/flag is flipped to manufacture eligibility.
The original prefix still cannot contain previous arithmetic votes. Connecting
an actually completed recovery/live event and the entire draft/public durable
set, rather than a matching count or caller-created state, remains required.
Draft NativePrepared sequences count draft votes; original WAL positions count
commands plus votes. This stage deliberately does not identify these sequences
or assert a complete pre-WAL bridge. First preparation is separate from retry.

Small kernel cases reuse the original native vote and parent components, plus
separately synthetic flags/policies. They check parent digest spellings, ASCII
representation, readiness/invalidation/membership and demonstrate that the
metadata alone loses signature/view/global position. The complete result retains
those original fields. These are not a new joined raw source-graph execution,
native capture, physical write or authenticated exporter/signature instance.

Independent Binding/aggregate/UnitSource/profile/current/source custody premises
remain. Unknown/torn/corrupt observations retain prior rejection; no absent-cut
exhaustiveness, repair/truncation permission, append/fsync/exposure, network/QC
power or recovery completion follows. Repeated arithmetic mixed histories,
arbitrary initial snapshots, full phase/send/delivery/current/crash/repair,
concrete bounded codec/hash/exporter resources, native -00/-01 and full-width
compatibility, amendment freeze, clean offline reproduction and independent
review remain open. This layer does not prove nativeArithmeticRecoveryRefines.
