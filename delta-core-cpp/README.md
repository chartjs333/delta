# delta-core-cpp

Pure deterministic DeltaReduce protocol core. The feature-003 slice currently implements the
bounded `delta-canonical-binary-v1` value/envelope parser, encoder, domain-separated content IDs
and cross-language golden-vector checks. Explicit `Command`, `RoundState`, `QuorumCertificate` and
`PreparedIntegerShard` types reject unknown fields, wrong field types, non-canonical decimal
values, invalid identifiers, malformed quorum arrays and incompatible integer fixture profiles.
Portable checked signed arithmetic covers INT64 and a two-limb INT128 implementation without
compiler extensions. The `bft-int-fixture-v1` pre-open gate proves the conservative
`ticket-count * coefficient-bound * value-bound + headroom` expression fits the selected width.
The pure transition entry point consumes only canonical prior-state and command bytes and returns
linked canonical next-state, effect-batch and WAL-record bytes plus their domain-separated IDs.
Pure consensus guards enforce durable vote uniqueness, exact validator membership/quorum policy,
commitment idempotency/equivocation, complete availability coverage and immutable input freeze.

The library is standard-library-only and deliberately has no socket, filesystem, wall-clock,
thread, JVM, Python or floating-point dependency. Runtime durability belongs to
`delta-runtime-cpp`; transport belongs to later feature branches.

Configure and run the isolated targets with:

```text
cmake --preset cpp20
cmake --build --preset cpp20 --parallel
ctest --preset cpp20
```

The `cpp23` preset exercises the compatibility language mode.
