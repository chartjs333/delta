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

## Update policy

1. Open an explicit toolchain update change.
2. Review stable upstream release notes and security/correctness fixes.
3. Pin release commits, artifact byte lengths and SHA-256 values.
4. Regenerate the complete Lean dependency/license lock.
5. Rebuild parser, safety, liveness, proof, mutant and refinement gates.
6. Invalidate earlier tool/evidence hashes and obtain the required reviews before GO.

Nightly/pre-release artifacts require a separately reviewed exception and cannot silently replace the mandatory stable profile.
