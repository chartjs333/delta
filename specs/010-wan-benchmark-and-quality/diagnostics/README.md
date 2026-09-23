# PR50 sidecar diagnostic campaign

This directory defines one non-qualifying diagnostic campaign. It separates
scheduler/allocation stalls from runtime demand before a later, separately
authorized embedded-versus-sidecar comparison. Diagnostic evidence is rejected
by `assemble_sidecar_comparison.py`; it cannot select a profile or establish a
Feature 010 gate, `BenchmarkResultQC`, Feature 010 GO, or Feature 011 authority.

No executable manifest, allocation, ledger, or result is checked in here.
`sidecar-diagnostic-manifest.example.json` is deliberately
`EXAMPLE_NOT_EXECUTABLE` and contains impossible identities.

## Immutable inputs and one-shot order

The following order is part of the evidence contract:

1. Commit all implementation changes as source commit **S** and record both
   `S` and `tree(S)`.
2. In the pinned build container, use the checked-in allocation assembler below
   to execute the canonical build plan. It records a full replacement
   environment, absolute executable argv, exact source working directory,
   captured stdout/stderr, `S/tree(S)`, builder image digest, and each output
   hash. The receipt's invocation hash is independently recomputed.
3. The same assembler creates the allocation manifest with exclusive creates
   and immediately round-trips it through the production verifier. It binds every input hash,
   the build-provenance receipt, the complete JDK tree inventory (canonical
   relative path, kind, mode, symlink target or file content), exact sibling
   `java`/`jfr`, container image/runtime, cgroup mode, cpuset, CPU limit, memory
   limit, and Java's cgroup-aware `availableProcessors()` result.
4. In a later, clean manifest checkout **M**, commit one canonical manifest
   marked `FROZEN_EXECUTABLE`. It binds S, the allocation manifest, collector
   script hash, random receipt nonce, host-exchange paths, an external ledger,
   the evidence path, 100 offers/s, one duration, and exactly
   `EMBEDDED_FFM` then `ISOLATED_SIDECAR`.
5. Create empty host-exchange, evidence-parent, and ledger directories. The
   ledger must be outside the evidence directory. Never reuse a campaign ID.
6. Start the container with S, M, and the allocation mounted read-only. Run the
   non-consuming preflight into a container-temporary receipt, then exclusively
   create the consuming attempt/ready seal. Only after that durable arm exists,
   start the preregistered Windows collector and run the diagnostic once.
7. Retain the ledger and evidence directory whether the attempt completes,
   fails, or is interrupted. Deleting either and trying again is forbidden.

## Deterministic allocation build and assembly

Allocation/provenance generation is not a manual JSON procedure. In the exact
pinned builder container, create one canonical plan conforming to
`sidecar-diagnostic-allocation-plan.schema.json`. Its exact fields are the
fresh absolute allocation root and allocation-manifest output path, source
commit/tree/repository, image/runtime identity, resource limits, and an
invocation containing absolute argv, `environment_mode: "REPLACE"`, the full
replacement environment, and a working directory exactly equal to the clean
source checkout. The manifest output must be outside the allocation root.
Because the replacement environment is serialized into provenance, it must be
an explicit minimal build allow-list and must not contain credentials or other
secrets.

The build argv must create this fixed Linux allocation layout in the previously
nonexistent root:

```text
corpus.bin
sidecar-diagnostic-tests.jar
jdk/bin/java
jdk/bin/jfr
libdelta_ffi.so
delta_runtime_sidecar
bin/strace
```

The checked-in source-bound builder used by that argv is
`build_sidecar_diagnostic_allocation.sh`. Invoke it through the pinned
`/bin/sh`, passing a fresh allocation root and a distinct fresh retained build
root. It uses JDK 25, GCC/C++20 with warnings-as-errors and no fast-math, builds
the production FFI and non-qualification sidecar, emits exactly 7,000 ordered
DLTSTRC1 operations (1,000 warm-up plus 60 seconds at 100/s), copies the
complete JDK, deterministically enables the preregistered `jdk.SafepointEnd`
event in the allocation-local `profile.jfc`, and copies the exact `strace`
executable into the frozen allocation. The allocation assembler independently
rejects a profile that does not enable every preregistered event and remains the
only supported caller because it binds the complete argv, replacement
environment, logs, source commit/tree, and output hashes.

