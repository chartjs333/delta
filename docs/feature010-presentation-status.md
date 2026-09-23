# Presentation checkpoint — 2026-09-23

The user's morning deliverable is a working application. The local presentation
is now runnable at **http://127.0.0.1:8870/**; the existing Controller/Worker and
advanced UI run at **http://127.0.0.1:8865/**. Keep these services available while
continuing formal work in the other worktree.

The presentation now supports **English / Русский**. New browsers default to
English; `?lang=en` explicitly selects it, and the UI remembers language changes.
The one-click launcher opens English. All presentation pages, known log messages,
statuses, dates and durations are localized. Original receipts/evidence retain
their bytes. English speaker notes: `tools/presentation/PRESENTATION-EN.md`.
Browser verification covered both languages, reload and storage persistence,
query-language override, history/readiness and switching during an actual training
run (`83737f24-d4c7-478c-867f-9a944cd282a4`, COMPLETED). Ten wrapper tests passed;
JavaScript syntax, Ruff and the complete recorded training/Docker log translations
were checked. No console errors were observed.

Original presentation source: `b5f06eff7488c367b882050483bb08130456bfd7`;
bilingual presentation checkpoint: `173da69`.
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

## Bilingual Admin UI checkpoint

Admin UI is available in English and Russian at
`http://127.0.0.1:8865/?lang=en#/live-execution` and
`http://127.0.0.1:8865/?lang=ru#/live-execution`.
Presentation → Admin and Admin → Presentation links preserve the selected language.
The Admin language selector preserves the current form, route and in-session
execution state; reload preserves the language through the URL. Admin execution
lists remain session-local, while Controller receipts remain available on the server.
Protocol IDs, canonical intent bytes, digests and original receipts are unchanged.

Installed UI source: `52ddc939a38fdb36ab2190bca4b6ff42b67fb534`.
The Controller stayed online at clean baseline `c8aea649…`; its build identity is
separate from the UI identity in `D:/delta-data/presentation-20260924/admin-ui/installed.json`.
Use `tools/presentation/install-admin-ui.ps1` to reproduce this UI deployment.
`START.cmd` preserves it; rebuilding the old baseline UI would replace it.

Verification:

- Full `npm run check` on the installed UI source passed: 242 tests in 39 files,
  pinned TypeScript typecheck, validator/catalog checks, offline build and boundary audit.
- Live build and boundary audit passed; all installed file SHA-256 hashes match
  the installation manifest. Browser review covered both languages, catalog,
  Controller forms, execution builder, language-preserving navigation and reload.
- Actual Admin-submitted execution `4ea0df87-ead3-41fb-8749-a614f7beb358`
  completed and loaded its terminal receipt. EN → RU switching preserved that
  execution. It used UI source `520287a`; later UI changes adjusted header contrast
  and compatibility labels. Receipt canonical digest and all lineage fields were
  checked again against saved Controller status:
  `sha256:1521a04bc0eada4008439c8238d3761d4b15ced69cb8d0ebb5b52b0aca868d93`.
- This is CPU synthetic training with `PLUGIN_BOUNDARY`, not GPU/native qualification.
  Workloads sample buttons show fixtures; Controllers is a local worksheet;
  Campaigns remains an unavailable placeholder. The English runbook describes
  the working Admin demonstration path.

Acceptance, test output, asset manifest, status and receipt are retained under
`specs/010-wan-benchmark-and-quality/evidence/presentation-local/20260923/admin-ui/`.
Local shortcuts: `D:/delta-presentation/ADMIN-EN.url` and `ADMIN-RU.url`.
Self-review only; no qualifying gate completion or independent attestation is claimed.

## Guided Admin UI

Latest installed Admin source: `4f6682451882358a6af26786982e81fa7b56728d`.
The live execution page now opens in **Simple mode / Простой режим**. A named
synthetic CPU example uses the existing intent/HTTP adapter, polls its actual
status and downloads the receipt only after existing schema/hash/lineage checks.
Uncertain admission blocks blind resubmission. Read failures expose no verified
result; completed/failed runs can be inspected in the technical views. No new
backend or protocol action is introduced. The six-stage protocol explanation is
explicitly educational and separate from local run progress.

All 249 tests in 40 files pass, including duplicate-click prevention, receipt
failure, uncertain admission, failed execution, language changes and unmount
fencing. Both bundle audits pass. Browser execution
`04729563-03b7-4c13-a969-fbdbc8101ede` completed; its downloaded receipt matched
the Controller digest and lineage. Its source was `3ea3430`; final source only
moved controls for the laptop viewport. Both languages and interactive explanation
were inspected. Controller baseline stays clean at `c8aea649…`.

Evidence: `specs/010-wan-benchmark-and-quality/evidence/presentation-local/20260923/admin-guided/`.
Scope/review: `tools/presentation/ADMIN-UX.md`. Startup continues to preserve the
installed static bundle. This remains local presentation evidence, without GO/QC.
