import {locales, supportedLanguage, translate, translateLog} from './i18n.mjs';

const $ = (id) => document.getElementById(id);
const pages = ['overview', 'runs', 'readiness'];
const preferenceKey = 'delta-presentation-language';
let storedLanguage;
try { storedLanguage = localStorage.getItem(preferenceKey); } catch { /* Storage may be disabled. */ }
const queryLanguage = new URL(location.href).searchParams.get('lang');
let language = supportedLanguage(queryLanguage) ? queryLanguage : supportedLanguage(storedLanguage) ? storedLanguage : 'en';
const t = (key, parameters) => translate(language, key, parameters);
let current = null;
let requested = false;
let refreshing = false;
let connectionFailed = false;
let connectionError = null;
let operationError = null;
let lastSignature = "";
const el = (tag, text, cls) => { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; if (cls) node.className = cls; return node; };
function navigate(page) {
  if (!pages.includes(page)) page = "overview";
  for (const name of pages) $(`page-${name}`).hidden = name !== page;
  document.querySelectorAll(".nav").forEach((button) => button.classList.toggle("active", button.dataset.page === page));
  $("page-title").textContent = t(page === 'runs' ? 'runs' : page);
  location.hash = page;
}
document.querySelectorAll(".nav").forEach((button) => button.addEventListener("click", () => navigate(button.dataset.page)));
window.addEventListener("hashchange", () => navigate(location.hash.slice(1)));
function message(text) { $("notice").textContent = text; $("notice").hidden = !text; }
function renderNotice() {
  message(connectionFailed ? t('connectionError', {error: connectionError}) : operationError ? translateLog(language, operationError) : '');
}
function download(job) { const link = el("a", t('download'), "button secondary"); link.href = `/api/report/${job.id}`; link.download = "delta-run.json"; return link; }
function badge(job) { return el("span", t(job.state), `status ${job.state === "COMPLETED" ? "success" : job.state === "FAILED" ? "failed" : "warning"}`); }
function title(job) { return t(job.kind === "training" ? 'trainingTitle' : 'controllersTitle'); }
function applyLanguage() {
  document.documentElement.lang = language;
  document.title = t('documentTitle');
  $('language').value = language;
  document.querySelectorAll('[data-i18n]').forEach((node) => { node.textContent = t(node.dataset.i18n); });
  document.querySelectorAll('[data-i18n-aria]').forEach((node) => { node.setAttribute('aria-label', t(node.dataset.i18nAria)); });
  try { localStorage.setItem(preferenceKey, language); } catch { /* Keep the current in-memory selection. */ }
  lastSignature = '';
  navigate(location.hash.slice(1) || 'overview');
  if (current) renderState();
  else {
    $('controller-state').textContent = t('checking');
    $('controller-detail').textContent = t('checkingHttp');
    $('gpu-memory').textContent = t('checking');
    $('gpu-name').textContent = t('readingGpu');
    $('live-label').textContent = t('idle');
  }
  renderNotice();
}
$('language').addEventListener('change', (event) => {
  if (!supportedLanguage(event.target.value)) return;
  language = event.target.value;
  const url = new URL(location.href);
  url.searchParams.set('lang', language);
  history.replaceState(null, '', url);
  applyLanguage();
});
function renderJobs(state) {
  const jobs = state.jobs;
  $("run-count").textContent = jobs.length;
  $("completed-count").textContent = jobs.filter((job) => job.state === "COMPLETED").length;
  const busy = !!state.active_job || requested;
  $("train").disabled = connectionFailed || busy || state.controller.status !== "READY";
  $("simulate").disabled = connectionFailed || busy;
  $("live-label").textContent = t(busy ? 'live' : 'idle');
  if (!jobs.length) { $('history').replaceChildren(el('p', t('emptyTitle'))); return; }
  const job = jobs[0];
  const signature = JSON.stringify(jobs.map((value) => [value.id, value.state, value.events.length, value.elapsed_ms]));
  if (signature === lastSignature) return;
  lastSignature = signature;
  const log = $("activity-log"); log.replaceChildren();
  for (const event of job.events) {
    const row = el("div", undefined, "log-row");
    row.append(el("time", new Date(event.time).toLocaleTimeString(locales[language], {hour12: false})), el("span", translateLog(language, event.message))); log.append(row);
  }
  if (job.error) { const row = el("div", undefined, "log-row"); row.append(el("time", t('error')), el("span", translateLog(language, job.error))); log.append(row); }
  log.scrollTop = log.scrollHeight;
  const result = $("latest-result"); result.hidden = job.state !== "COMPLETED"; result.replaceChildren();
  if (job.state === "COMPLETED") {
    const row = el("div", undefined, "result-row"); const text = el("div", undefined, "result-text");
    const duration = Number.isFinite(job.elapsed_ms) ? (job.elapsed_ms / 1000).toLocaleString(locales[language], {minimumFractionDigits: 1, maximumFractionDigits: 1}) : '…';
    text.append(el("b", t(job.kind === "training" ? 'trainingSuccess' : 'simulationSuccess')), el("small", `${duration} ${t('seconds')} · ${job.id.slice(0, 12)}`));
    row.append(text, download(job)); result.append(row);
    if (job.result?.phases) {
      const phases = el("div", undefined, "phase-results");
      const names = {"all-online": 'allOnline', "one-lost": 'oneLost', "two-lost": 'twoLost', restarted: 'restarted'};
      for (const [key, name] of Object.entries(names)) {
        const phase = job.result.phases[key];
        const card = el("div", undefined, "phase-result");
        card.append(el("small", t(name)), el("b", `${phase.votes.length}/4 · ${t(phase.simulated_quorum_present ? 'quorum' : 'blocked')}`)); phases.append(card);
      }
      result.append(phases);
    }
  }
  const history = $("history"); history.replaceChildren();
  for (const item of jobs) {
    const card = el("article", undefined, "panel history-item"); const info = el("div");
    info.append(el("h2", title(item)), el("p", `${new Date(item.created_at).toLocaleString(locales[language], {hour12: false})} · ${item.id.slice(0, 12)} · SIMULATED_LOCAL`));
    card.append(info, badge(item), download(item)); history.append(card);
  }
}
function renderGates(state) {
  const rows = [
    [t('localApplication'), "HTTP Controller → Python Worker → execution receipt", t(state.controller.status === "READY" ? 'working' : 'unavailable')],
    [t('dockerControllers'), t('dockerGateDescription'), "SIMULATED_LOCAL"],
    ["Feature000", t('formalGateDescription'), state.formal_candidate.decision],
    ["PR50 / native runtime", "PARAMETER/APPLY, WAL, retry/recovery, C ABI/FFM/IPC", t('dependsFormal')],
    [t('gateA'), t('gateADescription'), t('notQualified')],
    [t('gateB'), t('gateBDescription'), t('notQualified')],
    [t('gateNetwork'), t('gateNetworkDescription'), t('notQualified')],
    ["ResultQC / GO checkpoint", t('resultQcDescription'), t('absent')],
  ];
  $("gates").replaceChildren(...rows.map(([name, desc, status], index) => { const row = el("div", undefined, "gate"); const info = el("div"); info.append(el("b", name), el("small", desc)); row.append(info, el("span", status || "UNKNOWN", `status ${index === 0 && state.controller.status === 'READY' ? "success" : "warning"}`)); return row; }));
  $("formal-detail").textContent = JSON.stringify(state.formal_candidate, null, 2);
}
function renderState() {
  const ready = current.controller.status === 'READY';
  $('controller-state').textContent = t(connectionFailed ? 'disconnected' : ready ? 'online' : 'unavailable');
  $('controller-state').className = ready && !connectionFailed ? 'good' : '';
  $('controller-detail').textContent = ready ? `HTTP ready · ${(current.controller.build_id || '').slice(0, 8)}` : t('startServer');
  $('advanced').href = current.controller_url;
  const gpu = (current.gpu.observation || '').split(',').map((value) => value.trim());
  $('gpu-memory').textContent = current.gpu.state === 'VISIBLE' ? gpu[2] : t(current.gpu.state === 'CHECKING' ? 'checking' : 'unavailable');
  $('gpu-name').textContent = current.gpu.state === 'VISIBLE' ? gpu[0].replace('NVIDIA GeForce ', '') : t('gpuScope');
  renderJobs(current); renderGates(current);
}
async function refresh() {
  if (refreshing) return;
  refreshing = true;
  try {
    const response = await fetch("/api/state", {signal: AbortSignal.timeout(10000)}); if (!response.ok) throw new Error(`HTTP ${response.status}`);
    current = await response.json();
    connectionFailed = false; connectionError = null;
    renderState(); renderNotice();
  } catch (error) {
    connectionFailed = true;
    connectionError = error.message;
    $("train").disabled = true; $("simulate").disabled = true;
    $("controller-state").textContent = t('disconnected');
    $("controller-state").className = "";
    renderNotice();
  } finally { refreshing = false; }
}
async function submit(path) {
  if (requested) return; requested = true; operationError = null; renderNotice(); $("train").disabled = true; $("simulate").disabled = true;
  try {
    const response = await fetch(path, {method: "POST", headers: {"Content-Type": "application/json", "X-Delta-Presentation": "1"}, body: "{}"});
    const value = await response.json(); if (!response.ok) throw new Error(value.error || `HTTP ${response.status}`);
  } catch (error) { operationError = error.message; renderNotice(); }
  finally { requested = false; await refresh(); }
}
$("train").addEventListener("click", () => submit("/api/train"));
$("simulate").addEventListener("click", () => submit("/api/simulate"));
applyLanguage();
await refresh();
setInterval(refresh, 1500);
