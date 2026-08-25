# Formal coverage matrix

**Task**: T001  
**Formal semantics version**: `1.0.0`  
**Registry**: `formal/reports/formal-id-registry.json`  
**Coverage status**: machine gates must be regenerated for the current semantic
source; independent human review gate pending

This matrix is a traceability contract, not a proof of its own completeness. The
cross-artifact analyzer checks IDs, set equality, source anchors and fixture
counts only. Semantic status comes from separately executed TLC, Lean,
production-mutation and refinement evidence; clean offline reproduction and two
independent human reviews remain fail-closed requirements. Any `UNRESOLVED` cell
is an unconditional STOP.

## Functional requirement mapping

| Requirement | Formal action or tooling boundary | Invariant / temporal property | Mandatory config or gate | Parametric proof / evidence |
| --- | --- | --- | --- | --- |
| FR-001 | Tooling boundary | N/A | `formal-parse`, `formal-proofs`, offline tool checksum gate | pinned lockfiles; T004–T006 |
| FR-002 | All `ACT-*` partitioned by registry module | `INV-TYPE-OK` | `CFG-SAFETY-F1`; SANY module parse | module import graph; T013–T038 |
| FR-003 | All public `ACT-*` | all registered properties | registry uniqueness gate | `formal-id-registry.json`; T003 |
| FR-004 | `Init`; disjunction of all public `ACT-*` | `INV-TYPE-OK` | `CFG-SAFETY-F1` | action reachability report; T038/T042 |
| FR-005 | `ACT-LOGICAL-TIME-ADVANCE`, `ACT-SEED-GENERATE`, parameter/apply actions | `INV-SEED-AFTER-FREEZE`, `INV-CONSENSUS-INTEGER-ONLY` | `CFG-INPUT-FREEZE-SEED`, `CFG-ARITHMETIC-BOUNDARY` | `PO-A1`–`PO-A3` |
| FR-006 | Constant/type initialization | `INV-TYPE-OK` | every TLC config | config constant inventory |
| FR-007 | Config boundary | all mandatory safety invariants | `CFG-SAFETY-F1` | recorded scope: `f=1`, 4 validators, ≥3 tickets, 2 domains, 2 shards |
| FR-008 | Config boundary | property-specific | all `CFG-*` in registry | coverage review; T042 |
| FR-009 | Config boundary | property-specific | every config using symmetry/constraints | soundness rationale and reachability evidence |
| FR-010 | Terminal predicate | `INV-ABORT-CERTIFIED`, `INV-CURRENT-CERTIFIED` | all safety configs | legal-terminal/deadlock classification |
| FR-011 | Fairness/assumption actions | all `LIVE-*` | all six `CFG-LIVENESS-*` models | assumption manifest; T041/T059 |
| FR-012 | asynchronous message/partition actions | all safety invariants | `CFG-SAFETY-F1`, `CFG-SPLIT-BRAIN-PARTITION` | no synchrony assumption in safety configs |
| FR-013 | all `*-VOTE` actions | `INV-VOTE-UNIQUENESS`, `INV-QC-UNIQUENESS` | `CFG-CONFIG-QC`, `CFG-VOTE-CRASH-RECOVERY` | `PO-Q1`, `PO-Q2` |
| FR-014 | `ACT-CRASH`, `ACT-RESTART`, `ACT-JOURNAL-RECOVER` | `INV-VOTE-UNIQUENESS`, `INV-RECOVERY-IDEMPOTENCE` | `CFG-VOTE-CRASH-RECOVERY` | `PO-Q2`, `PO-R2` |
| FR-015 | `ACT-TIMEOUT-SOFT`, `ACT-VIEW-VOTE`, `ACT-VIEW-FINALIZE` | `INV-VIEW-CHANGE-CERTIFIED`, `INV-QC-UNIQUENESS` | `CFG-SPLIT-BRAIN-PARTITION`, `CFG-VOTE-CRASH-RECOVERY` | `PO-Q1`, `PO-Q2` |
| FR-016 | `ACT-ABORT-VOTE`, `ACT-ABORT-FINALIZE` | `INV-ABORT-CERTIFIED`, `INV-ABORT-PRESERVES-PARENT` | `CFG-SAFETY-F1`, `CFG-APPLY-RECOVERY`, `CFG-SPLIT-BRAIN-PARTITION` | `PO-Q1`, `PO-Q2`, `PO-R1` |
| FR-017 | lease, commit and availability actions | `INV-TICKET-IMMUTABILITY`, `INV-LEASE-COMMIT-SAFETY`, `INV-COMMIT-UNIQUENESS`, `INV-AVAILABILITY-BEFORE-ISC` | `CFG-TICKET-LEASE-AVAILABILITY` | trace fixtures and duplicate-commit mutant |
| FR-018 | `ACT-INPUT-CLOSE`, `ACT-ISC-VOTE`, `ACT-ISC-FINALIZE` | `INV-AVAILABILITY-BEFORE-ISC`, `INV-ISC-IMMUTABILITY` | `CFG-INPUT-FREEZE-SEED`, `CFG-AVAILABILITY-LOSS-REPAIR` | mutable-ISC mutant |
| FR-019 | `ACT-SEED-GENERATE` | `INV-SEED-AFTER-FREEZE` | `CFG-INPUT-FREEZE-SEED` | early-seed mutant |
| FR-020 | EC/APC vote/finalize actions | `INV-EC-SUBSET-ISC`, `INV-APC-PARENTAGE`, `INV-CONSENSUS-INTEGER-ONLY`, `INV-NO-OVERFLOW` | `CFG-CERTIFICATE-FRANKENSTEIN`, `CFG-ARITHMETIC-BOUNDARY` | `PO-A1`–`PO-A3`, `PO-D1` |
| FR-021 | parameter propose/vote/finalize actions | `INV-NO-OVERFLOW`, `INV-SHARD-VIEW-ATOMICITY` | `CFG-ARITHMETIC-BOUNDARY`, `CFG-CERTIFICATE-FRANKENSTEIN` | `PO-A1`–`PO-A3`, `PO-H1`, `PO-H2` |
| FR-022 | root assemble/vote/finalize actions | `INV-SHARD-VIEW-ATOMICITY`, `INV-AGGREGATE-COMPLETENESS` | `CFG-CERTIFICATE-FRANKENSTEIN`, `CFG-SAFETY-F1` | `PO-C1`, `PO-H1`, `PO-H2` |
| FR-023 | apply compute/vote/finalize/current actions | `INV-APPLY-UNIQUENESS`, `INV-CURRENT-CERTIFIED`, `INV-NO-OVERFLOW` | `CFG-APPLY-RECOVERY`, `CFG-ARITHMETIC-BOUNDARY` | `PO-AP1`, `PO-AP2`, `PO-D1` |
| FR-024 | artifact corrupt/lose/repair actions | `INV-ISC-IMMUTABILITY`, `INV-RECOVERY-IDEMPOTENCE`, `INV-ABORT-PRESERVES-PARENT` | `CFG-AVAILABILITY-LOSS-REPAIR` | `PO-R1`, `PO-R2` |
| FR-025 | `ACT-PUBLISH` | `INV-PLANE-SEPARATION`, `INV-CERTIFIED-PUBLISH-ONLY` | `CFG-SAFETY-F1`, publication mutant | forbidden-media fixtures |
| FR-026 | all public actions | all `INV-*` | safety config matrix below | safety result manifest |
| FR-027 | fairness-enabled actions | all `LIVE-*` | phase-specific `CFG-LIVENESS-*` models | temporal result manifest |
| FR-028 | theorem tooling boundary | N/A | `formal-proofs`, no-`sorry`/axiom gate | `PO-Q1`–`PO-R2` |
| FR-029 | N/A | `INV-QC-UNIQUENESS` theorem link | theorem gate | `PO-Q1`, `PO-Q2` |
| FR-030 | parameter/apply arithmetic actions | `INV-CONSENSUS-INTEGER-ONLY`, `INV-NO-OVERFLOW` | `CFG-ARITHMETIC-BOUNDARY` | `PO-A1`, `PO-A2`, `PO-A3`, `PO-H2` |
| FR-031 | parameter/root actions | `INV-AGGREGATE-COMPLETENESS` | `CFG-CERTIFICATE-FRANKENSTEIN` | `PO-H1`, `PO-H2` |
| FR-032 | apply vote/finalize/current actions | `INV-APPLY-UNIQUENESS`, `INV-CURRENT-CERTIFIED` | `CFG-APPLY-RECOVERY` | `PO-Q1`, `PO-Q2`, `PO-AP1`, `PO-AP2` |
| FR-033 | root/certificate hash abstraction boundary | `INV-AGGREGATE-COMPLETENESS`, certificate parent invariants | `CFG-CERTIFICATE-FRANKENSTEIN` | `PO-C1`; named injective/hash assumption report |
| FR-034 | mutant tooling boundary | intended target invariant per mutant | `formal-mutants` | mutant inventory in Phase 9 |
| FR-035 | mutant tooling boundary | expected failing invariant | `formal-mutants` | expected-counterexample manifest |
| FR-036 | trace normalization boundary | N/A | `formal-mutants`, canonical JSON tests | normalized counterexample hash |
| FR-037 | every public `ACT-*` emits trace event | trace schema validity | `formal-refinement` | `formal-trace.schema.json`; T009/T053 |
| FR-038 | public action or documented stutter | all projected `INV-*` | `formal-refinement` legal/illegal fixtures | standalone checker; T054–T056 |
| FR-039 | later-feature implementation traces | affected properties | compatibility/formal-impact gate | ownership map and `formal_semantics_id`; T057 |
| FR-040 | report tooling boundary | all result classes | `formal-report` | report schema/evidence graph; T010/T063 |
| FR-041 | deterministic decision function | all mandatory result classes | report verifier | missing/incompatible evidence → `NO_GO` |
| FR-042 | canonical hash tooling | `INV-RECOVERY-IDEMPOTENCE` where replayed | clean offline reproduction | evidence graph and SHA-256 fixtures |
| FR-043 | CI boundary | all mandatory properties | aggregate `formal-check` | parser/model/proof/mutant/refinement/report jobs |
| FR-044 | tool/environment boundary | N/A | offline clean environment | no secret/data/network dependency scan |
| FR-045 | documentation/report boundary | N/A | final review | assumptions, abstractions, limitations and non-claims fields |
| FR-046 | semantic registry/report boundary | all stable IDs | compatibility verifier | changed semantic inputs invalidate `formal_semantics_id` and prior GO |

