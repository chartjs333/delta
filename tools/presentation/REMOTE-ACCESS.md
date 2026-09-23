# Remote presentation / Удалённый показ

Run on the prepared **host computer** / Запускайте на подготовленном основном ПК:

```powershell
pwsh -NoProfile -File D:\delta-presentation\START-REMOTE.ps1
```

Or double-click `D:\delta-presentation\START-REMOTE.cmd`. The window stays open
so you can copy the current URL and access code. Use the printed HTTPS URL in
the browser on your presentation computer; nothing needs installing there.

Или дважды щёлкните `START-REMOTE.cmd`: окно останется открытым для копирования
адреса и кода. На компьютере для показа откройте выведенный HTTPS URL в браузере.
На нём ничего устанавливать не нужно. На странице входа выберите English/Русский.

The launcher starts the existing local app if necessary, starts one authenticated
gateway and one Cloudflare Quick Tunnel, waits for connection, then checks the
public login page before printing **Presentation EN/RU, Admin UI EN/RU, SDK
and Visual guide EN/RU**.
Repeating `start` reuses the verified process and prints its current address.
After a reboot or tunnel stop, run it again: the new address replaces the old one.
This is a manual restart launcher; it does not install a Windows startup service.

Скрипт запускает локальное приложение, защищённый шлюз и Cloudflare Quick Tunnel.
Адрес появляется только после подключения и проверки внешней страницы входа.
Повторный `start` показывает адрес работающего экземпляра. После перезагрузки или
остановки туннеля запустите скрипт снова: он получит и сохранит новый адрес.
Автоматическая служба при старте Windows не устанавливается.

```powershell
pwsh -NoProfile -File D:\delta-presentation\START-REMOTE.ps1 status
pwsh -NoProfile -File D:\delta-presentation\START-REMOTE.ps1 stop
```

`status` verifies the live process and external login before displaying a URL.
`stop` closes remote access only: local Presentation/Controller and saved data
remain available. Stopped/dead processes never cause an old URL to be advertised
by the launcher. `current-url.txt` is the last verified address, not a live monitor;
run `status` to check it after an unexpected crash.

`status` проверяет процесс и внешний вход; `stop` закрывает только удалённый доступ.
Локальные приложения и сохранённые данные остаются. При аварии файл URL может
содержать последний проверенный адрес — команда `status` проверит его заново.

If the host resolver returns NXDOMAIN for a new hostname, the launcher can verify
HTTPS using that hostname's A record from Cloudflare public DNS. TLS hostname and
certificate checks remain enabled. It prints a DNS note in this case; system DNS
and the hosts file are not changed. A browser on the same failing resolver may
still be unable to open the URL. Retry later or use another network that resolves
the hostname; this fallback is verification, not a browser DNS reconfiguration.

Если DNS текущей сети не разрешает новый адрес, скрипт проверяет HTTPS по записи
публичного DNS Cloudflare с проверкой имени и сертификата и выводит предупреждение.
DNS Windows и hosts не меняются. Браузер с тем же неисправным DNS может не открыть
ссылку: повторите позже или используйте сеть, где разрешается этот адрес.

Files / Файлы в `D:\delta-data\presentation-20260924\tunnel`:

- `current-url.txt` — last verified public URL / последний проверенный внешний URL.
- `access-code.txt` — persistent random access code / сохраняемый случайный код входа.
- `gateway.stderr.txt`, `cloudflared.log` — connection diagnostics / диагностика.
- `control.json`, `process.json` — private launcher metadata; do not share them.

Keep the host powered on, plugged into power and connected to the Internet.
The gateway requests Windows to prevent automatic idle sleep while running;
manual sleep, shutdown, lid policy, lost connectivity and reboot still interrupt
the presentation. Docker scenarios also require Docker Desktop to be ready.

Оставьте основной ПК включённым, подключённым к питанию и Интернету. Во время
работы шлюз запрашивает запрет автоматического сна от бездействия, но ручной сон,
закрытие крышки согласно настройкам Windows и перезагрузка прерывают показ.
Для Docker-сценария должен работать Docker Desktop.

## Shared app and access boundary

`Cloudflare HTTPS → 127.0.0.1:8871 authenticated gateway → Presentation/Admin 8870
→ baseline Controller/Worker 8865`. All navigation and API calls stay on the
public origin. EN/RU, profile, campaign/workload selection, execution status and
receipt are the same local application data. A remote visitor with the code
can edit the shared profile and run supported demo jobs: give it only to your
audience. This is one shared presentation code, not individual user accounts,
independent authority custody, or a production identity system.

Внешний и локальный интерфейсы используют один профиль, кампании и результаты.
Получатель кода может менять профиль и запускать разрешённые демонстрационные
задания. Это общий код презентации; индивидуальные учётные записи добавляются позже.

Remote requests require a signed, expiring Secure/HttpOnly/SameSite cookie;
credentials are not in URLs or JavaScript. Writes require the exact public
Origin and existing action headers. Only fixed existing application routes are
forwarded. Shutdown and gateway controls are unavailable remotely. Local
passwordless access stays unchanged. Codes/control metadata are outside Git,
in an ACL-restricted directory. Sessions expire after 12 hours or gateway restart.
To rotate a code: stop the tunnel, remove only `access-code.txt`, then start again.

The login document uses `Referrer-Policy: same-origin`: browser form submissions
must retain their real Origin. `no-referrer` can turn that Origin into `null`,
causing ORIGIN_FORBIDDEN even with the correct code. Null/missing/cross-site
origins remain rejected. Other gateway responses retain `no-referrer`.
If an older login page is already open after an update, reopen the current URL
printed by the launcher before entering the code.

Если после ввода кода появляется `ORIGIN_FORBIDDEN`, заново откройте актуальную
ссылку из `START-REMOTE.ps1`, чтобы загрузить исправленную форму входа. Код
не меняется. Форма сохраняет Origin своего сайта; проверка чужих адресов остаётся.

Quick Tunnels are for temporary development/testing, use a random hostname,
have no uptime SLA, permit at most 200 concurrent in-flight requests and do not
support SSE. This app polls for status. Cloudflare docs:
[Quick Tunnels](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/).

This connection enables remote UI access only. It is **not Gate D WAN evidence**,
an independent controller authority, or a Feature010 qualification. Demo mode
remains **SIMULATED_LOCAL**, with no BenchmarkResultQC or GO checkpoint.

## Implementation / self-review scope

T051 / HR010-001; pre-implementation Constitution Check: presentation tooling,
formal impact NONE. Existing accepted baseline GO report verifies; no changed
consensus transition, arithmetic, canonical vote, state, authority or durability
rule is implemented here. All protocol/runtime sources remain unchanged.
The SDK page documents the existing reviewed Python plugin contracts and ships
a runnable teaching example; it does not dynamically install plugins.

Checks cover authentication, tampered/expired sessions, origin enforcement,
forbidden/private routes, bounded inputs, credential stripping, bilingual login,
remote-safe links, SDK language state and exact downloadable example contents.
Public HTTPS execution, local browser and tunnel restart evidence is recorded under
`specs/010-wan-benchmark-and-quality/evidence/presentation-local/20260924/remote-sdk/`.
This is self-review, not an independent attestation.
