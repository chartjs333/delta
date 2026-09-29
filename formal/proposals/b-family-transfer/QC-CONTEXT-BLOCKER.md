# R2.3 architectural checkpoint: parent QC versus parent body

Tasks T044/T047/T053–T057. **R2 OPEN; implementation STOP.** R2.1 and R2.2
remain user-accepted CLOSED. Frozen DoD R1–R7 is unchanged. R3 is not started.
This is the existing certificate/context/state part of R2.3, not a new gate.

## Minimal obstruction

Use one ISC body B, one round/height/view/epoch, four validators and quorum 3.
All four validators sign B once. The two valid signer subsets {1,2,3} and
{1,2,4} form certificates Q1 and Q2 with the same exact voted body. Their native
content IDs differ because certificate canonical bytes include the signers.
No validator signs conflicting ISC bodies and no extra identity is created.

Retain both original certificates in one immutable native snapshot. Two EC
proposals have the same eligibility decisions; each refers to its own exact
ISC QC, seed transcript and norm evidence. The seed value/profile/shares and
norm values are unchanged; their parent-QC references and derived IDs differ.
Native `vote_context_id(eligibility, ..., input_set_certificate_id)` therefore
gives two different contexts. Both proposals, the complete unchanged policy,
and both votes by validator-1 pass the original native checks. Its original
local journal has ISC at sequence 1, then EC at sequences 2 and 3.

The public ISC body is computed from round/configuration/close-policy/entries.
It does not contain quorum signers or the native QC content ID. Consistent
primitive metadata for the identical original ISC body therefore gives the
same public B for Q1 and Q2. Public `VoteEC` uses `body.isc` as the vote context.
There are only two cases for the projected EC bodies E1 and E2:

| Projection | Unavoidable failure for the same honest validator |
|---|---|
| E1 differs from E2 | Both have `.isc = B`; `CertificateVoteUniqueness` permits at most one such body and `HasConflictingECVote` disables the second vote. |
| E1 equals E2 | The public EC records and envelopes are equal. Sets retain one EC vote; the original ISC + two EC journal entries project to only two public durable votes. Keeping original logical sequence 3 violates `DurableSequenceExact`; changing it loses an original record/sequence. `vote ∉ ecVotes` also disables the second vote. |

This is a static obstruction to retaining the complete journal and the existing
public invariants. It is not a new transition/recovery proof. The two-case
argument does not depend on choosing distinct seed/norm aliases. Inventing a
QC-specific ISC body, another actor/round, or a coordinate-level protocol object
changes original body/context identity and is excluded by the frozen contract.
Erasing either certificate/vote is not an exact full-state projection.

## Exact existing sources and predicates

Native source is the already used PR50 pin
`60c692f6e391f839829dfc64e93380db54cd507b`, extracted as exact Git blobs:

- `delta-core-cpp/src/certificates/contracts.cpp`: ISC encoding/content ID
  includes `signer_ids`; `project_input_set_vote_body` in `consensus.cpp`
  removes QC-only threshold/signers from the voted body.
- `delta-core-cpp/src/certificates/vote_admission.cpp`:
  `validate_typed_snapshot` accepts each ordered finalized ISC QC with its exact
  valid quorum; it has no same-body/unique-QC restriction. EC typed parents must
  refer to the exact original QC. `validate_vote_admission_policy` accepts both
  distinct candidate contexts. `validate_vote_admission` accepts both votes.
- `delta-core-cpp/src/consensus.cpp`: `vote_context_id` for EC uses the exact
  parent QC ID. `VoteJournal::record` keys uniqueness by validator/epoch/context.
- `delta-runtime-cpp/src/runtime.cpp`: the existing record-vote path uses that
  journal and admission check. This source was read and pinned; **this diagnostic
  does not execute a filesystem WAL, runtime recovery or network delivery**.

Unchanged public sources:

- `formal/tla/DeltaReduceCertificates.tla`: `VoteEC`,
  `HasConflictingECVote`, `CertificateVoteUniqueness`; `FinalizeISC` also permits
  only the first finalized body for a round rather than adding arbitrary new
  signer variants as new finalized events.
- `formal/tla/DeltaReduceQuorums.tla`: `CanPersistVoteEnvelope` and
  `PersistVoteEnvelopeChanges` allocate a sequence only for a fresh envelope.
- `formal/tla/DeltaReduceFailures.tla`: `DurableSequenceExact` is the exact
  per-validator cardinality of the complete durable-vote set.
- `formal/proofs/DeltaReduce/PublicPlanningBody.lean`:
  `loadIscBody` / `IscBody.value` derive the body from original `bodyId`/body
  and shared metadata; `EcBody.vote` uses that public parent body as context.
  `PublicAuthority.iscValue` has no QC/signers discriminator.
- Frozen `candidate-contract.md`: R2 must retain observable
  actor/context/parents/body/certificate/state distinctions, cannot assume a
  whole translated state, and cannot collapse protocol-distinct states by aliases.

The exact missing implication is: **different accepted native EC contexts must
not authorize multiple fresh votes for one original actor and one computed
public ISC-body context**. The existing native predicate does not imply it.
The witness falsifies total coverage of that accepted native snapshot/journal
domain by the current source-bound public representation. Merely adding another
conditional checker would exclude the witness, not close total R2 applicability.

## Reproduction and limits

Run from the candidate repository:

```text
C:/Python312/python.exe -X utf8 formal/proposals/b-family-transfer/check_qc_context.py
```

The checker extracts pinned native blobs, compiles the diagnostic harness with
MSVC `/std:c++20 /EHsc /W4 /WX`, then calls the original policy/admission and
in-memory journal functions. Four original ISC votes supply both signer sets;
the selected actor's original sequence 1 is retained before EC sequences 2/3.
Canonical state/vote bytes, exact IDs, source hashes and compiler identity are
recorded in `formal/proposals/evidence/r2-qc-context/counterexample.json`.
The public obstruction is the source-reviewed exhaustive equality/disequality
argument above, not a claimed full public-checker/TLC run or new Lean theorem.

The test uses synthetic authenticated-artifact/signature assumptions at the
existing formal boundary. It does not execute cryptographic signing, construct
an authenticated exporter, or prove a production-reachable native history.
The native header calls its snapshot a projection of an already-prepared formal
state; treating that comment as a trusted complete-state equality would assume
the very R2 relation being required. A separately established source restriction
excluding the witness could alter the conclusion, but none is established by
the current native validation or the named primitive authentication assumptions.
This is therefore an architectural blocker for the **claimed total mapping of
the accepted native domain**, not a claim of a deployed exploit or a failed
production safety invariant observed over a real network.

No repair is selected or implemented. In particular there is no silent
canonical-QC selection, changed native context/journal key, changed public
Init/Next, changed certificate semantics, or new scope restriction. Resolving
the incompatible context boundary requires a separately authorized decision.

## Residual delta within the same frozen R2.3

Before finding this obstruction, conditional snapshot constructors were added
inside the existing `FamilyRelation.lean`: original certified PARAMETER/ROOT
parents no longer require inventing a local vote, and the sufficient ABORT
component retains nonempty downstream PARAMETER/ROOT lists and exact public
round-collection coverage. Their kernels are checked separately. They remain
conditional components, not a full relation or total initial/incomplete coverage.

The residual is still one unclosed full R2.3 relation over the same three frozen
areas. The concrete context collision above blocks its required total domain;
complete snapshot/environment and initial/incomplete/ABORT integration is not
claimed complete. R2.1/R2.2 are not reopened. Work stops here before eight active
hours. No R3 or automatic continuation is authorized by this checkpoint.
