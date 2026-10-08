# Retention policy source binding checkpoint

8 October 2026. T047/T053, ISC-S16-D01. **NEED_DECISION; R2.3 OPEN; Formal NO_GO.**

The storage byte component is published at `d1608a1226bbb931ad2c6b078e0d2bb202545122`.
It checks the signed `retention_epoch_id` against a supplied component Context.
It does not resolve the original retention obligation. The next source-binding
step exposed a missing contract for that resolution. No code, schema, model,
proof, producer rule, retention period or deployed service changes accompany
this checkpoint.

## Existing obligation and exact sources

Pins below refer to exact Git blobs, not mutable worktree text. Their hashes,
relevant line ranges and bounded search results are in
`evidence/storage-source-v1/retention-policy-boundary.json`.

| Pin and path | What it establishes |
|---|---|
| `60c692f6e391f839829dfc64e93380db54cd507b:specs/003-bft-round-state-machine/spec.md`, FR-014 | Storage statements must bind exact leaf IDs, lengths and retention epoch. It does not define the retention policy object or its resolution. |
| `1438fa3d78ec99291475cf4660fd8c190ac01bb3:docs/adr/0016-storage-availability-source-binding-v1.md`, section 3 | `storage_authority` contains epoch/registry; `availability_policy.storage_binding` contains retention epoch, storage epoch, registry and threshold. The retention epoch names an exact immutable obligation; original policy must be available, otherwise verification fails closed. |
| Same ADR, sections 4–6 | A and D sign/bind the retention epoch and full context; step 1 resolves the original policy. An epoch label or signature alone does not supply that policy. |
| `90561a97de7f41f409bf22065ad6cdc9b3932458:docs/adr/0018-authenticated-availability-contract-v1.md`, section 4 item 5 | The approved O contract expressly requires resolving the original retention policy, not inferring it from an epoch label or clock. Missing policy rejects. It adds no duration or expiry rule. |
| `26eb02d0632435c9aa0d8ef44eb496b6fa73dd13:docs/adr/0013-snapshot-provenance-profile-v1.md`, sections 2–3 | Independent configuration/source pins provide the authority route. They do not themselves supply a missing policy encoding or interpretation. |
| `d1608a1226bbb931ad2c6b078e0d2bb202545122:formal/reference/storage_source/codec.py`, `Context`, `context`, `authenticate` | Concrete equality and signature checks; no retention-policy input, decoder or resolution rule. This limitation is explicit in the existing component. |

The approved O decision remains
`scope-decision-e5c12ebc8342d99630d5fcf28a9c6753`, scope 11. Its removal of
physical-presence claims does not remove section 4 item 5. The request is not
to reopen O, F/E, R2.1/R2.2 or the completed E audit.

## Minimal unresolved relation

The missing link is:

`independently pinned initial/RoundConfig policy + original retention_epoch_id`
`→ exact original retention obligation/preimage and deterministic binding check`.

The available contract gives equality to the original configured label, but
does not provide a policy object, an authoritative existing source path for
that object, or a rule resolving that label to the obligation asserted by A/D.
No new signed field is claimed necessary: an existing binding through the
signed RoundConfig could suffice if its exact policy contract is supplied.

An indistinguishability example explains the limit. Fix identical bootstrap,
RoundConfig storage-binding fields, A/D bytes and valid signatures, with label
`retention-1`. Interpreting that label as either obligation P or a different
obligation Q leaves all current component inputs and checks unchanged. Label
equality cannot decide which obligation was originally selected. P and Q are
abstract unequal interpretations, not proposed retention durations, instantiated
production histories or an executed safety counterexample. The missing
normative resolution would exclude the ambiguity; no impossibility theorem is
claimed.

This finding does not demand a clock, expiry implementation, honest storage,
physical observation, perpetual retention or a new trust root. O continues to
allow false storage claims and physical loss. The issue is the identity and
meaning of the declaration being authenticated, not proof of its fulfillment.

## Search boundary and decision

The audit checked the pinned native N and profile P schema/runtime/specification
surfaces, the approved S/O documents, current reference code, and reachable Git
history for `retention_epoch_id`. N/P have the FR-014 requirement but no concrete
storage-retention resolver. The reachable additions of that field are S and the
new byte component. This is a finding about the available pinned corpus; it
does not rule out an independently supplied external policy contract.

The Pending decision requests one of these concrete resolutions:

1. Supply an already applicable immutable policy contract and original evidence
   path, including how the configured label selects it and how its original
   bytes are bound to the independent configuration.
2. If none exists, specify/authorize the exact missing retention-policy binding
   as a new contract decision under the existing provisioning authority. Any
   change of the O claim or signed/configuration bytes must be explicit.

No option, retention duration, encoding, authority or source restriction is
selected automatically. Approving an unchanged request that contains no policy
definition does not resolve this gap. General R2.3 authorization remains valid.
No source-success boolean or supplied Context can replace the missing binding.

## Workflow and preserved state

Official read-only observability confirmed execution revision 194, active
`formal-linkage`, assignment `13069d7e-a148-475a-bd49-9885bf2f283d`.
Fresh actual-role GET verified scope 11, source/core hashes and persisted ACK
`scope-ack-a07a96b9126f50c24a663f2b99658f95`. The general whoami query succeeded;
repository replies timed out, including a 90-second attempt. Observability and
the role-authenticated request context independently confirmed the same current
assignment. No new role was inferred from local service state.

No worker completion/result or review is claimed by this document. A Pending
request is not a graph transition or approval. The existing assignment, reviews,
old objects/signatures/QC/WAL, delivery multiplicity and published component
remain intact. Full source/public-state composition and the named recovery
theorem remain unproved; production integration and full R3 remain forbidden.
