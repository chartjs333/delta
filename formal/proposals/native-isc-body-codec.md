# Versioned native ISC voted-body preimages

T044/T048/T049/T053/T057/T060; candidate amendment 0001. This is component
encoding evidence. Formal authority, complete-prefix support and local benchmark
acceptance remain NO_GO. No native runtime or arithmetic guard is changed.

## Exact source and representation

The independently fixed PR50 source commit is
`60c692f6e391f839829dfc64e93380db54cd507b`. The proposal retains all eight input
blob hashes and the line/span hashes of ten extracted C++ definitions.
`VoteInputSetBody` is distinct from a finalized `InputSetCertificate`: it has
only `context`, `input_root` and ordered `tuples`. Quorum/signers are not added to
the pre-quorum body, and a QC content ID cannot replace its voted-body ID.

The body hash preimage is binary, not the earlier draft JSON:

1. ASCII `deltareduce.vote.input-set-body.v1`, followed by NUL;
2. native Context: arithmetic profile, height, parameter schema, round config,
   round ID, validator epoch, view, in precisely that order;
3. input root;
4. tuple count, then each tuple's availability-certificate ID, commitment ID,
   domain ID and ticket ID, in precisely that order.

Integers and text lengths occupy eight bytes in big-endian order; text follows
its byte count. No host layout/padding, locale, object representation or unordered
iteration defines these bytes. `native_isc_body.py` implements a bounded Python
encoder and inverse decoder for this **hash payload**. It is not a decoder for
native C ABI, network frames, snapshots, WAL or the certificate wire envelope.

The proposal profile accepts ASCII strings of at most 128 bytes, at most 4096
tuples and a 4 MiB payload. These bounds are explicitly tooling restrictions,
not an inferred native contract. Encoding preserves empty/duplicate/unsorted
tuples and even invalid primitive IDs: the original native hash function also
does not decide admission. Such cases exercise encoding only. No silent sorting,
deduplication, validation bypass or new runtime rejection rule is introduced.

## Separate source registry and component execution

`native-isc-body-vectors.json` uses
`deltareduce.native-voted-body-fixture.v1-candidate`, containing
`deltareduce.native-isc-body.v1-candidate` witnesses. Each binds complete typed
fields, exact hash payload/preimage and body ID. The base primitive values were
read from the pinned `vote_fixture.cpp/.hpp`; the other twenty cases deliberately
change individual fields or cover count/order/uint64/ASCII boundaries. They are
not twenty new admissible votes. No full C++ fixture/admission constructor runs.

The cross-check compiles unmodified extracted `Context`, `InputTuple`,
`VoteInputSetBody`, native hash append functions, `authority_content_id`,
`vote_input_set_body_id` and `sha256_hex`, together with the entire unmodified
native `sha256.cpp/.hpp`. The small harness only constructs typed values and
prints bytes/IDs. Exact function spans and generated harness source are retained.
MSVC x64 /std:c++20 /EHsc /W4 /WX is used; its actual version is read from `/Bv`.
No replacement SHA implementation or approval callback is substituted.

All 21 C++ byte strings and native SHA-256 body IDs match Python. The base is
635 bytes and hashes to
`sha256:33e327fe50bd52a92e0675c846fe2ee53671dde65350152380c82a99af21c27d`.
This is actual native **component** execution, not an execution of the reactor,
vote admission, journal, durability barrier, transport or authenticated exporter.
Compiled binaries remain ignored and are not committed. One compiler lane is
not GCC/Clang/sanitizer/cross-platform qualification or a general SHA proof.

The verifier compares the witness with a separately resolved original typed body
before decoding. A candidate cannot replace that original by changing fields,
rehashing the payload or asserting authenticated provenance. JSON type identity
is preserved, including rejection of Python's Boolean/integer equality alias.
All outputs remain synthetic source fixtures, `native_export_authenticated=false`
and `gate_eligible=false`. Their registry is not independent production custody.

## Missing public relation and unchanged legacy evidence

The production TLA InputBody contains `round`, full `config`, close `policy`,
`entries` and `canonicalRoot`; the latter is the same abstract entry set, not a
cryptographic string. Native tuples instead carry commitment and availability
certificate IDs. The following still require actual artifacts and provenance:

| Native primitive | Required public/native relation still open |
| --- | --- |
| Context round/config/profile/schema/epoch | Authenticate immutable configuration and identity aliases; native ISC context keys by round ID whereas public ISC context keys by height/epoch. |
| Commitment ID | Resolve actual ticket/content/domain and complete Q commitment bytes. |
| Availability certificate ID | Resolve certificate preimage and the required complete availability observations. |
| input_root | Check the actual native root construction over the exact ordered tuples against the public canonical entry set. |
| closed input-set authority | Establish CloseInput policy/required coverage/phase and original immutable admission snapshot. |

In particular `ChainVerifier::verify_input_set` shape/context/quorum checking
alone cannot supply root/availability freeze. The minimal arithmetic graph's
ISC_PROJECTION is not this complete native voted body or a finalized native QC.
The prior original ISC/EC/APC/ROOT label hashes cannot be silently replaced with
new IDs. No legacy artifact, envelope, receipt, sequence 5/6/8 or journal root is
rewritten; the mixed-prefix checker still rejects the incomplete old history.

The next step is the typed certificate/commitment/availability/configuration
relation and equivalent actual EC/APC/ROOT body witnesses, then the mandatory Lean
prefix and phase/QC/send/current/recovery composition. No new Lean theorem,
production TLC execution/mutant or nativeArithmeticRecoveryRefines is claimed.
Formal-first STOP, explicit trust boundaries and unknown/incomplete durability
rules remain intact. Native adapters/WAL/admission, arbitrary snapshots/failures,
contract freeze, clean reproduction and independent review remain mandatory.

## Reproduction

Run `python formal/scripts/generate_native_isc_body_vectors.py` for the exact
versioned JSON fixture. Add `--vcvars <VS2019 vcvars64.bat>` to compile and compare
the fixed native source components in ignored `formal/build/native-isc-codec`.
The eight pinned Git blobs must exist locally; no branch head is substituted.
Run `python -m unittest discover -s formal/tests -p test_native_isc_body.py -v`.
Eleven tests include every truncated prefix of the 635-byte base, trailing bytes,
length/count/resource limits, all 4096 supported tuples, source/span reproduction,
each rehashed field substitution and forged provenance/version/QC fields.
