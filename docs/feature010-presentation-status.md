# Presentation checkpoint — 2026-09-23

The user's morning deliverable is a working application. The local presentation
is now runnable at **http://127.0.0.1:8870/**; the existing Controller/Worker and
advanced UI run at **http://127.0.0.1:8865/**. Keep these services available while
continuing formal work in the other worktree.

Source: `b5f06eff7488c367b882050483bb08130456bfd7`.
Baseline Controller: `c8aea64972f741060d1e527ebbb6f9a5a168a075`, clean
`D:/delta-main-demo`. Original port 8765 was not stopped or modified.

User entry point: `D:/delta-presentation/START.cmd` (one click), or
`D:/delta-presentation/ОТКРЫТЬ.url`. Russian five-minute presentation runbook:
`tools/presentation/README.md`. Data and logs: `D:/delta-data/presentation-20260924`.

Actual browser-triggered, clean-source runs:

- TRAIN_TICKET job `25f4b942a3da49fd819fbd642667abc0`, execution
  `1883cca9-eab3-4029-a92d-a984b1675500`: COMPLETED in 3,609 ms; receipt lineage
  matches intent/admission/execution. CPU synthetic tabular plugin.
- Docker job `0836507ffdfe4260825bfc2d190c1a30`, run
  `sim-0f22b60922844f7aa838d1f314958d35`: completed in 22,515 ms;
  4/4 → 3/4 → 2/4 → restarted 3/4. Offline signature verification passed in
  the pinned image and exact owned-resource cleanup completed.
- Ten wrapper tests, Ruff, JavaScript syntax and PowerShell parsing passed.
- Graceful full stop/restart preserved history; repeated start was idempotent.
- Browser history, JSON download event, readiness page and console were checked.
- Backend HTTP smoke covered real completion, cancellation, receipt lineage and
  required request headers; original report remains under the local data root.

Machine-readable acceptance and public evidence are in
`specs/010-wan-benchmark-and-quality/evidence/presentation-local/20260923/`.
Review was performed by the same agent. No independent review/custody is claimed.
The Windows host lacks `openssl`; standalone verification should use the pinned
Docker image, as the runner already does. No runtime dependency was installed to
mask that difference.

The presentation wrapper changes no protocol/native semantics. It does not execute
Java/Netty/native WAL or GPU training. Training and Docker runs are separate;
they do not establish scientific joined lineage, real WAN or Gate A/B/C/D PASS.
The separate formal candidate remains NO_GO. BenchmarkResultQC and GO checkpoint
remain null, and Feature011 stays blocked.

Next: keep the app operational and continue the actual formal/runtime/qualification
work using `docs/feature010-progress.md` in the feature000-binding-candidate worktree.
Do not rewrite this demo as a qualifying benchmark or mark mandatory tasks done.
