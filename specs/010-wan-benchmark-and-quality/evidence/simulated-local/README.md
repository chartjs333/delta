# SIMULATED_LOCAL development evidence

This directory contains infrastructure-only evidence. It completes no qualifying
T028+ / HR010-004+ task, carries no BenchmarkResultQC and provides no Feature011
admission. The technical review below is self-review, not independent governance.

## Executed source and result

- Source: `744e9234d6040f4d7acf09f0b73a07d180c61884`.
- Source tree: `9da9306ef535ad0d1fff0e611d2f4d319283febd`; checkout clean at capture.
- Run: `sim-3ed32ec8feb34316a2be5b163435485d`.
- Report SHA-256: `560627eae83ac9d5f3b084c6caa2ba847d636537783ebfcac94b3d143199956a`.
- Diagnostic: `PASS`; qualification: `STOPPED_BEFORE_PROTOCOL_EXECUTION`.
- Physical device visibility: RTX 3070 Laptop, 8192 MiB, driver 581.32, same GPU
  UUID in host and container. CUDA training/8 GiB profile was not executed.
- Four / three / two / restarted-three actual Docker processes returned the
  expected simulation quorum outcomes. Native consensus/WAL was not exercised.
- Cleanup: no remaining containers or network from this run.

The nested directory includes the exact runner and Dockerfile bytes, public
identity/signature evidence, measured local HTTP round trips, raw byte counts,
manifest, report and cleanup result. There are no private keys. The report hashes
the manifest and phase/source artifacts; it has no self-hash cycle.

## Completed checks

- Docker execution and offline evidence verification on the exact source above.
- 18 simulation tests, including mutation of executed evidence: all pass.
- Existing formal contract suite: 56 tests pass.
- Existing formal phase-0 and toolchain-lock checks: pass.
- Existing merged FormalVerificationReport offline verification: PASS/GO for
  **unchanged** `cc98f15a...` semantics only.
- `ruff check .` and `ruff format --check .`: pass at the source checkpoint.
- Worker mypy: 102 source files, no issues.
- Worker pytest: 319 pass, 3 skip. Skips are the unavailable standalone C++
  compiler lane, dedicated physical QLoRA qualification, and optional CUDA smoke.
  They are not physical or cross-language qualification evidence.
- `git diff --check`: pass.

No new TLC/Lean/native/JDK/profile/Gate A/B/C/D qualification is claimed. Formal
source, native runtime, C ABI, Java and production benchmark contracts are unchanged.

## Self-review outcome

The mode has its own signing domain, type, source/evidence namespace and fixed
non-eligibility fields. It cannot sign a benchmark-definition/result vote or a
runtime action. Evidence mutation cannot relabel it as real WAN or gate-eligible.
Duplicate voters/shared keys, bad signatures, mismatched bodies and stale
generations fail closed. Restart intentionally rotates ephemeral test identity;
that result must not be interpreted as durable vote recovery.

The initial review found and corrected mutable runner binding, Windows/Linux
output ownership, report-promotion type checking, and helper-container cleanup
on failure. The final run binds an immutable per-run runner snapshot and cleans
only exact resource names created by that run.

Remaining Feature000/native/profile/scientific/WAN/ResultQC work is recorded in
the report's blocker list. A separate formal design candidate is
`cf918e8` on `codex/feature000-binding-candidate`; it is explicitly
`DRAFT_NOT_AUTHORITY`, with 13 passing arithmetic design tests and no new Formal GO.

## Offline verification

Use the recorded image ID from `manifest.json`. Mount the archived `runner.py`
at `/simulated_local.py` and the nested run directory read-only at `/evidence`:

```text
docker run --rm --network none --entrypoint python3 \
  --mount type=bind,source=<absolute-run-dir>/runner.py,target=/simulated_local.py,readonly \
  --mount type=bind,source=<absolute-run-dir>,target=/evidence,readonly \
  <recorded-image-id> /simulated_local.py verify --output /evidence
```
