# ISC S16 contract freeze v1

**ISC-S16-A01 — documentation-only dependency/status freeze.**
Existing requirement/task linkage: feature-000 T010/T011/T024/T053/T057;
HR008-001/002/003/018. No production or formal qualification is asserted.

Source baseline: `ea5a70d8c5fd3516de243632f2c5681b0e5a6292`.
Sprint/from commit: `4873b3559b390318c0fc8ff80dd00ecea4ea7b59`.
Assigned scope: `docs/adr/0014-*.md` and the
[machine-readable checklist](evidence/0014-isc-contract-freeze-v1.json).
The sprint directory remains byte-for-byte intact. This freeze records existing
approval boundaries and makes the dependency direction explicit; it is not an
approval of all proposed production bytes, an implementation budget, or Formal GO.

## Status and precedence

| Contract/decision | Current status | Exact authority boundary |
| --- | --- | --- |
| [Commitment A](0014-isc-commitment-profile-v1.md) | APPROVED for FR-004 | Ordered unique tuples, canonical J(t), leaf/node/root rules; duplicate JSON member rejection. Does not qualify full context, producer or durability |
| [I-B](0014-isc-identity-sequence-amendment.md) | APPROVED architecture decision | b is consensus body identity; c is original witness/artifact identity, only in a future qualified semantics generation |
| [S-RANK](0014-isc-identity-sequence-amendment.md) | APPROVED architecture decision | s is physical slot; V_a(s) counts original kind-2 votes. Never collapse votes or relabel old sequences |
| [W1](0014-isc-finalization-wal-capsule-v1.md) | APPROVED local byte/storage contract | DRW1 kind 3 and four section layouts; opaque storage qualification is distinct from payload/authentication/production authority |
| P-EXPLICIT | SELECTED_FOR_SPECIFICATION | Direct parent in future B/C, supplementing config binding; exact v2 bytes/hash proposal not promoted to approved |
| SIG-ISC-ED25519-v1 | SELECTED_FOR_SPECIFICATION | Exact domain-separated Vote signature and independent epoch registry; concrete V/G/K/R encoding/build qualification remains open |
| ISC-EVIDENCE-BUDGET-v1 | SELECTED_FOR_SPECIFICATION | Inline retained inventory with pre-admission event/byte bounds; proposed numeric E values and model guards remain draft |
| [Consolidated amendment](0014-isc-production-contract-amendment-v1.md) | DRAFT_EXACT_DETAILS | One combined production proposal, not three new proof layers |
| [Producer Integration](0014-isc-producer-integration-v1.md) | BLOCKED | No implementation authority; requires approved exact closure and exact compatible merged Formal GO |

I-B alone does not change the existing C encoding; the separate consolidated
draft proposes explicit parent/new C bytes. Likewise S-RANK alone does not add
admission counters; the budget proposal does. Earlier unchanged-payload/Init/Next
statements are scoped to those individual decisions, not a claim that the combined
draft is refinement-only. The consolidated proposal is SEMANTIC_CHANGE.

The new sequential assignment authorizes this documentary task and separately
assigned quarantined reference/formal lanes, not production integration. Nothing
here closes R2.3/R3 or replaces their existing STOP. Graph reviewer gates are not
automatically independent technical attestations for Formal GO.

## Non-circular dependency order

The shorthand order is:

```text
source profile → σ → E/e → R/r → V/v → M/sig/G/g → C/c/W1/evidence
```

An arrow is a prerequisite for construction or admission; it does not add a field
to the destination encoding. In particular V has no r/e/g field, and C contains
the original signer IDs and body, not G or its own c.

The complete dependency graph has the following additional branches:

| Node | Prerequisites | Result and boundary |
| --- | --- | --- |
| source profile | Approved source rules and still-labelled draft specifications | Symbolic σ parameter, codec/domain rules, budget constants, model/proof obligations. No deployment bytes/IDs |
| semantic artifacts | source profile | Complete non-mutant TLA, mandatory Lean and public trace-schema source set; future work, not produced here |
| σ | semantic artifacts + independently selected formal_semantics_version | Existing compatibility derivation below, not a new algorithm. No value assigned here |
| E/e | σ + fixed source budget constants | Instantiate formal_semantics_id, encode J(E), compute e. No own e member |
| K/key_id | Independent bootstrap public-key provisioning + source key codec | Encode key descriptor; no σ/r/v/g or own key_id member |
| R/r | σ + E/e + K/key_id + independently trusted epoch/validator/role/quorum/origin | Encode J(R), compute r. R does not authenticate or provision itself |
| B/b | σ + admitted round/config/parent and frozen ordered original inputs + source B/root codec | Compute root, PB and b; no signatures or C/c input |
| V/v | σ + B/b + independent validator/context/original slot; validate against R | Encode exact signable V, then v. No signature_id, G/g or certificate hash in V |
| M | R/r + K/key_id + V | Exact domain-separated preimage, not a digest/signature identifier |
| sig | M + independently provisioned signing key | Ed25519 result after durable original vote intent |
| G/g | R/r + K/key_id + V + sig | Encode exact detached artifact, then g; no g member in G |
| C/c | B + original matching authenticated delivered V/G signer set | Canonical witness for that cut. Different C for B remain distinct artifacts, not different consensus decisions |
| W1 | Verified original source prefix, C/c, b, original V/G evidence, P0/P1 and original receipt/effects | Four approved sections; preserve original slots, multiplicity, lineage and hashes |
| evidence/report | Source/σ pins + generated objects/traces/W1/results | Binds completed outputs downstream. Report content address remains outside its own payload |

