# Agent execution contract

## Required reading order

Before changing implementation or protocol artifacts, read:

1. `.specify/memory/constitution.md`;
2. `docs/adr/0000-formal-verification-gate.md`;
3. `docs/adr/0001-deltareduce-v1.md`;
4. `docs/adr/0010-hybrid-runtime-boundary.md`;
5. `specs/ROADMAP.md` and `specs/HYBRID-RUNTIME-MAP.md`;
6. `specs/000-formal-tla-spec/failure-semantics.md`, `proof-obligations.md` and `refinement-contract.md`;
7. current feature `spec.md`, `plan.md`, `tasks.md`;
8. current feature `runtime-profile.md` and `runtime-tasks.md` when present.

The current branch is the implementation boundary. Later feature behavior must not be implemented opportunistically.

## Formal-first STOP rule

- No implementation task in `001–011` starts until the exact merged `FormalVerificationReport(GO)` is verified.
- Current accepted formal semantics ID is `sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.
- Any new externally visible transition, changed vote/QC context, deadline, failure terminal, durability ordering, availability rule, certificate edge, arithmetic precondition or current-state behavior returns to feature 000 first.
- A failed model, proof, production-mutant, refinement or compatibility gate is an unconditional STOP.

## Hybrid boundary rules

### C++ core and native runtime

- `delta-core-cpp` contains no socket, DNS, TLS, wall-clock or filesystem adapter.
- `delta-runtime-cpp` is the only owner of consensus WAL, snapshots, durable vote journal and single-writer state reactor.
- Consensus code uses fixed-width integers, checked arithmetic, explicit endian conversion and deterministic ordering.
- Raw struct memory, padding, pointer values, `unordered_map` iteration and host locale never define canonical bytes or state hashes.
- No exception crosses the C ABI. Every exported function is `noexcept` and returns a versioned status.
- No accepted consensus path uses floating-point addition or compiler `fast-math`.

### C ABI / FFM

- The FFI is a small versioned C ABI; no `std::string`, `std::vector`, reference, template, virtual type or compiler-specific enum crosses it.
- ABI structures include `abi_major`, `abi_minor` and `struct_size` where extensibility is required.
- The primary API is command/effect based; Java cannot reconstruct state-machine semantics through fine-grained setters.
- C++ never retains a pointer to Java/Netty-owned memory after the downcall returns.
- Zero-copy is optional. A bounded-copy fallback is mandatory and must produce identical canonical outputs.
- Startup fails on incompatible ABI, schema, protocol, build or `formal_semantics_id`.

### Java node

- Reference runtime is JDK 25; JDK 26 runs as a compatibility lane unless a later ADR changes the baseline.
- Netty owns connections, TLS sessions, framing, rate limits, backpressure and peer routing.
- Java treats consensus payload/effects as opaque canonical bytes except transport envelope fields explicitly assigned to it.
- FFM/WAL calls never block a Netty event loop; they run on the dedicated consensus reactor boundary.
- Java delivers opaque timer tokens only. It cannot call `change_view`, `abort` or `apply` directly by phase name.
- Direct `ByteBuf` lifetime is explicitly retained/released around synchronous FFM use; heap/composite buffers use bounded staging memory.

### Python worker

- Python/PyTorch owns local training, token/data accounting, QLoRA and evaluation.
- A worker contribution becomes consensus-visible only as canonical normalized/quantized bytes.
- Python object layout, pickle and framework checkpoint internals never define network protocol bytes.

## Persist-before-expose

A native transition returning outbound votes/messages must follow:

```text
validate command → compute candidate → append WAL → durability barrier
→ commit state root → return canonical effects → Java sends
```

If durability fails, no externally sendable effect is returned. Replay returns the same effect identity idempotently.

## Threading

- Exactly one consensus reactor thread may call mutating native functions for one runtime handle.
- Netty event loops submit bounded commands through an MPSC queue.
- Read-only diagnostics require explicitly documented snapshot semantics.
- Single writer removes local data races but does not replace BFT ordering or formal refinement.

## Quality gates

```text
# Formal or semantic-impact changes
make formal-check

# Python
uv run ruff check .
uv run ruff format --check .
uv run mypy delta-worker-python/src
uv run pytest delta-worker-python/tests

# C++ reference shape (instantiated by feature 003)
cmake --preset ci
cmake --build --preset ci
ctest --preset ci

# Java reference shape (instantiated by feature 003/005)
./gradlew --no-daemon check

# Cross-language
make conformance
```

C++ gates include GCC and Clang, ASan/UBSan, a separate TSan lane, parser fuzzing and cross-compiler state-root fixtures. Java gates include JDK 25 reference and JDK 26 compatibility. Cross-language gates compare exact canonical bytes, status codes, ABI descriptor and formal traces.

## Branch discipline and evidence

- Feature commits reference existing `T###` and supplemental `HR###-*` task IDs.
- Mark tasks complete only with machine-readable evidence.
- Performance, zero-copy, latency, 8 GB and native-crash-containment claims remain targets until measured.
- Embedded FFM and isolated native sidecar are distinct deployment profiles; do not claim crash isolation for embedded mode.
- Secrets, private data, restricted model weights, generated native binaries and private keys are never committed.
