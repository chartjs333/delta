# Feature 002 offline exit gate

**Decision**: PASS

**Executed**: 2026-08-26, Europe/Berlin

**Implementation source commit**: `c66a4ca2c48c6de096782110eb8b835a6494cd27`

**Environment**: Python 3.12.1, uv 0.6.14, PyTorch 2.6.0+cpu,
Windows 10.0.19045

**Network policy**: `PUBLIC_NETWORK_BLOCKED`; `HTTP_PROXY`, `HTTPS_PROXY` and
`ALL_PROXY` pointed to closed loopback port 9, `UV_OFFLINE=true`, and `NO_PROXY` was limited to
loopback for the implementation gate. Formal replay used only the already materialized pinned
Windows JRE, TLA+ jar, Lean toolchain and Lake dependency cache.

## Formal binding and replay

- Formal report: `decision=GO`, source
  `1e6e0f6f70056161d95933e71494ec390c7c1151`, report SHA-256
  `b31c54c3372e36baf1f049b2e45326222b8834362d8fdfbac1e323532986dcab`.
- Formal semantics:
  `sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.
- Predecessor evidence SHA-256:
  `9edbc2454895498a7c0570b0011359b84be8ed12d2408206aa63a40ee22d52b5`.
- Final compatibility evidence SHA-256:
  `9868a974945b30a061a609c78a93bfb41bae6ebe1ae207c55121790b0e5cf83e`.
- The final compatibility analyzer rediscovered all 24 semantic artifacts, rederived the same
  formal semantics ID, found no formal-source diff and found no new action ID, failure terminal or
  protocol-visible durability outcome. Classification remains `REFINEMENT_ONLY`.
- The complete feature-000 formal gate was replayed from an LF-normalized detached worktree at the
  accepted GO commit `7abd0f43f8f1b15ec9aa6c3d2c80b32bfb4a6eca`: Phase0, 27 formal contract
  tests, locked toolchains, SANY parse, 19 TLC safety models, 6 TLC liveness models, Lean build,
  10 production-action mutants, 7 legal and 16 illegal refinement fixtures, and GO report
  verification all passed. The full liveness scenario reached `APPLIED`; the no-fairness
  countercheck produced the expected temporal counterexample. Lean verified all 28 normative
  conjuncts.

This compatibility result is a refinement and traceability gate, not a new claim of semantic
completeness. The TLA+, Lean, mutation, clean Linux reproduction and independent human-review
evidence remain the accepted feature-000 Formal GO evidence.

## Commands and results

All implementation commands ran fail-fast with public network access blocked.

| Gate | Command | Result |
| --- | --- | --- |
| Lock integrity | `uv lock --check` | PASS; 25 packages resolved, no lock mutation |
| Offline environment | `uv sync --frozen --offline` | PASS; 24 packages audited |
| Lint | `uv run ruff check .` | PASS |
| Formatting | `uv run ruff format --check .` | PASS; 135 files formatted |
| Types | `uv run mypy delta-worker-python/src` | PASS; 48 source files |
| Python suite | `uv run pytest delta-worker-python/tests -q` | PASS; 106 passed, 1 optional CUDA skip |
| Protocol/architecture | `uv run pytest delta-worker-python/tests/contract delta-worker-python/tests/architecture -q` | PASS; 42 tests |
| Predecessor | `uv run python specs/002-local-round-engine/scripts/verify_predecessor.py --check-only` | PASS; exact merged feature-001 evidence and Formal GO |
| Final compatibility | `uv run python specs/002-local-round-engine/scripts/verify_final_compatibility.py --check-only` | PASS; 24 artifacts, `REFINEMENT_ONLY` |
| Formal baseline replay | direct equivalents of all `make formal-check` targets at accepted GO commit | PASS |
| Patch integrity | `git diff --check` | PASS |

## Covered acceptance paths

- one deterministic domain-pure ticket binds the exact data range, `B`, `H`, parent checkpoint,
  parameter schema, optimizer profile and arithmetic profile;
- worker execution consumes exactly the ticket range and reaches `A_j=H` before candidate
  eligibility;
- parent minus final local state reconstructs the emitted `LocalDelta`, and division by `A_j`
  matches the normalized FP32 contribution reference;
- tied parameters have one canonical owner and an explicit alias/omission contract;
- token and optimizer-step ledgers commit only at optimizer boundaries;
- completion and candidate manifests are canonical, content-addressed and published only after
  referenced safe-tensor objects verify recursively;
- completion, partial work, OOM, cancellation, deadline, data exhaustion, non-finite state,
  crash/recovery, exact replay and conflicting replay are deterministic and fail closed;
- incomplete outcomes publish terminal evidence and never publish an eligible candidate;
- architecture tests prohibit worker-local contribution objects in the distribution plane and
  prohibit native/JVM validator dependencies in this Python feature;
- feature-004 receives runtime-neutral encoder inputs and boundary vectors, without accepting or
  implementing quantized bytes early.

## Final Constitution Check

- **I / IV**: immutable ticket, dataset, parent, optimizer and arithmetic bindings plus direct
  reference parity preserve scientific correctness and domain-pure fixed work.
- **II**: the exact accepted Formal GO was independently reverified; the implementation adds only
  internal stuttering and existing `ACCEPTED`/`FAULT` projections.
- **III / VI / VII**: feature 002 introduces no validator authority, certificate transition,
  randomness, input-freeze or Apply behavior.
- **V**: the worker normalizes only after the exact `A_j=H` guard; consensus quantization,
  clipping, weighting and integer reduction remain explicitly deferred to feature 004.
- **VIII**: static and behavioral architecture tests enforce reduce/distribution separation.
- **IX**: trust-boundary artifacts use strict canonical JSON and safetensors; pickle is forbidden.
- **X**: every local failure path has a terminal completion, candidate suppression and explicit
  idempotent recovery/replay behavior.
- **XI**: structured telemetry, deterministic injected faults, immutable evidence and orphan-claim
  recovery provide observability and reversibility.
- **XII**: runtime-neutral schemas, media types, canonical fixtures and hashes keep the worker
  implementation replaceable.

The optional CUDA smoke path was skipped because no CUDA device was present; the mandatory CPU
path passed. INT16 quantization, C++ consensus code, Java transport and any performance or 8 GB
achievement claim remain out of scope and are not presented as completed.
