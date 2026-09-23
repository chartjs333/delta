import { useState } from "react";
import { useLanguage } from "../../i18n";
import example from "./sdk_plugin_example.py?raw";
import "./sdk.css";

const baseline = "c8aea64972f741060d1e527ebbb6f9a5a168a075";
const root = `https://github.com/chartjs333/delta/blob/${baseline}/`;
const sections = ["start", "dataset", "model", "register", "reference"] as const;
type Section = typeof sections[number];
const en = {
  title: "Build your first plugin", eyebrow: "DEVELOPER SDK", intro: "Bring your own model and data. Start with a small Python example, understand the contracts, then integrate a reviewed plugin into your deployment.",
  start: "Quick start", dataset: "Dataset provider", model: "Model plugin", register: "Register & test", reference: "API reference",
  download: "Download full example", copy: "Copy code", copied: "Copied", failed: "Copy unavailable. Select the code or download the example.", source: "Source contracts", version: "Documented baseline", language: "Descriptions follow your selected language. Python names and code stay identical.",
  overview: "A complete, runnable example", overviewText: "Two classes, one feature and a nearest-centroid classifier. Four points are used for training and four different points for evaluation. The example uses the real registries and ModelPluginRunner on your CPU.",
  dataCard: "1. Provide the data", dataBody: "Own the dataset identity, fixed partitions, validation and evaluation split.", modelCard: "2. Implement the model", modelBody: "Declare tensor shapes and order; implement local training and evaluation.", runCard: "3. Bind and run", runBody: "Register factories, check compatible tags and run one local ticket.",
  setup: "Run it locally", setupText: "Use Python 3.12 and the repository's locked Worker environment. Save the downloaded file in the repository root, then run these commands there. Initial setup may download the locked dependencies.",
  expected: "Expected tutorial output", outputNote: "1,000,000 ppm means 100% on these four synthetic evaluation points. This is an API demonstration, not a scientific quality result. No HTTP Controller, Java transport, native WAL or consensus checkpoint is produced.",
  datasetIntro: "Implement DatasetProvider", datasetText: "Return a stable descriptor without loading data. materialize validates or prepares the source; honor allow_download for any network access. training_partition must return the exact requested partition and evaluation_data must use a separate evaluation split.",
  datasetDetail: "Here the data is embedded in the file, so materialize does not need disk or network access. An unknown partition is rejected. Real providers should bind immutable source content, licenses, split identity and partition metadata.",
  modelIntro: "Implement ModelPlugin", modelText: "Keep tensor names, shapes and order stable. Return a LocalTrainingResult from train_ticket and measured metrics from evaluate. The generic runtime handles the protocol boundary; the plugin owns its local model computation.",
  modelDetail: "This teaching model computes fresh class centroids. It rejects parent updates and advertises supports_stage_c_real_drq1=False. Its scale-1 integer decoder illustrates the interface only; it is not a production Apply arithmetic profile.",
  imports: "Imports used by the example", fragment: "The snippets below are parts of the same file. Download the complete file to run them together.",
  registerIntro: "Register explicit factories", registerText: "Register a descriptor and factory in ModelPluginRegistry and DatasetRegistry, then pass those registries to ModelPluginRunner. sample_kind and target_kind must match exactly. Constructors should be lightweight: registration instantiates a factory to validate its contract.",
  tests: "Checks before integration", test1: "Run training twice on the same fixed partition; compare tensor names, shapes, values and metadata.", test2: "Reject wrong tags, unknown partitions, malformed shapes, invalid labels, non-finite values and unsupported execution scopes.", test3: "Verify schema fingerprint, tensor order, total element count and checkpoint decode/encode rules. A descriptor capability is not execution evidence.", test4: "Evaluate a separate split and keep the dataset, model, environment and result identities together.",
  deploy: "Make a reviewed plugin available in Admin UI", deployText: "The tutorial uses private in-process registries. It does not install into the running Controller. Integration requires an explicit code change and deployment:",
  deploy1: "Register reviewed factories in the Worker registries and update the deployment's allowed model/dataset IDs and scopes.", deploy2: "Add matching descriptors under tools/registry/plugins and tools/registry/datasets; bind the catalog provenance to the reviewed source. Regenerate the catalog and rebuild Admin UI.", deploy3: "Run contract, negative and execution tests before deployment. Update the local profile's supported workload policy deliberately; the current presentation only enables the 10-gene example.",
  referenceIntro: "Contracts at a glance", member: "Member", purpose: "Responsibility", external: "External analysis plugins", externalText: "The separate DeltaPlugin protocol exposes metadata(), health() and analyze(request). It does not replace ModelPlugin or DatasetProvider. Use validate_plugin_manifest and validate_analyze_response; return ABSTAIN or PLUGIN_INCOMPATIBLE when evidence or compatibility is missing. Manifest validation checks structure; it does not authorize dynamic code loading.",
  boundary: "Local development example", boundaryText: "The SDK page documents existing Python contracts. It does not change protocol semantics or enable Stage C, Feature010 GO or production plugin loading from the browser.", browse: "Browse workload catalog →",
};
const ru: typeof en = {
  title: "Создайте свой первый плагин", eyebrow: "SDK ДЛЯ РАЗРАБОТЧИКОВ", intro: "Подключите свою модель и данные. Начните с небольшого примера на Python, изучите контракты, затем добавьте проверенный плагин в свою сборку.",
  start: "Быстрый старт", dataset: "Источник данных", model: "Плагин модели", register: "Регистрация и тесты", reference: "Справочник API",
  download: "Скачать полный пример", copy: "Копировать код", copied: "Скопировано", failed: "Копирование недоступно. Выделите код или скачайте пример.", source: "Исходные контракты", version: "Описанная версия", language: "Описания используют выбранный язык. Имена Python и код остаются одинаковыми.",
  overview: "Полный запускаемый пример", overviewText: "Два класса, один признак и классификатор по ближайшему центроиду. Четыре точки используются для обучения, четыре другие — для оценки. Пример использует реальные реестры и ModelPluginRunner на CPU.",
  dataCard: "1. Подготовьте данные", dataBody: "Определите идентификатор набора, фиксированные части, проверку данных и выборку для оценки.", modelCard: "2. Реализуйте модель", modelBody: "Объявите формы и порядок тензоров, реализуйте локальное обучение и оценку.", runCard: "3. Свяжите и запустите", runBody: "Зарегистрируйте фабрики, проверьте совместимость типов и выполните одну локальную заявку.",
  setup: "Запустите локально", setupText: "Используйте Python 3.12 и зафиксированную среду Worker из репозитория. Сохраните скачанный файл в корень репозитория и выполните там команды ниже. При первой подготовке могут загружаться зафиксированные зависимости.",
  expected: "Ожидаемый вывод примера", outputNote: "1 000 000 ppm означает 100% на этих четырёх синтетических точках оценки. Это демонстрация API, а не научный результат. HTTP Controller, Java, native WAL и консенсусная контрольная точка здесь не используются.",
  datasetIntro: "Реализуйте DatasetProvider", datasetText: "Возвращайте стабильный дескриптор без загрузки данных. materialize проверяет или подготавливает источник; для сетевой загрузки учитывайте allow_download. training_partition должен возвращать именно запрошенную часть, а evaluation_data — отдельную выборку для оценки.",
  datasetDetail: "В этом примере данные встроены в файл, поэтому materialize не обращается к диску или сети. Неизвестная часть отклоняется. В реальном источнике фиксируйте содержимое, лицензии, разбиение и метаданные частей.",
  modelIntro: "Реализуйте ModelPlugin", modelText: "Сохраняйте стабильные имена, формы и порядок тензоров. train_ticket возвращает LocalTrainingResult, а evaluate — измеренные метрики. Общая среда управляет границей протокола, плагин — локальными вычислениями модели.",
  modelDetail: "Учебная модель вычисляет новые центроиды классов. Она отклоняет обновления родительской модели и объявляет supports_stage_c_real_drq1=False. Декодер целых координат с масштабом 1 иллюстрирует интерфейс и не является рабочим профилем арифметики Apply.",
  imports: "Импорты примера", fragment: "Фрагменты ниже — части одного файла. Чтобы выполнить их вместе, скачайте полный файл.",
  registerIntro: "Зарегистрируйте явные фабрики", registerText: "Зарегистрируйте дескриптор и фабрику в ModelPluginRegistry и DatasetRegistry, затем передайте реестры в ModelPluginRunner. sample_kind и target_kind должны совпадать точно. Конструкторы должны быть лёгкими: регистрация создаёт экземпляр для проверки контракта.",
  tests: "Проверки перед интеграцией", test1: "Дважды выполните обучение на одной фиксированной части; сравните имена, формы, значения тензоров и метаданные.", test2: "Отклоняйте несовместимые типы, неизвестные части, неверные формы, недопустимые метки, нечисловые значения и неподдерживаемые режимы.", test3: "Проверьте хеш схемы, порядок тензоров, число элементов и правила кодирования и декодирования контрольной точки. Возможность в дескрипторе не является доказательством выполнения.", test4: "Оценивайте отдельную выборку и сохраняйте связь идентификаторов данных, модели, среды и результата.",
  deploy: "Сделайте проверенный плагин доступным в Admin UI", deployText: "Пример использует собственные реестры внутри процесса. Он не устанавливает плагин в работающий Controller. Интеграция требует явного изменения кода и развёртывания:",
  deploy1: "Зарегистрируйте проверенные фабрики в реестрах Worker и обновите разрешённые идентификаторы моделей, данных и режимов в конфигурации развёртывания.", deploy2: "Добавьте соответствующие дескрипторы в tools/registry/plugins и tools/registry/datasets; свяжите происхождение каталога с проверенным кодом. Обновите каталог и пересоберите Admin UI.", deploy3: "Перед развёртыванием выполните контрактные, негативные и исполнительные тесты. Явно обновите политику допустимых задач локального профиля: сейчас презентация разрешает только пример с 10 признаками.",
  referenceIntro: "Краткий справочник контрактов", member: "Член интерфейса", purpose: "Назначение", external: "Внешние плагины анализа", externalText: "Отдельный протокол DeltaPlugin предоставляет metadata(), health() и analyze(request). Он не заменяет ModelPlugin или DatasetProvider. Используйте validate_plugin_manifest и validate_analyze_response; возвращайте ABSTAIN или PLUGIN_INCOMPATIBLE при нехватке доказательств или совместимости. Проверка манифеста проверяет структуру и не разрешает динамическую загрузку кода.",
  boundary: "Пример локальной разработки", boundaryText: "Страница SDK описывает существующие контракты Python. Она не меняет семантику протокола, не включает Stage C, Feature010 GO или загрузку рабочего плагина через браузер.", browse: "Открыть каталог задач →",
};

