# Campaign 02 bootstrap controller appointment and signing

**Status**: procedure proposed for governance review; no controllers appointed

**Related work**: T009, T051, HR010-018; C2-037 and C2-040

Apply the [trust and custody policy](campaign02-controller-custody-policy.md).
This procedure closes the missing organizational documentation before bootstrap
signing. It does not change the verifier or qualify new executable source.

## 1. Freeze the package to be reviewed

The current reference is the unsigned replacement package in
[draft PR #28](https://github.com/chartjs333/delta/pull/28), evidence HEAD
`84b337892cb70d0ce9823ef2d64fab572752b145`. Its
[immutable package README](https://github.com/chartjs333/delta/blob/84b337892cb70d0ce9823ef2d64fab572752b145/reports/benchmark/campaigns/campaign-02/bootstrap-registration/README.md)
records the byte digests and zero-execution lineage. These are reference inputs,
not a claim that a later HEAD has already been reviewed.

| Binding | Expected reference |
| --- | --- |
| Mapping ID | `sha256:7c03edabceabf86575f87b69e7ccc089d01eb57e0e06a3cbeeffffadadec3583` |
| API evidence root | `sha256:9375a72a5d7cc09800a6d031e5d9efe7335df4a59cc034f826437ba9708c9717` |
| Registration receipt ID | `sha256:fabdccc49a19b8558003b163e6f59979229de561ce0fa86d3807f5ffea5fb84e` |
| Bootstrap merge | `2197a0eeff6daafa031d002725e09e0cf465ce34` |
| Qualified source / tree | `95b287168ad02bbe585fbb05a7b27bbd951713f3` / `814afa83551bab2312f99e68b9f66ac48dc7158c` |
| Qualification receipt | `sha256:b54ab4b75a14609d79ee6f1647486a56b76ae4b872ace5477a541b04569802d9` |
| Registration run / attempt | `34753634320` / `1` |
| Artifact ID | `10315828623` |
| PR #28 signature window | After `2026-09-13T11:12:47.874641Z`, before `2026-12-12T11:07:55Z` |

Recompute the IDs from the pinned package with the existing canonical classes;
do not treat this table as a substitute for verification. Check the actual current
PR decision, artifact availability/expiry and terminal evidence before signing.
If the package is superseded or the window expires, stop and obtain a fresh
governance-reviewed package. The closed PR #24 mapping and receipt remain
permanently superseded. Do not refresh timestamps or edit an old receipt in place.

## 2. Complete the appointment register

Copy [the template](templates/campaign02-controller-register.template.json) into a
separate governance review change, for example
`reports/benchmark/campaigns/campaign-02/controller-governance/controller-register-v1.json`.
Do not put the template into the signed bootstrap-registration directory or pass
it to the protocol verifier as a validator set.

Replace every null required for appointment with verified facts. `slot` is only a
worksheet index, never a `signer_id` or `controller_id`. Set `template` to `false`
only in the completed copy; record its status as `PENDING_GOVERNANCE_REVIEW` until
the external exact-revision approval exists. Keep this source template blocked.

For each of the four slots, obtain:

- the accountable owner's auditable identity and authenticated acceptance reference;
- the chosen identity type, stable `signer_id` and `controller_id`;
- its independently generated public key in canonical Base64 and raw-key SHA-256;
- the administrative/custody domain, allowed signing/deployment/recovery roles,
  backup/export policy and sanitized immutable supporting evidence references;
- the owner-approved signing/evidence-verification procedure and audit location;
- key-binding verification and a bounded appointment validity period.

List the named governance authority and independent reviewer. Complete all six
pairwise independence reviews. Unknown ownership, inaccessible evidence or common
signing/recovery control blocks appointment. Services and bots need the same
evidence as people. This repository does not provide real owners or custody
systems to populate these fields automatically.

The register contains sensitive metadata only by sanitized reference. Share the
underlying restricted evidence with authorized reviewers through its approved
system; do not commit credentials or private infrastructure inventories.

## 3. Freeze the canonical validator set and approve custody

Construct `bootstrap-validator-set.json` only after all four owner/key bindings
are verified. Use the unchanged
[schema](../delta-protocol/schemas/010/campaign-02/workflow-bootstrap-validator-set-v1.json)
and `BootstrapValidatorSet.from_dict` from the qualified source:

- `type_name = CAMPAIGN02_WORKFLOW_BOOTSTRAP_VALIDATOR_SET`;
- `schema_version = 1.0.0`, inherited `formal_semantics_id`;
- `execution_authorized = false`, `f_b = 1`, `quorum_threshold = 3`;
- exactly four entries containing only `signer_id`, `controller_id`,
  `public_key_base64`.

Serialize `validator_set.document` with `canonical_json_bytes` (an optional final
newline is accepted by the CLI) and obtain `validator_set.content_id`. Record this
ID in the register and compare all four entries exactly. Owner names, custody
metadata and policy IDs belong only in the separate register/review record.

Obtain an explicit adoption/appointment decision referencing the frozen policy
and register revisions/digests, validator-set ID, package IDs, all four owner
acceptances, reviewer findings and the approved signing window. The approving
authority must explicitly permit bootstrap signing. Repository merge approval
and a cryptographic verifier PASS alone do not supply that permission.

## 4. Collect independently verified votes

Each controller independently checks the policy's signing checklist, creates the
existing `SignedBootstrapMappingVote` and `SignedWorkflowRegistrationVote`
payloads and signs each object's `.message` bytes with its own key. Retain the
verification and signing audit events, including actual submission time. Only
public vote artifacts leave the custody boundary.

The review overlay contains one canonical validator set, exactly three
`mapping-vote-<signer>.json` files and exactly three
`registration-vote-<signer>.json` files, using filesystem-safe file labels without
changing the signed IDs. Both quorums use the same set ID. Never generate all keys
on a coordinator or copy test keys into this package.

## 5. Run the existing canonical verifier and obtain final review

Use the existing
[`campaign02_bootstrap_control.py`](../specs/010-wan-benchmark-and-quality/scripts/campaign02_bootstrap_control.py).
It checks canonical file bytes, both quorums, API evidence and exact source/caller
checkouts. Run it with the qualified source's locked Python environment. The
following command assumes separately verified, clean checkouts at the pinned
bootstrap and qualified-source commits, and the completed signed overlay at the
operator-supplied absolute path. Replace the three signer file labels with the
actual selected quorums; mapping and registration trios may differ.

```bash
campaign02_package=/absolute/path/to/reviewed/bootstrap-registration
campaign02_bootstrap=/absolute/path/to/checkout-at-2197a0ee
campaign02_source=/absolute/path/to/checkout-at-95b28716
cd "$campaign02_source"
uv run python specs/010-wan-benchmark-and-quality/scripts/campaign02_bootstrap_control.py \
  --mapping "$campaign02_package/campaign02-workflow-bootstrap-mapping.json" \
  --validator-set "$campaign02_package/bootstrap-validator-set.json" \
  --vote "$campaign02_package/mapping-vote-SIGNER_A.json" \
  --vote "$campaign02_package/mapping-vote-SIGNER_B.json" \
  --vote "$campaign02_package/mapping-vote-SIGNER_C.json" \
  --registration "$campaign02_package/campaign02-workflow-registration-receipt.json" \
  --registration-api-evidence "$campaign02_package/campaign02-workflow-registration-api-evidence.json" \
  --registration-vote "$campaign02_package/registration-vote-SIGNER_A.json" \
  --registration-vote "$campaign02_package/registration-vote-SIGNER_B.json" \
  --registration-vote "$campaign02_package/registration-vote-SIGNER_C.json" \
  --bootstrap-root "$campaign02_bootstrap" \
  --qualified-source-root "$campaign02_source" \
  --repository chartjs333/delta \
  --workflow-ref chartjs333/delta/.github/workflows/campaign02-stage-a-bootstrap.yml@refs/heads/main \
  --workflow-sha 2197a0eeff6daafa031d002725e09e0cf465ce34 \
  --run-id 34753634320 --run-attempt 1 \
  --event-name workflow_dispatch --dispatch-ref refs/heads/main \
  --github-sha 2197a0eeff6daafa031d002725e09e0cf465ce34
```

Retain the actual successful output as `bootstrap-registration-verification.json`
in a fresh review overlay. Do not pre-create a PASS artifact, overwrite prior
evidence or replace a failure with hand-written JSON. Retain the exit status,
command/input revisions and reviewer evidence alongside the result. The output's
`execution_authorized` must remain `false` and `observations` must remain `0`.

Obtain current-head CI and a separate independent human governance review of the
actual terminal overlay HEAD, including its custody approval. Keep PR #28 Draft
until its existing governance process explicitly permits promotion. Neither this
documentation nor the registration verifier grants Definition, stage or merge
authority; C2-023 and C2-024 remain separate later decisions.
