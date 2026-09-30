# Feature010 continuation checkpoint

## ISC producer ownership audit — 30 September 2026 — MISSING PRODUCTION TRANSITION / STOP

The user accepted the previous STOP and authorized only an ownership audit.
The [audit](adr/0013-isc-producer-ownership-audit.md) classifies the result as
**3. MISSING PRODUCTION TRANSITION**, with a necessary qualification: the original
native owner, abstract FinalizeISC contract and canonical object contracts DO
exist. The missing part is the executable received-quorum -> finalized typed ISC
-> durable/exposed native state transaction and its state/WAL binding.

Original August design assigns computation to C++ core and persistence/exposure
to native runtime. Java/FFM/sidecar forward opaque inputs; the Python/controller
Authorization Gate has no consensus authority. No intentionally external producer
contract was found. ISCBuilder/QC is a plan node; existing constructors/validators,
fixture signers and summary ACT-ISC-FINALIZE traces do not establish the production
transition. The checked source pins and historical design blobs are preserved in
[documentary evidence](adr/evidence/0013-isc-producer-ownership-source-audit.json).

No transition, predicate, authority, schema, code, proof, Profile v1 or DoD change.
R1/R2.1/R2.2 CLOSED; R2.3/R2 OPEN. R2/R3 were not continued. STOP pending a new
direct production architecture decision; do not infer programming authorization.
Older continuation entries below are historical.

## R2.3 stage 1 — 29 September 2026 — INSUFFICIENT / ARCHITECTURE STOP

The user authorized only the existing-native-producer/bounds sufficiency check,
maximum four active hours. The [stage-1 checkpoint](adr/0013-r2-3-stage1-sufficiency.md)
identifies a minimal missing source-bound native finalization edge: original
votes/prior snapshot -> first finalized ISC in `input_set_certificates` and
`finalized_input_set_ids`. Existing native code validates supplied collections;
FINALIZE_INPUT_FREEZE updates only RoundState, and journal replay pins an immutable
startup policy. Public FinalizeISC already specifies the protocol obligation,
but substituting public Next for an independent native producer is forbidden by
approved Profile v1. No fix/new rule was introduced.

The mandatory early STOP precedes completion of the planned 33/64-field map.
Whole-public bounds were located but their total applicability is NOT ESTABLISHED;
no valid produced oversized cut or production-reachable EC counterexample is
claimed. The [source audit](adr/evidence/0013-r2-3-stage1-source-audit.json) pins
inspected sources and unchanged baseline hashes; it is not new formal evidence.

R1/R2.1/R2.2 CLOSED; R2.3/R2 OPEN; R3 not started. Profile/DoD and all code,
proofs, schemas, fixtures, Init/Next and QC/WAL identities remain unchanged.
Stages 2-5 are NOT authorized; the conditional 30-52 hour estimate assumed
producer sufficiency and is not validated. STOP pending a new direct decision;
heartbeat does not authorize a fix or continuation. Earlier entries are historical.

## R2.3 execution plan — 29 September 2026 — approved profile / STOP

The user approved Snapshot Provenance Profile v1 for the current production
scope and authorized only a short implementation/proof plan. The finite
[R2.3 plan](adr/0013-r2-3-implementation-plan.md) names the exact proposal files,
six target statements, five work packages and CLOSED/STOP criteria. Conditional
estimate: 32–56 active hours, with a source-contract/representation stop-check
within the first 2–4 hours of any later authorized implementation. This is an
estimate, not current programming authority or a Formal GO/R3 estimate.

The target is independent raw profile/source-history binding -> admissible
native cut -> complete static family relation using accepted R2.1/R2.2. A
success-only checker or supplied full-state equality cannot close it; complete
coverage/totality on the approved source domain is required. No new source cap,
public-success premise or protocol identity change may hide an incompatibility.
Production recovery/activation and R3 are excluded. No new provenance alternative.

R1/R2.1/R2.2 CLOSED; R2.3/R2 OPEN; R3 not started. Only planning/progress docs
changed; no code, schema, checker or proof implementation. STOP after plan until
the user explicitly authorizes programming. Older entries are historical.

## Snapshot Provenance Profile v1 — 29 September 2026 — concrete proposal / STOP

The user conceptually accepted ADR-0013 as the production trust model and asked
for one concrete profile, documentation only. The
[Linux single-epoch profile](adr/0013-snapshot-provenance-profile-v1.md) selects
offline independent bootstrap, genesis-to-cut native history verification, a
separate non-rolled-back trust volume retaining original own journals/floor,
immutable data generations plus one authoritative activation commit, and closed
canonical JSON control metadata preserving original protocol bytes/identities.

The eight-step procedure is bounded: fresh runtime on an empty data disk ->
bootstrap anchor -> certificate authority -> full provenance -> exact trusted
floor -> original WAL reconstruction -> atomic activation -> READY. This profile
restores an already enrolled identity with independent retained own history;
it does not invent membership or a new empty journal. Rollback of the trust
volume/host-root compromise is outside its explicit threat boundary. Full native
producer composition and original typed signature evidence binding are not yet
implemented/proved; missing checker/input ends BLOCKED, never READY.

R1/R2.1/R2.2 CLOSED; R2.3/R2 OPEN; R3 not started. Only profile/progress docs
changed; no schema/code/proof/fixture/normative DoD or baseline modification.
Detailed profile awaits approval; STOP after this report, with no automatic
R2/R3 or production work. Earlier entries are historical.

## Snapshot Provenance Contract v1 — 29 September 2026 — draft / STOP

The user selected the production architecture: independently trusted validator
set/epoch -> existing ApplyQC/checkpoint -> snapshot -> WAL -> recovered current,
with fail-closed rollback protection against a known newer trusted anchor.
[ADR-0013 specification](adr/0013-snapshot-provenance-contract-v1.md) records the
exact reusable types, missing bindings, import/bootstrap/rollback/crash rules,
R2/R3 impact and remaining decisions. Detailed contract awaits approval.

Existing ApplyQC authenticates its model/optimizer tuple, not a complete
consensus snapshot root or private local journals. The draft proposes complete
cut derivation from independently verified native producer history, using the
existing certificates; no parallel SnapshotQC. That producer/checker is not yet
complete, and replay from an arbitrary supplied snapshot is insufficient. A
direct full-root certificate commitment would instead require an explicit
separate semantic decision. Key/epoch provisioning, monotone floor storage,
genesis/import profiles and concrete evidence encoding remain stated decisions.

R1/R2.1/R2.2 remain accepted CLOSED; R2.3/R2 OPEN; R3 not started. This is
documentation only, not a new predicate, proof, schema, fixture, runtime change,
Formal GO or completed provenance verification. Frozen DoD and baseline inputs
remain unchanged. STOP after specification; no automatic R2/R3 or A/B/C work.
Await approval and a separate scoped implementation instruction. Earlier entries
are historical; their unselected P1/P2 status predates the user's new decision.

## Latest decision memo — 29 September 2026 — P1/P2 awaiting user choice

The user accepted `MISSING SNAPSHOT PROVENANCE CONTRACT` as the architectural
blocker for R2.3. The requested documentation-only comparison is in
[ADR-0012 provenance decision memo](adr/0012-snapshot-provenance-decision-memo.md).
P1 states explicit conditional R2/R3 targets and a logical non-circularity
argument for an external native-origin assumption; it does not prove R2/R3.
P2 describes a proposed genesis/epoch/QC-rooted recovery evidence contract and
source-only origin verification. A signature alone cannot establish history
legality, and a checkpoint QC cannot authenticate every actor's local WAL.

Neither option is adopted. Their trust-boundary/DoD/claim and verification impact
is documented, including that a missing full producer contract cannot be hidden
inside a Boolean assumption or a digest-only checker. The full article text is
not present; claim impact is grounded in the repository's source provenance
memos and normative formal requirements rather than unverified article quotes.

R1/R2.1/R2.2 remain accepted CLOSED; R2.3/R2 OPEN; no R3. No new formal predicate,
proof, schema, fixture, runtime change or normative contract amendment. No formal
GO claimed. Direct STOP until the user chooses; no automatic implementation of
P1/P2 or A/B/C, and no automatic R2/R3 continuation. Earlier entries are historical.

## Latest checkpoint — 29 September 2026 — MISSING SNAPSHOT PROVENANCE CONTRACT

The user's documentation-only audit is complete:
[snapshot provenance audit](adr/0012-snapshot-provenance-audit.md), with
[documentary source hashes](adr/evidence/0012-snapshot-provenance-source-audit.json).
It inventories supplied startup policy, local snapshot/replay, backup/recovery
cut, certified current artifacts, exported witness and synthetic fixture paths:
producer, authentication, required lineage, continuity checker and existing
requirement. No new predicate or proof layer is created.

The frozen contract contains anchor/recovery/certificate/export authentication
premises and partial continuity checks, but no already specified sufficient
independent authority/provenance predicate for the full nonempty initial snapshot
and its producing protocol prefix. An uninterpreted authentication premise or
policy/WAL hash cannot silently be given that stronger meaning. This is a contract
decision STOP, not a request to implement a new exporter or prove cryptography.

Result: **MISSING SNAPSHOT PROVENANCE CONTRACT**. No A/B/C selected or implemented;
no domain restriction adopted. R1/R2.1/R2.2 CLOSED; R2.3/R2 OPEN; no R3. Existing
DoD/requirements, code, proofs, schemas, fixtures, guard and old evidence remain
unchanged. No new native/formal execution. Await a separate user contract/
architecture decision; no automatic R2 continuation. Keep automation present,
healthy demos and frozen refs unchanged. Earlier entries below are historical.

## Latest analysis — 29 September 2026 — R2 domain not established / STOP

The bounded documentation-only domain analysis is recorded in
[the ADR-0012 addendum](adr/0012-r2-domain-analysis.md), with its
[source audit](adr/evidence/0012-r2-domain-source-audit.json).
It does not establish either requested binary outcome. The old API witness is
not protocol genesis and its exact sequence cannot run through one pinned
Runtime/WAL. Existing TLA finalization also excludes two finalized ISC records
for the round. These source arguments do not establish the complete native
initial/origin predicate for the frozen R2 domain. No admissible initial or
production-reachable representation counterexample has been established either.

The one precise analysis residual is the independent origin of preloaded,
nonempty certificate collections. Native replay derives a history from supplied
initial state/policy; it does not derive that initial snapshot's protocol origin.
Restricting coverage to empty snapshots/current guarded Runtime would omit the
already required nonempty cuts and amended arithmetic. Defining origin by a
successful R2 projection would be circular. This is the existing initial/source
part of R2.3, not a new obligation or production exporter requirement.

No A/B/C implementation or source-domain restriction is selected. The diagnostic
alone is not grounds for requiring an architecture change. R1/R2.1/R2.2 CLOSED,
R2.3/R2 OPEN, R3 NOT STARTED. No code, proof, protocol, schema, fixture, guard or
old evidence changes; no new native/formal run. STOP after this analysis; no
automatic R2 continuation. Keep the existing automation present and healthy
demos/frozen refs unchanged. Earlier entries below are historical.

## Latest analysis — 29 September 2026 — ADR-0012 / no implementation

The user's EC context/identity decision analysis is recorded in
[ADR-0012](adr/0012-ec-context-identity-options.md), with exact source provenance
in [its documentary audit](adr/evidence/0012-ec-context-source-audit.json).
Options A/B/C, existing contract impact, affected proofs/evidence and conditional
active-hour estimates are compared. No option is selected or implemented.

Reachability clarification: the prior ISC@1/EC@2/EC@3 witness combines separate
ISC and EC admission fixtures/policies in one in-memory VoteJournal. The exact
chain cannot run through one Runtime/WAL at the pinned native revision:
ISC requires available, EC requires eligible, committed submit invalidates the
immutable vote policy, and replay rejects replacement policy identity. A fresh
ELIGIBLE state/policy supplied through OPEN is a different initial-state/API
claim, not a protocol-generated history; its Runtime execution was not tested.
Production TLA FinalizeISC also prevents a second finalization for that round.
This is source/control-flow analysis, not a new native run, Lean theorem or TLC
result. The native pin is not an ancestor of this candidate or the frozen demo.

The old API-domain counterexample remains valid at its exact source. It is not
a proven production-reachable safety violation and does not by itself establish
that production semantics must change. Source-qualified initial-state admission
is already in the frozen contract; neither an assumed whole-state translation
nor a new unconditional source-domain restriction is introduced here.

R1/R2.1/R2.2 remain CLOSED. R2.3/R2 OPEN; no R3. The same full snapshot/static
collections/initial-incomplete-sufficient-ABORT relation remains unclosed.
No proof, implementation, schema, fixture, report, guard or demo changes; no new
proof layers. STOP and the frozen DoD remain. Await a direct scoped instruction;
heartbeats and unused old budgets do not authorize implementation.

## Latest checkpoint — 29 September 2026 — R2 OPEN / architectural STOP

Direct R2.3-only authorization followed user acceptance of R2.1/R2.2 as CLOSED.
The eight-active-hour maximum was stopped early on a concrete representation
obstruction. No R3, scope expansion or production fix is authorized here.
R1 and R2.1/R2.2 remain CLOSED; full R2 and Formal GO remain OPEN/NO_GO.

One original ISC body with two valid quorum signer subsets {1,2,3}/{1,2,4}
produces different native QC IDs. The unchanged native policy admits two EC
contexts/votes for the same actor, retaining its prior ISC vote and original
EC sequences 2/3. The public EC context is the identical ISC body. Distinct
projected EC bodies violate CertificateVoteUniqueness; equal bodies collapse
the durable set and cannot retain the original vote count/sequence. This blocks
total coverage of the accepted native snapshot/journal domain by the current
source-bound public representation. The test executes original admission and
the in-memory VoteJournal, not a filesystem WAL or a production-reachable trace.
An assumed complete public-state projection is not an admissible way to exclude
the witness. No production predicate or certificate/WAL identity was changed.

Before STOP, conditional snapshot PARAMETER/ROOT constructors and a sufficient
ABORT component were added inside the existing FamilyRelation. They retain
original nonempty downstream lineage and do not invent a local vote for remote
certificates. Their kernels do not establish the unclosed complete-state or
initial/incomplete applicability claim. The same frozen R2.3 residual remains;
no extra deliverable or universal full-ABORT gate is introduced.

Exact reproduction, source predicates, limitations and residual delta:
`formal/proposals/b-family-transfer/QC-CONTEXT-BLOCKER.md`.
Native diagnostic evidence:
`formal/proposals/evidence/r2-qc-context/counterexample.json`.
Proposal kernel/source audit:
`formal/proposals/evidence/b-family-constructors.json`.
Active time and final commit are recorded in
`D:/delta-presentation/FORMAL-GO-R1-R3-ACTIVE-TIME.json` and the latest continuation
entry. No automatic R2 resumption or R3; keep the existing automation ACTIVE,
preserve healthy demos and frozen refs. Earlier entries below are historical.

---

Updated: 2026-09-23. Current stage: **Feature000 arithmetic binding candidate, IN_PROGRESS**.
No new Formal GO, qualifying BenchmarkResultQC or Feature010 GO checkpoint exists.

## Morning presentation — working app available

The user's latest priority is presenting a working application on September 24.
The separate simulation worktree contains a runnable English/Russian presentation UI:
`http://127.0.0.1:8870/?lang=en`, with the baseline Controller/Worker at port 8865.
Presentation source: `b5f06eff7488c367b882050483bb08130456bfd7`; acceptance/evidence
overlay: `856ddaf`; localization: `173da69`. English is the default and the one-click
launcher explicitly opens English. The clean baseline `D:/delta-main-demo` remains
at `c8aea649...`.

One-click user entry: `D:/delta-presentation/START.cmd`. Data root:
`D:/delta-data/presentation-20260924`. Read `tools/presentation/README.md` and
`docs/feature010-presentation-status.md` in the simulation worktree for lifecycle,
reviewed evidence and the five-minute demo. Ten tests, real browser-triggered
CPU training/receipt and Docker 4→3→2→3 runs passed. Full graceful stop/restart
preserved history. Do not disturb the unrelated service on port 8765.

Keep the presentation available while continuing the formal work below. This
wrapper has semantic impact NONE and does not implement Java/native/WAL or GPU
scientific training. It does not close qualifying gates or change this candidate's
NO_GO. The hourly continuation has been updated with this presentation priority.

## Authorization and working copies

The user authorized sequential implementation, self-review and continued overnight
work. Unavailable independent authorities and real WAN must have a separate
`SIMULATED_LOCAL` mode. Self-review must be identified honestly; it is not evidence
of independent key custody or evaluator signatures. Follow AGENTS.md and the
formal-first STOP before changing features 001–011.

Active candidate worktree:
`C:/Users/madoev/.codex/worktrees/feature000-binding-candidate/delta`, branch
`codex/feature000-binding-candidate`. Always inspect its git status first. Original
`D:/delta` has unrelated untracked user files; preserve them.

Separate simulation worktree:
`C:/Users/madoev/.codex/worktrees/feature000-arithmetic-binding/delta`, branch
`codex/feature010-simulated-local`. Its source is
`744e9234d6040f4d7acf09f0b73a07d180c61884`; evidence commit is
`7195cbb519865d7d4192d4480cc89f9e780b580e`.

Last inspected remote baseline (recheck before integration): main
`c8aea64972f741060d1e527ebbb6f9a5a168a075`; PR50 OPEN at
`60c692f6e391f839829dfc64e93380db54cd507b`; recovery candidate
`e94fb08ad75d0693d566f1761cac8cc992bb4e42`. PR50 has not been qualified by this work.

## Candidate work performed

- Draft canonical byte graph and independently supplied native pre-state anchor:
  schema, checked arithmetic profile, domain/shard assignments, q-shard commitments,
  certificate projections, parent model/optimizer and aggregate result binding.
  Certificates are an explicit authentication premise, not implemented signatures.
- PARAMETER expected numerator and APPLY expected model/optimizer computation from
  those bytes, with exact canonical candidate equality before any persistence.
- Python/C++ arithmetic comparison and standalone Lean helper lemmas.
- Production TLA+ actions now derive bounded arithmetic from input constants in
  place of expected-output constants. Vote actions revalidate before persistence.
  New nonzero safety/liveness configurations and four production-source mutants.
- TLC coverage parser now handles successive complete cumulative snapshots and
  rejects duplicate rows, incomplete snapshots and regressing counters.

This is still a candidate: the TLA model has one coordinate per shard and uniform
q/weights. It does not establish arbitrary vectors, the public byte decoder,
current-state binding at every crash cut, or the native runtime implementation.

## Executed checks

- 38 proposal tests passed after rejection hardening; consult
  `formal/proposals/evidence/candidate-checks.json` for the final run counts.
- 1,012 Python/C++ arithmetic cases passed with GCC/UBSan; exact retained report:
  `D:/delta/artifacts/feature000-binding/cross-language-002/report.json`.
  This compares arithmetic, not complete C ABI/FFM/IPC canonical bytes.
- 15 standalone Lean statements compiled without `sorryAx`. Their declared axioms
  are `propext`, `Quot.sound` and `Classical.choice`; this is not the full proof gate.
- All 20 mandatory safety and 7 liveness TLC configurations passed. The removed
  fairness countercheck produced its expected temporal counterexample.
- All 14 production-source mutants were killed by their intended invariants.
- 61 formal tooling tests passed. Existing refinement fixtures passed after
  regeneration with the candidate semantics ID; they do not yet check arithmetic
  artifact witnesses, so this is not arithmetic refinement closure.

The former `cc98f15a...` report applies only to its historical merged artifact set.
The changed candidate has a different semantics ID and cannot inherit that GO.
Task checkboxes remain open until their complete evidence requirements are met.

## Self-review: remaining Feature000 work, in order

### September 23 continuation: trace admission regression closure

The public checker incorrectly accepted all 15 newly retained negative traces:
mixed vote height/epoch, relabeled finalizer height/epoch, a crashed validator
voting, and votes/recovery enabled by unsuccessful recovery/restart outcomes.
The fixed checker rejects all 15 with the intended reason. It preserves durable
conflict detection across recovery and permits recovery retry and config QC
finalization after a leader-view change. `view` is not blindly appended to all
QC keys: `ConfigContext` binds height/epoch, and view-change-specific contexts
remain action-specific. Source anchors are `DeltaReduceTypes.RoundContexts`,
`ConfigContext`, `DeltaReduceQuorums.CanVote`, and the existing recovery actions.

Evidence: `formal/proposals/evidence/refinement-admission.json`, the retained
test log and `formal/reports/refinement-evidence.json`. There are now 72 passing
formal tooling tests and 9 legal / 31 illegal public fixtures. The before/after
comparison executes the checker from source `0aacd14` against the same 15 traces.
Changed Python files pass Ruff and formatting. This is self-review only.

TLA/Lean/public schema bytes did not change in this correction, so the candidate
semantics ID stays `e3db697d...`. Arithmetic witnesses, the full proof gate and
independent reviews are still missing; the updated report must remain NO_GO.
The full formal check still stops at its phase-zero frozen-input mismatch; do not
refreeze incomplete contracts merely to hide it. No native implementation is
authorized by these partial fixture checks.

### Next substantive stage

1. Freeze production artifact encoding and a trace schema that independently
   binds authenticated native pre-state, canonical source bytes and certified
   parents. Both vote actions must reject missing witnesses. The draft JSON
   projections are not a production certificate decoder.
2. Extend the TLA arithmetic fixtures to heterogeneous domains/weights and the
   rounding-before-mixture counterexample; cover changed model/optimizer,
   stale role/view/epoch/deadline, missing/corrupt bytes and persist/restart cuts.
   Audit revalidation against the current checkpoint after current advances.
3. Integrate parametric binding/conversion/width/recovery proofs into the mandatory
   Lean project. `PO-AB1` is registered with four mandatory theorem conjuncts;
   their production source is intentionally absent until proved. The helper file
   alone does not discharge these obligations, and no placeholder was introduced.
4. Add the remaining production mutants, public trace negatives and complete
   cross-language canonical graph vectors. Verify every prerequisite separately.
5. Update semantics version/registry, proof and trace coverage, phase-zero hashes,
   exact-source evidence and clean reproduction. Run the full formal gate and
   write an honestly scoped self-review/new report. Never reuse old GO or invent
   reviewer attestations. Merge only a genuinely complete reviewed formal authority.

## Later stages still open

After the exact merged new Formal GO: recover the best PR50/candidate source,
implement native PARAMETER/APPLY admission and WAL/retry/recovery semantics; run
all C ABI/FFM/IPC and inline/SHM checks; qualify profile selection; then Gate A,
scientific Gate B on physical GPU, simulated Gate C, real Gate D, ResultQC and
final publication/Constitution check in that order.

Simulation currently has a Docker controller quorum/restart harness with test
keys, 18 tests and GPU visibility evidence. It is not the joined
Python → Java/Netty → C++/WAL → model/evaluator path. It cannot close Gate A/B/C/D.
Observed GPU: RTX 3070 Laptop, 8192 MiB, driver 581.32,
UUID `GPU-4f9cec9a-c8e8-3f95-4706-c70e0b11df5d`. Capacity/visibility is not scientific
qualification. Real model/data/evaluator licenses and the frozen workload still
need evidence.

Keep `gate_eligible=false`, `benchmark_result_qc=null`,
`feature010_go_checkpoint_sha=null`, `feature011_admitted=false` for simulation.
Independent controller custody, real WAN identities/paths and final evaluator
quorum remain external prerequisites for actual GO.

## Reproduction notes

Pinned local TLC Java:
`D:/delta/formal/toolchain/windows/tla-runtime-17.0.20.1/java/bin/java.exe`;
jar: `D:/delta/formal/toolchain/cache/tla2tools.jar`.
Lean helper compiler:
`D:/delta/formal/toolchain/windows/lean-4.32.1-windows/bin/lean.exe`.
The full mathlib dependency/cache environment has not been verified.

Arithmetic Docker image ID:
`sha256:b68c134517a27e91bb2568eb4b46073dfb48d9aa740423ec13b0da6442d643fb`.
The first comparison failed because compiler temporary storage was read-only;
retain `cross-language-001` as failure evidence. The second run used bounded tmpfs
for `/build` and `TMPDIR`, with read-only root, no network and dropped capabilities.

An hourly heartbeat named `Feature010 — последовательная доработка` continues this
task using this file. Each run should make concrete progress and update this
checkpoint; report meaningful completion/failures, not unchanged status. When
all locally executable work is complete, stop the continuation and report the
remaining external requirements honestly.

## September 23: current-parent vote admission

Source `0615ade`: TLC reproduced a delayed first PARAMETER vote after current
advanced (36-state counterexample). VoteParameter now rechecks current at
persistence, matching VoteApply. Two focused f=1 configurations execute
production 3-of-4 quorums and probe the fourth validator before and after
crash/restart/recovery. Four current-guard removal mutants fail the intended
invariant; historical votes remain intact. This is a serialized Phase6 suffix,
not full lifecycle or public arithmetic-witness refinement.

Pinned parsing, 22 safety configs, 7 liveness configs, 18 production mutants and
72 tooling tests pass. The 9 legal / 31 illegal traces regenerate under version
1.1.0, candidate ID `f57b27a2feae0328e1ecf0c8d14b0a041eef260231a26958647af41303caedda`.
Trace/reproduction tools read the registry version; the exact frozen baseline
remains required and intentionally unchanged. Phase zero still fails. No native
guard removed, no independent attestations and no Formal GO. Evidence:
`formal/proposals/evidence/current-binding.json`, TLC report and four retained
production counterexample fixtures. Next formal work remains the production
witness, heterogeneous arithmetic and parametric proofs listed above.

The user additionally requested connected Admin/Presentation workflows with
a shared disk-backed local profile (accounts later). That presentation work
continues in the separate presentation worktree; keep baseline c8aea649 intact.

## September 24: parametric ordered arithmetic kernel

T044/T048/T049: added PO-A4 to the mandatory proof imports, registry, coverage,
normative obligation and axiom audit. `ArithmeticKernel.lean` proves soundness,
completeness and exact rejection of checked accumulation over arbitrary ordered
integer lists. Product and accumulator widths are independent; quantum
conversion separately checks intermediate and output widths. The kernel includes
INT64_MIN, signed half ties, intermediate overflow hidden by cancellation and
the per-domain-rounding counterexample. This is integer reasoning, not an
artifact decoder, coefficient derivation or PO-AB1 discharge.

All 13 registered statements compiled with pinned Lean 4.32.1/Std and only the
declared standard axioms. Five source mutations fail the original proofs, and
five separate concrete counterexample theorems compile. The runner verifies the
locked compiler archive and that the executable matches its archive member.
Evidence: `formal/proposals/evidence/arithmetic-kernel.json`. No new TLA action
or production runtime was changed; the earlier finite-model evidence keeps its
original scope.

The 72 formal tooling tests and regenerated 9 legal / 31 illegal trace fixtures
pass. The trace witnesses still do not establish arithmetic input binding.
The full proof audit does not pass: PO-AB1's four production theorems remain
absent, this worktree has no materialized mathlib/Lake package cache, and the
default `lake` executable is not on PATH. The scoped check uses the explicit
pinned executable and does not claim the full project was built. `make` is also
not on PATH; its first mandatory `formal-phase0` command was run directly and
still fails on the intentionally unfrozen amendment inputs. No baseline hashes
were changed to hide that STOP.

Report generation now runs phase zero before setting `baseline_inputs.verified`;
previously it unconditionally wrote true. The new report must record false and
NO_GO. Candidate semantics change with the imported proof source, so fixtures
and the report receive a new ID; the historical cc98f15a authority remains
inapplicable. No independent review, merged Formal GO, native guard removal,
qualifying ResultQC or GO checkpoint is claimed.

Next: bind concrete authoritative bytes and native pre-state into the public
witness/schema and prove the remaining PO-AB1 conjuncts, extend heterogeneous
TLA arithmetic, materialize/verify the pinned full proof environment, then
refreeze only complete reviewed contracts and run the complete formal gate.
The presentation services and current public tunnel were kept running unchanged.

Current candidate semantics:
`sha256:a9dafb262dd89c327272cc4a2376392c2f378cd3ce1deffa0c7153053ca56a34`.
The report verifier accepts the canonical NO_GO report without errors; this
verifies report integrity and its negative decision, not completion of the gates.

## September 24: full project proof environment and fail-closed source cache

T005/T006/T049: materialized all nine exact locked dependency source checkouts
on C:, verified their clean trees, upstream URLs/revisions, license hashes,
mathlib manifest and Lean toolchain. The source preparation command requires
explicit `--download`; ordinary verification, the proof runner and the axiom
audit reject missing or modified sources before Lake can fetch them. Existing
checkouts are never reset or repaired. Lake runs with `--no-cache`.

The first explicit mathlib cache attempt against the official master container
found 0 of 937 entries; the official master/legacy chain then retrieved all 937.
These upstream CI artifacts are not independently reproduced or authenticated
by our source verifier. With pinned Lean/Lake 4.32.1, the complete current
`DeltaReduce` import bundle built successfully (961 jobs). The real mandatory
proof gate then verified 41 of 45 registered conjuncts using only the allowed
kernel axioms. It still fails on the four missing PO-AB1 theorems: native byte
graph uniqueness, PARAMETER conversion, APPLY result and admission/recovery
refinement. No placeholder or waived obligation was added.

Evidence: `formal/proposals/evidence/proof-environment.json` and retained setup,
build, audit and test logs under `formal/proposals/evidence/proof-environment/`.
The 84 formal tooling tests pass, including twelve cache-verification tests.
This is connected Windows development evidence, not the required clean offline
Linux reproduction or an independent review. Existing TLA/public witness and
phase-zero gaps remain. Formal semantics bytes did not change in this tooling
stage; candidate ID stays `a9dafb26...`. The regenerated report stays NO_GO.

No native guard, application service or tunnel was changed. Next implement the
production byte/witness contracts and the four missing PO-AB1 conjuncts, extend
heterogeneous TLA arithmetic, and refreeze only the complete reviewed contracts.
The missing local mathlib environment is no longer the reason for the proof STOP.


## September 24, 09:06 UTC continuation: heterogeneous arithmetic and liveness STOP

T029/T031/T050/T057: generalized the production arithmetic abstraction from
uniform scalar inputs to explicit ordered ticket/domain maps, rational weights,
per-domain/per-shard quantum, unequal domain mixture weights and separate parent
model/optimizer coordinates. Four new finite configurations use four validators,
f=1, four tickets, two domains and two one-coordinate shards. The positive
serialized Phase6 suffix persists/transports/finalizes four PARAMETER QCs plus
root/APPLY QCs, advances current and executes crash/restart/recovery/replay.
Independent expected literals are N=(3,16,-1,-3), model=(19,-22), optimizer=(2,1).
Negative configurations reject product overflow, intermediate prefix overflow
hidden by cancellation and conversion overflow before the forbidden state/vote.

Pinned SANY parsing, all 26 safety configurations, 23 production-source mutants,
91 tooling tests, 9 legal / 31 illegal public trace fixtures and the independent
Python mathematical oracle pass. The five new production mutations remove the
product/prefix/conversion checks, replace unequal mixture weights or change
rounding order. A first fixture did not distinguish equal and unequal weights;
the second coordinate was corrected and the actual mixture mutant then failed
with the intended complete counterexample. The mutant runner needs an explicit
16 MiB JVM stack to retain complete nested-record counterexample traces; partial
trace output was correctly rejected, not counted as a kill.

The complete config-to-APPLIED liveness configuration now times out after the
unchanged 600-second limit. Fairness and required properties were not weakened.
Diagnostics show expensive TLC ENABLED expansion of the full progress relation;
this is an evaluation regression requiring investigation, not a proof that the
protocol is live or a demonstrated protocol counterexample. The native-arithmetic
full-chain case completed with 42 states in about five minutes. Six of seven
liveness configurations pass; the zero-input full-chain case remains timed out. No-fairness removal still produces the intended temporal violation.
This is an unconditional formal STOP. Do not claim all seven liveness configs pass.

During failure review, the gate runner was found to retain an older PASS log if a
new run timed out or failed before writing output. It now invalidates every log
in the selected gate before the first process, captures nonzero/timeout output,
and marks incomplete runs. Five regression tests cover old PASS reuse, partial
success text followed by failure, launch failure and normal success. The report
coverage calculation also requires the complete registered TLC config set and
a successful aggregate status. Prior successful logs were removed from current
candidate evidence; retained historical checkpoints keep their original scope.
A separate log parser issue surfaced on the five-minute native run: the pinned
TLC emits a two-line coverage-overhead terminator instead of the short form.
The exact string was verified in the pinned jar's MP.class, and the parser now
accepts that complete form while rejecting truncation (two additional tests).
Reprocessing the retained actual output then validated its complete coverage.

The complete pinned Lean project builds (961 jobs), but the proof audit still
verifies only 41/45 conjuncts: four PO-AB1 binding/recovery theorems remain absent.
The frozen phase-zero baseline was not rewritten to hide incomplete contracts.
Byte graph decoding, arbitrary vector refinement, public arithmetic witnesses,
all interleavings/crash cuts, clean offline Linux reproduction and independent
review remain open. This finite model is not native conformance or Gate A/B/C/D.

Evidence: `formal/proposals/evidence/heterogeneous-arithmetic.json` plus retained
logs and counterexamples. New candidate semantics:
`sha256:ec55655fc564a46108b7062a4ca9cb780fd96322a49fd0faf61f474a868b5866`.
A canonical NO_GO report must bind the clean source checkpoint; old cc98f15a and
a9dafb26 reports do not authorize this changed model. No native guard was removed.

Presentation 8870, Controller 8865 and node training 8872 stayed on the same live
instances. The current Cloudflare host still returns the access-code login page
for Presentation, Admin and node-training routes. This read-only check is not a
new authenticated browser run. No demonstration source, service or tunnel changed.

Next concrete stage: resolve TLC's full-chain fairness evaluation regression
without reducing the required scope or changing the fairness assumption, rerun
both complete liveness configurations, then continue production byte/witness
contracts and the four PO-AB1 proofs. Only after complete reviewed formal authority
may native arithmetic admission change.


## September 24, 10:07 UTC continuation: full liveness restored

T041/T042/T059/T057: resolved the zero-input full-chain TLC timeout without
changing the production actions, formulas, checked bounds, fairness expression,
temporal properties, configured populations or the 600-second limit. The old
ABApply formula is now named ABApplyEvaluated. Its public wrapper uses singleton
function application `[v \in {g} |-> F(v)][g] = F(g)` to bind the computed integer
gradient. ABApplyChecked binds the sole complete result record before checking
every intermediate index. This prevents repeated expansion of the arithmetic
lineage by TLC ENABLED; no arithmetic guard or observable transition is removed.

All 26 safety configurations, all 7 liveness configurations, the no-fairness
countercheck, all 23 production mutants, pinned SANY parsing, 91 tooling tests
and 9 legal / 31 illegal trace fixtures pass. The mandatory zero-input and
nonzero full-chain temporal checks each reach 42 states; this execution took
63 and 19 seconds respectively. These are diagnostic TLC durations, not runtime
benchmark measurements. The earlier 600-second failure remains in its historical
checkpoint and is superseded, not erased.

Supplemental `check_arithmetic_evaluation.py` snapshots exact base source
`9a45110891e06613bb9dd8426a4425e6e63ee796` and current TLA modules. It executes
Init/Next plus invariants for both full-chain profiles and compares complete DOT
state/transition dumps byte-for-byte. Both graphs are identical, including state
values (42 states each); the only changed model module is DeltaReduceArithmetic.
The diagnostic copies omit temporal properties, so this comparison cannot
qualify liveness. Actual mandatory liveness is executed separately with unchanged
WF and property declarations. The matched graphs are retained as lossless gzip
artifacts with the original byte hashes. Evidence:
`formal/proposals/evidence/arithmetic-evaluation.json` and
`formal/proposals/evidence/liveness-recovery.json`.

The first parallel safety attempt encountered a TLC parser NullPointerException
while reading standard modules from the shared Windows temp directory. No
protocol counterexample was produced. Concurrent module extraction is a suspected
cause, not established proof of causality. That failed log is retained; the entire
safety gate was rerun alone and passed. Until per-process temp isolation is added,
run TLC gate families sequentially on this Windows development environment.

The full pinned Lean project still builds (961 jobs); mandatory audit still stops
at 41/45 conjuncts because four PO-AB1 theorems are absent. Phase zero still fails
on intentionally unfrozen/incomplete amendment contracts. No independent review,
clean offline Linux reproduction, concrete native byte graph or complete public
arithmetic witness is claimed. No native guard, runtime source or demo service
was changed. The new candidate ID is:
`sha256:61b4b0553d044e09392979c59e5d497e4631a8c4f75d7127623e8444b14718f9`.
The resulting FormalVerificationReport remains NO_GO.

Next concrete stage: promote the draft canonical byte graph into explicit public
trace/native-state witness contracts and the refinement checker, with mutation
cases for substituted/missing/rehashed artifacts. Prove the actual four PO-AB1
statements against those production contracts; do not replace them with trivial
helpers. Then complete reviewed contract freezing and clean reproduction. Only
merged Formal GO can authorize PR50 native arithmetic admission.

Presentation, Controller and node-training retained the same healthy process
instances and the existing Cloudflare URL. Baseline c8aea649 and presentation
worktree remained clean; saved results/receipts were not modified.

## September 24, 11:07 UTC continuation: public native arithmetic witness

T053/T054/T055/T056/T057: accepted PARAMETER/APPLY first votes now require an
explicit public arithmetic witness. The verifier takes native snapshots and
their SHA256 separately from the trace; it cannot construct authority from the
vote command. Snapshot IDs bind actor, native pre-state root, round-contract ID,
action/context, current checkpoint, sequence and recovered arithmetic anchor.
The exact command and typed input artifact graph are decoded, rehashed and
recomputed through the candidate byte oracle. Native context, role, deadline,
domain/shard coverage, model/optimizer hashes and finalized parent projection
are checked before accepting the public vote observation.

Twenty-one new public negative cases reject missing bytes/witnesses, snapshot
substitution, wrong actor/state/sequence/role/current/optimizer, rehashed parent
model/optimizer, rehashed PARAMETER/APPLY results, altered certificate projection
and malformed/noncanonical commands. Result mutations also recompute the model
value hash and entire body hash, so self-consistent caller hashes are insufficient.
Each negative must fail for its registered reason. The new positive recovered
trace executes crash/restart/journal recovery before arithmetic votes. Self-review
also caught reused sequence numbers in old synthetic fixtures: fixture votes now
use increasing per-actor sequences and native admission rejects sequence reuse.

Validation: 10 legal / 52 illegal public traces, 99 formal tooling tests, 38
arithmetic/byte-oracle tests and targeted Ruff checks pass. Phase zero intentionally
remains FAIL for unfrozen amendment contracts. The pinned liveness checkpoint's
27 TLA/Lean semantic input hashes are unchanged; TLC/Lean were not rerun for this
public-schema-only semantic change. Prior executed model/mutant/proof evidence
retains that scope. Candidate semantics is now
`sha256:f0f77dc58b60fe1a58075c87b3b0a22ad746a717bbcb49dfff3995c8b300da3c`.
The new source-bound report remains NO_GO, with explicit native trust limitations.

Scope remains first-vote offline projection, not authenticated native production.
The separate evidence digest fixes bytes but does not prove where they came from.
Checked-in native snapshots/manifest are synthetic fixtures, not attestations.
Arbitrary schema-coordinate mapping, trusted real native export, exact durable
receipt/effect/retry identity (including retry after current advances), rejected
stutter and every crash cut still need binding. The four substantive PO-AB1
proofs, frozen contracts, clean reproduction and independent reviews stay open.
No native guard or implementation under 001-011 was changed.

Next concrete stage: bind the concrete schema coordinates and the persist/retry
receipt witness to the same public/native relation, with stale-current and
post-recovery replay negatives; then prove the actual PO-AB1 conjuncts. Do not
replace these obligations with a pure-function determinism helper or a green
fixture count. Evidence: `formal/proposals/evidence/native-trace-witness.json`.

Presentation 8870, Controller 8865 and node training 8872 retained their healthy
instances. The same Cloudflare URL returns HTTP 200/access-code login. This is
a read-only reachability check, not a fresh authenticated browser execution.
The baseline/presentation worktrees and saved receipts/results remain unchanged.

## September 24, 12:07 UTC continuation: concrete schema coordinates

T053/T054/T055/T056/T057: the public parameter-schema hash now binds exact
ordered scalar `coordinates` and `ranges` mapping every parameter obligation ID
to its offset/length. The old parameter IDs are obligation labels; concrete
scalar IDs are a separate shared vector. Every domain must partition that entire
vector exactly once, with no gap/overlap, no duplicate domain/shard key and no
shard ID aliasing different intervals across domains. Range checks use bounded
integers and interval sweeps, not expansion of arbitrarily repeated ranges.

`coordinate_projection.py` constructs the unique native SCHEMA payload from the
immutable contract. Its complete canonical bytes must match the SCHEMA resolved
from the separately pinned native authority graph. Parent model/optimizer and
q-shard schema references remain checked by the byte oracle. Neither observed
vote coverage nor rehashed caller metadata establishes coordinate authority.

The new positive full public trace uses three domains, six parameter keys, two
shards of lengths 2 and 3, five coordinates and 21 arithmetic votes. Its separately
derived expected model is `[19,-20,19,-19,19]` and optimizer `[2,-1,2,-2,2]`.
Eleven new negative public traces cover order, missing range, out-of-bounds,
overlap/gap, cross-domain alias, duplicate domain/shard and native/public schema
substitutions. Native substitutions rehash every graph edge and recompute all
PARAMETER/APPLY bodies, dependent aggregates and result hashes. They fail the
specific binding guard rather than an incidental stale hash. Three deliberate
in-process removals of that production Python guard make those otherwise
self-consistent traces pass, establishing this boundary check's non-vacuity.

Validation: 11 legal / 63 illegal public traces, 106 formal tooling tests,
38 arithmetic/byte-oracle tests, targeted Ruff and byte-exact fixture regeneration
pass. Phase zero remains FAIL for the unfrozen amendment. All 27 TLA/Lean semantic
artifact hashes match the previous checkpoint; those tools were not rerun for
this public-schema/checker change. The previous finite TLC/mutant/proof evidence
is retained with its original scope. Candidate semantics is now
`sha256:8dd92208f268b51cce468b69b470ad054d7352f62d35ea8b05e6d2b9f9fd1924`.
The new source-bound report remains NO_GO.

This closes the executable coordinate projection for the candidate's flattened
vectors under the existing 4096-item witness bound and contiguous shared shards.
It does not prove arbitrary vector lengths, native framework/tensor/QLoRA adapter
decoding or frozen-base identity. The TLC model still abstracts one coordinate
per shard. Native snapshot provenance, WAL/effect/receipt/retry identity, rejected
stutter, every crash cut, all four PO-AB1 conjuncts, contract freeze, clean offline
reproduction and independent reviews remain open. No runtime implementation,
arithmetic admission guard, benchmark gate or GO checkpoint changed.

Next concrete stage: bind persist/retry receipt evidence to the same public/native
relation, including identical retries after current advances and after recovery,
conflicting canonical bytes and rejection without append/effect. Then discharge
the actual PO-AB1 proof statements against these contracts, not a generic pure
function determinism lemma. Evidence: `formal/proposals/evidence/coordinate-binding.json`.

Presentation, baseline Controller and node-training retain the same healthy
instances. The unchanged Cloudflare URL responds HTTP 200 with the access-code
login page. Baseline/presentation repositories and saved receipts were untouched;
no fresh authenticated demonstration execution is claimed for this heartbeat.

## September 24 continuation: draft durable receipt and retry projection

T053/T054/T055/T056/T057: pinned evidence now includes content-addressed operation
observations. The checker reconstructs each actor's observed vote prefix from an
empty journal, checks exact sequence increments, rejects duplicate appends and
binds validation/append/barrier/commit/expose ordering to canonical diagnostic
receipt/effect bytes. A retry's original receipt sequence is distinct from the
current journal tip (positive vector: 5 versus 8).

Two new legal traces exercise PARAMETER retry before current advance and both
PARAMETER/APPLY retry after advance, crash/restart/recovery, a conflicting
canonical command and another successful exact retry. Replays preserve original
receipt/effect bytes and allocate no new sequence. Conflict uses existing
REJECTED plus state/journal stutter, with no receipt, effect, result or artifact.
Rejected recovery cannot enable replay. Successful recovery binds the same
complete observed journal prefix.

Twenty-five new negative fixtures mutate ordering, receipts/effects, canonical
bytes, prior/next prefixes, sequence, recovery readiness, stutter and conflict
writes. Rehashed observations fail for their intended reason. Three deliberate
Python guard removals admit otherwise-consistent mutants; these are not new TLA
production mutants or independent attestations.

Validation: 115 formal tooling tests, 38 arithmetic/byte-oracle tests, 13 legal /
88 illegal traces (57 native negative cases), targeted Ruff and byte-exact
fixture regeneration PASS. All 27 TLA/Lean semantic input hashes are unchanged
from 95941efbf2f1ba263079506423c6c62f85068bab. No new TLC/Lean execution is claimed;
prior finite model/proof evidence retains its scope. Candidate semantics is now
`sha256:bef672fb02621f6a498889b051998c41ab8949e14fc70ac889b378c62e3c8056`.
Phase zero still fails for the unfrozen amendment. The source-bound formal
report remains NO_GO. Evidence: `formal/proposals/evidence/durable-retry.json`.

The receipt/effect encoding is a draft diagnostic projection, not production
WAL/C ABI. Stage observations do not prove fsync. Native exporter/provenance,
initial snapshots, torn writes, failed barriers, persist-without-expose cuts,
non-conflict first-admission rejections, and four PO-AB1 proofs remain open.
No runtime implementation, arithmetic guard, qualifying gate or GO checkpoint
was changed. Contract freeze, clean reproduction and independent review remain
required; a fixture count cannot substitute for these obligations.

Next concrete stage: model and bind crash cuts between arithmetic admission,
append, durability, state commit and exposure, including failed barriers and
recovery of persisted but unexposed receipts. Then prove the actual PO-AB1
conjuncts against the complete contract.

Presentation 8870, Controller 8865 and node-training 8872 retain their healthy
instances. The same Cloudflare origin responds HTTP 200 with the access-code
login page. Both demo worktrees remain clean; saved receipts/results are intact.
This read-only health check is not a fresh authenticated UI execution or a
qualifying Feature010 run.


## September 24 continuation: persistence crash-cut model

T015/T016/T018/T042/T050/T051/T052/T057/T058/T059/T061: the candidate now has a
persistence suffix using production PARAMETER/APPLY vote, send, crash, restart
and recovery actions. The two new mandatory configurations explore uninterrupted
execution and cuts after validation, append, durability, commit and exposure,
plus barrier failure and a corrupt/torn append. An unacknowledged append or failed
barrier may leave either no record or the original complete record. Both branches
remain unable to expose a result before verified recovery. Surviving votes retain
the original receipt tuple and sequence; replay allocates no second record.
Corrupt recovery stays unready. Only DONE/BLOCKED local terminal stages explicitly
stutter, so an accidental dead end elsewhere fails TLC.

Validation: parser, all 28 safety and 7 liveness configurations (plus the existing
no-fairness countercheck), all 27 production mutants, 115 formal tooling tests,
38 arithmetic/byte-oracle tests, 13 legal / 88 illegal public traces, fixture
regeneration and targeted Ruff PASS. Both new configurations reach all 21 required
actions: PARAMETER has 100 distinct states, APPLY 276. Four new production mutations
change sequence increments or remove volatile restoration in RecoverJournal.
Two separate candidate-harness counterchecks detect exposure before commit and
corrupt recovery becoming READY; these are not production-source mutations.

All 27 prior TLA/Lean inputs and the public schema remain unchanged; the new
harness adds one semantic input. Candidate semantics is now
`sha256:eacc55df055cf3743d58604885334f06e4bb38af6c5f389ae15a2fc5064fbc87`.
Nine Lean source files match the previous checkpoint; no new Lean execution is
claimed. The retained proof audit still verifies 41/45 conjuncts, with all four
PO-AB1 targets missing. Phase zero still fails for the unfrozen amendment/version
and invariant registry. The report remains NO_GO. Evidence and exact limitations:
`formal/proposals/evidence/persistence-crash-cuts.json`.

Scope: one validator/fault, one scalar coordinate/shard, a serialized certified
suffix and no concurrent current changes. Receipt tuples are an abstraction, not
production bytes. This finite model does not establish disk/fsync behavior,
physical crash injection, arbitrary initial snapshots, native exporter provenance
or the public/native refinement for persisted-but-unexposed operations. No new
protocol action/outcome, native runtime implementation, arithmetic admission guard,
benchmark qualification or GO checkpoint was introduced.

Next concrete stage: extend the pinned public/native witness to represent and
verify incomplete operations and ambiguous durability outcomes against this model,
without equating a missing response with a missing durable vote. Bind recovery
of the exact persisted bytes and rejection without append, then discharge the
substantive PO-AB1 graph/conversion/Apply/recovery proofs. Contract freeze, clean
offline reproduction and independent review remain required for Formal GO.

The user no longer needs a demonstration today. Frozen Git demo refs and saved
receipts/results remain intact; the idle presentation services were left as a
reserve. No new demonstration, training or external qualification run is claimed.

## September 24 continuation: persisted-but-unexposed public witnesses

T053/T054/T055/T056/T057: evidence container 1.2.0 now binds complete persisted
arithmetic records whose receipt/effect has not yet been returned. PARAMETER and
APPLY each have four synthetic legal cuts: DURABLE, COMMITTED, complete append
without acknowledgement, and complete append surviving a failed barrier. The
first accepted event represents the internal durable vote, not an API response.
Its output is null. Crash/restart/verified recovery retains the original command,
receipt/effect bytes and sequence; exact retry exposes them without another append.
Unacknowledged presence requires subsequent verified recovery and is never
inferred from a missing response alone. An acknowledged durable prefix may remain
incomplete without being mistaken for an absent record.

The public checker excludes unexposed votes from quorum counts. Validated exact
replay can expose the old vote once; duplicate replays cannot add signer power.
Nine additional negative traces check early output, invalid stages, premature
quorum use, retry before crash, unverified surviving records, recovery truncation
and modified replay bytes. Three deliberate Python guard removals admit otherwise
consistent invalid traces. They are separately scoped checker counterchecks,
not TLA production mutations or independent attestations.

Validation: 121 formal tooling tests, 38 arithmetic/byte-oracle tests, 21 legal /
97 illegal traces (66 native negative cases), targeted Ruff and byte-exact
regeneration of 238 fixture files PASS. All 28 TLA/Lean semantic inputs match
631d95ca8592f1a035042ec936b61878d2b52278. No new TLC/Lean execution is claimed;
the retained 28 safety/7 liveness/27 production-mutant results keep their original
finite scope. The retained Lean audit remains 41/45 with four PO-AB1 targets
missing. The public schema changes the candidate semantics ID to
`sha256:3b43d64af4833f7b315211f6bce4e16d4734e844948280e8f1411fd86006437b`.
Phase zero still fails for the unfrozen amendment. The formal report remains
NO_GO. Evidence: `formal/proposals/evidence/persisted-unexposed.json`.

Self-review checked that observation identity alone supplies no authenticity,
that only a fully checked replay can contribute signer power, and that an
unacknowledged write cannot pass without recovery of the exact prefix. The
diagnostic byte layout remains separate from production WAL/C ABI. This stage
does not implement native recovery or prove physical fsync, and does not close
the complete crash-cut refinement obligation or any PO-AB1 proof.

Next concrete stage: bind absent/torn/unknown durability outcomes and rejected
first admission to the public/native witness without inventing durable presence,
absence or append. Preserve fail-closed recovery, then discharge the substantive
PO-AB1 graph/conversion/Apply/recovery proofs. Native exporter provenance,
production WAL bytes, initial snapshots, contract freeze, clean reproduction
and independent review remain required before Formal GO. Runtime arithmetic
guards and Feature010 qualification remain unchanged.

Presentation 8870, Controller 8865 and node-training 8872/node-training/ answered
HTTP 200. Their idle instances and frozen Git snapshots were preserved. This was
a read-only health check, not a fresh demo, GPU run or authenticated tunnel test.

## September 24 continuation: unknown append outcomes and first-result rejection

T053/T054/T055/T056/T057: evidence container 1.3.0 now distinguishes a rejected
first arithmetic result from a valid command interrupted during append. A rejected
result requires full native anchor/graph/contract binding and the specific
ARITHMETIC_RESULT_MISMATCH from recomputation. It produces no append, receipt,
effect or state change. A valid command or an invalid native snapshot cannot be
used as the reason. A following correct command receives the original next
sequence. Other first-admission failures remain outside this narrow projection.

Interrupted append and failed-barrier observations keep the post-journal and
sequence unknown (null). Missing output does not establish absence. The owner's
next action must be crash; subsequent supported operations are restart/recovery.
A verified absent scan binds the exact last known prefix before fresh admission.
Corrupt and ambiguous scans remain unready, with no repair/truncation transition
in this bounded scope. Incomplete traces preserve an explicit unresolved count.
The old prefix at scan entry is the last verified prefix, not a claim about all
physical bytes. A passing incomplete prefix is not a total concrete-state
abstraction, successful run or completed refinement proof. Complete surviving
records still require the separately pinned retrospective v1.2 projection.

Validation: 127 formal tooling tests, 38 arithmetic/byte-oracle tests, 33 legal /
112 illegal traces (81 native negative cases), Ruff and byte-exact regeneration
of 292 fixture JSON files PASS. Twelve legal and fifteen negative cases are new.
Three separate Python guard removals admit false rejection, false knowledge of
the journal and promotion from a blocked scan; they are not TLA production mutants.
All 28 TLA/Lean semantic inputs match 63510eb7fad1d5f06625b1d225e91a8e57c228b0;
no new TLC/Lean run is claimed. Prior 28 safety/7 liveness/27 production-mutant
results retain their original finite scope, and the Lean audit remains 41/45.
The public schema changes the candidate semantics ID to
`sha256:52b39ab5a70ac3cbe826b5a14558e7f7774b2c8ea1f69b874b3f7583d70b5a22`.
Phase zero still fails for the unfrozen amendment; the report remains NO_GO.
Evidence: `formal/proposals/evidence/uncertain-append.json`.

Self-review retained explicit native provenance/certificate assumptions and
checked that uncertainty cannot become ordinary successful recovery, blocked
scans cannot become READY, a fresh admission is not mislabeled as replay, and
invalid anchors cannot justify rejection. Runtime code, arithmetic guards,
frozen demonstration refs and services are unchanged.

Next substantive stage: construct the mandatory PO-AB1 graph/conversion/Apply/
recovery proof layer, starting with independently anchored typed graph uniqueness.
Do not count pure-function reflexivity, assumed result equality or an assumed
uniqueness premise as the required proof. Complete native decoder/exporter/WAL
refinement, arbitrary admission failures, initial snapshots, frozen contracts,
clean offline reproduction and independent review remain open. No Feature010
qualifying gate or GO checkpoint is authorized by these fixture results.

## September 24 continuation: mandatory typed graph uniqueness proof

T044/T048/T049/T057/T060: `formal/proofs/DeltaReduce/ArithmeticBinding.lean`
now proves `nativeArithmeticGraphUnique`. Two independent stores resolving one
authenticated authority have identical complete ordered path domains and exact
bytes/typed payloads at every path. The proof covers recursively referenced Q
shards and fixes the authority, schema, profile, plan, eligibility/contribution
order, current model and optimizer by payload identity. It derives that result
from lookup/content/canonical/kind checks and path induction, not from assumed
graph/result equality or pure-function reflexivity.

The codec, hash collision resistance, independent anchor/recovery authentication
and parent certificate authentication are explicit premises. Concrete native
parser, role/time admission, state production and cross-field arithmetic validity
remain separate obligations. See `formal/proposals/native-graph-proof.md`.

Source-linked Lean examples contain the actual twelve canonical artifact byte
strings from the pinned synthetic native fixture, all eleven artifact kinds and
a complete Binding. The finite lookup codec's collision premise is checked over
its twelve accepted strings. Four kernel counterexamples reject missing Q data,
its incomplete parent graph, wrong kinds and substituted Q bytes. These examples
use synthetic trust and a finite decoder, not real certificates, general native
decoding, SHA-256 verification or production TLA mutants.

Validation: full Lean project build (963 jobs), fresh kernel checks and axiom
audit PASS. The main graph theorem depends only on the permitted kernel axiom
`propext`; named semantic/cryptographic premises remain theorem parameters.
Mandatory conjunct coverage advances from 41/45 to 42/45. The audit correctly
remains FAIL for PARAMETER conversion, APPLY uniqueness and recovery refinement.
132 tooling tests, 38 oracle tests, 33 legal / 112 illegal traces, targeted Ruff,
and byte-exact regeneration of 292 JSON files plus one Lean file PASS.

Candidate semantics:
`sha256:5497ab6e27349c75ab662338269ce77305959ab48018d135d7fd7b7243d6604b`.
Nineteen TLA modules and the public trace schema are unchanged. No fresh TLC
execution is claimed; retained 28 safety/7 liveness/27 production-mutant results
keep their earlier finite scopes. The normative contract freeze still fails, so
the source-bound report remains NO_GO. Machine evidence:
`formal/proposals/evidence/native-graph-proof.json`.

Self-review checked that graph identity is not confused with input validity,
the independent store is not assumed equal, all referenced ordered children are
required, and finite synthetic witnesses do not imply native authenticity.
There is no runtime, arithmetic guard, qualifying benchmark or frozen demo ref
change. Read-only health checks returned HTTP 200 for Presentation 8870,
Controller 8865 and node-training 8872/node-training/; none was restarted.

Next concrete stage: prove `nativeParameterConversionSound` over the typed
authority/plan/Q inputs and the already checked integer operation graph. It must
derive coefficients, ordered prefixes, exact domain/shard coverage and quantum
rounding from inputs, without assuming the expected result. Then discharge APPLY
and recovery, instantiate the native decoder/exporter/WAL relation, and complete
arbitrary admission failure/initial snapshot/repair coverage, contract freeze,
clean offline reproduction and independent review. Feature010 qualifying gates
remain stopped until exact merged Formal GO; external authorities/WAN/evaluator
quorum remain BLOCKED_EXTERNAL.

## September 24 continuation: checked PARAMETER vector arithmetic

T044/T048/T049/T057/T060: `ParameterKernel.lean` now derives coefficients from
raw reduced weights and the specific denominator, proves the exact division
identity, and checks coefficient-sum prefixes independently of coordinate sums.
It computes whole vectors in the original row order, rejecting shape mismatch,
input/product/prefix overflow and empty top-level inputs. Twelve helper theorems
prove accepted-result soundness, row-kernel completeness/rejection equivalence,
and exact projection of every present coordinate into the existing checked
scalar accumulator. Quantum conversion proves checked products, per-coordinate
rounding and unchanged vector length. No expected-result equality is assumed.

This is the arithmetic sublayer of PO-AB1, not the complete native PARAMETER
theorem. It deliberately has no ticket, commitment, domain/shard or canonical
body fields. The bridge from independently authenticated graph/plan/Q bytes to
exact eligible rows, full PARAMETER metadata and schema placement remains open.
The required `nativeParameterConversionSound` name is not supplied by a weaker
helper. Mandatory coverage therefore honestly remains 42/45, with PARAMETER,
APPLY and recovery targets still missing. Scope and commands:
`formal/proposals/parameter-kernel-proof.md`.

Validation: the full Lean project (965 jobs), fresh kernel checks, and axiom
audit PASS. The twelve helpers use only permitted `propext`/`Quot.sound` kernel
axioms. Kernel-checked oracle vectors cover 36 PARAMETER and 22 conversion cases,
including two source-linked native-fixture assignments, signed INT64/INT128,
nonunit quanta, noncanonical fractions, shape/empty inputs, unsafe prefixes with
safe final sums, coefficient-sum overflow with zero coordinates, and conversion
cancellation. These are not actual native runtime or TLA mutant executions.
136 tooling tests, 38 oracle tests, 33 legal/112 illegal traces, targeted Ruff,
and byte-exact regeneration of 293 JSON/two Lean files PASS.

Candidate semantics:
`sha256:8ad76fc75f5ba3e3b52f085774801c0307d873665b9be90fec67471ba7f869ae`.
Nineteen TLA modules, the public trace schema and the graph proof are unchanged.
No new TLC execution is claimed; retained 28 safety/7 liveness/27 production
mutant results keep their earlier finite scopes. The contract-freeze and full
proof gates remain failed, so the source-bound formal report remains NO_GO.
Evidence: `formal/proposals/evidence/parameter-kernel.json`.

Self-review checked asymmetric signed bounds, INT64 Q/weight limits under both
accumulator profiles, every coefficient/product/prefix, exact shape preservation,
the absence of fraction reduction after accumulation, and the separate native
metadata/eligibility obligations. No runtime or arithmetic admission guard was
changed. The three idle demos returned HTTP 200 and the frozen refs are unchanged.

Next concrete stage: connect these kernels to checked extraction of typed
authority/plan/eligible Q inputs in `ArithmeticBinding.lean`. Derive ticket order,
commitment equality, domain/shard/schema/quantum/length checks and full canonical
PARAMETER body metadata; then prove schema placement of conversion. Do not assume
row validity or expected-result equality to obtain the missing native theorem.
APPLY/recovery, native decoder/exporter/WAL refinement, contract freeze, clean
offline reproduction and independent review still follow before Formal GO.

## September 24 continuation: checked graph to PARAMETER body

T044/T048/T049/T057/T060: the mandatory `ArithmeticBinding.lean` project now
loads authority-bound schema/plan/ISC/EC/APC bytes and derives the selected
PARAMETER input rows. The loaders construct proofs of content identity, length,
canonical type, source origin and Q commitment/metadata/shape checks. They enforce
exact eligible ticket order and the full ordered domain/shard assignment matrix.
No command-supplied rows, expected body or repaired input is trusted.

The checked extractor computes the numerator vector with `ParameterKernel`,
retains the specific unreduced denominator and original leaf order, and derives
every typed expected-body field. Four helper theorems prove positional source
binding, no row omission/padding, body metadata/shape/prefix soundness and exact
per-coordinate refinement to the checked scalar accumulator. They apply to
arbitrary mathematical list lengths under the explicit codec/trust premises.

This completes the checked body extraction sublayer, not the full PARAMETER
conversion conjunct. Comparing all certified aggregate bodies, conversion and
final schema placement, canonical body serialization and the concrete native
decoder remain open. PARAMETER computation deliberately does not require later
conversion success. Role/time/admission and physical WAL behavior are not supplied
by a successful mathematical extractor. Mandatory coverage remains 42/45, with
`nativeParameterConversionSound`, `nativeApplyResultUnique` and
`nativeArithmeticRecoveryRefines` missing. Scope:
`formal/proposals/native-parameter-body-proof.md`.

Validation: full Lean build (965 jobs), fresh body/vector kernel checks and
axiom audit PASS. New proof dependencies are limited to permitted `propext`,
`Quot.sound` and `Classical.choice`; `loadPayload` has no axiom dependencies.
The twelve original artifact byte strings instantiate the checked frame and two
complete PARAMETER body comparisons against the proposal oracle. Twenty-one
additional negative kernel examples cover malformed graph/row references,
metadata, eligibility, schema coverage, assignment ordering and duplicate vote
contexts. They are finite synthetic witnesses, not native C++ executions or TLA
production-mutant results. The earlier four graph negatives and 36 PARAMETER/22
conversion arithmetic vectors remain. 136 tooling tests, 38 oracle tests,
33 legal/112 illegal traces, targeted Ruff and byte-exact regeneration of
293 JSON/two Lean files PASS.

Candidate semantics:
`sha256:8b986d240324f06913c2b94774fe07c4806c5b31b6e173745e51aacd7dc8ccc8`.
Only three Lean inputs changed; nineteen TLA modules and public schema are
unchanged. No fresh TLC execution is claimed; the retained 28 safety/7 liveness/
27 production-mutant results retain their finite scopes. Contract freeze and
full proof gates remain failed; FormalVerificationReport remains NO_GO.
Machine evidence: `formal/proposals/evidence/native-parameter-body.json`.

Self-review checked exact metadata equality, non-reduced plan denominator,
membership/ordering, current state/schema binding and separation of PARAMETER
from conversion. No new runtime behavior or arithmetic guard change is made.
All three idle demo services returned HTTP 200 without restart and their frozen
Git refs remain unchanged. Self-review is not independent attestation.

Next concrete stage: resolve the authenticated aggregate and check exact ordered
equality of every certified body against these independently derived bodies.
Connect their checked quantum conversions and prove exact schema-offset placement
for every domain coordinate; then discharge the complete PARAMETER conjunct.
Do not replace it with reflexive function equality or assumed valid rows. APPLY,
recovery, native decoder/exporter/WAL refinement, arbitrary admission failures,
initial snapshots/repair, contract freeze, clean reproduction and independent
review remain before new merged Formal GO. Feature010 qualification stays stopped
and real authorities/WAN/evaluator quorum remain BLOCKED_EXTERNAL.

## September 24 continuation: certified conversion and schema placement

T044/T048/T049/T057/T060: `nativeParameterConversionSound` is now present in
the mandatory Lean project and its axiom audit. Coverage advances from 42/45 to
43/45. This is the conditional mathematical PARAMETER/conversion conjunct;
`nativeApplyResultUnique` and `nativeArithmeticRecoveryRefines` are still missing,
and actual native decoder/serialization/admission refinement remains mandatory.

The pipeline derives every body in the exact native domain/shard matrix, resolves
the anchored authenticated aggregate and compares its complete ordered body
list before conversion. Each conversion preserves original quanta/denominator
and checked product/rounding order. A separate guard retains FULL_SIGNED_INT64
output even with INT128 accumulation. A valid PARAMETER can still precede a failed
conversion; conversion success is not a new PARAMETER vote precondition.

Placement uses source schema offsets and requires exactly one cell for every
domain coordinate. General proofs establish source row/shard/index binding,
prefix and conversion safety, exact vector shape/order, no gaps/duplicates and
no cells outside the declared domains/schema. The top-level theorem packages
these proved properties of the checked program; it does not assume expected
results or valid rows. Its named codec/hash/anchor/certificate/recovery premises
remain explicit. Scope: `formal/proposals/native-parameter-conversion-proof.md`.

Validation: the full Lean build (965 jobs), fresh kernel/axiom checks and the new
mandatory conjunct PASS. Overall Lean evidence remains FAIL for the two missing
targets. New dependencies use only permitted propext/Quot.sound/Classical.choice.
Seventeen additional finite kernel examples cover full certified conversion,
whole-body mismatches, schema-order placement and INT128-to-INT64 boundaries.
Three Python tests rehash incorrect certified numerators, fraction aliases and
ordering and require rejection before generating Lean output. 139 tooling tests,
38 oracle tests, 33 legal/112 illegal traces, Ruff and byte-exact regeneration of
293 JSON/two Lean files PASS. Finite lookup codecs/synthetic trust remain distinct
from actual native execution and TLA production-mutant qualification.

Candidate semantics:
`sha256:162412d26aa243bd034e04a0729f63cce15b12bc9798b8ea43cc2f7b6222f9cb`.
Four Lean inputs changed; nineteen TLA modules and public schema are unchanged.
No fresh TLC execution is claimed; retained 28 safety/7 liveness/27 production
mutant results keep their finite scopes. Contract freeze, clean reproduction
and independent reviews remain open, so the source-bound report is NO_GO.
Evidence: `formal/proposals/evidence/native-parameter-conversion.json`.

Self-review checked full body equality rather than numerator/hash-only matching,
output-width separation, rounding before mixture, source offset placement and
the distinction between mathematical soundness and native admission completeness.
All three idle demos returned HTTP 200 without restart; frozen refs are unchanged.
No native runtime, arithmetic guard or qualifying benchmark was modified.

Next concrete stage: derive checked domain mixture and optimizer operations from
these certified domain vectors and independently bound current model/optimizer,
then prove full typed APPLY/model/optimizer result identity. Read the exact
proposal/native operation widths and rounding sequence; do not silently widen
outputs or reuse caller-supplied result hashes. Recovery and concrete native
refinement, admission failures/initial snapshots/repair, contract freeze, clean
offline reproduction and independent review still precede merged Formal GO.

## September 24 continuation: checked APPLY operation kernel

T044/T048/T049/T057/T060: the mandatory Lean project now contains
`ApplyKernel.lean` and `ApplyKernelVectors.lean`. Nineteen helper theorems prove
least-common-denominator construction, ordered mixture products/prefixes,
optimizer operation order, full vector shape/bounds and uniqueness of checked
mathematical derivations. This does not discharge `nativeApplyResultUnique`:
native graph extraction and full expected body/hash binding are still required.
Mandatory coverage remains 43/45; APPLY and recovery conjuncts remain missing.

The program derives the LCM from reduced nonnegative domain weights and requires
exact normalization. It checks both product stages before each mixture prefix,
rounds the mixture once, then checks all twelve optimizer intermediates in the
frozen sequence. Original inputs, products, rounded values and both output
vectors must fit INT64 in the native profile, even when PARAMETER used INT128.
Zero learning rate does not bypass earlier overflow. Exact coordinate traversal
and shape proofs exclude missing domain values and list truncation. The native
bridge must independently derive the mathematical rows and current state; they
are not yet supplied by a proved native APPLY loader.

Thirty-two oracle/Lean cases include two complete pinned fixture computations,
the five-coordinate/three-domain graph, coprime weights, signed rounding and
endpoints, zero weights, noncanonical/unnormalized fractions, invalid shapes,
LCM/product/prefix overflow and optimizer overflow before division or zero step.
All execute with kernel `decide`. Five tooling tests verify exact reproduction
and rejection before output of substituted bytes, missing/stale optimizer and
a rehashed but incorrect certified aggregate. Fixture authentication/conversion
is performed by the proposal oracle, not by this Lean module or native C++.

Validation: full Lean build (967 jobs), fresh kernel checks and axiom audit PASS.
New proofs and proof-producing functions use only permitted propext/Quot.sound;
no new assumptions are declared. 144 tooling tests, 38 oracle tests, 33 legal and
112 illegal traces, targeted Ruff and exact regeneration of 294 JSON/three Lean
files PASS. Full formal authority is still blocked by the two missing native
proofs, unfrozen amendment contracts, concrete refinement/reproduction and
independent review. Self-review is not an independent attestation.

Candidate semantics:
`sha256:e2751f9ed6ee0a6bd26f14912e1a99ab6e09bfe9dbb9494153e96a6a92be3c8e`.
Two new Lean sources plus the project imports and axiom audit changed. All
nineteen TLA modules, the public schema and the previous native graph/conversion
proofs remain unchanged. No fresh TLC execution is claimed; retained 28 safety,
7 liveness and 27 production-mutant results retain their finite scopes. The new
source-bound FormalVerificationReport remains NO_GO. Machine evidence:
`formal/proposals/evidence/apply-kernel.json`; detailed scope and reproduction:
`formal/proposals/apply-kernel-proof.md`.

All three idle demo services returned HTTP 200 without restart. The frozen
presentation/controller/node-training tags still resolve to their original
commits. No native runtime, arithmetic guard or qualifying benchmark was changed.

Next concrete stage: connect `NativeConversion` to the APPLY kernel using exact
domain names/order and weights from the anchored profile, independently bound
current model/optimizer and fixed INT64 bounds. Construct all expected APPLY body
fields and next-state hashes from derived outputs and prove agreement across
independently anchored stores; do not assume row/result identity. Then discharge
native recovery and concrete decoder/exporter/WAL refinement. Arbitrary admission
failures, initial snapshots/repair, contract freeze, clean offline reproduction
and independent review still precede merged Formal GO. Feature010 qualification
remains stopped; real authorities/WAN/evaluator quorum remain BLOCKED_EXTERNAL.

## September 24 continuation: native APPLY body/byte identity

T044/T048/T049/T057/T060: the mandatory `nativeApplyResultUnique` conjunct now
passes kernel and axiom checks. Lean coverage advances to 44/45; only
`nativeArithmeticRecoveryRefines` is missing. This is the conditional formal
result, not an executed native runtime or permission to remove the arithmetic
guard. FormalVerificationReport remains NO_GO.

The proof compares independently resolved schema/plan/certificate payloads,
derives exact certified body equality at the anchored aggregate, then proves
conversion and schema placement agree across independent stores. Assignment and
partition lookup witnesses are retained from actual checked extraction; no new
selection behavior is added. Checked alignment preserves all domain names,
weights and coordinates before the existing INT64 APPLY kernel consumes the
bound current model, optimizer and coefficients. Input or result equality is
never supplied as a premise of the native theorem.

The checked program constructs every APPLY body field, exact PARAMETER body IDs,
next vectors and value hashes, then encodes the whole canonical body. Explicit
ASCII/decimal/lowercase-hex byte encoders use sorted keys and exact separators;
invalid identifier spelling or ID length rejects. The named `HashAdapter`
premise binds artifact and model/optimizer domains, NUL separators and ordered
decimal preimages. Actual SHA-256, canonical input decoder completeness and
native limits/allocation/admission remain separate refinement obligations.

Fourteen general helper theorems plus the mandatory conjunct are added, with
seventeen kernel examples for full pinned body/byte equality, PARAMETER encoding,
hash preimages, signed INT64/INT128 decimal endpoints and alignment/encoding
rejections. The finite fixture codec adds hashes for two output PARAMETER bodies
and the next-state vectors; input decoding/collision freedom remain scoped to
the same twelve input byte strings. This does not turn the synthetic fixture
into a native C++ or TLA production-mutant execution. The separate 32 APPLY and
36 PARAMETER/22 conversion kernel cases remain.

Validation: full Lean build (967 jobs), fresh body/vector kernel checks and axiom
audit PASS, with only permitted propext/Quot.sound/Classical.choice dependencies.
146 tooling tests, 38 oracle tests, 33 legal/112 illegal traces, targeted Ruff
and byte-exact regeneration of 294 JSON/three Lean files PASS. The aggregate
`make formal-check` is unavailable in this Windows environment; scoped checks
are recorded individually and phase0 still fails for the unfrozen amendment.
Two new tooling mutations require missing/stale optimizer input to reject
before generating Lean.

Candidate semantics:
`sha256:5b5d490fd3e273768042c47c90df9219388402d5afd870279dccb8acc1df00a6`.
ArithmeticBinding, NativeGraphVectors and AxiomAudit changed. The nineteen TLA
modules and public schema are unchanged; no fresh TLC execution is claimed.
Retained 28 safety/7 liveness/27 production-mutant results keep their finite
scopes. Evidence: `formal/proposals/evidence/native-apply.json`; detailed proof
scope and assumptions: `formal/proposals/native-apply-proof.md`.

Self-review checked actual lookup witnesses, whole certified-body comparison,
domain order, fixed INT64 mixture/optimizer operations, canonical field coverage
and exact hash preimages. It is not independent review. All three idle demos
returned HTTP 200 without restart and frozen tags remain unchanged.

Next concrete stage: prove `nativeArithmeticRecoveryRefines` against the pinned
public/native journal witnesses and persistence crash-cut semantics. Bind
PARAMETER/APPLY authority and exact canonical bytes to first admission without
append on rejection, persisted-but-unexposed receipt recovery, same-context retry
and conflict, and unknown durability outcomes. Missing response must not imply
absence of a durable vote; ambiguous/corrupt scans remain blocked. Do not assume
recovered-state equality or replace recovery with a reflexive snapshot lemma.
Then complete concrete native decoder/exporter/WAL refinement, arbitrary failures,
initial snapshots/repair, contract freeze, clean offline reproduction and
independent review before merged Formal GO. Feature010 qualification is still
stopped and external authorities/WAN/evaluator quorum remain BLOCKED_EXTERNAL.

## 2026-09-24 — Checked recovery replay kernel (T044/T048/T049/T057/T060)

Added `RecoveryKernel.lean` to the mandatory project. Twenty-six helper theorems
prove replay soundness/completeness against an independent history relation,
exact ordered record preservation, fresh sequence/no-duplicate checks, original
receipt/effect/sequence lookup after any accepted suffix, retry/conflict fencing,
and authenticated current-pointer compare-and-set/idempotent replay. This is an
actual recursive replay program; it does not assume a recovered snapshot equals
the old state. All three current pointers are retained by vote entries.

Pre-WAL preparation and exposure are separate: failed admission cannot produce
a pending record, and exposure needs ready mode, committed stage and the exact
saved record. One unknown append is resolved only by an authenticated, exact
whole-prefix presence or explicit absence claim followed by replay. An ordinary
old-prefix scan cannot imply absence; incomplete/corrupt/ambiguous recovery keeps
unknown sequence or stays blocked. No silent repair/truncation is introduced.

The adapter still supplies semantic admission, receipt/effect encoding and
certificate/scan authentication. These parameters have NOT yet been connected
to the full native binding and public witness encoders. Consequently this is
not `nativeArithmeticRecoveryRefines`: mandatory coverage remains 44/45, with
that conjunct missing. No runtime change or Formal GO is authorized.

Thirty-seven kernel-decide cases use the pinned diagnostic bytes of two PARAMETER
records (sequences 5/6) and one APPLY record (sequence 8), including replay after
current advancement and receipt/sequence/body mutation rejection. The five other
vote slots have explicitly synthetic empty receipt/effect bytes; Lean admission
uses a finite table checked by the Python oracle before generation. This is not
production native execution or general exporter authentication. Five tooling
tests also reject rehashed receipt/sequence corruption, absent outputs and a
missing current optimizer before emitting any proof/evidence output.

Validation: full Lean build (969 jobs), fresh recovery/vector kernel checks and
axiom audit PASS. The new helpers/examples use only permitted propext/Quot.sound;
six executable functions are audited too. 151 tooling tests, 38 oracle tests,
33 legal/112 illegal traces, targeted Ruff and byte-exact regeneration of 295 JSON
and four Lean files PASS. The Lean obligation checker still correctly fails for
the missing recovery conjunct. GNU make remains unavailable; these scoped checks
are not aggregate `make formal-check`. Phase0 remains failed for the unfrozen
amendment. Nineteen TLA modules and the public schema are unchanged; no fresh TLC
execution or new production mutant result is claimed. Retained 28 safety/
7 liveness/27 production-mutant results retain their previous bounded scopes.

Candidate semantics:
`sha256:444ae28886b5a8a18d14b4a71041a256f9a4e904ddaaaf68b87fee16536679d0`.
Evidence: `formal/proposals/evidence/recovery-kernel.json`; assumptions and scope:
`formal/proposals/recovery-kernel-proof.md`. Self-review inspected missing-response
ambiguity, exact receipt retention, old-parent retry, counterfeit scan rejection
and the explicit adapter gap; this is not independent review. All three demos
responded HTTP 200 without restart, and frozen tags remain unchanged.

Next concrete stage: connect the checked replay kernel to native PARAMETER/APPLY
binding in `ArithmeticBinding.lean`. Construct command/context/authority/body
data from independently anchored graph derivation, implement and bind the exact
public diagnostic effect/receipt encoding, and instantiate admission at the
then-current checkpoint/model/optimizer. Establish full record provenance and
the initial-prefix relation before using the replay lemmas. Connect authenticated
scan claims to the pinned public witnesses, retaining unknown/blocked modes and
all original bytes. Only then prove `nativeArithmeticRecoveryRefines`; a finite
table adapter or assumed admission correctness is not that theorem. Concrete
decoder/hash/exporter/WAL, arbitrary initial snapshots/failures/repair, contract
freeze, clean reproduction and independent review remain required thereafter.

## 2026-09-24 — Native-derived pre-WAL records (T044/T048/T049/T057/T060)

Continued under the user's explicit instruction to proceed autonomously. Fourteen
new helpers in `ArithmeticBinding.lean` connect independently anchored arithmetic
to complete internal vote records. First PARAMETER body uniqueness is now derived
across independent stores without an already certified aggregate. The checked
preparer derives either PARAMETER or APPLY, exact command/body/envelope/effect/
receipt bytes, independent authority and actor/context key, and native sequence
from the prior vote count. It rechecks current checkpoint/model/optimizer, ready
mode, validator/recovery flags, logical deadline, identifier/metadata/hash bounds,
absence of an old record and exact canonical request equality before preparation.
Missing graph, stale/unready state, mismatched bytes or an existing key reject.

Receipt encoders implement the public diagnostic JSON spelling and domain-separated
command/effect hash inputs. Full ASCII escaping matches Python, including control
characters and DEL. These are internal pre-WAL bytes, not sendable effects or a
new production WAL/C ABI. Native metadata provenance and sampled-time freshness
remain named trust-boundary obligations. General replay adapter instantiation,
complete record provenance and the initial-prefix relation are still open.
`nativeArithmeticRecoveryRefines` is therefore still missing: mandatory coverage
remains 44/45 and FormalVerificationReport remains NO_GO.

Forty-six kernel examples compute two PARAMETER records with no aggregate anchor
and one APPLY record from the actual pinned graph, match complete diagnostic
records at sequences 5, 6 and 8, and pass each through the replay step. Negative
cases cover changed command/current pointers, time/role/recovery, duplicates,
missing authority, context/projection/hash/metadata/sequence bounds. The finite
codec still accepts twelve input artifact strings; output hash samples now also
cover the APPLY body and diagnostic commands/effects. Synthetic metadata trust,
the finite replay adapter and earlier synthetic non-arithmetic prefix slots are
not production execution or an independent authentication proof.

Validation: full Lean build (970 jobs), fresh body/vector checks and axiom audit;
156 tooling/38 oracle tests, 33 legal/112 illegal traces, targeted Ruff and exact
regeneration of 296 JSON/five Lean files. The new layer audits fourteen helpers,
eleven functions and 46 kernel examples. The full obligation check still fails
for the missing native recovery conjunct. GNU make is unavailable; scoped checks
do not replace aggregate formal-check. Phase0 remains failed for the unfrozen
amendment. Nineteen TLA modules and public schema remain unchanged; no fresh TLC
or production-mutant execution is claimed. Earlier finite results retain scope.

Candidate semantics:
`sha256:94d92399a456ccc7496d9d029d6efdb6108085dd779eacab6c6155636d0d7423`.
Evidence: `formal/proposals/evidence/native-prewal.json`; detailed scope:
`formal/proposals/native-prewal-proof.md`. Self-review is not independent review.
No demo/runtime code or frozen demonstration ref was changed.

Next: instantiate the general recovery adapter from these proof-producing native
records, not a supplied `admitted` predicate or finite table. Bind the original
authenticated event metadata and exact encoder functions to every journal entry;
establish prefix provenance, ApplyQC current advancement and the public witness
scan relation. Preserve historical exact retry after current advances while
blocking fresh old-parent admission. Keep unknown/blocked scans unresolved until
their verified presence/absence condition holds. Only a substantive general proof
of this relation discharges `nativeArithmeticRecoveryRefines`. Concrete decoder/
hash/exporter/WAL, arbitrary failures/snapshots/repair, contract freeze, clean
reproduction and independent reviews still follow before merged Formal GO.

## 2026-09-24 — Native arithmetic replay adapter (T044/T048/T049/T057/T060)

`NativeReplay.lean` now instantiates replay admission/effect/receipt from the
native graph computations, rather than a Boolean arithmetic-admission predicate
or finite accepted-record table. The independent context resolver supplies
authenticated historical metadata and an optional graph; missing authority
rejects. Whole context/authority/command/body equality and all original fresh
state checks are enforced. Accepted replay yields a complete `NativePrepared`
witness and exact record equality, with original receipt/effect/sequence.

Checked ApplyQC replay recomputes the full APPLY body, compares the actual parent
and next model/optimizer hashes, then requires a separate authenticator for the
body/certificate/next-checkpoint tuple. Thirteen general helper theorems derive
native transition histories by replay induction, exact records from an empty
arithmetic journal, retry/conflict retention after current advance, stale first
admission rejection, and verified unknown-append presence/absence reconstruction.
The current-state equality is computed by replay, not an assumed recovered state.

Self-review found an adapter gap: the generic replay kernel previously required
total effect/receipt functions. Real encoder failure cannot safely be represented
as empty bytes. Both return `Option Bytes` now; preparation and replay require
successful exact encoding. Failure rejects without a pending record. Existing
kernel proofs and examples are rechecked under this partial encoding interface.
No protocol outcome, trace schema, TLA transition or production runtime changed.

Forty-two kernel examples execute the native adapter. They preserve the three
pinned records at original sequences 5/6/8 and separately replay an explicitly
arithmetic-only journal from empty state with sequences 1/2/3. The latter is not
the full public trace; its five non-arithmetic vote kinds remain unconnected.
Tests cover mutated record fields, failed encoders (including empty output),
QC current substitutions, stale parent, historical retry/conflict, unexposed
survival, verified absence, truncated scans and unknown/blocked recovery.
Input/hash samples and metadata/QC/scan trust remain finite/synthetic in examples.

Validation: full Lean build (972 jobs), fresh native replay/vector checks and
axiom audit; 161 tooling tests, 38 oracle tests, 33 legal/112 illegal traces,
targeted Ruff and byte-exact regeneration of 297 JSON/six Lean files. Thirteen
new helpers, six functions and 42 examples are axiom-audited. The full mandatory
check still fails at 44/45 for `nativeArithmeticRecoveryRefines`. GNU make is
unavailable; scoped checks do not replace `make formal-check`. Phase0 remains
failed for the unfrozen amendment. Nineteen TLA modules/public schema are
unchanged; no fresh TLC or new production-mutant execution is claimed.

Candidate semantics:
`sha256:ca0ce1437cd6aa3a41d6509df5b36d232cd7d2a36395410ef813557154987dc4`.
Evidence: `formal/proposals/evidence/native-replay.json`; exact scope and named
assumptions: `formal/proposals/native-replay-proof.md`. Formal authority remains
NO_GO. Demo services and frozen fallback refs are preserved.

Next concrete stage: connect this general arithmetic replay adapter to the full
public journal/witness projection, including original per-actor sequence and
every intervening non-arithmetic vote. Preserve action/context/envelope mapping,
ordered envelope-ID journal roots, authenticated original event snapshots,
current-advance/certificate exposure, unknown/null observations and exact scans.
Do not renumber the full public trace, assume its prefix equality, supply an
arithmetic admission flag or count the three-vote subhistory as complete native
recovery. The mandatory theorem must connect public vote admission and recovered
state through the same checked native relation. Concrete input decoding/hash/
exporter/WAL, arbitrary snapshots/failures/repair, contract freeze, clean offline
reproduction and independent review still follow before merged Formal GO.

## 2026-09-25 — Complete per-actor public vote journal (T044/T048/T049/T057/T060)

`PublicJournal.lean` connects native arithmetic replay to every original vote
slot, including CONFIG/ISC/EC/APC/ROOT. The normal validator-1 example replays all
eight votes from an empty journal and preserves native PARAMETER/APPLY records
at original sequences 5/6/8. It retains exact canonical envelopes, keys, order,
receipt/effect bytes and computed public envelope-ID journal roots. No full
public trace is renumbered. Current advancement leaves the journal unchanged.

Sixteen general helpers establish checked slot admission, native preparation
provenance, full-prefix sequence allocation, duplicate rejection, replay history,
exact slot/key retention and computed before/after observation roots. Arithmetic
admission rederives the bound result through NativeReplay; the other-action
authorization callback cannot bypass it. Non-arithmetic native receipts remain
absent because the current public witness does not project them. Their internal
admission-only context/count view is not persisted or exposed receipt evidence.

Forty-one kernel examples cover all eight encoded envelopes and nine prefix
roots, the full vote-slot replay, original native observations, missing/renumbered
prefixes, authorization bypass, missing graph, substituted bytes/body/actor,
duplicate context, wrong roots, unknown tips and incorrect exposure bytes.
Seventeen finite hash samples are not a general SHA implementation. Other-action
authorization in examples is a finite set from a source trace first validated
by the complete Python refinement checker; it is not a Lean phase/QC proof.
Six generator tests require exact reproduction or reject history/epoch/sequence
and rehashed root/receipt mutations before generating output.

This is still a vote-journal projection, not the full public event lifecycle.
Authenticated event snapshots/state roots, phase/role/QC availability, actual
exposure/barrier ordering, crash/restart and unknown presence/absence scan
reconstruction remain to be connected. `nativeArithmeticRecoveryRefines` stays
OPEN (44/45 mandatory conjuncts); Formal authority is NO_GO. Unknown/null output
must never be treated as proof that no durable vote exists.

Validation: full Lean build (974 jobs), fresh public-journal/vector kernel and
axiom checks; 167 tooling/38 oracle tests, 33 legal/112 illegal traces, targeted
Ruff and byte-exact regeneration of 298 JSON/seven Lean files. Twenty executable
functions, sixteen helpers and 41 examples are audited. Nineteen TLA modules and
the public schema are unchanged; no fresh TLC or production mutant execution is
claimed. Earlier 28 safety/7 liveness/27 production-mutant results retain their
bounded scope. GNU make remains unavailable; scoped checks do not replace the
aggregate formal-check. Phase0 remains failed for the unfrozen amendment.

Candidate semantics:
`sha256:7eec316735463e36bc7760ca844548a1faf6274482f6ff9d4304265cc78ef420`.
Evidence: `formal/proposals/evidence/public-journal.json`; assumptions and exact
scope: `formal/proposals/public-journal-proof.md`. All three demos returned HTTP
200 without restart; frozen fallback refs are unchanged. Self-review is not an
independent review, and no native runtime code or arithmetic guard changed.

Next: extend the all-vote journal with the actual public execution lifecycle,
preserving original per-actor sequences and independently authenticated event
snapshots. Connect non-arithmetic phase/QC admission, canonical public state-root
projection, exposure/SendVoteEnvelope, current advancement, crash/restart and
exact authenticated presence/absence scans. Unknown append/barrier stays unknown
until verified; corrupt/ambiguous scans remain blocked. Do not treat a supplied
exposure flag, other-action admission callback or a finite fixture hash table as
the missing proof. Then concrete bounded decoder/hash/exporter/WAL, admission
completeness, arbitrary snapshots/failures/repair, contract freeze, clean offline
reproduction and independent reviews remain before merged Formal GO.

## 2026-09-25 — All-vote persistence/recovery lifecycle (T044/T048/T049/T057/T060)

`PublicRecovery.lean` now checks ordered diagnostic stages and recovery readiness
on top of the complete public vote journal. First arithmetic observations still
execute the native graph/metadata/body/receipt admission checks. Only the exact
VALIDATED → APPENDED → DURABLE → COMMITTED → EXPOSED sequence can expose the first
receipt. Known unexposed cuts retain the original record but require crash,
restart and verified recovery before a retry can expose it. No vote or current
advance is enabled in the intervening states.

UNKNOWN/failed-barrier observations retain the candidate separately, preserve
the last known log/journal and return null post-tip/output. Authenticated scans
must bind the exact initial state, previous log, pending slot and scan. Verified
presence replays the full prior log plus the exact pending record; verified
absence replays exactly the previous log. An ordinary old-prefix scan cannot
infer absence. Replayed native computations determine all records/current
pointers; recovered-state equality is not supplied. Incomplete remains recovering,
corrupt/ambiguous blocks, and no implicit repair can restore readiness.

Twenty helpers and sixteen functions cover required crash/restart, exact stage
classification, unchanged known prefix under uncertainty, all-vote replay/history,
computed roots and no recovery output. Historical retry after current advance
returns the same original receipt/sequence; different command bytes conflict
without append. Forty-four kernel examples use fourteen independently checked
whole public/native fixtures, original arithmetic sequences 5/6/8 and exact
witness stage/root/output values. The normal four-vote prefix and full eight-vote
journal are constructed from empty state. Six generator tests reject rehashed
stage/output/root/absence/truncation mutations before producing new evidence.

Scan authentication is synthetic in examples. General unknown-presence and
explicit incomplete-scan examples are separately labeled mathematical cases:
the current public witnesses use retrospective accepted/unexposed projection
for complete surviving records and do not gain a new public UNKNOWN-to-presence
transition. The new layer does not establish full live-state/log reachability
against authenticated public snapshots, canonical public state roots or global
SendVoteEnvelope/QC power. Other-action phase/QC admission, concrete bounded
native decoder/hash/exporter/WAL, arbitrary initial snapshots/failures/repair,
contract freeze, clean offline reproduction and independent reviews remain open.
`nativeArithmeticRecoveryRefines` is still missing: mandatory 44/45, Formal NO_GO.

Validation: full Lean build (976 jobs), fresh lifecycle/vector kernel and axiom
checks; 173 tooling/38 oracle tests, 33 legal/112 illegal traces, targeted Ruff,
and byte-exact regeneration of 299 JSON/eight Lean files. Nineteen TLA modules
and the public schema are unchanged; no new TLC/production-mutant execution.
Retained 28 safety/7 liveness/27 mutant results keep their finite scope. GNU make
is unavailable, so scoped checks do not replace aggregate formal-check. Phase0
still fails for the unfrozen amendment. Production runtime/guards are unchanged.

Candidate semantics:
`sha256:8994c0461799528cab8c37cbcdb1bf8ed5afa63108179799571e7660ac183d84`.
Evidence: `formal/proposals/evidence/public-recovery.json`; exact scope:
`formal/proposals/public-recovery-proof.md`. All three demos returned HTTP 200
without restart, and frozen fallback refs remain unchanged. Self-review is not
an independent attestation.

Next: establish the reachable live-machine/log invariant from empty initialization
through these checked operations, then bind it to independently authenticated
public event snapshots and canonical state-root transitions. Connect existing
non-arithmetic phase/QC admission and actual exposure/global quorum eligibility;
retain original contexts/sequences and the separate known/unknown scan cases.
Only the full native/public refinement relation discharges the remaining recovery
conjunct; adapter booleans, fixture hashes or assumed state equality cannot do so.

## 2026-09-25 — Reachable live-machine/all-vote invariant (T044/T048/T049/T057/T060)

`PublicReachability.lean` derives one invariant from empty initialization through
actual successful persistence, other-vote, current-advance, crash, restart,
recovery and historical-retry calls. No invariant, recovered-state equality,
prefix equality or arithmetic-admission Boolean is a reachability premise.
The initial actor/current remains unchanged. Replaying the entire ordered log
produces exactly the current journal, including original all-vote slots,
arithmetic records and current pointers.

Thirty general helpers establish checked transition composition, exact slot
projection/provenance and native arithmetic preparation of every stored
arithmetic record, with its original receipt/effect and sequence. Every pending
candidate remains checked against the known journal and excludes ready mode.
Every exposed arithmetic slot is stored with a native record. Authenticated
presence/absence recovery is proven to extend the known log and preserve earlier
records; missing responses still do not imply absence. Incomplete/corrupt/ambiguous
scans keep the known prefix and cannot silently restore readiness.

Thirty additional example/composition proofs include two sequence helpers,
four kernel-decide crash/restart facts, full eight-vote/current-advance and
historical retry, known unexposed crash/recovery/retry, unknown presence/absence,
incomplete and blocked histories. Five unreachable-state counterchecks reject
ready-with-pending, early receipt, invented non-arithmetic native receipt,
deleted log and rewritten nonempty initial state. These reuse previous fixture
adapters and original sequences 5/6/8; no new native/public trace is claimed.
Unknown-to-presence and explicit incomplete scans remain mathematical cases.

All sixty new declarations pass the kernel axiom audit with only permitted
propext/Quot.sound/Classical.choice. Full Lean build: 978 jobs; fresh invariant
and composition checks PASS. 173 tooling/38 oracle tests, 33 legal/112 illegal
traces, targeted Ruff and byte-exact regeneration of 299 JSON/eight generated
Lean sources PASS. The two new Lean files are hand-authored proof sources.
Nineteen TLA modules/public schema and native witness bytes are unchanged;
145 public traces only change semantic ID. No fresh TLC/production-mutant run;
retained 28 safety/7 liveness/27 mutant results keep their bounded scope. GNU make
is unavailable; scoped checks do not replace aggregate formal-check. Phase0
remains failed for the unfrozen amendment.

Candidate semantics:
`sha256:dc71cd7e8d31e5d77384de0ec68ef69cd026c0f267a3453cb45bc42f8a33a2df`.
Evidence: `formal/proposals/evidence/public-reachability.json`; scope:
`formal/proposals/public-reachability-proof.md`. All three demos HTTP 200 without
restart; frozen fallback refs unchanged. Native runtime/arithmetic guard unchanged.

The environment/resolver is fixed for each reachable history. Initial actor/current
authentication, real scan completeness, finite hash/codec and metadata/QC trust
retain their previous assumptions. This is the general reachable-machine/log
sublayer, not `nativeArithmeticRecoveryRefines`: mandatory coverage still 44/45,
Formal NO_GO. Self-review is not an independent attestation.

Next: bind reachable operations to independently authenticated original public
event snapshots and canonical public state-root transitions, preserving actor,
context, sequence, exposure and original bytes. Connect non-arithmetic phase/QC
admission and global SendVoteEnvelope/QC eligibility. Do not promote fixture
lookup adapters or assumed snapshot equality into authority. Concrete bounded
native decoder/hash/exporter/WAL, admission completeness, arbitrary snapshots,
availability/failures/repair, contract freeze, clean offline reproduction and
independent reviews remain mandatory before merged Formal GO and PR50 work.

## 2026-09-25 — Exact native snapshot/first-event binding (T044/T048/T049/T053/T054/T056/T057/T060)

`PublicSnapshot.lean` now encodes the complete existing v1 native snapshot and
its exact domain-separated SHA preimage, then checks the separately resolved
registry entry against the original native anchor/metadata, contract, finalized
parent, event and all-vote journal. The first event preserves actor/action/round/
height/epoch/context/body/parents, view/time/validator role, exact command and
prospective sequence. UNKNOWN retains a null sequence and public-root stutter.
The executor calls the existing checked persistence operation; successful
execution derives the previously proved reachable journal invariant.

Thirteen general helper theorems and fifteen functions are audited. Fifty-two
kernel-decide cases use the three pinned original snapshots/bytes/hash preimages
at arithmetic sequences 5/6/8. They cover first execution, unknown append and
field/byte/identity/context substitutions. Four re-encoded snapshots with
synthetic matching hashes load but fail binding to independent native inputs.
One additional composition theorem links execution to the reachable four-vote
prefix. Seven Python tests cover exact generation, five rehashed substitutions
rejected before output, and the explicit root-scope counterexample below.

A material refinement gap was confirmed: current fixture state roots hash
`trace_id:state:index` labels; `validate_trace_document` checks adjacency, not a
full-state preimage. Replacing the initial root and first prior root preserves
checker PASS without supplying any state preimage. Retained evidence explicitly
marks FULL_PUBLIC_STATE_ROOT_NOT_VERIFIED. Exact snapshot bytes bind an opaque
producer root; they do not prove the full public state or its transition hash.

The snapshot registry still needs genuine producer provenance; examples use
synthetic trust and three finite snapshot hash samples, not a general decoder/
SHA proof or native exporter. Non-arithmetic phase/QC admission, global delivery/
quorum eligibility, arbitrary snapshots/failures/repair and production WAL remain
open. No public schema, TLA transition or runtime arithmetic guard was changed.
`nativeArithmeticRecoveryRefines` remains OPEN (mandatory 44/45, Formal NO_GO).

Evidence: `formal/proposals/evidence/public-snapshot.json`; exact scope:
`formal/proposals/public-snapshot-proof.md`. Next: define and check the complete
canonical public-state preimage and allowed action relation. Inspect
`formal/tla/DeltaReduceTypes.tla:ProtocolVariables`, `DeltaReduce.tla:Init/Next`,
`formal/scripts/formal_artifacts.py:validate_trace_document`, and production
round-state encoding/exporter boundaries before choosing the abstraction.
Do not substitute per-actor journal roots or legacy RoundState summaries for a
full state when that hides protocol distinctions. Existing frozen fixtures must
retain their honest adjacency-only scope. Then compose real phase/QC/exposure
rules, concrete bounded native adapters, freeze, offline reproduction and reviews.

Validation: mandatory Lean build 980 jobs, fresh snapshot body kernel and fresh
snapshot vector compilation PASS; all 81 new theorem/function declarations use
only permitted propext/Quot.sound/Classical.choice. 180 tooling/38 oracle tests,
33 legal/112 illegal traces, targeted Ruff and byte-exact regeneration of 300
JSON/nine generated Lean files PASS. Four Lean semantic artifacts changed;
145 public traces change only semantics ID; native witness bytes and 19 TLA
modules/public schema unchanged. No new TLC/production mutants; retained finite
28 safety/7 liveness/27 mutant scope unchanged. GNU make unavailable and Phase0
unfrozen: scoped checks are not aggregate formal-check. Three demos HTTP 200,
no restart, frozen refs unchanged. Candidate semantics:
`sha256:b057047e8712df5159adc1a376a11e2e732e0ead07bdfac40ae52f842c33f94c`.

### Complete public-state preimages and production-action replay

T009/T011/T012/T044/T048/T049/T053/T054/T056/T057/T060, amendment 0001.
Added the separate `deltareduce.full-public-state.v1-candidate` evidence profile.
`DeltaReducePublicState.tla` explicitly maps all 64 ProtocolVariables, including
transport multiplicity, delivered votes, intermediate certificates, repair,
per-actor sequence/recovery, current pointers, phase/time and crash coverage.
Inventory checks compare declarations, tuple, record and match clauses; no
RoundState summary or per-actor journal stands for complete protocol state.
Canonical tagged values distinguish booleans/integers/strings/model values/sets/
functions. Records and sequences share their actual TLA function representation;
sets/domains are ordered without duplicates. Full preimages bind source modules,
formal semantics and the exact pinned finite configuration. Missing/unsupported
values fail; unresolved durability cannot masquerade as a complete observation.

Generated TLC replay checks actual production Init, TypeOK, Next and selected
actions over every complete adjacent state. It does not use a Python action
approval or a supplied state-equality predicate. A 16-state/15-step path covers
three honest RoundConfig persist/send/delivery paths, crash/restart/recovery
before exposure, quorum and stutter. Seven deliberately rehashed invalid paths
produce expected TLC counterexamples: noninitial state, hidden clock side effect,
wrong action label, erased durable vote, send-before-persist, QC before third
delivery and a changed state called stutter. These are new finite replay checks,
not additional production mutants or a replacement for the retained model suite.
Exact generated modules/configurations/logs are retained for all eight cases.

Sixteen Python tests cover regeneration, every field omission/change, aliases,
ordering, source/config/root substitution, incomplete durability, action vocabulary,
resource limits, inventory drift and fail-closed TLC transcript parsing. The
existing v1 public trace root counterexample remains valid and honestly scoped:
legacy label-root fixtures were NOT upgraded to full-state or native refinement.
The new profile has no native exporter/provenance adapter and is not yet joined
to the full arithmetic trace/Lean reachable-history relation. Mandatory Lean
coverage remains 44/45; nativeArithmeticRecoveryRefines stays OPEN. No runtime
arithmetic guard, baseline demo or native execution behavior was changed.

Evidence: `formal/proposals/evidence/public-state.json`; specification/scope:
`formal/proposals/public-state-projection.md`. Validation: 196 tooling/38 oracle
tests, 33 legal/112 illegal legacy traces, full SANY parser, new TLC replay cases,
Ruff, syntactic consistency and byte-exact regeneration of 301 JSON/nine generated
Lean files. All Lean inputs unchanged; the checked audit retains 44/45 and the
previous 980-job build, with no new mathematical proof claimed. Nineteen prior
TLA modules and the existing public schema unchanged; one projection-only module
added. Retained 28 safety/7 liveness/27 production mutants retain their prior
bounded scope. GNU make unavailable; aggregate formal-check is not claimed.
Phase0 remains unfrozen. Three demos stay HTTP 200, frozen refs unchanged.
Candidate semantics:
`sha256:413d169e8ebe06713aa33c8b355a94f71bd6361cc5dbf1261db4e7a265bc7832`.

Next: extend this complete-state/action relation to the arithmetic public path,
including all intervening vote/certificate/availability/phase actions, and bind
its original snapshots/context/bytes/sequences (5/6/8) to PublicSnapshot and the
reachable native journal. The finite config-only example cannot discharge the
full recovery theorem. Retain distinct unknown/incomplete versus authenticated
complete scans; source-linked original metadata/exposure/QC/current advancement
must be derived, not assumed. Decoder/hash/exporter/WAL, arbitrary initial
snapshots/availability/failures/repair, contract freeze, clean offline reproduction
and independent review remain mandatory before native authority.

### Complete arithmetic public-state path from pinned artifact inputs

T009/T011/T012/T044/T048/T049/T053/T054/T056/T057/T060, amendment 0001.
The complete-state replay now includes the arithmetic path from actual production
Init through ticket/availability/ISC/seed/EC/APC, both PARAMETER QCs, aggregate QC,
APPLY QC and current advancement. The checked path contains 132 complete states
and 131 steps, with all 64 protocol variables in every canonical preimage.
It preserves all 36 original public event positions/times, every actor's sequence
1..8 and original arithmetic sequences 5/6/8. All 24 votes have explicit production
send and delivery; 35 clock steps preserve the original event times.

A new generated TLA input module binds the exact twelve-artifact native fixture
via a separately pinned bundle hash and typed graph validation. The manifest
retains artifact IDs, Q/schema/shard placement, weights/quanta, current model and
optimizer, coefficients and full expected native bodies. The two PARAMETER values
are 1 and -2; APPLY gives model [19,-19] and optimizer [2,-2]. Production TLA
arithmetic checks these results against the actual configured input functions.
The TLA model/source/configuration are immutable inputs to each state identity.
Limit 127 is explicitly finite and does not claim native INT64-wide admission.

Three rehashed invalid full paths fail the production action relation: wrong
PARAMETER numerator, wrong next optimizer and current advance without ApplyQC.
The earlier RoundConfig/crash/recovery path and its seven negative cases were
rechecked after introducing shared TLA value operators. These checks are finite
replays, not new production mutants or native executions. Lossless field pooling
keeps the arithmetic vector file manageable; expansion checks every reference,
preimage and root. No variable is summarized or erased. Full negative TLC logs
are retained as deterministic gzip with decompressed byte hashes.

The 36-event correspondence explicitly records that legacy snapshot roots are
incompatible opaque labels. Original snapshot bytes/roots were not rewritten.
This is not authenticated native exporter provenance or Lean reachable-history
composition; nativeArithmeticRecoveryRefines remains open, mandatory 44/45.
No arithmetic crash/unknown-append path is newly claimed. General admission,
bounded decoder/hash/exporter/WAL, initial snapshots, failures/repair, contract
freeze, clean offline reproduction and independent review still block authority.

Evidence: `formal/proposals/evidence/public-arithmetic-state.json`; scope and
reproduction: `formal/proposals/public-arithmetic-state.md`. Validation: 204 tooling
tests, 38 oracle tests, 33 legal/112 illegal legacy traces, full SANY parser,
Ruff, syntactic consistency and byte-exact regeneration of 303 JSON/nine generated
Lean files plus the new input TLA/configuration. All Lean inputs remain unchanged;
the audit was rechecked at 44/45, retaining the previous 980-job build. Twenty prior
TLA modules and public schema unchanged; only the new fixture input module added.
Retained 28 safety/7 liveness/27 production mutants retain their prior bounded
scope. GNU make unavailable; aggregate formal-check is not claimed. Phase0 remains
unfrozen. Demos remain HTTP 200 without restart and frozen refs are unchanged.
Candidate semantics:
`sha256:70bea95f4288e579b1dae60ad3cf4ab76f15a1a533c560ec9b564c6ae4e23496`.

Next: derive and check a complete-state/native-event binding with explicit original
actor/context/bytes/sequence and native current/model/optimizer/authority mappings.
An incompatible v1 snapshot must reject; do not merely replace its root with a new
hash and claim exporter authentication. Specify the new projection/provenance
boundary, compose it with PublicSnapshot/PublicReachability, and extend to arithmetic
crash/unknown recovery and global exposure/QC/current advancement. Only that full
general relation can discharge the remaining mandatory recovery conjunct.

### Checked complete-state/native first-vote correspondence

T009/T011/T012/T044/T048/T049/T053/T054/T056/T057/T060, amendment 0001.
Added the separate `deltareduce.full-public-native.v2-candidate` projection with
an explicit synthetic source-registry boundary. Nine first PARAMETER/APPLY votes
are checked against complete prior/next preimages, immutable source/configuration
identity, independently pinned original native metadata and the twelve-artifact
graph. Actor, role, context, height/epoch/view/time/deadline, parent/readiness and
original per-actor sequence 5/6/8 are checked. The single appended envelope and
complete vote-effect field changes are derived from actual before/after states.

Actual modeled parent certificates must have matching durable and delivered
signer envelopes. Whole PARAMETER/APPLY bodies, authority inputs, schema/shard
placement, bound model/optimizer, conversions and next vectors are independently
reconstructed by the native artifact oracle and compared against the modeled
bodies. Original command/envelope/receipt/effect bytes and snapshot ASCII bytes
are retained exactly; no native record or new runtime receipt is written.

The v2 wrapper keeps old opaque snapshot roots as source observations and binds
complete roots separately. Old v1 snapshots cannot masquerade as v2 evidence;
rehashing a changed result, state or provenance label cannot bypass derivation.
The registry pins are integrity checks, not native producer authentication.
Every result remains `SYNTHETIC_PINNED_FIXTURE_NOT_NATIVE_AUTHENTICATION` with
`native_export_authenticated=false`. The required independent producer/run/source/
position/native-snapshot/full-state tuple is specified as a still-open premise.
No authentication Boolean or supplied expected-result equality discharges it.

Sixteen new tests cover exact generation, all original bytes/sequences, legacy
versions/roots, incomplete states, changed current/readiness/phase/time/view,
sequence/actor/action, hidden side effects, missing/undelivered QCs, rehashed
PARAMETER/APPLY arithmetic, complete ISC/EC/APC identities, parent model/optimizer/
profile inputs and forged claim/provenance fields. The complete tooling suite has 220 passing tests plus
38 oracle tests; 33 legal/112 illegal legacy traces retain their scope. The
132-state/131-step production TLC path was rerun with byte-identical harness and
configuration, and its finite scope is unchanged. All 304 generated JSON files,
nine Lean files and the existing input TLA/config reproduce byte-for-byte.
Targeted Ruff and syntactic consistency pass. The audit still reports 44/45;
no new Lean theorem is claimed and the prior 980-job build is retained.

Evidence: `formal/proposals/evidence/public-native-projection.json`; scope and
reproduction: `formal/proposals/public-native-projection.md`. All 21 TLA modules,
Lean sources, public schema and original native/complete-state vectors remain
unchanged. Formal semantics stays
`sha256:70bea95f4288e579b1dae60ad3cf4ab76f15a1a533c560ec9b564c6ae4e23496`;
the new NO_GO report binds the new tool/source commit. Retained 28 safety/7
liveness/27 production-mutant results keep their previous finite scopes. GNU make
unavailable; aggregate formal-check is not claimed. Phase0 is still unfrozen.
All three demos remain HTTP 200, with no restart or frozen-ref movement.

This is a finite completed-trace correspondence, not production authentication,
general admission or a new requirement that PARAMETER wait for a later aggregate.
The structural vote check does not replace production Next. No arithmetic crash,
unknown-durability, historical retry or general initial-snapshot relation is
newly claimed. Native arithmetic guards remain unchanged; qualifying runtime work
stays blocked by Formal NO_GO.

Next: represent the complete public state and its native identity projection in
the mandatory proof layer. Derive actor/current/sequence/parent/body bindings
through checked extraction of all relevant fields from that complete object;
retain the whole preimage/source/configuration/provenance boundary. A summarized
RoundState, finite approval table or assumed recovered-state equality is not
sufficient. Compose this with PublicSnapshot/PublicReachability and production
vote/send/QC/current behavior, then arithmetic crash/unknown recovery. General
decoder/hash/exporter/WAL/admission, arbitrary snapshots/failures/repair, contract
freeze, clean offline reproduction and independent reviews remain mandatory.

### Complete tagged public state and native metadata extraction in Lean

T009/T011/T012/T044/T048/T049/T053/T054/T056/T057/T060, amendment 0001.
Added the mandatory `PublicState` representation/extraction layer and its four
generated example modules. The state retains all 64 production variable names,
tagged finite values, canonical complete bytes and independently supplied
semantic/module/configuration identity. Checked loading verifies every field,
canonical ordering, resource bounds and the exact domain-separated preimage.
It consumes typed values; it does not prove a byte parser or native allocation
safety. SHA and native identity mappings remain explicit assumption boundaries.

Forty general helpers and fifty named executable definitions retain complete
rows and derive actor, original current parent, time/view, all-vote sequence,
one new arithmetic envelope, proposed body, fresh context and preservation of
old durable votes. The optional native frame binder checks selected original
anchor/metadata fields; it does not authenticate the mapping or join the full
arithmetic graph/body/QC/pre-WAL/recovery relation.

The source-linked examples contain 18 complete states, nine first arithmetic
votes retaining original sequences 5/6/8, and three complete loaded/projected
state pairs. Fifty-eight kernel cases include exact bytes, native metadata,
structural/mapping/clock/sequence/readiness rejection and a deliberate scope
countercheck: inserting an earlier nonempty message set still passes extraction.
Thus extraction is not production Next or a check of all after-state effects.
The generator verifies the countercheck actually changes the source state.
Finite SHA samples and the explicitly synthetic zero example semantic ID are
not authenticated native observations. The zero avoids a semantic self-hash.

Complete byte equalities, canonicality, ordering, depth, node counts and lengths
are composed from checked component lemmas. Earlier draft errors and expensive
whole-list simplification were corrected before acceptance. Exact hash-sample
branch proofs avoid evaluating unrelated multi-megabyte byte comparisons; every
selected sample still requires exact bytes. No native-decide oracle, assumed
result equality or additional axiom was introduced. Full Lean build (985 jobs),
fresh generic kernel and all declaration axiom checks pass. Only the permitted
propext/Quot.sound/Classical.choice dependencies occur. Mandatory coverage stays
44/45; `nativeArithmeticRecoveryRefines` is still missing.

Evidence: `formal/proposals/evidence/public-state-lean.json`; exact scope and
reproduction: `formal/proposals/public-state-lean-proof.md`. Final tooling/oracle,
byte-exact regeneration and unchanged-demo/source checks are retained with this
evidence. All 21 TLA modules, public schema and 147 native witness files remain
unchanged; the 145 legacy public traces change only their semantics ID. No fresh
TLC or new production mutant execution is claimed. Prior 28 safety/7 liveness/27
mutant and 132-state/131-step arithmetic-path results retain their bounded scope.
New semantics:
`sha256:259e5008ced76aac948a3be1a8baed17bc1c6b205e7b659be5c67124a7690aca`.
The candidate remains NO_GO; Phase0 is unfrozen and GNU make is unavailable.
Self-review is not independent attestation. Runtime guards and frozen demos are
unchanged; this proof sublayer is not Feature010 completion.

Next: check the complete allowed PARAMETER/APPLY after-state footprint, preserving
every unchanged variable and deriving every changed vote/journal field. Reject
the demonstrated message-set counterexample. Then join complete native graph,
body, metadata and pre-WAL preparation with the reachable all-vote journal and
actual phase/send/QC/current transitions, including crash/unknown recovery.
The footprint alone cannot discharge the full recovery theorem. Concrete bounded
decoder/hash/exporter/WAL/admission, arbitrary initial snapshots/availability/
failures/repair, contract freeze, clean offline reproduction and independent
review remain required before native authority and qualifying Feature010 gates.

### Complete arithmetic first-vote after-state footprint

T009/T011/T012/T044/T048/T049/T053/T054/T056/T057/T060, amendment 0001.
`PublicVoteEffects.lean` derives the four assigned fields from the preceding
complete state and the extracted PARAMETER/APPLY envelope, then checks all 64
after-state fields. Thirty-seven general helpers establish exact set insertion,
the actor sequence increment, preservation of other actors' sequences and all
sixty unassigned fields. Message exposure, delivery and current advancement
cannot be hidden inside the checked vote step. The preceding layer's unchanged
message countercheck is now rejected by the composed checker; extraction alone
still accepts it and remains explicitly insufficient.

Eleven executable definitions, eighteen calculation definitions, fifty-four
component calculation proofs and twenty-nine example/composition proofs are
included in the mandatory project. All 149 new named declarations pass the
axiom audit, using only permitted propext/Quot.sound/Classical.choice. Nine
original first votes and three loaded state pairs retain the original sequences
5/6/8. Existing eighteen full states and component ordering lemmas are reused.
This avoids introducing larger fixtures or normalizing the complete byte graphs
inside each dependent proof. Draft resource-heavy proof attempts were replaced
with component proofs; only the final frozen-source successful checks count.

Full Lean build (988 jobs), fresh generic kernel, 231 tooling and 38 oracle
tests, 33 legal/112 illegal legacy refinement traces, Ruff and syntactic
consistency pass. Byte-exact regeneration covers 305 JSON, fourteen generated
Lean files and the input TLA/config (321 files). A new syntactic correspondence
test expands both actual production vote actions into four assignments and
sixty preserved variables; omissions and substituted assignments reject. This
is not a proof of all TLA guards or a new production mutant execution.

Evidence: `formal/proposals/evidence/public-vote-effects.json`; scope:
`formal/proposals/public-vote-effects-proof.md`. New semantics:
`sha256:fbd646eb8aab4443a13a3f2e959cf0c942116b076b147374225bd2c7a5c51034`.
All 21 TLA modules, public schema and 147 native witnesses remain unchanged;
the 145 legacy public traces change only semantics ID. No fresh TLC or new
production mutants; retained 28 safety/7 liveness/27 mutants and the 132-state,
131-step arithmetic path retain their bounded scope. Mandatory coverage remains
44/45, with `nativeArithmeticRecoveryRefines` absent. Phase0 remains unfrozen;
GNU make is unavailable and aggregate formal-check is not claimed. Native guards
and frozen demonstration references remain unchanged.

This closes the complete-effect footprint gap, not full admission or recovery.
Next, join these full effects to independently anchored native arithmetic/body/
metadata and original pre-WAL preparation, with the actual reachable all-vote
journal. Preserve complete parent/QC/phase guards and global send/delivery/
current transitions, then crash and unknown outcomes. Do not assume a whole-body
translation, supplied state equality or finite authorization table. The finite
scalar TLA path and general native vector proofs must not silently be treated as
the same identity relation. Unknown/incomplete observations remain incomplete;
exact presence/absence must be authenticated and blocked scans stay blocked.
Concrete adapters, arbitrary snapshots/availability/failures/repair, contract
freeze, offline reproduction and independent review remain mandatory.

The user has allowed four hours plus the night and accepted synthetic
participants/Docker networking instead of independent authorities/real WAN for
a separate local acceptance scope. See
`docs/feature010-local-acceptance-20260925.md`. A control report is due at 19:05 UTC
on September 25. This agreement does not waive actual native arithmetic/WAL or
formal-first STOP, issue a local PASS, or turn simulation into original GO.

### Lossless scalar/vector correspondence and partial numeric join

T044/T048/T049/T053/T057/T060, amendment 0001. The native vector and scalar-per-
shard TLA representations now have an explicit checked numeric abstraction.
`NativeScalarProjection.lean` derives the layout from the bound schema, checks
exact coordinate coverage and reads by schema offset. Nineteen general helper
theorems prove no lost/invented coordinates, injectivity, checked PARAMETER
accumulation and paired model/optimizer projection. Vector shards have no scalar
projection; this is a model limitation, not a new native admission restriction.

`PublicScalarNumbers.lean` compares complete abstract numeric tables to actually
derived native results, checks event frame and all-vote sequence, composes the
complete public effect footprint with original native pre-WAL preparation, and
preserves reachable journal execution for known persistence cuts. Its sixteen
general helpers do not establish whole public body/authority/parent/QC identity
or complete prior durable-prefix correspondence. Unknown append observations
cannot enter this complete-state API; the earlier incomplete/verified-scan
recovery layer remains responsible for them. No absence is inferred.

Eighteen scalar-projection kernel examples include the existing pinned schema,
two native PARAMETER derivations and native APPLY derivation, offsets, signed
endpoints and rejected coverage/shape cases. Fifteen small public-table/record
examples reject substituted or missing values and aliases. A deliberate scope
countercheck accepts numerical records in a body missing authority/parent;
numeric correctness alone therefore cannot stand for full body validity.
No new combined full-state/native execution example is claimed. Resource-heavy
draft reductions were removed; only final successful component/kernel checks
are retained. The generic checked join and reachability composition compile.

Four mandatory-project modules, seventeen general definitions and six example
definitions add 91 audited names. Full Lean build (992 jobs), fresh generic
kernels and axiom audit pass with only permitted propext/Quot.sound/Classical.choice.
231 tooling/38 oracle tests, 33 legal/112 illegal legacy traces, Ruff and syntactic
consistency pass. Regeneration is byte-exact for all 321 files (305 JSON,
fourteen generated Lean files and input TLA/config). No further fixture expansion
was introduced. All 21 TLA modules, schema, runtime and 147 native witnesses are
unchanged; 145 legacy public traces change only semantics ID. Prior 28 safety,
7 liveness, 27 production mutants and the 132-state/131-step arithmetic path
retain their bounded scope, with no fresh TLC or mutant execution this stage.

Evidence: `formal/proposals/evidence/native-scalar-projection.json`; exact scope:
`formal/proposals/native-scalar-projection-proof.md`. Semantics:
`sha256:1d71c93d8c5a09efda9dbe629a4ea15e70bc0968022af3e2967c6859b8ab6e3e`.
Mandatory coverage remains 44/45: `nativeArithmeticRecoveryRefines` is missing.
Phase0 remains unfrozen and GNU make unavailable; aggregate formal-check is not
claimed. Frozen demos and native guards remain unchanged. This is NO_GO and not
Feature010 completion or local Docker acceptance.

Next: derive the complete public authority/input/body/parent projection from the
bound native graph and configured identity relation, including denominator,
quantum and domain/shard identity. Match the entire prior public durable vote set
to the reachable native all-vote journal instead of only its size. Then compose
actual phase/send/delivery/QC/current and crash/unknown transitions. General
bounded adapters/admission, arbitrary snapshots/availability/failures/repair,
contract freeze, clean offline reproduction and independent review remain open.

### Complete scalar arithmetic inputs from the bound native graph

Tasks T044/T048/T049/T053/T057/T060. `NativeInputProjection.lean` now loads the
complete native input plan and committed Q bytes before result computation.
The loader does not require a later aggregate or successful PARAMETER/APPLY.
Twenty-five general helpers connect exact ticket order, every assignment and
each scalar Q cell to its checked canonical artifact and commitment. Ticket
weights must agree across shards, and domain denominators across assignments;
inconsistent or missing data cannot silently become a scalar model input.
Native profile fractions, schema-offset current model/optimizer and checked
mixture LCM determine the remaining input values.

`PublicArithmeticInputs.lean` adds fourteen general helpers and constructs all
23 canonical `NativeArithmeticInputs` fields. It preserves all function entries,
checks lengths before zipping, checks the complete configured namespaces and
compares the whole derived record. A configured ticket without corresponding
eligible native Q cells is unrepresentable, rather than assigned invented zero
values. Scalar width and limit 127 remain explicit finite-model restrictions,
not changes to native admission or proofs of full-width guard equivalence.

Nineteen native input examples include the original checked input blocks and
projection, plus separate multi-ticket/domain and rejection cases. Fourteen
public codec cases and 38 component/encoding proofs check exact full record
bytes, all 23 field names, alias/namespace/shape failures, changed fraction or
current values and canonical sequence keys above nine. The generated fixture
uses the same independently pinned twelve-artifact source and retains its
synthetic trust/finite codec scope. No new complete native execution or public
recovery trace is claimed. Component proofs replace superseded resource-heavy
draft reductions; only final checked files count as evidence.

The four mandatory-project modules add 200 audited declarations. Scope and
reproduction: `formal/proposals/native-input-projection-proof.md`; evidence:
`formal/proposals/evidence/native-input-projection.json`. Semantics:
`sha256:afdbae063a439fe5d37265083d9462ffb15f9cfcf9da585b7a60b94116d2ba1d`.

Final full Lean build (996 jobs), fresh generic kernels and axiom audit pass
with only propext/Quot.sound/Classical.choice. 235 tooling/38 oracle tests,
33 legal/112 illegal legacy traces, Ruff and syntactic consistency pass.
Regeneration is byte-exact for 322 files: 305 JSON, fifteen generated Lean
files and input TLA/config. All 21 TLA modules, public schema, runtime and 147
native witnesses remain unchanged; 145 legacy traces change only semantics ID.
No fresh TLC or production mutant is claimed: retained 28 safety/7 liveness/
27 mutant results and the 132-state/131-step arithmetic replay keep their
previous finite scope. Mandatory coverage stays 44/45; Phase0 is unfrozen and
GNU make unavailable, so aggregate formal-check is not claimed. All three demo
services returned HTTP 200 without restart, and frozen refs stayed unchanged.

This layer is not the complete authority or PARAMETER/APPLY body. Next: derive
the authority/ISC/EC/APC/parent/certificate identity chain and compare the entire
body, then bind the entire prior public durable vote set to the reachable native
journal. Actual phase/send/delivery/QC/current and crash/unknown composition,
bounded adapters/admission, arbitrary snapshots/failures/repair, contract freeze,
offline reproduction and independent review remain open. Mandatory recovery is
still missing; this is NO_GO, not Feature010 completion or Docker acceptance.


### Conditional complete public authority and parent construction

Tasks T044/T048/T049/T053/T057/T060. `PublicAuthority.lean` constructs the ten
public arithmetic authority fields from actual checked native input projection.
All 23 arithmetic-input fields and schema-offset current values are retained.
ISC, seed, EC and APC records are built from the original commitments, eligible
members and checked native parent-reference edges; no whole translated parent
or authority body is supplied. The complete candidate and canonical tagged-value
shape are checked. Twenty-seven general helpers establish original metadata
keys, entry count/order/provenance, exact parent links, full inputs and current
model/optimizer fields. Sorting retains entries; canonical validation rejects
duplicates. Thirty-eight component/kernel cases include actual pinned native
header/commitment references and separately constructed complete public values.

Configuration, seed, norm evidence, coefficient symbols and close policy are
not present in the minimal native parent payloads. The new named MetadataTrust
premise must independently authenticate those primitive values. Context/ref/Q
substitutions cannot reuse the same lookup key. Fixture metadata is synthetic,
and arbitrary alias injectivity/native exporter authentication remains open.
This is a conditional construction, not authenticated production certificates,
phase/quorum admission, a full PARAMETER/APPLY body or recovery proof. No new
combined full-state/native execution trace is claimed. Original artifact bytes
and native sequences 5/6/8 stay unchanged.

Scope: `formal/proposals/public-authority-proof.md`; final evidence:
`formal/proposals/evidence/public-authority.json`. Native arithmetic guard and
formal-first STOP remain active. The next substantive stage constructs and
compares the entire PARAMETER/APPLY body using these parents and the actual
native computations, then binds the full prior durable set and phase/QC/current
and crash/unknown transitions. The mandatory native recovery theorem, general
bounded adapters/admission, arbitrary snapshots/failures/repair, contract freeze,
clean reproduction and independent review remain open. NO_GO is unchanged;
Docker/synthetic acceptance is not issued by these proofs.

Final stable-source checks: full Lean build 998 jobs, fresh generic/vector kernels
and all 106 new declaration audits pass with only propext/Quot.sound/Classical.choice.
238 tooling/38 oracle tests, 33 legal/112 illegal legacy traces, Ruff and syntactic
consistency pass. Mandatory audit remains 44/45 (nativeArithmeticRecoveryRefines
missing); Phase0 remains unfrozen and aggregate formal-check is not claimed.
Semantics: `sha256:9fa840076d8943d1987352a4959bd5827c7cf9424834ff7cf7dc87ad90b15ae5`.
Byte-exact regeneration covers 322 files (305 JSON, fifteen generated Lean,
input TLA/config). All 21 TLA modules, public schema, runtime and 147 native
witnesses are unchanged; 145 legacy traces change only semantics ID. No fresh
TLC or production mutants are claimed. Three demo services returned HTTP 200
without restart and all frozen refs remain unchanged.


### Complete PARAMETER body and checked native-preparation composition

Tasks T044/T048/T049/T053/T057/T060. PublicParameterBody constructs all fifteen
public PARAMETER fields from actual DerivedParameter rows and the checked
PublicAuthority/input corpus. It compares the whole canonical body, including
all authority and parent records. Frame, assignment, original ordered rows,
weights, Q cells, denominator and quantum remain bound to native inputs. The
former numeric-only body without authority now has a general rejection proof.
No later aggregate or conversion is needed for PARAMETER construction.

Narrow arithmetic is recomputed from the original rows; equal output at native
and model widths follows from their exact recurrence. Coefficients, products
and every prefix are checked. The separate public result bound is symmetric,
whereas arithmetic permits -limit-1: at limit 127, -128 passes raw arithmetic
but fails the result guard. The supported projection uses equal model/result
bounds; binding that equality to the actual configuration remains required.
Denominator fitting adds a representability restriction absent from the TLA
parameter guard. These are not new native admission restrictions or a proof
that native INT64/INT128 success implies bounded model success.

PublicParameterJoin loads these source-bound bodies together with actual
original NativePrepared records, complete PublicVoteEffects and original
all-vote sequence, then composes successful known-cut persistence with
PublicReachability. UNKNOWN and APPLY reject at this new complete-body API.
The entire prior public durable set, shared alias/configuration identity,
phase/committee/availability/QC/send/current guards and complete recovery remain
open. MetadataTrust remains independently required and synthetic in fixtures.
This stage is not native execution or a new full-state/native trace.

The three modules contain 23 general helpers, 14 executable definitions and
33 component/kernel proofs plus five small fixture definitions: 75 names are
axiom-audited. Native examples reuse original two PARAMETER computations; other
cases separate body components and arithmetic-width failures. Scope and
reproduction: formal/proposals/public-parameter-body-proof.md; final evidence:
formal/proposals/evidence/public-parameter-body.json. Semantics:
sha256:9bdb3c2ab80b5815b3bd75c599c8d5ea294e31977d57898a37a65c987a16ffff.

Next: construct the entire certified PARAMETER leaf corpus and aggregate/APPLY
body, including narrow conversion/mixture/optimizer guards. Check nextCheckpoint
against the actual command/current-advance contract: read-only production
CurrentPointerStore::advance requires next_checkpoint_id == apply_qc.next_model_hash,
while the present native APPLY_EXPECTED body contains next vector hashes but no
independent nextCheckpoint field. NativeReplay currently delegates the checkpoint
edge to named QC authentication. Do not invent a new checkpoint name or claim
this relation without checking the contract and public identity mapping. Then
match the full prior durable prefix and compose actual phase/QC/crash/unknown
behavior. The mandatory recovery theorem and full native/benchmark gates remain
open; NO_GO and formal-first STOP stay active.

Final stable-source verification: full Lean build 1001 jobs, fresh body/join/vector
kernels and all 75 axiom audits pass with only propext/Quot.sound/Classical.choice.
241 tooling/38 oracle tests, 33 legal/112 illegal legacy traces, targeted Ruff
and syntactic consistency pass. A report-text line-length warning was corrected
without changing its string value; final Ruff checks pass. Mandatory audit stays
44/45, Phase0 is unfrozen and GNU make unavailable; aggregate formal-check is not
claimed. Byte-exact regeneration covers 322 files (305 JSON, fifteen generated
Lean and input TLA/config). All 21 TLA modules, schema, runtime and 147 native
witnesses remain unchanged; 145 legacy traces change only semantics ID. No fresh
TLC or production mutant is claimed. The previous bounded 28 safety/7 liveness/
27 mutant results and 132-state/131-step replay retain their scope. All three
demos returned HTTP 200 without restart and frozen refs remained unchanged.


### Complete aggregate/APPLY body and narrow arithmetic rechecks

Tasks T044/T048/T049/T053/T057/T060. PublicApplyArithmetic rechecks every actual
native certified conversion, preserves every source entry and derives output
identity by the exact conversion formula. It recomputes mixture and optimizer
at projected bounds from the actual NativeApply rows/current vectors/profile.
General cross-width proofs derive denominator, gradient and both next-vector
identities; coefficients/products/prefixes and optimizer intermediates cannot
be bypassed by wide native success or a zero learning rate.

PublicApplyBody constructs every complete public PARAMETER leaf from the exact
native certified corpus, with original ordered source, frame/row/coverage and
shared-parent checks. It constructs all twelve aggregate and ten APPLY fields,
complete authority and schema-tagged next-vector tables, then compares the whole
canonical candidate. The native aggregate remains independently anchored and
its full ordered body list is retained. Canonical public leaf sets retain all
values and reject duplicates. Numeric-only missing-authority bodies reject.

The separate configured next-checkpoint model symbol must map, through the
independent IdentityMap, to the exact sha256 spelling of the computed native
next-model hash. This checks the existing runtime convention observed in
CurrentPointerStore::advance; the native APPLY_EXPECTED has no separate checkpoint
field. It does not authenticate the configuration/map or prove the entire
normative ApplyQC/current-pointer edge. Structured public vector values are
not silently equated with cryptographic content IDs. Those identity/configuration
premises, including native exporter provenance, remain explicit and unresolved.

PublicApplyJoin now offers a source-bound complete-body API for both PARAMETER
and APPLY. It preserves original NativePrepared records, full before/after vote
effects and sequences, then composes actual successful known-cut persistence
with reachable journal operations. UNKNOWN still cannot enter this complete-state
API. The entire preceding public durable set beyond count, unified aliases,
non-arithmetic phase/QC/send/delivery/current and full crash/unknown composition
are still open. The old PARAMETER-only API retains its explicit APPLY rejection.

Four modules contain 31 general helpers/21 definitions and 34 component/kernel
examples/eleven definitions: 97 names are axiom-audited. One example rechecks the
actual pinned native APPLY arithmetic; another uses its prior kernel-checked
result for checkpoint mapping. Other examples separate complete body components
and arithmetic guard failures. No new combined full-state/native execution,
production mutant or authenticated exporter is claimed. Scope/reproduction:
formal/proposals/public-apply-body-proof.md; evidence:
formal/proposals/evidence/public-apply-body.json. Semantics: sha256:a314b03b877a03a63946a70bfc3bcc064b2ca8349d91b053b317427d021b3911.

Remaining mandatory recovery, native bounded adapters/WAL/admission, arbitrary
snapshots/availability/failures/repair, contract freeze, clean reproduction and
independent reviews are not waived. Formal-first STOP stays active; this is
NO_GO and not local Docker/synthetic acceptance. Next bind the ENTIRE previous
public durable vote set to the reachable all-vote journal with checked original
action/context/body identity for each slot; count equality is insufficient.
Do not introduce a whole-body approval mapping or rename otherAuthorized as a
phase proof. Then compose actual protocol send/QC/current/crash recovery.

Final stable-source verification: full Lean build 1005 jobs, fresh arithmetic,
body/join/vector kernels and 97 axiom audits pass with only propext/Quot.sound/
Classical.choice. 244 tooling/38 oracle tests, 33 legal/112 illegal legacy traces,
Ruff and syntactic consistency pass. Regeneration is byte-exact for 322 files
(305 JSON, fifteen generated Lean and input TLA/config). All 21 TLA modules,
schema/runtime and 147 native witnesses remain unchanged; 145 legacy traces
change only semantics ID. No fresh TLC or production mutants; previous finite
28 safety/7 liveness/27 mutants and 132-state/131-step replay keep their scope.
Mandatory audit stays 44/45; Phase0 is unfrozen, make unavailable and aggregate
formal-check not claimed. All three demos HTTP 200 without restart; frozen refs
unchanged.

### Exact actor-prefix checker and confirmed legacy body-preimage gap

Tasks T044/T048/T049/T053/T057/T060. PublicDurablePrefix derives historical
arithmetic body correspondence from the same independently resolved graph and
original metadata, checking complete canonical envelopes, keys, records,
sequences, receipts/effects and public actor/kind/context/parent/round identity.
Historical correspondence does not reapply current first-vote freshness.
Reachability separately supplies original admission. Induction over paired
slots checks each original sequence and both directions of exact public-set
coverage. Untrusted ordering evidence must be a duplicate-free permutation of
the complete actor-filtered public state; equality of counts is insufficient.
The new known-cut wrapper checks this prefix before actual persistence and
composes its result with the existing reachable journal. UNKNOWN rejects.

This is a fail-closed PARTIAL bridge. No accepting non-arithmetic body branch
exists, and otherAuthorized cannot bypass it. The original four-slot prefix
before the first PARAMETER and all eight original slots fail the stronger gate.
The prior scoped APIs remain unchanged. No successful nonempty full-prefix
native execution, full recovery theorem or new acceptance PASS is claimed.

The separately pinned source audit confirms that ISC/EC/APC/ROOT vote bodies
at original sequences 2/3/4/7 are hashes of four literal labels; their vote
parent arrays are empty. They are not the different minimal arithmetic graph
projection artifacts and cannot supply canonical native certificate fields.
CONFIG at sequence 1 has a canonical round-contract projection preimage, which
is not a native finalized configuration certificate. Actual arithmetic canonical
body preimages at 5/6/8 remain unchanged. No old hash, command, receipt or root is
rewritten. This is a fixture-provenance gap, not a SHA collision or a claimed
production bug. The machine inventory reports
MIXED_PREFIX_BODY_PROVENANCE_INCOMPLETE/full_prefix_bridge_pass=false.

Next derive versioned non-arithmetic voted-body witnesses from exact native
types/encoders and independently bound primitive inputs. PR50 source
60c692f6e391f839829dfc64e93380db54cd507b distinguishes VoteInputSetBody and its
body ID from finalized InputSetCertificate/QC IDs; preserve that distinction
also for EC/APC/ROOT/VIEW/ABORT. Do not use QC signer lists as pre-quorum bodies,
silently map labels to content IDs, or rewrite the original evidence. A new
source/version/run registry and explicit projection are required. Then compose
phase/send/delivery/QC/current/crash/unknown relations. Native bounded adapters,
WAL/admission, arbitrary snapshots/failures/repair, freeze, clean reproduction
and independent reviews remain open. Formal-first STOP and NO_GO remain.

Two modules contain sixteen general helper proofs/eight executable definitions
and nineteen small component/composition examples/seven definitions. All fifty
names are axiom-audited. Positive alignment examples are mathematical records,
not authenticated vote bodies; original-prefix negatives reuse actual slots.
Scope: formal/proposals/public-durable-prefix-proof.md. Evidence:
formal/proposals/evidence/public-durable-prefix.json.

Final stable-source verification: full Lean build 1007 jobs; fresh generic and
vector kernels and all fifty new axiom audits pass with only
propext/Quot.sound/Classical.choice. 248 tooling/38 oracle tests,
33 legal/112 illegal legacy traces, Ruff and syntactic consistency pass.
Regeneration is byte-exact for 322 files (305 JSON, fifteen generated Lean and
input TLA/config). Semantics:
sha256:c0e7baa47535a52378158b2f28d8a1e138c5b020d698a537badc7f1a5b650795.
All 21 TLA modules, schema/runtime and 147 native witnesses are unchanged;
145 legacy traces change only semantics ID. No fresh TLC or production mutants;
retained 28 safety/7 liveness/27 mutants and the 132-state/131-step arithmetic
path keep their finite scopes. Mandatory 44/45, unfrozen Phase0 and unavailable
make remain; aggregate formal-check is not claimed. Three demo services returned
HTTP 200 without restart and all frozen refs were unchanged.

### Versioned ISC voted-body preimages and native encoder/SHA component execution

Tasks T044/T048/T049/T053/T057/T060. A new separately versioned proposal witness
retains the complete native VoteInputSetBody typed fields, exact binary hash
payload/preimage and body ID. It is bound to PR50 source
60c692f6e391f839829dfc64e93380db54cd507b; it is not a replacement for any legacy
label hash, envelope, receipt or original sequence. The pre-quorum body has no
QC signer/quorum fields. Its root/availability/configuration primitives still
require independent native-state provenance and field-level public projection.

The bounded Python hash-payload encoder/decoder was cross-checked against ten
unmodified extracted C++ type/function definitions, plus the entire unmodified
native SHA source. MSVC 19.29.30146 x64 with C++20/W4/WX compiled the proposal
harness; 21 exact byte strings and SHA IDs agree. The pinned base body is 635
bytes. Other cases change each context/tuple/root field and cover uint64/text,
empty/duplicate/reversed-list boundaries. These encoding cases are not admission
tests: native hash encoding preserves typed order and does not itself validate
IDs, availability, phase, roots or quorum. The full native reactor/fixture
admission constructor/WAL/exporter is not executed. Generated binaries are ignored.

Eleven new tooling tests include all 635 truncated prefixes, trailing bytes,
length/count/resource checks and the supported 4096-tuple boundary, exact source
span/fixture reproduction, rehashed substitutions and forged provenance/QC fields.
The comparison preserves JSON type identity rather than accepting Boolean/integer
aliases. ASCII<=128/4096 tuples/4MiB are proposal profile restrictions, not new
native admission rules or the native wire/C ABI/WAL decoder contract.

Scope: formal/proposals/native-isc-body-codec.md. Evidence:
formal/proposals/evidence/native-isc-body.json. The source/hash registry is still
synthetic; native_export_authenticated=false and gate_eligible=false throughout.
Full config/policy/content/AC/root/closed-input authority, EC/APC/ROOT body
projection and the Lean journal/phase/QC/recovery relation remain open. The
stronger mixed-prefix checker still rejects the old incomplete history.
nativeArithmeticRecoveryRefines remains missing; NO_GO and formal-first STOP
are unchanged. No local Docker/synthetic acceptance has been issued.

Verification: 259 tooling tests, 38 oracle tests and the final eleven targeted
codec tests pass, as do 33 legal/112 illegal legacy traces, Ruff and syntactic
consistency. New fixture, extracted harness and C++ result regeneration is
byte-exact; every one of the preceding 322 generated files is unchanged. Lean,
all 21 TLA modules, public schema, runtime and old native/public fixtures are
unchanged. Semantics remains
sha256:c0e7baa47535a52378158b2f28d8a1e138c5b020d698a537badc7f1a5b650795.
No new Lean build/TLC/production mutant is claimed; the prior 1007-job build,
44/45 audit, 28 safety/7 liveness/27 mutants and 132-state/131-step path retain
their old scope. Phase0 remains unfrozen and make unavailable. Three demo
services returned HTTP 200 without restart; frozen refs remain unchanged.

### Complete native certificate bytes and ISC/EC/APC/ROOT voted-body components

Tasks T044/T048/T049/T053/T057/T060. A separate versioned fixture constructs
seven exact native certificates (ISC/seed/norm/EC/APC/PARAMETER QC/ROOT QC),
retaining their distinct QC IDs and four pre-quorum body IDs. The checker resolves
the exact anchored bytes and complete shared parent/leaf chain. EC's seed parent
is separately supplied under the exact EC ID and checked against APC; it is not
present in the native EC certificate. Missing/substituted/extra/duplicate leaf
records, wrong contexts/parents and malformed canonical bytes reject.

Unmodified PR50 canonical/SHA/certificate translation units and headers, plus
four body structs and twenty exact consensus functions, compiled with MSVC
19.29.30146 x64 C++20/W4/WX. Seven certificate byte strings/content IDs and four
voted-body IDs match independent Python construction. Four Merkle cases include
odd-leaf promotion. Five actual native shape rejections and three identity
variants pass; changed signers change QC ID but retain the pre-quorum body ID.
Ten native Git source blobs and all twenty-four extracted spans are pinned to
60c692f6e391f839829dfc64e93380db54cd507b. This is native component execution,
not reactor/admission/WAL/exporter execution or a native arithmetic benchmark.

Native certificate bytes keep their ORIGINAL cc98f15a semantic ID. They are not
rehashed under the candidate amendment and do not provide compatible formal
authority. Synthetic signers, primitive input/availability/norm/seed roots,
configuration IDs and EC seed metadata still lack independent provenance.
PARAMETER QC result 1 is the old component fixture, not the candidate vector
computation. An explicit countercheck rehashes a structural chain around another
opaque ISC root: original-anchor verification rejects it, while a caller-supplied
new anchor passes only the structural checks and still reports no authenticated
export/admission. Threshold/list shape is not signature or committee verification.

Scope: formal/proposals/native-certificate-chain.md. Evidence:
formal/proposals/evidence/native-certificate-chain.json. Sixteen new tests cover
exact source/output reproduction, every certificate substitution/removal,
rehashed parent/context/leaf changes, metadata and signer/body separation,
Merkle order/coverage, strict types/fractions/resources/versions, fixed-anchor
counterchecks and fail-closed C++ result parsing. Proposal ASCII/list/size/depth
bounds are explicit restrictions, not native parser/admission equivalence.

Verification: 275 tooling/38 oracle tests, 33 legal/112 illegal legacy traces,
Ruff and syntactic consistency pass. New fixture/harness/component results
regenerate byte-exactly; all preceding 322 generated files plus the previous
three ISC artifacts remain unchanged. No Lean/TLA/runtime/schema/legacy/native
witness input changed. Semantics remains
sha256:c0e7baa47535a52378158b2f28d8a1e138c5b020d698a537badc7f1a5b650795.
No new Lean/TLC/production-mutant run is claimed; retained 1007-job build,
44/45 audit, 28 safety/7 liveness/27 mutants and 132-state/131-step path keep
their bounded scope. Phase0 remains unfrozen, make unavailable. The three demo
services remain HTTP 200 without restart and frozen refs are unchanged.

The stronger mixed-prefix gate still rejects the old label-body history. No
receipt, sequence 5/6/8 or journal root was rewritten. Next bind actual complete
configuration, commitment/availability and closed-input snapshot primitives to
these typed bodies and their public fields; derive supported non-arithmetic
branches in the mandatory Lean prefix bridge. Then compose phase/send/delivery/
QC/current/crash/unknown relations. CONFIG/VIEW/ABORT, native bounded adapters,
WAL/admission/recovery, arbitrary snapshots/failures/repair, contract freeze,
clean reproduction and independent reviews remain open. Mandatory
nativeArithmeticRecoveryRefines is still missing. Formal and local acceptance
remain NO_GO/unissued; Docker/synthetic participants do not waive these gates.

### Native InputLedger execution and the frozen-input closure boundary

Tasks T044/T048/T049/T053/T057/T060. Complete unmodified PR50 consensus,
canonical, SHA and certificate translation units now execute the actual native
InputLedger in a proposal harness. Thirty-six ordered operations retain exact
active commitment/availability rows, frozen rows and late counts through reversed
arrival, retry, conflict, invalid coverage/attesters/threshold, freeze and late
evidence. Every actual disposition and before/after accessor projection matches
independent expected frames. This is not a full private-state snapshot: late
payloads have no accessor and remain represented only by counts.

A separate native ISC is constructed from EVERY actual frozen row plus explicit
fixture domain metadata. Its exact canonical ASCII, QC ID and pre-quorum body
ID match Python. The necessary tuple relation derives fields from the frozen
rows and rejects missing/extra/duplicate/reordered/substituted rows or wrong
metadata. The preceding singleton ISC rejects against the full two-row list and
is unchanged. No original label, receipt, journal root or sequence is rewritten.

Confirmed boundary: native freeze accepts a partial permitted set and has no
close-policy parameter. The named coverage conjunct accepts this subset for
OMIT_UNAVAILABLE and rejects it for ABORT_ON_INCOMPLETE. Native empty freeze
rejects, whereas TLA's OMIT_UNAVAILABLE coverage conjunct permits empty entries.
InputLedger does not compute input_root or prove actual current per-shard storage
availability; its proof/threshold/leaf parameters still need independent origin.
The typed ISC admission snapshot separately checks closed-body membership and
context; constructing/authenticating that snapshot from complete public state
remains open. These are component/adapter boundaries, not a demonstrated full
runtime admission defect.

Scope: formal/proposals/native-input-ledger.md. Evidence:
formal/proposals/evidence/native-input-ledger.json. Twelve native source blobs
are pinned to 60c692f6e391f839829dfc64e93380db54cd507b; actual MSVC19.29.30146
x64 C++20/W4/WX compile/run passed. Nine new tests cover all operation frames,
full frozen/ISC binding, metadata and exact-set mutations, policy/root
counterchecks, strict native output parsing and source reproduction. Signatures,
content/root preimages, domain/configuration metadata and native exporter
authentication remain unproved. Native cc98f15a certificate semantics is retained.
Component execution is not reactor/WAL/recovery, complete public CloseInput or
Feature010 acceptance.

Verification: 284 tooling/38 oracle, 33 legal/112 illegal legacy traces, Ruff and
syntactic consistency pass. New fixture/harness/component results are byte-exact;
all preceding 322 generated files plus six prior ISC/certificate-chain artifacts
are unchanged. Lean, all 21 TLA modules, schema/runtime/native/public fixtures are
unchanged. Semantics remains
sha256:c0e7baa47535a52378158b2f28d8a1e138c5b020d698a537badc7f1a5b650795.
No fresh Lean/TLC/production mutants; retained 1007-job build, 44/45 audit,
28 safety/7 liveness/27 mutants and 132-state/131-step path retain bounded scope.
Phase0 remains unfrozen; make unavailable; aggregate formal-check is not claimed.
Three demos returned HTTP200 without restart and frozen refs remain unchanged.

Next derive/check the actual immutable native admission snapshot's state/config/
closed-input binding against complete public pre-state, preserving distinct
commitment/content/AC/root identities and explicit provenance. Do not equate the
native RoundState summary with all 64 public variables or infer live availability
from a flat historical attester list. Establish missing root/closed-set contracts
before accepting non-arithmetic PublicDurablePrefix branches; keep the mixed
legacy prefix fail-closed. CONFIG/VIEW/ABORT, phase/send/delivery/QC/current/crash/
unknown composition and nativeArithmeticRecoveryRefines remain open. Native
bounded adapters/WAL/admission, arbitrary snapshots/failures/repair, freeze, clean
reproduction and independent reviews remain mandatory. No original GO or local
SIMULATED_LOCAL PASS has been issued.


## 2026-09-25 native admission snapshot component boundary

T044/T048/T049/T053/T057/T060. Continued from source f49e5fe / report 978551d.
Compiled eight unchanged PR50 translation units and executed 66 native
policy/admission cases. Exact DRC1 RoundState/Vote bytes and ISC body identities
are retained and independently checked; these are binary core envelopes, not
certificate JSON or a full 64-variable public state. Eleven stale-state cases,
closed-set/body/context/config/epoch/schema/profile substitutions and live
sequence/readiness/parent/deadline violations reject. Both PARAMETER and APPLY
pass fixture policy validation and reject at the authoritative arithmetic-input
guard in live and recovery. No mutant macro or runtime edit was used.

Counterchecks precisely bound the missing producer relation: a rehashed inner
state root changes state_id but supplies no complete public preimage; rebound
ISC root/commitment/AC plus candidate/closed IDs can pass at the same state_id.
The synthetic ISC fixture also passes without a finalized-config assertion.
The component consumes trusted prepared authority; these findings are not a
claim of attacks on the complete production pipeline. Native runtime separately
serializes/binds policy identity and invalidates it after state commands; that
origin/WAL contract remains to be connected and is not executed here.

Scope formal/proposals/native-admission-snapshot.md; evidence
formal/proposals/evidence/native-admission-snapshot.json. Ten new tests cover
actual responses, exact original bytes/hash inputs and strict bounded flat
DRC1 decoding, including all truncated state prefixes and changed diagnostics.
Full checks: 294 tooling/38 oracle, 33 legal/112 illegal legacy traces, targeted
Ruff/consistency; new fixture/harness/native results byte-exact. All prior 322
files plus nine prior component artifacts unchanged. No Lean/TLA/schema/runtime
or old native/public fixture changes; no fresh Lean/TLC/production mutants.
Semantics stays sha256:c0e7baa47535a52378158b2f28d8a1e138c5b020d698a537badc7f1a5b650795.
Retained build1007/audit44of45 and bounded28safety/7liveness/27mutants plus
132state/131step path remain their prior scope. Phase0 is unfrozen, make is
unavailable, aggregate formal-check is not claimed. Demos remain healthy without
restart; frozen refs unchanged. Formal and local acceptance remain NO_GO.

Next bind the actual complete policy serialization/identity at runtime open and
replay, and locate its independently authenticated producer. Preserve exact
native state/config/candidate/closed-body identities without claiming that a
policy hash proves public CloseInput or all64 state fields. Establish the actual
root/commitment/content/live-availability bridge before enabling non-arithmetic
PublicDurablePrefix; unavailable provenance remains explicit. Full phase/send/
delivery/QC/current/crash/unknown composition and nativeArithmeticRecoveryRefines
remain open, plus general bounded adapters/WAL/admission, arbitrary snapshots/
failures/repair, contract freeze, clean reproduction and independent review.


## 2026-09-25 exact native policy/WAL identity and local replay

T044/T048/T049/T053/T057/T060. Continued from 6cee903 / NO_GO overlay925faca.
Twelve unchanged PR50 translation units execute62 codec/runtime observations in
fresh isolated Windows directories. Native policy DVPOL001 bytes are retained,
nine action fixtures roundtrip; all1920 ISC truncated prefixes and five malformed
cases reject. A syntactic inventory covers all33 snapshot fields in declaration/
encoder/decoder order, not general injectivity.28native Git blobs pinned.

Actual native Runtime/WAL persists full-policy SHA256 as64ASCIIhex in each vote
entry, independently of native state_id. Eight valid changed policies reject
reopen against existing vote WAL; the same policies can open empty directories,
which authenticates no producer. Missing policy also rejects durable votes.
Caller mutation after open leaves runtime's by-value policy unchanged. Record,
retry, conflict, snapshot and reopen preserve exact original DRC1 vote and native
DVREC001 receipt; replay is separate metadata and encoded replay byte stayszero.
A separate ISC+FINALIZE_INPUT_FREEZE history preserves historical receipt through
state command/reopen and rejects a fresh vote without append. This is not ApplyQC
current advancement or the original public trace; old5/6/8 bytes remain untouched.

Six native exception crash hooks: before/partial/named-prebarrier recover0votes;
durable-before-commit and both pre-return hooks recover1vote with identical retry
receipt. Missing receipt therefore does not imply absent vote. IMPORTANT actual
source: named after_wal_append_before_durability throws BEFORE append_and_sync,
not a real uncertain barrier; after_effect_copy_before_return shares the same
pre-return branch, not a tested transport-copy failure. Partial diagnostics stay
incomplete until actual native recovery scans/truncates. Corrupt WAL/snapshot
reject. Both arithmetic record_vote calls reject under unchanged guard, noappend.
Actual Windows fflush/_commit/snapshot calls ran; noOSkill/powerloss/POSIXcustody,
FFM/sidecar/network/full-public recovery claims. Producer inspection is read-only:
FFI/sidecar accept configured opaque policy bytes; Java copies them; fixture
exporter produces test policies. Complete authenticated public-source derivation
remains missing. Native old semantics is not candidate authority.

Scope formal/proposals/native-policy-wal.md; evidence formal/proposals/evidence/
native-policy-wal.json. Eleven new tooling tests;305tooling/38oracle,
33legal/112illegallegacy,Ruff/consistency PASS. New fixture/harness/full native
results reproduce byte-exact; previous322generated+12componentartifacts unchanged.
NoLean/21TLA/schema/runtime/old native/publicfixture changes; semantics remains
sha256:c0e7baa47535a52378158b2f28d8a1e138c5b020d698a537badc7f1a5b650795.
No freshLean/TLC/productionmutants: retained1007build/audit44of45 andbounded
28safety/7liveness/27mutants,132state/131steppath keep their scope. Phase0unfrozen;
makeunavailable, aggregateformal-check notclaimed. DemosHTTP200 no restart and
frozenrefs unchanged. No originalGO or SIMULATED_LOCAL PASS.

Next compose the actual policy/WAL/receipt relation with mandatory Lean/public
recovery using explicit DVPOL001/DRW1/DVREC001 adapters; begin with durable policy
identity and original canonical receipt binding, not proposal JSON renamed as
native bytes. Initial policy producer, full public CloseInput/configuration/
commitment-content-availability/root relation, phase/send/delivery/QC/current,
arbitrary snapshots/failures/repair and unknown outcomes remain open. The general
nativeArithmeticRecoveryRefines, contract freeze, clean offline reproduction,
independent reviews and joined runtime/profile/GPU/Docker evidence remain required.


## 2026-09-25 native DVREC001 structural inverse and byte identity

T044/T048/T049/T053/T057/T060. Continued from643bbf3 / NO_GO overlay47e81ab.
NativeReceiptBytes.lean implements actual binary receipt-container fields and
proves general bounded big-endian/length-section inversion, complete roundtrip,
encoding injectivity, canonical decoded bytes and exact field preservation.
Operational replay does not alter bytes. The native16MiB/frame/71byteID/4096text
bounds and complete consumption are explicit; encoded length is derived.

This is STRUCTURAL container validity, not full native semantic receipt parsing:
DRC1 frame fields, native domain-separated SHA/ID-to-frame relation and admission
remain open. An explicit kernel countercheck accepts unauthenticated frame/ID
bytes with valid structure. Do not treat this as parser equivalence or authority.
NativeReceiptVectors retain nine original native frames/exact receipts; full
encoding proofs use components and decoder results use the general inverse.
Reserved-byte rejection uses a general theorem. Small edge/counterexamples cover
sequence/action/text/section limits and UINT64 maximum. All declarations audited.

Nine unchanged PR50 translation units execute nine operational codec cases and
27 negative checks (reserved/trailing/hash mismatch). All replay bytes identical.
Native hash mismatch rejects despite valid container shape. PARAMETER/APPLY are
CODEC-only cases, not admitted votes; no nativeRuntime/WAL/arithmetic/network run
is newly claimed. Prior62 runtime/WAL observations stay separate and unchanged.
Scope formal/proposals/native-receipt-codec-proof.md; source-bound evidence
formal/proposals/evidence/native-receipt-codec.json. No full recovery theorem or
GO/local PASS. Full formal tests/build/refinement/reproduction and their exact
counts are retained in that machine-readable evidence. Semantics changes because
mandatory Lean inputs change, not because runtime/TLA transitions were edited.

Next bind complete DRC1 vote field parsing/canonical encoding and actual vote-ID
hash preimage to this container, then connect original canonical receipt and
policy identity to native WAL decoding/replay and the reachable public history.
Do not assume an expected receipt/whole-body translation or accept an approval
Boolean. Initial policy provenance, full public CloseInput/configuration/phase/
send/QC/current/unknown composition and nativeArithmeticRecoveryRefines remain
open. Contract freeze/offline reproduction/independent reviews and joined native
profile/GPU/Docker evidence are still required. Healthy demos remain reserved.

Final frozen-source verification: full Lean1009 jobs, fresh receipt/vector kernels,
115 declaration audits (propext/Quot.sound only),19 general helpers/52 examples;
311tooling/38oracle/6targeted,33legal/112illegal legacy,Ruff/consistency PASS.
324 files (306JSON/16generatedLean/inputTLA/config) reproduce byte-exact;15prior
native component/WAL artifacts unchanged. All21TLA/schema/runtime/147native
witnesses unchanged;145legacy traces change only semanticID. New semantics:
sha256:2baf77eb5d992dd403e1c5de86660da993be337024f86720ffac3218d06b70fd.
Mandatory44/45 remains FAIL for nativeArithmeticRecoveryRefines. No fresh TLC or
production mutants; earlier28safety/7liveness/27mutants and132state/131steppath
retain finite scope. Phase0 unfrozen, make unavailable; aggregate formal-check
not claimed. DemosHTTP200, no restart, frozenrefs unchanged. Only final successful
source checks count; draft recursion/syntax/source-selector failures superseded.


## 2026-09-25 native DRC1 vote and semantic receipt binding

T044/T048/T049/T053/T057/T060. Continued from51dd421 / NO_GO overlay85312de.
NativeVoteBytes.lean reads the actual binary VOTE header and all13 ordered fields,
checks default native text/envelope limits, canonical uint64 decimals, content IDs,
nonempty printable identifiers and exact common constants. It retains the old
native accepted semantics; candidate semantics are not silently substituted.
Frame inverse/injectivity and soundness derive all fields and numeric bounds.
The complete DVREC001 decoder now checks actual frame/sequence/context/action
and the domain+NUL+full-frame SHA input. Digest width/hex spelling are computed;
SHA itself and signatures/admission remain explicit outside this proof.

The nine original native receipts are reused unchanged. Finite exact-preimage
SHA lookups are fixture adapters only, not general SHA/native authentication.
Each complete receipt is composed through generic checked component lemmas;
modified sequence/context/action/ID rejects. The prior structurally accepted
unauthenticated container now fails the semantic decoder. Small text/decimal
boundary checks include uint64 maximum, overflow, leading zero and bad tags.

Three unchanged native units execute49 parser/SHA cases:12 accepted/37 rejected.
The native VOTE parser accepts nonempty unknown kind; DVREC action binding is the
separate closed nine-kind rule. All accepted native frames re-encode exactly.
This is new codec execution, not Runtime/WAL, arithmetic admission, TLC or new
production mutants. Prior native component/WAL evidence stays unchanged.
Scope formal/proposals/native-vote-codec-proof.md and source-bound machine evidence
formal/proposals/evidence/native-vote-codec.json retain final checks and counts.

Next connect these original semantic receipts to actual DVPOL001 policy and DRW1
WAL entry parsing/replay. Preserve initial policy provenance and complete public
state/phase/CloseInput/send/delivery/QC/current/crash/unknown relation as open until
proved. Do not confuse parsed receipt with authorized vote, response exposure,
network delivery or durable recovery; missing response does not prove absence.
The remaining nativeArithmeticRecoveryRefines theorem stays mandatory and OPEN.
Contract freeze/offline reproduction/independent review and joined runtime/GPU/
Docker gates are still required. No formal GO or separate local PASS is issued.

Use explicit typed computation witnesses in future kernel examples. A metavariable
argument to a theorem about decode can trigger evaluation of the entire closed
parser during unification. Generic transport lemmas and explicit arguments avoid
that redundant reduction. Earlier unfinished UTF8/namespace/implicit-argument
and tactic-scope drafts are not passing evidence; only final stable logs count.

The nine actual PR50 codec fixtures are separate sequence1 examples, not one
combined nine-vote execution or the legacy proposal5/6/8 history. Actual Runtime
WAL sequence counts BOTH state transitions and votes; its recovered vote-count
and protocol state durable-sequence are different quantities. The next bridge
must preserve these distinctions when deriving original DVREC sequences.

Final stable-source verification: full Lean1011 jobs, fresh generic kernel and
270 named declaration audits PASS (25 general helpers,182 component/kernel
proofs,63 executable/sample definitions). The standalone final vector kernel
also passed before the mandatory build. 318tooling/38oracle/7targeted,
33legal/112illegal legacy,Ruff/consistency PASS.326files (307JSON/17Lean plus
inputTLA/config) reproduce byte-exact. All21TLA/schema/runtime/147native witnesses
are unchanged;145legacy traces only semanticID.15prior native component/WAL
artifacts retain exact hashes. New semantics:
sha256:30153d01cc15ebcacfbcb8786ef2f6e48f09921dbc2bd1a2f33ae07f649c8ed2.
Mandatory44/45 still FAIL for nativeArithmeticRecoveryRefines; no fresh TLC/new
mutants. Retained28safety/7liveness/27mutants and132state/131step path remain
bounded. Phase0 remains unfrozen, make unavailable, aggregate formal-check not
claimed. Three demos HTTP200/no restart, frozen refs unchanged. NO_GO persists.

## 2026-09-25 — DRW1 entry and original receipt/policy binding

T044/T048/T049/T053/T057/T060, amendment 0001. The candidate remains NO_GO.
Scope: formal/proposals/native-wal-codec-proof.md. Evidence is recorded in
formal/proposals/evidence/native-wal-codec.json after the final stable checks.

NativeWalBytes.lean reads the actual DRW1 header, total length, uint64 sequence,
record kind/reserved bytes and all four sections. General inverse, injectivity
and successful-decode proofs retain the entire checksum preimage and exact
canonical bytes. SHA remains an explicit adapter; implementation equivalence,
cryptography and physical durability are not proved. Structural decoding,
single-frame scanning and runtime sequence admission are deliberately separate.
The structural native format permits sequence zero and an empty vote policy
section. The scanner enforces 72-byte minimum and 64 MiB maximum, reports short
headers/incomplete declared frames as torn, and rejects corrupt complete headers.
The all-entry position theorem counts state commands as well as votes.

The composed checker binds a parsed WAL entry to the actual semantic native
receipt and original vote frame, sequence and startup-policy digest. Policy ID
is 64 lowercase ASCII SHA hex bytes over the complete provided policy, with no
vote-ID prefix. Policy decoding, initial producer provenance and runtime
admission remain open. A valid checksum does not supply those premises.

Generated examples reuse three actual retained native frames: the original ISC
vote and the separately configured ISC-plus-state-command history. Both vote
records remain at sequence 1, the command is sequence 2, and historical retry
retains the original semantic receipt. No native frame is renumbered to the
separate proposal history 5/6/8. Exact-preimage digest samples are finite; small
structural counterchecks explicitly use synthetic hashes. Generator checks also
retain three actual complete-but-unexposed records; missing response never
implies absent durability. No new native execution, power-loss/OS-kill test,
unknown-outcome resolution or arithmetic admission is claimed.

Next: compose complete-file scanning and sequence validation, including exact
validated-prefix bytes and unresolved torn tails, with native replay. Then bind
state-command results/logical time/request deduplication, original vote admission
and policy, snapshots and independently authenticated public histories. The
single-frame/receipt relation does not reconstruct those states or discharge
nativeArithmeticRecoveryRefines. Full CloseInput/configuration/availability/
phase/send/delivery/QC/current/crash/unknown composition, contract freeze, clean
offline reproduction and independent reviews remain required. Native arithmetic
guards and the healthy demonstrations remain unchanged.

Final stable-source verification: full Lean 1013 jobs, fresh generic kernel and
113 explicit helper/function/example axiom audits PASS (16 general theorems,
50 component/kernel proofs, 47 definitions). Only propext/Quot.sound/
Classical.choice are permitted; no new axiom or proof hole. 326 tooling,
38 oracle and 8 targeted tests; 33 legal/112 illegal legacy traces;
Ruff/consistency PASS. All 328 generated files (308 JSON/18 Lean plus input TLA
and config) reproduce byte-exact. New semantics: sha256:d369d4f6b36d10923f8f8cfb85b70b03b83cd7b1f8b23f5874ba664442e1fa14.
All 21 TLA modules, public schema, runtime and 147 native witnesses are unchanged;
145 legacy traces change only semantics ID. The 15 prior native component/WAL
artifacts retain exact hashes. No fresh TLC/native run or new production mutant
is claimed; retained 28 safety/7 liveness/27 mutants and the 132-state/131-step
arithmetic path keep their finite scope. Mandatory coverage remains 44/45 FAIL
for nativeArithmeticRecoveryRefines. Phase0 remains unfrozen; make is unavailable
and aggregate formal-check was not executed. Formal/local GO remain absent.

Maintenance during verification: Presentation8870 and Controller8865 were found
stopped (connection refused); cause was not established. The existing launcher
restored both on the same c8aea649 baseline without source/UI/training changes.
Node8872 stayed online and was not restarted. All pages return HTTP200, including
Verification RU. The saved job57af5edb42364e33ab6049a4a37a289e canonical report was
rehash-verified against original SHA256
91d612026a425e6d11b86c0d90c2d54c976dc8bfcd90f9127c9d845c2cfce861.
Frozen refs remain unchanged. See native-wal-codec/demo-recovery.json; do not
describe this run as having required no restart.

## 2026-09-26 — complete observed-byte WAL scan and original sequence

T044/T048/T049/T053/T057/T060, amendment 0001. NO_GO remains in force.
Scope: formal/proposals/native-wal-scan-proof.md. Final evidence is retained in
formal/proposals/evidence/native-wal-scan.json after stable checks.

NativeWalScan.lean composes the DRW1 reader over all supplied bytes, starting
from an empty prefix. Actual checked scan steps derive exact original frames,
their order, the consumed byte prefix and unresolved tail. The input-length
recursion budget is proved sufficient; failure derives a reachable corrupt
frame rather than fuel exhaustion. A corrupt later complete frame rejects the
whole scan. Torn bytes remain explicit; nothing is truncated or exposed.

A separate checker validates every native WAL sequence from 1, counting both
votes and state commands. It derives original sequence at each position and
uniqueness. Its indexed receipt theorem composes the actual semantic receipt/
policy checker to retain original frame, receipt and WAL bytes. It does not
prove vote admission, policy semantics/provenance or runtime replay readiness.
Omitting an interior entry fails sequence checking; omitting an entire suffix
cannot be detected from the remaining bytes alone. Complete means complete for
the supplied observation, not an authenticated complete physical WAL.

Examples retain the exact prior native 3546-byte ISC-plus-command history
(823+2723 bytes, original all-entry sequences 1/2) and actual 411-byte partial
write. Existing original receipts are unchanged. These are not new native runs
and are not the separate proposal arithmetic sequence 5/6/8. Small corruption,
sequence and tail counterchecks use a separately labeled synthetic digest.
Finite native hash samples do not prove SHA or the C++ implementation.

Next compose these parsed original entries with actual native state-command,
logical-time, request/vote-cache, policy/admission and snapshot reconstruction,
then independently authenticated public histories. Physical scan provenance,
crash/unknown presence/absence, complete public phase/send/delivery/QC/current
composition and nativeArithmeticRecoveryRefines remain OPEN. Contract freeze,
clean offline reproduction, independent review and joined profile/GPU/Docker
gates remain required. No formal GO or local acceptance PASS is issued.

Final stable-source verification: full Lean1015 jobs, fresh generic kernel and
75 explicit helper/function/example audits PASS (24 general theorems,32
component/kernel proofs,19 definitions). Only propext/Quot.sound/Classical.choice
are permitted; no proof hole or new axiom. 329tooling/38oracle/3targeted,
33legal/112illegal legacy,Ruff/consistency PASS. All328 generated files
(308JSON/18Lean plus inputTLA/config) reproduce byte-exact. New semantics:
sha256:8d31089d613753beb158307a9b4de0b463798e5ae2449c6f6bf9328b8e76bf4e.
All21TLA/public schema/runtime/147native witnesses are unchanged;145legacy
traces only change semanticsID.15prior native component artifacts retain exact
hashes. No freshTLC/native run or production mutant is claimed; retained
28safety/7liveness/27mutants and132state/131step path keep bounded scopes.
Mandatory44/45 still FAIL: nativeArithmeticRecoveryRefines remains missing.
Phase0 remains unfrozen; make unavailable/aggregate formal-check not executed.
All three demos HTTP200 without restart in this stage; frozen refs unchanged.
The previous stage's recorded service restoration is not erased by this check.

## 2026-09-26 — native state/command codecs and original scanned fields

T044/T048/T049/T053/T057/T060, amendment 0001. NO_GO remains in force.
Scope: formal/proposals/native-state-codec-proof.md; final machine-readable
evidence: formal/proposals/evidence/native-state-codec.json.

NativeStateBytes.lean parses all11 native COMMAND and all14 ROUND_STATE fields,
retaining exact original canonical bytes. General inverse/success/injectivity
proofs cover both concrete layouts. Ticket counts use unsigned64 binary tags
with semantic uint32 bounds and ordered counts; sequence/height/view/logical
tick use canonical uint64 decimal text. Actual native phase names, identifier
syntax, fixed schema/native semantics and default text/envelope bounds are
checked. The native summary state is not the complete64-variable public model.

The new inspector derives the command and recorded next-state from actual DRW1
entry sections and composes with the whole-byte scanner to retain original
bytes and all-entry sequence. Effects and inner-WAL sections stay opaque here.
This is not transition recomputation or recovered-state equality. The actual
retained journal command is entry2, while the encoded state transition count is
1. The preceding vote and original receipt retain sequence1; proposal5/6/8 is
separate. Domain/NUL/frame hash preimages are bound, with SHA still explicit.

A fresh isolated harness executes55 native codec cases against three unchanged
translation units from pinned60c692f6:12accept/43reject, exact re-encoding and
content-ID comparison. No Runtime/crash/arithmetic admission run or production
mutant is claimed. Examples reuse original configured state/command/next-state
bytes and finite hash samples. Known unknown-command and substituted-valid-root
acceptance is preserved explicitly: these pass parsing but confer no transition
authorization. Self-run source-pinned native logs are not independent attestation.

Next reconstruct the actual native transition/effects/inner-WAL, then logical
time, request and vote caches, startup policy/admission and snapshots. Preserve
independently authenticated input/file provenance and distinguish known records
from missing responses and unknown/incomplete diagnostics. Full public/native
state/action/send/QC/current/recovery composition and nativeArithmeticRecoveryRefines
remain open, with contract freeze/offline reproduction/independent review and
joined runtime/profile/GPU/Docker gates still required. Healthy demos and native
arithmetic guards remain unchanged; no formal or local GO follows.

Final stable-source verification: full Lean1017 jobs, fresh generic kernel and
165 explicit helper/function/example audits PASS (28 general theorems,90
component/kernel proofs,47 definitions). Only propext/Quot.sound/Classical.choice
are permitted; no proof hole or new axiom. 337tooling/38oracle/8targeted,
33legal/112illegal legacy,Ruff/consistency PASS. All330 generated files
(309JSON/19Lean plus inputTLA/config) reproduce byte-exact. New semantics:
sha256:63eacbf671e2ecb489a2fc18f51a21f952b3e674a0a0120f01cbc6e14644a25f.
All21TLA/public schema/runtime/147native witnesses are unchanged;145legacy
traces only change semanticsID.15prior native component artifacts retain exact
hashes. A fresh55-case codec harness (12accepted/43rejected) compiled three unchanged
native translation units; no fresh Runtime/crash/TLC/production mutant is claimed; retained
28safety/7liveness/27mutants and132state/131step path keep bounded scopes.
Mandatory44/45 still FAIL: nativeArithmeticRecoveryRefines remains missing.
Phase0 remains unfrozen; make unavailable/aggregate formal-check not executed.
All three demos HTTP200 without restart in this stage; frozen refs unchanged.
The previous stage's recorded service restoration is not erased by this check.

## 2026-09-26 — computed native command transitions and exact stored outputs

T044/T048/T049/T053/T057/T060, amendment 0001. NO_GO remains in force.
Scope: formal/proposals/native-transition-proof.md; final machine-readable
checks: formal/proposals/evidence/native-transition.json.

NativeTransition reconstructs all seven pinned summary commands from parsed
prior state and command. Exact phase/context/count/view/sequence guards precede
computed updates. Config replay retains its counter; other commands check and
increment it. Dynamic decimal/output encoding is validated. General helpers
derive enabled guards, original context, immutable fields, exact sequence,
computed state and complete effect/inner-WAL construction with actual hash
preimages. No caller-provided result predicate or recovered-state equality.

replayEntry recomputes all three stored output sections. scannedExecution
composes actual entry execution with byte-scan sequence/frame provenance.
Initial state remains an explicit input; full mixed native vote/command replay
and complete public protocol refinement are not claimed. SHA remains explicit;
fixture samples and self-run logs do not authenticate native export/custody.

A fresh source-pinned native core harness executes59 cases (21accept/38reject),
covering all42 phase/command combinations, context/count/view/sequence limits
and all ten native transition error categories. Exact three byte outputs/five
content IDs match Python reconstruction. Lean also reuses the original freeze
entry's full outputs, WALsequence2 versus statecounter1; prior vote sequence1
and separate arithmetic proposal5/6/8 remain unchanged. No new Runtime/crash/
arithmetic-admission run or production mutant is claimed.

The explicit old-clock and aggregate-without-QC counterchecks distinguish this
pure core from runtime policy and public certificate authority. Next derive
mixed replay time/request/receipt caches, policy/authority invalidation and
snapshot checks, then independently authenticated public histories and unknown
recovery. Contract freeze/offline reproduction/independent reviews and joined
runtime/profile/GPU/Docker gates still block GO. Healthy demos/native guards
remain unchanged.

Final stable-source verification: full Lean1019 jobs, fresh generic kernel and
317 explicit helper/function/example audits PASS (24 general theorems,119
component/kernel proofs,174 definitions). Only propext/Quot.sound/Classical.choice
are permitted; no proof hole or new axiom. Three generated-vector unused-simp
warnings remain informational. 345tooling/38oracle/8targeted,
33legal/112illegal legacy,Ruff/consistency PASS. All332 generated files
(310JSON/20Lean plus inputTLA/config) reproduce byte-exact. New semantics:
sha256:f4b40752107e38cc96254a11badbb4144b062efad28c4e79e80b315b9c73ee88.
All21TLA/public schema/runtime/147native witnesses are unchanged;145legacy
traces only change semanticsID.15prior native component artifacts retain exact
hashes. A fresh59-case core harness (21accepted/38rejected) compiled four unchanged
native translation units; no fresh Runtime/crash/TLC/production mutant is claimed; retained
28safety/7liveness/27mutants and132state/131step path keep bounded scopes.
Mandatory44/45 still FAIL: nativeArithmeticRecoveryRefines remains missing.
Phase0 remains unfrozen; make unavailable/aggregate formal-check not executed.
All three demos HTTP200 without restart in this stage; frozen refs unchanged.
Earlier recorded service restoration remains retained; no restart in this stage.


## 2026-09-26 — computed command recovery, cached receipts and typed snapshots

T044/T048/T049/T053/T057/T060, amendment0001. NO_GO remains. Scope:
formal/proposals/native-command-replay-proof.md; machine evidence:
formal/proposals/evidence/native-command-replay.json.

NativeCommandReplay derives actual command-only execution from parsed initial
state and an empty request cache at outer sequence0. Every entry is checked at
its next position, decoded and computed through NativeTransition; all three
stored outputs must match. Induction proves cache extension and origin,
sequence/count, unique request IDs, original receipt fields and monotonic
policy-clock updates. Retry uses saved command ID before fresh state/time
admission and returns the original receipt with replay=true, without append.
No caller-supplied transition result or recovered-state equality is assumed.

Positive snapshots compare exact replayed state at their own position; a
general theorem extracts that entry. Sequence-zero snapshots are parsed but
not required by actual runtime to equal initial/final state. Final state is
always replayed. The observed-byte API rejects torn/incomplete input, grants
no truncation/absence/readiness/exposure, and requires separate physical-file
authentication. DRS1 snapshot metadata and optional policy initial clock are
typed inputs here, not decoded/authenticated native policy authority.

Votes explicitly reject; the original mixed ISC1/freeze2 example is not claimed
as a recovered command-only log. One step keeps originalsequence2; a separately
mathematical single-command sequence1 case reuses checked native components.
Original native bytes and proposal arithmetic5/6/8 are unchanged. A fresh local
Windows runtime/WAL harness compiled12 unchanged pinned units and ran22cases:
11accept/11reject. A separate live freeze/view/abort journal has actual1/2/3,
snapshot2 and exact first receipt retry after movement/reopen. Rehashed output,
order/gap/duplicate, backwards-time and snapshot substitutions reject. Native
empty effect/record cases reject structurally; Python also substitutes nonempty
sections to test semantic recomputation. No OS power-loss, native arithmetic,
mixed vote recovery, authenticated exporter or new production mutant claim.

Final stable-source checks: fullLean1021 jobs, fresh generic kernel, all86names
(31general helpers,33component/kernel proofs,22definitions) axiom-audited with
only propext/Quot.sound/Classical.choice. New modules have no warnings/holes;
three earlier NativeTransitionVectors unused-simp warnings are retained.
353tooling/38oracle/8targeted,33legal/112illegal legacy,Ruff/consistency PASS.
All332files(310JSON/20generatedLean/inputTLA/config) reproduce byte-exact; the two
new Lean modules are hand-authored. Semantics sha256:f08d975cb2fe36f0b943f79d3756610b8574bc4cfc98a4b001e8a7297fa7bb89.
All21TLA/schema/runtime/147native witnesses unchanged;145legacy traces only
semanticsID. No new TLC/mutant suite; prior28safety/7liveness/27mutants and132state/
131step path retain bounded scopes. Mandatory44/45 still FAIL with
nativeArithmeticRecoveryRefines missing. Phase0 unfrozen; make unavailable,
aggregate formal-check not executed. All3demos HTTP200/no restart/frozenrefs
unchanged this stage; earlier recorded service restoration remains retained.

Next derive full native policy codec/admission for intervening votes, compose
mixed replay and actual snapshot/scan provenance, then join the complete public
protocol relation. Contract freeze/offline reproduction/independent reviews and
runtime/profile/GPU/Docker acceptance remain mandatory; no local PASS or GO.


## 2026-09-26 — Complete DVPOL001 policy byte grammar (T044/T048/T049/T053/T057/T060)

- Added NativePolicyCodec/NativePolicySchema/NativePolicyBytes and small kernel examples to the mandatory Lean project. Complete native wire inventory: 35 record schemas, 238 fields, all 33 immutable snapshot fields and 15 candidate parent fields. Every nested body/certificate/vector is parsed, retained and re-encoded; this is not an opaque policy digest or a finite accepted-policy table.
- Eighteen general helpers prove structural encode/parse inversion with arbitrary suffix, encoding injectivity, complete accepted payload retention, bounds and computed policy-header/candidate extraction. Canonical shape checks preserve native validator ordering, role/abort vocabulary, candidate tuple order and global context uniqueness. Signed rational words retain all64 bits, with explicit signed64 interpretation. Native reserve/allocation/exception/preflight behavior is not proved.
- Thirty component/kernel proofs plus59 definitions: all107 named definitions/theorems axiom-audited, only permitted propext/Quot.sound/Classical.choice. The complete minimal Lean policy is a mathematical codec example with empty identifiers; it does NOT satisfy native startup authority. Inverted deadlines/zero denominators/empty body IDs may parse structurally and remain admission failures. Snapshot duplicates/order are preserved, not silently normalized.
- Fresh unchanged C++ codec execution:51cases (22accept/29reject),12pinned translation units/28blobs from60c692f6e391f839829dfc64e93380db54cd507b, MSVC19.29.30146 strictflags. Nine original native action policies plus a separately populated complete synthetic snapshot; every named native primitive and ordered list is compared with Python, not only re-encoded bytes. Distinct path-derived scalars test field order; signed/unsigned endpoints and malformed sizes/bytes/order/context cases retained. No Runtime handle/WAL/network/arithmetic execution or production-mutant suite is newly claimed.
- Nine tooling tests cover every238-field omission/extra key, exact native field inventory, full primitive comparison, all1920 original ISC truncated prefixes, bounds/signs, malformed/rehashed evidence and byte-exact generated schemas/examples. 362tooling/38oracle,33legal/112illegal legacy, Ruff/format/consistency PASS; full Lean1025jobs and fresh generic kernel/axiom audit PASS. 334files (310JSON/22generatedLean/inputTLA/config) regenerate byte-exact. All21TLA/public schema/runtime/147native witnesses unchanged;145legacy traces only semanticID. No fresh TLC/new mutants; earlier bounded scopes retained.
- Semantics sha256:a7dd77c9401efcf948a8df4ed03496a66eec5bc79ce3d3a96b599a75cc74784c. Evidence formal/proposals/evidence/native-policy-codec.json; scope formal/proposals/native-policy-codec-proof.md. Full policy startup state/certificate/committee/context authority and actual live/recovery admission remain next; mixed vote/command recovery still rejects in NativeCommandReplay. DRS1 decoder/physical provenance/repair, full public refinement, exporter authentication and independent review remain open. Mandatory44/45 still FAIL/nativeArithmeticRecoveryRefines missing; Phase0 unfrozen and GNU make unavailable, so aggregate formal-check is not claimed. No Formal GO/local acceptance PASS. Healthy demo/frozen refs preserved (machine evidence); previous restoration history retained.


## 2026-09-26 — computed CONFIG startup/admission from native bytes

T044/T048/T049/T053/T057/T060; amendment0001. Scope:
formal/proposals/native-config-admission-proof.md; evidence:
formal/proposals/evidence/native-config-admission.json. NO_GO remains.

NativeConfigAdmission checks a singleton CONFIG candidate with an empty
certificate graph, using complete DVPOL001 and actual DRC1 state/vote decoders.
It derives source lookups, initial-state content preimage, schema/profile IDs,
3f+1/local validator membership, candidate body/proposed membership, all15
parent fields, context/height/view and deadline checks. All27 non-config
snapshot vectors must be empty. SourceChecks is derived from successful
execution, not a supplied approval flag or recovered-state equality.

The vote gate retains original bytes and checks actor/epoch/round/current,
parent/body/context and sequence. Live admission requires ready; recovery can
run before ready but still rejects invalidation, wrong phase and hard-deadline
expiry. The configured initial tick is distinct from actual admission time.
A different candidate checkpoint can pass startup but fails vote admission.
A rehashed native summary root can pass supplied-state consistency; this is
explicitly not initialization authentication or complete public-state binding.

General helpers compose successful byte decoding and computed startup/vote
results; a complete original CONFIG example reuses the prior native vote and
kernel-checks its exact policy/state components. Two finite SHA samples remain
explicit. The low-level typed checkVote alone is not startup authority; only
fromBytes composes the full new gate. This is a strict subdomain, not admission
completeness for all CONFIG policies, certificates or the remaining8actions.

Fresh unchanged C++ comparison:54cases,29startup accepts/25rejects and8vote
accepts/46rejects.53supported cases agree with computed Python checks; a separate
nonempty abort graph accepts native startup but intentionally rejects this
subset.12unchanged units/28sourceblobs,MSVC19.29.30146,strictflags; no Runtime/WAL
or native arithmetic execution. Original native fixture bytes remain unchanged.

Final checks are recorded in the machine evidence: fullLean1027jobs,
20generalhelpers/109componentkernelproofs/35definitions,164audited names,
only propext/Quot.sound/Classical.choice;373tooling/38oracle/11targeted,
33legal/112illegal legacy,Ruff/consistency and335generatedfiles
(310JSON/23Lean/inputTLA/config) byte-exact. Two harmless unused-simp warnings
in bindConfigComplete and three earlier transition-vector warnings are retained.
Semantics sha256:eee605ca96b305530fcac0f8de8d5f157b66ccd611b0498326e0af062017e169.
No new TLC/production mutants; prior bounded scopes remain. All21TLA/schema/
runtime/147native witnesses unchanged;145legacytraces onlysemanticsID.
Mandatory44/45 still FAIL; nativeArithmeticRecoveryRefines missing, Phase0
unfrozen, make unavailable/aggregate formal-check not claimed. No local PASS.
Three demos healthy without restart this stage; frozen refs unchanged; earlier
service-restoration history retained.

Next compose this computed CONFIG gate with actual mixed command/vote replay,
full policy identity, original receipt/context/outer sequence and request cache;
then extend native graph/certificate admission and complete public refinement.
DRS1 decoding, independently authenticated startup/physical scans, unknown
outcomes/repair, arbitrary failures, contract freeze, clean offline reproduction,
independent reviews and runtime/profile/GPU/Docker acceptance remain mandatory.


## 2026-09-26 — Computed mixed CONFIG/command native WAL replay

T044/T048/T049/T053/T057/T060; amendment0001. Scope:
formal/proposals/native-config-replay-proof.md; evidence:
formal/proposals/evidence/native-config-replay.json. NO_GO remains.

NativeConfigReplay derives startup from the complete native policy/state bytes,
then folds actual CONFIG admission and NativeCommandReplay results in the same
outer journal. Complete policy digest, original vote/frame/receipt/parents,
command outputs and per-entry sequence are checked. Histories derive both cache
provenances, uniqueness, outer position and total command+vote cache count.
Positive snapshots compare the exact replay state at the chosen position;
for votes this is current state, not the empty WAL state section. Zero-position
snapshots retain the native parse-only comparison scope. Historical retries keep
original bytes/sequence after movement, while fresh invalidated votes reject.
Observed scans grant neither physical completeness nor READY/exposure.

Two Lean modules reuse original CONFIG components with four finite hash samples:
26 general helpers,21 component/kernel/composition proofs,20 definitions,67
axiom-audited declarations. The general next-command composition uses an actual
checked result; there is no new kernel-evaluated complete mixed native trace.
Original ISC1/freeze2 still rejects in this CONFIG-only gate; no filtering or
renumbering. All arithmetic/native fixture bytes and original5/6/8 remain.

Fresh native Runtime/WAL execution compiled12unchanged units/28sourceblobs at
60c692f6e391f839829dfc64e93380db54cd507b:32cases,14accept/18reject. A separate actual
CONFIG1/config-command2/view-command3/abort-command4 journal preserves original
vote and command receipts after movement and reopen. Wrong policy/outputs/order/
sequences/duplicates/snapshots/time reject. This is finite CONFIG/empty-graph
scope, not native arithmetic, all-vote recovery, physical power-loss, network,
production mutants or authenticated export. Final stable-source validation is
recorded in machine evidence; earlier draft failures do not count.

Next extend computed admission to actual nonempty certificate graphs and other
vote kinds, preserving original policy/current/body/provenance and mixed journal
ordering. DRS1 decoding/physical scan authentication/unknown resolution/repair,
full public protocol binding and nativeArithmeticRecoveryRefines remain open.
Mandatory44/45 is not completion of Feature010. Contract freeze, offline
reproduction, independent reviews and native/profile/GPU/Docker gates remain.
No local acceptance PASS or Formal GO; no runtime guard change.

Final stable-source checks: fullLean1029jobs, fresh generic kernel/axiom audit;
384tooling/38oracle/11targeted,33legal/112illegallegacy,Ruff/consistency PASS.
335files(310JSON/23generatedLean/inputTLA/config) reproduce byte-exact. New Lean
modules are hand-authored. All21TLA/schema/runtime/147nativewitnesses unchanged;
145legacytraces changed onlysemanticsID. No new TLC/productionmutants; previous
28safety/7liveness/27mutants and132state/131step path retain bounded scopes.
Semantics sha256:9343f18876b34e619f2f5e9273d0f14f204fd99393c0701d620805751453986b.
Only propext/Quot.sound/Classical.choice; new modules have no warnings/holes,
prior five unused-simp warnings retained. Mandatory44/45 still FAIL, Phase0
unfrozen; GNU make unavailable, aggregate formal-check not claimed. All3demos
HTTP200 without restart thisstage; frozenrefs unchanged. Earlier restoration
history remains retained. Continuation automation now references the durable
current instruction file; saved configuration was verified, stale Sep24 date
removed. No schedule or acceptance-scope change.


## 2026-09-26 — Computed native ISC proposal admission

T044/T048/T049/T053/T057/T060; amendment0001. Scope:
formal/proposals/native-isc-admission-proof.md; evidence:
formal/proposals/evidence/native-isc-admission.json. NO_GO remains.

NativeInputSetBody and NativeIscAdmission derive complete proposed ISC bodies
from decoded DVPOL trees and compare the entire expected context, ordered tuple
pairs, computed native body IDs and closed membership. Actual complete policy /
state / vote byte decoders compose startup and live/recovery checks; original
candidate parents, actor/epoch/current coordinates and sequence are retained.
General helpers retain exact body source trees/count/order and derive selected
body provenance. This subdomain has one ISC candidate and no finalized ISC or
later graph; it does not accept an admission Boolean or translated body table.

Three modules:28 general helpers,137 component/kernel proofs,50 definitions,
215 audited names. The original complete ISC policy/state/vote is composed using
three explicitly finite SHA samples and component byte/guard proofs. Actual
native body preimage is distinct from DVPOL bytes, certificate JSON and QC ID.
A source-backed kernel countercheck permits same ticket/different ordered
commitments, as native tuple shape does; ledger uniqueness remains separate.

Fresh unchanged C++ comparison:60cases,26startup accepts/34rejects,14vote accepts/
46rejects.59supported cases match computed Python; a valid native abort-request
graph explicitly rejects this subset. Rehashed root/tuple primitive and inner
state-root substitutions can pass supplied-snapshot consistency; authentication,
root preimage and live availability are not inferred.11tooling tests retain
these boundaries, original byte identities, full context/shape negatives and
strict result/scope checking. No new Runtime/WAL, arithmetic, network, TLC or
production-mutant execution is claimed. Original ISC1/freeze2 remains unsupported
by CONFIG-only mixed replay; no filtering or renumbering and original5/6/8 retained.

Next compose actual CONFIG/ISC admission with mixed WAL/receipt/snapshot replay,
then finalized certificate graphs and full public state/actions. DRS1 decoding,
physical scan/initialization/export authentication, unknown outcomes/repair,
full nativeArithmeticRecoveryRefines, contract freeze, offline reproduction and
independent review remain mandatory. Full Feature010 and local acceptance are
not complete. Final validation/source identity is recorded in machine evidence.

Final stable-source checks: full Lean1032jobs, fresh generic body/admission
kernels and axiom audit PASS.395tooling/38oracle/11targeted,33legal/112illegal
legacy,Ruff/format/consistency PASS.336files(310JSON/24generatedLean/inputTLA/
config) reproduce byte-exact. Only permitted propext/Quot.sound/Classical.choice;
all215new declarations audited. New modules have no proof holes or warnings;
five pre-existing unused-simp warnings retain their earlier scope.
Semantics sha256:4ab02965dff1e75c073a1d56b6a938cfc7f9f56abbd9bbcaa535ad46cee1bdd6.
All21TLA/schema/runtime/147nativewitnesses unchanged;145legacytraces changed
onlysemanticsID. No fresh TLC/productionmutants; retained28safety/7liveness/
27mutants and132state/131step arithmetic path remain bounded. Mandatory44/45
FAIL, Phase0 amendment unfrozen, GNU make unavailable; aggregate formal-check
not claimed. All3demos HTTP200, no restart thisstage, frozenrefs unchanged.
Source-bound report remains NO_GO; no local acceptance PASS or guard change.


## 2026-09-26 — Whole CONFIG/ISC candidate admission and original mixed WAL

T044/T048/T049/T053/T057/T060; amendment0001. Scope:
formal/proposals/native-proposal-replay-proof.md; evidence:
formal/proposals/evidence/native-proposal-replay.json. NO_GO remains.

Original ISC1/freeze2 uses a TWO-candidate CONFIG/ISC policy. The new general
NativeProposalAdmission checks the whole original canonical policy/list, every
candidate, all proposed ISC bodies and the exact original graph/state/body/
context/parent links. It derives original list/order/count and per-candidate
source provenance. Actual complete policy/state/vote decoders compose fresh
admission. No singleton policy is substituted under the old WAL policy ID.
Fourteen general helpers and15definitions;21 small component/kernel examples
and8fixture definitions reuse the existing original candidates and ISC graph.
All58names are audited. Component cases are not a new full-policy byte or Lean
mixed-history proof. Four inherited finite hash samples are not general SHA.

The shared Python fold has fixed computed CONFIG-only or CONFIG/ISC gates.
Historical receipt/cache lookup remains separate from fresh admission. Selected
parents and receipt action come from the actual selected vote, including ISC2.
Fresh unchanged C++ runs32cases(14accept/18reject) with both vote and command
receipts. Its first two entries and policy bytes equal the earlier original
ISC1/freeze2 observation exactly; subsequent view/abort are explicit3/4.
Both receipts survive current movement and reopening. No renumbering, filtering,
assumed recovered-state equality, changed runtime source or guard override.

Draft comparison caught a CONFIG-only action tag in the expanded Python receipt
encoder; final ISC receipt now matches native exactly. Repeated freeze reaches
native's AVAILABLE guard before the duplicate-cache check, so its retained
error category is core rather than the earlier CONFIG-case category8. These
are final corrected checker results, not production protocol changes.

The general Lean mixed replay join remains OPEN: NativeConfigReplay.lean still
has its original CONFIG-only gate. Next reuse one typed fold with a closed
computed admission result, compose both modes and kernel-check the actual
original ISC1/freeze2. Do not replace admission with callbacks or duplicate the
whole history proof. No full nativeArithmeticRecoveryRefines, all-graph/action
admission, authenticated snapshot/ledger/root/export/physical scan, unknown
resolution/repair, complete public refinement or Feature010 GO is claimed.
Contract freeze, offline reproduction, independent reviews and runtime/profile/
GPU/Docker gates remain mandatory. Diagnostic Python resource limits remain
smaller than native/Lean. Final validation details follow after stable checks.

Final stable-source checks: full Lean1034jobs, fresh general/vector kernels
and axiom audit PASS.407tooling/38oracle/12targeted,33legal/112illegallegacy,
Ruff/format/consistency PASS.336generated files(310JSON/24Lean/inputTLA/config)
byte-exact; the two new Lean modules are hand-authored. All58new names use only
propext/Quot.sound/Classical.choice; no new proof holes or warnings. Prior five
unused-simp warnings remain. All21TLA/schema/runtime/147nativewitnesses unchanged;
145legacy traces onlysemanticsID. No new TLC/productionmutants; previous bounded
28safety/7liveness/27mutants and132state/131step arithmetic path retained.
Semantics sha256:e98cca9a7d16d233a9af4729b92494da1e5bc6cf17bd7e94c8a16a6450b92992. Mandatory44/45 still FAIL;
phase0 unfrozen; make unavailable, aggregate formal-check not claimed. Three
demosHTTP200 with no restart thisstage, frozenrefs unchanged. Source-bound
report stays NO_GO; no local acceptance PASS or native guard change.


## 2026-09-26 — Shared computed CONFIG/ISC native recovery in Lean

T044/T048/T049/T053/T057/T060; amendment0001. Scope:
formal/proposals/native-mixed-replay-proof.md; evidence:
formal/proposals/evidence/native-mixed-replay.json. NO_GO remains.

NativeReplayAdmission defines closed computed CONFIG-only and CONFIG/ISC modes.
The existing NativeConfigReplay now uses one mode-indexed executable fold and
one inductive history, preserving full startup, positions, policy ID, computed
command state/effects, time, unique caches and exact snapshot matching. Selected
parents and CONFIG1/ISC2 receipt action are derived from actual admission.
Recovered vote and command caches have original checked log provenance, and
proposal cache entries retain complete original candidate/source/phase checks.
No external admission callback, recovered-state equality or renumbering.

A new generated module proves exact original TWO-candidate policy bytes using
existing byte components. Ten finite SHA preimages bind this original policy,
vote, contexts, ISC body and command state/effect/record outputs; not general
SHA or authentication. Small component proofs derive the original ISC1/freeze2
history and recovery, preserving both receipts/retries after invalidation.
Missing, repeated, reordered and wrong-policy records reject; fresh stale votes
reject while historical retries retain their bytes. Old CONFIG vectors pass in
explicit config mode. The prior32-case native execution remains retained evidence,
not a fresh native run. No combined new raw physical scan example is claimed.

Expensive concrete hash/recovery reductions were replaced with small general
component lemmas. Discarded draft resource failures are not final evidence.
Finalized certificate graphs, general DRS1 decoding, authenticated initialization/
ledger/root/physical-scan/export provenance, arbitrary failures/repair, complete
public/native recovery, nativeArithmeticRecoveryRefines, contract freeze,
offline reproduction and independent review remain OPEN. Unknown or missing
response never proves absence. Runtime/demo/frozen refs remain unchanged.
Final stable-source validation follows in the evidence record.

Final stable-source checks: full Lean1037jobs, fresh admission/replay/vector
kernels and axiom audit PASS.411tooling/38oracle/4targeted,33legal/112illegallegacy,
Ruff/format/consistency PASS.337generated files(310JSON/25Lean/inputTLA/config)
byte-exact. All206 named definitions/proofs in six affected/new modules audited,
including110new declarations; onlypropext/Quot.sound/Classical.choice. New modules
have no proof holes or warnings; five pre-existing unused-simp warnings remain.
All21TLA/schema/runtime/147nativewitnesses unchanged;145legacytraces onlysemanticsID.
No freshTLC/native execution/productionmutants; retained32nativecases(14accept/
18reject),28safety/7liveness/27mutants and132state/131step path keep earlier scopes.
Semantics sha256:2cd020e87c4d859d084e22bc7d866a6fe32ab13a12f0b062bc9f4013920176ca. Mandatory44/45 FAIL; phase0 unfrozen;
make unavailable, aggregate formal-check not claimed. Three demosHTTP200 with
no restart thisstage, frozenrefs unchanged. Source-bound report stays NO_GO;
no local acceptance PASS, independent attestation or native guard change.


## 2026-09-26 — Complete native ISC certificate and finalized section in Lean

T044/T048/T049/T053/T057/T060; amendment0001. Scope:
formal/proposals/native-isc-certificate-proof.md; evidence:
formal/proposals/evidence/native-isc-certificate.json. NO_GO remains.

NativeIscCertificate reads the original complete certificate tree/wire, checks
configured context/3f+1 committee/2f+1 ordered signer membership, derives all14
canonical native JSON fields and separate QC/body content IDs. General helpers
retain original bytes/tree, exact fields and quorum provenance; failed hashing
rejects. NativeFinalizedIscSection checks the whole original certificate vector,
strict QC ordering and finalized-ID subset with actual policy/state readers and
recomputed state ID. This is an isolated section, not full graph/vote admission.
CONFIG/proposed-ISC replay modes were not widened. No fabricated proposal-membership
rule or callback substitutes for the native certificate relation.

Original native certificate and its exact section in retained codec-EC policy
are independently pinned and compared before generation. Kernel examples retain
actual JSON/wire and separate QC/body IDs; changed signer set changes this sampled
QC ID while preserving its body. Three finite SHA samples are not a general hash.
Separate mathematical set cases reject absent/duplicate/invented finalized IDs,
including substitution of the body ID. They do not claim a new whole policy/state
acceptance proof. Source provenance/crypto signatures/ledger/root/availability,
seed/EC/APC, full admission/recovery and nativeArithmeticRecoveryRefines remain open.
Contractfreeze, offline reproduction and independent review still required.
No fresh native/TLC/production-mutant run; original witnesses/runtime/demo preserved.
Final stable-source validation follows in the retained evidence.

Final stable-source checks: full Lean1040jobs, fresh certificate/section/vector
kernels and axiom audit PASS.417tooling/38oracle/6targeted,33legal/112illegallegacy,
Ruff/format/consistency PASS.338generated files(310JSON/26Lean/inputTLA/config)
byte-exact. All122 new named definitions/proofs in three modules audited:
25 general helpers/25 definitions and57 vector proofs/15 definitions; only
propext/Quot.sound/Classical.choice. New modules
have no proof holes or warnings; five pre-existing unused-simp warnings remain.
All21TLA/schema/runtime/147nativewitnesses unchanged;145legacytraces onlysemanticsID.
No freshTLC/native execution/productionmutants; retained32nativecases(14accept/
18reject),28safety/7liveness/27mutants and132state/131step path keep earlier scopes.
Semantics sha256:c706d14c8df4914973fc9dcaed6286f39a6bc145c13b294204e3f3435a69bbe2. Mandatory44/45 FAIL; phase0 unfrozen;
make unavailable, aggregate formal-check not claimed. Three demosHTTP200 with
no restart thisstage, frozenrefs unchanged. Source-bound report stays NO_GO;
no local acceptance PASS, independent attestation or native guard change.


## 2026-09-26 — Exact seed transcript and finalized ISC edge in Lean

T044/T048/T049/T053/T057/T060; amendment0001. Scope:
formal/proposals/native-seed-transcript-proof.md; evidence:
formal/proposals/evidence/native-seed-transcript.json. NO_GO remains.

NativeSeedTranscript reads exact original seed fields/wire and derives all14
canonical JSON fields and the separate transcript ID. It checks exact expected
context, primitive ID shape and complete ordered nonempty share IDs. Its linked
component computes the actual ISC certificate and exact QC parent relationship.
NativeSeedSection first runs the actual finalized-ISC section, then checks every
original seed against its actual finalized IDs, with strict transcript order.
General helpers derive original list/count and checked parent certificate witnesses.
Whole graph/admission/recovery and finalization provenance are not supplied.

Original native seed JSON and codec-EC wire section remain byte-exact. Three finite
SHA samples bind original ISC QC/body and seed transcript, composing their actual
component edge. Missing/wrong/unfinalized parent and malformed fields/hash reject.
A deliberate countercheck changes the primitive seed and still passes shape: this
explicitly demonstrates missing randomness authentication. No new whole-policy/state
acceptance fixture, native execution or production phase/history claim is made.
Finalization/committee/seed shares/ledger/root/export origin remains unauthenticated.
CONFIG/proposed-ISC replay modes remain unchanged and reject later graphs.

Next norm/EC/APC and full checked graph/recovery composition. Native EC certificate
has no seed field; its finalized metadata supplies that separate edge. Preserve
original payload/ID distinctions and unknown/incomplete fail-closed behavior.
Full nativeArithmeticRecoveryRefines, contractfreeze, offline reproduction,
independent reviews and exact merged GO remain mandatory. Runtime/demo untouched.
Final stable-source validation follows in retained evidence.

Final stable-source checks: full Lean1043jobs, fresh certificate/section/vector
kernels and axiom audit PASS.422tooling/38oracle/5targeted,33legal/112illegallegacy,
Ruff/format/consistency PASS.339generated files(310JSON/27Lean/inputTLA/config)
byte-exact. All95 new named definitions/proofs in three modules audited:
22 general helpers/16 definitions and47 vector proofs/10 definitions; only
propext/Quot.sound/Classical.choice. New modules
have no proof holes or warnings; five pre-existing unused-simp warnings remain.
All21TLA/schema/runtime/147nativewitnesses unchanged;145legacytraces onlysemanticsID.
No freshTLC/native execution/productionmutants; retained32nativecases(14accept/
18reject),28safety/7liveness/27mutants and132state/131step path keep earlier scopes.
Semantics sha256:2c8071714b460df716846964c03db9dd71acf170a4b99fdc8889adcf732fbf57. Mandatory44/45 FAIL; phase0 unfrozen;
make unavailable, aggregate formal-check not claimed. Three demosHTTP200 with
no restart thisstage, frozenrefs unchanged. Source-bound report stays NO_GO;
no local acceptance PASS, independent attestation or native guard change.


## 2026-09-26 — Confirmed native decimal canonicality gap and exact lexical model

T044/T048/T049/T053/T057/T060; amendment0001. Scope:
formal/proposals/native-certificate-decimal-proof.md; evidence:
formal/proposals/evidence/native-certificate-decimal.json. NO_GO remains.

A fresh build of unchanged pinned native certificate components confirms acceptance
of noncanonical -00/-000 norm values and signed -01/-0001 numerators. Native JSON
retains each original spelling and produces distinct content IDs; these findings
must not be normalized away or mistaken for complete runtime safety violations.
31 strings across two actual certificate types give62 cases, including9 accepted
spellings rejected by the separate strict Python proposal profile. Runtime/native
arithmetic guard is unchanged. This is component execution, not a new WAL/trace run.

NativeCertificateDecimal explicitly models the lexical/INT64/nonnegative checks
and retains original bytes. General helpers prove result bounds, digits and exact
source retention; negative-spelled nonnegative output is zero. Separate Canonical
counterexamples refute the inference that every accepted string is canonical.
62 generated kernel cases match retained native outcomes and6 additional proofs
show the discrepancy and byte distinction. General std::from_chars/native language
equivalence is NOT proved. The strict prior tooling profile remains unchanged.

The planned norm/EC proof must use the observed source behavior, not an assumed
canonical parser. Next all13 norm fields and actual finalized ISC parent; then
complete EC/APC and shared admission/replay. Native repair requires formal/contract
compatibility review and exact authority. Full nativeArithmeticRecoveryRefines,
physical recovery, contract freeze, offline reproduction and independent reviews
remain mandatory. Final stable-source validation follows in retained evidence.

Final checks: full Lean1045jobs, fresh lexical/vector kernels and
axiom audit PASS.428tooling/38oracle/6targeted,33legal/112illegallegacy,
Ruff/format/consistency PASS.340generated files(310JSON/28Lean/inputTLA/config)
byte-exact. All90 new named declarations audited:13 general helpers/9 definitions,
68 vector proofs; only propext/Quot.sound/Classical.choice. New modules have no
warnings/holes; five pre-existing unused-simp warnings remain.
Fresh unchanged MSVC certificate components:62 cases(17accept/45reject),9 accepted
noncanonical spellings; native canonicality FAIL is preserved explicitly. No
whole native runtime/WAL/recovery run or production mutant is claimed. All21TLA/
schema/runtime/147nativewitnesses unchanged;145legacytraces onlysemanticsID.
Retained32mixednativecases,28safety/7liveness/27mutants and132state/131step path
keep earlier finite scopes. Semantics sha256:8d3565b23399725912fdfa3f42f195496d1f2a2def82d3c9cf9a90a5e268df26. Mandatory44/45 FAIL; phase0 unfrozen,
make unavailable, aggregate formal-check not claimed. Native stdout archive
line endings were normalized to LF after full regression; all6 targeted tests and
Ruff/format were repeated on that final archiver. Canonical payload bytes unchanged. Three demosHTTP200 without
restart, frozenrefs unchanged. Source-bound report remains NO_GO; no local PASS,
independent attestation, native repair or guard change.


## 2026-09-26 — Original complete norm evidence and finalized ISC edge in Lean

T044/T048/T049/T053/T057/T060; amendment0001. Scope:
formal/proposals/native-norm-evidence-proof.md; evidence:
formal/proposals/evidence/native-norm-evidence.json. NO_GO remains.

NativeNormEvidence derives all13 native JSON fields and complete original wire,
checking original context, ordered full entry list, positive u64 scales and the
source-preserving int64 decimal rule. Original -00 is retained, not normalized;
the native canonicality failure remains open. General proofs derive original
entry provenance, nonnegative parsed values and actual computed ISC QC parent.
NativeNormSection composes the finalized-ISC section with the entire original
norm vector and derives parent certificate witnesses and original list/count.
It does not widen closed CONFIG/proposed-ISC admission/replay modes.

Original native norm JSON and codec-EC section stay byte-exact; three finiteSHA
samples compose the actual original ISC/body/norm identity edge. Separate cases
reject malformed/empty/duplicate/reordered/overflowing values and demonstrate
that -00/0 have equal values but distinct JSON. Alternate norm-root/ticket cases
still pass shape, explicitly retaining absent Q recomputation/membership proof.
No fresh native execution or whole policy acceptance fixture is claimed.

Next exact EC body/certificate membership and separate seed metadata, then APC
and complete shared admission/replay. Root/randomness/exporter/finalization
provenance, general native codec/hash equivalence, full public/native recovery,
nativeArithmeticRecoveryRefines, contractfreeze, offline reproduction and
independent review remain required. Runtime/demo/frozenrefs unchanged.
Final stable-source validation follows in the retained evidence.

Final stable-source checks: full Lean1048jobs; fresh norm/section/vector
kernels and axiom audit PASS.434tooling/38oracle/6targeted,33legal/112illegallegacy,
Ruff/format/consistency PASS.341generated files(310JSON/29Lean/inputTLA/config)
byte-exact. All123new names audited:28generalhelpers/21definitions,
62vectorproofs/12definitions. Onlypropext/Quot.sound/Classical.choice;
no new warnings/holes, five pre-existing unused-simp warnings remain.
All21TLA/schema/runtime/147nativewitnesses unchanged;145legacytraces onlysemanticsID.
No fresh native/TLC/productionmutant execution; retained62decimal/32mixednative
cases,28safety/7liveness/27mutants and132state/131step path keep earlier scopes.
Native decimal canonicality still FAIL; norm value/root/member authenticity and
general native language equivalence remain unproved. Semantics sha256:cea4c97a3496b449bbad0180d88cfc01c87506800447f4f9c4e354b229ea20d9.
Mandatory44/45 FAIL; phase0 unfrozen; make unavailable, aggregate formal-check
not claimed. Three demosHTTP200 without restart, frozenrefs unchanged. Source-bound
report stays NO_GO; no local PASS, independent attestation or runtime repair.


## 2026-09-26 — Complete native EC membership and original parent sections in Lean

T044/T048/T049/T053/T057/T060; amendment0001. Scope:
formal/proposals/native-eligibility-proof.md; evidence:
formal/proposals/evidence/native-eligibility.json. NO_GO remains.

NativeEligibility constructs all16 certificate JSON fields and exact separate
proposed-body/wire bytes, retaining actual integer gamma bits and checking
nonnegative int64, u64 denominator and reduction. Complete ordered ticket/domain
membership is compared to the actual checked ISC; exact count/position follows.
NativeEligibilityLineage resolves original ISC/norm/seed records. Proposed EC
uses configured synthetic signers only for validation; finalized QC retains
its actual signers and independent seed metadata. No signature authority inferred.
NativeEligibilitySection executes actual earlier parent checks, both complete
EC lists, strict computed identity ordering and the finalized-QC subset; derives
original source lists and actual checked parent witnesses.

The native proposed loop checks norm.isc equality, but finalized loop does not
repeat that equality. Both require seed.isc and original checked norm records.
The model preserves this distinction; the guard countercheck alone is not a
complete mixed-parent snapshot or runtime exploit. Gamma/accepted/reason/robust
selection and norms are not derived from Q. Original norm decimal defect remains.
Six synthetic finite SHA samples bind original retained ISC/norm/seed/EC identities;
component proofs are not new native execution or a complete policy/run example.

Next complete APC accepted-ticket/assignment/weight/seed/accumulator lineage,
then remaining graph and shared admission/replay. Complete native/public recovery,
nativeArithmeticRecoveryRefines, authentication, contractfreeze/offline reproduction
and independent review remain open. Runtime/demos/guard/frozenrefs unchanged.
Final stable-source validation follows in retained evidence.

Final stable-source checks: full Lean1052jobs; fresh EC/lineage/section/vector
kernels and axiom audit PASS.441tooling/38oracle/7targeted,33legal/112illegallegacy,
Ruff/format/consistency PASS.342generated files(310JSON/30Lean/inputTLA/config)
byte-exact. All192new names audited:33generalhelpers/38definitions,
96vectorproofs/25definitions. Onlypropext/Quot.sound/Classical.choice;
no new warnings/holes, five pre-existing unused-simp warnings remain. Earlier
resource-heavy combined vector proof was replaced by checked component lemmas;
only final stable-source logs are evidence. All21TLA/schema/runtime/147native
witnesses unchanged;145legacytraces onlysemanticsID. No fresh native/TLC/new
productionmutants; retained62decimal/32mixednativecases,28safety/7liveness/
27mutants and132state/131step path keep previous bounded scopes. Native decimal
canonicality still FAIL; norm/Q/robust derivation and general native language
identity remain unproved. Semantics sha256:e7a7a99bc593e3eb214c7f453a7cc03abdad1864a8af92b56a84ab0701a54878.
Mandatory44/45 FAIL; phase0 unfrozen; make unavailable, aggregate formal-check
not claimed. Three demosHTTP200 without restart, frozenrefs unchanged. Source-bound
report stays NO_GO; no local PASS, independent attestation or runtime repair.

## 2026-09-26 — Complete native APC coverage and original parent section in Lean

T044/T048/T049/T053/T057/T060; amendment0001. Scope:
formal/proposals/native-plan-proof.md; evidence: formal/proposals/evidence/native-plan.json.
NO_GO remains. NativePlan derives all20 APC JSON fields and distinct complete
body/policy wire; checks original context, integer alpha/gcd, both strict ordered
nonempty arrays, iteration bounds and configured signer/quorum. Coverage compares
all accepted EC tickets with sorted assignments and original weights; count/position
and impossible all-rejected nonempty plan follow generally.

NativePlanLineage resolves original ISC/EC/seed and required accumulator; section
executes actual earlier checks, both entire APC lists and finalized subset. The
observed native APC predicate does not repeat EC.isc=plan.isc equality. Its isolated
countercheck does not demonstrate any accepted complete native mixed-parent snapshot.
No fabricated equality is added. Alpha/bucket/transcript/accumulator derivation,
crypto signatures/provenance and full later graph/admission/replay remain open.

Two new finite SHA samples extend prior six checked parent samples. Original
codec-APC/codec-PARAMETER observations stay exact. Component and separate multi-ticket
kernel cases are not new native/TLC/mutant executions or whole policy acceptance.
Closed admission modes, runtime/guard, healthy demos and frozen refs stay unchanged.
Next native PARAMETER original decimal results/leaf/denominator/parents, then full
graph/replay/recovery/nativeArithmeticRecoveryRefines. Contractfreeze, offline
reproduction, independent review and exact merged formal authority still required.
Final stable-source validation follows in retained evidence.

Final stable-source checks: full Lean1056jobs, including fresh vector compilation;
standalone APC/lineage/section kernels and axiom audit PASS.448tooling/38oracle/7targeted,33legal/112illegallegacy,
Ruff/format/consistency PASS.343generated files(310JSON/31Lean/inputTLA/config)
byte-exact. All228new names audited:45generalhelpers/47definitions,
110vectorproofs/26definitions. Onlypropext/Quot.sound/Classical.choice;
no new warnings/holes, five pre-existing unused-simp warnings remain. Earlier
resource-heavy structural/vector reductions were replaced by component lemmas;
only final stable-source logs are evidence. Duplicate standalone vector invocation
was interrupted after full build passed; no second vector completion is claimed. All21TLA/schema/runtime/147native
witnesses unchanged;145legacytraces onlysemanticsID. No fresh native/TLC/new
productionmutants; retained62decimal/32mixednativecases,28safety/7liveness/
27mutants and132state/131step path keep previous bounded scopes. Native decimal
canonicality still FAIL; norm/Q/robust derivation and general native language
identity remain unproved. Semantics sha256:c8a1dff20ffc29f7cf7fa856b6759577ea9f22e5c40be29b2126aca6f637dcca.
Mandatory44/45 FAIL; phase0 unfrozen; make unavailable, aggregate formal-check
not claimed. Three demosHTTP200 without restart, frozenrefs unchanged. Source-bound
report stays NO_GO; no local PASS, independent attestation or runtime repair.

## 2026-09-26 — Complete original native PARAMETER section

T044/T048/T049/T053/T057/T060; amendment0001. Scope:
formal/proposals/native-parameter-proof.md; evidence: native-parameter.json.
NO_GO remains. Complete original JSON/policy/body and signed-decimal strings
are retained; no normalization or replacement with arithmetic outputs.
Actual checked ISC/EC/APC sections compose with both PARAMETER modes. Proposed
assignment map/set, required matrix and domain/parent guards are preserved;
finalized guards retain their original distinct scope. General list induction
proves distinct assignment keys/contexts. Every original matrix/body/QC record
and finalized subset is checked, not only counts.

Separate assignment vote_context_id is in policy but omitted by native body hash;
a general lemma and component checks preserve this source convention. It is not
a collision or complete runtime exploit. Source require_id means nonempty only.
Native verify_shard does not compute result/denominator/Q coverage. Earlier true
arithmetic and whole original admission/replay must still be joined. PARAMETER
body-hash examples are source-derived, not fresh C++ observations. Original
certificate/policy observations are pinned. No native repair/execution or GO.

Next aggregate exact leaf/Merkle matrix, APPLY/current and complete shared
admission/replay; mandatory recovery/public binding, general codec/hash/physical
WAL/unknown scans, contractfreeze/offline reproduction/independent review remain.
Final stable-source checks follow in retained evidence.

Final stable-source checks: full Lean1060jobs; original new vector
compiled in the component build, then full stable-source build and standalone
PARAMETER/lineage/section kernels and axiom audit PASS.
456tooling/38oracle/8targeted,
33legal/112illegallegacy,Ruff/format/consistency PASS.344generated files
(310JSON/32Lean/inputTLA/config) byte-exact. All198new names
audited:41generalhelpers/39definitions,
99vector/componentproofs/19definitions.
Onlypropext/Quot.sound/Classical.choice. Final evidence uses stable source;
an earlier interleaved refresh/build was superseded, not claimed as final evidence.
No new proof holes; five pre-existing unused-simp warnings remain. All21TLA/schema/
runtime/147nativewitness unchanged;145legacytraces onlysemanticsID. No fresh native/
TLC/newmutants; retained62decimal/32mixednativecases,28safety/7liveness/27mutants and
132state/131step path keep prior bounded scopes. Native decimal canonicality FAIL;
arithmetic/provenance/full native language identity remain unproved.
Semantics sha256:cdb7d08c2892364725fc091a8a1cd83f05c352d4e65628c904912bfc24f376da. Mandatory44/45 FAIL; phase0 unfrozen; make unavailable,
aggregateformal-check not claimed. Three demosHTTP200 without restart, frozenrefs
unchanged. Source-bound NO_GO; no localPASS/independentattestation/runtime repair.


## 2026-09-26 — Separate native certificate JSON bounds

T044/T048/T049/T053/T057/T060; amendment0001. Scope:
formal/proposals/native-contract-size-proof.md; evidence native-contract-size.json.
Source review for ROOT found that old Lean certificate helpers omitted the native
4MiB whole-JSON guard; policy wire bounds do not imply expanded JSON bounds.
Unchanged native NormEvidence checks now confirm four cases, including exactly
4194303/4194304/4194305 JSON bytes and ACCEPT/ACCEPT/limit_exceeded. Native already
rejects overlimit; this is a formal-model correction, not a native runtime repair.
The overlimit certificate has65523 entries and a separately encoded1507572-byte
norm wire component, not a demonstrated complete accepted policy.

NativeContractSize derives the inclusive bound and original hash/bytes from
success. NativeSizedParameterSection runs actual prior checks and checks all nine
ISC/norm/seed/EC/APC/PARAMETER certificate groups with computed canonical JSON,
original records, finalized identities, complete list count/order/position.
Earlier raw section remains a lower layer; future ROOT composition uses the
sized entry point. ProposedISC/laterROOT/APPLY/current/full policy and native
error-order/resource-use equivalence remain open. Boundary proofs avoid reducing
multi-megabyte lists. One original norm composes its existing actual source checks
with the size guard; synthetic hash examples retain explicit scope.
No full public/native recovery, authentication, local PASS or GO. Original decimal
canonicality failure remains. Runtime/guard, healthy demos and frozen refs unchanged.
Final stable-source checks follow in evidence.

Final stable-source checks: full Lean1063jobs, two generic standalone
kernels, standalone example kernel and all62new declarations
axiom-audited. 29generalhelpers/14defs;
16kernel/componentproofs/3defs.
Only permitted propext/Quot.sound/Classical.choice. 464tooling/
38oracle/8targeted tests,33legal/112illegallegacy,
Ruff/format/consistency PASS. Full tooling suite passed before a test-only RUF005
list-notation fix; the eight affected-module tests were rerun after that fix.
No generator/Lean/production source changed in the fix.344generated files(310JSON/32Lean/inputTLA/config)
byte-exact. Four fresh unchanged-native component cases, not runtime execution
or new production mutants.21TLA/schema/runtime/147nativewitness unchanged;
145legacytraces onlysemanticID. Retained62decimal/32mixednativecases,
28safety/7liveness/27mutants and132state/131step path keep previous finite scopes.
Native decimal canonicality still FAIL. Mandatory44/45 FAIL, phase0 unfrozen,
make unavailable; aggregateformal-check not claimed. No localPASS or GO.
Semantics sha256:9c22be13bef75212335ec0759673353aae133e39ef705d938bb88410fbaa73c8. Three demosHTTP200 without restart; frozenrefs unchanged.


## 2026-09-26 — Complete native ROOT/Merkle and bounded prior-section composition

T044/T048/T049/T053/T057/T060; amendment0001. Scope
formal/proposals/native-aggregate-proof.md; evidence native-aggregate.json.
NativeAggregateMerkle computes exact canonical leaf hashes and decoded-digest
pair hashes with odd carry;256-byte generic round trips bind the produced
lowercase IDs to the original native nibble/shift/or arithmetic. Empty/over100000
reject; original Python4096 tool bound is not silently used as native admission.
NativeAggregateRoot retains all18 JSON fields, full body/policy bytes, and applies
the4MiB JSON guard to both original and synthetic proposed certificates.
NativeAggregateLineage resolves all three finalized parents and every exact
original finalized PARAMETER leaf, rechecks context/signers/parents/hash/bound,
and derives full required-matrix coverage, record count/order/position.
NativeAggregateSection executes the actual sized previous section and checks
both complete ROOT lists and finalized subset. No supplied body translation,
Merkle equality adapter or arithmetic approval table is accepted.

Five modules; 52generalhelpers/52defs,
120kernel/componentproofs/33defs;
all257names axiom-audited, onlypropext/Quot.sound/Classical.choice.
Examples reuse original ROOT JSON/QC/body, actual PARAMETER/parents and four
retained native Merkle observations(counts1..4), including odd carry. Both modes
compose actual checked component results. No complete native policy/runtime
execution, exporter authentication or new C++ run. Proposed synthetic QC SHA is
explicitly Python-derived. Strict decoder equivalence is for generated lowercase
IDs, not arbitrary malformed values. Earlier development-only interrupted builds
are superseded by the final stable-source run; they are not evidence.

FullLean1068jobs, three generic standalone kernels, axiom audit,
474tooling/38oracle/10targeted,
33legal/112illegallegacy,Ruff/format/consistency PASS.345files(310JSON/33generatedLean/
inputTLA/config) byte-exact.21TLA/schema/runtime/147nativewitness unchanged;
145legacytraces onlysemanticID. No fresh native/TLC/new production mutants;
retained62decimal/32mixednativecases,28safety/7liveness/27mutants and132state/131step
path remain bounded. Original decimal canonicality still FAILS.
Semantics sha256:7b4f69d8753912275cc6e775ed9f5b89d18e4d55f0e5f1100957cea7554fa719. Mandatory44/45 FAIL; nativeArithmeticRecoveryRefines missing;
Phase0 unfrozen; make unavailable, aggregateformal-check not claimed.
APPLY/current, separate proposedISC size calls, full shared admission/replay,
arithmetic/source binding, full native/public recovery, general codecs/JSON/SHA,
physical WAL/unknown scans/repair and provenance remain open. Contract freeze,
offline reproduction and independent review remain required. Source-bound NO_GO;
no localPASS, runtime repair, native guard change or independent attestation.
Three demo servicesHTTP200 without restart; frozen refs unchanged.


## 2026-09-26 — Complete original native APPLY structural certificates and ROOT join

T044/T048/T049/T053/T057/T060; amendment0001. Scope
formal/proposals/native-apply-certificate-proof.md; evidence native-apply-certificate.json.
NativeApplyProfile checks original rational wire bits/reduced nonnegative values,
all domain weights, rounding/nesterov and all10 JSON fields. NativeApplyCertificate
retains original full candidate vectors/signed strings and all18candidate/18QC
fields; all3 canonical hashes have inclusive4MiB bounds. The known negative-zero/
leading-zero defect is preserved. APPLY body identity is the actual candidateID.
NativeApplyLineage computes original candidateID, checks proposed/full-committee
or finalized candidate+QC, exact finalizedROOT/profile/currentparent, both contexts
and certified hashes/structural signers. NativeApplySection executes the actual
bounded ROOT section, checks complete original lists/order/finalizedsubset and
derives ROOT/profile provenance and retained sources/counts from successful results.

Five modules; 42generalhelpers/45defs;
91kernel/componentproofs/24defs.
All202names axiom-audited, onlypropext/Quot.sound/Classical.choice.
Original codec-APPLY/guard-APPLY policy bytes are pinned; profile/candidate components
reproduce exactly. The original observation has NO finalizedApplyQC: the finalmode
example is explicitly synthetic via native as_apply_certificate. Three finiteSHA
preimages/JSON are Python-derived, not new native observations or authentication.
Kernel counterchecks retain missing arithmetic/current joins: changed model999
passes candidate structural validity; changed parentoptimizer leaves link checks
true. These are partial-checker limits, not complete accepted-runtime exploits.

FullLean1073jobs,3generic standalone kernels, axiom audit,
482tooling/38oracle/8targeted,
33legal112illegallegacy,Ruff/format/consistency PASS.346generatedfiles=310JSON/
34Lean/inputTLA/config byte-exact.21TLA/schema/runtime/147nativewitness unchanged;
145legacytraces onlysemanticID. No fresh C++/TLC/productionmutants. Earlier
32mixed/62decimal cases,28safety7liveness27mutants and132state131step remain bounded.
Semantics sha256:7fcdc2a24f052e4a455667d5731073a6461968b803114d8f3055a7037b8bfd49. Mandatory44/45FAIL nativeArithmeticRecoveryRefines missing;
Phase0 unfrozen; make unavailable, aggregateformal-check notclaimed. Native decimal
canonicality stillFAIL. Timeout/view/abort/current, fullsharedadmission/replay,
separate proposedISC size, actualarithmetic/source/nativepublicrecovery, codecs/
JSON/SHA/physicalWAL/provenance, freeze/offline/independentreview remainopen.
No localPASS, nativeguardchange, runtime repair or independentattestation.
Three demosHTTP200 without restart; frozenrefs unchanged.


## 2026-09-26 — Original native timeout/view/abort snapshot tail

T044/T048/T049/T053/T057/T060; amendment0001. Scope
formal/proposals/native-failure-proof.md; evidence native-failure.json.
NativeFailurePayload reads exact original timeout/view/request/abort trees and
retains canonical policy wire bytes. VIEW/ABORT IDs derive original binary
uint64-length/count preimages, distinct from policy uint32 encoding; no invented
certificate-JSON4MiB hash guard. NativeFailureSection checks exact tuple order,
request reasons and computed body-ID order, every abort current field and all
seven original finalized lists. Successful results retain original sources and
all fourteen field relationships. bindSection executes NativeApplySection;
prepare uses actual bounded policy/state decoders. No caller approval/translation.

Three modules; 28generalhelpers/31defs,
69kernel/componentproofs/30defs;
all158names audited, onlypropext/Quot.sound/Classical.choice.
Original codec-VIEW_CHANGE/codec-ABORT policy bytes and body IDs pinned. Two finite
SHA samples and two complete checkTail kernel compositions reuse the original
CONFIG fixture state. These are component proofs, not new native execution.
Every abort field substitution, list order/multiplicity, duplicate/reversed keys,
request vocabulary, uint64 overflow and malformed shapes are checked. Counterchecks
on standalone TailChecks/AbortExact preserve the missing candidate enabling scope:
VIEW next-view freshness is not a snapshot check; a matching finalizedApply list
is not prohibited here. No complete policy admission or native exploit claimed.

FullLean1076jobs,2generic standalonekernels/axiomaudit,
490tooling/38oracle/8targeted,
33legal112illegallegacy,Ruff/format/consistency PASS.347generatedfiles=310JSON/
35Lean/inputTLA/config byte-exact.21TLA/schema/runtime/147nativewitness unchanged;
145legacytraces onlysemanticID. No fresh native/TLC/newproductionmutants;
retained32mixed/62decimal/28safety7liveness27mutants/132state131step keep prior scope.
Semantics sha256:66ab27677e172084d536901c6f1bbacb90557782f94455c6ed2dec4425dfbaad. Mandatory44/45FAIL nativeArithmeticRecoveryRefines missing;
Phase0 unfrozen; make unavailable, aggregateformal-check notclaimed. Native decimal
canonicality stillFAIL. Candidate VIEW/ABORT parents/context/timeout/increment,
request/deadline/phase/readiness, CurrentPointerCommand, complete sharedadmission/
replay, separate proposedISC size, actualarithmetic/source/publicnative recovery,
physicalWAL/codecs/SHA/provenance/freeze/offline/independentreview remainopen.
No localPASS, runtime repair, native guard change or independentattestation.
Three demo servicesHTTP200 without restart; frozen refs unchanged.


## 2026-09-26 — Original native failure candidate and selected-vote guards

T044/T048/T049/T053/T057/T060; amendment0001. Scope
formal/proposals/native-failure-authority-proof.md; evidence native-failure-authority.json.
NativeFailureAuthority computes original VIEW/ABORT contexts and checks all15
parent slots, actual source body/timeout membership, current coordinates,
no-overflow view increment/deadline and empty finalized APPLY for ABORT.
NativeFailureVote decodes original policy/state/VOTE bytes, selects the actual
original candidate, executes the prior section and checks identity/body/current
parent/sequence, live/replay readiness, invalidation, phase and exact request/time
windows. Successful checks retain original vote bytes. SHA and runtime facts
remain explicit boundaries; this is not full shared admission or journal recovery.

Source review corrected an overrestriction in the previous timeout/request
predicate: native require_id only rejects empty strings, whereas policy wire
separately bounds printable ASCII to4096 bytes. WireId replaces certificate Label
at that exact use. Kernel examples retain spaces, punctuation and129-character
IDs; this is a formal projection fix, not a measured native runtime repair.
Existing header/config/certificate Label uses require their own source review.

Three new modules: 29generalhelpers/22defs,
79vectorproofs/12defs;
142new-module names audited. Including the updated
prior payload module, 182definitions/theorems were audited,
onlypropext/Quot.sound/Classical.choice. Original policy and DRC1 vote observations
are pinned; two context SHA samples plus two retained body samples. Both original
candidate and selected-vote component examples pass. No new wholefromBytes fixture,
nativeexecution or authenticatedexporter. Negatives cover all12 forbidden parent
slots, timeout/body/coordinates, uint64wrap, finalizedAPPLY, request/timeendpoints,
foreignrequest/live/replay/readiness/invalidation/sequence/phase and wireIDs.

FullLean1079jobs,3generic standalonekernels/axiomaudit,
498tooling/38oracle/8targeted,
33legal112illegallegacy,Ruff/format/consistency PASS.348generatedfiles=310JSON/
36Lean/inputTLA/config byteexact.21TLA/schema/runtime/147nativewitness unchanged;
145legacytraces onlysemanticID. No fresh native/TLC/newproductionmutants;
retained32mixed/62decimal/28safety7liveness27mutants/132state131step keep prior scope.
Semantics sha256:b4fa03f68a7c767f77098bb0721d8aac90e221822f367a985814ce13fe85c534. Mandatory44/45FAIL nativeArithmeticRecoveryRefines missing;
Phase0unfrozen;make unavailable,aggregateformal-check notclaimed. Native decimal
canonicality stillFAIL. Complete shared policy/all-candidate closure, current
command, sourcearithmetic, journalretry/unknown/recovery, physicalWAL/codecs/SHA/
provenance/freeze/offline/independentreview remainopen. No localPASS, runtime repair,
nativeguardchange or independentattestation. Three demosHTTP200 withoutrestart;
frozenrefs unchanged.


## 2026-09-27 — Shared snapshot base and bounded proposed ISC expansion

T044/T048/T049/T053/T057/T060; amendment0001. Scope
formal/proposals/native-snapshot-base-proof.md; evidence native-snapshot-base.json.
NativeProposedIsc parses actual original bodies, derives complete certificates
with every configured validator and computed2f+1, and checks original context,
ordered tuples, binary body ID and separate inclusive4MiB JSON certificate hash.
List proofs retain every source/count/position. NativeSnapshotBase checks the
original configuration sets, optional accumulator ID, full expected constructor
context, ordered proposed bodies and exact closed-body membership. Its wrapper
executes all existing typed snapshot sections via NativeFailureSection on the
same original policy/state. prepare reuses actual bounded policy/state decoding
and Canonical role/action/order/count/globalcontext checks. No graph/candidate
replacement, whole-body translation or approval Boolean is supplied.

Source review corrects another formal overrestriction: configured validator IDs
need only be nonempty (wire bounds remain separate); actual certificate signers
retain Label. A finalized subset may omit a configured non-Label ID, while
proposed certificates use all validators and reject it. Header round Label is
retained: ChainVerifier constructor unconditionally validates expected context,
even with empty graph. This is a formal predicate correction, not runtime repair.

Three newmodules: 27generalhelpers/7defs,
48vectorproofs/14defs;
96new-module names. Including updated original
NativeIscCertificate, 135names axiom-audited, onlypropext/
Quot.sound/Classical.choice. Original codec-ISC policy/body and separately pinned
ISC certificate are checked. One newly derived four-signer SHA sample plus the
prior three finite cases; not new native observation/authentication. Kernel
examples execute actual proposed-body and checkBase components. No complete
bindSnapshot/prepare fixture or full native execution is newly claimed.
Negatives cover configuration/accumulator/closed-body versusQC, omission,
duplicate/order/context/committee/signers. A mathematical JSON expansion exceeds
4MiB while body wire fits; its duplicated tuples are not an admitted nativepolicy.
General oversized rejection uses the exact computed JSON, not caller size.

FullLean1082jobs,3genericstandalonekernels/axiomaudit,
506tooling/38oracle/8targeted,
33legal112illegallegacy,Ruff/format/consistency PASS.349regeneratedfiles=310JSON/
37Lean/inputTLA/config byteexact.21TLA/schema/runtime/147nativewitness unchanged;
145legacyonlysemanticID. No freshnative/TLC/productionmutants; retained32mixed/
62decimal/28safety7liveness27mutants/132state131step keep their prior boundedscope.
Semantics sha256:ec2dd83efc8122628183dcb92d7b1998eacbd93128b1254107572f9b956110d9. Mandatory44/45FAIL/nativeArithmeticRecoveryRefines missing;
Phase0unfrozen;makeabsent,notaggregateformal-check. Native decimalcanonicality
stillFAIL. All actual candidate authorities/sharedpolicy, CurrentPointerCommand,
sourcearithmetic, journalretry/unknown/recovery, physicalWAL/SHA/exporter,
freeze/offline/independentreview remainopen. No localPASS, GO or nativeguardchange.
Three demosHTTP200 withoutrestart; frozenrefsunchanged.

## 2026-09-27 — All original candidate authorities on the shared snapshot

T044/T048/T049/T053/T057/T060; amendment0001. Scope
formal/proposals/native-candidate-authority-proof.md; evidence native-candidate-authority.json.
NativeCandidateShape checks all15 original parent slots with exact per-action
content-ID/nonempty/empty requirements. NativeCandidateAuthority derives all9
original candidate authorities using actual first proposed-body and finalized
parent lookups, original domain-separated contexts, exact heights/views and
individual parent links. PARAMETER keeps its original assignment context.
APC resolves finalizedEC.norm, PARAMETER/ROOT resolve finalizedplan.seed, and APPLY
retains the computed original candidate identity and body current checkpoint.
VIEW/ABORT use the same original checked failure tail. A general CONFIG checkpoint
is not prematurely forced to current before the later selected-vote guard.

bindPolicy actually executes NativeSnapshotBase.bindSnapshot on the SAME original
policy/state, then checks every original candidate in order. List proofs retain
original records/count/positions/all-members; byte preparation retains canonical
role/reason/action/count/order/globalcontext. No candidate replacement, emptygraph
proxy, supplied wholebody translation or approval Boolean. Source section and
ISC/EC/failure source lemmas retain the actual previously computed rows.

Three modules: 36generalhelpers/23defs,
89vectorproofs/46defs;
194names audited, onlypropext/Quot.sound/Classical.choice.
One original CONFIG full snapshot/candidate wrapper and original byte wrapper
pass the kernel. Other action examples reuse original individually checked rows
inside an EXPLICITLY SYNTHETIC mixed component snapshot; no new whole nonempty
mixed native execution or wrapper fixture claimed. All9 original candidate
records and8 contextSHA samples are pinned. Negatives cover each parent, all
context/height mismatches, body/finalized/config/closed/timeout omissions, norm/
seed/Merkle/apply/current substitutions, abort after APPLY and invalidsecondslot.
Global duplicate contexts/reversed candidate order remain canonicality failures.

FullLean1085jobs,2genericstandalonekernels/axiomaudit,
514tooling/38oracle/8targeted,
33legal112illegallegacy,Ruff/format/consistency PASS.350regeneratedfiles=310JSON/
38Lean/inputTLA/config byteexact.21TLA/schema/runtime/147nativewitness unchanged;
145legacyonlysemanticID. No freshnative/TLC/productionmutants; retained32mixed/
62decimal/28safety7liveness27mutants/132state131step keep earlier boundedscope.
Semantics sha256:2927b3521bd0a2f79ca84e754816ba8f7314d9f36f054b1d551fb3536650df88. Mandatory44/45FAIL/nativeArithmeticRecoveryRefines missing;
Phase0unfrozen;makeabsent,notaggregateformal-check. Native decimalcanonicality
stillFAIL. Selected livevote enabling on sharedsnapshot, currentcommand,
sourcearithmetic, journalretry/unknown/recovery, physicalWAL/SHA/exporter,
freeze/offline/independentreview remainopen. No localPASS, GO or nativeguardchange.
Three demosHTTP200 withoutrestart; frozenrefsunchanged.


## 2026-09-27 — Selected VOTE on the complete original native policy

T044/T048/T049/T053/T057/T060; amendment0001. Scope
formal/proposals/native-selected-vote-proof.md; evidence native-selected-vote.json.
NativeSelectedVote first executes the full shared original policy/snapshot and
all original candidates, then derives first-match selection and checks exact
actor/epoch/round/height/view/context/body/current parent/all-vote sequence,
readiness/invalidation/phase and exact deadline/request predicates. No substitute
policy, whole-body translation or supplied approval. The CURRENT native arithmetic
input guard remains explicit: PARAMETER/APPLY reject in live AND recovery modes.
Recovery bypasses only readiness; it does not bypass any other guard. RuntimeFacts
are still inputs, not authenticated physical observations. Original canonical
policy/state/VOTE bytes and selected record identity are retained by general lemmas.

Read-only source inspection/tests preserve the separate native order: historical
exact journal retry precedes fresh admission and returns original caches; WAL scan
rechecks policy identity/admission with recovered state, then rejects duplicate
records. This stage does not newly compose that complete journal/WAL theorem.
Raw guard APIs consume supplied bounds; only checkAdmission/fromBytes compute whole policy.

Two modules: 33generalhelpers/12defs,
67vectorproofs/18defs;
130names audited, onlypropext/Quot.sound/Classical.choice.
Seven non-arithmetic selected component checks, live/recovery arithmetic refusals,
all54 action/phase combinations, deadline endpoints, exact request/bodyreason,
current/identity/sequence/readiness/invalidation negatives. Original CONFIG whole
policy/state/VOTE byte wrapper passes. Other assembled state/tail examples remain
synthetic components; no new original nonempty mixed-policy wrapper/native run.
Signature-substitution deliberately passes syntactic checks, exposing the remaining
cryptographic authentication premise. Request-only altered-body examples are not
new authenticated body/source fixtures. Original native bytes/sequences unchanged.

FullLean1087jobs,1genericstandalonekernel/axiomaudit,
522tooling/38oracle/8targeted,
33legal112illegallegacy,Ruff/format/consistency PASS.351regeneratedfiles=310JSON/
39Lean/inputTLA/config byteexact.21TLA/schema/runtime/147nativewitness unchanged;
145legacyonlysemanticID. No freshnative/TLC/productionmutants; retained32mixed/
62decimal/28safety7liveness27mutants/132state131step retain previous finite scope.
Semantics sha256:51677e685057e66f8ecb150cf3a09b2a5f9a6b2c3b1a386750b52ceb1c48d640. Mandatory44/45FAIL/nativeArithmeticRecoveryRefines missing;
Phase0unfrozen;makeabsent,notaggregateformal-check. Native decimalcanonicality
stillFAIL. Current command/sourcearithmetic/full journal retry/unknown/recovery,
physicalWAL/SHA/exporter, full publicrefinement/arbitrarysnapshots/availability,
freeze/offline/independentreview remainopen. No localPASS, GO or nativeguardchange.
Three demosHTTP200 withoutrestart; frozenrefsunchanged.


## 2026-09-27 — Complete original-policy admission joined with computed WAL history

T044/T048/T049/T053/T057/T060; amendment0001. Scope
formal/proposals/native-whole-replay-proof.md; evidence native-whole-replay.json.
NativeReplayAdmission now has a closed whole mode: original policy/state decoding,
complete source snapshot and ALL original candidates, original initial tick,
then NativeSelectedVote on the actual fold state. Older config/proposals domains
remain restricted. NativeWholeReplay proves an executable prefix/suffix for every
stored vote, global position including commands, original policy ID and exact
vote/receipt/parent cache. Tick/invalidation/expected sequence come from that
actual history. Historical retry keeps original bytes without fresh deadline or
current checks; duplicate scans reject. CURRENT PARAMETER/APPLY guard remains;
no vacuous arithmetic recovery theorem is added.

The ORIGINAL nonempty two-candidate CONFIG/ISC policy now composes all snapshot
sections, proposed ISC and separately bounded committee expansion, both candidate
contexts, original ISC1/freeze2 transition and vote/command cache retries. These
are the exact two-record prefix of the four-record no-snapshot capture, also
retained in the earlier native WAL evidence; not a new whole four-record run.
Eleven finite actual SHA samples, no synthetic assembled snapshot proxy. The
result is identical to the earlier original mixed replay through the now complete
policy gate. No native bytes or original positions/5/6/8 were rewritten.

Two general modules (including modified mode module) audit 29
helpers/8defs; handwritten vectors 59
proofs/19defs. All115 named declarations
audited, onlypropext/Quot.sound/Classical.choice. Negatives cover missing/reordered/
repeated positions, altered policy ID, independent duplicate key, invalidated
fresh vote; original retry survives arbitrary core changes. Generic byte-scan
composition rejects incomplete observations. The new fixture uses original typed
WAL entries whose byte decoders remain separate; no unified outer-WAL/admission
hash fixture is newly claimed. Torn-tail rejection is explicitly narrower than
native truncation, not full repair/failure equivalence. Physical completeness,
SHA/signature/export authentication and arbitrary snapshots remain open.

FullLean1089jobs,2fresh generic kernels/axiom audit,
530tooling/38oracle/8targeted,
33legal112illegallegacy,Ruff/format/consistency PASS.351regeneratedfiles=310JSON/
39Lean/inputTLA/config byteexact.21TLA/schema/runtime/147nativewitness unchanged;
145legacyonlysemanticID. No freshnative/TLC/productionmutants; retained32mixed/
62decimal/28safety7liveness27mutants/132state131step retain previous finite scope.
Semantics sha256:2a08f65ef39412fef59f57640476c59527e8cfdbe7a4b97169013812bc9cdb82. Mandatory44/45FAIL/nativeArithmeticRecoveryRefines missing;
Phase0unfrozen;makeabsent,notaggregateformal-check. Native decimalcanonicality
stillFAIL. CurrentPointerCommand/sourcearithmetic, complete public/native
phase/QC/current/unknown/repair, physicalWAL/SHA/exporter, freeze/offline and
independent reviews remain required. No localPASS, GO or nativeguard change.
Three demosHTTP200 withoutrestart; frozenrefsunchanged.


## 2026-09-27 — Original current-pointer command and separate text WAL recovery

T044/T048/T049/T053/T057/T060; amendment0001. Scope
formal/proposals/native-current-pointer-proof.md; evidence native-current-pointer.json.
NativeCurrentPointer checks all14 original canonical command fields, bounded
command/QC JSON IDs and all5 exact context/parent/model/optimizer relationships.
It models exact replay before parent/height CAS and strictly increasing fresh
height. The optional finalized-source bridge computes the original complete APPLY
section and selected finalized certificate/candidate/ROOT/profile links, not a
caller approval Boolean. This stronger bridge is not claimed inside the actual
low-level pointer store and has no new full-policy combined fixture.

NativePointerWal uses actual separate text lines, checksum over original payload,
canonical uint64 height, parent extension and exact stored IDs; it is not DRW1.
Computed history retains all complete records and the actual unterminated suffix.
Unknown remains distinct from known empty bytes. Native truncation is represented
as retained discarded bytes, not physically executed/authenticated repair. The
actual before/after-append-before-durability labels both throw before append;
during-append writes literal truncated. Complete durable/unacknowledged and
committed/unreturned outcomes remain distinct. Exact replay writes nothing.

Explicit scope counterchecks: a single unconfigured signer passes native QC
shape checks; rehashed fabricated stored IDs pass pointer recovery, which never
reloads an ApplyQC body. These expose caller/physical provenance requirements,
not a new full-runtime exploit or proof of certificate authentication. Four
finite actual SHA samples bind original008 golden command/QC and SYNTHETIC
source-derived WAL lines. No new native capture/run, vote sequence rewrite,
general SHA/JSON/stdlib/physical durability proof or public current relation.

Two generic modules: 30helpers/31defs;
45vector proofs/17defs;
all123names axiom-audited, onlypropext/Quot.sound/Classical.choice.
FullLean1092jobs,2fresh generic kernels/audit,
538tooling/38oracle/8targeted,
33legal112illegallegacy,Ruff/format/consistency PASS.353regeneratedfiles=311JSON/
40Lean/inputTLA/config byteexact.21TLA/schema/runtime/147nativewitness unchanged;
145legacyonlysemanticID. No freshnative/TLC/productionmutants; retained32mixed/
62decimal/28safety7liveness27mutants/132state131step keep earlier finite scope.
Semantics sha256:ff5918705a66c52ec737da856084c52ba1acae661dda4f34d7345b615b01349d. Mandatory44/45FAIL/nativeArithmeticRecoveryRefines missing;
Phase0unfrozen;makeabsent,notaggregateformal-check. Native decimalcanonicality
stillFAIL. Full source arithmetic/result/current binding, public/native phase/QC/
unknown/repair, physicalWAL/SHA/exporter, freeze/offline/independent reviews remain
required. No localPASS, GO or nativeguard change. Three demosHTTP200 withoutrestart;
frozenrefsunchanged. Earlier expensive ASCII-string draft reductions were stopped;
final byte-literal/component proofs and final stable checks alone count.


## 2026-09-27 — Computed APPLY values, exact hashes and partial original-source pointer relation

T044/T048/T049/T053/T057/T060; amendment0001. Scope
formal/proposals/native-apply-result-proof.md; evidence native-apply-result.json.
NativeApplyResult uses actual deriveNativeApply and independently hashes every
next/parent model and optimizer coordinate with the original engine's exact
value preimages. Original decimal spellings, vector order and both parent IDs
must match; full signed output bounds follow from the existing computation.
Shared profile coefficients/domain weights, round/height/view/epoch and every
ordered ROOT leaf's domain/shard/denominator/numerators are checked. The join
computes the original complete APPLY snapshot/selected candidate or finalized QC,
retains original canonical IDs and composes a fresh pointer command with the
modeled recovered record and exact replay. No physical WAL or public current
refinement is inferred; historical retries are not re-admitted by this fresh API.

The native configuration/schema/arithmetic-profile/accumulator/ISC/EC/APC/Q-artifact
identity bridge to the draft graph remains OPEN. Different native contract and
draft artifact IDs are not equated. Component counterchecks show missing metadata,
accumulator identity and Q leaves can pass the respective numeric-only checks;
these are not accepted whole-runtime counterexamples. Original label-root graphs
are unchanged: parent1 is not the model value hash, so no successful full original
source/arithmetic/pointer example is newly claimed. Three real SHA samples and
a synthetic candidate reuse the existing pinned kernel graph result.

NEW confirmed contract-fixture scope gap: original008 golden next_model_hash and
next_optimizer_hash are SHA of next-model/next-optimizer LABELS, not their shown
101/-49 and11/-4 vector preimages. Both stored/computed IDs, actual engine preimages
and pinned generator source are retained in machine evidence. This is not a new
native execution failure. Original bytes are not rewritten. Native -00/-01
canonicality remains FAIL; the computed exact-spelling relation rejects those
aliases rather than normalizing accepted native strings.

Two generic modules: 29helpers/23defs;
44vector proofs/13defs;
all109names axiom-audited, onlypropext/Quot.sound/Classical.choice.
FullLean1095jobs,2fresh generic kernels/audit,
545tooling/38oracle/7targeted,
33legal112illegallegacy,Ruff/format/consistency PASS.355regeneratedfiles=312JSON/
41Lean/inputTLA/config byteexact.21TLA/schema/runtime/147nativewitness unchanged;
145legacyonlysemanticID. No freshnative/TLC/productionmutants; retained32mixed/
62decimal/28safety7liveness27mutants/132state131step retain earlier finite scope.
Semantics sha256:2d95a8132c9c0475c70a49f14f6c691dbefe292cb28a839317d18923db29a165. Mandatory44/45FAIL/nativeArithmeticRecoveryRefines missing;
Phase0unfrozen;makeabsent,notaggregateformal-check. Full source-identity binding,
public/native phase/QC/current/unknown/repair, physicalWAL/SHA/exporter,
freeze/offline/independent reviews remain required. No localPASS, GO or guard
change. Three demosHTTP200 withoutrestart; frozenrefsunchanged.


## 27 September 2026 — original Q-source preimages and explicit missing certificate inputs

T044/T048/T053/T054/T056/T057. Formal-only tooling; NO_GO remains.
Scope formal/proposals/native-source-artifacts.md; evidence
formal/proposals/evidence/native-source-artifacts.json. The versioned original
Q-source relation resolves exact manifest/config/profile/schema/scale/plan/proof
bytes and complete DRQ1 leaves. It derives tensor inclusion/ranges and shard
partition from original metadata, checks every expected header, ordered coverage,
source-domain hashes, payload hashes, Merkle root, byte totals and signed INT16
Q values. No expected whole header/body, value equality or approval Boolean is
supplied. Duplicate/noncanonical JSON, mismatched links, substitutions, omitted/
extra/reordered leaves, bad prefix/length/endian range and incomplete sources fail.

Seventeen source/fixture files are pinned byte-exact to native60c692f. Original004
contains12 resolvable objects, including5 DRQ1 shards and all36 Q coordinates.
Original008 still lacks16 selected source preimages in that retained store:
schema/arithmetic-profile/config/accumulator plus12 input leaves. The12 leaves
are hashes of generator labels, not supplied DRQ1 bytes. Their exact original
IDs/labels are retained. Original004 baseconfig/parent preimages are absent too.
This is a fixture scope gap, not a new native execution failure or a claim of
global nonexistence. Neither fixture nor source identity is rewritten.

Proof bytes/input links/selected width are retained; mathematical declared
bounds/headroom/theorem authority are NOT validated here. Schema-to-draft
coordinate/shard names and original certificate-to-draft graph identity remain
OPEN. Rehashed changed Q can form a different content-valid manifest, explicitly
not the same independent authority. The named future provenance boundary needs
original snapshot/config/source/build/run/position and complete original
preimages; digest equality is not exporter authentication. All output labels
retain fixture-only scope. No native execution, public transition, WAL or
recovery proof is inferred from this Python source decoder.

Final562 tooling/38oracle/17newtargeted tests, Ruff/format, consistency and
33legal112illegal legacy refinement PASS. New JSON generator byte-exact; all355
prior generated files unchanged (not rerun). All Lean/TLA/public-schema/runtime
and legacy/native traces unchanged. Semantics unchanged
sha256:2d95a8132c9c0475c70a49f14f6c691dbefe292cb28a839317d18923db29a165.
Mandatory audit rechecked44/45; no fresh Lean build/proof claimed, retained1095-job
build remains prior evidence. No fresh TLC/native/productionmutants. Phase0
unfrozen; make unavailable, not aggregate formal-check. Three demosHTTP200
withoutrestart and allfrozenrefs verified. Full original source/graph/admission,
public/native phase/QC/current/unknown/repair, physicalWAL/exporter/SHA, freeze,
offline and independentreview remain open. No localPASS, GO or guardchange.


## 27 September 2026 — original accumulator proof/config and Q-source composition

T044/T048/T053/T054/T056/T057. Formal-only tooling; NO_GO remains.
Scope formal/proposals/native-accumulator-source.md; evidence
formal/proposals/evidence/native-accumulator-source.json. The new original004
relation resolves proof/config/profile bytes, checks all18 proof/12config fields
and exact shared source links, then recomputes coefficient/count/Q product,
canonical prefix and separate product/accumulator widths. Every declared bound
must match; PASS/theorem names cannot approve incorrect arithmetic. Exact
positive common denominator is retained without choosing/reducing another one.
The composed entry resolves the entire original Q graph and retains all12objects,
5DRQ1 leaves and36coordinates. No supplied decoded QSource or expected values.

Original canonical proof has NO headroom field. Final-minus-prefix derives the
unique admissible request headroom, including nonzero values; it does not prove
what an actual native call supplied. A separate primitive comparison rejects
mismatched observed headroom but does not authenticate that observation. Original
native test explicitly supplies0 and agrees. Historical formal/Lean IDs and exact
theorem groups are metadata checks, not a new authority or Lean proof.

Original008 APPLY profile's complete10field codec and actual accumulator edge
are checked. The source still lacks the referenced sha256:222... proof preimage;
substituting004bytes fails. A changed/rehashed profile example is synthetic only.
Worker ties-even and APPLY half-positive remain separate stages. APPLY quantum
is absent from original008profile; certified weights/common denominator/count,
conversion/mixture/optimizer bounds and original-to-draft identity remain open.
Native008 labels use128chars/colon, distinct from004segment255/slash; checked.

Nineteen new targeted tests cover rehashed arithmetic/metadata/source changes,
allfield omissions, exact INT64/INT128 limits, nonzero/negative headroom, separate
widths, count/coefficient/Q ranges, denominator retention and full rehashed Q
graphs with invalid proofs. Eleven native source files pinned; four reuse prior
exact copies. Final581tooling/38oracle/19targeted tests,Ruff/format/consistency,
33legal112illegal legacy PASS. NewJSON regeneration byteexact;356priorgenerated
files unchanged, oldgenerators notrerun. AllLean/TLA/schema/runtime/legacy/native
traces unchanged. Semantics unchanged
sha256:2d95a8132c9c0475c70a49f14f6c691dbefe292cb28a839317d18923db29a165.
Mandatory audit44/45; retained1095-job build, no newLean proof/build, TLC/native
execution or productionmutants. Phase0unfrozen;makeabsent,notaggregateformal-check.
Native decimal -00/-01 stillFAIL. DemosHTTP200 withoutrestart/frozenrefsverified.
Full source/graph admission, nativeArithmeticRecoveryRefines/public phase/QC/
current/unknown/repair, physicalWAL/SHA/exporter, arbitrarysnapshots, freeze,
offline and independentreview remain required. No localPASS, GO or guardchange.


## 27 September 2026 — original APC membership and actual coefficient bound relation

T044/T048/T053/T054/T056/T057. Formal-only tooling; NO_GO remains.
Scope formal/proposals/native-plan-weights.md; evidence
formal/proposals/evidence/native-plan-weights.json. resolve_members loads original
APC/EC/ISC/seed/norm bytes and checks all contexts, exact full ticket/domain lists
including rejected entries, and full accepted APC weights/buckets. Duplicate ISC
tickets cannot collapse through an associative lookup. Original commitments, AC
identities, final alpha, gamma and every source byte are retained. EC seed is a
separately keyed primitive because absent from the EC wire; provenance remains
independent. Stronger cross-parent/norm membership and resource restrictions
are not native predicate/error-order equivalence or authenticated admission.

resolve_plan_weights resolves the APC's exact original proof/config/profile and
recomputes its bounds. It derives c_j=a_j*(L/b_j) using that SPECIFIC denominator,
requires divisibility and c_j<=A, and global accepted count<=N including zero
coefficients. Global count is a sufficient projection restriction. It checks
source config schema/base-config identities and derives complete ordered
per-domain rows and worst absolute Q-prefix bounds. No LCM substitution, rounding,
expected whole body or approval Boolean; EC gamma is NOT multiplied into final
APC alpha again. Q values/manifest/availability/source-draft identity remain open.
No later PARAMETER/aggregate/APPLY dependency is introduced.

Original pinned native policy/certificate membership passes, but its required
sha256:ffff... proof preimage is absent; full numeric join rejects without
rewriting that original capture. Independent004 bytes under that ID reject.
A separate versioned synthetic test graph has four tickets/three eligible/two
domains, alpha0,1/3,1/2, gamma1/7 and denominator12 (not minimalLCM6), deriving
coefficients0,4,6. Eight exact objects retained. A deliberate unconfigured-signer
countercheck passes this numeric helper: signer/finality/policy provenance is
not authenticated. Existing typed Lean section relations are not newly composed
with this Python relation into a kernel theorem.

Twenty-two new tests include exact rational scaling against Fraction, zero
weights/counts, coefficient limits, rehashed invalid proof, full-field omissions,
source/canonical/resource failures, mixed contexts/parents and full membership.
Final603tooling/38oracle/22targeted,Ruff/format/consistency,33legal112illegal PASS.
NewJSON byteexact;357priorgenerated files unchanged, oldgenerators notrerun.
Four native source pins plus a fifth separately retained verifier at60c692f;
current candidate verifier differs and was NOT substituted for those bytes.
AllLean/TLA/schema/runtime/legacy/native traces unchanged; semantics unchanged
sha256:2d95a8132c9c0475c70a49f14f6c691dbefe292cb28a839317d18923db29a165.
Mandatory44/45; prior1095-job build retained, no newLean build/proof/native/TLC/
productionmutants. Phase0unfrozen;makeabsent,notaggregateformal-check. Native
decimal-00/-01 stillFAIL. DemosHTTP200 withoutrestart/frozenrefsverified.
Full Q/commitment/schema/draft identity and nativeArithmeticRecoveryRefines,
public phase/QC/current/unknown/repair, physicalWAL/SHA/exporter, arbitrary
snapshots, freeze/offline/independentreview remain open. No localPASS/GO/guardchange.


## 27 September 2026 — original Q coverage, native availability and eligible APC inputs

T044/T048/T053/T054/T056/T057. Formal-only relation plus unchanged native component
verification; NO_GO remains. Scope formal/proposals/native-available-q.md; evidence
formal/proposals/evidence/native-available-q.json. New candidate observation
version explicitly allows only UNAUTHENTICATED_COMPONENT_INPUT, not a native
export/snapshot/authority format. Exact native primitives and selected manifest
ID are preserved; no approval Boolean or invented commitment hash convention.

The relation resolves all original004 manifest/schema/scale/plan/config/profile/
proof/DRQ1 preimages, checks actual ticket, and derives the full lexicographic
leaf set while preserving original schema/range order. Missing/extra/reordered/
duplicate lists reject even if native caller-required and covered lists agree.
Composed APC API retains every eligible row and checks original ticket/domain/
commitment/AC/schema/proof/config identities, full order/count and source byte
limits. Rejected ISC members remain in complete certificate preimages but their
Q payloads are outside this accepted arithmetic corpus. No later aggregate is
required. This is not the complete native frozen history or authenticated source.

The original InputLedger has no manifest-ID/commitment preimage or AC signature
decoder. It accepts arbitrary well-shaped opaque commitment/AC IDs if its input
primitives agree. The composed API rejects substitutions against unchanged ISC
rows, but a wholly new rehashed history is still unauthenticated. No equality of
commitmentID/manifestID/Merkle-root is invented. The example retains original004
12objects/5DRQ1leaves/36coordinates and constructs a separate synthetic APC and
component inputs; original008 history and original5/6/8 are unchanged. A second
two-ticket test constructs distinct new source bytes to check order/duplication.

Ten source files pinned at60c692f. Seventeen fresh cases execute four WHOLE
unmodified C++ translation units (consensus/canonical/SHA/contracts), not patched
functions or runtime/WAL. Exact frozen triples and accept/reject match. Native
accepts mutually consistent nonempty incomplete caller-leaf lists; source Q
relation rejects. Native empty sets reject. Initial draft empty-set assumption
and shared-list negative fixture were corrected before final stable checks; only
final corrected source/results count. No production-mutant claim.

Final622tooling/38oracle/19targeted,Ruff/format/consistency,33legal112illegal PASS.
NewJSONbyteexact;358priorgenerated files unchanged; oldgenerators notrerun. All
Lean/TLA/publicschema/runtime/native/legacy fixtures unchanged; semantics stays
sha256:2d95a8132c9c0475c70a49f14f6c691dbefe292cb28a839317d18923db29a165.
Mandatory44/45; prior1095-job build retained, no newLean proof/build orTLC.
Native-00/-01 canonicalityFAIL;Phase0unfrozen;makeabsent,notaggregateformal-check.
DemosHTTP200 withoutrestart/frozenrefsverified. Commitment/manifest/AC/config/
current provenance, original-to-draft projection, full nativeArithmeticRecoveryRefines,
public phase/QC/current/unknown/repair, physicalWAL/codecs/SHA/exporter, arbitrary
snapshots, freeze/offline/independentreview remain required. No localPASS/GO/guardchange.


## 27 September 2026 — original vector inputs and draft arithmetic correspondence

T044/T048/T053/T054/T056/T057. Formal tooling only; NO_GO remains. Scope
formal/proposals/native-vector-projection.md; evidence
formal/proposals/evidence/native-vector-projection.json. New versioned projection
loads complete original APC/Q preimages itself, checks shared schema/profile/
proof/config/scale/plan/parent and derives every included coordinate and original
shard interval. Explicit name:ten-digit-flat-offset and shard-ordinal profile
preserves original values/ranges; names over117chars or non-order-preserving
prefix names reject as projection limits, not native admission changes. Complete
original dtype/dimensions/frozen/alias metadata remains in source bytes; the draft
SCHEMA alone is not injective over that metadata or a frozen-model proof.

Every full vector Q_SHARD and complete domain-by-shard assignment is derived
from original values/quanta/final APC weights and specific proof denominator.
Every product/prefix rechecked at original separate widths; existing draft
parameter oracle independently recomputes results. No scalar127 generalization,
minimal-LCM substitution, extra EC-gamma multiplication or zero-weight deletion.
Source-bound fields are compared against an independently supplied actual draft
Witness graph, original round/height/view/epoch/parent checkpoint and proof width.
Rehashed internally valid target schema/Q/weight/quantum/denominator substitutions
reject. Per-assignment vote contexts, current vectors, complete APPLY profile,
deadline/parent-QC projection and source authentication remain explicitly OPEN.
Positive counterchecks change learning rate/current model/context and still pass
this input-only layer; NativeAnchor validity is not established by construction.

First example retains original004 12objects/5DRQ1leaves/36coordinates with lengths
4,8,8,8,8; APC/draft authority are synthetic. Second NEW source graph has3tickets,
2domains,36coordinates per ticket, finalalpha1/3,1/2,0 and ECgamma1/7; denominator12
produces coefficients4,6,0, first-domain -2Q from Q/-Q and second-domain zeros.
All coordinates crosschecked with Fraction; original008/sequences5/6/8 unchanged.
24new tests cover source/target preimages, whole rehashed graph substitutions,
all ranges, naming/resources, contexts/shared parent and the remaining boundaries.

Final646tooling/38oracle/24targeted,Ruff/format/consistency,33legal112illegal PASS.
NewJSON byteexact;359priorgeneratedfiles unchanged, oldgenerators notrerun.
AllLean/TLA/schema/runtime/native/legacy fixtures unchanged; semantics remains
sha256:2d95a8132c9c0475c70a49f14f6c691dbefe292cb28a839317d18923db29a165.
Mandatory44/45; prior1095-job build retained, no newLean/native/TLC/mutant claim.
Native-00/-01 canonicalityFAIL;Phase0unfrozen;makeabsent,notaggregateformal-check.
DemosHTTP200 withoutrestart/frozenrefsverified. Original/draft current/profile/
authority provenance, kernel composition and full nativeArithmeticRecoveryRefines,
phase/send/QC/current/unknown/repair, generalcodec/SHA/WAL/exporter/arbitrarysnapshots,
freeze/offline/independentreview remain mandatory. No localPASS/GO/guardchange.


## 27 September 2026 — original DRQ1 framing and vector byte decoding in Lean

T044/T048/T053/T054/T056/T057. Formal proposal only; NO_GO. Scope
formal/proposals/native-q-bytes-proof.md; evidence
formal/proposals/evidence/native-q-bytes.json. NativeQBytes computes original
DRQ1 version/length framing and ordered little-endian signed INT16 vectors from
bytes without a supplied decoded list or approval flag. General proofs retain
byte pairs/positions, range[-32767,32767], exact length2*n, order/zeros/duplicates,
uniqueness, append composition and bounded frame roundtrip/exact whole preimage.
Odd/truncated/trailing/invalidversion/forbidden-32768 inputs reject. Framing
bounds are header1..65536 and payload1..1048576; this is not complete native
read_shard validation or a machine-memory execution proof.

Five original004 blocks retain exact original header/payload/envelope bytes and
all36 coordinates (4,8,8,8,8). Original source boundary remains independently
pinned, not native producer authentication. Twenty small kernel cases and
compositional original-byte proofs avoid whole-state/dependent reductions.
Header JSON and SHA remain OPEN: non-JSON header bytes and changed Q with the
unchanged original header both pass this framing layer. The separate Python
source checker rejects the latter with PAYLOAD_HASH. This countercheck prevents
misrepresenting byte parsing as source admission. Schema/ranges/quanta/weights,
source-to-draft LoadedRow/RowsBound/DerivedParameter and full recovery remain open.

27general helpers/12definitions plus Frame/PayloadRelation;45component/kernel
proof declarations/15fixture definitions. All101new named declarations audited,
only allowed standard kernel axioms. Fresh fullLean1097jobs and both standalone
kernels PASS. Final651tooling/38oracle/5targeted,Ruff/format/consistency and
33legal112illegal PASS;362generatedfiles byte-exact. All21TLA modules/public
schema/runtime/147native witnesses unchanged;145legacy traces only semanticsID.
No new native/TLC/productionmutants; earlier bounded scopes retained.
Mandatory44/45/nativeArithmeticRecoveryRefines still missing, Native decimal
-00/-01 canonicalityFAIL, Phase0unfrozen, makeabsent/notaggregateformal-check.
DemosHTTP200 withoutrestart, frozenrefs unchanged. No localPASS/GO/guardchange
or independent attestation. New source-bound semantics: sha256:e54304e6bd3febec04d3eb5f22b8825303025dc2a10e6fae0234eeb7f438d842.


## 27 September 2026 — original canonical DRQ1 header bytes in Lean

T044/T048/T053/T054/T056/T057. Formal proposal only; NO_GO. Scope
formal/proposals/native-q-header-proof.md; evidence
formal/proposals/evidence/native-q-header.json. NativeQJson/NativeQHeader consume
actual original header bytes with exact sixteen keys, unsigned canonical decimal
and unescaped ASCII text. All values are derived, not supplied as a decoded
header/approval. General lemmas retain ordered fields and exact complete preimage,
parse/encode roundtrip and uniqueness, numeric ranges and uint64 segment offset.
The composed join compares header element_count with actual decoded Q length,
retaining payload relation/two-byte positions and global coordinate bounds.
Historical semantics/profile IDs and content-ID spelling are not current authority.

All five original004 headers/frames and36coordinates remain exact. Shared primitive
byte proofs plus general parser/frame lemmas prove all five joined results;
28small cases include malformed numeric/text/key/constants and the SHA boundary.
Non-JSON framing countercheck now rejects in the composed header API. Changed Q
with the original SHA header still passes this Lean layer and fails the existing
Python PAYLOAD_HASH check. SHA/source graph/expected-header authentication and
original schema/plan/quanta/weights to LoadedRow/RowsBound/DerivedParameter remain
OPEN. No native execution/equivalence, machine-memory or general JSON proof.
Exact native Header declaration is independently source-pinned; original payloads
and receipts are not rewritten. uint64 offset+count/actual plan intervals remain
separate checks, not implied by the header's global element_start+count bound.

26general helpers/25definitions plus five type declarations;108component/kernel
proofs/38fixturedefs,202new named declarations axiom-audited, standard kernel
axioms only. FullLean1100jobs, three fresh standalone kernels PASS. Final657tooling/
38oracle/6targeted,Ruff/format/consistency,33legal112illegal PASS;364generatedfiles
byte-exact. Earlier expensive rcases/whole-header draft was discarded; final pool
of primitive byte proofs avoids repeating large reductions. Only stable final
sources/logs count.21TLA/schema/runtime/147native witnesses unchanged;145legacy
traces only semanticsID. No fresh native/TLC/productionmutants; old bounded scopes
retained. Mandatory44/45/nativeArithmeticRecoveryRefines missing; native certificate
-00/-01canonicalityFAIL unaffected, Phase0unfrozen, makeabsent/notaggregateformal-check.
DemosHTTP200/no restart, frozenrefs unchanged. No localPASS/GO/guardchange or
independent attestation. Source-bound semantics: sha256:8ac0cf149236e348f94afd4e35aeecdee98245fac419e0ccfe287a281b3a91a3.


## 27 September 2026 — original scale bytes and parsed Q quantum in Lean

T044/T048/T053/T054/T056/T057. Formal proposal only; NO_GO. Scope
formal/proposals/native-scale-binding-proof.md; evidence
formal/proposals/evidence/native-scale-binding.json. NativeScaleBytes parses the
actual original004 nested scale-table JSON with exact keys/types/order, bounded
segment array and complete canonical preimage. General roundtrip/uniqueness and
ordered-list lemmas retain numerator-as-string and denominator-as-number.
NativeScaleBinding derives positive reduced uint32 quantum, actual segment
name/start/count/ordinal and contiguous total from decoded bytes. Its composed
bind runs the actual DRQ1 header/vector decoder, selects the exact source segment
and checks shared source IDs, offset+count and global coordinate placement.
General lemmas retain every original coordinate, parsed quantum and payload.
Internal scale layout does not establish referenced schema/shape/omission/plan.

Hash adapter remains UNVERIFIED. Its exact domain-separated canonical preimage
is retained, but the fixture recognizes one pinned preimage and is not SHA256,
source authentication or a native exporter. All five original blocks and all36
coordinates compose with the exact643-byte scale table/two original segments.
Thirty-two small cases expose their scope: byte grammar, typed quantum/layout/
range guards and a changed-payload countercheck. Changed first Q with the old SHA
header STILL PASSES the Lean scale join and fails Python PAYLOAD_HASH. No payload
hash/native admission proof is claimed. Source-to-draft LoadedRow/RowsBound/
DerivedParameter, complete source graph and arithmetic recovery remain OPEN.

30general theorems/23definitions plus seven type declarations;74component/kernel
theorems/33fixturedefs,167new named declarations audited including Bound.quantum,
standard kernel axioms only. FullLean1103jobs and three fresh standalone kernels
PASS. Final663tooling/38oracle/6targeted,Ruff/format/consistency,33legal112illegal
PASS;366generatedfiles byte-exact. Original fixtures were reused; no giant new
combined native/state reduction. Only final stable sources/logs count.
21TLA/schema/runtime/147native witnesses unchanged;145legacy only semanticsID.
No new native/TLC/mutants; retained bounded scopes unchanged. Mandatory44/45,
nativeArithmeticRecoveryRefines missing; separate native certificate -00/-01
canonicalityFAIL unchanged, Phase0unfrozen, makeabsent/notaggregateformal-check.
DemosHTTP200/no restart; frozenrefs unchanged. No localPASS/GO/guardchange or
independent attestation. Source-bound semantics: sha256:d019f4d958204f080e90ba84af62d3623e4ba115db1c17a633d90b59214065e1.


## 27 September 2026 — original schema shapes, omission and exact scale coverage in Lean

T044/T048/T053/T054/T056/T057. Formal proposal only; NO_GO. Scope
formal/proposals/native-schema-binding-proof.md; evidence
formal/proposals/evidence/native-schema-binding.json. NativeJsonSequence and
NativeSchemaBytes parse the actual complete original schema bytes: every parameter,
shape, dtype, trainable flag and alias/owner. General bounded-list roundtrip,
canonical preimage and uniqueness proofs retain order/multiplicity until checking;
no decoded schema or whole translated body is supplied. NativeSchemaBinding derives
positive bounded shape products (scalar empty shape=1), exact inclusion by omission
policy, unique ordered names and valid ordered alias ownership. Original256-character
schema names versus included255-character native tokens are explicitly checked.
All frozen parameters and aliases remain in the original source bytes.

Complete ordered segment names/counts/ordinals/prefix starts and total are derived
from the included parameters and compared with the actually decoded scale table.
General indexed placement and original dimension lemmas retain exact source data.
bindQ composes schema/scale/header/vector parsing and retains selected schema-row
membership and actual coordinate ranges. Full shard-plan/manifest partition and
source-to-draft LoadedRow/RowsBound/DerivedParameter are still OPEN; an arbitrary
Q corpus has not been proved complete/nonoverlapping by this per-block relation.

All three original parameters, the omitted frozen scalar, alias, both segments,
five original Q blocks and36coordinates compose using component lemmas. The exact
schema preimage is376bytes (fixture file's terminalLF excluded per originalfingerprint).
Schema hash uses raw canonical bytes, no domain/NUL; scale has a separate original004
domain. The two-preimage fixture adapter is SYNTHETIC/UNVERIFIED, not SHA256 or producer
source/exporter authority.35small cases distinguish byte parser checks and typed
shape/policy/alias/list guards. Changed first Q with old payloadSHA still joins in
Lean and fails Python PAYLOAD_HASH. Native admission/recovery is not established.

47generaltheorems/46defs+10types;78component/kerneltheorems/20fixturedefs,201newnames
axiomaudited including dotted helpers, standardkernelaxiomsonly. FullLean1107jobs,
fourfreshkernels PASS; final670tooling/38oracle/7targeted,Ruff/format/consistency and
33legal112illegal PASS;368generatedfiles byte-exact. Original fixtures reused,
no new giant native/state corpus. Only final stable logs count.21TLA/schema/runtime/
147nativewitnesses unchanged;145legacy onlysemanticsID. No newnative/TLC/mutants;
retained bounded scopes unchanged. Mandatory44/45/nativeArithmeticRecoveryRefines
missing; separate nativecertificate-00/-01canonicalityFAIL unchanged,Phase0unfrozen,
makeabsent/notaggregateformal-check. DemosHTTP200/no restart;frozenrefs unchanged.
No localPASS/GO/guardchange/independentattestation. Source-bound semantics: sha256:d44c5573892eb1da5ec4207ccfa0f1afb2a254092f85962a286bb7a84a3f4e50.


## 27 September 2026 — original shard-plan bytes and exact derived partition in Lean

T044/T048/T053/T054/T056/T057. Formal proposal only; NO_GO. Scope:
formal/proposals/native-shard-plan-proof.md; evidence:
formal/proposals/evidence/native-shard-plan.json. NativeShardPartition computes
the original004 greedy partition from the full decoded schema. General kernel
proofs establish exact total, coordinate coverage, ordered nonoverlapping
intervals, increasing ordinals and bounded counts/payloads. The target must be
even 2..1048576 bytes; global fuel is4096 shards. Exhaustion rejects rather than
returning a partial plan. Counts use min(target/2,remaining), offsets and starts
come from the schema, and every payload has exactly two bytes per coordinate.

NativeShardPlanBytes decodes all nine top-level fields and every ordered six-field
entry from original canonical bytes. NativeShardPlanBinding retains every numeric
field/name/position, computes the entire expected plan, compares the whole ordered
list, and checks semantics/profile/schema/scale/version/type/total. The per-Q join
retains the whole decoded scale and requires the exact plan slot at the parsed
header ordinal. This proves a complete plan and individual block membership,
not full manifest/corpus availability or producer authentication.

All five original Q blocks and36coordinates compose with the unchanged1079-byte
plan. Its preimage is original004 shard-plan domain + NUL + original canonical
bytes, separately from schema/scale domains. The three-preimage fixture adapter
is SYNTHETIC/UNVERIFIED, not SHA/source/exporter authority.23small kernel cases
separate byte grammar, computed partition, metadata and remaining hash scopes.
Changed Q with old payload SHA still joins in Lean and fails Python PAYLOAD_HASH.
Python mutation tests deliberately bypass only resolved plan documents to reach
partition checks; separate source substitution fails SOURCE_HASH before writing.

35 general theorems/23 definitions/10 types;72 component/kernel theorems/32 fixture
definitions.172 new named declarations audited, standard kernel axioms only.
Full Lean1111 jobs and four fresh kernels PASS. Final677 tooling/38 oracle/7 new
targeted tests,33 legal/112 illegal traces, Ruff/format/consistency PASS;
370 generated files byte-exact. Only final stable logs count.21 TLA modules,
public schema, runtime and147 native witnesses unchanged;145 legacy traces only
semanticsID. No fresh native/TLC/mutants, prior finite scopes retained.
Mandatory44/45/nativeArithmeticRecoveryRefines still missing; native certificate
-00/-01 canonicality FAIL unchanged. Phase0 unfrozen; make absent, aggregate
formal-check not claimed. Three demos HTTP200 without restart, frozen refs unchanged.
No native guard change/local PASS/GO/independent attestation. Next: complete
original manifest/leaf/header list and byte totals, config/proof/availability
and SHA/source authority, then source-to-draft arithmetic and full recovery.
Source-bound semantics: sha256:df97e6a9107ae243e4a3f555404384745acb1f781860329e6391a3c8107fe8a0.


## 27 September 2026 — complete original manifest and ordered raw Q corpus in Lean

T044/T048/T053/T054/T056/T057. Formal proposal only; NO_GO. Scope
formal/proposals/native-manifest-proof.md; evidence formal/proposals/evidence/native-manifest.json.
NativeManifestBytes decodes all18 fields and each ordered8-field reference from
original bytes, with complete canonical preimage/roundtrip/uniqueness and bounded
list guards. NativeManifestBinding actually decodes schema/scale/plan, derives
the entire partition and matches all reference entries and actual raw blocks in
order. Each complete expected header comes from original manifest/ref fields and
the actual payload hash adapter. Unmatched tails reject. Every original numeric
field, leaf identity, payload, vector and envelope remains linked to its position.
General corpus proofs derive exact counts, full coordinate coverage and both
byte totals; source lemmas preserve original complete frame/payload preimages.

NativeManifestMerkle decodes content-ID hex to32 raw bytes, hashes each ordered
pair with the original domain andNUL, duplicates an odd final node and preserves
a singleton. General Layer/Tree lemmas retain the exact recurrence, pair digest
sizes and level lengths. The complete original2198-byte manifest, five blocks,
36coordinates,72payloadbytes and4798envelopebytes compose from checked components.
This is local complete corpus correspondence under UNVERIFIED hash, not remote
availability, cryptographic identity, exporter authority or protocol admission.
Original parent checkpoint preimage is still absent. Config/proof/parent/AC/ISC/
EC/APC authority, general native resources/codecs and source-to-draft arithmetic
remain open. The synthetic exact-preimage hash adapter is NOT SHA verification.

Large whole-document byte reduction was replaced by source-component preimage
lemmas; hash witnesses use explicit branch proofs and Merkle layers compose from
checked pair facts. Only final stable-source results count; discarded draft
resource/compile failures are not evidence. Full Lean1115jobs, four fresh kernels,
axiom audit,685tooling/38oracle/8targeted,33legal112illegal,Ruff/format/consistency
and372file byte-exact regeneration PASS. Declaration inventory and exact counts
are recorded in machine-readable evidence.21TLA/schema/runtime/147nativewitnesses
unchanged;145legacy onlysemanticsID. No fresh native/TLC/production mutants.
Mandatory44/45/nativeArithmeticRecoveryRefines missing; separate nativecertificate
-00/-01canonicalityFAIL unchanged. Phase0 unfrozen,make unavailable, no aggregate
formal-check claim. Stopped Controller/Presentation restored; nodePID unchanged; saved verification hash and baseline receipt reverified. All3HTTP200/frozenrefs unchanged. No guard
change/localPASS/GO/independentattestation. Next: checked original config/proof
bodies and their actual source links, verified hashes/authority, then full-vector
source-to-draft/current/arithmetic and general phase/journal/QC/recovery relation.
Source-bound semantics: sha256:031ac06b84d94541b8579e19e0b49f7f5fa724380314cdff2c285fc3dba518bb.


## 27 September 2026 — original configuration/proof bytes and accumulator bounds in Lean

T044/T048/T053/T054/T056/T057. Formal proposal only; NO_GO. Scope
formal/proposals/native-accumulator-lean-proof.md; evidence
formal/proposals/evidence/native-accumulator-lean.json. NativeAccumulatorBytes
decodes all12 config and18 proof fields, including fixed ordered theorem-name
metadata, from canonical original bytes. General roundtrip/preimage/uniqueness
proofs do not treat historical IDs, theorem names or PASS as proof authority.
NativeAccumulatorBinding parses exact canonical decimals up to positive INT128,
recomputes P=32767*A and S=P*N and checks separate product/accumulator widths,
declared bounds and S<=F<=selected maximum. General FixedPoint composition proves
every bounded signed product and subset/prefix sum under explicit actual
coefficient/Q/count premises. The exact denominator remains independently bound;
no LCM, quantum or certified-weight divisibility is inferred. F-S is proved the
unique admissible headroom, not an observation of an actual native call.

The loader compares the complete immutable004 worker profile and original
config/proof metadata/hash-domain preimages. bindCorpus executes the complete
original manifest/schema/scale/plan/raw-Q relation and uses its actual proof and
config/schema/plan/scale/profile edges. General composition preserves every
original block; it accepts no caller-approved whole corpus. Original config/proof
examples compose checked byte components/numeric fields. Three finite hashes
remain SYNTHETIC/UNVERIFIED, not verified SHA/native authentication.29 small cases
separate positive endpoints, width errors, product/prefix substitutions, canonical
decimals and metadata. No new combined full-corpus example or native execution.

Three modules:22 general theorems/28 definitions/7 structures and138 fixture
theorems/71 definitions;266 new declarations axiom-audited with only standard
propext/Quot.sound/Classical.choice. Large string-to-byte length reduction caused
a discarded draft resource failure; explicit identical byte constants remove
that cost. Only final stable-source build/tests/logs count. Full Lean1118jobs,
three fresh kernels,690 tooling/38 oracle/5 new targeted tests,33 legal/112 illegal,
Ruff/format/consistency and374-file byte-exact regeneration PASS.21TLA/schema/
runtime/147native witnesses unchanged;145 legacy changes onlysemanticsID. No fresh
TLC or mutants. Mandatory44/45/nativeArithmeticRecoveryRefines missing; original
native certificate decimal canonicality FAIL unchanged. Phase0 unfrozen;make
unavailable, aggregate formal-check not claimed. Three demos HTTP200 without
restart; frozen refs unchanged. No guard change/local acceptance PASS/GO.

BaseRoundConfig/parent/008proof source bytes, authenticated authority/hash/exporter,
actual source-to-draft vector/weight/current/model/optimizer/APPLY relation and
full phase/QC/journal/crash/unknown/torn/repair recovery remain open. Next: derive
actual original APC coefficients from the specific loaded proof denominator and
complete eligible membership, preserving final alpha (do not multiply EC gamma
again), then join every actual Q vector and native/draft assignment. Missing
original proof/preimages must stay missing; synthetic examples do not authenticate
history. Contract freeze/offline reproduction/independent reviews still required.
Source-bound semantics: sha256:32609e9e3f8b4b2dec130c993e4b7f8c5c06db7ffda8ea97b23ece3b446dd57e.


## 27 September 2026 — original APC membership and proof-bound coefficients in Lean

T044/T048/T053/T054/T056/T057. Formal proposal only; NO_GO. Scope
formal/proposals/native-plan-coefficients-proof.md; evidence
formal/proposals/evidence/native-plan-coefficients.json. NativePlanMembers
executes actual original policy/state decoding and selects the exact finalized
APC with its checked ISC/EC/norm/seed source edges. It checks every common context,
parent and primitive EC-seed edge, unique ISC tickets and full norm membership,
then aligns all ordered ISC/EC entries including rejected members. Complete
accepted rows retain original commitments, ACs, domains, final alpha, gamma and
buckets; no missing/extra tail or supplied coverage table is accepted. The prior
cross-ISC counterexample now rejects in this stronger projection relation.

NativePlanCoefficients loads the actual APC-referenced config/proof/profile and
checks schema/base-config identity. From the specific loaded denominator L and
each reduced final alpha a/b it checks b|L and computes c=a*(L/b), proving c*b=a*L.
No minimal-LCM substitution or second gamma multiplication. Global count includes
zero weights. Generic product/domain-prefix/subset proofs compose the decoded
proof limits with actual derived coefficients. Positions preserve every term;
Q-value bounds remain explicit premises pending full original raw-vector join.
Stronger cross-parent/4096/global-count restrictions are not native admission
equivalence. Shared raw hash adapter, source policy/finality/signers/EC-seed and
availability provenance remain unauthenticated, with no approval Boolean.

Original APC components and its missing proof identity are retained. Separate
synthetic components have four ISC/EC members, three accepted weights0,1/3,1/2,
gamma1/7, L12 and coefficients0,4,6.32 small kernel cases cover full coverage,
order/domain/parent/duplicate failures, count and denominator/weight bounds.
The count-negative retains a valid internally computed two-term proof before
rejecting three actual rows. No new whole-policy/proof kernel execution or
native run. All original native bytes/sequences5/6/8 unchanged.

Three modules:25 general theorems/17 definitions/8 structures;32 kernel examples/
8 fixture definitions.90 names axiom-audited with only standard propext,
Quot.sound,Classical.choice. Full Lean1121jobs/three fresh kernels,695tooling/
38oracle/5targeted,33legal112illegal,Ruff/format/consistency and376 generated
files byte-exact PASS. Only final stable-source evidence counts.21TLA/schema/
runtime/147nativewitnesses unchanged;145legacy onlysemanticsID. No freshTLC or
productionmutants. Mandatory44/45/nativeArithmeticRecoveryRefines missing;
nativecertificate-00/-01canonicalityFAIL unchanged. Phase0unfrozen;make absent,
aggregateformal-check not claimed. Three demosHTTP200withoutrestart/frozenrefs
unchanged. No runtime guard/localPASS/GO/independentattestation.

Next: every complete original Q manifest/DRQ1/schema/scale/plan/config/proof
preimage matched to the derived accepted APC rows and native availability inputs,
then full original-to-draft vector assignments and arithmetic. Native commitment
and AC IDs have no invented equality to manifest/Merkle IDs; retain unauthenticated
primitive mapping and require its real source provenance. Missing original008
proof/base/current/model/optimizer/APPLY preimages remain missing. General
phase/QC/send/current/crash/unknown/torn/repair/WAL relation, hash/codecs/exporter,
freeze/offline reproduction/independent reviews and merged authority remain open.
Source-bound semantics: sha256:ded966cc2a667de9dcddbf7fc8ba82ba3d431fe40f150c1d1d69e0efdbecdbaf.


## 27 September 2026 — original Q corpus and source-derived coefficient bounds in Lean

T044/T048/T053/T054/T056/T057. Formal proposal only; NO_GO. Scope
formal/proposals/native-available-q-lean-proof.md; evidence
formal/proposals/evidence/native-available-q-lean.json. NativePlanQCorpus.bind
executes original policy/state/APC coefficient loading, then every accepted row's
complete original manifest/schema/scale/plan/config/proof/profile/DRQ1 loader.
Exact ordered ticket/domain/commitment/AC/schema/proof/config links retain every
eligible term, including zero weights; missing/extra input tails reject. Rejected
EC members remain in original certificate source. Shared decoded accumulator
identity is derived from actual loader equations and proof-ID equality, not
assumed for caller-supplied whole bodies/snapshots. Original bytes/sequences stay.

NativeAvailableQ checks typed native first-insert availability primitives,
ordered unique required/covered sets and distinct configured attesters/threshold.
Exact manifest permutation checks full leaf multiplicities without changing
schema/range order. An equal but incomplete required/covered pair fails the new
source relation despite passing the old native component. Native commitment ID,
manifest ID, Merkle root and AC ID remain distinct. Typed permissions/observations
are UNAUTHENTICATED_COMPONENT_INPUT; their source provenance, JSON-envelope
codec, signatures and actual availability are NOT proved. Opaque-ID positive
counterchecks explicitly retain this gap; original ISC identity alone does not
authenticate an entirely substituted synthetic history.

Generic original frame/payload lemmas derive signed16 Q range from actual bytes.
Successful full source binding now gives product and every domain subset/prefix
bound using actual coordinate lookup equations, with no assumed Q-value bound.
The selector may vary coordinates between tickets: this is a bound, not yet
aligned vector reduction equality. No second gamma or minimum-LCM substitution.
Proof/config/schema are shared; cross-ticket scale/plan/parent/range/quantum and
full original-to-draft assignments remain next. Existing per-parser resources
retain their scope; no aggregate allocation or native failure-order equivalence.

Three modules:24 general theorems/10 definitions/five structures/one inductive
relation;55 component kernel theorems/40 fixture definitions. All135 names
axiom-audited with only propext/Quot.sound/Classical.choice. Twenty primitive and
coverage pairs reuse all17 retained native component cases plus three mutations.
Five original block range proofs reuse the preceding complete manifest; one
product example combines actual payload with a separately synthetic coefficient.
No new combined whole-policy/manifest/proof kernel example or native run claimed.
Membership drafts that unnecessarily evaluated full structures were replaced by
explicit position witnesses; only final stable-source logs/evidence count.

Full Lean1124jobs/three fresh kernels,700tooling/38oracle/5targeted,33legal112illegal,
Ruff/format/consistency and378file byte-exact regeneration PASS.21TLA/schema/runtime/
147nativewitnesses unchanged;145legacy changes onlysemanticsID. No freshTLC or
productionmutants. Mandatory44/45/nativeArithmeticRecoveryRefines missing;
nativecertificate decimal -00/-01 FAIL unchanged; Phase0unfrozen;make unavailable,
aggregate formal-check not claimed. All3demosHTTP200withoutrestart/frozenrefs
unchanged. No nativeguard/localPASS/GO/independentattestation.

Next: derive cross-ticket shared original vector/range/quantum context, construct
source-to-draft SCHEMA/Q_SHARD and full LoadedRow/RowsBound/DerivedParameter.
Native commitment/AC/config/current source authority and original008 proof/base/
current preimages remain missing. Do not fabricate authenticated mappings, model/
optimizer/APPLY quantum or silently identify original and draft content IDs.
Full phase/QC/send/delivery/current/crash/unknown/torn/repair/WAL relation,
codecs/hash/exporter/arbitrary snapshots, contract freeze/offline reproduction
and independent reviews remain mandatory before merged formal authority.
Source-bound semantics: sha256:0ee83e8c3d30190a8d518c9069175f3e26d22c5c1cd86263e3f4aeb09df563f5.


## 27 September 2026 — aligned original full-vector arithmetic in Lean

T044/T048/T053/T054/T056/T057. Formal proposal only; NO_GO. Scope
formal/proposals/native-vector-arithmetic-lean-proof.md; evidence
formal/proposals/evidence/native-vector-arithmetic-lean.json. NativeVectorContext
loads the entire original policy/APC/Q byte corpus through NativePlanQCorpus,
then compares all seven shared manifest identities, complete decoded schema/
scale/plan and every ordered block range/quantum. Actual loader equations derive
same original preimages; neither hash injectivity nor caller-supplied decoded
corpus/expected-body equality is assumed. Same parent identity is not current
model authority. Full source records and rejected EC members remain retained.

NativeVectorArithmetic.run derives every domain/shard key and computes complete
vectors from original APC final alpha, exact proof denominator and actual Q
payloads. Within-domain member order and zero weights remain. General theorems
bind each output coordinate to checked accumulation over the original derived
coefficients, with exact original slice frames and no coordinate lookup fallback.
Original product-width bounds compose actual byte/plan loaders. Separate kernel
fraction/denominator/coefficient-sum and every prefix guard are rechecked; these
are explicit stronger draft restrictions, not original native admission changes.
No second gamma, minimum-LCM replacement, supplied result or scalar reduction.

Three modules:31 general theorems/15definitions/fourstructures,51component kernel
cases/16fixturedefinitions; all117explicitnames axiom-audited onlypropext,
Quot.sound,Classical.choice. Original five-block36-coordinate layout, widths
4/8/8/8/8 and quanta are reused. Ten vector cases from the pinned synthetic
multi-ticket example cover two domains, alpha1/3,1/2,0,L12,Q/-Q; Fraction checks
every coordinate/prefix independently. One kernel case directly reuses an original
loaded block with a separately synthetic weight. Context/range/order/quantum,
shape/fraction/denominator and overflow negatives pass. No new complete raw-source
run example or native execution; original bytes/sequences5/6/8 remain unchanged.

Full Lean1127jobs/three fresh kernels,706tooling/38oracle/6targeted,
33legal112illegal,Ruff/format/consistency and380file byte-exact regeneration PASS.
Only final stable-source logs count.21TLA/schema/runtime/147nativewitnesses
unchanged;145legacy traces onlysemanticsID. No freshTLC/productionmutants.
Mandatory44/45/nativeArithmeticRecoveryRefines missing; nativecertificate decimal
-00/-01FAIL unchanged;Phase0unfrozen;make absent/noaggregateformal-check.
Three demo servicesHTTP200withoutrestart/frozenrefsunchanged. No runtime guard,
localPASS, independentattestation or GO.

Next: complete original-to-draft SCHEMA/Q_SHARD byte constructors, explicit
coordinate naming/range/size representability and distinct original/draft hash
preimages; join actual draft LoadedRow/RowsBound/DerivedParameter to this checked
source arithmetic. This stage does not yet prove that codec/graph relation.
Missing original008proof/base/current preimages and unauthenticated primitive
availability/configuration/EC-seed remain missing. Full current/model/optimizer/
APPLY,phase/QC/send/delivery/journal/crash/unknown/torn/repair/WAL,arbitrarysnapshots,
codecs/hash/exporter,native decimal compatibility,freeze/offline reproduction and
independent reviews remain mandatory before merged formal authority.
Source-bound semantics: sha256:90dc0a6911746969c8cbbb6dc7377788ecfafa04cdd552174a12e2191a70bd7d.


## 27 September 2026 — exact original vector draft artifacts and PARAMETER join in Lean

T044/T048/T053/T054/T056/T057. Formal proposal only; NO_GO. Scope
formal/proposals/native-vector-artifacts-lean-proof.md; evidence
formal/proposals/evidence/native-vector-artifacts-lean.json. NativeVectorLayout
constructs every original coordinate/shard label with complete ordered local/global
coverage and representability checks. Original schema/plan metadata remains;
long names and a/a.b conflicts reject this profile without changing native admission.

NativeVectorArtifacts constructs entire canonical SCHEMA/Q_SHARD byte images,
distinct draft hash preimages and original full-vector contributions. Actual
loadRow/loadImages check stored byte and typed-payload equality, original committed
Q/frame fields and complete RowsBound with original weights/order/values.
NativeVectorJoin.run calls original source bind and actual deriveParameter, checks
exact stored SCHEMA bytes, full frame, contribution/row lists, specific denominator
and accumulator width, then derives numerator identity from the checked computations.
The original coefficient/coordinate theorem composes; no supplied expected result.

Four modules:27 generic theorems/27definitions/sixstructures;92component/kernel
proofs/19fixturedefinitions. All171explicitnames audited onlypropext/Quot.sound/
Classical.choice. Original36coordinates/five full vectors and1338-byte SCHEMA plus
five complete Q bytes match Python. Layout/name/range/order/hash-kind/vector/byte
negatives are checked. Component row metadata is explicitly constructed; no new
complete raw-source run or authenticated native history. Original bytes/5/6/8 stay.

Full Lean1131jobs/four fresh kernels,712tooling/38oracle/6targeted,
33legal112illegal,Ruff/format/consistency and382file byte-exact regeneration PASS.
21TLA/schema/runtime/147nativewitnesses unchanged;145legacyonlysemanticsID.
No freshTLC/productionmutants. Mandatory44/45/nativeArithmeticRecoveryRefines missing;
nativecertificate decimal-00/-01FAIL remains,Phase0unfrozen,make absent and aggregate
formal-check not claimed. DemosHTTP200withoutrestart/frozenrefsunchanged.

This joins one selected domain/shard under existing codec/hash/draft Binding
premises. The8MiB cap is per selected assignment, not the full-batch Python cap;
allocation/time equivalence is not proved. Full original context/certificate/current/
model/optimizer/APPLY authority and source provenance remain open. Original008proof/
base/current preimages remain missing. Next: instantiate a complete original-source
and draft PARAMETER join example through component lemmas, then derive the full
original configuration/context and current/model/optimizer/APPLY profile relation;
do not infer them from matching parent strings or invent absent captures.
General bounded codecs/hash/exporter, full phase/QC/send/delivery/journal/current/
crash/unknown/torn/repair/WAL, arbitrary snapshots, full-batch resources, native
decimal compatibility, freeze/offline reproduction and independent reviews remain.
No localPASS, runtime guard change, independentattestation or GO.
Source-bound semantics: sha256:12954f785fc8726b3b53c580805a624eefda5700f3eb0ecfb158fc13b855d5d7.


## 27 September 2026 — whole original policy/state APC membership and proof refusal

T044/T048/T053/T054/T056/T057. Formal proposal; NO_GO. Scope
formal/proposals/native-plan-source-proof.md; evidence
formal/proposals/evidence/native-plan-source.json. NativePlanSourceVectors composes
the retained5849-byte codec-PARAMETER policy and674-byte state matching its snapshot
ID through actual raw decoders, finalized ISC, norm, seed, EC, APC and eligible-member
extraction. All original lists, parent IDs, final alpha/bucket and unused later
PARAMETER fields are retained. The latter are not admitted by this plan parser.

The attempted positive whole-vector example exposed incompatible existing sources:
original008 requires sha256:ffff...ffff; available004 proof has a different actual
content ID. This was not repaired by rewriting the source. NativeSourceRefusal
proves missing/incorrect proof refusal through coefficients, Q corpus, context and
the complete NativeVectorJoin.run for arbitrary permissions/Q inputs and separate
draft Binding. Concrete raw-source cases reject missing and substituted004 proof.
Finite SHA samples remain explicitly synthetic and do not authenticate the source.

Two modules:7 general refusal/composition theorems,56 component/kernel theorems and
23 fixture definitions. All86 names audited onlypropext/Quot.sound/Classical.choice.
Existing component encodings/certificate lemmas reused;19 new encoding lemmas.
Full Lean1133jobs/twofreshkernels,717tooling/38oracle/5targeted,33legal112illegal,
Ruff/format/consistency and384file byte-exact regeneration PASS. Only final stable
source counts; draft failures superseded.21TLA/schema/runtime/147nativewitnesses
unchanged;145legacytraces onlysemanticsID. No freshTLC/productionmutants.
Mandatory44/45/nativeArithmeticRecoveryRefines missing;native certificate -00/-01
FAIL remains;Phase0unfrozen;make absent/noaggregateformal-check. Three demosHTTP200
withoutrestart/frozenrefsunchanged. No native guard/localPASS/GO/attestation.

This is a complete raw-source plan membership example and end-to-end refusal, not
a successful original-source arithmetic/draft join. Original008 proof/base/current
captures remain missing. Next: construct a separately versioned synthetic whole
policy/state wrapper for the already available004 graph and joined_fixture source
documents, with new identities and explicit primitive provenance, then instantiate
actual raw source bind/vector join through checked component lemmas. Do not reuse
the incompatible original008 proof/context or call the new wrapper a native capture.
Advance full source configuration/context/current/model/optimizer/APPLY binding;
do not spend another stage only rediscovering the same missing original proof.
General codecs/hash/exporter, arbitrary snapshots, full-batch resources, complete
phase/QC/send/delivery/journal/current/crash/unknown/torn/repair/WAL relation, native
decimal compatibility, amendment freeze, offline reproduction and independent
review remain required. No helper discharges nativeArithmeticRecoveryRefines.
Source-bound semantics: sha256:c91af44224ba718bf965120bcf580b91a580b9cb74be2fdb057fd6ed96b9149d.


## 27 September 2026 — synthetic raw source to complete original Q arithmetic

T044/T048/T053/T054/T056/T057. Formal proposal; NO_GO. Scope
formal/proposals/native-vector-source-proof.md; evidence
formal/proposals/evidence/native-vector-source.json. A separately versioned
synthetic4598-byte policy and674-byte state now instantiate actual source section,
membership, accumulator, complete Q corpus and NativeVectorContext.bind checks.
The original004 schema/scale/plan/config/proof/profile/manifest/five DRQ1 preimages
remain unchanged. New certificates/state use their actual newly computed IDs;
original008's absent proof is not repaired. All36 coordinates across five vector
reductions are computed from the loaded source rows. Missing/extra input lists
reject at the raw corpus entry. Python negatives reject corrupt Q or missing proof.

Two new modules and four general composition helpers:222 component/helper/kernel theorems and93 definitions,315 explicitly
axiom-audited names, onlypropext/Quot.sound/Classical.choice. Forty-two new policy
encoding lemmas reuse prior components. Thirty exact-preimage SHA samples share
one synthetic adapter; no SHA implementation or exporter authentication is proved.
Full Lean1135jobs/fourfreshkernels,723tooling/38oracle/6targeted,33legal112illegal,
Ruff/format/consistency and387file byte-exact regeneration PASS. Only final stable
source logs count; resource-heavy draft reductions were superseded by component
proofs.21TLA/schema/runtime/147nativewitnesses unchanged;145legacyonlysemanticsID.
No newTLC/productionmutants. Mandatory44/45/nativeArithmeticRecoveryRefines missing;
native decimal -00/-01FAIL,Phase0unfrozen,make absent/noaggregateformal-check.
Three demosHTTP200withoutrestart/frozenrefsunchanged. No nativeguard/localPASS/GO.

The nonempty candidate required by the policy grammar is explicitly STRUCTURAL-ONLY,
with an opaque body ID and empty parents; it is NOT admitted. The synthetic inner
state root and signer/seed/norm/availability observations remain primitive and
unauthenticated. Parent checkpoint equality does not supply current vectors, and
worker quantization profile is distinct from certificate APPLY profile. The new
full-run equation reaches the remaining draft join but does not instantiate a
complete draft Binding or successful NativeVectorJoin.run.

Next: compose source-derived artifact store/RowsBound/DerivedParameter through
the remaining draft join, while deriving/checking the full source configuration,
vote context and current/model/optimizer/APPLY relation. Avoid another isolated
numeric example or re-proving absent008 proof. Use component equations, not giant
decide over dependent complete contexts. Missing original base/current/proof
captures stay explicit. General codecs/hash/exporter, full-batch resources,
arbitrary snapshots, phase/QC/send/delivery/journal/current/crash/unknown/torn/
repair/physical-WAL refinement, decimal compatibility, amendment freeze, clean
offline reproduction and independent review remain mandatory. No helper discharges
nativeArithmeticRecoveryRefines. Source-bound semantics: sha256:9a37056ab6320dbd4f2c29a175d4b690bcac0bd90de4721ed027d35ee21b7e64.


## 27 September 2026 — constructive vector source to actual PARAMETER extraction

T044/T048/T053/T054/T056/T057. Formal proposal; NO_GO. Scope
formal/proposals/native-vector-derivation-proof.md; evidence
formal/proposals/evidence/native-vector-derivation.json. NativeVectorDerivation
adds the constructive direction: actual Resolves/LoadedRow/RowsBound/FrameOrigin
witnesses imply the corresponding executable loader succeeds; an internally
checked DerivedParameter implies actual deriveParameter returns it.

The new Inputs relation carries checked layout/schema, actual resolved and fully
validated draft frame, selected assignment/partition, full eligible order, actual
original vector reduction, successful loadImages, exact contributions, denominator,
widths, source schema bytes and selected-assignment resource bounds. It contains
no expected body/numerators, successful draft derive equation or approval Boolean.
The constructor derives all eight typed PARAMETER_EXPECTED fields from these
inputs. General theorems prove actual extraction, existing join and complete raw
run success under these checked input witnesses. Every original slice position
retains the exact generated Q bytes/store presence/leaf ID/source weight; omitted
contributions and missing leaves are impossible under the relation. A different
decoded quantum rejects even if numerical rows could match.

One new generic module:19 general theorems,one definition,one structure; all21
explicit top-level declarations axiom-audited, onlypropext/Quot.sound/Classical.choice.
Full Lean1136jobs/freshgeneric kernel,723tooling/38oracle,33legal112illegal,
Ruff/format/consistency and387file byte-exact regeneration PASS. No fixture expansion
or new concrete complete raw-run instantiation. Only final stable-source logs count.
21TLA/schema/runtime/147nativewitnesses unchanged;145legacyonlysemanticsID.
No freshTLC/productionmutants. Mandatory44/45/nativeArithmeticRecoveryRefines
missing;native decimal -00/-01FAIL,Phase0unfrozen,make absent/noaggregateformal-check.
Three demosHTTP200withoutrestart/frozenrefsunchanged. No nativeguard/localPASS/GO.

The relation retains actual loadImages deliberately: an arbitrary RowsImage
structure alone does not separately establish each decoder payload/quantum check.
This is a general conditional construction, not proof that the previous synthetic
raw fixture or a native capture supplies the required complete Inputs/Binding.
Output context comes from the decoded draft assignment; original source config,
vote contexts/deadlines, current model/optimizer and APPLY profile identity remain
OPEN. Codec/exporter/anchor authentication remains external. It is not the missing
nativeArithmeticRecoveryRefines theorem.

Next: derive/check original source configuration/context/parent/ISC/EC/APC fields
against the independently loaded draft frame, including complete membership,
domain-shard coverage and assignment-context identity; then instantiate Inputs
from that checked relation. Do not obtain a claimed native bridge by filling
dummy model/optimizer/profile/current/authority values into a synthetic wrapper.
Missing original008 proof/base/current preimages remain explicit. Preserve actual
bytes and all per-actor sequences. General codecs/hash/exporter, full-batch resources,
arbitrary snapshots, phase/QC/send/delivery/journal/current/crash/unknown/torn/repair/
physicalWAL, decimal compatibility, contract freeze/offline reproduction and
independent review remain required. Source-bound semantics: sha256:77a0edb93e2cd9286ff8f670cd659d1891b73e88123241b247a78a115e2659e8.


## 27 September 2026 — original vector authority and selected PARAMETER body checks

T044/T048/T053/T054/T056/T057. Formal proposal; NO_GO. Scope
formal/proposals/native-vector-authority-proof.md; evidence
formal/proposals/evidence/native-vector-authority.json. NativeVectorAuthority
follows raw source loaders to the original policy/state and computes all six
context fields, complete ISC/eligible membership and ticket/domain order.
The executable join now runs original proposed PARAMETER lineage, separately
checks vote context, full source certificate context, exact ISC/EC/APC and
denominator, complete configured assignment keys, and a permutation of whole
original typed bodies/payloads. It does not substitute equal counts or body IDs.

The stronger verify/run entry compares the selected proposal numerators and
all original manifest Q leaf references with actual vector computation and
exact shard-position lookups. Source contribution order stays intact; only the
native certificate leaf list is sorted, preserving every multiplicity. Missing,
extra, duplicate or numerically substituted entries reject. Original strings
are retained, including the unresolved -00/-01 compatibility boundary.

Two modules:32 general theorems,23 definitions,five structures; eight small
comparator kernel cases/one fixture definition. All69 explicit top-level names
axiom-audited with onlypropext/Quot.sound/Classical.choice. Full Lean1138jobs,
two fresh kernels,723tooling/38oracle,33legal112illegal,Ruff/format/consistency
and387files byte-exact PASS. All final source/evidence hashes match Git blobs.
21TLA/schema/runtime/147nativewitnesses unchanged;145legacyonlysemanticsID.
No freshTLC/productionmutants. Mandatory44/45/nativeArithmeticRecoveryRefines
missing;Phase0unfrozen;make absent/noaggregateformal-check. Three demosHTTP200
without restart and frozenrefs unchanged. Only final stable-source evidence counts.

No new complete Inputs/Binding or successful full raw/native run is instantiated.
Small comparator examples deliberately have invalid authority/tiny leaf labels;
a numeric-only positive is not protocol admission. Exact native shard-label to
draft-label equality is a representability restriction. Draft/native schema,
profile and ISC/EC/APC artifact mappings, every original ISC commitment, current
vectors and APPLY profile remain OPEN. No parent checkpoint string proves them.
General codec/hash/exporter authentication and full-batch resources remain open.

Next: construct source-derived ISC/EC/APC artifact payloads with independently
anchored original-to-draft Q/manifest correspondence for every member, including
rejected members, and derive the configured shard-label mapping from real source
contracts. Do not invent missing current/model/optimizer/APPLY profile payloads
or populate a synthetic wrapper to claim a native bridge. Then instantiate the
full Inputs relation and joined original/draft run. Full arbitrary snapshot,
phase/QC/send/delivery/journal/current/crash/unknown/torn/repair/physical-WAL
recovery, decimal compatibility, contract freeze/offline reproduction and
independent review remain mandatory. Original008 proof/base/current preimages
remain absent. Source-bound semantics: sha256:cca88293f7943266b07d7fa3c200563f77fd4224564d0352288c9af75e19f865.


## 27 September 2026 — complete original ISC corpus and computed ISC/EC graph

T044/T048/T053/T054/T056/T057. Formal proposal; NO_GO. Scope
formal/proposals/native-isc-projection-proof.md; evidence
formal/proposals/evidence/native-isc-projection.json. NativeIscCorpus loads all
original ISC members and their complete manifests/Q preimages, including rejected
EC members. It preserves exact tuple/EC entry order, native context, original
commitment/availability identifiers and every original shard reference. Missing
or extra inputs reject. The full eligible member/manifest list must equal the
actual checked arithmetic corpus, not only its count or values.

NativeIscProjection computes canonical Q, full ISC and EC records, retaining all
original-to-projected leaf positions. Eligible Q encoding is definitionally the
same as the existing arithmetic projection. The store checker resolves the exact
computed schema/ISC/EC and every Q preimage, then joins the same previously
checked PARAMETER frame/body with those complete authority/parent contents.
No external whole translated body or arithmetic approval Boolean is supplied.

Three modules:40 general theorems,31 definitions,seven structures/one inductive;
27 kernel/component cases and five fixture definitions. All111 explicit top-level
names axiom-audited with only propext/Quot.sound/Classical.choice. Full Lean1141
jobs,three fresh kernels,725tooling/38oracle,33legal112illegal,Ruff/format/consistency
and387generated files byte-exact PASS. All final source/evidence hashes match Git
blobs. 21TLA/schema/runtime/147native witnesses unchanged;145legacyonlysemanticsID.
No freshTLC/productionmutants. Mandatory44/45/nativeArithmeticRecoveryRefines
missing;Phase0unfrozen;make absent/noaggregateformal-check. All3demosHTTP200
without restart and frozenrefs unchanged. Only final stable-source evidence counts.

The actual all-member raw load is instantiated using the existing one-member
synthetic raw source and original004 Q preimages. A separate rejected-member
component changes only the eligibility bit; it is not a newly finalized EC.
Tiny encoding cases use deliberately invalid IDs and agree with independent
Python canonical JSON expectations. There is no new successful complete
original/draft Binding, joined PARAMETER execution or native exporter evidence.

Original commitment/availability observations remain explicit unauthenticated
primitive inputs. Current InputLedger receives required leaf IDs separately;
the ISC tuple alone cannot authenticate their derivation. Source-derived PLAN/APC,
native shard naming, current model/optimizer/APPLY profile, general codec/hash/
exporter and full-batch resource bounds remain open. Individual artifacts retain
the4MiB projection cap. Original008 proof/base/current captures remain absent.
No checkpoint label or worker quantization profile supplies current/APPLY vectors.

Next: derive actual PLAN assignments and APC payload from original finalized APC
weights/buckets and the complete checked ISC/EC corpus. Resolve the original
required_parameter_keys versus ordinal shard-label projection explicitly; preserve
every original assignment/member/quantum and reject missing or ambiguous mappings.
Then instantiate complete Inputs and the joined original/draft computation from
real available preimages. Do not fill missing authority/current/profile data with
dummy fixture values or equate structured TLA values with native content hashes.
General arbitrary-snapshot phase/QC/send/delivery/journal/current/crash/unknown/
torn/repair/physicalWAL recovery, native decimal compatibility, amendment freeze,
clean offline reproduction and independent review remain mandatory.
Source-bound semantics: sha256:d0da28582d27b85325fd8d60892f94d72c9770b43be79fa15eda2c4996780555.


## 27 September 2026 — complete PLAN/APC from original prepared assignments

T044/T048/T053/T054/T056/T057. Formal proposal; NO_GO. Scope
formal/proposals/native-plan-projection-proof.md; evidence
formal/proposals/evidence/native-plan-projection.json. NativePlanAssignments
derives every contribution from original finalized APC rational weights, whole
eligible member/manifest identity and exact original Q position. It retains every
domain row, decoded quantum/vector shape and actual proof denominator. Assignment
contexts and full original bodies come from NativeSizedParameterSection; the
original expanded-certificate 4MiB guards apply. No later aggregate or APPLY is
required. Full required-key matrix and entire selected body multiset are checked.

NativePlanProjection constructs canonical complete PLAN/APC and checks actual
store bytes/hash/length/typed payloads, reusing complete SCHEMA/Q/ISC/EC provenance.
Its joinedFrameOrigin theorem constructs all five FrameOrigin resolve relations
for the same existing checked PARAMETER frame. No caller-supplied whole translated
PLAN/APC or arithmetic approval flag is used. The APPLY-profile reference remains
an explicit shape-checked primitive; it is not derived or authenticated.

Three modules:32 general helper theorems/24 definitions/five structures,
23 kernel/component cases/12 definitions. All96 explicit top-level names
axiom-audited with only propext/Quot.sound/Classical.choice. Full Lean1144jobs,
three fresh kernels,727tooling/38oracle,33legal112illegal,Ruff/format/consistency
and387generated files byte-exact PASS. All final source/evidence hashes match
Git blobs. 21TLA/schema/runtime/147native witnesses unchanged;145legacyonly
semanticsID. No freshTLC/productionmutants. Mandatory44/45,
nativeArithmeticRecoveryRefines missing;Phase0unfrozen;make absent/noaggregate
formal-check. All3demosHTTP200withoutrestart/frozenrefsunchanged.

Existing source components retain actual ticket/weight/Q bytes and first-block
quantum1/4. A deliberately partial member image is not a full checker example.
Four short invalid-ID encoding cases match independent Python canonical JSON.
Draft context/contributions key order and local recursion-limit failures were
fixed before freezing; only final evidence counts. No new full original/draft
Binding, joined native execution or native exporter authority is instantiated.
Pinned original contract sources are separately hashed at e94fb08ad75d0693d566f1761cac8cc992bb4e42;
they are not the current-checkout runtime files and were not edited.

Native shard-name/ASCII context restrictions are explicit projection restrictions.
The native preparation accepts assignment context separately; APC alone does not
supply it. Original commitment/availability authority, current model/optimizer/
APPLY profile, full-batch resources and concrete hash/codec/exporter remain open.
Worker004 profile and checkpoint labels are not substitutes. Original008
proof/base/current captures remain absent; decimal -00/-01 compatibility still
fails. Conditional FrameOrigin is not the full admission/recovery relation.

The existing NativeApplyProfile module already checks original optimizer
coefficients and canonical original profile ID. Original ApplyArithmeticProfile
has an accumulator-proof reference but no explicit applyQuantum/outputRange;
these draft fields need an independently justified mapping. compute_candidate
receives parent values and parent IDs separately; its local content-ID shape
check alone cannot establish their hash equality. Inspect the caller/snapshot
provenance before composing current identity. Do not write a duplicate profile
decoder without checking the existing source module.

Next: bind current model/optimizer and actual APPLY profile from independently
anchored original preimages, then construct complete Inputs/Binding and instantiate
the joined original/draft computation. Inspect normative current-pointer/snapshot/
profile contracts first; preserve original preparation context and every canonical
record. Missing captures must remain missing, not be replaced with synthetic
fixture model/optimizer/deadline/profile values. Reuse component proofs and avoid
large new numeric fixtures. General arbitrary-snapshot phase/QC/send/delivery/
journal/current/crash/unknown/torn/repair/physicalWAL recovery, concrete bounded
hash/codec/exporter, native decimal compatibility, contract freeze, clean offline
reproduction and independent review remain mandatory.
Source-bound semantics: sha256:bdb9f2259277ac391e3b8f7a8905e14d6b841b83ee170292a7580497c1487b53.

## 27 September 2026 — original pointer history and canonical current values

T044/T048/T053/T054/T056/T057. Formal proposal; NO_GO. Scope
formal/proposals/native-current-history-proof.md; evidence
formal/proposals/evidence/native-current-history.json. NativeCurrentValues derives
every model/optimizer integer from the original finalized candidate decimal
spellings, retains exact order/count/bytes and signed64 bounds, and computes both
native value-hash preimages/IDs. The canonical round-trip requirement is a stronger
projection restriction; old native -00/-01 acceptance is unchanged.

NativeCurrentHistory checks every complete original pointer-WAL record against
one original policy/state byte pair, executing complete decoders/APPLY section,
selecting an actually listed finalized QC, constructing its command and comparing
the whole pointer record. Candidate parent model/optimizer match the previous
pointer. Exact next vectors/hashes are derived from the original candidate, not
supplied as a translation. Adjacent states, increasing heights and final pointer
are proved by checked execution/induction. Whole decoded-WAL and joined-history
final state equality is derived, not a premise. All source pairs and records
are retained in exact order; missing/extra evidence rejects.

Current vectors come only from the final checked candidate. Known empty or
torn-only history cannot invent initial values. Unknown stays incomplete.
Corrupt checksum, duplicate record and CRLF line rejection is preserved using
existing component proofs. The original torn suffix is retained, not claimed to
be physically truncated or authenticated. Existing rehashed-uncertified-WAL
counterexample still passes old recovery but cannot enter this API without
historical evidence. Parent-optimizer/canonical-value checks are additional
restrictions, not runtime recovery equivalence or a runtime fix.

Three modules:40 general helper theorems/11 definitions/eight structures,
34 kernel/component cases/two definitions. All95 explicit names axiom-audited,
only propext/Quot.sound/Classical.choice. Full Lean1147jobs,three fresh kernels,
729tooling/38oracle,33legal112illegal,Ruff/format/consistency and387generatedfiles
byte-exact PASS. Final source/evidence hashes match committed Git blobs.
21TLA/schema/runtime/147nativewitnesses unchanged;145legacyonlysemanticsID.
No freshTLC/productionmutants. Mandatory44/45/nativeArithmeticRecoveryRefines
missing;Phase0unfrozen;makeabsent/noaggregateformal-check. All3demosHTTP200without
restart/frozenrefsunchanged.

Small cases reuse prior separately synthetic candidate vectors[19,-19]/[2,-2]
and finite SHA samples, plus synthetic existing pointer-WAL components. Original
golden candidate placeholder hashes reject. No new positive full history,
original native capture, full original/draft Binding or joined execution is
instantiated. Initial draft names/default recursion errors are superseded by
the final stable run; local2048 recursion only for two prior small WAL negatives.

Original contracts separately pinned at e94fb08ad75d0693d566f1761cac8cc992bb4e42:
current-pointer next checkpoint equals QC next model hash; recovery does not
reload certificates/vectors. Original DomainAggregate and parent State types do
not contain quantum/schema; QLoRA forwards their values/IDs. Runtime is unchanged.
Whole observation completeness,
initial pointer provenance, independently authenticated policy/state and historical
APPLY arithmetic are not proved by this structural history checker.

Next: source-derived current MODEL/OPTIMIZER and actual APPLY PROFILE artifact
projection, preserving the distinction between native value-hash domains and
draft artifact domains. Schema/quantum/round configuration must come from an
independently bound source. Original ApplyArithmeticProfile has no explicit
applyQuantum/outputRange; do not fill these from synthetic fixtures. Reuse the
existing NativeApplyProfile and NativeApplyResult relations, checked original
current-history preimages and complete SCHEMA/PLAN/ISC/EC/APC derivation to build
complete Inputs/Binding where source permits. Missing original008 proof/base/
current captures remain missing. No later APPLY result may stand in for earlier
preparation. Full arbitrary-snapshot phase/QC/send/delivery/journal/current/crash/
unknown/torn/repair/physicalWAL, concrete bounded codecs/hash/exporter/resources,
decimal compatibility, contract freeze, clean offline reproduction and independent
review remain mandatory.
Source-bound semantics: sha256:5b3b0b0ddc51fe478ab47bf096d240d16d74f6a7c35e674cfa03ab8f6f7b4973.


## 27 September 2026 — complete current-state and profile artifact projection

T044/T048/T053/T054/T056/T057. NO_GO. Scope
formal/proposals/native-state-projection-proof.md; evidence
formal/proposals/evidence/native-state-projection.json. NativeStateArtifacts
computes all draft PROFILE fields from original coefficients/domain order,
actual checked accumulator width and an explicit quantum input. Complete
MODEL/OPTIMIZER encodings retain original current values and the actual computed
schema reference. Native value hashes and draft artifact hashes remain distinct.

NativeStateProjection checks the full original policy APPLY-profile list, exact
selected original profile ID and accumulator proof edge, then composes the
original checked pointer history with complete NativePlanProjection graph.
Current checkpoint must match the preceding preparation parent, current height
must be earlier and original schema must match. These are explicit projection
restrictions. Both complete vector lengths match source schema coordinates.
All three artifacts are packed canonically, bounded to4MiB and checked against
actual store bytes/hash/length/decoded typed payloads. General exact-byte/Resolves
theorems and a named common HashAdapter current-value relation are proved.
The raw run API executes original NativeVectorContext.bind before construction.

UnitSource is a named UNRESOLVED primitive, returning only quantum for complete
original context/APC/profile/proof/current-pointer identity. Missing metadata
rejects; no whole translated profile/state or arithmetic approval is supplied.
Presence is not authentication or configured-profile authority. A general
theorem proves no function of the original profile alone can return two distinct
quantum projections; two positive numeric-profile cases at1/4 and1/2 expose
that ambiguity. Original native State/DomainAggregate/profile formats lack the
unit field. No default quantum or fixture value fills this source gap.

Three modules:19 general helper theorems/13 definitions/five structures/one alias,
16 kernel/component cases/seven definitions. All61 explicit names audited with
only propext/Quot.sound/Classical.choice. Full Lean1150jobs,three fresh kernels,
731tooling/38oracle,33legal112illegal,Ruff/format/consistency,387generatedfiles
byte-exact PASS. All final source/evidence raw hashes match Git blobs.
21TLA/schema/runtime/147nativewitnesses unchanged;145legacyonlysemanticsID.
No freshTLC/newproductionmutants. Mandatory44/45/nativeArithmeticRecoveryRefines
missing;Phase0unfrozen;make absent/noaggregateformal-check. All3demosHTTP200without
restart/frozenrefsunchanged.

Examples reuse a separately constructed prior numeric original profile and
synthetic vectors[19,-19]/[2,-2]. Three short complete JSON encodings use invalid
short schema IDs and match independent Python canonical JSON. No positive full
raw history/preparation/store, native run, authenticated UnitSource or full
Binding instance is claimed. Prior layout4096 and extra fraction/current-height/
schema checks retain bounded representation scope, not native restrictions.
Resource-heavy draft generic proof attempts were discarded; local irreducibility
of checker definitions, separate assembly and explicit branch proofs avoid deep
native graph reduction. The final generic projection compiles without an
increased heartbeat limit. Only final evidence counts.

Next: construct the complete authority root and source-derived Inputs/Binding
from the computed graph/state/profile, deriving Complete/Walk relations instead
of accepting a caller's whole translated authority or state equality. Keep
UnitSource/configured-profile and independent certificate/current/recovery trust
as named unresolved source boundaries; a conditional constructed Binding is not
nativeArithmeticRecoveryRefines. Investigate actual source configuration for
quantum and schema rather than inventing a contract or reusing later APPLY data.
Initial no-history snapshots, missing original008 proof/base/current captures,
native decimal -00/-01 compatibility, arbitrary phase/QC/send/delivery/journal/
current/crash/unknown/torn/repair/physicalWAL, bounded hash/codec/exporter/resources,
contract freeze, clean offline reproduction and independent review remain open.
Source-bound semantics: sha256:c16981d6c0b5e90838aaa5f4b3649ffdbb10f54335cc0a3d262d111a003e491d.


## 27 September 2026 — computed authority graph and conditional Binding

T044/T048/T053/T054/T056/T057. NO_GO. Scope
formal/proposals/native-binding-construction-proof.md; evidence
formal/proposals/evidence/native-binding-construction.json.
NativeGraphClosure executes the actual store/decoder at every reference and
recurses over all decoded children in exact field/list order. Successful finite
depth checks derive the inductive Complete relation and ordered paths. Missing
nodes, wrong bytes/kinds/lengths/edge types, noncanonical data and exhausted depth
reject. DAG sharing is supported; no finite approval table or caller Complete
proof defines the general relation. Depth bounds path length, not total work.

NativeAuthorityProjection computes all eight artifact references and complete
source context into the canonical AUTHORITY payload, including its full parents
object. Original round/epoch/parent byte identity and identifier checks retain
the source context. Actual root bytes/hash/length/decoded payload and full
recursive closure are checked. The raw API composes NativeStateProjection.run
on original preparation/history; no whole translated authority is accepted.

NativeBindingConstruction derives a pre-aggregate Anchor and constructs Binding
from those successful executions, deriving Complete and model/optimizer/profile
Walk paths at exact positions. Original values, bytes, schema and quantum remain
the computed artifacts. Native current value hashes follow under the named
common HashAdapter, mandatory for all Binding construction entry points.
PARAMETER composition uses the existing original/draft
arithmetic verifier with this constructed Binding and exact source leaf coverage.

This remains CONDITIONAL: Premises independently require native anchor/recovery
and ISC/EC/APC certificate authentication. No instance of them is created or
proved. A computed self-consistent root is not native pre-state custody or unit
provenance. UnitSource/configured profile/initial/current authority remain OPEN.
Aggregate is explicitly none; certified APPLY aggregate, full raw original/draft
Inputs/execution and nativeArithmeticRecoveryRefines are not established.

Four modules:26 general helper theorems/12 definitions/one premise structure;
27 kernel/component proofs/29 small fixture definitions. All95 explicit names
axiom-audited with only propext/Quot.sound/Classical.choice. Full Lean1154jobs,
four fresh kernels,733tooling/38oracle,33legal112illegal,Ruff/format/consistency,
387generatedfiles byte-exact PASS. All final source/evidence raw hashes match
committed Git blobs. Only final frozen-source/logs count. Small draft elaboration
errors were corrected without changing runtime or increasing heartbeat limits.
One interrupted draft final-run was superseded after self-review made the common
HashAdapter mandatory; only the subsequent complete stable-source run counts.

Examples use a synthetic one-byte codec to check a shared ten-artifact graph and
missing/changed inputs. It is not canonical JSON, SHA or native authentication.
Separate short canonical context/reference proofs compose full authority bytes
and agree with independent Python JSON. No large full native history reduction,
new native capture or positive authenticated native/draft execution is claimed.
21TLA/schema/runtime/147nativewitnesses unchanged;145legacyonlysemanticsID.
No freshTLC/newproductionmutants. Mandatory44/45/nativeArithmeticRecoveryRefines
missing;Phase0unfrozen;make absent/noaggregateformal-check. All3demosHTTP200without
restart/frozenrefsunchanged. Native -00/-01 compatibility FAIL remains.

Next: extend the constructed source Binding through actual certified aggregate
and APPLY computation, deriving the aggregate root/full ParameterShardQC corpus
instead of accepting supplied expected bodies. Preserve pre-aggregate PARAMETER
admission and exact original schema/profile/context/denominator/quantum/parent
and current vectors. Independently authenticate source UnitSource/configuration/
native root/current/certificates; do not turn named premises into constant true.
Existing original008 proof/base/current captures stay absent. Construct an actual
original/draft Inputs instance only where source evidence suffices. Keep unknown
observations incomplete and join complete journals/arbitrary-snapshot phase/QC/
send/delivery/current/crash/torn/repair/physicalWAL. Concrete bounded codecs/hash/
exporter/resources, native compatibility, contract freeze, clean offline
reproduction and independent review remain mandatory. No helper discharges the
full nativeArithmeticRecoveryRefines by renaming or assuming its conclusion.
Source-bound semantics: sha256:a34c0502332c36f3ccfe15f5dad25818aec483cc7e117a31e6cd17a6da088f76.


## 28 September 2026 — original certified corpus and conditional aggregate/APPLY

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
Evidence: `formal/proposals/evidence/native-aggregate-binding.json`.

NativeCertifiedCorpus loads the actual original aggregate section, including
bounded original PARAMETER certificates, selects an actually finalized ROOT by
its original ID, and executes deriveParameterCorpus on the computed authority.
A strict ordered zipper checks every original finalized shard against its own
fresh NativeVectorJoin computation. The original shard ordinal is selected from
the original layout. Each leaf retains the full source Q list, domain/shard,
ISC/EC/PLAN/context, denominator, exact numerator vector and canonical decimal
spelling. The computed body also equals the corresponding computed corpus body,
including all projected Q identifiers. Previously checked proposed PARAMETER
bodies are not used as evidence for finalized QCs.

All original root keys and leaves are retained in order. Missing/extra records
reject by length; changed keys, parents, values and leaf sets reject at their
corresponding checks. Source native leaves are sorted only as required by the
original certificate encoding; source contribution order remains intact. Draft
domain/shard enumeration must equal original ROOT key order: this is a projection
restriction, not a new native admission rule. Exact decimal spelling is stronger
than the old native negative-zero/leading-zero behavior. No native repair occurs.

NativeAggregateBinding constructs the entire AGGREGATE_PROJECTION canonical JSON
from the computed authority ID and all computed PARAMETER bodies. Store bytes,
length, hash, canonical decoding and exact payload must agree. It constructs
aggregate Complete (inline bodies have no recursive payload edges) and extends
Binding to an Anchor containing both authority and aggregate. The original
authority bytes, model, optimizer, profile and paths are retained unchanged.
AUTHORITY has no aggregate edge, avoiding circular hashes. The older PARAMETER
entry point still requires no later aggregate or APPLY.

The extension requires the SAME HashAdapter and separate authentication of the
new Anchor/recovery and projected certificate. An explicit CertificateAuthority
premise relates the entire original ROOT source and QC ID to the exact projected
artifact. There is no instance of this premise and no inference of signatures or
custody from successful hashing. Original native QC IDs and projected artifact
IDs have different preimages. Earlier anchor authentication does not authenticate
the extended anchor. UnitSource and configured profile provenance remain OPEN.

The APPLY checker reloads the actual original APPLY section, selects the original
proposal, and compares its entire selected ROOT certificate plus original ID and
selected profile ID. A general theorem derives equality of the full original
ROOT source representations using their checked parsers, not hash equality.
NativeApplyResult.check executes all certified-body loading, conversions, mixture
and optimizer calculations and compares exact candidate decimal values and native
model/optimizer/parent hashes. fromSource composes the earlier raw preparation,
current-history, source graph and authority construction, corpus checking,
aggregate extension and APPLY candidate checking with the same selected original
profile. All trust and quantum premises remain explicit.

This is a conditional executable composition, not an authenticated native run or
full admission/recovery theorem. No positive full raw original/draft instance is
manufactured; original008 proof/base/current captures remain absent. Tests reuse
existing original certificate components and separately check small mathematical
body mutations and complete JSON bytes. Synthetic short encodings do not prove
native signatures, codec/hash implementations or current-state custody.

Remaining: instantiate independently authenticated original artifacts/configuration/
units/current, join arbitrary initial snapshots, full historical journal and actual
phase/QC/send/delivery/current/crash/unknown/torn/repair/physical-WAL relations,
prove concrete decoder/hash/exporter resource bounds, resolve native compatibility,
freeze the amendment, reproduce clean offline and obtain independent review.
Known computed outputs confer no phase role, send authority, quorum or current
advance. No nativeArithmeticRecoveryRefines, local PASS, guard change or GO.

Validation: full Lean1157jobs, three fresh kernels,85 explicit names axiom-audited;735tooling/38oracle,33legal112illegal,Ruff/format/consistency and387generatedfiles byte-exact PASS. Twenty-seven general helpers,27 kernel/component cases,26definitions,5structures. Only final frozen-source results count; draft elaboration/decide reductions superseded without raised heartbeat limits.21TLA/schema/runtime/147nativewitnesses unchanged;145legacyonlysemanticsID. No freshTLC/newmutants. Mandatory44/45/nativeArithmeticRecoveryRefines missing;Phase0unfrozen;make absent/noaggregateformal-check. All3demosHTTP200withoutrestart/frozenrefsunchanged. Source-bound semantics: sha256:edf27bc2263e87f57f2c7742ea8ec0ad23af736a04f1438d1691c58f23742f58.


## 28 September 2026 — source-bound finalized APPLY and current recovery

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
Evidence: `formal/proposals/evidence/native-certified-current.json`.

NativeCertifiedCurrent reuses the actual original complete APPLY snapshot and
selects a finalized ApplyQC using the original CurrentPointerCommand QC ID.
It recomputes NativeApply from the source-derived Binding and compares the entire
original ROOT certificate plus ROOT ID and the exact source-selected profile.
The prior certified PARAMETER corpus checker supplies every original finalized
leaf with full Q coverage, exact parents, values and decimal spelling. A general
lemma derives equality of the original ROOT source representations from actual
checked decoders. Whole-body translations or caller arithmetic approvals are
not inputs. fromSource composes the constructed raw authority, original current
history, certified corpus and computed aggregate under the common HashAdapter.
Both raw-source entry points take the complete pre-advance current tuple from
that executed history, including its original QC and height; they do not accept
an independently supplied current tuple with merely matching numerical hashes.
Both also refuse a retained torn suffix in that preceding history. A prior
successful value reconstruction alone does not authorize a new pointer advance.

The checker retains the full candidate model/optimizer decimal vectors, exact
native output and parent hashes, canonical original command/QC hash preimages
and the selected finalized QC ID. Draft artifact IDs do not replace native
certificate/command IDs. Fresh current advancement checks both parent model and
optimizer against the admitted anchor, plus the original CAS/height decision.
The exact original five-field pointer-WAL record is derived from that preparation.
Successful record replay reaches the computed next tuple; exact retry uses the
historical preparation and allocates no second record. It does not incorrectly
apply first-advance freshness to an already advanced pointer.

The observation API parses the actual pointer-WAL bytes and compares the complete
observed record list to the one selected next record. It rejects missing, extra,
duplicated or substituted records, wrong parent/height and corrupt checksums.
Unknown remains incomplete. A torn suffix is preserved as evidence; the separate
completeObservation/resumable gate rejects it. This restricted single-next-record
API is not an arbitrary journal-prefix recovery proof, physical fsync/observation
authentication, or authorization to truncate or resume native writes. The earlier
native WAL scanner still accepts rehashed uncertified IDs; its counterexample is
retained and the added exact-record comparison rejects that substituted record.

Tests reuse original008 certificate/command components and the already retained
synthetic pointer-WAL fixture with finite SHA samples. They are not a new full
source-graph execution, native capture, authenticated quorum or SHA proof.
The golden current tuple hash convention is independently checked in Python.
No missing original008 proof/base/current vectors are invented. Native decimal
compatibility and full signed-boundary differences remain unresolved.

All Binding anchor/recovery/certificate premises, UnitSource/configured profile,
initial/current custody, cryptographic signer authority and physical observation
remain independently required. Reading finalized membership and checking signer
shape does not authenticate those premises. The fresh/current/recovery wrappers
are conditional formal proposal APIs only. Native runtime and arithmetic guards
are unchanged. No local acceptance PASS or nativeArithmeticRecoveryRefines.

Next: source-bound original arithmetic vote metadata/admission and pre-WAL record
composition with the mixed journal. Full phase/QC/send/delivery/current/crash,
unknown/torn/repair and arbitrary initial snapshots, bounded concrete codecs/hash/
exporter resources, compatibility, amendment freeze, clean offline reproduction
and independent review remain mandatory before exact merged Formal GO.

Validation: Full Lean1159jobs, two fresh kernels,72 explicit declarations axiom-audited;737tooling/38oracle,33legal112illegal,Ruff/format/consistency and387generatedfiles byte-exact PASS.34general helpers,27kernel/component cases,11definitions. Only final frozen-source results count; an earlier refresh-only run was superseded after self-review added the prior-history torn-suffix guard.21TLA/schema/runtime/147nativewitnesses unchanged;145legacyonlysemanticsID. No freshTLC/newmutants. Mandatory44/45/nativeArithmeticRecoveryRefines missing;Phase0unfrozen;make absent/noaggregateformal-check. All3demosHTTP200withoutrestart/frozenrefsunchanged. Source-bound semantics: sha256:79d78fdf8c939d1888b5ef575447afadcedda5b1fdb598851fd8d6c215a607f3.


## 28 September 2026 — original arithmetic vote selection and mixed prefix

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
Evidence: `formal/proposals/evidence/native-arithmetic-vote.json`.

NativeArithmeticVote defines a separate candidate arithmetic relation. It reloads
the original complete policy/snapshot, executes the original first-match candidate
selection and parent/body authority checks, and checks validator, epoch, round,
height, view, context, body identity, checkpoint, global position, readiness or
recovery, invalidation, phase, failure requests and the strict hard deadline.
The unchanged NativeSelectedVote guard still rejects both arithmetic actions;
an explicit theorem retains that rejection even when candidate selection passes.
The small Checks predicate alone is not arithmetic admission.

PARAMETER selects its actual original body from that same checked snapshot,
derives the shard ordinal from the source plan, and executes NativeVectorAuthority
against actual source Q rows and the constructed Binding. Complete common fields,
vote context, original body ID, ordered leaf coverage and canonical decimal values
are compared. Equality of both original source representations is derived from
their checked decoders, not supplied by a caller. The original body hash has its
actual native body preimage; the projected artifact hash is a different domain.
No later aggregate or APPLY result is required for this path.

APPLY recomputes NativeApply using the earlier complete finalized PARAMETER
corpus and aggregate relation, checking full original ROOT/profile identity and
all output values and native hashes. The original selected candidate ID and
ROOT-derived vote context are retained. Raw source wrappers reuse the actual
constructed authority and selected original profile with a common HashAdapter.
They reject a torn preceding current-pointer history. Binding, aggregate,
UnitSource/configured-profile and source availability/custody premises remain
independent; no cryptographic authority is inferred by selection or arithmetic.

NativeArithmeticPrefix scans the complete supplied original WAL prefix and
executes the existing guarded mixed command/vote replay from its supplied initial
snapshot. It checks that the resulting entire canonical state equals the source
preparation state; the source-loading proof binds exactly the same policy bytes.
It derives time, invalidation and global sequence from that executed prefix,
rejects an existing vote key, parses the exact next original DRW1 entry and DRC1
VOTE, binds the policy record hash, executes candidate arithmetic and constructs
the original receipt container. Every previous cached vote has an actual executed
position, canonical command/receipt/parents and suffix; a matching count alone
is insufficient. Unknown, corrupt, reordered or torn prefix observations do not
qualify. The next VOTE position counts both previous commands and votes.

This is deliberately ONE candidate arithmetic record after an original guarded
prefix. That prefix cannot already contain arithmetic votes. Command invalidation
is retained and is not cleared to manufacture an eligible history. The selected
next bytes are checked data, not evidence they were appended, fsynced or exposed.
The receipt is a mathematical container, not a returned native admission receipt.
Initial snapshots, source-loading facts and physical observations still require
independent authentication. No complete joined raw instance is asserted.

The original complete VOTE is retained, including signature ID, view, sequence
and historical native semantic ID. These fields cannot be dropped when joining
ArithmeticBinding.NativePrepared: its distinct draft JSON envelope omits several
of them and its diagnostic sequence counts only draft votes. That lossless
metadata/pre-WAL bridge, actual repeated arithmetic mixed histories, public
durable-set correspondence, phase/send/delivery/QC/current/crash/unknown/repair
and physical persist-before-expose remain OPEN. This stage neither constructs
an authenticated VoteMetadata instance nor proves nativeArithmeticRecoveryRefines.

Small kernel cases reuse original VOTE records and existing mixed journal/scanner
components, with explicit synthetic phases/times and finite SHA adapters. There
is no new fixture graph/native capture, signature proof, full native admission,
runtime edit or guard removal. Native decimal -00/-01 and full-width compatibility,
bounded concrete codec/hash/exporter resources, amendment freeze, clean offline
reproduction and independent review remain required before exact merged GO.

Validation: Full Lean1162jobs, three fresh kernels,78explicit declarations axiom-audited;740tooling/38oracle,33legal112illegal,Ruff/format/consistency and387generatedfiles byte-exact PASS.30general helpers,29kernel/component cases,13definitions,5structures/1inductive. No new joined source-graph example/native capture; original VOTE and mixed replay components reused separately. Only final frozen-source evidence counts.21TLA/schema/runtime/147nativewitnesses unchanged;145legacyonlysemanticsID. No freshTLC/newmutants. Mandatory44/45/nativeArithmeticRecoveryRefines missing;Phase0unfrozen;make absent/noaggregateformal-check. All3demosHTTP200withoutrestart/frozenrefsunchanged. Source-bound semantics: sha256:b62d18c1591d3cd6b0131fb0ba6f9a190d5e83ee9837dadc595e04e2a32064b1.


## 28 September 2026 — lossless source-derived vote metadata

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
Evidence: `formal/proposals/evidence/native-vote-metadata.json`.

NativeVoteMetadata executes the prior original PARAMETER/APPLY selection and
source computation, then constructs the draft VoteMetadata and ExpectedNativeVote
from that actual VoteSource. No whole translated body, expected result, approval
table or authenticated metadata instance is supplied or invented. PARAMETER uses
the actual DerivedParameter, its exact domain/shard, APC projection and original
plan parent; APPLY uses actual NativeApply, its certified aggregate projection
and original ROOT parent. The complete body encoders operate on these results.
Original native body hash preimages and projected artifact hash preimages are
retained separately. They are different representations, not byte-equal IDs.

The actor and vote context have checked ASCII roundtrips. The original native
parent is decoded using the strict digest decoder, checked to be 32 bytes, and
re-encoded to the exact original 71-byte sha256 spelling. No finite alias map is
used. All six anchor context fields are compared with the original source
context, including checked original round/epoch/checkpoint byte spellings and
height/view. Source parameter context equality is checked by ExpectedNativeVote;
the APPLY context retains the original ROOT-derived preimage relation even though
the old low-level VoteSource.apply context predicate alone accepts any string.

The metadata time is the actual supplied event tick. Its validator flag computes
both local-validator equality and original policy membership. This is structural
membership, not signature verification or an authenticated committee export.
The conservative candidate recovered flag requires ready=true, recovery=false
and invalidated=false. It is explicitly not a proved interpretation of an
authenticated production event. Original selection already checks the actual
phase, deadline, invalidation and candidate parent chain. Existing runtime and
original guarded reference checker remain unchanged and reject arithmetic votes.

The result retains the complete original typed VOTE, every original parent slot,
and the separate draft envelope. The mixed-prefix wrapper additionally retains
the exact original DRW1 entry, signature, receipt container and original arithmetic
objects. It executes the prior whole original guarded prefix check, preserving
global command-plus-vote position and the exact original VOTE/DRW1 re-encodings.
The historical native semantics ID is not rewritten to the new draft semantics.
No old diagnostic arithmetic record at sequences5/6/8 is changed.

General rejection theorems show that these recovery-scan results cannot produce
NativePrepared even if a caller separately supplies authenticated metadata: the
actual prefix facts have recovery=true and ready=false, so recovered remains
false and NativeFresh fails. No mode/flag is flipped to manufacture eligibility.
The original prefix still cannot contain previous arithmetic votes. Connecting
an actually completed recovery/live event and the entire draft/public durable
set, rather than a matching count or caller-created state, remains required.
Draft NativePrepared sequences count draft votes; original WAL positions count
commands plus votes. This stage deliberately does not identify these sequences
or assert a complete pre-WAL bridge. First preparation is separate from retry.

Small kernel cases reuse the original native vote and parent components, plus
separately synthetic flags/policies. They check parent digest spellings, ASCII
representation, readiness/invalidation/membership and demonstrate that the
metadata alone loses signature/view/global position. The complete result retains
those original fields. These are not a new joined raw source-graph execution,
native capture, physical write or authenticated exporter/signature instance.

Independent Binding/aggregate/UnitSource/profile/current/source custody premises
remain. Unknown/torn/corrupt observations retain prior rejection; no absent-cut
exhaustiveness, repair/truncation permission, append/fsync/exposure, network/QC
power or recovery completion follows. Repeated arithmetic mixed histories,
arbitrary initial snapshots, full phase/send/delivery/current/crash/repair,
concrete bounded codec/hash/exporter resources, native -00/-01 and full-width
compatibility, amendment freeze, clean offline reproduction and independent
review remain open. This layer does not prove nativeArithmeticRecoveryRefines.

Validation: Full Lean1164jobs, two fresh kernels,68explicit declarations axiom-audited;743tooling/38oracle,33legal112illegal,Ruff/format/consistency and387generatedfiles byte-exact PASS.23general helpers,25kernel/component cases,15definitions/5structures. Small original wire/parent and separately synthetic readiness/membership cases, no new joined source-graph example/native capture. Only final frozen-source evidence counts.21TLA/schema/runtime/147nativewitnesses unchanged;145legacyonlysemanticsID. No freshTLC/newmutants. Mandatory44/45/nativeArithmeticRecoveryRefines missing;Phase0unfrozen;make absent/noaggregateformal-check. All3demosHTTP200withoutrestart/frozenrefsunchanged. Source-bound semantics: sha256:4cc37ee1aa7302ff7fd562b9b6bcc721adfe0fc646bace47e15e8bcbf4efd430.


## 28 September 2026 — repeated source-checked candidate arithmetic journal

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
Evidence: `formal/proposals/evidence/native-arithmetic-history.json`.

NativeArithmeticJournal defines a separate candidate mixed step. Each arithmetic
input supplies actual primitive source bytes, Q inputs/permission, application
root/profile where relevant, and an independently premised Binding. Its Source
contains a proof that NativeVectorContext.bind actually loads those inputs.
The step compares the entire policy bytes and preceding canonical state bytes
with that source. It then executes NativeArithmeticPrefix.compute, including
original whole-policy selection, parent/body identity, phase/deadline checks and
the actual DerivedParameter or NativeApply computation, and derives the complete
NativeVoteMetadata image. No arithmetic admission callback, Boolean approval
table, whole body translation or arbitrary expected-state equality is supplied.
The loader equality is the actual existing executable graph relation, not an
external assertion that two translated states match. Independent Binding,
HashAdapter, aggregate, source availability and custody premises remain explicit.

The original VOTE, all original parent slots and exact receipt/frame/context
identity accompany each checked arithmetic result. The candidate cache uses the
original native Stored representation; the distinct projected image and source
are retained at the executed step, not mistaken for an original Stored body.
Every record checks the original global sequence, exact policy ID, vote key
freshness, empty vote state/effects and snapshotGuard on the actual preceding
state. Commands and non-arithmetic votes execute unchanged NativeConfigReplay
whole steps. An arithmetic input without a source remains subject to its
original rejection guard. An extra source on a command rejects. Invalidation is
monotone; supplying another Source cannot reset it or invent an authority refresh.
The original guarded checker and production runtime are unchanged.

NativeArithmeticHistory folds this step over an arbitrary finite input list.
Its closed History records only executed steps. General theorems derive sequence,
command-plus-vote counts, unique request/vote keys, monotone time/invalidation,
and actual executable pre/step/suffix provenance for every stored vote. Every
arithmetic input has its actual checked source computation at its exact prefix
position; the API has no first-arithmetic-only restriction. This is a conditional
general relation, not a claim that any desired sequence or phase is reachable.
Recovery starts from complete original prepareWhole and initialMachine, checks
full snapshot coverage and returns only a completely executed history. Exact
retry uses the existing read-only historical cache lookup and preserves its
original position rather than re-running current first-vote admission.

Snapshot position zero has an additional explicit candidate restriction:
snapshot.state must equal the initial canonical state bytes. The existing
NativeCommandReplay.initialMachine marks zero matched without comparing those
bytes itself. This new check is not a change to, or an equivalence claim about,
the original guarded replay/runtime contract. Positive snapshots have an actual
prefix/step/suffix witness with the matching full state, not just a sequence.

The byte front end requires a known observation, complete NativeWalScan.check,
no torn flag or tail, and an exact-length positional alignment with sources.
Both complete entry and source lists are retained; zip truncation is impossible.
Original checked frame partitions and global positions are retained unchanged.
UNKNOWN rejects even with an empty source list. Corrupt/incomplete observations
cannot be interpreted as an empty durable journal or authorize repair/truncation.
The caller's observation and initial-state physical provenance are still open.

Kernel cases lift the previously checked original ISC1/freeze2 execution through
the new no-source branch, using its component lemmas and an explicit adapter-SHA
equality. Other small cases cover source shape/position, invalidation, reorder,
duplicate, unknown and zero-snapshot mismatch. There is no new successful joined
multi-arithmetic raw fixture, authenticated source capture or physical native
write. Original diagnostic arithmetic bytes/sequences5/6/8 and historical cc98
semantics stay unchanged. Python checks use the already retained original mixed
WAL observation and reject altered order, missing prefix, duplicate, torn and
corrupt frames; these are scanner checks, not an arithmetic-admission oracle.

Recovery-scan images still have ready=false/recovery=true/recovered=false and
cannot pass prepareNativeFirst, even with a separately supplied authentication
premise. No NativeVoteTrust instance or live-ready completion is invented. Full
prior draft/public durable contents, original mixed-position versus draft-vote
position correspondence, authenticated completed recovery/live events and the
lossless NativePrepared bridge remain open. This typed finite replay does not
prove arbitrary production snapshots, full phase/send/delivery/QC/current,
crash/unknown/torn/repair, physical persist-before-expose or absence/exposure
semantics. Concrete bounded codec/hash/exporter/full graph resources, native
decimal -00/-01 and FULL_SIGNED_INT64 compatibility, missing original008 captures,
amendment freeze, clean offline reproduction and independent review remain.
This layer does not prove nativeArithmeticRecoveryRefines or authorize native
guard changes, local acceptance PASS, BenchmarkResultQC or formal GO.

Validation: Full Lean1167jobs, three fresh kernels,87explicit declarations axiom-audited;746tooling/38oracle,33legal112illegal,Ruff/format/consistency and387generatedfiles byte-exact PASS.41general helpers,25kernel/component cases,14definitions/6structures/1inductive. Existing original ISC1/freeze2 execution lifted with explicit adapter-SHA equality; no new successful joined multi-arithmetic source graph/native capture. Only final frozen-source evidence counts.21TLA/schema/runtime/147nativewitnesses unchanged;145legacyonlysemanticsID. No freshTLC/newmutants. Mandatory44/45/nativeArithmeticRecoveryRefines missing;Phase0unfrozen;make absent/noaggregateformal-check. All3demosHTTP200withoutrestart/frozenrefsunchanged. Source-bound semantics: sha256:09db847aeb0e9f77e93b2e74595a53bfc47f9774ba994e73ec87db409c751e67.


## 28 September 2026 — complete source-bearing native vote cache

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
Evidence: `formal/proposals/evidence/native-vote-cache.json`.

NativeVoteCache.capture executes the previous candidate mixed-journal step and
retains one source-bearing row for every ordinary or arithmetic vote. Ordinary
rows retain the actual NativeSelectedVote.Checked, its complete checked original
snapshot, ordered candidates and exact selected parents. Arithmetic rows retain
the actual Source, NativeVectorContext.bind provenance, computed PARAMETER/APPLY
result and NativeVoteMetadata image. Both retain the entire original WAL entry,
preceding canonical state and a separate all-vote ordinal. The ordinary candidate
body ID is not itself a public body; the original typed snapshot supplies its
primitive artifacts. No caller-supplied translated body or approval table is used.

General soundness AND completeness show this capture has exactly the same
successful candidate steps and final native machine as NativeArithmeticJournal.
Its complete native cache extension is the ordered map of all retained rows,
not merely a membership or count assertion. Original VOTE frames, signatures,
semantics, context, parents and receipt/global sequences are preserved. Strict
lookup accepts only one matching original validator/epoch/context key; missing
and ambiguous keys cannot become first-match authority. Lookup alone grants no
source authority: callers must retain execution/recovery provenance.

NativeCacheHistory extends that relation to arbitrary finite runs, typed recovery
and complete observed-byte recovery in both directions. Commands execute through
the same original checker and remain part of the actual input execution. Every
row has an executable original prefix, its actual capture/RowSource and suffix.
Recovery derives exact equality of the ENTIRE final native vote cache with the
ordered row projection. All-vote ordinals are exactly 1 through the vote count.
At each actual row position, original WAL sequence equals its all-vote ordinal
plus the number of preceding commands. This is not per-actor public numbering,
and is not an arithmetic-only renumbering. Original sequence bytes are unchanged.
Known complete scanning, exact-length Source alignment, complete policy startup,
snapshot checks and the earlier stronger snapshot-zero identity check are reused.
This proves equivalence to the previous candidate, not the production runtime.

NativeCacheProjection re-executes deriveExpectedNativeVote from each retained
arithmetic Source and original scan metadata. It checks complete data, envelope
and effect equality with the actually computed image, then encodes a diagnostic
receipt at the separate all-vote ordinal. The result is RecoveryKernel.Record;
these newly encoded diagnostic bytes are NOT original DVREC/WAL receipts,
physical persistence evidence or an authenticated NativeReplay.Resolved value.
The complete list traversal has a proved pairwise relation in both directions,
retains every row and derives exact ordinal order. It cannot filter out an
unsupported row or silently keep a successful subset. Ordinary rows currently
have no public-body projection and therefore reject the ENTIRE projection,
including when they occur after arithmetic rows. UNKNOWN also rejects.

The low-level row and projection constructors are mathematical data operations;
only the executed cache/recovery relation establishes source provenance. No
NativeVoteTrust instance, arbitrary env.input map, NativePrepared, ready event,
first-vote freshness or completed-recovery fact is manufactured. In particular,
executed scan arithmetic still has recovered=false. A diagnostic projection
cannot change this fact or re-admit a historical retry at the current state.

Kernel cases reuse the actual prior ISC1/freeze2 components under the same named
adapter-SHA equality, show exact native cache/parents/receipt and the different
global/vote counters, and reject duplicate/altered-ordinal lookups and ordinary
rows anywhere in a projected list. There is no new successful nonempty joined
arithmetic projection, full raw multi-arithmetic source capture or native write.
Python cases inspect the retained original four-entry WAL observation, its one
vote and three commands, and demonstrate codec-valid changed bytes with the same
cache key but different original vote identity. They do not claim admission of
those changed bytes. Original diagnostic sequences5/6/8 and147native witnesses
remain unchanged; no fixture expansion or new physical custody is asserted.

This closes the complete native-cache retention and all-vote/mixed-position
relation. Full public/draft durable equality remains OPEN: typed non-arithmetic
public body/context/parent projections, all actors, public sequence abstraction,
source/configuration/alias authority and authenticated live/recovery resolution
are not supplied by this layer. MetadataTrust, IndependentBinding, UnitSource,
initial/current/export/signature/custody premises remain explicit. Missing
original008 captures remain missing. Full phase/send/delivery/QC/current,
crash/unknown/torn/repair, arbitrary production snapshots, physical
persist-before-expose, concrete bounded codec/hash/exporter/full-graph resources,
native -00/-01/FULL_SIGNED_INT64 compatibility, contract freeze, clean offline
reproduction and independent review remain required. This layer does not prove
nativeArithmeticRecoveryRefines or authorize runtime/guard changes, local PASS,
BenchmarkResultQC or formal GO.

Validation: Full Lean1171jobs, four fresh kernels,80explicit declarations axiom-audited;749tooling/38oracle,33legal112illegal,Ruff/format/consistency and387generatedfiles byte-exact PASS.40general helpers,23kernel/component cases,13definitions/3structures/1inductive. Existing original ISC1/freeze2 execution retained with explicit adapter-SHA equality; no new successful nonempty joined arithmetic projection or native capture. Only final frozen-source evidence counts.21TLA/schema/runtime/147nativewitnesses unchanged;145legacyonlysemanticsID. No freshTLC/newmutants. Mandatory44/45/nativeArithmeticRecoveryRefines missing;Phase0unfrozen;make absent/noaggregateformal-check. All3demosHTTP200withoutrestart/frozenrefsunchanged. Source-bound semantics: sha256:15e2fd2d86b7eff77a228a7f6c311f0831af4c5ca456bcddaa5e5964d3821f45.


## 28 September 2026 — original CONFIG/ISC public vote projection

Tasks T044/T048/T053/T054/T056/T057; Feature000 amendment 0001. This is
conditional early-vote body construction at the original historical state,
not complete public/native recovery, local acceptance or Formal GO.

`NativeEarlySource` executes `NativeSelectedVote.fromBytes` on the original
policy, preceding state and VOTE bytes with the actual replay facts. Existing
whole snapshot/candidate admission, exact original frame/state encoding,
validator/epoch/height/view/round/context/body/parents and sequence identity are
retained. CONFIG checks its selected kind, configured native ID and proposed
membership. ISC scans the entire original checked snapshot input list and
requires exactly one matching native body ID. It rechecks the original body
decoder, computed body ID, complete expected context and tuple validity. Missing
or ambiguous matches reject. Original tuple order/count and each complete
availability/commitment/domain/ticket tuple are retained. No later aggregate,
arithmetic Binding or successful PARAMETER/APPLY is required.

`PublicEarlyBody` loads independently keyed primitive names and close policy.
CONFIG builds the entire public envelope and ConfigContext; ConfigBodies in the
TLA model are configured model values, so the native configuration ID maps to a
primitive public name, not an invented decoded configuration. ISC builds all
five InputBody fields and the complete public envelope. Public canonicalRoot is
the complete entry set, not the native input-root hash. Each content-name key
includes native body ID, the whole native body/context/root/ordered tuple list,
and the entire selected tuple. Ticket names also retain the full native context.
Every source tuple becomes one entry; no filter, truncating zip or deduplication
can remove it. Sorting retains all values. Pairwise distinct projected entries
and complete canonicality are checked before comparing the entire candidate
vote, including validator, kind, context and body.

The metadata boundary is substantive: `Trust` must independently authenticate
the primitive names and close policy. The native ISC does not contain the
public content symbol or configured close policy. Fixture trust is deliberately
synthetic. Rejecting collapsed entries is a projection representability
restriction, not a change to native admission. Global alias injectivity,
configuration/policy agreement across every module, cryptographic/exporter
authentication and public availability/committee/QC semantics remain open.
Raw constructors and a caller-selected Checked value do not establish original
source authority; use Loaded and the historical source relation.

`PublicEarlyHistory` combines the source/body check with the original row's
preceding state and runtime facts. An ordinary captured row loads the same
original selected candidate by executable determinism. Successful candidate
recovery supplies an actual executed prefix, prior machine and capture step
for every ordinary row, with its original position. It does not re-admit a retry
against the later final state. This helper does not yet project the entire
cache or equate it with all public actor durable sets. NativeCacheProjection
still rejects every ordinary row; no resolver, NativeVoteTrust, NativePrepared,
ready event or recovered flag is manufactured.

Kernel cases reuse the actual pinned original ISC admission and native body hash
component proofs, then compose a complete ISC public vote with synthetic names.
CONFIG examples check shape/canonicality only, not new native CONFIG admission.
Small negatives cover actor, context, kind, body, omitted entries, close policy,
missing names/policy, duplicate public entries and complete source-key retention.
Python cross-source checks compare retained original native body/context hashes
and public TLA field inventories; a counterexample shows why a ticket/commitment
alias alone loses availability/domain/root distinctions. No new native run,
full-state trace, production mutant or independent attestation is claimed.

Remaining ordinary EC/APC/ROOT/VIEW/ABORT projections, shared alias/configuration
identity, all-actor sequence abstraction and complete public durable equality
are still required. Full phase/send/delivery/QC/current/crash/unknown/torn/repair
refinement, production snapshot equivalence, physical WAL/exposure authority,
bounded concrete codec/hash/exporter resources, native compatibility, contract
freeze, clean offline reproduction and independent review remain open. The
mandatory nativeArithmeticRecoveryRefines theorem remains missing; guard and
runtime are unchanged. UNKNOWN/incomplete cannot become complete through this
construction.

Reproduce with `lake --no-cache build DeltaReduce` in `formal/proofs`, fresh
individual compilation of the four named modules and AxiomAudit, tooling/oracle
tests, refinement fixtures and semantic regeneration. Evidence records the
precise final sources; source constructors alone are not formal authority.

Validation: Full Lean1175jobs, four fresh kernels,118explicit declarations axiom-audited;752tooling/38oracle,33legal112illegal,Ruff/format/consistency and387generatedfiles byte-exact PASS.43general helpers,29kernel/component cases,33definitions/11structures/2inductives. Existing original ISC admission/body-hash proofs compose with a complete public vote under synthetic metadata; CONFIG cases are public shape only. No new native execution. Only final frozen-source evidence counts.21TLA/schema/runtime/147nativewitnesses unchanged;145legacyonlysemanticsID. No freshTLC/newmutants. Mandatory44/45/nativeArithmeticRecoveryRefines missing;Phase0unfrozen;make absent/noaggregateformal-check. All3demosHTTP200withoutrestart/frozenrefsunchanged. Source-bound semantics: sha256:bbe328b655c19b0a9b2aedaed21217f9a39ef6095cfbffab434481b9f2de5d56.


## 28 September 2026 — original EC/APC public vote projection

Tasks T044/T048/T053/T054/T056/T057; Feature000 amendment 0001. These are
conditional source/body and historical composition proofs. They do not establish
full public/native recovery, native admission equivalence, local PASS or GO.

`NativePlanningSource` uniquely locates the selected EC/APC in the complete typed
snapshot of `NativeEarlySource.Loaded`. It derives the actual eligibility/plan
section checks from executed whole native admission, then derives the selected
original lineage computation and exact candidate parent/context authority.
Missing or ambiguous selection rejects. Proposed bodies and finalized parent
certificates retain their distinct identities. EC retains actual ISC/norm/seed
source witnesses; APC retains actual ISC/seed and finalized EC witnesses. The
ordered native accepted-ticket list equals both original plan bucket tickets
and original weight tickets, by the existing native coverage checks. No future
arithmetic Binding, supplied whole translated body or approval table is used.

`PublicPlanningBody` constructs all four EC fields, all five APC fields and
their complete public vote envelopes. EC context is the complete public ISC;
APC context is the complete public EC. The parent ISC includes all original
tuples through the prior primitive CONFIG/ISC metadata scheme. Actual EC
accepted flags determine members; actual APC weights determine APC members.
Every selected ticket is retained in order before canonical set construction.
Sorting preserves entries; collapsed aliases and noncanonical candidates reject.
APC public members are compared with EC public members without dropping entries.

Seed, norm-evidence and coefficient symbols are primitive metadata with an
explicit independent `Trust` boundary. Their keys retain full original seed
transcript including shares, norm evidence including original decimal bytes and
the full EC common data, and complete plan common data including weights,
buckets, accumulator, context, seed and EC data. The constructor does not accept
whole public records. These named metadata premises are not discharged here;
fixtures use synthetic trust. This is not a proof of valid public norm evidence,
seed randomness, coefficient safety, authentic signers or shared configuration.

Native lineage guards do not alone establish every TLA parent equality.
`SamePlanParents` explicitly checks native ISC QC ID AND the entire certificate,
plus seed ID AND the full seed transcript, against the EC's actual parents.
These are stronger projection restrictions, not newly claimed native admission
requirements. Public APC reuses the checked equal EC parent and seed. Original
source witnesses and complete payload equality remain required; equal opaque
IDs alone are insufficient. No public equality is assumed from hash injectivity.
The finalized native EC path also does not repeat the proposed-only norm/ISC
equality. Its original checks are preserved; public norm validity stays open.

`PublicPlanningHistory` reloads the original policy/state/VOTE with the actual
preceding machine facts, compares the full public candidate, and proves that an
ordinary captured row retains the same selected object and original bytes.
Prior executed-cache recovery already supplies the prefix and original position.
This does not yet project the entire ordered cache to all public durable sets;
the existing ordinaryBlocksAll diagnostic rejection remains unchanged. No
NativeReplay resolver, NativeVoteTrust, NativePrepared or ready/recovered event
is manufactured. UNKNOWN/incomplete is not converted into complete state.

Kernel cases reuse pinned individual EC/APC lineage and parent source components
with synthetic public names. They construct complete public EC/APC values,
check canonicality and field identity, reject changed parent/seed payloads,
retain full metadata keys, and reject ISC input at the planning source gate.
The coarse native parent-predicate countercheck deliberately lacks whole source
authority; it is not a counterexample to full native admission. There is no new
whole native EC/APC snapshot, joined recovery execution or physical capture.
Python checks use existing pinned observations and public TLA definitions; a
weight-change countercheck keeps ticket membership but changes native body/QC
identity. It grants no admission or signature authority.

ROOT/VIEW/ABORT, shared alias/configuration/primitive provenance, all-actor
sequence abstraction, complete public durable equality and actual phase/send/
delivery/QC/current/crash/unknown/torn/repair refinement remain required. So do
production snapshot equivalence, bounded concrete codec/hash/exporter resources,
physical WAL/exposure provenance, native compatibility, contract freeze, clean
offline reproduction and independent review. The mandatory
nativeArithmeticRecoveryRefines theorem remains missing. Runtime and guard are
unchanged. Reproduction uses the full Lean build, four fresh module kernels,
AxiomAudit, tooling/oracle tests, refinement fixtures and byte-exact regeneration.

Validation: Full Lean1179jobs, four fresh kernels,127explicit declarations axiom-audited;755tooling/38oracle,33legal112illegal,Ruff/format/consistency and387generatedfiles byte-exact PASS.41general helpers,30kernel/component cases,43definitions/11structures/2inductives. Original EC/APC lineage component proofs and small complete public bodies checked under synthetic metadata; no new whole EC/APC snapshot or joined native execution. Only final frozen-source evidence counts.21TLA/schema/runtime/147nativewitnesses unchanged;145legacyonlysemanticsID. No freshTLC/newmutants. Mandatory44/45/nativeArithmeticRecoveryRefines missing;Phase0unfrozen;make absent/noaggregateformal-check. All3demosHTTP200withoutrestart/frozenrefsunchanged. Source-bound semantics: sha256:e801438bb9ccadc9152a8db9660413f02f37b2a0365508675228ca5cf97f13fd.


## 28 September 2026 — original VIEW and empty-lineage ABORT projection

Tasks T044/T048/T053/T054/T056/T057; Feature000 amendment 0001. This is
conditional source/body and historical composition, not full recovery or GO.

`NativeFailureSource` reloads VIEW/ABORT selection from the actual complete
`NativeEarlySource.Loaded` snapshot. Executed whole admission derives the
original checked failure tail and exact candidate row, native body/context ID,
parent fields and action. Row checks retain original canonical payload and hash
preimage. VIEW retains the original timeout observation and exact native
round/height/fromView/toView/deadline. Actual source environment supplies native
phase, requests, deadline and runtime-fact guards, including the existing
recovery readiness bypass. Those facts and hashing remain explicit inputs;
this is not evidence of a physical timeout or completed recovery.

ABORT retains all seven original finalized lists from the exact policy through
the checked tail: configs, ISC, EC, APC, PARAMETER, ROOT and APPLY. The original
no-finalized-APPLY check remains. This proves exact list presence/absence in the
given checked source; it does not authenticate exporter completeness or physical
absence. Missing, unknown or corrupt source is not replaced by empty lists.

`PublicFailureBody` constructs the complete four-field VIEW_CHANGE body, its
round/fromView context and actor/kind/context/body envelope. Native integer
views/deadlines are preserved exactly and checked against explicit public model
limits. Both configured deadlines must also equal the original native policy;
range checking a body alone is insufficient. Public aliases, configuration
identity and authenticity still require the prior independent metadata boundary.
The public timeout observation is derived from the exact original observation;
no send, delivery, quorum or phase transition is inferred from membership.

ABORT support is deliberately restricted to empty ISC/EC/APC/PARAMETER/ROOT/APPLY
lists. Every nonempty downstream list rejects the whole projection, even when
all scalar fields match. This is an incomplete projection domain, not a new
native admission restriction or native/TLA equivalence claim. Within that domain
the full eight-field body and envelope are constructed, including all original
configs, six empty structured lineage sets, native view/deadline, round/epoch,
checkpoint and reason. Configs map one-for-one through primitive config names;
sorting preserves all values and collapsed aliases reject. No certificate ID
is cast to a structured public body. The checkpoint is primitive metadata keyed
by the entire original ABORT body, including native parent and all seven lists.
Its independent trust is unresolved and synthetic in examples. All six public
abort reasons are decoded by exact native ASCII equality; unknown and NO_ABORT
reject. Configured reason/state/current/alias agreement remains open.

`PublicFailureHistory` composes exact policy/state/VOTE bytes and prior runtime
facts with complete public candidate comparison. Captured ordinary row sources
retain the selected native object by executable determinism. Existing cache
provenance retains executed prefix and original position. This does not yet
translate the entire durable cache or establish per-actor sequence abstraction.
The ordinary diagnostic guard remains unchanged; no NativePrepared or
ready/recovered event is manufactured.

Kernel examples reuse pinned native failure candidate/tail components and small
public values, not a new positive whole selected VIEW/ABORT snapshot. Synthetic
names and checkpoint trust are explicit. Cases cover all six nonempty lineage
rejections, limits/deadlines, unsupported reasons, missing checkpoint, preserved
duplicate configs, changed envelopes and rejection of ISC at failure selection.
Python checks reuse pinned observations, independently check public field/reason
inventories, and verify that every omitted/changed native lineage list affects
the original canonical preimage. No new raw fixture or native execution occurs.

Nonempty ABORT lineage and ROOT need typed original certificate-body projection,
with arithmetic source/configuration agreement. Complete public durable equality,
all-actor sequences, authority/current/phase/send/delivery/QC/crash/unknown/repair,
physical persistence/export, production snapshots, concrete bounded resources,
native compatibility, contract freeze, offline reproduction and independent
review remain required. `nativeArithmeticRecoveryRefines` is still missing;
runtime/native guard remain unchanged and status remains NO_GO.

Validation: Full Lean1183jobs, four fresh kernels,117explicit declarations axiom-audited;758tooling/38oracle,33legal112illegal,Ruff/format/consistency and387generatedfiles byte-exact PASS.36general helpers,33kernel/component cases,37definitions/10structures/1inductive. Pinned original failure candidate/tail components and small public values use synthetic metadata; no new positive whole selected failure snapshot or joined native execution. ABORT with nonempty downstream lineage remains unsupported and rejects. Only final frozen-source evidence counts.21TLA/schema/runtime/147nativewitnesses unchanged;145legacyonlysemanticsID. No freshTLC/newmutants. Mandatory44/45/nativeArithmeticRecoveryRefines missing;Phase0 errors unchanged/unfrozen;make absent/noaggregateformal-check. All3demosHTTP200withoutrestart/frozenrefsunchanged. Source-bound semantics: sha256:1c8047dc68099e4e9a3f9206b30974601ad01eb23b15c8596502aea9f9072300.


## 28 September 2026 — fix impossible finalized PARAMETER corpus predicate

Tasks T044/T048/T053/T054/T056/T057; amendment 0001. NO_GO remains.

The preceding original aggregate binding had an unsatisfiable condition for
every nonempty finalized PARAMETER corpus. `NativeCertifiedCorpus.LeafChecks`
called `NativeVectorAuthority.AssignmentChecks`, which requires a nonempty
proposed-vote context. The actual finalized certificate decoder sets that field
to the empty list: the certificate wire has no such field. Thus its conditional
success theorems did not establish an executable positive finalized-corpus path.
Earlier component/encoding examples did not exercise this join. The prior
evidence is retained as historical evidence, not treated as a successful run.

`NativeFinalizedAssignment.decodedContext` and `originalContext` derive the empty
field from the actual decoder and executed finalized lineage check.
`proposedPredicateImpossible` proves the conflict for every checked finalized
edge and every vector bound/assignment, not just one fixture.

The corrected corpus calls a distinct finalized-certificate predicate. It checks
the original empty field, full native certificate context, all ISC/EC/PLAN IDs
and denominator. The computed assignment context stays in the computed body; it
is not copied into or claimed to occur in the original certificate. The existing
frame, domain, shard ordinal, full computed body, ordered corpus, full Q leaves,
native computation and exact decimal checks remain. This neither relaxes native
admission nor proves these stronger projection checks equivalent to it. Original
native certificate/proposed IDs and preimages remain distinct.

`leafFromComponents` reconstructs the real corrected executable leaf checker
from its exact ordinal, vector join, original Q extraction and field/body checks.
The successful checker proves the empty source context; independently, actual
finalized lineage derives the same property for every loaded ROOT leaf. No
proposed-body lookup, fresh-vote admission or future APPLY is added to that path.

Regression examples reuse the pinned original finalized parser/check and hash
proofs, show the former predicate impossible for any assignment, and exercise
the corrected field predicate positively on that exact certificate. Mutations
of native context, each parent, denominator and fabricated vote context reject.
These are component proofs, not a new positive whole vector/corpus/ROOT run.
The independent Python check compares the original certificate/proposal payloads
and schema inventories: only the proposal carries `vote_context_id`.

No full raw positive original/draft corpus execution is claimed. ROOT public body,
nonempty ABORT lineage, shared source/configuration/unit/alias authentication,
complete public durable sets, all-actor sequences and phase/send/delivery/QC/
current/crash/unknown/repair/persist-before-expose refinement remain open.
Concrete bounded codec/hash/exporter resources, native decimal compatibility,
arbitrary snapshots, contract freeze, offline reproduction and independent review
remain required. No new native capture, runtime/guard change, local PASS or GO.

Validation: Full Lean 1185 jobs, three fresh kernels, 58 explicit declarations audited across new modules and modified corpus (12 new general helpers, 16 regression cases, 3 new definitions). 760 tooling/38 oracle,33 legal/112 illegal,Ruff/format/consistency and387 generatedfiles byte-exact PASS. Universal old-predicate impossibility and pinned actual finalized field/parser/hash components verified; no complete positive original/draft corpus or native execution. 21 TLA/schema/runtime/147 nativewitnesses unchanged;145legacyonlysemanticsID. No freshTLC/newmutants. Mandatory44/45/nativeArithmeticRecoveryRefines missing;Phase0 errors unchanged/unfrozen;make absent/noaggregateformal-check. All3demosHTTP200withoutrestart/frozenrefsunchanged. Source-bound semantics: sha256:6e0d9d665a9cdb0b33c76cb2db5b2643ca52d24e17b57da59bbd4a84e7602519.


## 28 September 2026 — proposed ROOT source and complete computed public body

Tasks T044/T048/T053/T054/T056/T057; amendment 0001. NO_GO remains.

NativeRootSource selects exactly one original proposed ROOT by the selected
whole-snapshot candidate. Its checked admission, original proposal preimage,
parent-derived vote context, full ordered leaf identities and each finalized
PARAMETER certificate check/hash follow from actual original source loaders.
Missing/ambiguous proposals and other action kinds reject. ROOT body ID and QC
ID remain different identities. Every finalized leaf retains its empty proposed
vote context; no previous PARAMETER proposal or fresh-vote guard is imposed.

NativeRootCorpus executes NativeVectorContext.bind on exactly the original
policy/state bytes and selected ROOT's plan ID. The policy/state equality with
the selected vote is proved from deterministic decoding of those same bytes,
not passed as an external translation. The shared HashAdapter is tied to the
Binding codec. It derives the complete ParameterCorpus and checks RootChecks
and every corrected NativeCertifiedCorpus.checkLeaf through a strict ordered
zipper. This preserves full source Q records, original certificate context,
ISC/EC/PLAN, domain/shard names, ordinal, denominator, canonical decimal vector,
computed numerator/body and complete key order. No finalized ROOT or future
APPLY is an input requirement. Original snapshot validation still validates
whatever other records are present; their presence is not forced.

PublicRootBody reuses actual checked corpus entries and full PublicAuthority.
It checks the same complete frame and independently rechecks/project all
PARAMETER leaves with PublicParameterBody. It constructs all twelve public
ROOT fields and checks the entire candidate equality plus canonicality. Every
public leaf retains a positional witness to an original finalized certificate
and its actual native computation, full authority and narrow scalar guards.
ROOT has no top-level authority field in this public model: authority is retained
inside each complete PARAMETER leaf. The public leaf set is canonically sorted;
its order-insensitive value does not erase the ordered native source witness.
Duplicate public leaves reject through canonicality. No opaque native QC ID is
substituted for the full public leaf body.

This is conditional general construction, not complete authenticated ROOT vote
or recovery refinement. Binding authentication/source closure, MetadataTrust,
primitive configuration/unit/alias provenance and equality to the configured
public state remain independently required. In particular the public parents
constructed by PublicAuthority must still be joined to the separately derived
original ISC/EC/APC public bodies under common primitive metadata; equal native
parent IDs alone do not prove this structured public identity. Complete public
envelope/phase/QC/durable history/current/recovery composition remains OPEN.

Scalar shape/width127, generated ordinal names, exact decimal spelling and
other existing projection restrictions remain explicit; they are not new native
admission rules or proven TLA/native equivalence. The pinned original shard-a is
not silently renamed to s0000000000. Original008 proof/base/current captures
remain absent. No complete positive raw vector/corpus/public ROOT run is claimed.

Kernel cases reuse the original proposed ROOT and finalized leaf lineage/hash
components, and separately test complete public body/leaf changes and canonical
duplicates. Python inspects the actual original ROOT policy observation: its
ROOT QC/finalized ROOT/APPLY lists are empty while the full PARAMETER QC is
already finalized. That evidence establishes source chronology, not a new
production run or the absent complete raw arithmetic projection instance.

Nonempty ABORT, whole public durable correspondence, all-actor/global sequences,
send/delivery/current/crash/unknown/repair and physical persist-before-expose,
bounded codec/hash/exporter resources, native decimal compatibility, arbitrary
snapshots, contract freeze, offline reproduction and independent review remain
required. No runtime/guard changes, new native capture, local PASS or GO.

Validation: Full Lean1189jobs, four fresh kernels,67 explicit declarations audited (30 general helpers,19 component cases,12 executable definitions,6 structures).762tooling/38oracle,33legal/112illegal,Ruff/format/consistency and387 generatedfiles byte-exact PASS. Original ROOT/leaf and separately public-body components verified; no full raw corpus/public ROOT execution.21TLA/schema/runtime/147nativewitnesses unchanged;145legacyonlysemanticsID.No freshTLC/newmutants.Mandatory44/45/nativeArithmeticRecoveryRefines missing;Phase0 errors unchanged/unfrozen;make absent/noaggregateformal-check.All3demosHTTP200withoutrestart/frozenrefsunchanged. Source-bound semantics: sha256:6ffc846dcec3fcf8bb04e8ac585c8a4a84554388a2cf1298b3fdcb336d5a52a9.


## 28 September 2026 — complete conditional ROOT parent agreement

Tasks T044/T048/T053/T054/T056/T057; amendment 0001. NO_GO remains.

NativeRootParents proves that the computed vector loader and original proposed
ROOT use the same complete PLAN section and the same original finalized PLAN
edge. This follows from executing the parsers on identical original policy/state
bytes, then determinism of section construction and lookup. Original ROOT ISC
and EC are proved equal to the PLAN parents using actual checked lineage and
RootChecks. No externally supplied complete parent equality is a premise.
The existing vector CrossParents checks and exact source lookups also derive
the entire ISC and seed objects shared by PLAN and its EC. Thus the planning
body's SamePlanParents condition follows from this actual checked vector source,
rather than being an extra whole-parent equality supplied by the caller.

Its complete checker loads every ISC member manifest and projected artifact,
including rejected members, with the same HashAdapter/codec and original vector
source. Exact schema/ISC/EC references and complete frame lists are checked.
The full original tuple and eligibility order, every commitment position, stored
canonical ISC/EC bytes and source resolutions are retained. Missing artifacts
reject. This uses the all-member graph checker directly: it does not require a
past proposed PARAMETER vote or future ROOT QC/APPLY. Physical availability and
export authentication remain named boundaries.

PublicParentNames checks primitive ticket/domain spellings, alias lookups and
content names through a strict zipper. Content keys include the entire actual
commitment and its ordered Q references. The original side retains the full ISC
body and original tuple in its independently trusted metadata keys. Original
member bytes are also compared with frame ticket spellings and aliases. General
lemmas derive complete entry/member value-list equality from these lookups and
the original constructors. No caller supplies a complete translated body or
finite arithmetic approval table. These agreement checks do not authenticate
the independently supplied primitive names.

PublicRootParents composes the actual complete proposed ROOT body checker, full
ISC graph checker and PublicPlanningBody.loadApcBody on the original ROOT PLAN.
It checks primitive height/epoch/configuration/close-policy/seed/norm/coefficient
names and full entry/member agreement. Complete ISC, seed, EC and APC value
identity is then proved by construction, including their nested structured
parents. The entire candidate ROOT fields contain those computed original
public parents. All original ISC tuples agree positionally with the full graph
rows; actual authority commitments retain those same positions. Duplicate
original public entries/member aliases reject separately through the existing
separation/canonicality checks, not silently through deduplication.

This is a conditional executable representation join. Shared independent
MetadataTrust, primitive configuration validity, alias injectivity/authentication,
units, native exporter and physical availability remain unproved. Existing
vector CrossParents and narrow scalar/ordinal/decimal restrictions remain stronger
projection restrictions, not newly imposed native admission rules or a native/
TLA equivalence theorem. The current live public configuration is not bound.
There is no complete ROOT envelope/history/phase/QC/recovery refinement here.

Small kernel cases check original pinned parent components and positive/negative
primitive agreement, missing/extra entries, changed ticket/domain/alias/ISC/Q
references and duplicate preservation with separate canonical rejection. Python
independently checks the actual original ROOT policy contains the same complete
earlier PLAN, ISC and EC payloads and no future ROOT/APPLY QC. Metadata is
synthetic in these examples. No new positive complete raw vector/corpus/ROOT
execution, native capture or raw fixture expansion is claimed. Original008
proof/base/current captures remain absent.

Complete ROOT envelope/history, nonempty ABORT, whole public durable set and
all-actor sequences, phase/send/delivery/current/crash/unknown/repair and physical
persist-before-expose still need composition. Bounded decoder/hash/exporter
resources, arbitrary snapshots, contract freeze, clean offline reproduction and
independent review remain required. No runtime/guard change, local PASS or GO.

Validation: Full Lean1193jobs, four fresh kernels,64 explicit declarations audited (35 general helpers,18 kernel cases,9 definitions,2 structures),only propext/Quot.sound/Classical.choice.764tooling/38oracle,33legal/112illegal,Ruff/format/consistency and387 generatedfiles byte-exact PASS. Complete conditional structured parent join; no positive whole raw ROOT/corpus execution or native capture.21TLA/schema/runtime/147nativewitnesses unchanged;145legacyonlysemanticsID.No freshTLC/newmutants.Mandatory44/45/nativeArithmeticRecoveryRefines missing;Phase0 sameerrors/unfrozen;makeabsent/noaggregateformal-check.All3demosHTTP200withoutrestart/frozenrefsunchanged. Source-bound semantics: sha256:9e35c2a80c5a6864cd898394288ea3acedeb185e7b847d0c491d4ab5312842bb.


## 28 September 2026 — complete conditional ROOT envelope and original history position

Tasks T044/T048/T053/T054/T056/T057. Candidate only; mandatory
nativeArithmeticRecoveryRefines remains absent and runtime STOP is unchanged.

NativeHistoryRow.locate executes the original mixed WAL prefix to obtain the
preceding machine, original input and captured row at a zero-based WAL index.
Command positions produce no vote. Source, entire-cache membership, original
bytes/state, global WAL sequence and distinct all-vote ordinal are retained by
general proofs. recoverAt first executes NativeCacheHistory.recover for the
ENTIRE log, so a successful early prefix cannot hide an invalid suffix. It
retains the exact startup, initial machine and successful full recovery witness;
no caller-selected prior machine substitutes for this computation. The existing
zero-snapshot restriction remains. This API consumes a supplied complete input
list; authenticated observation/scan provenance is not newly discharged.

PublicRootEnvelope runs the complete source-bound ROOT parent/body checker,
constructs actor from metadata keyed by the original validator and epoch, kind
AGGREGATE_ROOT, context equal to the ENTIRE structured APC, and the computed ROOT
body. Whole candidate equality and canonicality are checked. The body APC field
and envelope context agree by the previous general parent construction. Native
action 6, original body hash and domain-separated parent context are retained.
No opaque native digest is cast to a structured public body or model symbol.

PublicRootHistory loads the original checked source from the historical policy,
state, WAL command bytes and preceding machine facts, then the selected ROOT,
actual native corpus, full original parents and complete public envelope. Only
ordinary cached rows are accepted. fromHistory uses NativeHistoryRow.Recovered;
the full original cached selection equals the newly loaded selection by actual
source loading determinism, not a supplied equality or finite approval table.
Whole native parent lists remain original. Historical checks do not manufacture
ready/recovered flags, NativePrepared, response exposure or first-vote freshness.

Validation uses the retained original ISC/freeze mixed execution for executable
position lookup and separately constructed ROOT envelope/body components for
actor/kind/context/body mutations and canonicality. There is NO new positive
full raw native ROOT/vector/corpus/history execution, no new native capture and
no giant fixture expansion. Primitive metadata in examples is synthetic. Python
checks the pinned original ROOT snapshot/parent convention and the actual TLA
VoteAggregateRoot envelope schema, including its still-separate phase guards.

OPEN: independent Binding/MetadataTrust/actor/configuration/unit/alias and source
observation authentication, equality to LIVE public configuration, original008
proof/base/current captures and a complete positive raw vector/corpus instance.
Scalar127/ordinal/decimal/CrossParents constraints remain stronger explicit
projection restrictions, not native admission equivalence. ROOT is still
unsupported by the arithmetic-only PublicState.expectedContext and
NativeCacheProjection APIs; the new code does not silently widen them. Complete
all-actor public durable correspondence, nonempty ABORT seven-list construction,
phase/committee/availability/send/delivery/QC/current/unknown recovery composition,
general bounded decoder/hash/exporter/WAL/admission, arbitrary initial snapshots,
failures/repair, contract freeze, clean offline reproduction and independent
review remain required. No local PASS, original BenchmarkResultQC, merged formal
GO, independent attestation or application completeness is claimed.

Validation: Full Lean1197jobs, four fresh kernels,65 explicit declarations audited (31 general helpers,20 kernel/component cases,10 definitions,4 structures),only propext/Quot.sound/Classical.choice.766tooling/38oracle,33legal/112illegal,Ruff/format/consistency and387 generatedfiles byte-exact PASS. Original mixed ISC/freeze lookup components and separate ROOT envelope components; no positive whole raw ROOT/corpus/history execution or new native capture.21TLA/schema/runtime/147nativewitnesses unchanged;145legacyonlysemanticsID.No freshTLC/newmutants.Mandatory44/45/nativeArithmeticRecoveryRefines missing;Phase0 sameerrors/unfrozen;makeabsent/noaggregateformal-check.All3demosHTTP200withoutrestart/frozenrefsunchanged. Source-bound semantics: sha256:c80fc949c211c3d2c0a28c68cb3ca18839462fc7a95724b90f996f7ca3c0f916.


## 28 September 2026 — native ABORT lineage and partial public ancestors

Feature000 candidate only (T044/T048/T053/T054/T056/T057). This does not
discharge nativeArithmeticRecoveryRefines or authorize runtime work.

NativeFinalizedLookup resolves each original ID to exactly one complete typed
object. Missing or ambiguous matches fail. General proofs retain exact query
order, positions, length, membership, unique identity and full payloads.
Unreferenced available objects are allowed; duplicate query IDs are preserved
by this generic resolver, not silently removed. Native snapshot strict finalized
list checks are the separate source of native duplicate-query rejection.

NativeAbortLineage starts with an actual NativeEarlySource.Loaded and an actual
selected NativeFailureSource.Abort. All seven lists come from that original
ABORT and equal the original policy snapshot's finalized lists. CONFIG is a
native ID list, not a full certificate payload collection; every listed config
is proved to equal the original configured native ID. ISC/EC/APC/PARAMETER/ROOT/
APPLY IDs resolve to complete typed objects from the checked snapshot sections.
The source-bound native certificate checks are retained for every ISC/EC/APC/
PARAMETER/ROOT object. Accepted ABORT implies APPLY absence; the resolved APPLY
list is therefore proved empty, rather than being supplied as an assumption.
Lookup uses finalized certificates, never a fabricated proposed ROOT vote or
current first-vote freshness for those certificates.

PublicAbortAncestors constructs CONFIG aliases and complete ISC/EC/APC ancestor
values with the existing source-derived loaders. Each public list preserves
the original finalized ID position and count and is paired with the full native
object. It retains full ISC tuples, EC seed/norm/member data and APC parents/
weights/coefficient keys. Inner and outer duplicate public values reject through
separation checks; set sorting preserves every value. Canonicality is checked
against the supplied model namespace. Primitive metadata and the namespace
still require independently authenticated live configuration; fixtures use
explicitly synthetic metadata. SamePlanParents remains a stronger projection
restriction, not a claim of native admission equivalence.

This is deliberately a PARTIAL public ABORT projection. The complete native
PARAMETER and ROOT objects and original IDs remain in the returned image, with
general retention proofs. They are not replaced by empty public sets. No full
ABORT body/vote constructor is exposed by this module; the existing complete
PublicFailureBody API still rejects nonempty downstream lineage. Numerical
PARAMETER/finalized ROOT public construction and full ABORT envelope/history
composition remain next work. The selected action-6 ROOT loader is not called
on an action-9 ABORT. NativeCertifiedCorpus can resolve finalized ROOTs once the
actual NativeVectorContext and required artifacts are source-bound.

Examples reuse original individual ISC/EC/APC/PARAMETER lookup components and
separate synthetic public ancestor components. Small general lookup/collection
cases cover missing, conflicting/identical duplicate, substituted, reordered,
extra and omitted values, missing primitive metadata and changed APC parents.
They do not instantiate a joined nonempty original ABORT snapshot/vector corpus,
and are not new native executions, captures, TLC runs or production mutants.

All-kind/all-actor exact prior public durable correspondence, independent raw
observation/alias/configuration authentication, actual phase/send/delivery/QC/
current/crash/unknown composition and general recovery remain open. Original
008 proof/base/current capture limitations and scalar/ordinal/decimal projection
restrictions remain. Runtime/native guard unchanged; no local PASS, GO,
BenchmarkResultQC or independent attestation is claimed.

Validation: Full Lean1201jobs,four fresh kernels,98 explicit declarations audited (49 general helpers,27 kernel/component cases,18 definitions,4 structures),only propext/Quot.sound/Classical.choice.768tooling/38oracle,33legal/112illegal,Ruff/format/consistency and387 generatedfiles byte-exact PASS. Original individual certificate lookup components and separate synthetic public ancestors only; no joined nonempty raw native ABORT/corpus execution or new native capture.21TLA/schema/runtime/147nativewitnesses unchanged;145legacyonlysemanticsID.No freshTLC/newmutants.Mandatory44/45/nativeArithmeticRecoveryRefines missing;Phase0 sameerrors/unfrozen;makeabsent/noaggregateformal-check.All3demosHTTP200withoutrestart/frozenrefsunchanged. Source-bound semantics: sha256:b96d22536c196d778dc3643149d4180a44a14993ac6d50d89845967627d420ad.


## 28 September 2026 — accepted R1–R7 scope; R1 candidate freeze

Tasks T000–T003. The user accepted the exact frozen R1–R7 Definition of Done
and authorized only R1–R3. R4–R7 are deferred, not waived. Control reporting is
required after 12 active hours or earlier upon closing R1/R2, an architectural
blocker or transition to BLOCKED_EXTERNAL. Reports describe the residual delta,
not counts of tests or helpers. No new standalone ABORT-body layer is required.

R1: the accepted residual document is preserved byte-for-byte in the feature
specification, with its original hash. candidate-contract.md fixes the existing
arithmetic domain, allowed named assumptions, required source/body correspondence,
and R2/R3 transition/initial-state obligations without widening the DoD. Finite
scalar/alias/fixture restrictions are not native admission equivalence. Independent
metadata provenance may be a named trust boundary; whole-body/recovery equality
may not be supplied as the desired conclusion.

The previously mixed 1.0.0 baseline and 1.1.0 registry are now one candidate
snapshot. The phase-0 verifier retains all existing amendment harness invariants,
checks the complete normative input inventory and accepted residual hash, and
recomputes compatibility from the actual semantic artifacts. Stale nested IDs and
published-looking candidate metadata are rejected. Scope deletion, rehashed input
omission and unknown semantic-version substitution are rejected as well.

R1 input/compatibility checks pass for this snapshot. The contract is frozen;
future source changes still require refreshed compatibility bindings without
changing its requirements. Existing semantic source bytes and semantics ID are
unchanged. The historical merged authority is explicitly separate, and this freeze
is CANDIDATE_NOT_FORMAL_GO. The previous NO_GO report remains evidence only for its
own source tree; final report/reproduction/review work was not started.

Residual delta: R1 OPEN -> CLOSED (contract/input freeze), R2 OPEN, R3 OPEN.
R2 must establish the faithful existing native/public data/admission mapping,
including sufficient ABORT projection and the stated width/vector domain.
R3 must preserve that mapping through the existing persistence, exposure,
QC/current and crash/recovery/replay relation with complete prior state.
The target statements are finite and fixed by PO-AB1, PO-R1/R2 and the accepted
refinement contract; helper-module count is not a completion criterion.
No proof or runtime implementation was changed in this R1 checkpoint.


## 28 September 2026 — R2 early checkpoint: vector bridge architecture

Tasks T044/T053–T057; only R2/R3 authorized. The user accepted R1 CLOSED.
The frozen R1–R7 DoD is unchanged. R4–R7 remain deferred.

A kernel-checked diagnostic establishes that every current complete public
PARAMETER body entails native shard length=1, and every complete public APPLY
body entails length=1 for all source shards. These are universal implications
over metadata, aliases, candidate values and model limits. Consequently the
existing complete-body constructors cannot be composed unchanged into the R2
relation for vector shards. The already checked original manifest has lengths
4,8,8,8,8. This is an architectural blocker in the current scalar bridge, not
an external resource blocker or a new requirement. It does not prove that a
vector-aware refinement is impossible.

Residual delta: no additional R item closed. R1 CLOSED; R2 OPEN; R3 OPEN.
The assumption that unchanged scalar APIs suffice for the general relation is
now ruled out. Next within R2: retain each original shard and all its ordered
coordinates in a faithful arithmetic/state image with the existing width bounds;
keep one original vote/context/certificate and atomic admission. Coordinate
checks alone cannot replace that identity/coverage/state-root relation. Then
finish the same fixed source/configuration/parent/body/state correspondence and
R3 preservation over the existing transition vocabulary. No standalone universal
ABORT-body deliverable was reinstated.

Diagnostic and exact limitations: formal/proposals/r2-domain-audit.md and
r2-domain-audit.lean. Targeted dependency build and fresh Lean diagnostic pass;
only propext/Classical.choice/Quot.sound occur in the audit. The original manifest
is reused evidence, not a new joined admission, runtime execution or exporter.
The diagnostic is outside the mandatory registry and semantic artifact inventory;
its source/dependency hashes are separately recorded in evidence/r2-domain-audit.json.
No production semantic/proof/runtime source, frozen contract, gate or GO report
was changed. The previous formal report remains historical NO_GO for its own tree.


## 28 September 2026 — requested minimal vector relation checkpoint

Tasks T044/T053–T057. The latest direct user instruction narrows this turn to
one representation relation and two proofs, followed by a checkpoint and STOP.
The accepted R1–R7 Definition of Done is unchanged; no further R2/R3 layer is
authorized automatically after this checkpoint.

The new proposal represents a shard as one original identity and one unchanged
manifest entry with an indexed vector. The relation equates the original
identity, full entry and entire ordered value list. It constructs the image
directly; it does not accept a translated body, arithmetic approval table or
desired output equality. Every original shard/vote/certificate identity accessor
is preserved. The actual existing manifest remains five objects of lengths
4/8/8/8/8, with starts 0/4/12/20/28 and all 36 original coordinates. Coordinate
views do not allocate new shards, votes or certificates. The instantiated source
is the original Q/manifest component, not a new joined vote/QC execution.

General kernel proofs show that successful vector PARAMETER computations project
to successful existing scalar checked computations at the SAME bounds and with
the original member order, coefficient checks, products and all prefixes. The
existing source reducer's own output constructs the image; width-one scalar
results remain unchanged. Conversion, mixture and optimizer project to their
existing checked scalar calls with the same intermediate guards and rounding.
The APPLY arithmetic composition uses the same gradient coordinate, and the
global slice theorem retains the original manifest position. There is no claim
that native wide success implies narrow-model admission.

Checkpoint: REQUIRES MODEL/ARCHITECTURE CHANGE for the current scalar public
bridge. The requested lossless numeric representation and scalar-coordinate
statements are proved, but the unchanged complete public body APIs still require
length one. They cannot accept this image for the original vector partition.
Connecting it requires a vector-valued public representation or a synchronized
coordinate-family lifting with one original vote and atomic admission. Neither
next layer is implemented here. This does not establish impossibility of all
alternative refinements and does not require changing native identities.

Residual delta: the two requested local statements are discharged; no top-level
R item closes. R1 CLOSED; R2 OPEN; R3 OPEN; R4–R7 deferred. The same finite
source/body/state and transition obligations remain; there is no new standalone
ABORT obligation or scope extension. Stop proof work pending a new direct user
instruction. Automation remains present and must not resume older broader work.

Reproduction and limitations: formal/proposals/vector-shard-representation.md
and .lean; source-linked evidence in evidence/vector-shard-representation.json.
Targeted dependencies, fresh kernel/explicit axiom audit and unchanged phase-0
contract check pass; only propext/Classical.choice/Quot.sound are used. The
proposal is outside the mandatory theorem registry/semantic inventory and does
not discharge nativeArithmeticRecoveryRefines. Candidate semantic/runtime and
accepted-contract bytes remain unchanged. No full formal gate, final report,
new native capture, exporter authentication, independent review or GO is claimed.
All three local demo endpoints remain HTTP200 without service restarts.


## 28 September 2026 — R2 architecture options, documentation only

The user requested an ADR comparing vector-aware public representation (A)
with a synchronized scalar projection family over one original vector object
(B), and explicitly prohibited implementation before choosing an option.
docs/adr/0011-r2-shard-representation-options.md is PROPOSED/AWAITING USER CHOICE.
It records affected TLA/Lean/public-schema/fixture contracts, reusable proofs,
required bridge changes and the distinction between formal representation and
native protocol semantics. B is recommended for scalar-contract reuse, not
claimed to minimize proof effort or to have established whole-state equivalence.
Neither option was selected or implemented. No code/schema/proof/fixture,
mandatory semantic artifact, accepted DoD or GO report was changed in this step.
R1 CLOSED; R2/R3 OPEN. STOP remains in effect pending a direct option decision
and authorization; no new proof layer follows this documentation checkpoint.

## 28 September 2026 — option B impact estimate only

Tasks T044/T047/T053–T057. The user accepted ADR-0011 as an architectural fork
and requested an implementation-free impact estimate for B, not authorization
to implement either option. docs/adr/0011-r2-b-impact-estimate.md records exact
existing TLA actions, Lean entry points, schema/checker and fixture families with
UNCHANGED / PROOF REUSE / MODIFICATION / RE-RUN ONLY / INVALIDATED classifications.
The estimate preserves original shard/vote/certificate/WAL identity, keeps scalar
leaf specifications, and identifies the required common family/state composition.
The current nativeSnapshot.projection_id is already an APC/aggregate binding and
must not be repurposed as a family ID. The existing full-width/ModelLimit guard
gap remains part of frozen R2, not an extra requirement or assumed equivalence.

Remaining R2 is estimated at 32–56 active hours and R3 at an additional 28–52,
conditional on the representation-only design being sufficient. These ranges
exclude final R4–R7 acceptance and all runtime/demo/benchmark work; they are not
a delivery promise. The former R2 estimate assumed unchanged scalar constructors
could be composed, which the later diagnostic ruled out for the accepted vectors.
Old scalar/native component theorems remain valid in scope. Old source-bound
aggregate evidence cannot automatically qualify a future changed family target.

Residual delta: none closed; R1 remains CLOSED and R2/R3 OPEN. Frozen DoD R1–R7
unchanged. This step edits documentation only; no implementation, mandatory
semantic/proof/schema/fixture artifact, report or runtime is changed and no new
proof layer or gate is run. STOP remains pending direct implementation permission.

## 28 September 2026 — conditional B feasibility spike / STOP checkpoint

Tasks T044/T047/T053–T057. The user authorized only the central B feasibility
experiment, at most eight active hours, with no production Init/Next, certificate
semantics or WAL identity changes and no automatic R2/R3 continuation.
Result **FEASIBLE within the bounded PoC scope**; see
`formal/proposals/b-feasibility/README.md` and
`formal/proposals/evidence/b-feasibility/checks.json`.

Residual reduction is a specific architectural subquestion, not a top-level R
closure: a complete synchronous coordinate family over one original vector object
can reconstruct its original ordered Q/result/model/optimizer data, retain its
original command bytes, shard/vote/QC identity and sequence, and share one journal
operation. The general Lean relation has no width-one constraint. The existing
checked vector PARAMETER computation derives each scalar coordinate at the same
bounds. Actual unchanged production actions compose in one synchronized finite
suffix; partial persist violates the common relation, and two original signers
cannot finalize a QC through coordinate multiplication.

The concrete source is the existing diagnostic `native-coordinate-matrix` d00/s01
shard `[3,-4,5]`, sequence 6; original 4/8/8/8/8 component proofs are reused without
pretending that their missing joined native vote/QC/WAL capture exists. The source
QC identity is a synthetic trace label and its receipt is a diagnostic journal
projection. Their preservation is not signature/exporter/fsync authentication.
The TLA suffix starts from the existing certified Phase6 premise, not from empty
production Init or a proven original full public/native state relation.

R1 remains CLOSED. R2 still owes the general source/body/admission/state relation,
all target widths and bound compatibility; R3 still owes complete recovery
refinement. R4–R7 are untouched, DoD unchanged, no new ABORT gate or residual.
The isolated proposal is outside the mandatory semantic inventory. No existing
production/TLA/schema/fixture/runtime/guard or GO report is changed. Healthy demos
8870/8865/8872 were checked read-only. Full R2 implementation is **not authorized**:
STOP after this checkpoint, keep the automation present and quiet, await a new
direct user decision.

## 28 September 2026 — selected B / general original-shard family transfer

Tasks T044/T047/T053–T057. The user selected B for R2 with a maximum of twelve
active hours, frozen R1–R7 and no automatic R3 continuation. See
`formal/proposals/b-family-transfer/README.md` for the checkpoint and exact residual.

R2 residual reduced: heterogeneous positive shard lengths now have a general
selector-family relation, two-sided ordered reconstruction and locality. It is
instantiated directly from the unchanged original 4/8/8/8/8 manifest and its byte
loader, preserving all five objects, offsets and 36 Q values. The source-loader
theorem covers every admitted layout within existing bounds, not only those five
sizes. Complete native PARAMETER families derive from actual ordered rows and
NativePrepared.source; their complete bodies/bytes/envelopes/sequence reconstruct.
NativeApply's whole vector state reconstructs through its actual schema's original
shard ranges, retaining next-model/optimizer hash preimages. Common original
signer/certificate/record objects cannot gain coordinate-level protocol identities.

This closes the representation/length-one obstruction, not the full R2 mapping.
The remaining fixed work is the family integration into full public input/body
constructors, native/public bound and admission compatibility, shared source/config/
alias/certificate/state correspondence, and general relation composition/review.
Existing scalar APIs are not claimed migrated. Named authentication boundaries and
the absent joined original004 vector vote/QC/WAL capture remain explicit; original008
scalar identities were not substituted. No new exporter or universal ABORT gate.

Fresh isolated kernels, axiom audit, read-only original source reproduction and
protected-source comparison are recorded in `formal/proposals/evidence/b-family-transfer.json`.
No production Init/Next, mandatory proof/schema/fixture, certificate semantics,
WAL identity, runtime guard, semantics registry or GO report changes. No fresh TLC
or complete formal gate is claimed. R1 CLOSED; R2 OPEN (remaining estimate 28–48
active hours); R3 not started by this task; R4–R7 untouched. Evidence is local
self-review, not independent attestation or Formal GO.

## 28 September 2026 — R2 three frozen obligations / bounded constructor stage

Tasks T044/T047/T053–T057. The user authorized only the three remaining R2
obligations for at most four active hours, beginning 17:12:54 UTC. Frozen R1–R7
and production Init/Next/certificate/WAL semantics are unchanged. The detailed
residual is in `formal/proposals/b-family-transfer/CONSTRUCTORS.md`; reproducible
source-bound evidence is `formal/proposals/evidence/b-family-constructors.json`.

1. **Family to complete public inputs/bodies — PARTIAL.** Original vector cells,
   ordered contributions and same-source current vectors now feed the complete
   public input encoder and complete PARAMETER/ROOT/APPLY constructors. Complete
   authority and body canonicality/acceptance follow from source-bound components,
   primitive metadata and exact encoded-set uniqueness, rather than an assumed
   whole translated body. The embedded inputs compute the same parameter value;
   current-to-next scalar mixture/optimizer cells use the original global offsets.
   ROOT does not require subsequent APPLY/conversion success. Remaining: all
   configured inputs under OMIT_UNAVAILABLE and total source/input-loader coverage.
   The final source-loader composition additionally proves exact block/corpus,
   family input and authority loading on that checked domain. Thus executable
   acceptance of an existing checked input is derived; existence and canonicality
   over every original source, including omitted inputs, remain open.
   The complete PARAMETER/APPLY body gates are now composed with those exact
   input loads, without a further successful-loader or whole-body equality premise.
2. **Native widths to existing public guards — PARTIAL.** Numeric implications
   cover checked coefficients/products/prefixes, conversions, mixture and optimizer
   intermediates at the relevant native widths, with a separate symmetric result
   bound. Original uint64 optimizer denominators/negative rounding and checked
   negation are represented. The existing native final LCM bound justifies signed
   domain-weight denominators and every LCM prefix. Remaining: compose these
   results with the full original source domain, removing or justifying old
   4096/name/encoded-size/signed-fraction adapter restrictions and binding the
   already required normalized immutable configuration. Raw profile syntax validity
   is not admission and does not establish normalization.
3. **Unified source/configuration/state relation — OPEN, partial composition.**
   Original arithmetic journal source, full computed family body and exact
   vote/context/sequence now compose in a checked arithmetic subrelation. ROOT
   parents agree through original primitive metadata; actor aliases are bijective
   to the original decoded committee, and signer count/quorum cannot multiply by
   coordinates. Remaining: one common authenticated configuration/alias namespace
   and complete static state/certificate/vote collection coverage across the
   existing object kinds. This arithmetic subrelation is not the complete R2.

The residual stays finite: these are the same three source/input/domain/static
state interfaces, not more vector-length cases or a new protocol feature. The
full existing ABORT body is not added as a separate gate; only its frozen sufficient
projection remains in R2. No requirement for production Init/Next, certificate or
WAL identity change has been established. This is not BLOCKED_EXTERNAL.

R2 remains OPEN and R3 was not started. No mandatory semantics, existing source
fixtures, runtime/guard or FormalVerificationReport was edited; the unchanged
historical NO_GO report is not an exact-source report for this new proposal.
Fresh isolated proposal kernels, complete named-declaration axiom audit, original
byte-source reproduction and protected-source equality are recorded in the linked
evidence. No fresh TLC, full formal gate, native execution, independent attestation
or GO is claimed. Remaining R2 planning estimate: 24–44 active hours, low confidence,
excluding R3 and R4–R7; this is not a delivery promise. The bounded stage ends at
its recorded checkpoint; no automatic R3 or broader continuation is authorized.

## 29 September 2026 — R2 six-hour stage / frozen residual checkpoint

Tasks T044/T047/T053–T057. Scope remains exactly the three accepted R2 obligations;
R1 stays CLOSED, R2 stays OPEN and R3 was not started. The bounded stage began at
07:59:56 UTC, with a maximum of 21600 active seconds. Exact elapsed time and the
end of authorization are recorded in the external active-time ledger. No new
requirement, protocol object, production predicate or independent proof layer
was added. See `formal/proposals/b-family-transfer/CONSTRUCTORS.md` and the exact
source/evidence manifest `formal/proposals/evidence/b-family-constructors.json`.

| Frozen R2 obligation | Checkpoint status | Change in residual |
|---|---|---|
| 1. Family to full public inputs/bodies | CLOSED | The original-source path constructs all configured inputs, including a proved latent completion for OMIT_UNAVAILABLE, and complete PARAMETER/ROOT/APPLY bodies. General admitted original shard lengths, ordered rows, global offsets and identities are preserved. Component canonicality is derived from checked primitive names and original values, not assumed whole-body equality. |
| 2. Native INT64/INT128 to public arithmetic guards | CLOSED | Direct constructors remove the old draft adapter limits. Checked products/prefixes, conversion, mixture and optimizer retain original widths, uint64 denominators, signed minimum and rounding. The actual policy-selected normalized profile and source-keyed quantum supply the same input/body configuration. |
| 3. Unified source/configuration/aliases/certificates/state relation | OPEN | Whole all-actor durableVotes/durableSequence now have exact original WAL coverage. Current/pointer/QC/value and observed config-alias components are joined. Remaining complete state/collection applicability and source coherence are described below. |

CLOSED for 1/2 is a component claim under the original source, checked immutable
numeric configuration and primitive namespaces. It does not assert that all
observed state is already related or that the remaining source authentication
boundary is proved. That global coherence remains the same obligation 3.

Within 3, the reader now consumes the original complete mixed WAL per actor,
preserves physical command/vote positions and matches the complete public vote
set in both directions. Supplied extra/missing/duplicate/substituted votes fail.
Public durableSequence counts actual votes; command positions are not mistaken
for vote counts. Historical source packets keep their own original context and
current; they are not required to satisfy a later first-vote freshness check.
Known but unexposed durable records are supported without inferring delivery.
Corrupt, torn or UNKNOWN observations cannot create a complete witness.

The same native certificate graph determines shared ISC/seed/EC/APC parents.
Current values can come from canonical authenticated initial anchors or an actual
finalized prior APPLY QC in a snapshot, without inventing pointer history. The
public currentCheckpoint uses both existing checkpoint namespaces and binds to
the actual pointer/QC/model/optimizer sources. Original current-QC signers and
quorum use the same decoded policy and actor namespace. Current certificate
parents are also constructed without requiring a local vote; native context and
agreement with an actual same-source vote are derived. This removes an adapter
dependency for those parents, not the complete remote-certificate relation.
Observed configuration aliases are checked not to merge distinct native IDs.

These components now also compose in `loadObservedState`, one executable static
check sharing the whole public state, actor namespace and current pointer. It
rejects a configuration alias collision between the actual current policy and
any observed journal row and derives forward name agreement for equal native
IDs. This joins the already constructed fields; it does not fill the remaining
certificate/candidate/environment collections or establish initial applicability.

The exact remaining obligation 3 is unchanged in scope:

- Join the existing primitive source/authentication/configuration/alias witnesses
  across the complete snapshot, including configured units and namespaces not
  determined by the observed journal alone.
- Bind all remaining certificate/candidate/current/environment collections and
  relevant fields, including their existing complete-document representation
  guards. The native ROUND_STATE summary alone is insufficient; these fields
  require the existing snapshot/artifact/environment sources. No production
  network/exporter implementation is added to R2.
- Prove applicability for the admitted initial/incomplete observations and the
  frozen sufficient ABORT projection. The reused full failure-body constructor
  still handles only empty downstream ABORT lineage; a universal full ABORT body
  constructor is NOT a new gate. Nonempty original lists must not be erased.

This is a finite set of existing source interfaces and the fixed public-state
field/action vocabulary. There is no new proof obligation per vector length or
coordinate. The obstruction is missing integration and general applicability,
not a demonstrated requirement to change production Init/Next, certificate
semantics or WAL identity. R2 is not declared BLOCKED_EXTERNAL. The earlier
remaining-hour estimate has not been independently recalibrated into a promise.

Fresh isolated Lean kernels, complete named-declaration dependency audit, exact
original byte-source reproduction, Ruff and protected-source checks are captured
in the proposal evidence. This is self-review. Mandatory semantics/report,
production/TLA/schema/fixtures/runtime/guard and frozen demo refs are unchanged.
No fresh TLC, full formal gate, production execution or GO is claimed.

At this bounded checkpoint, STOP: no automatic further R2 work and no R3.
The existing automation stays present/ACTIVE and quiet for unchanged state;
a heartbeat is not a new scoped instruction or an extension of this budget.
