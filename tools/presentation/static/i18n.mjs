// Presentation text only. Original receipts, IDs and evidence remain unchanged.
const strings = {
  howItWorks: ['How it works', 'Как это работает'],
  sharedProfileNote: ['One local profile for Admin UI and Presentation. Definitions are saved on the application host.', 'Общий локальный профиль Admin UI и Presentation. Настройки сохраняются на компьютере, где запущено приложение.'],
  configureCampaign: ['Configure campaign →', 'Настроить кампанию →'],
  profileUnavailable: ['Local profile unavailable. Saved definitions have not been overwritten.', 'Локальный профиль недоступен. Сохранённые настройки не перезаписаны.'],
  linkedRun: ['LINKED EXECUTION', 'СВЯЗАННЫЙ ЗАПУСК'],
  controllerRun: ['Controller execution', 'Запуск Controller'],
  linkedUnavailable: ['Unable to verify this execution. No result is shown.', 'Не удалось проверить запуск. Результат не показан.'],
  openSameRun: ['Open this run in Admin UI →', 'Открыть этот запуск в Admin UI →'],
  linkedVerified: ['Receipt digest and execution lineage verified. Local execution; no qualifying GO.', 'Хеш receipt и связь с запуском проверены. Локальное выполнение; квалификация GO не получена.'],
  downloadReceipt: ['Download receipt', 'Скачать receipt'],
  documentTitle: ['DeltaReduce · Local Lab', 'DeltaReduce · Локальная лаборатория'],
  workspaceLabel: ['WORKSPACE', 'РАБОЧЕЕ ПРОСТРАНСТВО'],
  workspace: ['Workspace', 'Рабочая область'],
  mainNavigation: ['Main navigation', 'Основная навигация'],
  overview: ['Overview', 'Обзор'],
  runs: ['Run history', 'История запусков'],
  readiness: ['Feature010 readiness', 'Готовность Feature010'],
  localLab: ['Local lab', 'Локальный стенд'],
  singleComputer: ['One computer · SIMULATED_LOCAL', 'Один компьютер · SIMULATED_LOCAL'],
  language: ['Interface language', 'Язык интерфейса'],
  languageHelpLabel: ['Help: Interface language', 'Подсказка: Язык интерфейса'],
  languageHelp: ['Choose the language of labels and help. Identifiers and original evidence remain unchanged. This preference is saved in the shared local profile.', 'Выберите язык интерфейса и подсказок. Идентификаторы и исходные доказательства сохраняют свои значения. Выбор сохраняется в общем локальном профиле.'],
  example: ['Example', 'Пример'],
  overviewEyebrow: ['FROM COMMAND TO VERIFIABLE RESULT', 'ОТ КОМАНДЫ ДО ПРОВЕРЯЕМОГО РЕЗУЛЬТАТА'],
  overviewHeading: ['The system in action', 'Система в действии'],
  overviewDescription: ['Run jobs, test resilience and save the results.', 'Запускайте задания, проверяйте отказоустойчивость и сохраняйте результаты.'],
  advanced: ['Open Admin UI ↗', 'Открыть Admin UI ↗'],
  completedRuns: ['Completed runs', 'Выполнено запусков'],
  lastThirty: ['Of the last 30 local runs', 'Из последних 30 локальных запусков'],
  physicalGpu: ['Physical GPU', 'Физическая GPU'],
  environment: ['Environment', 'Среда'],
  testEnvironment: ['Test signatures · local network', 'Тестовые подписи · локальная сеть'],
  executionKicker: ['01 / LIVE EXECUTION', '01 / ЖИВОЕ ИСПОЛНЕНИЕ'],
  train: ['Run training', 'Запустить обучение'],
  trainingDescription: ['A real job through the HTTP Controller and a separate Python Worker.', 'Реальное задание через HTTP Controller и отдельный Python Worker.'],
  classifier: ['Nearest-centroid classifier', 'Классификатор по ближайшему центроиду'],
  dataset: ['Dataset', 'Датасет'],
  datasetName: ['Synthetic 10-gene cohort', 'Синтетический 10-gene cohort'],
  execution: ['Execution', 'Исполнение'],
  executionScope: ['Local training · PLUGIN_BOUNDARY', 'Локальное обучение · PLUGIN_BOUNDARY'],
  result: ['Result', 'Результат'],
  receiptDescription: ['Verifiable execution receipt', 'Проверяемый execution receipt'],
  trainingBoundary: ['Measured local plugin execution; this run does not qualify scientific Gate B.', 'Измеренный результат локального плагина; scientific Gate B этим запуском не закрывается.'],
  simulationKicker: ['02 / FAILURE SIMULATION', '02 / СИМУЛЯЦИЯ ОТКАЗОВ'],
  quorumHeading: ['Test the quorum', 'Проверить кворум'],
  simulationDescription: ['Four Docker processes. Real test signatures. Controlled failures.', 'Четыре Docker-процесса. Реальные тестовые подписи. Управляемые отказы.'],
  fourControllers: ['Four controllers', 'Четыре контроллера'],
  scenarioOnline: ['4/4 online', '4/4 в сети'],
  scenarioQuorum: ['3/4 quorum', '3/4 кворум'],
  scenarioBlocked: ['2/4 blocked', '2/4 блок'],
  scenarioRestart: ['restart', 'рестарт'],
  simulate: ['Run Docker scenarios', 'Запустить сценарии в Docker'],
  simulationBoundary: ['One host and one administrator. Signatures are not independent; a Docker bridge is not a real WAN.', 'Один хост и один администратор. Подписи не независимы; Docker bridge не является real WAN.'],
  activity: ['Execution log', 'Журнал выполнения'],
  activityDescription: ['Events from the actual process, without generated metrics.', 'События реального процесса, без сгенерированных метрик.'],
  emptyTitle: ['Ready for your first run', 'Готово к первому запуску'],
  emptyDescription: ['Choose training or a Docker scenario above.', 'Выберите обучение или Docker-сценарий выше.'],
  footerBoundary: ['Local mode · Feature010 GO has not been issued', 'Локальный режим · Feature010 GO не выдан'],
  historyEyebrow: ['EXECUTION HISTORY', 'ИСТОРИЯ ВЫПОЛНЕНИЯ'],
  historyDescription: ['Results are saved on disk and remain available after restarting the interface.', 'Результаты сохранены на диске и доступны после перезапуска интерфейса.'],
  readinessEyebrow: ['EVIDENCE & QUALIFICATION', 'ДОКАЗАТЕЛЬСТВА И КВАЛИФИКАЦИЯ'],
  readinessDescription: ['The working local application and the status of full qualification.', 'Работающее локальное приложение и статус полной квалификации.'],
  inDevelopment: ['IN DEVELOPMENT', 'В РАЗРАБОТКЕ'],
  noGo: ['BenchmarkResultQC(GO) has not been obtained', 'BenchmarkResultQC(GO) ещё не получен'],
  readinessBoundary: ['This demo runs the existing local Controller/Worker and separate Docker scenarios. The full Java/Netty → native C++/WAL → checkpoint pipeline depends on a new Formal GO.', 'Демонстрация запускает существующий локальный Controller/Worker и отдельные Docker-сценарии. Полная цепочка Java/Netty → native C++/WAL → checkpoint зависит от нового Formal GO.'],
  formalReport: ['Reviewed formal candidate report', 'Проверенный отчёт formal-кандидата'],
  download: ['Download result ↓', 'Скачать результат ↓'],
  QUEUED: ['Queued', 'В очереди'], RUNNING: ['Running', 'Выполняется'], COMPLETED: ['Completed', 'Завершено'],
  FAILED: ['Failed', 'Ошибка'], INTERRUPTED: ['Interrupted', 'Прервано'], CANCELLED: ['Cancelled', 'Отменено'], TIMED_OUT: ['Timed out', 'Время истекло'],
  trainingTitle: ['Training · 10-Gene Phenotype', 'Обучение · 10-Gene Phenotype'],
  controllersTitle: ['Docker · controllers and quorum', 'Docker · контроллеры и кворум'],
  live: ['● RUNNING', '● ВЫПОЛНЯЕТСЯ'], idle: ['IDLE', 'ОЖИДАНИЕ'], error: ['ERROR', 'ОШИБКА'],
  trainingSuccess: ['✓ Training completed · receipt verified', '✓ Обучение завершено · receipt проверен'],
  simulationSuccess: ['✓ Docker scenarios and offline verification passed', '✓ Docker-сценарии и офлайн-проверка пройдены'],
  seconds: ['s', 'с'], allOnline: ['All online', 'Все в сети'], oneLost: ['One failure', 'Один отказ'],
  twoLost: ['Two failures', 'Два отказа'], restarted: ['After restart', 'После рестарта'], quorum: ['quorum', 'кворум'], blocked: ['blocked', 'блок'],
  localApplication: ['Local application', 'Локальное приложение'], working: ['Running', 'Работает'],
  unavailable: ['Unavailable', 'Недоступно'], dockerControllers: ['Docker controllers', 'Docker-контроллеры'],
  dockerGateDescription: ['Test Ed25519 signatures, quorum loss and generation changes', 'Тестовые Ed25519 подписи, потеря кворума, смена поколения'],
  formalGateDescription: ['Arithmetic/model binding; required proofs and refinement', 'Arithmetic/model binding; обязательные доказательства и refinement'],
  dependsFormal: ['Requires Formal GO', 'Зависит от Formal GO'],
  gateA: ['Gate A · safety', 'Gate A · безопасность'],
  gateADescription: ['Full processes and mandatory runtime checks', 'Полные процессы и mandatory runtime проверки'],
  notQualified: ['Not qualified', 'Не квалифицирован'],
  gateB: ['Gate B · scientific quality', 'Gate B · scientific quality'],
  gateBDescription: ['Physical GPU, frozen real models/data and joined lineage', 'Физическая GPU, реальные frozen модели/данные и joined lineage'],
  gateNetwork: ['Gate C / D · network', 'Gate C / D · сеть'],
  gateNetworkDescription: ['Simulated WAN separated from approved real WAN', 'Simulated WAN отдельно от approved real WAN'],
  resultQcDescription: ['All mandatory gates and evaluator quorum', 'Все mandatory gates и evaluator quorum'],
  absent: ['Absent', 'Отсутствуют'], online: ['Online', 'В сети'], checking: ['Checking…', 'Проверяем…'],
  checkingHttp: ['Checking HTTP readiness', 'Проверка HTTP readiness'], readingGpu: ['Reading nvidia-smi', 'Чтение nvidia-smi'],
  startServer: ['Run presentation-start.ps1', 'Запустите presentation-start.ps1'],
  gpuScope: ['Device visibility; training here uses CPU', 'Видимость устройства; обучение здесь использует CPU'],
  disconnected: ['Disconnected', 'Нет связи'],
  connectionError: ['Connection lost: {error}. Check that the server is running.', 'Связь с приложением прервана: {error}. Проверьте, что сервер запущен.'],
  eventSubmit: ['Submitting TRAIN_TICKET to the existing HTTP Controller.', 'Отправка TRAIN_TICKET в существующий HTTP Controller.'],
  eventAccepted: ['Controller accepted job {id}.', 'Controller принял задание {id}.'],
  eventWorker: ['Python Worker: {state}.', 'Python Worker: {state}.'],
  eventLineage: ['Verified intent → admission → execution → receipt lineage.', 'Проверена связь intent → admission → execution → receipt.'],
  eventDocker: ['Starting four Docker controllers with ephemeral Ed25519 test keys.', 'Запуск четырёх Docker-контроллеров с временными Ed25519 test keys.'],
  eventManifest: ['Recorded source/image IDs and GPU visibility in Docker.', 'Зафиксированы source/image IDs и видимость GPU в Docker.'],
  eventAll: ['4/4 controllers: signatures collected.', '4/4 контроллера: подписи собраны.'],
  eventOne: ['One controller stopped: 3/4, quorum retained.', 'Один контроллер остановлен: 3/4, кворум сохранён.'],
  eventTwo: ['Two controllers stopped: 2/4, no quorum.', 'Два контроллера остановлены: 2/4, кворума нет.'],
  eventRestart: ['Controller restarted; generation and test key changed.', 'Контроллер перезапущен; поколение и test key изменены.'],
  eventVerified: ['Offline signature verification passed; containers from this run were removed.', 'Офлайн-проверка подписей пройдена; контейнеры этого запуска удалены.'],
  eventComplete: ['Run completed. Result saved on disk.', 'Запуск завершён. Результат сохранён на диск.'],
  eventFailed: ['Execution stopped with an error; no successful result was created.', 'Выполнение остановлено с ошибкой; успешный результат не создан.'],
  busyError: ['Wait for the current run to finish.', 'Дождитесь завершения текущего запуска.'],
  interruptedError: ['The interface was restarted; completion is unconfirmed.', 'Интерфейс был перезапущен; завершение не подтверждено.'],
  timeoutError: ['Timed out waiting for the Controller; success is unconfirmed.', 'Истёк срок ожидания Controller; успех не подтверждён.'],
  terminalError: ['Controller finished the job with status {state}', 'Controller завершил задание со статусом {state}'],
};