Run exactly:

```text
uv run python /source-s/specs/010-wan-benchmark-and-quality/diagnostics/assemble_sidecar_diagnostic_allocation.py \
  build-and-assemble \
  --plan /sealed-inputs/sidecar-diagnostic-allocation-plan.json \
  --source-checkout /source-s
```

The assembler refuses a dirty or mismatched source checkout, relative build
executable, non-replacement environment, pre-existing allocation root,
pre-existing provenance/allocation output, missing/empty required artifact, or
noncanonical plan. It runs the exact argv without a shell, retains
`build.stdout` and `build.stderr` as hash-bound execution records, inventories
the complete JDK tree, exclusively creates both canonical receipts with
durability barriers, and verifies the result with
`load_and_verify_allocation`. It never starts a diagnostic lane.

An independent source-only recheck is:

```text
uv run python /source-s/specs/010-wan-benchmark-and-quality/diagnostics/assemble_sidecar_diagnostic_allocation.py \
  verify \
  --plan /sealed-inputs/sidecar-diagnostic-allocation-plan.json \
  --source-checkout /source-s \
  --allocation-manifest /sealed-inputs/frozen-allocation.json
```

Only after that succeeds should the allocation root be mounted read-only and
its allocation-manifest hash copied into the later executable campaign
manifest. The plan, build logs, build-provenance receipt, and allocation
manifest are retained together; none may be regenerated under the same
campaign identity.

Before creating any ledger record, the runner verifies both clean Git
checkouts, exact commits/trees, the tracked manifest blob, all allocation and
build hashes, the JDK tree, read-only mounts, exact argv-to-artifact bindings,
live cgroup identity, and every capability probe. That first phase creates only
a container-temporary receipt whose fixed state is
`PREFLIGHT_PASSED_NON_CONSUMING` and whose `consumes_campaign` value is `false`;
its path must be under the container temporary directory and outside the
evidence, host-exchange, and ledger roots, so it cannot alias a consuming
record. It creates no host artifact, evidence directory, or ledger record. A
separate arm phase revalidates the frozen identities, then creates
`<campaign>.attempt.json` with state `ARMED_ONE_SHOT_NO_RERUN`, an OS-level
exclusive create, and a durability barrier. This arm is the only consuming
transition and is the collector's ready handshake. Every run first creates an
exclusive `<campaign>.started.json` execution claim before any live validation
or capture side effect. Completion and failure both compete for the same
exclusive `<campaign>.terminal.json` arbitration record, then create exactly
one of `<campaign>.completed.json` or `<campaign>.failed.json`. A second runner
cannot terminalize the execution whose started claim it lost. Wrapper-side
host-receipt/collector failures after the durable arm invoke the same failure
transition. These records are outside the removable result tree, and no record
is replaced or truncated.

The direct container entry point is:

```text
uv run python /source-s/specs/010-wan-benchmark-and-quality/scripts/run_sidecar_diagnostic.py \
  --manifest /manifest-m/s15v2-pr50-diagnostic-manifest.json \
  --manifest-checkout /manifest-m \
  --source-checkout /source-s \
  --preflight-receipt /tmp/s15v2-pr50-diagnostic.preflight.json \
  --preflight-only

uv run python /source-s/specs/010-wan-benchmark-and-quality/scripts/run_sidecar_diagnostic.py \
  --manifest /manifest-m/s15v2-pr50-diagnostic-manifest.json \
  --manifest-checkout /manifest-m \
  --source-checkout /source-s \
  --preflight-receipt /tmp/s15v2-pr50-diagnostic.preflight.json \
  --arm-only

uv run python /source-s/specs/010-wan-benchmark-and-quality/scripts/run_sidecar_diagnostic.py \
  --manifest /manifest-m/s15v2-pr50-diagnostic-manifest.json \
  --manifest-checkout /manifest-m \
  --source-checkout /source-s \
  --preflight-receipt /tmp/s15v2-pr50-diagnostic.preflight.json \
  --output-directory /evidence/s15v2-pr50-diagnostic
```

