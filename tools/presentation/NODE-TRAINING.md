# Node training example / Пример обучения узлов

Open **Node training / Обучение узлов** in Admin UI or Presentation.
The page uses the same origin and access code, preserves EN/RU in its navigation,
and adopts the application's light cards, navy navigation and blue/green accents.
Local entry: `http://127.0.0.1:8870/node-training/?lang=en` (or `lang=ru`).
`START-REMOTE.ps1 start` / `restart` prints the current external EN/RU URLs.

For the presentation:

1. Choose EN or RU. A previous verified result is visible immediately if available.
2. Press **Run demo / Запустить демо** to execute a fresh example; wait for 100%.
3. Show the four worker processes, centralized/distributed accuracy and BYTE-EXACT.
4. Switch **All 4 nodes / Все 4 узла** to **Failure and recovery / Сбой и восстановление**.
5. Return to Admin or Presentation through the top navigation.

This is the existing MNIST example from `D:/delta/worktree-c2` (Git root
`D:/delta-worktrees/campaign02-demo-controllers`), not the main Controller workload.
Its runs are deliberately separate from the saved campaigns/executions. Only its
presentation is adapted; source training, native/Java adapters and report validation
are unchanged. No profiles, receipts or evidence are silently converted between them.
The source's existing EN/RU updates are preserved in the
`demo/node-training-2026-09-24` Git snapshot without changing its working checkout.

Scope stays **LOCAL_DEMO_ONLY**. It uses real MNIST and local processes, includes a
synthetic EEG plugin illustration and clearly labels the historical QLoRA reference.
It does not establish real WAN, independent signing custody, scientific Gate B,
Feature010 GO or BenchmarkResultQC.

## Host setup

`presentation-start.ps1 start` also starts the demo, and remote `start` checks it
even when a tunnel is already running. Missing demo prerequisites do not stop the
main Controller/Presentation. Use `node-training-start.ps1 status` to inspect it.

The starter runs the existing `tools/run-mnist-demo.ps1 -PrepareOnly -Offline`
in a hidden, independent Windows process and retains its pinned Java/native environment.
It requires the already prepared source checkout, `.venv`, CMake, JDK/Netty cache and
MNIST cache. It never replaces an unrelated listener. The fixed loopback backend
is 8872; its health/management paths are not published. Only the page, status,
registry catalog and empty run command are proxied, behind authentication and
same-origin checks. Original nonce CSP and run-token validation remain active.
The browser sends exactly `{}` as a JSON envelope; the adapter passes an empty
command to the original runner. This avoids Cloudflare chunking a zero-length POST
without accepting any caller-provided runner arguments.

Data is stored under `D:/delta-data/presentation-20260924/node-training/`:
`runs/` contains original reports/artifacts, `last-view.json` retains the last result,
`host.log` records startup/run errors, and `process.json` pins process ownership.
After restart the saved report is validated before being displayed; opening a page
or switching languages never starts training. Keep private files in `runs/controllers`
and the tunnel access code local. No private keys are exposed by the proxy or committed.

По-русски: откройте «Обучение узлов», нажмите «Запустить демо», дождитесь результата
и переключите сравнение на восстановление после сбоя. Это отдельный локальный пример;
его метрики не подменяют результаты кампаний. После перезагрузки запустите
`D:/delta-presentation/START-REMOTE.ps1 start`: скрипт выведет действующий внешний адрес.
