# Campaign 02 replacement bootstrap registration package

This directory records the successful zero-execution `REGISTER_ONLY` run for the
replacement Campaign 02 default-branch bootstrap. It is an unsigned registration
package, not execution authority.

## Accepted bootstrap lineage

- Caller PR: `#27`, independently approved at
  `410ea1dd9c3dfe97d2073335c4e418001fb5807e`.
- Bootstrap merge commit: `2197a0eeff6daafa031d002725e09e0cf465ce34`.
- Merge parents: `7ca7de2a7e2e423590c1b2cb21e2c535796ecb30` and
  `410ea1dd9c3dfe97d2073335c4e418001fb5807e`.
- Merge tree: `b9d482b60ff50b60d361c5c453222621ce85a9f6`.
- Bootstrap workflow: `.github/workflows/campaign02-stage-a-bootstrap.yml`.
- Bootstrap workflow Git blob: `a60fd3fc44e33c5abcce27586fd7c67e7d16abe9`.
- Bootstrap workflow content ID:
  `sha256:7cabaa1cce8b69233a49c21fd82beacac09975bfc9f961573b820938a11c4482`.
- Qualified source commit: `95b287168ad02bbe585fbb05a7b27bbd951713f3`.
- Qualified source tree: `814afa83551bab2312f99e68b9f66ac48dc7158c`.
- Qualification PR: `#26`, merged as
  `b2af7b926f3525494bb5634dbedcca3fe97051e1`.
- Terminal qualification receipt:
  `sha256:b54ab4b75a14609d79ee6f1647486a56b76ae4b872ace5477a541b04569802d9`.
- Reusable Stage A workflow content ID:
  `sha256:05da996e4d8f67ad7b11d2c5bfc152a804201936de63ed13441817b576d8396f`.

## Zero-execution registration

- Registration workflow: `356506253`.
- Registration run: `34753634320`, attempt `1`.
- Run HEAD: `main@2197a0eeff6daafa031d002725e09e0cf465ce34`.
- Registration job `103714222939`: `success`.
- `EXECUTE_STAGE_A` job `103714223445`: `skipped`.
- Registration artifact: `10315828623`.
- Artifact name:
  `campaign02-bootstrap-registration-34753634320-attempt-1`.
- Artifact archive digest:
  `sha256:92ae026cb7e305dd8e5f3f9d08bcb5349834b8b0803018f5421c2bd4dbb3cd77`.
- Extracted zero-execution marker SHA-256:
  `sha256:1fd9947b32442aeed53915ffd5beb2b8b3892c1713e52a77d681f7fe9c0605fc`.

The marker records no authority bundle, zero execution artifacts, zero executions,
zero observations, zero Stage A plans and no `StageGateReceipt`.

## Fresh canonical identities

- Bootstrap mapping ID:
  `sha256:7c03edabceabf86575f87b69e7ccc089d01eb57e0e06a3cbeeffffadadec3583`.
- Raw GitHub API evidence root:
  `sha256:9375a72a5d7cc09800a6d031e5d9efe7335df4a59cc034f826437ba9708c9717`.
- Auxiliary raw jobs snapshot ID:
  `sha256:b25f5fa93af1f1dd9a302b139827b8854cd3cb44571bf1e6ef458e8aa296bc4d`.
- Registration receipt ID:
  `sha256:fabdccc49a19b8558003b163e6f59979229de561ce0fa86d3807f5ffea5fb84e`.

The API evidence preserves the exact response bytes for workflow metadata, the
default-branch ref, the bootstrap workflow file/blob, the completed workflow run
and artifact metadata. The auxiliary jobs snapshot preserves the exact jobs API
response bytes and proves that the inert registration job succeeded while the
execution job was skipped.

## File-byte digests

- `campaign02-workflow-bootstrap-mapping.json`:
  `sha256:db026b39a1e4806e61240bd0e45204c5457306a7c5483f48d9f21ab0f584a437`.
- `campaign02-workflow-registration-api-evidence.json`:
  `sha256:faa7ce2ae49d11b38ce4443d28e93d7119945391e8d11cd3e17047918f0e9571`.
- `campaign02-workflow-registration-jobs-api-snapshot.json`:
  `sha256:e57872517892e842dd25ee8d123a672082c93d29c372f17d5ac29d843e09d7cd`.
- `campaign02-workflow-registration-receipt.json`:
  `sha256:f9c8b98e351e83f5afd3321c1f8c5b10482e4d06fba38a2508d71f420d5ae69e`.
- `zero-execution-marker.json`:
  `sha256:1fd9947b32442aeed53915ffd5beb2b8b3892c1713e52a77d681f7fe9c0605fc`.

## Governance status

`AWAITING_FRESH_DETACHED_SIGNATURES_AND_INDEPENDENT_REVIEW`

No bootstrap validator set, mapping votes, registration votes or verified
attestation is included. Those cryptographic statements must be supplied by the
independent controllers for the fresh mapping and receipt IDs above. The closed
PR `#24` mapping `sha256:c7995666a7bc14272638bee33f2186267c1383233a393a9c416a06d271ce6208`
and receipt `sha256:99ec1cdfcc50bc82bb268227b3a1a0e1e943fad2518252a779a6ad270b21918f`
remain permanently superseded and must not be signed or reused.

This package does not authorize `EXECUTE_STAGE_A`, C2-023, C2-024, Stage A/B/C,
real-WAN execution, `BenchmarkResultQC`, Feature 010 GO or Feature 011.