## Safety property coverage

| Invariant | Primary actions | Mandatory configs | Parametric support | Non-vacuity / negative evidence | Status |
| --- | --- | --- | --- | --- | --- |
| `INV-TYPE-OK` | all | every config | none | schema/type mutation | EXECUTED PASS |
| `INV-CONFIG-UNIQUENESS` | config propose/vote/finalize | `CFG-CONFIG-QC`, `CFG-SPLIT-BRAIN-PARTITION` | `PO-Q1`, `PO-Q2` | conflicting config trace | EXECUTED PASS |
| `INV-TICKET-IMMUTABILITY` | ticket/lease/commit | `CFG-TICKET-LEASE-AVAILABILITY` | none | post-open ticket mutation trace | EXECUTED PASS |
| `INV-LEASE-COMMIT-SAFETY` | lease expire/reassign/commit | `CFG-TICKET-LEASE-AVAILABILITY` | none | old/new holder race | EXECUTED PASS |
| `INV-COMMIT-UNIQUENESS` | commit | `CFG-TICKET-LEASE-AVAILABILITY`, `CFG-SAFETY-F1` | none | duplicate-commit mutant | EXECUTED PASS |
| `INV-VOTE-UNIQUENESS` | every vote; crash/recover | all `CFG-VOTE-LIFECYCLE-*`, `CFG-VOTE-CRASH-RECOVERY` | `PO-Q2` assumption correspondence | production missing-durable-vote mutation | EXECUTED PASS |
| `INV-ALL-QC-VOTES-PERSISTED` | every QC-producing vote | all nine `CFG-VOTE-LIFECYCLE-*` configs | durable-envelope correspondence | production `VoteISC` without persistence mutation | EXECUTED PASS |
| `INV-QC-UNIQUENESS` | every finalize-QC action | `CFG-CONFIG-QC`, `CFG-SPLIT-BRAIN-PARTITION`, `CFG-SAFETY-F1` | `PO-Q1`, `PO-Q2` | conflicting-QC traces | EXECUTED PASS |
| `INV-AVAILABILITY-BEFORE-ISC` | availability, close, ISC | `CFG-TICKET-LEASE-AVAILABILITY`, `CFG-AVAILABILITY-LOSS-REPAIR` | none | AC-shortfall trace | EXECUTED PASS |
| `INV-ISC-IMMUTABILITY` | close/ISC; loss/repair | `CFG-INPUT-FREEZE-SEED`, `CFG-AVAILABILITY-LOSS-REPAIR` | none | mutable-ISC mutant | EXECUTED PASS |
| `INV-SEED-AFTER-FREEZE` | seed generation | `CFG-INPUT-FREEZE-SEED` | none | early-seed mutant | EXECUTED PASS |
| `INV-EC-SUBSET-ISC` | EC vote/finalize | `CFG-CERTIFICATE-FRANKENSTEIN` | none | EC-adds-ticket trace | EXECUTED PASS |
| `INV-APC-PARENTAGE` | APC vote/finalize | `CFG-CERTIFICATE-FRANKENSTEIN` | none | missing-APC-parent mutant | EXECUTED PASS |
| `INV-CONSENSUS-INTEGER-ONLY` | EC/APC/parameter/apply | `CFG-ARITHMETIC-BOUNDARY`, `CFG-SAFETY-F1` | `PO-A1`–`PO-A3`, `PO-D1` | float/invalid rational fixture | EXECUTED PASS |
| `INV-NO-OVERFLOW` | EC/APC/parameter/apply | `CFG-ARITHMETIC-BOUNDARY`, `CFG-SAFETY-F1` | `PO-A1`–`PO-A3` | unchecked-overflow mutant | EXECUTED PASS |
| `INV-SHARD-VIEW-ATOMICITY` | parameter/root | `CFG-CERTIFICATE-FRANKENSTEIN` | `PO-C1` | mixed-parent mutant | EXECUTED PASS |
| `INV-AGGREGATE-COMPLETENESS` | root assemble/finalize | `CFG-CERTIFICATE-FRANKENSTEIN`, `CFG-SAFETY-F1` | `PO-C1`, `PO-H1`, `PO-H2` | incomplete-root mutant | EXECUTED PASS |
| `INV-APPLY-UNIQUENESS` | apply vote/finalize | `CFG-APPLY-RECOVERY`, `CFG-SPLIT-BRAIN-PARTITION` | `PO-Q1`, `PO-Q2`, `PO-AP1` | conflicting apply trace | EXECUTED PASS |
| `INV-CURRENT-CERTIFIED` | current advance/replay | `CFG-APPLY-RECOVERY` | `PO-AP2` | current-without-ApplyQC mutant | EXECUTED PASS |
| `INV-ABORT-PRESERVES-PARENT` | abort and all non-apply transitions | `CFG-SAFETY-F1`, `CFG-APPLY-RECOVERY`, `CFG-AVAILABILITY-LOSS-REPAIR` | `PO-R1` | abort-after-loss trace | EXECUTED PASS |
| `INV-RECOVERY-IDEMPOTENCE` | crash/restart/recover/replay/repair/current | `CFG-VOTE-CRASH-RECOVERY`, `CFG-APPLY-RECOVERY`, `CFG-AVAILABILITY-LOSS-REPAIR` | `PO-R2`, `PO-AP2` | duplicate command traces | EXECUTED PASS |
| `INV-VIEW-CHANGE-CERTIFIED` | soft timeout/view vote/finalize | `CFG-SPLIT-BRAIN-PARTITION`, `CFG-VOTE-CRASH-RECOVERY` | `PO-Q1`, `PO-Q2` | view-without-quorum trace | EXECUTED PASS |
| `INV-ABORT-CERTIFIED` | hard deadline/abort vote/finalize | `CFG-SPLIT-BRAIN-PARTITION`, `CFG-SAFETY-F1` | `PO-Q1`, `PO-Q2` | abort-without-quorum trace | EXECUTED PASS |
| `INV-PLANE-SEPARATION` | publish | `CFG-SAFETY-F1` | none | partial-publication mutant | EXECUTED PASS |
| `INV-CERTIFIED-PUBLISH-ONLY` | publish/current | `CFG-SAFETY-F1`, `CFG-APPLY-RECOVERY` | `PO-AP2` | weak/missing-certificate trace | EXECUTED PASS |

