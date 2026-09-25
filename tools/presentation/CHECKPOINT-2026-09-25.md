# September 25 · Verification lab release

The user requested a visibly new working application for a presentation within
two hours. The new Verification lab is installed at
`http://127.0.0.1:8870/verification/?lang=en` (also `ru`) and linked from both
Presentation and Admin UI. Use the current Quick Tunnel origin printed by
`D:/delta-presentation/START-REMOTE.ps1`; the route is `/verification/?lang=en`.

Application implementation commit: `36817a9`.
Panel-only restart option commit: `d15a00a8aac362e70cdab60282b858ff1120caca`.
The release snapshot is tagged `demo/verification-lab-2026-09-25` and branched
`codex/demo-verification-lab-20260925`. The September 24 frozen refs remain
unchanged; they are the fallback, not replaced by this tag.

Verified live report:

- job `57af5edb42364e33ab6049a4a37a289e`;
- report SHA-256 `91d612026a425e6d11b86c0d90c2d54c976dc8bfcd90f9127c9d845c2cfce861`;
- computation SHA-256 `3c1a423ea205a97027e1345f75fa1b9cd79924fadff844567b739124a1165c25`;
- seven expected outcomes, including five actual oracle rejections;
- authenticated HTTPS login, static EN/RU pages, fixed-command POST and downloaded
  report checked through Quick Tunnel; unauthorized API and cross-origin POST
  rejected. This was a remote HTTP test, not a claimed remote-browser interaction;
- actual browser EN all-case run, RU negative case, SHA verification and reload
  checked on staging; installed Admin link and saved result checked in the browser.

The report is stored in the existing panel jobs directory. Deployment evidence
is `D:/delta-data/presentation-20260924/panel/verification-remote-smoke.json`.
Tests/source scope are recorded in `verification-checks-2026-09-25.json`.
The operational scenario is in `VERIFICATION-LAB.md`.

The first panel promotion used the historical launcher `stop`, which also
gracefully restarted Controller/Worker on the unchanged `c8aea649...` baseline.
Controller returned READY, all four saved profile runs remained, and the prior
receipt `7b845920-6c20-419f-9a5a-543fb9fdd2e5` verified again. The node-training host
was not restarted. Future panel-only updates use `stop -KeepController`.

This release is **FORMAL_REFERENCE_DEMO / SIMULATED_LOCAL**. It executes the
unchanged pinned Python proposal oracle on a synthetic twelve-artifact example,
not native C++ admission/WAL or scientific training. No new protocol semantics,
Formal GO, BenchmarkResultQC, Feature010 GO checkpoint or qualification is claimed.
The native arithmetic guard is unchanged. Self-review is not an independent review.

Formal work remains on the separate clean `codex/feature000-binding-candidate`
checkout at `2098ee0ac0961e78240c0b7fddf37a2724d8cce2` (NO_GO, mandatory 44/45).
The unfinished next Lean representation draft was parked in ignored
`formal/build/PublicState.draft.lean`; it is not a compiled proof or an authority.
Resume the complete public-state/native identity representation there after this
presentation priority. Preserve healthy demo services during a showing.
