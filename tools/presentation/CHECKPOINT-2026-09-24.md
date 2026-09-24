# Saved demonstration / Сохранённая демонстрация

Frozen for the next presentation on **25 September 2026**. This is the working
presentation fallback; it is not Feature010 GO or a BenchmarkResultQC.

| Component | Git reference | Source commit |
|---|---|---|
| Presentation, Admin EN/RU, SDK, slides, tunnel and node-page integration | `demo/presentation-2026-09-24` | Application code: `6df5957068449c5ada0a7c7b92991be967ff7e59`; the tag adds this checkpoint documentation |
| MNIST node-training page including the existing EN/RU changes | `demo/node-training-2026-09-24` | `2f76e6993c50f3248487539d09597c233d634bf9` |
| Baseline Controller / Worker | `demo/controller-2026-09-24` | `c8aea64972f741060d1e527ebbb6f9a5a168a075` |
| Formal candidate shown at snapshot time, **NO_GO** | `demo/formal-status-2026-09-24` | `0d192cf7deb8ba7798b31b4380d0d08ba3bdf984` |

The node snapshot was created using a separate Git index. The original node
checkout, index and working files were left unchanged; its previously uncommitted
translations are now also retained in the named snapshot commit. All four refs
belong to the same repository. Machine-readable pins and checks are in
[checkpoint-2026-09-24.json](checkpoint-2026-09-24.json).

## Show it tomorrow / Показ завтра

On the prepared host, run:

```powershell
pwsh -NoProfile -File D:\delta-presentation\START-REMOTE.ps1 start
```

It starts missing owned services and prints the current external HTTPS URLs and
access code. Run `status` to recheck them. After a reboot, run `start` again;
the Quick Tunnel URL can change. Keep the host powered and connected.

For the presentation, use **How it works → Admin / Live execution → receipt →
Node training → Failure and recovery**. EN/RU share the saved application state.
The node-training example is separate from Controller campaigns and carries
`LOCAL_DEMO_ONLY`; simulated controllers/WAN remain `SIMULATED_LOCAL`.

По-русски: запустите команду выше на основном ПК, скопируйте выведенные адрес и
код. Покажите слайды, Admin и выполнение задания с квитанцией, затем обучение
узлов и восстановление после сбоя. После перезагрузки снова выполните `start`:
старый адрес туннеля может перестать действовать. Текущее рабочее демо сохранено
отдельно от продолжающейся разработки Feature010.

## Restore sources / Восстановление исходников

To inspect or rebuild a saved version, create new worktrees at the frozen tags.
Use new, absent directories. Do not reset or replace a running checkout:

```powershell
git -C D:\delta worktree add --detach D:\delta-demo-restore-20260924 demo/presentation-2026-09-24
git -C D:\delta worktree add --detach D:\delta-node-restore-20260924 demo/node-training-2026-09-24
```

Git preserves source, the supplied slide images, launchers and these version
pins. Prepared Python/Java/native tools, MNIST/model caches, generated UI assets,
profiles, run history and signing/access credentials live outside Git. The
prepared host remains the runnable environment; a fresh host needs the setup
in [README.md](README.md), [NODE-TRAINING.md](NODE-TRAINING.md) and
[REMOTE-ACCESS.md](REMOTE-ACCESS.md). The installed Admin UI manifest and its ten
file hashes are preserved in the checkpoint; its source is unchanged between
`7ee7bb87ebb475ed9155440baadd72d42079b356` and the saved application commit.

The local checkpoint directory `D:/delta-presentation/checkpoints/2026-09-24`
also contains a verified Git bundle, the read-only HTTP verification record and
a small data snapshot. The data snapshot contains the saved profile, job JSON,
node result/view and installation metadata. It is **not a complete runtime or
credential backup**. Original data in `D:/delta-data/presentation-20260924` is
retained. Access codes, signing keys and controller key directories stay out of
Git and the small snapshot. Do not overwrite live state with the snapshot while
services or jobs are running.

Development continues in the separate `codex/feature000-binding-candidate`
worktree. Upgrade the demonstration only after the replacement has been tested
and its scope is accurately labelled. Preserve these refs for rollback.