`Invoke-SidecarDiagnosticCampaign.ps1` is the Windows/Docker Desktop wrapper.
It verifies the collector hash and Docker version, launches the exact image
with no network and the frozen quota/cpuset/memory, mounts source, manifest and
allocation read-only, runs preflight, durably arms the attempt, and only then
starts `Collect-SidecarDiagnosticHost.ps1`. The collector independently refuses
to publish a receipt unless that exact campaign's arm seal exists. All host and
container paths are explicit parameters; the wrapper does not invent a
replacement manifest or allocation. Review the command and parameters before
the unique real run.

## Independent host evidence

Container environment variables are not accepted as image, runtime, or host
identity evidence. The PowerShell collector runs outside the container. It
hashes its own preregistered source, reads container ID/image/resource limits
from Docker, records the Docker server version and Windows machine identity,
and exclusively writes a nonce/campaign-bound host receipt. The runner compares
that receipt with both the allocation and its own `/proc`/cgroup observations.

The runner writes `lanes-complete.json` only after both raw lanes are durable.
The host collector hashes that handshake, then writes final telemetry covering
the whole capture. Docker Desktop/WSL pause/restart/suspend and Windows
WHEA/storage/reset/thermal/power families are either an explicit event list or
`NOT_AVAILABLE(reason)`; an empty successful query is distinct from an
unavailable query. Final evidence retains exact copies of both host documents.

Linux cgroup paths are resolved from `/proc/self/cgroup` together with each
mount's root and mountpoint in `/proc/self/mountinfo`. In particular, Docker
Desktop's v1 form, where process path and mount root are both `/docker/<id>`,
resolves to the controller mountpoint. There is no fallback to an unrelated
controller root.

## Real scheduling and runtime path

`SidecarDiagnosticCapture` reaches the existing comparison implementation in
`SidecarComparisonCapture` and consumes the same DLTSTRC1 corpus. Each operation
uses the real `EmbeddedAdapter` or `IsolatedAdapter`; it is not a synthetic
timer loop. The warm-up remains exactly 1,000 operations and the measured grid
remains exactly 100 offers/s with absolute monotonic deadlines, no rebase, no
catch-up rewrite, and no rate reduction.

For each slot, the lane records a wake-up timestamp immediately after the
absolute wait. CPU/thread/schedstat, corpus and WAL preparation then run. A
separate `actual_offer_ns` is captured immediately before the real
`adapter.tryExecute` call. Therefore:

```text
wakeup_lateness_ns    = wakeup_ns - scheduled_offer_ns
preparation_latency_ns = actual_offer_ns - wakeup_ns
scheduler_lateness_ns = actual_offer_ns - scheduled_offer_ns
```

A miss is `scheduler_lateness_ns >= 10,000,000`. A harness preparation defect
is derived, rather than asserted, when the final offer is late but wake-up was
not: `miss && wakeup_lateness_ns < 10,000,000`. The 100/s policy is unchanged.

Every offer must have available process CPU, scheduler-thread CPU, Linux
schedstat, a present WAL observation made between wake-up and offer, and exact
admission/timing fields. Every completion must join by ordinal/request/profile,
carry exact offered-to-completion and native-phase latency, and have a present
post-completion WAL observation. Offers, completions, state roots, and durable
sequences must be complete and contiguous. The embedded lane uses the versioned
native submit-receipt ABI and rejects a missing native journal sequence; Java
does not synthesize one. The first measured completion is anchored to the
post-warm-up native state root and sequence, and the final state is read back.
Exit must be zero, timeout is forbidden, and terminal state read-back must pass.
Empty, truncated, duplicated or manufactured zero-miss logs fail before
classification.

The host sampler timestamps the beginning and end of each multi-file sample.
A missed interval may use only a sample whose end is at or before the scheduled
deadline and a sample whose beginning is at or after the actual offer. Samples
that straddle either boundary cannot establish a causal predicate. Process CPU
records bind PID, resolved executable, Linux start time and parent chain. When
`strace` wraps a lane, its process and any non-target descendants are excluded.
The sustained-demand predicate subtracts the maximum CPU that could have run
in the two sampling overhangs, so activity outside the missed interval cannot
be relabelled as causal target demand.

