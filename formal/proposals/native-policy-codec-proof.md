# Complete native policy wire grammar (candidate)

T044/T048/T049/T053/T057/T060; amendment 0001. NO_GO.

This stage models DVPOL001 from pinned native source
60c692f6e391f839829dfc64e93380db54cd507b. It changes only formal proposal,
proof and verification tooling. Native runtime sources and arithmetic guards
are unchanged. This is a structural codec, not startup policy authority or
the missing `nativeArithmeticRecoveryRefines` theorem.

## General Lean relation

`NativePolicyCodec` implements finite named record, vector, ASCII text, Boolean
and unsigned big-endian integer formats. The generated `NativePolicySchema`
contains 35 record definitions with 238 declared fields, including every one
of the 33 immutable snapshot fields, all nested bodies/certificates and all
15 candidate parent fields. Names identify projections; names themselves are
not additional wire bytes. Nested vectors retain exact order and duplicates.

The parser consumes actual bytes. The encoder rejects mismatched tree shapes,
oversized integers/text/vectors and non-ASCII text. General structural induction
proves parsing every successfully encoded value with any suffix returns that
same value and suffix. The vector induction covers arbitrary bounded lengths,
not a table of approved policies. This gives whole-format encoding injectivity
and exact decode/encode round trips. Acceptance retains the entire parsed tree;
no initial/recovered-state equality or admission callback is supplied.

Rational numerators preserve their original 64-bit two's-complement word in
the Lean tree. `signed64` defines its integer interpretation; endpoint checks
cover minimum, maximum and minus one. The Python projection exposes signed
integers and compares them against the native `int64_t` fields. Fraction
validity, nonzero denominators and arithmetic admissibility are separate.

`NativePolicyBytes` extracts the policy header, original snapshot and every
candidate from the complete tree, then checks the native codec shape: nonempty
sorted distinct validators, role 1, closed abort reason, nonempty candidates,
action range, strict `(height, view, action, context)` ordering and globally
unique candidate contexts. The complete header/version/reserved bytes and
re-encoded payload must equal the input. Helpers derive these checks, byte
bound, computed extraction and retention of the complete original payload.

The native limits are retained: 4 MiB whole policy, 4096-byte ASCII text,
100000 entries for nested certificate vectors, 4096 validators, 8192
candidates, uint32/uint64 words and one-byte Booleans. The Lean interpreter
checks vector counts and consumes each element; it does not model native
reserve/allocation, exception paths or the parser's early aggregate-size
preflight optimizations. Resource/allocation equivalence is not proved.

## Checks against unchanged C++

The isolated harness compiles the same 12 unmodified translation units as the
earlier policy/WAL evidence, using MSVC 19.29.30146 and strict existing flags.
Twenty-eight original blobs, harness and input hashes are pinned. No runtime
handle is opened, no WAL is written and no demo is restarted by this harness.

There are 51 codec observations. Nine policies reuse the original native action
fixtures. A separately constructed synthetic policy populates every nested
record and vector. Distinct path-derived integer and text values exercise field
order; the C++ harness reads named native struct members and emits every
primitive and ordered list. Python compares that complete result and the exact
re-encoded bytes. Endpoint cases separately cover uint32/uint64 maxima and
signed int64 limits. These are finite implementation checks, not a proof of
the C++ parser or native admission.

Negatives cover malformed headers, trailing/truncated bytes, size/count/text/
Boolean bounds, validator order/duplicates, role/reason/action errors, candidate
order and a repeated context under a different candidate key. The fresh input
recipes are deterministic. Tests additionally reject omissions/extra keys in
all 238 record fields, all 1920 proper prefixes of the original ISC policy,
rehashed substitutions in native decoded evidence, and forged scope claims.

Thirty small Lean proofs cover a complete mathematical minimal policy,
generic-inverse composition, whole-frame mutations, bounds, signed endpoints,
lexicographic comparison and exact duplicate/order retention. The minimal
policy is deliberately not an authenticated or admissible startup policy.
It is not a new native arithmetic execution trace or a production-mutant suite.

## Explicit remaining boundary

The native codec accepts several values that startup admission rejects:
empty local validator/body identifiers, inverted deadlines and zero rational
denominators can have a valid wire representation. Named tests preserve that
distinction. Snapshot list duplicates/order are retained, not silently sorted
or strengthened into certificate validity. In particular the successful
complete minimal Lean example contains empty primitive identifiers.

Startup admission must still bind the parsed policy to the actual initial
RoundState and validate the complete certificate/parent/committee/context
chain. Both PARAMETER and APPLY remain blocked by the unchanged native
arithmetic guard. Mixed vote/command recovery, DRS1 decoding, physical scan
identity/completeness, arbitrary failures/repair, public state/action refinement,
initialization/exporter authentication, SHA equivalence, contract freeze,
clean offline reproduction and independent reviews remain open. The separate
Docker/synthetic acceptance has not passed. This layer grants no Formal GO.
