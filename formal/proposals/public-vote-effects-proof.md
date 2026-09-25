# Complete first PARAMETER/APPLY vote effects

T009/T011/T012/T044/T048/T049/T053/T054/T056/T057/T060; amendment 0001.
Candidate proof sublayer, **not native authority or full recovery refinement**.

`PublicVoteEffects.lean` reads the actual preceding state's durable/volatile
envelopes, selected phase-vote set and actor-sequence function. It constructs
the next sequence from that function, inserts the exact extracted envelope
into both envelope sets, inserts the exact actor/body record into the selected
phase-vote set, and preserves the other sixty fields. The executable checker
compares the complete after-state against this computed state. Expected rows,
result equality, sequence and an admission flag are not caller arguments.

General proofs establish exact insertion membership (no missing or invented
members), domain/order preservation by function update, the selected sequence
increment, preservation of every other actor's sequence, and the unchanged
field rule for any field outside the four assignments. Message exposure,
delivery and current advancement cannot occur as a side effect of these vote
steps. The original extraction-layer message mutation now rejects by the
general theorem. The old countercheck remains intact: extraction alone is
still insufficient.

The `project` function composes both existing complete-state loaders with this
checker. It retains exact complete preimages and source/configuration identity.
Raw `check` consumes complete typed rows; canonicality/ordering/resource and
root checks belong to the composed loaders. Insertion orders by the existing
canonical byte comparator and handles structural duplicates. It does not prove
encoding injectivity; a collision between distinct encodings cannot pass the
loader's strict ordered-set check. No cryptographic or authentication assumption
is silently supplied by the component helper proofs.

The source-linked calculations reuse the prior eighteen complete states and
their component byte/order proofs. They verify all nine original first votes
and three complete loaded state pairs, retaining sequences 5/6/8. Large byte
comparisons use the already checked ordering lemmas, and projection composes
checked function results without reducing a whole large input again. The
generator validates the independently pinned synthetic source correspondence
and prior source-vector identity before writing. Reproduction is byte-exact;
the finite identity/SHA/zero-semantic example profile is unchanged. These are
kernel-checked examples, not newly executed native traces or production mutants.

A separate syntactic inventory test expands actual production TLA variable
groups: the two named vote actions each assign four fields and preserve sixty,
covering all 64 exactly once. Omitted messages or substituted assignments fail
that test. This is source correspondence, not a Lean proof of TLA semantics.

## Limits and next binding

This proves the complete **effect footprint** for the checked honest first-vote
scope. It does not establish all admission guards: configured enable flags,
committee membership/bounds, full ValidParameterResultBody/ValidApplyBody,
certificate/phase/QC support or MaxDurableSequence. Existing extraction requires
fresh actor/kind/context and ACTIVE/READY; it is not the adversarial branch of
the production transition relation. Whole arithmetic/native graph/metadata and
physical pre-WAL admission are still separate relations. The complete after-state
is checked; arbitrary canonical states are not thereby shown reachable from Init.

`nativeArithmeticRecoveryRefines` remains absent. The current next step is to
join these complete before/after effects with independently anchored native
arithmetic preparation and the checked reachable journal, then actual phase,
send/delivery/QC/current and crash/unknown recovery. Unknown/incomplete durability
must retain incomplete observations; no full state or absence is inferred from
a missing response. Concrete bounded decoder/hash/exporter/WAL, admission,
arbitrary initial snapshots/availability/failures/repair, contract freeze,
offline reproduction and independent review remain required for Formal GO.

The user's Docker/synthetic-participant acceptance applies to a separately
labeled SIMULATED_LOCAL profile. It changes neither these proof obligations nor
the meaning of real WAN, independent custody or an original qualifying GO.

## Reproduce

Run the pinned Lean project build, fresh `PublicVoteEffects.lean` kernel check
and `AxiomAudit.lean`, then `check_lean_evidence.py` (expected NO_GO: 44/45).
Run `generate_public_vote_effects.py` after the existing state generators;
the generated calculations must reproduce exactly. Run formal tooling/oracle
tests, refinement fixtures and syntactic consistency on the same frozen source.
Machine-readable evidence is `formal/proposals/evidence/public-vote-effects.json`.
