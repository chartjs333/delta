# Verification lab · September 25 demonstration

Scope: presentation/tooling only; semantic impact NONE. Related Feature010
T013/T023/T051 and HR010-001 remain subject to their original acceptance gates.
This demonstration does not complete those gates or override the formal STOP.

## Open and demonstrate

Use `/verification/?lang=en` or `/verification/?lang=ru` on Presentation port
8870 or on the current authenticated Quick Tunnel origin. Links are in both
Presentation and Admin UI. The Controller stays on 8865 and node training on
8872; they are separate examples reached through the common presentation host.

English, about three minutes:

1. “This is a live execution of our pinned formal arithmetic reference on a
   small synthetic example. The native qualification is still in progress.”
2. Click **Run all 7 checks**. Point to the parent `[20, -20]`, shard numerators
   `[1, -2]`, converted coordinates `[1, -1]`, and next model `[19, -19]`.
   Each launch executes a new local Python child process. The displayed duration
   measures this reference calculation, not native runtime performance.
3. Open **Repeat → identical bytes / Details**. The two new witnesses in that
   process reconstruct the same canonical bodies. This is not an independent
   validator/process safety-gate result.
4. Run **Change an artifact’s bytes**. Open **Details** and show `ARTIFACT_BYTES`.
   The bytes were actually changed while the old content ID was retained; the
   unchanged oracle rejected the mismatch. The pipeline above explicitly shows
   baseline reference values, not accepted output from the invalid input.
5. Download JSON. Show the browser-verified report digest and the separate stable
   computation digest. Switch language or reload: the selected result remains.
6. Follow **Show node training** if the audience wants the existing learning demo.

Русский, около трёх минут:

1. «Это живой запуск закреплённого формального эталона на небольшом синтетическом
   примере. Квалификация native runtime ещё продолжается». Нажмите
   **Запустить все 7 проверок**.
2. Покажите исходную модель, расчёты PARAMETER, преобразованные координаты и
   следующую модель. Откройте подробности повтора: байты результатов совпадают.
3. Запустите **Подменить байты артефакта** и откройте **Подробности**. Причина
   отказа — `ARTIFACT_BYTES`. Аналогично можно показать неверный результат,
   отсутствующий optimizer или другую исходную модель.
4. Скачайте JSON, покажите проверенный SHA-256, обновите страницу. Отчёт сохранён.
5. При необходимости перейдите к существующему примеру обучения узлов.

## Exact execution boundary

`verification_oracle/manifest.json` pins two unchanged proposal Python modules
and `formal/fixtures/traces/native/normal-apply.json` from source commit
`998866280cc4df4c8ef586a2ef023758b3262237`. The runner verifies the manifest and
every file hash before importing via explicit local paths. No mutable formal
checkout, network fetch, arbitrary shell input or user-provided Python is used.
The finite example contains twelve artifacts. Snapshot/certificate projections
are synthetic premises, not authenticated native snapshots or signatures.

The runner derives both PARAMETER bodies, checks them with the existing proposal
oracle, converts quantum values and computes APPLY. Negative cases actually call
that oracle with changed bytes, candidate bodies or anchor state. An unexpected
acceptance or different rejection reason makes the presentation job fail; the
runner cannot label that execution successful merely by setting a summary flag.

Every report says `FORMAL_REFERENCE_DEMO`, `SIMULATED_LOCAL`,
`native_execution=false`, `native_export_authenticated=false`,
`gate_eligible=false`, with null WAL receipt, BenchmarkResultQC and GO checkpoint.
The formal source's decision remains **NO_GO**. Hash integrity is not a digital
signature, native execution, durable-vote evidence or scientific qualification.

POST `/api/verify/{all,valid,repeat,parameter-tamper,apply-tamper,artifact-tamper,
missing-optimizer,stale-parent}` accepts only `{}` with the existing origin and
request marker checks. Presentation jobs share one active-job lock, so reference
runs cannot overlap existing presentation training/controller jobs. The child
process has a 30-second timeout; reports are atomically written in the existing
panel data directory. History/download use existing job IDs and report routes.

## Restart and fallback

`D:/delta-presentation/START-REMOTE.ps1` starts the stack and prints the current
external URLs/access code after a reboot. Quick Tunnel names can change. Open
the printed origin plus `/verification/?lang=en` (or `ru`). If an old page is
cached, reload. The access code protects this page exactly like Admin UI.

The frozen `demo/presentation-2026-09-24`, `demo/node-training-2026-09-24` and
`demo/controller-2026-09-24` references remain unchanged. Never move these tags.
For rollback, check out the frozen presentation tag in a separate worktree and
use its launcher against the existing data after stopping the owned idle panel
and gateway; reinstall that source's Admin assets using `install-admin-ui.ps1`.
Do not reset a dirty checkout or stop the Controller/Worker or node host during
a showing. The checkpoint bundle is in `D:/delta-presentation/checkpoints/2026-09-24`.

## Reproduce checks

```powershell
python -m unittest discover -s tools/presentation -p test_verification.py -q
python -m unittest discover -s tools/presentation -p test_server.py -q
python -m unittest discover -s tools/presentation -p test_tunnel_gateway.py -q
node --check tools/presentation/static/verification/app.js
npm --prefix tools/admin-ui run typecheck
npm --prefix tools/admin-ui test -- src/app/App.test.tsx src/i18n/language.test.tsx
npm --prefix tools/admin-ui run build:live
npm --prefix tools/admin-ui run audit:live
```

Also exercise the real browser run, a negative scenario, EN/RU switch, reload,
JSON download/digest, and authenticated remote route. The oracle tests deliberately
change its pinned source/manifest and rehash false reports to verify fail-closed
handling. These are presentation tests, not new production protocol mutants.
