const $ = (id) => document.getElementById(id);
const titles = {overview: "Обзор", runs: "История запусков", readiness: "Готовность Feature010"};
const stateNames = {QUEUED: "В очереди", RUNNING: "Выполняется", COMPLETED: "Завершено", FAILED: "Ошибка", INTERRUPTED: "Прервано"};
let current = null;
let requested = false;
let refreshing = false;
let connectionFailed = false;
let lastSignature = "";
const el = (tag, text, cls) => { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; if (cls) node.className = cls; return node; };
function navigate(page) {
  if (!(page in titles)) page = "overview";
  for (const name of Object.keys(titles)) $(`page-${name}`).hidden = name !== page;
  document.querySelectorAll(".nav").forEach((button) => button.classList.toggle("active", button.dataset.page === page));
  $("page-title").textContent = titles[page];
  location.hash = page;
}
document.querySelectorAll(".nav").forEach((button) => button.addEventListener("click", () => navigate(button.dataset.page)));
window.addEventListener("hashchange", () => navigate(location.hash.slice(1)));
navigate(location.hash.slice(1) || "overview");
function message(text) { $("notice").textContent = text; $("notice").hidden = !text; }
function download(job) { const link = el("a", "Скачать результат ↓", "button secondary"); link.href = `/api/report/${job.id}`; link.download = "delta-run.json"; return link; }
function badge(job) { return el("span", stateNames[job.state] || job.state, `status ${job.state === "COMPLETED" ? "success" : job.state === "FAILED" ? "failed" : "warning"}`); }
function title(job) { return job.kind === "training" ? "Обучение · 10-Gene Phenotype" : "Docker · контроллеры и кворум"; }
function renderJobs(state) {
  const jobs = state.jobs;
  $("run-count").textContent = jobs.length;
  $("completed-count").textContent = jobs.filter((job) => job.state === "COMPLETED").length;
  const busy = !!state.active_job || requested;
  $("train").disabled = busy || state.controller.status !== "READY";
  $("simulate").disabled = busy;
  $("live-label").textContent = busy ? "● ВЫПОЛНЯЕТСЯ" : "ОЖИДАНИЕ";
  if (!jobs.length) return;
  const job = jobs[0];
  const signature = JSON.stringify(jobs.map((value) => [value.id, value.state, value.events.length, value.elapsed_ms]));
  if (signature === lastSignature) return;
  lastSignature = signature;
  const log = $("activity-log"); log.replaceChildren();
  for (const event of job.events) {
    const row = el("div", undefined, "log-row");
    row.append(el("time", new Date(event.time).toLocaleTimeString("ru-RU")), el("span", event.message)); log.append(row);
  }
  if (job.error) { const row = el("div", undefined, "log-row"); row.append(el("time", "ERROR"), el("span", job.error)); log.append(row); }
  log.scrollTop = log.scrollHeight;
  const result = $("latest-result"); result.hidden = job.state !== "COMPLETED"; result.replaceChildren();
  if (job.state === "COMPLETED") {
    const row = el("div", undefined, "result-row"); const text = el("div", undefined, "result-text");
    text.append(el("b", job.kind === "training" ? "✓ Обучение завершено · receipt проверен" : "✓ Docker-сценарии и офлайн-проверка пройдены"), el("small", `${(job.elapsed_ms / 1000).toFixed(1)} с · ${job.id.slice(0, 12)}`));
    row.append(text, download(job)); result.append(row);
    if (job.result?.phases) {
      const phases = el("div", undefined, "phase-results");
      const names = {"all-online": "Все online", "one-lost": "Один отказ", "two-lost": "Два отказа", restarted: "После restart"};
      for (const [key, name] of Object.entries(names)) {
        const phase = job.result.phases[key];
        const card = el("div", undefined, "phase-result");
        card.append(el("small", name), el("b", `${phase.votes.length}/4 · ${phase.simulated_quorum_present ? "кворум" : "блок"}`)); phases.append(card);
      }
      result.append(phases);
    }
  }
  const history = $("history"); history.replaceChildren();
  for (const item of jobs) {
    const card = el("article", undefined, "panel history-item"); const info = el("div");
    info.append(el("h2", title(item)), el("p", `${new Date(item.created_at).toLocaleString("ru-RU")} · ${item.id.slice(0, 12)} · SIMULATED_LOCAL`));
    card.append(info, badge(item), download(item)); history.append(card);
  }
}
function renderGates(state) {
  const rows = [
    ["Локальное приложение", "HTTP Controller → Python Worker → execution receipt", state.controller.status === "READY" ? "Работает" : "Недоступно"],
    ["Docker-контроллеры", "Тестовые Ed25519 подписи, потеря кворума, смена поколения", "SIMULATED_LOCAL"],
    ["Feature000", "Arithmetic/model binding; обязательные доказательства и refinement", state.formal_candidate.decision],
    ["PR50 / native runtime", "PARAMETER/APPLY, WAL, retry/recovery, C ABI/FFM/IPC", "Зависит от Formal GO"],
    ["Gate A · безопасность", "Полные процессы и mandatory runtime проверки", "Не квалифицирован"],
    ["Gate B · scientific quality", "Физическая GPU, реальные frozen модели/данные и joined lineage", "Не квалифицирован"],
    ["Gate C / D · сеть", "Simulated WAN отдельно от approved real WAN", "Не квалифицированы"],
    ["ResultQC / GO checkpoint", "Все mandatory gates и evaluator quorum", "Отсутствуют"],
  ];
  $("gates").replaceChildren(...rows.map(([name, desc, status]) => { const row = el("div", undefined, "gate"); const info = el("div"); info.append(el("b", name), el("small", desc)); row.append(info, el("span", status || "UNKNOWN", `status ${status === "Работает" ? "success" : "warning"}`)); return row; }));
  $("formal-detail").textContent = JSON.stringify(state.formal_candidate, null, 2);
}
async function refresh() {
  if (refreshing) return;
  refreshing = true;
  try {
    const response = await fetch("/api/state", {signal: AbortSignal.timeout(10000)}); if (!response.ok) throw new Error(`HTTP ${response.status}`);
    current = await response.json();
    if (connectionFailed) { message(""); connectionFailed = false; }
    $("controller-state").textContent = current.controller.status === "READY" ? "Online" : "Недоступен";
    $("controller-state").className = current.controller.status === "READY" ? "good" : "";
    $("controller-detail").textContent = current.controller.status === "READY" ? `HTTP ready · ${(current.controller.build_id || "").slice(0, 8)}` : "Запустите presentation-start.ps1";
    $("advanced").href = current.controller_url;
    const observation = current.gpu.observation || ""; const gpu = observation.split(",").map((value) => value.trim());
    $("gpu-memory").textContent = current.gpu.state === "VISIBLE" ? gpu[2] : current.gpu.state === "CHECKING" ? "Проверяем…" : "Недоступна";
    $("gpu-name").textContent = current.gpu.state === "VISIBLE" ? gpu[0].replace("NVIDIA GeForce ", "") : "Видимость устройства; обучение здесь использует CPU";
    renderJobs(current); renderGates(current);
  } catch (error) {
    connectionFailed = true;
    $("train").disabled = true; $("simulate").disabled = true;
    $("controller-state").textContent = "Нет связи";
    $("controller-state").className = "";
    message(`Связь с приложением прервана: ${error.message}. Проверьте, что сервер запущен.`);
  } finally { refreshing = false; }
}
async function submit(path) {
  if (requested) return; requested = true; message(""); $("train").disabled = true; $("simulate").disabled = true;
  try {
    const response = await fetch(path, {method: "POST", headers: {"Content-Type": "application/json", "X-Delta-Presentation": "1"}, body: "{}"});
    const value = await response.json(); if (!response.ok) throw new Error(value.error || `HTTP ${response.status}`);
  } catch (error) { message(error.message); }
  finally { requested = false; await refresh(); }
}
$("train").addEventListener("click", () => submit("/api/train"));
$("simulate").addEventListener("click", () => submit("/api/simulate"));
await refresh();
setInterval(refresh, 1500);