## Collector capability gates

Preflight runs before the one-shot attempt record and is explicitly
non-consuming. Every subprocess receipt contains exact argv, an explicit
working directory, `environment_mode: "REPLACE"`, and the complete minimal
environment; the lane and probe environments cannot inherit JVM, loader, or
tool options from the wrapper/container process. Preflight proves that:

- the exact Java dry-run sees the frozen processor count and 100/s contract;
- the exact JDK's `profile.jfc` enables every selected GC, safepoint, and
  compiler family, then creates and parses a short real JFR recording (zero
  occurrences remain valid because enablement is separately proven);
- the exact `strace` traces a child process and parses at least one real
  `fsync` event;
- the sidecar starts with its expected no-argument failure and the native
  library loads; and
- CPU and IO PSI are explicitly `AVAILABLE` or `NOT_AVAILABLE`.

Each real lane must also produce a non-empty parseable JFR recording and at
least one completely parseable `fsync`/`fdatasync` trace. A missing PSI stream
is allowed to preserve the one campaign, but every miss that lacks its required
PSI bracket is necessarily `INCONCLUSIVE`. No absence is inferred from missing
telemetry.

## Deterministic classification

For every missed slot the runner recomputes all joins and predicates from raw
lane logs, conservative host samples, JFR JSON, strace lines, WAL observations,
and final host telemetry. Classification order is:

1. `ENVIRONMENT_INVALID` for an overlapping physical/host fault, or when the
   target was runnable but not continuously consuming CPU and an overlapping
   cgroup, PSI, run-queue, or WAL/fsync signal exists.
2. `HARNESS_OR_TIMER_DEFECT` for the derived wake-up/preparation condition.
3. `GENUINE_RUNTIME_DEMAND_INDICATOR` only when every mandatory collector is
   available, there is no environment invalidator, and sustained target CPU
   demand overlaps the lateness without an overlapping JFR GC, safepoint, or
   compiler interval. JFR pauses/compiler activity are runtime explanatory
   evidence, not an environment invalidator, so their overlap remains
   `INCONCLUSIVE` rather than being labelled genuine demand.
4. `INCONCLUSIVE` otherwise.

No misses yields `NO_MISSED_SLOTS_OBSERVED`. Mixed per-miss causes yield
`INCONCLUSIVE` rather than a preferred narrative.

## Independent verification

Evidence artifact paths are relative to the evidence root. The verifier does
not trust the stored classification. It reopens the external attempt, started,
terminal and completion ledger, clean source and manifest checkouts, frozen
manifest and allocation; recomputes all file/JDK/build hashes; validates every
raw lane event; reruns the exact JFR tool against each recording; reparses all
strace files; redoes every host join, missed-slot predicate and classification;
and checks the completion seal's evidence hash. It rejects an absolute/traversing
artifact path, conflicting failure seal, incomplete lane, or fabricated zero-miss
result.

Run it in the same frozen container/allocation context:

```text
uv run python specs/010-wan-benchmark-and-quality/scripts/classify_sidecar_diagnostic.py \
  /evidence/s15v2-pr50-diagnostic
```

## Source-only checks

These checks do not execute a lane or campaign:

```text
uv run ruff check \
  specs/010-wan-benchmark-and-quality/diagnostics/assemble_sidecar_diagnostic_allocation.py \
  specs/010-wan-benchmark-and-quality/scripts/sidecar_diagnostic_common.py \
  specs/010-wan-benchmark-and-quality/scripts/run_sidecar_diagnostic.py \
  specs/010-wan-benchmark-and-quality/scripts/classify_sidecar_diagnostic.py \
  specs/010-wan-benchmark-and-quality/tests/test_sidecar_diagnostic.py
uv run pytest -q specs/010-wan-benchmark-and-quality/tests/test_sidecar_diagnostic.py
java -ea -cp <compiled-sidecar-test-classes> \
  io.deltareduce.node.sidecar.SidecarDiagnosticCaptureDryRun
```
