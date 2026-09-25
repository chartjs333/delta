# Complete tagged public state and first-vote extraction in Lean

T009/T011/T012/T044/T048/T049/T053/T054/T056/T057/T060; amendment 0001.
This is a mandatory-project representation/extraction sublayer. It does not
discharge `nativeArithmeticRecoveryRefines`, grant native authority or change
the production TLA transition relation. Formal status remains NO_GO.

## Complete representation and canonical preimage

`PublicState.lean` defines mutually inductive finite values: Boolean, integer,
printable ASCII string, configured model value, set and finite function. Records
and sequences retain their TLA function representation. There is no null,
unknown-value, abbreviated fingerprint or omitted-field constructor. Canonical
validation checks set and function-domain ordering/uniqueness by encoded bytes;
model values remain distinct from same-spelled strings. The input is typed:
this is not a proof of a byte parser, allocation limits or stack safety.
The byte comparator uses Boolean lexicographic traversal, with general proofs
equating it to strict list ordering and equating the ordered-list check to
pairwise strict ordering. The computation does not change the canonical order.

The checked state requires all 64 names, once each, in canonical order. General
proofs derive field presence, unique lookup, exact original rows and rejection
of missing/extra/reordered names. A changed observed field changes the retained
rows. These statements do not assert general encoding injectivity or SHA
collision resistance. Those remain separate obligations.

The full document encoder retains every field and binds the profile, independently
supplied expected semantic/configuration/module identity and complete values.
The loader compares the actual supplied document bytes, validates canonical
values, depth/node/byte limits and the exact domain-separated hash preimage.
Successful loading produces proofs of those checks. Its SHA function and expected
identity/model vocabulary are explicit parameters, not proof of authentic source
selection. Resource checks apply to typed evidence (4 MiB, 250000 nodes, depth64),
not production native admission. Production TypeOK and Init/Next are not proved
by passing this representation loader.
`loadProvided` proves that an explicitly constructed, fully checked loaded object
is returned by the same executable loader. The examples establish its actual
canonicality, bounds, full document equations and hash lookup facts individually;
no acceptance flag or assumed expected body replaces a check. This modular proof
avoids normalizing a large dependent equality proof inside the entire loader.

## Checked extraction

The executable frame extractor reads current checkpoint, view, logical time,
actor sequence and the entire durable envelope set. It validates ACTIVE,
empty abort requests, live actor and READY, and derives the actor's sequence from
all its durable votes, including non-arithmetic kinds. Envelopes must have the
exact four fields; no Boolean arithmetic acceptance or expected frame is supplied.

The first-vote extractor derives the one new envelope from complete before/after
durable sets, preserves all old votes, checks the next all-vote sequence, actor,
fresh kind/context, exact proposed body and body parent against current. PARAMETER
context comes from body domain/shard; APPLY context comes from its aggregate.
General proofs establish these extraction facts. `projectFirst` composes both
complete loaders and this extractor under one source/configuration identity.

`IdentityMap` is a separately supplied *assumption boundary*, mapping abstract
actor/checkpoint/height/epoch values to native identifiers. The optional native
frame binder checks those resolved identifiers against original Anchor and
VoteMetadata, plus view, time, deadline and recovered readiness. It does not
authenticate that map or check full native action/role/context/body/graph/QC
bindings. In particular, a finite symbol map is not native content identity.
No native preparation, receipt, hash or journal evidence is manufactured here.

The extraction checker deliberately does **not** validate every after-state
effect, parent certificates, arithmetic, delivery or production Next. A changed
unrelated field can pass extraction while violating Next. It must not be used
alone as admission. Existing complete-state TLC replay and native arithmetic
proofs remain separate until joined by a substantive general relation.
A dedicated kernel countercheck inserts the nonempty message set from an earlier
complete source state while preserving a successful extraction. The generator
checks that this actually changes the selected after-state, whose original
message set is empty. This is evidence of the extraction boundary, not an
allowed production action or a newly executed TLC counterexample.

## Source-linked examples without a semantic self-hash cycle

