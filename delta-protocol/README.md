# delta-protocol

Runtime-neutral authoritative schemas, media types, action IDs and exact byte fixtures.

This component contains data contracts only. It cannot import Python training code, native C++
code, Java classes, transport libraries or framework object layouts. JSON objects are hashed only
after the canonical UTF-8 encoding declared by the fixtures. Tensor vectors use the documented
safe tensor envelope and never pickle.

The registry binds every contract to formal semantics
`sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.

Feature 003 adds `delta-canonical-binary-v1`: an explicit envelope and typed-value codec with
immutable type codes and hash domains. Its valid, invalid and cross-language fixtures are data
contracts only; the Python verifier is fixture/evidence tooling and does not implement validator
state transitions.

Feature-003 consumers use `fixtures/003/valid/protocol-inputs-v1.json` for canonical protocol
objects, `fixtures/003/invalid/canonical-binary-negative-v1.json` for fail-closed decoding,
`fixtures/003/cross-language/golden-v1.json` for byte identity,
`core-portability-v1.json` for compiler/endian identity and `prepared-100-v1.json` for the bounded
native exit run. `schemas/003/delta-abi-v1.json` mirrors the frozen C descriptor. Every registered
path is verified against its SHA-256 before use; fixture JSON is never an alternate consensus
implementation.

Feature 004 registers `int16-fixed-v1`, reduced rational scale tables, fixed-point configs,
deterministic shard plans, encoded manifests/shards and concrete accumulator proof instances. The
cross-language golden fixture binds source rationals, q values, little-endian payload/envelope
bytes, shard leaves and the commitment root. `direct-q-100-v1.json` separately versions the
feature-003 state/effect/WAL result of consuming verified q values without float conversion.
