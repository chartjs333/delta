# DeltaReduce v1 Formal Failure and Recovery Semantics

**Status**: Normative input to the TLA+ model  
**Feature**: `000-formal-tla-spec`

## 1. Outcome classes

Every protocol operation resolves into one of four abstract outcomes:

- **FINALIZED**: a unique valid QC/certificate/state transition exists.
- **RETRYABLE**: no finalized value exists; the same immutable context may continue in a later view or after artifact repair.
- **ABORTED**: deterministic terminal round outcome; parent current checkpoint remains authoritative.
- **BLOCKED**: safety is preserved but liveness assumptions are absent (for example permanent partition without hard-abort policy). Production profiles SHOULD configure a hard deadline so active rounds terminate as ABORTED.

No failure rule permits an unsigned, partial, floating, arrival-order or single-validator fallback.

## 2. Deadline model

- `softDeadline(view, phase)` enables `ViewChange` when required QC/progress is absent.
- `hardDeadline(round, phase)` enables `HardAbort` and is immutable in RoundConfig.
- Logical deadlines are state-machine values; worker/operator wall clocks cannot directly finalize transitions.
- Retries/view changes do not extend the hard deadline unless RoundConfig contains an exact bounded extension rule certified before opening.

## 3. Failure matrix

| Failure point | Observable condition | Allowed transition | Recovery/progress condition | Terminal behavior | Preserved invariants |
| --- | --- | --- | --- | --- | --- |
| Proposer crashes before proposal | no durable proposal body | soft timeout → next view | honest proposer and quorum eventually reachable | hard deadline → ABORTED | Config/QC uniqueness, parent current |
| Proposer equivocates | conflicting proposal bodies in one context | honest validators vote at most once; record evidence | one body may obtain quorum | no quorum by hard deadline → ABORTED | QCUniqueness |
| Validator crashes before durable vote | no durable vote record | restart/recover; may vote once later | valid proposal and context | hard deadline → ABORTED | VoteUniqueness |
| Validator crashes after durable vote before send | durable vote exists, send unknown | restart re-sends exact vote idempotently | quorum eventually gathers | hard deadline → ABORTED | no double vote |
| Validator crashes after send | recipient/vote delivery unknown | exact replay allowed | quorum eventually gathers | hard deadline → ABORTED | idempotency |
| Validator loses durable journal | journal integrity/hash failure | quarantine validator; no new votes in epoch | recover verified backup or retain quorum without it | insufficient quorum → ABORTED | safety over liveness |
| Fewer than `2f+1` validators responsive | quorum impossible now | view changes/retries within deadline | quorum restored under same epoch | hard deadline → ABORTED | no fabricated QC |
| Permanent network partition | no component has required honest quorum, or one component does | only a component with valid quorum may finalize | eventual healing for liveness | BLOCKED/ABORTED by policy | conflicting QCs impossible |
| Duplicate/reordered/replayed message | same command/vote/certificate received repeatedly | idempotent no-op or same receipt | none required | original outcome | RecoveryIdempotence |
| Unknown/revoked/wrong-role signer | signature outside active role/epoch | reject before semantic action | valid quorum without signer | hard deadline may abort | QC validity |
| Active epoch key compromise | confirmed compromise evidence | emergency stop/abort; no dynamic membership rewrite | new epoch only in later round | ABORTED | epoch immutability |
| Ticket lease expires before commitment | current lease deadline finalized, no accepted C | reassign same immutable ticket with incremented lease epoch | eligible replacement worker | missing ticket handled by close/abort policy | ticket immutability |
| Old/new lease holders race | competing commits | BFT order accepts at most first valid current lease/epoch root | none | conflict evidence | CommitUniqueness |
| Worker submits same root twice | exact idempotent retry | return original receipt | none | original outcome | CommitUniqueness |
| Worker submits conflicting root | same ticket, different C | reject and record equivocation | none | ticket remains bound to first root | CommitUniqueness |
| Commitment lacks enough AC attestations before close | incomplete coverage/quorum | remain COMMITTED; not eligible for ISC | more valid attestations before close | omitted according to frozen close rule or round abort | AvailabilityBeforeISC |
| Storage attester equivocates | conflicting availability claims | reject conflicting vote/attestation; evidence | enough honest attestations | omit/abort | AC uniqueness |
| Shard corrupt/lost before ISC | hash/read failure | repair/reupload before AC/close | exact bytes restored and attested | tuple omitted/round abort by policy | no false AC |
| Late C/AC after ISC | valid but after freeze | record late evidence only | eligible in later round if policy permits | no current-round effect | ISCImmutability |
| Required shard corrupt/lost after ISC | ISC tuple exists but bytes unavailable | bounded exact-ID fetch/repair from attested replicas | exact bytes restored before hard deadline | ABORTED; ISC not rewritten | F-AVAIL, AbortPreservesParent |
| All post-ISC replicas lost | irrecoverable content ID | no substitution/replacement | none | ABORTED | certificate lineage |
| Seed shares/beacon unavailable | no valid transcript after ISC | retry/fallback only if exact fallback profile was precommitted | sufficient valid shares/beacon | ABORTED | SeedAfterISC |
| Seed proposal bound to wrong/no ISC | invalid parent | reject | valid transcript | hard deadline → ABORTED | SeedAfterISC |
| EC norm/trim computation overflow or mismatch | validators produce invalid/different body | reject; view change after deterministic recomputation check | identical valid body | ABORTED | integer safety |
| APC coefficient/headroom unsafe | proof precondition fails | reject APC | none without new round/config/profile | ABORTED | NoOverflow |
| Parameter proposer absent/crashes | no result body | view change/retry | exact inputs available and quorum reachable | ABORTED | no partial fallback |
| Parameter proposer sends wrong/mixed view | parent/config/shard mismatch | reject, record evidence | valid proposal | ABORTED if no quorum | ShardViewAtomicity |
| Parameter committee cannot obtain quorum | fewer than `2f_s+1` matching votes | view change/retry | quorum restored | ABORTED | QCUniqueness |
| Parameter result arithmetic overflow | checked operation fails | deterministic reject/abort evidence | none for same plan | ABORTED | NoOverflow |
| Aggregate assembly missing shard | incomplete required table | cannot vote/finalize | missing valid QC arrives before deadline | ABORTED | AggregateCompleteness |
| Aggregate assembly duplicate/overlap | invalid coverage | reject | corrected complete table | ABORTED | AggregateCompleteness |
| Aggregate assembly mixed view | any parent root differs | reject whole proposal | uniform table | ABORTED | ViewAtomicity |
| Apply validators disagree | different next hashes/body | honest validators sign deterministic expected body only | environment/profile corrected only in new execution with same exact semantics; otherwise no quorum | ABORTED | ApplyUniqueness |
| Apply arithmetic overflow | checked operation fails | reject/abort | none for same aggregate/profile | ABORTED | NoOverflow |
| Apply quorum unavailable | ApplyQC cannot form | view change/retry | quorum restored | ABORTED; parent current | AbortPreservesParent |
| Crash after ApplyQC before artifact publication | QC final but artifact visibility incomplete | verify/reconstruct exact artifact and retry publication | exact bytes available | BLOCKED for distribution, not a different state | Apply uniqueness |
| Crash after ApplyQC before current-pointer CAS | QC exists, pointer still parent | replay exact ApplyQC and CAS | durable QC/artifact available | pointer advances once or remains safely parent until recovery | CurrentCertified |
| Duplicate current-pointer application | same ApplyQC replay | idempotent success | none | same current | ApplyUniqueness |
| Conflicting current-pointer application | another ApplyQC/body for same height | reject | none | parent/original current remains | ApplyUniqueness |
| P2P initial seed lost | certified object pieces not all locally available | fetch from remaining verified peers | complete union reachable | `PIECE_UNAVAILABLE`; no certificate rollback | plane separation/current certification |
| Distribution receives local/partial artifact | forbidden media type | reject before advertisement | none | no publication | PlaneSeparation |
| Evidence sink unavailable | mandatory evidence cannot be sealed | protocol may preserve state but wave/next-round promotion follows configured fail-safe | evidence service recovers | stop/abort future progress as policy states | history integrity |

