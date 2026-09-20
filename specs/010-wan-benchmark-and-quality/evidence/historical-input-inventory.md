# Feature 010/011 historical input inventory

**Current authority base**: `7a9faf852e0ccae4d25fdc363fbf39ecf1719341`
**Current authority tree**: `2ae9ad2ad0064cfb65c956464dc737c2ab03034a`

None of the five named draft heads is an ancestor of the current base, and no head
contains a patch-equivalent commit suitable for wholesale reuse.

The manifest cannot embed its own final commit without a Git self-reference. The
verifier therefore computes actual HEAD/tree, ancestry and changed paths at run
time; the PR and official handoff bind that computed candidate commit externally.
Before merge these files are a proposed authority, not a current-main publication.

## PR #11 — historical NO_GO

- Head: `881301d8443c667a478617cc663d1450aee9777a`.
- Draft/conflicting; the recorded primary scientific pre-run stopped with zero
  executions.
- Feature 010 remained NO_GO and Feature 011 unauthorized.
- Decision: retain only the audit record and gate design; import no code, schema,
  candidate definition, or result.

## PR #19 — governance STOP

- Head: `b2af7b926f3525494bb5634dbedcca3fe97051e1`.
- Historical qualified source `95b287168ad02bbe585fbb05a7b27bbd951713f3`,
  tree `814afa83551bab2312f99e68b9f66ac48dc7158c`, did not obtain Definition
  governance, execution authorization, primary observations, or ResultQC.
- Decision: retain qualification facts as historical only; rebind and requalify any
  future implementation on the current lineage.

## PR #28 — unsigned zero-execution registration

- Head: `84b337892cb70d0ce9823ef2d64fab572752b145`.
- Historical run `34753634320` emitted zero executions, observations, Stage A
  plans, and StageGateReceipts.
- Mapping `sha256:7c03edabceabf86575f87b69e7ccc089d01eb57e0e06a3cbeeffffadadec3583`
  and receipt `sha256:fabdccc49a19b8558003b163e6f59979229de561ce0fa86d3807f5ffea5fb84e`
  had no validator set or detached signature quorums.
- Decision: historical provenance only; do not sign, refresh, or promote it as
  current authority.

## PR #29 — proposed custody policy

- Head: `de3348fdcbd527046d5b66bc6d8c90df098d5aa8`.
- Policy was proposed, not adopted. Four controller slots were unassigned and all
  six pairwise reviews pending.
- Decision: adapt its independence requirements into the current SpecKit; do not
  represent the proposal or template as an appointment register.

## PR #30 — non-authoritative demo

- Head: `670b58f4c400f5c8904ca40ba9cf3a2072e98d78`.
- Demo artifacts declared `authoritative=false`, `governance_eligible=false`,
  `execution_authorized=false`, and used placeholder native signatures.
- Current draft checks also contain failing Netty/native APPLIED and TSan lanes.
- Decision: import no demo/runtime diff and no benchmark/pilot evidence.

## Current-main artifacts retained

- The manual bootstrap caller is already on main with blob
  `a60fd3fc44e33c5abcce27586fd7c67e7d16abe9`. Its default `REGISTER_ONLY` mode
  is zero-execution; the separately selectable `EXECUTE_STAGE_A` mode is not
  inert and remains forbidden until all current-lineage gates and authorities
  exist. Neither mode supplies governance authority by itself.
- Ten generic model/data plugin files from the demo line were separately integrated
  through commit `ffdc148c59613949f50b1aff41d7ff3391275231` and PR #32 merge
  `4992d9e`; they are reusable working-version implementation, not demo evidence.
- No historical draft file is copied into this reconciliation candidate.
