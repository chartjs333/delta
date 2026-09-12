# Campaign 02 bootstrap registration package

This directory records the successful zero-execution `REGISTER_ONLY` run for the
Campaign 02 default-branch bootstrap. It is an unsigned registration package,
not execution authority.

## Immutable provenance

- Bootstrap merge commit: `7ca7de2a7e2e423590c1b2cb21e2c535796ecb30`
- Bootstrap workflow: `.github/workflows/campaign02-stage-a-bootstrap.yml`
- Qualified source commit: `300ad8415862f82eeb9e0fd9c34c01620dfab399`
- Qualified source tree: `e3fe90b6eb90924c41b11cc9379e4752c99ffe74`
- Registration run: `34694625433`, attempt `1`
- Registration artifact: `10297469550`
- Registration artifact archive digest:
  `sha256:9e4fd6008b5dd4ef5ec38b4e8db4d926a06165a509bb4cbb679f6fddbda2f0fd`
- Extracted zero-execution marker SHA-256:
  `sha256:c6881ff57688ea197ad99e39f92eedb17a86bc233799980c33c0bc6a743cda7a`

## Canonical identities

- Bootstrap mapping ID:
  `sha256:c7995666a7bc14272638bee33f2186267c1383233a393a9c416a06d271ce6208`
- Raw GitHub API evidence root:
  `sha256:88a261c3d3d94b5352692be26c866ac8e01b887e2e40236d8e5f8981903be16e`
- Registration receipt ID:
  `sha256:99ec1cdfcc50bc82bb268227b3a1a0e1e943fad2518252a779a6ad270b21918f`

The API evidence contains the exact response bytes for the workflow metadata,
default-branch ref, bootstrap workflow file, workflow run and artifact metadata.
The repository verifier accepts their binding to the mapping and receipt.

## Governance status

`AWAITING_DETACHED_SIGNATURES`

No bootstrap validator set, mapping votes, registration votes or attestation is
included. The run executed zero Stage A plans, supplied no authority bundle,
created no observation and emitted no `StageGateReceipt`. It does not authorize
`C2-023`, `C2-024`, Stage A/B/C, a `BenchmarkResultQC`, Feature 010 GO or
Feature 011.
