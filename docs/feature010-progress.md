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
