# MNIST-over-Delta commission workspace

This loopback-only browser workspace demonstrates MNIST passing through existing
Delta component interfaces without changing Campaign 02 governance. MNIST is only
the workload: four Python workers produce independent node-local statistics, the
demo adapter converts each statistic set into its own canonical contribution, and
existing Java and C++ Delta components perform transport validation, durability,
certificate validation, aggregation, Apply, and the current-state transition.

## Start the presentation

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File tools/run-mnist-demo.ps1
```

The wrapper verifies or builds the native integration process, selects or
content-verifies and locally provisions the locked reference JDK 25, verifies the
four pinned Netty jars, compiles the Java relay, and opens a page bound only to
`127.0.0.1`. The operator then presses
**Запустить демо**; no paths, seeds, JSON documents, or protocol knobs are exposed.

Prepare the native/Java toolchain and dependency cache before the presentation:

```powershell
powershell -ExecutionPolicy Bypass `
  -File tools/run-mnist-demo.ps1 `
  -PrepareOnly
```

On a machine without the locked toolchain cache, the first non-offline preparation
downloads the 141 MB JDK archive, approximately 1.7 MB of Netty jars, and then the
demo downloads approximately 11 MB of pinned MNIST data. Every download is checked
against a committed byte length and SHA-256. After that, require a cache-only
demonstration:

```powershell
powershell -ExecutionPolicy Bypass `
  -File tools/run-mnist-demo.ps1 `
  -Offline
```

Generated runs stay below `artifacts/local/mnist-demo/`, which is excluded from
Git. A failed build, hash check, transport receipt, WAL operation, QC validation,
native model comparison, or trace check stops the demo; there is no success-mode
fallback.

## Hard no-hidden-aggregation criterion

`DEMO_PASS` is emitted only when all of the following are true:

1. MNIST admission and the four disjoint shards are content-bound.
2. Each Python worker computes only its own class statistics. The workload adapter
   converts one worker summary at a time into one canonical `int16` model delta;
   the conversion function never receives another worker's summary.
3. Java verifies the demo Ed25519 signature and moves the exact opaque bytes over
   a real Netty loopback TCP connection without numeric arithmetic.
4. `CertificateVoteRuntime` persists every phase vote before exposing its frame.
5. `ChainVerifier` validates ISC, EC, APC, ParameterShardQC, AggregateRootQC, and
   ApplyQC under the existing Delta certificate interfaces.
6. The only cross-node numeric reduction is
   `delta::robust::reduce_parameter_shard` in the native core.
7. `delta::apply::compute_candidate` produces the model candidate and
   `CurrentPointerStore` reaches `APPLIED`.
8. The distributed result is evaluated only from native `applied-model.bin`; its
   bytes must equal the separately computed centralized baseline under the same
   integer profile.
9. The machine-readable execution trace contains the ordered component chain and
   records `python_cross_node_aggregation_performed=false`.

The demo integration module has no `aggregate_summaries` function and Java has no
model-coordinate or aggregation API. Python does compute the explicitly labelled
centralized comparison arm, but neither that model nor its sufficient statistics
enter the distributed execution path. The demo-only native executable orchestrates
production libraries; it contains no alternate reduction algorithm.

## Executed path

```mermaid
flowchart LR
    A[MNIST dataset] --> B[4 isolated Python workers]
    B --> C[one-summary-at-a-time workload adapter]
    C -->|signed canonical contributions| D[Java Netty loopback]
    D --> E[demo-only native process adapter]
    E --> F[CertificateVoteRuntime + durable WAL]
    F --> G[ChainVerifier: six QC phases]
    G --> H[robust::reduce_parameter_shard]
    H --> I[apply::compute_candidate]
    I --> J[CurrentPointerStore: APPLIED]
    J -->|native model bytes| K[MNIST evaluation + UI]
```

The adapter boundary and its exact acceptance criteria are documented in
`integration/mnist-delta/README.md`. Every run also writes a run-specific diagram to
`delta-execution/execution-path.mmd`.

This is not the deployable `delta-node-java` service topology. The Java main and
native executable in `integration/mnist-delta/` are demo-only process adapters:
the Java adapter reuses production `BenchmarkTransport` and Netty code, and the
native adapter calls the existing production runtime, certificate, robust-reduce,
Apply, and current-pointer interfaces. The transport is loopback TCP without the
production TLS/peer-routing/WAN layer.

## Inspect one run

After a successful button press, the UI shows the participating component chain.
The underlying evidence remains inspectable in the run directory:

```text
delta-execution/execution-trace.json
delta-execution/execution-path.mmd
delta-execution/native-nodes/validator-*/trace.jsonl
delta-execution/native-nodes/validator-*/votes/runtime.wal
delta-execution/network/**/relay-evidence/*.json*
delta-execution/models/validator-*/applied-model.bin
```

`execution-trace.json` binds the contribution IDs, transport receipts, six
certificate identities, model SHA-256, exact toolchain executables, ordered real
Delta components, terminal `APPLIED`, and the crash/recovery observations.
The repository also includes the portable trace excerpt from a successful full
MNIST run at `integration/mnist-delta/example-execution-trace.json`.

## Fault demonstration

Validator 04 is terminated after its Apply vote is durable but before the vote is
exposed. The same node directory is reopened, the durable journal is recovered,
and the identical vote is replayed through the normal transport/certificate path.
The run is accepted only after all four nodes converge on byte-identical APPLIED
model artifacts.

This is a local persistence/replay demonstration, not a multi-region availability
claim.

## Governance boundary

Every result is `LOCAL_DEMO_ONLY` and records:

```text
authoritative: false
governance_eligible: false
execution_authorized: false
feature_010_go_claimed: false
```

The Java transport signatures use real disposable Ed25519 demo keys. Native QC
signature IDs are explicit local-demo content-ID placeholders, not Ed25519 votes
from independent human/controller identities. Consequently, `ChainVerifier` is
exercised against the demo QC objects, but the run does not prove a cryptographic
controller quorum. It also does not create `BenchmarkDefinitionQC`,
`BenchmarkResultQC`, a real-WAN result, controller appointment, Feature 010 GO, or
Feature 011 authority. Controller governance remains a separate workflow.

MNIST attribution: Yann LeCun, Corinna Cortes, and Christopher J.C. Burges,
<https://yann.lecun.org/exdb/mnist/index.html>.
