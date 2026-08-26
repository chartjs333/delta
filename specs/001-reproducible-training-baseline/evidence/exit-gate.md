# Feature 001 offline exit gate

**Decision**: PASS

**Executed**: 2026-08-26, Europe/Berlin

**Source commit**: `ee7bbacb0a3fd04c941599ac476307b921c3f8f2`

**Environment**: Python 3.12.1, uv 0.6.14, PyTorch 2.6.0+cpu,
Windows 10.0.19045

**Network policy**: `PUBLIC_NETWORK_BLOCKED`; `HTTP_PROXY`, `HTTPS_PROXY` and
`ALL_PROXY` pointed to closed loopback port 9, `UV_OFFLINE=true`, and `NO_PROXY` was limited to
loopback.

## Formal binding

- Formal report: `decision=GO`, source
  `1e6e0f6f70056161d95933e71494ec390c7c1151`, report SHA-256
  `b31c54c3372e36baf1f049b2e45326222b8834362d8fdfbac1e323532986dcab`.
- Formal semantics:
  `sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.
- `final-compatibility.json` SHA-256:
  `dc41f532ecbb79f410236c97a0f1ad7a254b0898d964dd0c906673663c44bcd0`.
- The final compatibility analyzer rediscovered the exact 24 tracked semantic artifacts,
  rederived the same ID and found no new action ID, failure terminal or protocol-visible
  durability outcome. Classification remains `REFINEMENT_ONLY`.

This compatibility/cross-artifact result is not presented as a new proof of semantic
completeness. It proves that feature 001 remains bound to the already accepted formal baseline;
the TLC, Lean, mutation and human-review evidence remains the feature-000 Formal GO evidence.

## Commands and results

All commands below ran in one fail-fast offline session; total elapsed time was 63.6 seconds.

| Gate | Command | Result |
| --- | --- | --- |
| Lock integrity | `uv lock --check` | PASS |
| Offline environment | `uv sync --frozen --offline` | PASS; 24 packages audited, no lock mutation |
| Lint | `uv run ruff check .` | PASS |
| Formatting | `uv run ruff format --check .` | PASS; 92 files formatted |
| Types | `uv run mypy delta-worker-python/src` | PASS; 28 source files |
| Python suite | `uv run pytest delta-worker-python/tests -q` | PASS; 57 tests |
| Formal prerequisite | `uv run python specs/001-reproducible-training-baseline/scripts/verify_formal_prerequisite.py --check-only` | PASS; exact merged GO/evidence/semantics |
| Negative prerequisite matrix | `uv run python -m unittest discover -s specs/001-reproducible-training-baseline/tests -v` | PASS; 6 fail-closed cases |
| Foundation evidence | `uv run python specs/001-reproducible-training-baseline/scripts/verify_foundation.py --check-only` | PASS; all 9 nested offline gates |
| Final compatibility | `uv run python specs/001-reproducible-training-baseline/scripts/verify_final_compatibility.py --check-only` | PASS; 24 artifacts, `REFINEMENT_ONLY` |
| WAN smoke | `uv run delta netem smoke configs/netem/wan-smoke-v1.json` | PASS; schedule `sha256:e11e8706ce0f25cf3d24f42d715b789b16b5441558cf88c0781bdbfe147296dc` |

The content-addressed foundation evidence is
`specs/001-reproducible-training-baseline/evidence/foundation-gate.json`, SHA-256
`8f628f1dad3d90a850790b37f72a7d2e9640715eab31fe50b3a76734fbcd0cf7`.

## Covered acceptance paths

- repeated CPU training and frozen one-step numerical reference;
- exact continuous-vs-optimizer-boundary-resume checkpoint equality;
- stable non-padding token accounting;
- structured terminal `FAILED` manifest for non-finite numeric state;
- recursive verification of every run/checkpoint artifact and eight corruption cases;
- atomic immutable publication, partial-write cleanup and traversal rejection;
- deterministic WAN delay/loss/reorder/disconnect/deadline behavior and cleanup-safe optional
  Linux `tc/netem` adapter;
- legal and illegal artifact lifecycle projections through the feature-000 refinement checker;
- no pickle or unsafe trust-boundary deserialization.

## Independent CI confirmation

Both GitHub workflow executions for the source commit completed successfully:

- PR run: `https://github.com/chartjs333/delta/actions/runs/32974466504`;
- push run: `https://github.com/chartjs333/delta/actions/runs/32974459370`.
