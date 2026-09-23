# Рабочее приложение для показа

Откройте **http://127.0.0.1:8870/**. Интерфейс на русском, все ресурсы локальные.
Основной Controller с полным admin UI: **http://127.0.0.1:8865/**.

## Запуск на подготовленном компьютере

Двойной щелчок по `START.cmd` в этой папке запускает приложение и открывает браузер.
Docker Desktop должен быть запущен для сценария четырёх контроллеров.
Для локального обучения Docker не нужен. Интернет после подготовки среды не нужен.

```powershell
pwsh -NoProfile -File tools/presentation/presentation-start.ps1 start
pwsh -NoProfile -File tools/presentation/presentation-start.ps1 status
pwsh -NoProfile -File tools/presentation/presentation-start.ps1 stop
```

Повторный `start` возвращает адрес уже работающего собственного экземпляра.
`stop` завершает только экземпляры, чьи PID, время старта и instance ID проверены.
При выполняющемся задании остановка отклоняется: дождитесь результата и повторите.
Результаты сохраняются после остановки. Порт 8765 и другие экземпляры не затрагиваются.
При аварийном завершении незаконченный запуск становится `INTERRUPTED`, а не успешным.

## Показ за пять минут

1. **Обзор.** Покажите Controller Online и физическую GPU 8192 MiB.
   Сразу обозначьте режим: локальное приложение и отдельная симуляция инфраструктуры.
2. **Запустить обучение.** Кнопка выдаёт настоящий TRAIN_TICKET существующему Controller.
   Отдельный Python Worker выполняет синтетический tabular plugin на CPU.
   Журнал показывает RUNNING → COMPLETED; приложение проверяет связь
   intent → admission → execution → receipt. Это не анимация и не готовый fixture.
3. **Скачать результат.** JSON содержит IDs, receipt, provenance и измеренную длительность.
   Можно открыть расширенный интерфейс для просмотра существующего каталога/Controller.
4. **Запустить сценарии в Docker.** Создаются четыре процесса с временными тестовыми
   Ed25519 ключами. Будут показаны 4/4, отказ одного (3/4), отказ двух (2/4, блок),
   restart одного (3/4). Офлайн проверяются подписи и отклонение stale generation.
   После выполнения собственные контейнеры и сеть удаляются.
5. **История запусков.** Покажите оба результата. Во вкладке **Готовность Feature010**
   показаны отдельно незакрытые formal/runtime/scientific/WAN gates.

Обучение и Docker — два отдельных запуска. Они не образуют joined scientific lineage.
Длительности зависят от компьютера; значения на экране поступают из реальных процессов.
Синтетический phenotype plugin используется только как программная демонстрация.

## Что работает и где граница

| Часть | Фактическое исполнение |
|---|---|
| Browser → Controller → Worker → receipt | Реальное локальное исполнение baseline |
| Модель/данные демонстрации | nearest-centroid, synthetic-10gene-cohort-v1, CPU |
| Четыре Docker-контроллера | Реальные процессы/тестовые подписи, один администратор |
| Отказы/рестарт | Реальные stop/restart контейнеров и проверка поколения |
| GPU | Физическая видимость через nvidia-smi; обучение этого экрана использует CPU |
| Java/Netty → native C++/WAL | Не запускается этим presentation wrapper |
| Независимые authority и WAN | SIMULATED_LOCAL, Docker internal bridge, без TLS/WAN qualification |
| BenchmarkResultQC / GO checkpoint | Отсутствуют; Feature011 не разблокирована |

Это presentation/tooling, semantic impact **NONE**. Native/core/protocol не изменены.
Baseline использует свою ранее принятую semantics `cc98f15a…`; она не объявляется
authority для новой arithmetic/model-binding семантики. Новый formal-кандидат
показывается как `NO_GO`, пока его обязательные доказательства не закрыты.
T013/T018/T023/T051 и HR010-001 здесь являются связью с tooling-задачами, а не
заявлением об их полном qualifying completion.

## Зафиксированная среда и файлы

- Controller repo: `D:\delta-main-demo`, clean commit
  `c8aea64972f741060d1e527ebbb6f9a5a168a075`.
- Подготовленная `.venv` и `tools/admin-ui/dist-live` находятся в baseline repo.
- Python launcher: `.venv/Scripts/python.exe` из baseline; PowerShell 7 (`pwsh`).
- Docker image: `sha256:cadbe5fced95ccb849fd7ce4f6fb5135cf684f99b5a1b1257fbd9174e985b08a`.
  Runner: `tools/feature010/simulated_local.py` в этом worktree.
- Данные: `D:\delta-data\presentation-20260924`.
- `panel/jobs/*.json`: история и downloadable результаты.
- `panel/simulations/<job-id>/sim-*/`: manifests, signatures, отчёт и cleanup.
- `panel/server.stderr.txt`: диагностика presentation server.
- `controller/working-version.stderr.log`: диагностика Controller/Worker.
- `local-8865.json`: исходный baseline deployment descriptor с локальным портом 8865.

Параметры `-ControllerRepo`, `-DataRoot`, `-FormalReport`, `-ControllerPort`, `-Port`
позволяют сменить пути/порты. Default значения соответствуют подготовленному компьютеру.
Для переноса подготовьте clean checkout указанного baseline, его зависимости и
admin UI по `docs/operations/working-version-runbook.md`, затем импортируйте/соберите проверенный
simulation image по `docs/feature010-simulated-local.md`. Launcher не скачивает
зависимости и не меняет исходники автоматически. Private keys из data-dir не переносите
в репозиторий и не включайте в презентацию.

## Проверки wrapper

```powershell
python -m unittest discover -s tools/presentation -v
uv run --frozen --only-group dev ruff check tools/presentation
uv run --frozen --only-group dev ruff format --check tools/presentation
node --check tools/presentation/static/app.js
```

Проверяются origin/Host, запрет произвольных команд, сериализация запусков,
запрет остановки активного job, блокировка data-dir, отсутствие ложного success
при ошибке receipt, восстановление и non-qualifying граница скачанного результата.
UI отдельно проверен живыми запуском обучения и Docker-сценарием в браузере.

При проблеме сначала выполните `status` и проверьте указанные логи.
Не удаляйте data-dir и не останавливайте чужие процессы для освобождения порта.
Если Docker недоступен, реальное обучение и история доступны; Docker job честно
завершится ошибкой и не покажет успешную симуляцию.