## Liveness coverage and claim boundaries

All positive liveness rows start from real empty `Init` before the named
milestone and exclude timeout/HardAbort as progress. They require eventual
synchrony, fair delivery/actions, bounded computation and an honest responsive
quorum in every required committee. Artifact-dependent rows additionally require
exact required bytes to remain available or repairable. These assumptions are
absent from safety configs.

| Temporal property | Progress actions | Positive config | Additional assumption | Required negative countercheck | Status |
| --- | --- | --- | --- | --- | --- |
| `LIVE-CONFIG-QC-REACHED` | config propose/persist/send/deliver/finalize | `CFG-LIVENESS-CONFIG-QC` | responsive quorum and fair transport | no-fairness model need not reach QC | EXECUTED PASS |
| `LIVE-ISC-REACHED` | config through close/ISC transport/finalize | `CFG-LIVENESS-ISC` | complete required input and fair transport | abort is disabled as a witness | EXECUTED PASS |
| `LIVE-PLAN-QC-REACHED` | config/ISC/seed/EC/APC full chain | `CFG-LIVENESS-PLAN` | valid norm/plan data and fair transport | abort is disabled as a witness | EXECUTED PASS |
| `LIVE-APPLIED-REACHED` | complete config→ISC→EC/APC→parameter→root→ApplyQC→current chain | `CFG-LIVENESS-EVENTUAL-SYNCHRONY` | all required quorums/artifacts and weak fairness | `NoFairnessSpec` violates `AppliedReached` | EXECUTED PASS |
| `LIVE-VIEW-QC-REACHED` | logical time→soft timeout→durable view votes→ViewChangeQC | `CFG-LIVENESS-VIEW-CHANGE` | view quorum and fair transport | no abort action is available | EXECUTED PASS |
| `LIVE-ABORT-QC-REACHED` | logical time→hard deadline→durable abort votes→AbortQC | `CFG-LIVENESS-ABORT-QC` | abort quorum and fair transport | ordinary progress is absent after deadline | EXECUTED PASS |
| `LIVE-ABORT-EXCLUDED-FROM-POSITIVE` | all positive milestone models | all four positive liveness configs | timeout/abort actions excluded | any ABORTED witness fails the property | EXECUTED PASS |
| `LIVE-CONFIG-FINALIZE-OR-ABORT` | config votes/finalize; view/abort | `CFG-LIVENESS-CONFIG-QC` | config proposal eventually enabled | permanent quorum loss reaches BLOCKED, never fake QC | EXECUTED PASS |
| `LIVE-COMMIT-AVAILABLE-OR-REJECT` | availability/close/abort | `CFG-LIVENESS-ISC` | required pre-ISC storage quorum or fixed close decision | unfair delivery is not claimed live | EXECUTED PASS |
| `LIVE-FROZEN-PLAN-OR-ABORT` | seed/EC/APC/abort | `CFG-LIVENESS-PLAN` | seed source/fallback and exact ISC bytes available | unavailable seed permits only abort/block | EXECUTED PASS |
| `LIVE-SHARD-QC-OR-ABORT` | parameter/view/abort | `CFG-LIVENESS-EVENTUAL-SYNCHRONY` | parameter committee quorum and shard bytes | permanent shard loss never rewrites membership | EXECUTED PASS |
| `LIVE-AGGREGATE-APPLY-OR-ABORT` | root/apply/view/abort | `CFG-LIVENESS-EVENTUAL-SYNCHRONY` | root/apply quorums and parent artifacts | apply quorum loss preserves parent | EXECUTED PASS |
| `LIVE-APPLY-QC-REPAIRS-CURRENT` | journal recover/current advance | `CFG-LIVENESS-EVENTUAL-SYNCHRONY`, `CFG-APPLY-RECOVERY` | durable ApplyQC and exact artifact available | artifact loss may remain BLOCKED | EXECUTED PASS |
| `LIVE-SOFT-TIMEOUT-CHANGES-VIEW` | soft timeout/view vote/finalize | `CFG-LIVENESS-VIEW-CHANGE` | `2f+1` timeout votes and fairness | one timeout observer cannot change view | EXECUTED PASS |
| `LIVE-HARD-DEADLINE-TERMINATES` | logical time/abort vote/finalize | `CFG-LIVENESS-ABORT-QC` | `2f+1` abort votes remain obtainable | without abort quorum hard deadline yields BLOCKED | EXECUTED PASS |

