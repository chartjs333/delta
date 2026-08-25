# Runtime Profile: 001 Reproducible Training Baseline

**Status**: Normative hybrid-runtime addendum  
**Formal impact**: `REFINEMENT_ONLY` — no change to the accepted DeltaReduce formal action relation  
**Architecture authority**: `docs/adr/0010-hybrid-runtime-boundary.md`

## Purpose

Feature 001 remains the scientific single-node reference and is implemented in **Python 3.12 + PyTorch**. It does not implement the C++ consensus core or Java transport node. Its additional responsibility in the hybrid architecture is to establish runtime-neutral canonical artifacts and the repository/build boundaries that later C++, Java and Python components share.

## Language and component allocation

- `delta-worker-python/`: training baseline, deterministic data pipeline, checkpoint/resume, QLoRA-ready worker abstractions and scientific evaluation.
- `delta-protocol/`: runtime-neutral schemas, media types, action IDs, canonical JSON/binary fixtures and content-hash test vectors. No PyTorch, JVM, C++ runtime or network dependency is permitted here.
- `delta-core-cpp/`, `delta-runtime-cpp/`, `delta-ffi/`, `delta-node-java/`: directory placeholders and build-boundary documentation MAY be created, but production native/JVM logic is deferred to features 003–008.

## Formal prerequisite

The accepted formal baseline currently binds:

- source commit `1e6e0f6f70056161d95933e71494ec390c7c1151`;
- formal semantics ID `sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`;
- Formal GO evidence on `000-formal-tla-spec`.

Implementation work starts only after PR #1 is merged and T000 independently verifies the merged report/evidence graph. A branch ref alone is not a substitute for merged predecessor state.

## Cross-runtime contracts introduced here

1. **Canonical artifact identity**: every persisted object has media type, schema version, byte length and SHA-256.
2. **No memory-layout protocol**: Python dataclasses, future C++ structs and future Java records are never serialized by dumping their in-memory representation.
3. **Stable error/action IDs**: events corresponding to the formal trace contract use registered IDs and explicit projection metadata.
4. **Safe tensor boundary**: tensor artifacts use safe non-pickle formats; untrusted input cannot execute code.
5. **Runtime manifest**: every run records Python version, dependency lock, platform, accelerator/runtime details and future protocol compatibility fields.
6. **Polyglot repository boundary**: component ownership and dependency direction are fixed before native/JVM implementation begins.

## Project layout established by 001

```text
delta-protocol/
  README.md
  schemas/
  fixtures/
  action-registry/

delta-worker-python/
  pyproject.toml
  src/deltatorrent/
  tests/

delta-core-cpp/       # placeholder only in 001
delta-runtime-cpp/    # placeholder only in 001
delta-ffi/            # placeholder only in 001
delta-node-java/      # placeholder only in 001
integration/
  cross-language/
  traces/
```

A placeholder contains documentation and build ownership only; it MUST NOT introduce protocol behavior before its feature branch.

## Exit additions

Feature 001 is not complete until:

- the merged Formal GO is verified offline;
- `delta-protocol` canonical fixtures are independent of Python object layout;
- the Python baseline emits artifact and event records conforming to the shared contracts;
- repository dependency tests prove that protocol schemas do not import training/native/JVM adapters;
- the hybrid ADR and branch runtime map pass cross-artifact analysis.