export const messages = Object.fromEntries(['en', 'ru'].map((language, index) =>
  [language, Object.fromEntries(Object.entries(strings).map(([key, values]) => [key, values[index]]))]));
export const locales = {en: 'en-GB', ru: 'ru-RU'};
export function supportedLanguage(value) { return Object.hasOwn(messages, value); }
export function translate(language, key, parameters = {}) {
  const template = messages[language]?.[key] ?? messages.en[key] ?? key;
  return template.replace(/\{(\w+)\}/g, (match, name) => parameters[name] ?? match);
}

// Legacy evidence stores human-readable messages in Russian. Match only known
// messages; retain unknown diagnostics verbatim instead of inventing a translation.
const logKeys = Object.keys(strings).filter((key) => key.startsWith('event') || key.endsWith('Error'));
const legacyMessages = new Map(logKeys.filter((key) => !messages.ru[key].includes('{')).map((key) => [messages.ru[key], key]));
export function translateLog(language, message) {
  if (legacyMessages.has(message)) return translate(language, legacyMessages.get(message));
  let match = /^Controller принял задание ([0-9a-f-]+)\.$/.exec(message);
  if (match) return translate(language, 'eventAccepted', {id: match[1]});
  match = /^Python Worker: ([A-Z_]+)\.$/.exec(message);
  if (match) return translate(language, 'eventWorker', {state: translate(language, match[1])});
  match = /^Controller завершил задание со статусом ([A-Z_]+)$/.exec(message);
  if (match) return translate(language, 'terminalError', {state: translate(language, match[1])});
  return message;
}
