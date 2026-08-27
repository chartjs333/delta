# Feature 003 offline exit gate

**Decision**: PASS

**Executed**: 2026-08-27, Europe/Berlin

**Final source commit**: `189e5f155b787c2d1d391630fc599b67ea366bba`

**Verified native source commit**: `9254e3f4a16104be731ea2b45299194c368aaa9b`

**Environment**: Python 3.12.1, uv 0.6.14, Windows 10.0.19045. Native compiler,
JDK and sanitizer execution used the pinned offline Linux containers recorded in the evidence.

**Network policy**: the local gate ran with `UV_OFFLINE=true`; the evidence verifiers perform no
public-network access. The bound native CI jobs compile and test inside content-addressed
toolchain images after checkout/provisioning and execute the phase harness with networking
disabled.

## Formal binding and final compatibility

- Formal report: exact `decision=GO`, source
  `1e6e0f6f70056161d95933e71494ec390c7c1151`, report SHA-256
  `b31c54c3372e36baf1f049b2e45326222b8834362d8fdfbac1e323532986dcab`.
- Formal semantics:
  `sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.
- Final compatibility evidence SHA-256:
  `2cd392aafaba1ab70cc0a6919cae9580955c742f9f92296f54a570af29dca769`.
- The final analyzer reverified every phase evidence file, all protocol registry hashes, ABI
  descriptor/header/Java bindings, all 53 semantic tasks, all 24 hybrid-runtime obligations and
  the Constitution 2.1.0 mapping. It found no formal source diff, new formal action, new failure
  terminal or new protocol-visible durability outcome. Classification remains `REFINEMENT_ONLY`.

This is a deterministic compatibility, traceability and execution-evidence gate. It is not
presented as a new proof of semantic completeness. TLA+, Lean, liveness, production-mutant,
refinement and independent-human-review guarantees remain the accepted feature-000 Formal GO
evidence.

## Local commands and results

| Gate | Command | Result |
| --- | --- | --- |
| Lock integrity | `uv lock --check` | PASS; no lock mutation |
| Offline environment | `uv sync --frozen --offline` | PASS; 24 packages audited |
| Lint | `uv run ruff check .` | PASS |
| Formatting | `uv run ruff format --check .` | PASS; 182 files |
| Types | `uv run mypy delta-worker-python/src` | PASS; 48 source files |
| Python suite | `uv run pytest -q` | PASS; 106 passed, 1 optional CUDA skip |
| Feature-003 evidence tests | `uv run pytest specs/003-bft-round-state-machine/tests -q` | PASS; fail-closed negative cases included |
| Nested evidence | all 16 feature-003 `verify_*.py --check-only` phase/refinement gates | PASS |
| Final compatibility | `verify_final_compatibility.py --check-only` | PASS; exact canonical report |
| Patch integrity | `git diff --check` | PASS |

## Independent native execution

The content-addressed evidence binds successful GitHub runs `33074959552`, `33076007138`,
`33076771800`, `33077580263`, `33078884399`, `33079721703`, `33080433068`,
`33082251599`, `33083688876`, `33086458108` and `33086458173`. Together they cover GCC
14.2 and Clang 20.1.8 in C++20/C++23 modes, JDK 25/26 FFM, C11 ABI compilation, Clang
ASan/UBSan, separate GCC TSan, the bounded 2,052-case parser/ABI fuzz lane and real
production-path mutants.

Four independent native runtimes processed 100 prepared integer tickets and produced:

- final state ID
  `sha256:c6fcf9131d0a481aee2918bf894dbebc62442dcb26be3c559630841f4d26f967`;
- effect transcript SHA-256
  `11d4f62cba6b96eb17710e023c910ff67da69eebaf3896b275f551c443a3147d`;
- WAL transcript SHA-256
  `9ddb1ff79eb2ef556e1310aa9cf057fadbe9dd50e952307473bbcd9775b72a06`;
- WAL file SHA-256
  `cc08e6944772f16e460495963ae4bdd630abeb7afb7126e13b95a636e3c54f90`.

The uninterrupted and crash/restart executions were byte-identical. Four legal native traces
were accepted by the exact feature-000 checker; the view-without-QC and
effect-before-durability production mutants produced the expected rejected counterexamples.

## Final Constitution check and scope boundary

- Exact fixed tickets, prepared integers, quorum membership, input freeze and canonical state
  bytes preserve principles I, III–VI and XII.
- Persist-before-expose, durable vote recovery, deterministic view change/abort and idempotent
  replay preserve principles X–XI.
- Architecture, fixture and ABI gates enforce reduce/distribution separation and bounded safe
  trust boundaries under principles VIII–IX.
- The exact accepted Formal GO and zero formal-source diff satisfy principle II.

Production quantization/rounding/clipping and codecs remain feature 004 scope; authenticated
protobuf/gRPC/Netty/TLS transport remains feature 005 scope; the full certificate hierarchy,
robust aggregation and Apply implementation remain feature 008 scope. No WAN performance, P2P
distribution or 8 GB achievement is claimed by this phase.
