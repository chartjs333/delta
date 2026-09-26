# Shared native candidate authority, candidate proposal (T044/T048/T049/T053/T057/T060)

This amendment0001 proposal adds executable candidate checks for all nine original
native vote actions on the SAME original typed snapshot. It does not discharge
`nativeArithmeticRecoveryRefines` or issue formal/local GO.

## Source and computation

Reference native source is commit
`60c692f6e391f839829dfc64e93380db54cd507b`, especially
`delta-core-cpp/src/certificates/vote_admission.cpp`
(validate_candidate_shape/validate_candidate_authority) and `consensus.cpp`
(vote_context_id). No native/runtime source is edited.

`NativeCandidateShape` parses all fifteen positional parent strings, requiring
the precise content-ID/nonempty/empty pattern for each action. The body is a
content ID; context is nonempty; CONFIG body equals the configured parent.
All unused parents must be empty, including last_finalized_certificate for ALL
actions. Domain/shard/reason are nonempty at this source boundary, not silently
strengthened to certificate Label. Policy wire decoding separately enforces text
bounds. A parent checkpoint is only required to be a content ID at this common
authority stage. Its equality to current parent belongs to selected-vote/live
admission, except explicit APPLY/ABORT body guards.

`NativeCandidateAuthority` uses actual find-first lookups in typed sections,
not a supplied translation, approval callback or precomputed whitelist:

| Action | Original source authority |
|---|---|
| CONFIG | Proposed configuration membership and computed height/epoch context |
| ISC | Closed body membership, actual proposed-body lookup and round context |
| EC | Exact original proposed EC, finalized ISC, matching ISC/seed/norm parents |
| APC | Exact proposed plan, finalized ISC/EC, ISC/seed/EC parents; separately resolve finalized EC and compare norm |
| PARAMETER | Exact body assignment context and finalized plan; ISC/EC/plan/domain/shard parents and resolved plan seed |
| ROOT | Exact proposed root, finalized plan, ISC/EC/plan and computed body's Merkle field, resolved plan seed |
| APPLY | Exact proposed candidate, finalized root, profile/candidate identity, body current checkpoint and root context |
| VIEW | Prior executable exact original view/timeout/context/current-view/deadline authority |
| ABORT | Prior executable exact original abort/reason/current-parent/empty-finalized-APPLY authority |

PARAMETER's native vote_context_id returns the original nonempty assignment
string. It is not another hash computation. Other domains retain their exact
domain-separated SHA preimages. Shared state height/view must match each original
candidate. All per-action general witness theorems retain the actual first lookup
and guard conjunction; sourceSections connects these rows to the original
executed typed section chain. ISC/EC source composition and original failure tail
are explicit helpers, not new primitive trust assumptions.

`bindPolicy` first executes `NativeSnapshotBase.bindSnapshot sha p s`, then
checks EVERY member of the original `p.candidates` in order. No singleton
replacement, graph clearing or closed-subdomain policy substitution occurs.
List proofs retain original records, count, positions and every checked member.
The byte wrapper decodes the original policy/state and reuses canonical
role/reason/action/count/order/global-context checks. Raw `check`/`checkAll`
are component APIs: a caller-constructed Bound is not authenticated or validated
merely by invoking them. The byte/bind wrappers execute the snapshot relation.

## Kernel evidence and boundaries

The generator pins the entire original nine-policy codec observation (SHA256
`d82c14dda8356bfebc1cc1febe3c2fd09c3393b467cc99bacd565b506a91d2ea`),
reproduces each policy's original bytes, and computes all eight hash contexts;
PARAMETER retains its original assignment context. Original candidate bodies,
parents and positions are retained. No fresh native execution is claimed.

A complete original CONFIG example executes the new full snapshot/candidate
wrapper, and its original policy/state byte wrapper composes the previously
kernel-checked decoders. Other action examples reuse actual individually checked
original body/certificate rows inside an EXPLICITLY SYNTHETIC mixed component
snapshot. That assembly is not claimed to be an original native snapshot or a
successful complete mixed-policy wrapper run. No arbitrary hash/certificate
authentication is inferred from finite samples. The mixed assembly deliberately
has no complete size-record/source-policy validation claim.

Negatives exercise every required parent and the always-forbidden synthetic
parent, all nine context/height mismatches, missing body/config/closed/timeout,
missing finalized root, changed EC norm/plan seed/Merkle/apply ID/current parent,
abort after finalized APPLY, and an invalid second candidate that cannot be
skipped. Canonical duplicate context/reversed order are separately checked.
A positive scope countercheck retains a different well-formed CONFIG checkpoint
at authority time; later live current-parent checking remains required.

## Remaining STOP

This is original native candidate structural authority, not full selected
vote/live enabling, model arithmetic input derivation, CurrentPointerCommand,
historical retry, persist-before-expose or crash/unknown repair. Native source
decimal canonicality (-00/-01) remains a separately confirmed unresolved
compatibility failure; no silent normalization or runtime repair occurs.
Complete nonempty original multi-action wrapper examples, source arithmetic,
physical WAL/scan completeness, SHA/producer/signature/finalization authentication,
the full public64-variable relation, contract freeze, offline reproduction and
independent review remain required. Mandatory44/45 stays FAIL and report NO_GO.
Earlier TLA/native/model/mutant evidence retains its recorded finite scope.

## Reproduction

Run `python formal/scripts/generate_native_candidate_authority.py`, then the
targeted unittest module, full Lean build and AxiomAudit in `formal/proofs`.
Evidence is `formal/proposals/evidence/native-candidate-authority.json` and its
adjacent directory. GNU make is unavailable on this host, so scoped commands do
not claim aggregate `make formal-check`. No demo service restart or promotion.
