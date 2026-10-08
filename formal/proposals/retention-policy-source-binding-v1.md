# Retention Policy Source Binding v1

**PROPOSED — one exact contract for approval; no implementation authority.**
8 October 2026. T047/T053, ISC-S16-D01. **R2.3 OPEN / Formal NO_GO.**

The proposed binding makes the original retention declaration an exact,
resolvable part of the already authenticated RoundConfig. It uses the existing
independent provisioning and configuration authority. It introduces neither a
retention duration nor a new storage truth assumption. Approval must expressly
accept the new configuration field and the limited, byte-identity claim below.

## 1. Authority and repeated source check

Human decision `scope-decision-b1b75af55b0e2518569446a9c997a59f` applied scope 12
to the existing assignment `13069d7e-a148-475a-bd49-9885bf2f283d`. It permits
one specification-only proposed binding if an applicable exact contract still
cannot be found, then STOP and a new Pending decision. Role 2753's exact ACK
`scope-ack-cd92c2992ea62c8b263db8c726f9e201` is GET-confirmed. This permission
does not approve the following proposal or implementation using it.

Applicable immutable sources are:

| Pin and path | Existing contract reused |
|---|---|
| `60c692f6e391f839829dfc64e93380db54cd507b:specs/003-bft-round-state-machine/spec.md`, US1, FR-001/014 | Independently checked, finalized RoundConfig selects availability policy; storage statements bind exact leaf IDs, lengths and retention epoch |
| `26eb02d0632435c9aa0d8ef44eb496b6fa73dd13:docs/adr/0013-snapshot-provenance-profile-v1.md`, sections 2–5 | Independent initial/config/schema/producer pins, existing validator authority, faithful original source custody, finite bundle and trusted floor |
| `1438fa3d78ec99291475cf4660fd8c190ac01bb3:docs/adr/0016-storage-availability-source-binding-v1.md`, sections 3–5 | Initial storage registry binding; RoundConfig storage policy; canonical J/ID; A/D sign both round_config_id and retention_epoch_id |
| `90561a97de7f41f409bf22065ad6cdc9b3932458:docs/adr/0018-authenticated-availability-contract-v1.md`, section 4 item 5 | Resolve the original retention policy; authenticate the obligation asserted, without inferring its physical fulfillment or a duration |
| `411f383122f2a3c34e7183810b007c5864ef30ed:formal/proposals/storage-retention-source-boundary.md` and its evidence JSON | Exact missing resolution and bounded source audit; no executable counterexample or impossibility claim |

The scope-12 recheck confirms those same pinned requirements and the published
storage component. The current remote branch tips and reachable history supply
no newly applicable approved policy resolver; the new operator decision supplies
specification authority, not an external policy artifact. The recheck receipt is
`evidence/storage-source-v1/retention-binding-recheck.json`. This finding is
limited to the recorded available corpus, not every possible external source.

## 2. One selected mechanism

Add exactly one field to the **future generation** of S's
`RoundConfig.availability_policy.storage_binding`:

```text
storage_binding = {
  retention_epoch_id,
  retention_policy_source,
  storage_epoch_id,
  storage_registry_id,
  threshold
}
```

`retention_policy_source` is the embedded closed object R defined below, not a
URL, callback, flag or optional extension. The other four fields keep S's types
and meaning. All enclosing original close/repair/deadline fields remain intact.
R is part of the exact canonical configuration body already authenticated by
the existing RoundConfig vote/QC and referenced by A/D's `round_config_id`.

The provisioned `initial_config_ref`, `schema_set_id`, source/producer and
semantics pins select this future configuration grammar before reading an
import. If the independently provisioned initial configuration itself carries
an availability policy, it uses the same embedded object at that policy's
storage_binding. Later RoundConfigs must pass the **existing** configuration
authority and producing-history checks from that initial state. A snapshot
cannot replace the initial pin, select a codec or self-finalize a RoundConfig.

There is no new global label registry or requirement to enumerate all future
retention epochs at genesis. Selection is contextual to the original accepted
RoundConfig: one exact configuration has one R. A different configuration may
select a different declaration using the existing config consensus rules. The
verifier never resolves a label globally, from a newer configuration, a local
default or the current wall clock. This preserves the existing configuration
authority rather than assigning provisioning or storage signers a new power
to finalize rounds.

Two alternatives are not selected: equality of a bare epoch cannot identify a
declaration; an independent mutable policy registry would introduce another
authority/freshness problem. Directly embedding R requires one configuration
field, no extra certificate, key, signature, consensus action or WAL kind.

## 3. Exact object, bytes and source identity

R has exactly these keys, in canonical ASCII order:

```text
obligation_ref, retention_epoch_id, schema_version, type_name
```

