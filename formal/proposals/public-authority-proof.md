# Conditional native graph to public authority construction

Tasks T044/T048/T049/T053/T057/T060; Feature000 amendment 0001. This layer
constructs the complete public arithmetic authority and its ISC/seed/EC/APC
parent values. It does not establish Formal GO, certificate admission or native
execution. The mandatory recovery theorem remains missing.

`PublicAuthority.lean` takes the actual checked `NativeInputProjection.Projected`
and constructs the complete 23-field arithmetic-input record through
`PublicArithmeticInputs.encodeProjected`. It loads primitive aliases from a
separate `Metadata` source. Keys include the exact authority reference and full
context for configuration/policy, native ISC/EC/APC and plan references, and the
full ISC commitment including every ordered shard/Q artifact reference for each
content alias. No caller supplies an authority, certificate body, expected
arithmetic record or arithmetic approval Boolean. Every lookup has a named
`MetadataTrust` provenance premise; missing metadata rejects.

This premise is substantive and unresolved for production. The native minimal
ISC/EC/APC payloads do not carry the public configuration, seed, norm evidence,
coefficient symbol or close-policy data. It would be incorrect to manufacture
these from a native hash or infer authentication from a matching wrapper.
`Metadata` provides only these primitive names/policy, not whole translated
records. Its authenticity must be established independently. The fixture source
uses synthetic trust. Alias injectivity across arbitrary native graphs,
cryptographic identity and a general exporter are not established here.

The construction retains all ordered native commitments before canonical set
encoding. Their count, original position, ticket alias and full content-source
key have general proofs. Sorting preserves every entry, including duplicates;
the final canonical check rejects duplicates instead of silently deduplicating.
EC/APC membership comes from the bound native eligible list. Missing ticket
aliases, duplicate member aliases or unconfigured names reject. The earlier
scalar representability restrictions remain: configured-but-unprovided tickets,
vector shards and inconsistent per-assignment weights/denominators do not enter
this finite model. These are projection limits, not new native admission rules.

The ISC contains exactly round/config/policy/entries/canonicalRoot. The seed
contains the same ISC and epoch. EC and APC share the same ISC, seed and eligible
set; APC contains the entire constructed EC and the coefficient alias keyed by
both native APC and plan. General lemmas extract the independently resolved
native ISC/EC/APC payloads and their checked reference edges. The ten authority
fields contain those complete parents, all arithmetic inputs, original parent,
schema/profile/apply-profile and schema-tagged model/optimizer values computed
from the checked native vectors. `check` recomputes this whole record, verifies
canonical tagged values and compares the entire candidate.

The two modules include general source/coverage/parent-chain proofs and small
kernel examples. Header/commitment examples reuse the original pinned native
binding and its exact references. Complete authority canonicality and parent
examples are component constructions using the previously pinned input record;
they are not a new combined full-state/native execution or production mutant.
Negative cases change authority, context, deadline, profile kind, plan/APC/EC,
ISC, epoch, Q leaf, leaf order, domain, aliases, metadata availability and policy.
Cross-source Python checks compare authority and parent field inventories with
the production TLA operators; these checks are syntactic, not a Next proof.

Full PARAMETER/APPLY body construction/comparison, actual ticket availability,
configured policy/seed/norm/coefficient validity, quorum/phase checks, complete
prior durable-set correspondence and composed public/native recovery remain
open. This construction does not validate a certificate's signers or delivery,
connect the full public state to a reachable journal, or justify current advance.
No unknown/incomplete durability observation becomes complete through this API.
Existing scan authentication and fail-closed handling remain necessary.

Reproduce with `lake --no-cache build DeltaReduce` from `formal/proofs`, followed
by `lake --no-cache env lean DeltaReduce/PublicAuthority.lean`,
`lake --no-cache env lean DeltaReduce/PublicAuthorityVectors.lean` and the existing
axiom audit. From the repository root, run
`python -m unittest discover -s formal/tests -v`. Final stable-source evidence is
`formal/proposals/evidence/public-authority.json`. Conditional proofs and passing
examples do not waive native bounded decoding/hash/export/WAL/admission,
arbitrary snapshots/failures/repair, contract freeze, clean reproduction,
independent review or the native/benchmark gates.
