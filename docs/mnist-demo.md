# Distributed MNIST commission workspace

This isolated browser workspace demonstrates real, reproducible learning without
changing Campaign 02 governance. It uses the public MNIST handwritten-digit corpus,
four local worker processes, a common test set and a centralized comparison arm.

## Start the presentation

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File tools/run-mnist-demo.ps1
```

The command opens a loopback-only page. The operator then presses **Запустить
демо**; there are no paths, seeds, JSON documents or configuration forms to fill.

The first run downloads approximately 11 MB of compressed MNIST data when the
cache is empty. Prepare and verify that cache before the presentation:

```powershell
uv run delta-mnist-demo prepare `
  --cache-dir artifacts/local/mnist-cache
```

After that, require a cache-only run:

```powershell
powershell -ExecutionPolicy Bypass `
  -File tools/run-mnist-demo.ps1 `
  -Offline
```

Every source file is admitted only when its exact byte length and SHA-256 match
the pinned values. The parser independently verifies the IDX magic, item count and
28×28 dimensions. Generated runs stay below `artifacts/local/mnist-demo/`, which is
excluded from Git.

## What is actually trained

The educational model is `nearest-centroid-int-sum-v1`. Training learns one pixel
centroid for each digit. The centralized arm computes the sufficient statistics on
the complete 60,000-image training set. The distributed arm assigns every image to
exactly one of four label-skew shards:

```text
worker-01: digits 0, 1, 2
worker-02: digits 3, 4, 5
worker-03: digits 6, 7
worker-04: digits 8, 9
```

Each process reads only its shard and returns integer class sums and counts. Raw
images are not part of the returned worker summary. Exact integer aggregation must
produce the same counts, sums, model ID and test predictions as the centralized
arm; any mismatch stops the demo.

Both arms are evaluated on the same 10,000-image test set. The page renders the
measured overall and per-digit accuracies, observed timing, summary-payload bytes
and one real test image for every digit. Charts are derived from the run report,
not from hard-coded presentation values.

## Failure view

**Отключить worker-04** removes its already measured summary from the illustrative
comparison. Because that shard owns digits 8 and 9, the page visibly shows their
lost training coverage and the resulting quality change. The failure arm always
records:

```text
coverage_complete: false
protocol_accepted: false
```

It is not presented as a DeltaReduce fallback. It demonstrates why missing data
coverage matters; it does not claim that the real protocol would accept or apply
that model.

## Reproducibility and scope

The reproducibility identity binds the four pinned dataset hashes, implementation
source, formal-semantics ID, partition rule, seed, shard identities, learned integer
model and measured deterministic quality results. Wall-clock timings and process
IDs remain honest observations but do not change that identity.

The workspace is deliberately marked `LOCAL_DEMO_ONLY` and records all of the
following as false:

```text
authoritative
governance_eligible
execution_authorized
feature_010_go_claimed
failure_simulation.protocol_accepted
```

It does not create `BenchmarkDefinitionQC`, `BenchmarkResultQC`, a real-WAN result,
controller appointment or any Feature 011 authority. The four Ed25519 controller
keys are real disposable demo keys, while their identities and custody remain
synthetic.

MNIST attribution: Yann LeCun, Corinna Cortes and Christopher J.C. Burges,
<https://yann.lecun.org/exdb/mnist/index.html>.
