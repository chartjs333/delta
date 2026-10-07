# ISC-S16-D01 — scope 11 storage source checkpoint

T047/T053, 7 October 2026. **R2.3 OPEN / Formal NO_GO.**

The exact O contract has been approved by human decision
`scope-decision-e5c12ebc8342d99630d5fcf28a9c6753`, scope revision 11.
Coordinator activation `47559b6bc7b39eda84ca631e70935a970b33e8ed` passed both
normal sequential process reviews; these are not independent GO attestations.
The graph assigned role 2753, assignment
`13069d7e-a148-475a-bd49-9885bf2f283d`, branch
`agent/isc-s16-formal-linkage`. Exact role ACK
`scope-ack-a07a96b9126f50c24a663f2b99658f95` is GET-confirmed.
Its effective-core hash is
`bfc8de59af53ab7034ae53ae729b023903bba6864ed58717041b8831423457e7`.

Commit `d1608a1226bbb931ad2c6b078e0d2bb202545122` adds the concrete
storage-source authentication component and reproducible evidence under
`formal/reference/storage_source/` and
`formal/proposals/evidence/storage-source-v1/`. The evidence's source and log
hashes were also checked against the actual committed Git blobs.

The narrowed implementation gap is exact Rs/Ks/A/Ms/SAG1/D/ac decoding and
cryptographic/per-leaf-witness verification. This component no longer relies on
an opaque authentication boolean. Every input occurrence is retained, including
duplicate, alternate and invalid delivery bytes. It does **not** establish the
origin or legal original cut of that inventory. No independent physical-history
premise was added; O does not infer remote presence from signatures.

The frozen R2.3 residual is still open: independently derive complete
source/configuration/aliases/units; remaining certificate/candidate/current/
environment collections and full revised public-state constraints; and initial,
incomplete and sufficient ABORT correspondence with nonempty lineage. The next
work derives component Context and witness eligibility from the original
configuration/ticket/commitment/manifest and source prefix, then composes the
approved O state/refinement relation and its applicable gates. Neither the
existing ledger aggregate nor a supplied Context is provenance. R2.1/R2.2 stay
closed in their original domains. No named recovery theorem or full R3 started.

## Publication failure, not a semantic decision

The component is locally committed but **not remote-published**. Three normal
pushes to the assigned branch received GitHub `Internal Server Error`:

- 16:54:41 UTC, request `E47E:339A47:42E725D:4020BEF:6AC67950`;
- 16:55:45 UTC, request `E65C:3774A8:4663EAF:432ACFF:6AC6798F`;
- 16:58:43 UTC, request `EB66:F223E:4405AF8:411DE16:6AC67A42`.

The last `git ls-remote` succeeded and still returned
`a2fd17259240be0a7721512e7a12fe972587f3bf`. No result, review or graph outcome
has been submitted for this unfinished worker assignment. Nothing is reported
as remotely reproduced, R2 closed or GO. This transport failure supplies no
reason for a scope amendment, new sprint, force push or manual graph transition.

Resume with official current identity and fresh effective scope, verify the
already persisted exact ACK, publish this same assigned branch when GitHub
accepts it, and continue the same unfinished work. Preserve existing reviews and
all previously accepted results. No renewed R2.3/O authorization is required.

## Local resource preservation

C: ran low twice during the workflow. Only executor-owned temporary raw HTTP
response copies were copied to D:, SHA-256 checked, and removed at their exact
old cache paths. Twenty copies totaling 8,280,135,254 bytes were retained in:

- `D:/delta-data/isc-s16-executor-http-cache-20261007-1623/`;
- `D:/delta-data/isc-s16-executor-http-cache-20261007-1642/`;
- `D:/delta-data/isc-s16-executor-http-cache-20261007-1650/`.

Each directory contains `relocation-index.json`; nginx-qa canonical history,
configuration, queues, credentials, services and Windows settings were untouched.
At 16:57 UTC C: had 3.29 GB free. Pagefile allocation was observed growing from
80,570 to 84,103 MiB earlier; this is an observation, not a complete disk-growth
attribution. Prefer D: for new build/log output and compact official observations.
Preserve demo services, frozen refs and all foreign files.