## Fault-to-config coverage

| Config | Fault IDs exercised | Principal properties |
| --- | --- | --- |
| `CFG-CONFIG-QC` | `FAULT-PROPOSER-CRASH`, `FAULT-PROPOSER-EQUIVOCATION`, `FAULT-SIGNER-SCOPE` | config/vote/QC uniqueness |
| `CFG-VOTE-CRASH-RECOVERY` | validator crash-before/after-persist/send, journal loss, message replay | vote uniqueness and recovery idempotence |
| `CFG-VOTE-LIFECYCLE-CONFIG`, `CFG-VOTE-LIFECYCLE-ISC`, `CFG-VOTE-LIFECYCLE-EC`, `CFG-VOTE-LIFECYCLE-APC`, `CFG-VOTE-LIFECYCLE-PARAMETER`, `CFG-VOTE-LIFECYCLE-AGGREGATE`, `CFG-VOTE-LIFECYCLE-APPLY`, `CFG-VOTE-LIFECYCLE-VIEW`, `CFG-VOTE-LIFECYCLE-ABORT` | persist/send/deliver/drop/duplicate and crash-before/after-persist/send for RoundConfig, ISC, EC, APC, Parameter, AggregateRoot, Apply, ViewChange and Abort votes | durable envelope backing, delivery-based signer power and recovery ordering |
| `CFG-TICKET-LEASE-AVAILABILITY` | lease expiry/race, commit replay/equivocation, AC shortfall, wrong-content attestation rejection | ticket/lease/commit/availability safety |
| `CFG-INPUT-FREEZE-SEED` | late input, early/wrong/conflicting seed, certificate replay/conflict | ISC immutability, seed ordering and EC/APC normal chain |
| `CFG-AVAILABILITY-LOSS-REPAIR` | pre/post real close/ISC loss, corruption, bounded exact-ID repair | identity-preserving availability repair and certified abort integration |
| `CFG-SPLIT-BRAIN-PARTITION` | quorum loss, partition, proposer equivocation, message replay | QC/view/abort uniqueness without synchrony |
| `CFG-CERTIFICATE-FRANKENSTEIN` | incomplete-input abort request, wrong EC/APC parents, non-subset membership, invalid norm evidence, unsafe coefficients | ISC/EC/APC parentage and fail-closed planning with parameter/root extensions |
| `CFG-ARITHMETIC-BOUNDARY` | EC/APC/parameter/apply overflow | integer-only and no-overflow |
| `CFG-APPLY-RECOVERY` | apply disagreement/quorum, post-ApplyQC crashes, pointer replay/conflict | Apply/current uniqueness and idempotence |
| `CFG-SAFETY-F1` | all fault families in bounded representative combinations, including P2P seed loss and forbidden publication | full mandatory safety regression |
| `CFG-LIVENESS-CONFIG-QC`, `CFG-LIVENESS-ISC`, `CFG-LIVENESS-PLAN`, `CFG-LIVENESS-EVENTUAL-SYNCHRONY` | phase-specific progress from real `Init`, through config/ISC/plan and the full path to `APPLIED` | positive milestone and conditional progress properties without abort as progress |
| `CFG-LIVENESS-VIEW-CHANGE` | soft-deadline observation followed by durable view-change vote transport and QC | `ViewQCReached`, `SoftTimeoutEventuallyChangesView` |
| `CFG-LIVENESS-ABORT-QC` | hard-deadline transition followed by durable abort vote transport and AbortQC | `AbortQCReached`, `HardDeadlineEventuallyTerminatesNonfinalizedRound` |

