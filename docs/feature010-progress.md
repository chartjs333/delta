# Feature010 continuation checkpoint

Updated: 2026-09-23. Current stage: **Feature000 arithmetic binding candidate, IN_PROGRESS**.
No new Formal GO, qualifying BenchmarkResultQC or Feature010 GO checkpoint exists.

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
