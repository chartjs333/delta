# R2.3: original seed evidence verification boundary

T047/T053 / ISC-S16-D01, 10 October 2026. **NEED_DECISION;
R2.3 OPEN; Formal NO_GO.** No seed protocol or verifier is selected here.

The EC companion computation/storage conjunct is qualified separately in
`ec-durable-binding-checkpoint.md`. Continuing the complete producing-prefix
join reaches an earlier prerequisite: the original seed transcript must be
derived from its selected evidence, not merely parsed or included in P0.

## Exact missing obligation

For an already durably finalized original ISC body b, the available selected
source contracts do not determine an executable check of

```text
original seed_profile_id + original accepted share/beacon bytes
 + independent existing authority + original ISC/epoch/round/cut
 -> verified original seed_id and complete original transcript
```

The missing material is the concrete profile/algorithm, authenticated share or
beacon preimages and verifier/key binding, and the exact derivation/selection
rule for the original seed. No accepted contract was found that supplies these
facts for the approved source generation. A named adapter port and opaque IDs
do not implement that contract. We do not infer authority from a signer list,
three later EC signatures, T's faithful custody, or a successful public state.

This is required by the existing 008 FR-007 and Profile v1's full native origin
check, not a new DoD or a request to authorize ordinary R2.3 engineering.
The claim blocked is independent legal origin of the seed prerequisite in the
full initial/recovered state. It is not a demand to formally prove Ed25519 or
randomness security from first principles.

## Immutable evidence and applicability

All abbreviations below expand to exact commit/path/raw-SHA256 references and
copies in `evidence/profile-seed-source-boundary/audit.json`. The reproducible
corpus inventory includes selected N/P/A/EC and worker/coordinator roots, source
trees and hit locations. It is an applicability audit of this available corpus,
not a theorem that an unsupplied external selected profile cannot exist.

| Existing source | What it establishes; why it does not close this edge |
|---|---|
| N `60c692f6…`: 008 `spec.md` FR-006/007; `plan.md` seed-source adapter; `runtime-profile.md` Seed and timers | Require post-ISC generation, profile/epoch binding and verified accepted evidence. They name no concrete share encoding, verification algorithm, key selection or seed derivation |
| N: `certificates/contracts.hpp`, `SeedTranscript`; `contracts.cpp`, its canonical serializer | Preserve full Context, ISC ID, `seed_id`, `seed_profile_id`, ordered `share_ids`. They check ID grammar/order and canonical bytes, not share contents or their cryptographic meaning |
| N: `certificates/verifier.cpp`, `ChainVerifier::verify_seed` | Validates Context and exact supplied ISC parent, then computes transcript content ID. It receives no original share bytes, seed verifier/profile implementation or independent seed keys |
| N: `robust/plan.cpp`, `build_plan` and `seed_number` | Deterministically consume caller-supplied seed ID for bucketing. They do not produce or authenticate that seed |
| A `bb9fce95…`: ADR0015 §§1,3,5 | SIG-NON-ISC dispatch covers eight validator vote kinds and explicitly excludes arbitrary worker/storage/beacon authentication. The seed evidence edge remains separate; substituting validator NSG1 is not authorized |
| EC `f1a9963e…`: selected EC-SOURCE-STEP-v1 §§3–4 | Requires backward origin of seed/norm and explicitly does not generate either. Its successful EC transition cannot discharge its own seed premise |
| W `47d75279…`: `NativeSeedTranscript`, `ProfileLineage` | Exact typed/canonical/context/parent joins. Their comments and statements explicitly leave primitive seed/share authority outside these checks |
| W: `NativeSeedTranscriptVectors.alternateSeedStillShapeValid` | Existing kernel countercheck: changing primitive seed to another well-spelled ID still satisfies shape. This is a shape/authority distinction, not a production attack |
| W: production TLA `GenerateSeed` / `SeedAfterInputFreeze` | Select the abstract `ExpectedSeedValue`, after one finalized ISC and before any conflicting seed. This is the target abstraction, not an independent native evidence verifier |
| N: 008 native/refinement evidence and task map | Qualify structural parent/order, full-chain fixture and seed-parent mutant; `semantic_completeness_claimed=false`. A checked task label is not a missing beacon verification implementation |

The exact source search includes native C++ core/runtime, C ABI and Java main
sources, existing 003/008 contracts/evidence, ADRs and selected scope/handoff
documents. Java's seed tag routes opaque certificate bytes to native checks;
P2P seed/repair and synthetic signing-key seeds have different meanings.
No external deployment or new native execution was performed for this audit.

## Minimal distinction, without inventing a valid history

Keep the same valid typed Context, finalized ISC reference, profile ID and
nonempty ordered share-ID list. Replace only the primitive `seed_id` with a
different valid content ID. The existing shape rule still accepts; canonical
bytes and transcript ID change. Neither result says which seed is derived from
the original shares. `verify_seed` has no additional evidence input to decide
that question. The existing countercheck demonstrates precisely this limited
fact. It does not assert that both transcripts are production-reachable or that
a complete authenticated Profile snapshot containing either is lawful.

Rejecting all seed events would make the successful EC/APC/APPLY source domain
vacuous or narrower. Equating every seed to the public fixture's ExpectedSeedValue
would use the refinement target as the native origin checker. Adding a trusted
`seed_valid` callback would assume the missing result. None is an acceptable fix.

## Why scope 18 does not resolve this automatically

The delegated class permits minimal deterministic persistence and source/history
association using **already approved authority**. It covers the EC companion
and ordinary subsequent byte/layout choices. It does not choose who vouches
for entropy/share truth, a new beacon/share signing protocol, or a weakened
seed claim. The selected non-ISC contract expressly leaves that authority out.
Even a proposed reuse of the existing validator keys would need a separately
selected seed signing/derivation protocol; NSG1 cannot be extended implicitly.

No new runtime/WAL/certificate identity or protocol rule has been introduced.
The immutable seed, QC and downstream identities remain unchanged. R1/R2.1/R2.2
remain CLOSED for their original domains. The three frozen R2.3 obligations
remain; this is the precise unresolved original seed edge within the first,
which prevents completing the other two for the full admitted history.

## Requested decision through the existing graph/UI

First, an already selected immutable seed profile/verifier and original evidence
may be supplied with exact applicability references. That would be checked
without inventing a new authority. If none exists, a bounded specification pass
must make the missing seed evidence/authority/derivation contract reviewable;
selection of its semantics requires an explicit human decision. This document
does not pick a beacon, threshold scheme, fallback, deterministic fake-random
seed, or weaker conditional claim. General R2.3 authorization remains valid.

Dependent source closure and the named recovery theorem stop at this boundary.
Ordinary result/two-review gates must run; process reviews by the same executor
are not independent Formal GO attestations. Neither a routing approval nor
scope ACK proves seed origin or closes R2.3.