- `schema_version` is exactly `"1.0.0"`.
- `type_name` is exactly `"STORAGE_RETENTION_POLICY_SOURCE"`.
- `retention_epoch_id` retains S's 1–128 `[A-Za-z0-9._:-]` grammar and must
  equal its enclosing storage_binding value and the original A/D values.
- `obligation_ref` has exactly `byte_length` and `sha256`.
  `byte_length` is a positive U64 decimal string, with no sign/leading zero.
  `sha256` is 64 lowercase hexadecimal digits: raw SHA-256 of the complete
  original declaration bytes E, not a Git object ID or a digest of parsed text.

The control object uses S/P's existing J: ASCII strings, keys sorted by ASCII,
no whitespace, BOM, escapes or trailing newline; no numbers/null; reject
unknown/missing/duplicate members before typed construction and require exact
decode/re-encode equality. Object/schema dispatch comes from the independent
pins, never from a source-supplied version claim alone.

```text
e = lowerhex(SHA256(E))
R.obligation_ref = {byte_length = decimal(len(E)), sha256 = e}
r = ID("deltareduce.storage-retention-policy-source.v1", J(R))
ID(d,x) = "sha256:" || lowerhex(SHA256(ASCII(d) || 00 || x))
```

E is the complete original provisioned/config-selected declaration artifact.
Its bytes are preserved without text decoding, newline conversion, decompression,
Unicode normalization, recursive resolution or code execution. A length plus
digest is not a substitute for E. A path/name only locates an untrusted copy;
only checked bytes resolve the reference. An empty/missing artifact supplies
no declaration and rejects. Existing source-specific validity rules for that
original artifact, if any, still apply; this binding waives none of them.

R does not contain r, a RoundConfig ID, initial-config ID or an import manifest
ID. The dependency order is E → R → configuration → original attestation/witness
→ import metadata, with no self-hash cycle. r is a derived provenance object
identity, not a storage signature, validator certificate or new protocol vote.
The enclosing configuration carries R itself, so no new wire reference to r is
needed. The import's existing artifact inventory retains E and its original
source association; it cannot supply a different policy behind the same label.

**What is being selected:** the normative declaration is the exact original E
chosen by the existing configuration authority. This format is a source binding,
not an executable language for temporal retention. It does not synthesize a
promise from `retention_epoch_id`, interpret an arbitrary document as a Boolean
admission oracle, or prove that E has been fulfilled. Deployment supplies genuine
E, just as it supplies genuine configuration/key/source preimages; the draft
does not fabricate a production policy value. If a further claim requires an
expiry evaluator or a new duration rule, that is outside this approval.

## 4. Finite resolution procedure

These are prospective verification obligations, not new code or proved lemmas.

1. Verify the independent Profile-v1 origin, initial configuration, fixed epoch,
   storage registry/key bindings and approved source/schema/producer pins.
   Reconstruct the original configuration authority through the existing native
   history rules. Do not use a public projection or `passes_R2` assumption.
2. Resolve the exact accepted RoundConfig preimage at the original event prefix.
   Verify its existing body ID, votes/QC and context using the original validator
   authority. A later/forked configuration cannot supply an earlier event's R.
   The configured availability policy must match the independent initial rules;
   supplying a syntactically valid R cannot repair an invalid configuration.
3. Strictly decode its storage_binding and R. Match original storage epoch,
   registry, retention epoch and threshold under S. Derive r from these very
   embedded bytes. No lookup by a bare retention label or importer-selected r.
4. Resolve E in the finite retained original source bundle. Check complete byte
   length and raw digest before accepting the reference, and retain its exact
   original source/event association under P. Required evidence must belong to
   the original source, not be fabricated from a later successful projection.
   No remote fetch, text interpreter, network bootstrap or wait loop is used.
5. Authenticate A and D with the existing storage keys and domains. Require the
   exact original `round_config_id` and retention epoch; recompute every original
   per-leaf witness and preserve alternate/duplicate deliveries. The chain
   `independent pins → original valid configuration → R → E`, plus authenticated
   A/D's configuration/epoch, identifies which declaration each signer asserted.
6. Pass that derived source association to the existing O/R2.3 composition.
   Continue all independent commitment, canonical close, data-use, full-state,
   floor/current and replay checks. This local resolution does not make any of
   those checks true or itself establish an admissible snapshot.

At every step, missing/malformed/conflicting input returns rejection with no
successful derived association. The future checker must return the exact
configuration/R/E references and original event association, not accept a
caller-supplied `policy_valid=true`. Initial/incomplete states without an event
requiring a retention declaration do not gain a fictitious AC or a new rejection
solely because there is no such event. Once an actual original statement/AC
requires it, missing R/E is the already required O rejection.

### Bounds and multiplicity