`FAULT-EPOCH-KEY-COMPROMISE` is modeled only within the declared `f`-Byzantine bound. Exceeding that bound is recorded as a limitation, not covered by a safety theorem.

## Proof dependency and usage coverage

| Proof | Establishes | Runtime/model consumers | Planned artifact |
| --- | --- | --- | --- |
| `PO-Q1` | `2f+1` quorum intersection in `3f+1` | every QC, including view and abort | `DeltaReduce/Quorum.lean` |
| `PO-Q2` | conflicting QC impossibility | vote/QC/view/abort/apply uniqueness | `DeltaReduce/Quorum.lean` plus durable-vote trace correspondence |
| `PO-A1` | signed product bound | parameter/apply multiply guards | `DeltaReduce/FixedPoint.lean` |
| `PO-A2` | flat accumulator bound | parameter/APC/apply sum guards | `DeltaReduce/FixedPoint.lean` |
| `PO-A3` | canonical reduced inputs, positive/divisible common denominator, numerator safety and all ADR-0002 rounding branches | APC/domain mixture/apply | nine named conjunct theorems in `DeltaReduce/FixedPoint.lean` |
| `PO-H1` | exact regional partition | topology and aggregate coverage preconditions | `DeltaReduce/Hierarchy.lean` |
| `PO-H2` | hierarchical result equals flat | regional/global parameter results | `DeltaReduce/Hierarchy.lean` |
| `PO-C1` | canonical complete coverage table | AggregateRootQC body/root | `DeltaReduce/Coverage.lean` |
| `PO-AP1` | ApplyQC vote uniqueness | apply finalization | `DeltaReduce/Apply.lean` |
| `PO-AP2` | ApplyQC/current uniqueness, accepted CAS and replay idempotence | pointer CAS/replay | four named conjunct theorems in `DeltaReduce/Apply.lean` |
| `PO-D1` | domain mixture independent of worker speed/order | deterministic apply candidate | `DeltaReduce/Apply.lean` |
| `PO-R1` | abort and non-apply transitions preserve current | hard abort/failure paths | `DeltaReduce/Apply.lean` plus TLA invariant |
| `PO-R2` | restoration of durable votes, certificates/current plus full observational and replay idempotence | journals, messages, repair and pointer recovery | five named conjunct theorems in `DeltaReduce/Apply.lean`; TLC for interleavings |

## Gate rule

The matrix records intended executable coverage; it does not certify semantic
completeness. Missing config coverage, an unreachable required action, a
contradictory assumption or any mismatch between a proof statement and
runtime/model preconditions changes the affected row to `UNRESOLVED` and stops
implementation until corrected. Formal GO requires passing semantic gates,
clean offline reproduction and both independent human review attestations.
