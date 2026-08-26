# Reproducible baseline and WAN smoke guide

Feature 001 provides a CPU-only scientific reference, immutable local run bundles and a
deterministic WAN simulator. It is bound to formal semantics
`sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.
It does not implement consensus, distributed reduction or Apply authority.

## Prepare the locked environment

Use Python 3.12 and the committed lockfile. The first dependency materialization may use the
configured package indexes; all acceptance commands after that run offline.

```text
uv sync --frozen
uv run python specs/001-reproducible-training-baseline/scripts/verify_formal_prerequisite.py --check-only
```

Both commands fail closed: they neither update `uv.lock` nor accept a different Formal GO or
formal semantics ID.

## Run and verify the CPU smoke baseline

From the repository root, on a checkout where `runs/cpu-smoke-v1` does not already contain a
final manifest:

```text
uv run delta baseline run configs/baseline/cpu-smoke-v1.json
uv run delta artifacts verify runs/cpu-smoke-v1/runs/cpu-smoke-v1/run-manifest.json --root runs/cpu-smoke-v1
```

The first command prints canonical machine-readable JSON with the run and checkpoint manifest
references. The second recursively verifies the protocol registry, media/schema pairing,
byte length and SHA-256 of each direct artifact, checkpoint manifest, safe tensor and training
state. A missing or changed object returns exit code 2 and identifies its expected `content_id`
and `locator`.

A finalized `run_id` is immutable. To perform another scientific run, copy the config and choose
a new `run_id` and `output_dir`; do not replace a completed bundle. A resume uses the same run ID
and an optimizer-boundary checkpoint from an interrupted run:

```text
uv run delta baseline resume path/to/config.json path/to/checkpoint-manifest.json
```

Resume restores model tensors, AdamW moments and step, the torch CPU RNG state, deterministic
sampler cursor and processed-token counter. The continuous-vs-resume integration test requires
the resulting safe-tensor bytes to match exactly.

## Reproducibility contract

The committed smoke profile fixes corpus bytes, tokenizer bytes, seed, sample ranking, batch
shape, gradient accumulation, model dimensions and canonical AdamW settings. It counts only
non-padding target tokens. A completed run records all input hashes, dependency lock, code
revision, platform fingerprint, seeds, token count, metrics and checkpoint links.

The required guarantees are deliberately scoped:

- repeated execution on the same supported CPU/PyTorch platform is bit-identical for model and
  resume checkpoints;
- one-step floating-point comparison across supported CPU kernels uses an absolute tolerance of
  `5e-7`, while parameter names, shapes, dtypes and schema fingerprint remain exact;
- bitwise equality across operating systems, accelerator architectures or different PyTorch
  builds is not claimed;
- throughput and wall time are measurements, never reproducibility inputs or performance claims.

NaN/Inf loss, gradient, optimizer state or metric stops training before `COMPLETED`. The runner
publishes a terminal `FAILED` manifest with a stable `failure_code`; partial valid metrics and the
latest fully published optimizer-boundary checkpoint remain content-addressed evidence.

## Exercise the WAN profile

The mandatory adapter is logical, deterministic, unprivileged and does not open a public socket:

```text
uv run delta netem smoke configs/netem/wan-smoke-v1.json
```

Its JSON report binds the seeded delivery schedule by SHA-256 and includes delay, loss,
reordering, disconnect and deadline outcomes. The Linux `tc/netem` adapter is optional, requires
root plus `tc`, validates its interface name and removes its qdisc in the context-manager cleanup
path even when the enclosed operation raises.

## Run the offline acceptance gate

After dependencies have been materialized, block outbound proxy access and run:

```text
uv lock --check
uv sync --frozen --offline
uv run ruff check .
uv run ruff format --check .
uv run mypy delta-worker-python/src
uv run pytest delta-worker-python/tests
uv run python specs/001-reproducible-training-baseline/scripts/verify_formal_prerequisite.py --check-only
uv run python -m unittest discover -s specs/001-reproducible-training-baseline/tests -v
```

The committed `specs/001-reproducible-training-baseline/evidence/foundation-gate.json` records
the same commands under `PUBLIC_NETWORK_BLOCKED`. Formal projection tests additionally send the
legal and deliberately illegal artifact lifecycle traces through the feature-000 refinement
checker.

