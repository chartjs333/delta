# Feature 010: SIMULATED_LOCAL

`SIMULATED_LOCAL` is a separate, non-qualifying development mode. It runs four
Docker controller processes with real ephemeral Ed25519 test signatures on one
internal Docker bridge. One machine/administrator owns every test key. This is
simulated governance and a local network, with no independence or real-WAN claim.

The current runnable slice is **infrastructure smoke only**. It does not run
training, Java/Netty, native consensus, PARAMETER/APPLY, or WAL. Feature000
arithmetic/model binding remains a prerequisite for those executions in either
mode. No Gate A/B/C/D task is completed by this smoke test.

## Run

From the repository root, with Python 3.12+ and Docker running:

```powershell
python tools/feature010/simulated_local.py plan --mode SIMULATED_LOCAL
python tools/feature010/simulated_local.py run --mode SIMULATED_LOCAL
```

The first run builds `Dockerfile.simulated` from a digest-pinned Python 3.12.11
image. The build downloads only the base image if it is absent; no pip/apt
resolution occurs. Execution uses the resolved immutable image ID. An existing
local image can be supplied with `--image sha256:<full-image-id>`; tags are refused.
An alternate image is recorded as such, never presented as the pinned baseline.

Each invocation creates a unique directory under
`artifacts/feature010/SIMULATED_LOCAL/sim-<uuid>/`. Use `--output PATH` to choose
another parent directory. Existing runs are not overwritten. Do not use the
production evidence namespace for these files.

No host port, Docker socket, production credential or model/data directory is
mounted into a controller. Containers have read-only roots, no Linux capabilities,
bounded memory/CPU/process counts and temporary key storage. The runner removes
only its exact named containers and network in `finally`; `cleanup.json` records
anything left behind. No `docker prune` or deletion of other workloads occurs.

The GPU probe checks actual `nvidia-smi` visibility through `--gpus all` and records
device/driver identity. It does not test CUDA kernels, PyTorch, memory headroom,
the frozen 8 GiB training profile, or Gate B. Missing GPU access does not prevent
the controller/network smoke; the probe's actual exit code is preserved.

## Executed scenarios

1. Four online controllers sign one exact canonical simulation body.
2. Kill controller 4: three signatures still meet the simulated threshold.
3. Kill controller 3: two signatures cannot meet that threshold.
4. Restart controller 3: its test key and generation rotate; old-generation votes
   are rejected. This is test-identity fencing, **not durable consensus recovery**.
5. Offline verification rejects duplicate voters, shared public keys, changed
   bodies, bad signatures and production/runtime signing purposes.

The network observations are measured HTTP-plus-signing round-trip times and JSON
body byte counts. They exclude HTTP/TCP overhead and retries. They are neither
phase timings nor the 100 ops/s/saturation/profile-selection benchmark. This
initial slice has no TLS, `tc/netem`, WAN path emulation or real WAN. These remain
separate implementation/qualification tasks.

## Evidence and verification

`manifest.json` binds source commit/tree, whether the checkout was dirty, actual
runner/Dockerfile hashes, image ID, Docker version and GPU visibility. Four phase
files contain public keys, generation IDs, signatures and raw local observations.
Private keys never leave controller tmpfs and are not evidence.

`report.json` and an identical SHA-256-named file contain the recomputed report
and hashes of the manifest/phase files. Offline verification recomputes signatures,
quorum results, negative probes, accounting checks and artifact IDs. If a saved
`report.json` exists, it must match the recomputed report exactly.

With OpenSSL 3 available, verification is:

```powershell
python tools/feature010/simulated_local.py verify --output PATH_TO_ONE_RUN
```

Or run the same command in the recorded image with networking disabled, mounting
the runner at `/simulated_local.py` and the run directory read-only at `/evidence`.
The verifier is offline; possession of public keys is sufficient.

Every report has fixed boundaries:

```json
{
  "mode": "SIMULATED_LOCAL",
  "label": "SIMULATED",
  "authority_scope": "LOCAL_DEVELOPMENT_ONLY",
  "result_type": "SIMULATED_INFRASTRUCTURE_REPORT",
  "gate_eligible": false,
  "primary_eligible": false,
  "real_wan_eligible": false,
  "governance_independent": false,
  "benchmark_result_qc": null,
  "feature010_go_checkpoint_sha": null,
  "feature011_admitted": false
}
```

`diagnostic_status=PASS` means only these infrastructure checks passed. The separate
qualification status remains `STOPPED_BEFORE_PROTOCOL_EXECUTION`. No ResultQC is
created. Its signature domain and body type differ from both benchmark governance
and runtime certificates. Relabeling the report cannot turn it into either kind.

## Moving to real resources

There is no `--production` or `--promote` switch. Real independent controller
custody, approved TLS/WAN inventory and evaluator signatures must enter through
the existing qualification contracts. They require a new frozen source/environment/
definition and a fresh run. Simulation keys, observations and reports cannot be
reused as qualifying evidence.

## Scope review

Formal impact: `NONE` for this infrastructure-only tool. It does not import or
invoke the worker training, native/FFI, Java, benchmark-governance signing or
current-pointer APIs. The accepted formal files and semantics ID remain unchanged.
Review is a self-review, as requested by the user; it is not an independent
formal/governance attestation. Task references: T013, T018, T023, T051 and
HR010-001; their qualifying completion states remain unchanged.
