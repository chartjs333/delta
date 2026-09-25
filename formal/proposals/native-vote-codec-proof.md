# Native DRC1 vote and semantic receipt binding (candidate)

T044/T048/T049/T053/T057/T060; amendment 0001. NO_GO.

NativeVoteBytes.lean adds an independently executable byte reader for the fixed
native VOTE envelope. It consumes the DRC1 version/type/length header, the map
tag and exactly thirteen fields in native sorted order, text tags, big-endian
lengths, and all input bytes. Common fields are the actual native schema1.0.0,
type VOTE and accepted old native formal semantics cc98f15a..., not the new
candidate semantics. This codec does not authorize substituting the candidate
semantics into a native build or lifting the arithmetic guard.

The specialized parser retains the default native 16MiB envelope and 4MiB value
limits. Thirteen flat text fields have fixed depth1 and are below the native
100000-member/32-depth defaults; other types, nested values and configurable
nondefault native limits are outside this specialization. It does not reuse the
older proposal decoder's narrower 16KiB/4096 limits. Receipt frame/context limits
still come from NativeReceiptBytes. No native allocation/time complexity or
general-purpose canonical decoder theorem is claimed. ASCII helpers construct
known ASCII constants only; incoming strings are bytes with printable checks.

Canonical decimal parsing checks nonempty ASCII digits, no sign/leading zeros
except the single zero, and the uint64 ceiling. Sequence must be positive;
height/view may be zero. Content IDs require sha256: followed by exactly64
lowercase hex digits. Context/kind/round/validator are nonempty printable text.
The protocol parser accepts an unknown nonempty kind; the receipt binding
separately restricts actions to the existing nine names. These are distinct
native rules, not a new admission restriction.

General proofs establish text/field/frame inverse parsing, preservation of all
ten variable fields and three constants, injectivity of frame encoding for
bounded printable inputs, semantic number/identity bounds, exact canonical
accepted frames and complete receipt binding. Neither an expected Vote nor an
approval Boolean is given to the parser. The semantic receipt decoder first
reads DVREC001, parses its actual frame, and checks exact sequence, context,
action/kind and ID. Success derives those equalities from executable branches.
Mismatches reject; the previous structurally valid unauthenticated container now
rejects. Operational replay remains absent from canonical receipt bytes.

The hash adapter receives exactly ASCII deltareduce:003:vote:v1, one NUL, and
the entire DRC1 frame. It must return32 bytes; lowercase hex/prefix encoding and
71-byte ID length are derived. The Lean module DOES NOT prove SHA-256, collision
resistance or adapter/native implementation equivalence. Generated examples use
separate exact-preimage finite digest lookups; every other input returns no
digest. Python hashlib and the actual native SHA implementation agree on the
retained cases. This is byte/hash-input binding, not certificate authentication,
signature verification, independent producer provenance or native admission.

Three unchanged PR50 translation units from
60c692f6e391f839829dfc64e93380db54cd507b execute the actual protocol parser,
canonical encoder and SHA. Forty-nine cases include the nine original frames,
two uint64 endpoints and the deliberately accepted unknown kind;37 malformed
frames reject. Cases mutate decimals, content IDs, nonempty/ASCII constraints,
common constants, missing/extra/duplicate/reordered fields, tags, version/type,
length/truncation and trailing bytes. Re-encoding every accepted native frame
returns exact input bytes. These are codec cases, not Runtime/WAL execution or
production-mutant/TLC evidence; PARAMETER/APPLY are still guarded at admission.

Kernel examples reuse the nine existing complete native receipt/frame fixtures;
each is a standalone sequence1 codec fixture, not a consecutive nine-vote journal
or the separate proposal history with sequences5/6/8. They prove frame bytes,
full semantic receipt success and four changed-field
rejections for each, plus decimal/text/hash-width boundaries. Shared small text
encoding lemmas avoid reducing whole encoders in one giant dependent expression.
Generated output is byte-exact reproducible; all named declarations are included
in the mandatory project and axiom audit. Only final stable-source runs count;
discarded draft namespace/UTF8/whole-frame reductions are not passing evidence.

Run generate_native_vote_codec_vectors.py with --vcvars for the existing VS2019
vcvars64.bat to reproduce native execution. Without it, validate the pinned
observations and regenerate the Lean/vector files. Evidence lives in
formal/proposals/evidence/native-vote-codec.json and its sibling directory.

Remaining: establish actual DVPOL001 policy and DRW1 WAL entry decoding/replay,
initial policy/source provenance, and compose original semantic receipts with
the reachable public/native history. Full CloseInput/configuration/availability/
phase/send/delivery/QC/current/crash/unknown behavior is not obtained from parsing
a vote. Missing response remains neither proof of absent append nor exposed
receipt. nativeArithmeticRecoveryRefines stays OPEN. Contract freeze, clean
offline reproduction and independent reviews are still required. No GO or
SIMULATED_LOCAL acceptance is issued; no runtime/demo code is changed.