const modelApi = [
  ["plugin_id", "Stable model identity; must match the descriptor.", "Стабильный ID модели; должен совпадать с дескриптором."],
  ["parameter_schema()", "Canonical ParameterSchema with sorted names, shapes and logical dtypes.", "Каноническая ParameterSchema с упорядоченными именами, формами и логическими типами."],
  ["tensor_order / total_elements", "Exact tensor order and total scalar count.", "Точный порядок тензоров и суммарное число скаляров."],
  ["create_model(state=None)", "Create a model, optionally from validated state.", "Создать модель, при необходимости из проверенного состояния."],
  ["train_ticket(*, ticket_id, data, parent_model=None, **kwargs)", "Perform local work and return tensors plus metadata.", "Выполнить локальную работу и вернуть тензоры с метаданными."],
  ["load_applied_checkpoint(values, parent_model=None)", "Decode compatible integer coordinates; validate shape and bounds.", "Декодировать совместимые целые координаты, проверить форму и границы."],
  ["evaluate(model, test_data)", "Return accuracy_ppm, optional loss and measured metrics.", "Вернуть accuracy_ppm, необязательный loss и измеренные метрики."],
];
const datasetApi = [
  ["dataset_id / descriptor()", "Immutable identity and matching sample_kind / target_kind.", "Неизменяемый ID и совместимые sample_kind / target_kind."],
  ["materialize(cache_dir, *, allow_download)", "Validate/cache data; respect the download policy.", "Проверить или кэшировать данные с учётом политики загрузки."],
  ["training_partition(partition_id)", "Return DataPartition: samples, targets, ID and metadata.", "Вернуть DataPartition: данные, метки, ID и метаданные."],
  ["evaluation_data()", "Return the held-out samples and targets tuple.", "Вернуть пару данных и меток отдельной выборки для оценки."],
];
const commands = "uv sync --frozen --package deltatorrent-worker\nuv run --frozen --package deltatorrent-worker python sdk_plugin_example.py";
const expected = '{"accuracy_ppm": 1000000, "centroids": [-3.0, 3.0], "consensus_executed": false, "evaluated_samples": 4, "scope": "LOCAL_SDK_EXAMPLE"}';
const snippets = {
  imports: example.split("# --- DATASET ---")[0].trim(),
  dataset: example.split("# --- DATASET ---")[1].split("# --- MODEL ---")[0].trim(),
  model: example.split("# --- MODEL ---")[1].split("# --- REGISTER AND RUN ---")[0].trim(),
  register: example.split("# --- REGISTER AND RUN ---")[1].trim(),
};