Reuse P's 4 MiB control-document limit, 65,536 artifact refs, 64 GiB total
bytes, and existing source-event/WAL and stricter per-object limits. R's bytes
count in the enclosing configuration's actual serialized length; E counts as
an original artifact. Reuse an already retained identical artifact; do not count
a digest in place of its bytes or delete any delivery/history to fit a budget.
Apply the existing accounting rules to the full final bundle and exact W1/P0/P1/
output representations where applicable. If the approved domain cannot fit,
report that boundary; no smaller label set, artificial policy cap or discarded
lineage is selected here. No universal bound sufficiency has been proved.

## 5. Claims, compatibility and original identities

The proposed local claim is: from an independently authorized original
configuration and actual checked source bytes, derive the unique byte-identical
declaration bound by the original authenticated statement's configuration and
retention epoch (subject to the already named hash/signature assumptions).
P and Q with different bytes yield different R/configuration commitments; the
same label alone cannot substitute one for the other.

The claim neither assumes nor concludes native/public refinement, truthful
remote storage, time remaining, storage honesty, absence of loss, or completion
of a round. It does not override O's physical-fault model, original deadlines,
late-input rules, repair or certified abort. Original AC/ISC/downstream lineage
survives later data loss and policy-retrieval failure. Such failure cannot
rewrite an old certificate or silently remove its ticket from the frozen set.

| Surface | Exact consequence if approved later |
|---|---|
| Trust | Same independent Profile-v1 bootstrap/source custody and existing configuration validator authority. New explicit source field; no observer, CA, key, authority service or stronger storage honesty premise |
| Configuration and signatures | Future canonical RoundConfig body gains embedded R, so its body/hash and actual config vote/QC bytes/IDs change. It is not a backward-compatible optional field in an old closed schema |
| S A/D, ISC and downstream | A/D field sets/domains stay the same, but their actual `round_config_id`, signatures/IDs and resulting ac change when the configuration changes. Ordered ISC tuples/B/b, signer-dependent C/c and dependent QC IDs therefore require future-generation qualification |
| WAL/replay | No new kind, slot, public vote ordinal or signer identity. Original s/V_a(s), receipts, source occurrences and retry identities are preserved; newly generated votes contain their newly qualified original bodies |
| Semantics/evidence | Exact source/configuration identity binding changes; no temporal policy, deadline, physical availability or certificate-quorum rule is added. A future semantics/source/schema generation must qualify this change; no concrete sigma is assigned |
| Legacy | Historical configurations, signatures, QC/WAL and evidence remain under their exact original pins. No retroactive field injection, migrated signature, relabel or claim that old missing-R sources now passed this binding |

An initial-config digest may also change when that configuration contains this
policy; its bootstrap/import IDs then change as prescribed by P. Do not claim
identity equality merely because a high-level label or storage signer is equal.

## 6. Finite work after a separate approval

| Obligation | Acceptance boundary |
|---|---|
| Source/schema dispatch | One closed R/obligation_ref shape and the one required storage_binding field; independent schema/producer pin selects it. No optional fallback to bare-epoch equality |
| Canonical bytes/resolution | Exact J/raw-E length/hash and r derivation; malformed members/lengths/hash/source replacement reject; diagnostic byte checks are not production evidence |
| Original authority | Resolve original config from independent initial state and its real validator/source chain, not a supplied Context. Old/foreign/forked config and hindsight policy substitution reject |
| S/O composition | Original A/D context resolves that config/R/E; preserve per-leaf signers and every original event. Data-use/fault/current obligations remain separate and mandatory |
| Formal composition | Future configuration representation/source-validity guards account for R/E. Bind the derived association into the existing whole-source R2.3 relation; reuse R2.1/R2.2 for original domains. No new TLA action or separate temporal retention model is proposed; do not claim old Init/Next/type evidence qualifies the new field |
| Qualification | Requalify affected schema/source/model/refinement/mutant/review gates with same-label/different-E, wrong original configuration, missing preimage, initial/incomplete and retained-loss lineage cases. No waiver, hidden axiom, circular refinement premise or future gate reported as passed |

These obligations are confined to the one missing source binding. They are not
a new decomposition of all R2.3 or authority to start full R3. Production runtime,
recovery deployment and guard removal remain behind exact compatible merged GO.

## 7. Decision and STOP

Approve/reject/edit this exact source-only binding, including the mandatory new
future RoundConfig field, literal-original-declaration claim, finite resolution
and compatibility consequences. Approval would settle the contract; it would
not certify a deployment policy, prove R2.3, or retroactively qualify old objects.
Any permission to implement/prove it must be explicit in the resulting scope.

**STOP after this specification and its new Pending decision.** No schema,
checker, C++/ABI/Java/sidecar, Lean/TLA proof/model or runtime implementation was
performed. The current assignment remains open. Normal result/reviewer gates
remain required; the documentary recheck is not an independent attestation.