The generator independently validates all nine completed first-vote source pairs
through the existing pinned fixture registry before emitting output. It retains
18 complete prior/next states, original per-actor arithmetic sequences 5/6/8,
all intervening vote contents and every model variable. It generates typed value
trees and separately assembled literal byte fragments; fragments share repeated
values without omitting any bytes. SHA samples are Python-computed exact hashes
of the complete example preimages, not a general Lean SHA implementation.
The finite lookup first checks the sample length, then still compares every byte.
The sample lengths are distinct for this fixed fixture; this is a test adapter,
not a general decoding or hashing implementation.
The identity header is assembled from checked literal module/configuration/hash
entries and JSON delimiters. Its binary congruence helper is proved by equality
elimination in the imported foundation; no unavailable library lemma or trusted
byte-equality oracle is used.
Each interned value has its own kernel-checked encoding equation, composed into
complete document equations by rewriting. This preserves every literal byte
while avoiding repeated expansion of large nested certificate trees. Generated
canonicality, depth and node-count facts are likewise proved per interned value
and composed into the six fully loaded state observations; all guards remain
present in the executable loader. These auxiliary facts are not separate
protocol-proof obligations or evidence of production native execution. Ordering
proofs remove only identical byte prefixes using a general inductive lemma,
then compare the differing suffixes. The generator's choice of shared fragments
is checked by Lean rewriting, not trusted as an ordering answer. Byte lengths
are also proved from component lengths and list concatenation,
then composed into whole-document resource bounds. The loader still compares
the complete bytes; a length match never substitutes for byte identity.
Generated fixture definitions are transparent `noncomputable` proof data to
avoid producing native code for large constant documents. The general checker
functions in `PublicState.lean` remain executable. Concrete byte equalities use
kernel definitional reduction against independently emitted literal fragments;
other examples use `decide +kernel`. No native-decide oracle or additional axiom
is introduced. Sequential elaboration limits simultaneous resource use.
The generated proof chain separates shared values (`PublicStateValues.lean`),
complete documents (`PublicStateDocuments.lean`), checked loading
(`PublicStateLoads.lean`) and extraction cases (`PublicStateVectors.lean`).
This separates elaboration caches without altering the cases or granting an
additional trust premise. Every module is built and audited.

Because mandatory Lean sources participate in the semantic ID, the Lean byte
examples use an explicitly **synthetic zero semantic ID**. Actual production TLA
module/config hashes and complete variable values remain pinned. This avoids
embedding a file's own semantic hash in itself. The vector manifest separately
binds the actual current source vectors. These encoding examples are not claims
of newly authenticated production observations. The general loader is parameterized
over the externally supplied expected semantic identity.

Positive kernel cases cover complete variable encodings, all nine first-vote
sequences, three complete load/project pairs and original native frame metadata.
Negative cases cover old snapshot version, changed source/config/hash/bytes,
missing/duplicate/reordered variables, duplicate sets, unsupported model/text,
false sequence, readiness/aliveness/phase, stale parent, wrong actor, no append
and native metadata mapping/clock. Rehashed structural negatives deliberately
use a collision-full synthetic SHA adapter, so rejection cannot depend merely
on retaining an old digest. This is explicitly not cryptographic evidence.

Seven Python tests check byte regeneration, actual TLA/Lean field inventory,
absence of a semantic self-hash, full case/sequence scope, rehashed clock/current/
phase substitutions before output and inclusion of all named functions/theorems
in the axiom audit. These are tooling/kernel cases, not production TLA mutants
or new native executions.

## Reproduce and remaining boundary

```text
python formal/scripts/generate_public_state_lean.py
lake --no-cache build DeltaReduce
lake --no-cache env lean DeltaReduce/PublicState.lean
lake --no-cache env lean DeltaReduce/AxiomAudit.lean
python -m unittest discover -s formal/tests -p test_public_state_lean.py -v
```

The pending general relation must connect the complete state to checked native
preparation/whole bodies and real public effect changes, then global send/QC/
current advance and reachable recovery. Unknown/incomplete durability stays an
incomplete observation; this type cannot be filled with guessed values to claim
a recovered state. Actual authenticated presence/absence, original records and
fail-closed corrupt/ambiguous scans remain mandatory.

Concrete bounded decoder/hash/exporter/WAL/admission, arbitrary initial states,
availability/failures/repair, contract freeze, clean offline reproduction and
independent review remain open. Self-review is not independent attestation.