function CodeBlock({ code, label }: { code: string; label: string }) {
  const language = useLanguage();
  const copy = language === "ru" ? ru : en;
  const [state, setState] = useState<"idle" | "copied" | "failed">("idle");
  async function copyCode() {
    try { await navigator.clipboard.writeText(code); setState("copied"); }
    catch { setState("failed"); }
  }
  return <div className="sdk-code"><div className="sdk-code-toolbar"><span>{label}</span><button type="button" onClick={() => void copyCode()}>{state === "copied" ? copy.copied : copy.copy}</button></div>
    <pre tabIndex={0} aria-label={label}><code>{code}</code></pre>
    {state === "failed" ? <p role="status">{copy.failed}</p> : null}</div>;
}

export function SdkPage() {
  const language = useLanguage();
  const copy = language === "ru" ? ru : en;
  const [section, setSection] = useState<Section>("start");
  function download() {
    const url = URL.createObjectURL(new Blob([example], { type: "text/x-python;charset=utf-8" }));
    const link = document.createElement("a"); link.href = url; link.download = "sdk_plugin_example.py"; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function apiTable(title: string, rows: string[][]) {
    return <div className="sdk-api"><h3>{title}</h3><table><thead><tr><th>{copy.member}</th><th>{copy.purpose}</th></tr></thead><tbody>
      {rows.map(row => <tr key={row[0]}><td><code>{row[0]}</code></td><td>{row[language === "ru" ? 2 : 1]}</td></tr>)}
    </tbody></table></div>;
  }
  return <article className="sdk-page" aria-labelledby="sdk-heading">
    <header className="sdk-hero"><div><p className="eyebrow">{copy.eyebrow}</p><h1 id="sdk-heading">{copy.title}</h1><p>{copy.intro}</p></div>
      <div className="sdk-hero-actions"><span className="sdk-badge">Python 3.12 · CPU</span><button className="primary" type="button" onClick={download}>{copy.download} ↓</button></div></header>
    <nav className="sdk-tabs" aria-label={language === "ru" ? "Разделы SDK" : "SDK sections"}>
      {sections.map(key => <button key={key} type="button" aria-pressed={section === key} onClick={() => setSection(key)}>{copy[key]}</button>)}
    </nav>
    <section className="sdk-content" aria-label={copy[section]}>
      {section === "start" ? <><h2>{copy.overview}</h2><p>{copy.overviewText}</p>
        <div className="sdk-flow">{[[copy.dataCard, copy.dataBody], [copy.modelCard, copy.modelBody], [copy.runCard, copy.runBody]].map(([title, body]) => <div key={title}><h3>{title}</h3><p>{body}</p></div>)}</div>
        <h3>{copy.setup}</h3><p>{copy.setupText}</p><CodeBlock code={commands} label={language === "ru" ? "Терминал · корень репозитория" : "Terminal · repository root"} />
        <h3>{copy.expected}</h3><CodeBlock code={expected} label="JSON" /><p>{copy.outputNote}</p></> : null}
      {section === "dataset" ? <><h2>{copy.datasetIntro}</h2><p>{copy.datasetText}</p><p className="sdk-note">{copy.fragment}</p>
        <details><summary>{copy.imports}</summary><CodeBlock code={snippets.imports} label="Python" /></details><CodeBlock code={snippets.dataset} label="sdk_plugin_example.py · DatasetProvider" /><p>{copy.datasetDetail}</p>{apiTable("DatasetProvider", datasetApi)}</> : null}
      {section === "model" ? <><h2>{copy.modelIntro}</h2><p>{copy.modelText}</p><p className="sdk-note">{copy.modelDetail}</p>
        <CodeBlock code={snippets.model} label="sdk_plugin_example.py · ModelPlugin" />{apiTable("ModelPlugin", modelApi)}</> : null}
      {section === "register" ? <><h2>{copy.registerIntro}</h2><p>{copy.registerText}</p><CodeBlock code={snippets.register} label="sdk_plugin_example.py · ModelPluginRunner" />
        <h3>{copy.tests}</h3><ul>{[copy.test1, copy.test2, copy.test3, copy.test4].map(text => <li key={text}>{text}</li>)}</ul>
        <h3>{copy.deploy}</h3><p>{copy.deployText}</p><ol>{[copy.deploy1, copy.deploy2, copy.deploy3].map(text => <li key={text}>{text}</li>)}</ol>
        <CodeBlock code="npm --prefix tools/admin-ui run generate:catalog\nnpm --prefix tools/admin-ui run check" label={language === "ru" ? "После проверки регистрации и дескрипторов" : "After reviewing registration and descriptors"} />
        <a href="#/workloads">{copy.browse}</a></> : null}
      {section === "reference" ? <><h2>{copy.referenceIntro}</h2>{apiTable("ModelPlugin", modelApi)}{apiTable("DatasetProvider", datasetApi)}
        <h3>{copy.external}</h3><p>{copy.externalText}</p></> : null}
    </section>
    <aside className="sdk-boundary"><strong>{copy.boundary}</strong><p>{copy.boundaryText}</p></aside>
    <footer className="sdk-sources"><strong>{copy.source}</strong><p>{copy.version}: <code>{baseline.slice(0, 12)}</code> · {copy.language}</p>
      {[['ModelPlugin', 'model_plugins/base.py'], ['DatasetProvider', 'data/base.py'], ['ModelPluginRunner', 'model_plugins/runner.py'], ['DeltaPlugin', 'plugins/contract.py']].map(([name, path]) => <a key={name} href={`${root}delta-worker-python/src/deltatorrent/${path}`} target="_blank" rel="noopener noreferrer">{name} ↗</a>)}</footer>
  </article>;
}
