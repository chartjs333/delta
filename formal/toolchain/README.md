# Pinned formal toolchain

The mandatory gate uses only the artifacts and exact dependency commits named by:

- `tla.lock` for SANY/TLC and the JVM;
- `lean.lock`, `formal/proofs/lean-toolchain`, `lakefile.toml` and `dependencies.lock.json` for Lean/mathlib;
- `container.lock` for the Linux/amd64 base image.

No lock may point at `latest`, `master`, `main`, a nightly channel or an unqualified container tag. Upstream branch names retained in the audited mathlib source manifest are informational; the effective dependency revisions are the full commits in `dependencies.lock.json`.

## Cache and offline policy

`prepare_cache.py --download` fetches the three binary artifacts into `cache/` and verifies size and SHA-256 before they are usable. Running it without `--download` performs verification only and never accesses the network.

The container build context is this directory:

```text
docker build --network none -t deltareduce-formal:local formal/toolchain
```

For a fully offline build, the pinned base image from `container.lock` must already be in the OCI cache and all binary files must already be in `formal/toolchain/cache/`. The image build has no `RUN` instruction that fetches packages or contacts a registry.

Lean package sources/oleans are a separate dependency cache governed by `formal/proofs/dependencies.lock.json`. The proof invocation must use an already materialized `.lake/packages`/cache matching that lock when public network is disabled. T062 archives and verifies that materialized cache as clean-reproduction evidence; its absence must fail closed rather than trigger an implicit download.

From a clean checkout, create the complete tracked-source manifest outside the
repository and run the retained reproduction in the prebuilt local image with
networking disabled:

```text
python formal/scripts/create_reproduction_source_manifest.py \
  --output /tmp/deltareduce-formal-source.json
docker run --rm --network none -v "$PWD:/workspace" -w /workspace \
  -v /tmp/deltareduce-formal-source.json:/source-manifest.json:ro \
  -e FORMAL_SOURCE_MANIFEST=/source-manifest.json \
  deltareduce-formal:local python formal/scripts/run_clean_offline_reproduction.py
```

The script refuses to pass unless it starts from complete tracked bytes matching
the mounted clean-Git manifest, runs inside Linux and Docker, observes only the
loopback network interface, verifies the complete local cache and passes every
machine gate. It regenerates Linux toolchain evidence and writes
`formal/reports/clean-offline-reproduction.json`; the report generator consumes
that exact evidence for FR-042. Report generation and verification then execute
as mandatory post-finalization gates. They are deliberately outside the
reproduction payload, which breaks the otherwise unavoidable
report→reproduction→report self-reference and ensures the report consumes the
fresh evidence from the same run.

The source manifest records two identities: the exact clean checkout (including
committed evidence/review overlays) and the latest commit that changes anything
outside the registered generated-output boundary. The latter remains the
reviewed source identity, so committing reproducible evidence or review
attestations cannot create a new `reviewed_commit` cycle.

Each successful reproduction check contains a versioned canonical result and a
source-bound receipt hash that the offline report verifier recomputes. Raw
stdout is retained only in failure diagnostics. Mandatory TLC configs use one
worker so graph depth is deterministic. TLC evidence content-addresses the
locked tool, module/config bytes, final state metrics, properties and required
action reachability; PID, timestamps, durations, heap/host telemetry, progress
rates and exact coverage counters remain non-addressed runtime diagnostics in
`formal/build/`. Mutant evidence hashes a normalized full counterexample that
retains state valuations while removing only those documented runtime fields.

## Update policy

1. Open an explicit toolchain update change.
2. Review stable upstream release notes and security/correctness fixes.
3. Pin release commits, artifact byte lengths and SHA-256 values.
4. Regenerate the complete Lean dependency/license lock.
5. Rebuild parser, safety, liveness, proof, mutant and refinement gates.
6. Invalidate earlier tool/evidence hashes and obtain the required reviews before GO.

Nightly/pre-release artifacts require a separately reviewed exception and cannot silently replace the mandatory stable profile.