## 4. View-change invariants

A view change may update only leader/view metadata, timeout bookkeeping and message/vote collection state. It MUST NOT change:

- finalized configuration or validator epoch;
- ticket definitions or accepted commitments;
- AC/ISC membership;
- seed transcript once finalized;
- EC/APC parentage or weights;
- finalized shard/aggregate/apply certificates;
- current checkpoint.

Durable votes remain visible to the no-double-vote guard across views when the vote context forbids re-voting conflicting values.

## 5. Repair semantics

Repair is identity preserving:

1. identify missing/corrupt content by committed content ID and length;
2. fetch from a peer/storage replica that can provide bytes;
3. verify exact hash/context before visibility;
4. atomically restore the same content ID;
5. never create a new commitment, AC, ISC entry or certificate body.

If the original bytes cannot be recovered, the only legal terminal result for an ISC-dependent round is ABORTED.

## 6. Recovery ordering

A restarted role MUST execute in this order:

1. authenticate runtime identity and active/historical epoch;
2. verify/load immutable config and parent state;
3. replay/verify durable vote and transition journal;
4. verify referenced artifact content IDs;
5. reconstruct derived caches and volatile queues;
6. resume idempotent send/receive/repair actions;
7. only then accept new vote/proposal commands.

Any durable-state corruption or ambiguity fails closed and may remove the role from liveness, never from historical verification.

## 7. Safety versus liveness claims

- **Safety scope**: asynchronous network, arbitrary reorder/duplicate/drop, up to `f` Byzantine validators, crash/restart and modeled artifact faults, subject to cryptographic and durable-journal abstractions.
- **Liveness scope**: eventual synchrony, at least `2f+1` honest/responsive validators in required committees, required artifact availability/repair, bounded computation and declared fairness.
- **Outside liveness scope**: the protocol may block until hard abort, but must not finalize conflicting or uncertified state.