Thus a registry/semantics change propagates forward to new objects and evidence.
No output is fed back to compute the source version that its own bytes embed.
An unbound snapshot or supplied signature/key ID cannot choose any upstream pin.

## Exact σ input boundary

Reuse the existing definition in [formal/schemas/README.md](../../formal/schemas/README.md)
and `discover_semantic_artifacts` / `derive_formal_semantics_id` in
[formal_artifacts.py](../../formal/scripts/formal_artifacts.py). Its membership is:

1. All non-mutant `formal/tla/**/*.tla` modules.
2. `formal/proofs/DeltaReduce.lean` and all `formal/proofs/DeltaReduce/**/*.lean`.
3. `formal/schemas/formal-trace.schema.json`.

For these sources only, canonicalize CRLF/lone CR to LF, hash each source, and
sort entries by `(path,kind)`. Existing canonical JSON encodes:

```text
{"artifacts": entries,
 "domain": "deltareduce.formal-semantics.v1",
 "formal_semantics_version": independently_selected_version}
σ = "sha256:" + lowercase_hex(SHA256(canonical_json(payload)))
```

The displayed object is explanatory notation, not literal whitespace-bearing
hash input. No version or digest is selected/computed by this task.

The source profile means the rules represented by that source set and separately
bound normative documents. It does **not** add ADRs, E/R manifests, a build digest
or a deployment directory to `artifacts`. Full report/source evidence separately
pins documents, codecs, library/build qualification and generated vectors. A
document-only change must not be described as a new qualified semantics hash.

**Excluded from σ input, including indirect inclusion inside a hashed source:**
concrete deployment E/e, R/r, K/key_id, B/b, V/v, M, signatures, G/g, C/c, W1 bytes,
receipt/effects, source snapshots/history, deployment build manifests, generated
vectors and resulting reports. No generated deployment ID may be pasted back as
a required constant/expected result into the semantic source closure to define
the σ that same deployment object embeds. A symbolic or universally quantified
semantics parameter and the source rules/constants for constructing/checking these
objects are permitted; a literal newly derived own σ is not.

This is not permission to omit an existing mandatory source from discovery, mask
bytes before hashing, or change the derivation. No existing source is rewritten.
If a future theorem/schema demands its newly derived σ/e/r as a literal in this
closure, that dependency is a STOP, not an iterative fixed-point calculation.
Generated deployment-specific schemas/manifests belong downstream and require
separate report bindings; they cannot silently replace the public trace schema.

Independent bootstrap is not a content-derived trust root. A trusted epoch/key
set can select/verify R after σ and E exist; the snapshot cannot supply its own
bootstrap authority. A qualified build can bind σ and exact E/R as downstream
release artifacts. The source-stage producer/signature profile rules must not
derive σ from those final manifests. No new bootstrap field or trust protocol is
introduced by this ordering.

## Construction and qualification boundary

1. Freeze source rules and close the required model/proof/compatibility inputs.
   Draft details remain draft until separately approved. Do not derive a new σ now.
2. At the future qualification gate, derive σ from the complete source closure
   using the existing algorithm; qualifying evidence is a separate requirement.
3. With independent provisioning, instantiate E, K and R, then construct admitted
   B and V for a specific round/validator/slot. Neither fixture IDs nor graph task
   IDs are deployment authority.
4. Preserve FR-003: append original kind-2 V intent → barrier → sign M → retain
   exact G/source association → barrier → expose. G adds no vote or WAL slot.
5. Validate every original delivered V/G and source event, form C using unique
   original signers, size-check exact W1/P0/P1/output before append, then preserve
   the approved append/barrier/commit/expose and replay semantics.
6. Bind output evidence to exact source and deployment pins. Hashes authenticate
   bytes, not quorum/producer legality, trusted provenance or successful fsync.

## Finite open obligations and prohibitions

The following are existing integration obligations, not new R2 residuals or proof
layers: exact draft approval; feature-000 parent/context and budget/liveness
qualification; concrete key/signature/source verification; original vote-intent/G
durability and recovery association; full-retained-inventory and P0/P1/output
sufficiency; mixed-WAL rank/refinement; exact compatible merged Formal GO and
separately authorized integration. The checklist records each as OPEN/BLOCKED,
without claiming that documentary DAG validation discharges it.

No production C++/ABI/Java/sidecar, schema/TLA/Lean/fixture/build edits; no guard
removal, new semantics value, old-object migration/relabel or lineage pruning.
Quarantined reference conformance is not production, full Formal GO, or an
independent attestation. Conditional integration estimate remains 70–116 active
hours with its existing exclusions; it is not an approved execution budget.

Only this assigned docs task is complete when the checklist, exact commit/push,
scope diff and sprint/source ancestry checks verify. Official graph handoff is
required before taking any next identity; no automatic production join or merge.
