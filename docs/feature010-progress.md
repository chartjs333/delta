# Feature010 continuation checkpoint

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
