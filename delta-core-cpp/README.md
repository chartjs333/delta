# delta-core-cpp

Pure deterministic DeltaReduce protocol core. The feature-003 slice currently implements the
bounded `delta-canonical-binary-v1` value/envelope parser, encoder, domain-separated content IDs
and cross-language golden-vector checks.

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
