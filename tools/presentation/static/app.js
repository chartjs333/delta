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
let linked = null;
let linkedError = false;
const linkedId = new URL(location.href).searchParams.get('execution');
let profileLanguageRead = false;
const el = (tag, text, cls) => { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; if (cls) node.className = cls; return node; };
function navigate(page) {
  if (!pages.includes(page)) page = "overview";
  for (const name of pages) $(`page-${name}`).hidden = name !== page;
  document.querySelectorAll(".nav").forEach((button) => button.classList.toggle("active", button.dataset.page === page));
  $("page-title").textContent = t(page === 'runs' ? 'runs' : page);
  location.hash = page;
}
document.querySelectorAll(".nav[data-page]").forEach((button) => button.addEventListener("click", () => navigate(button.dataset.page)));
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
  $('advanced').href = adminLink('/live-execution', linkedId);
  $('visual-guide').href = adminLink('/guide');
  $('node-training').href = `/node-training/?lang=${language}`;
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
  void saveProfileLanguage();
});
async function saveProfileLanguage() {
  try {
    const previous = await fetch('/api/workspace', {cache:'no-store', signal:AbortSignal.timeout(10000)});
    if (!previous.ok) throw new Error('Profile unavailable');
    const profile = await previous.json();
    if (!profile.data) return;
    profile.data.language = language;
    const response = await fetch('/api/workspace', {method:'PUT', headers:{'Content-Type':'application/json','X-Delta-Presentation':'1'}, body:JSON.stringify(profile), signal:AbortSignal.timeout(10000)});
    if (!response.ok) throw new Error('Profile save failed');
  } catch { operationError = t('profileUnavailable'); renderNotice(); }
}
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
  const adminUrl = new URL('/admin/', location.origin);
  adminUrl.searchParams.set('lang', language);
  if (linkedId) adminUrl.searchParams.set('execution', linkedId);
  adminUrl.hash = '/live-execution';
  $('advanced').href = adminUrl.href;
  const gpu = (current.gpu.observation || '').split(',').map((value) => value.trim());
  $('gpu-memory').textContent = current.gpu.state === 'VISIBLE' ? gpu[2] : t(current.gpu.state === 'CHECKING' ? 'checking' : 'unavailable');
  $('gpu-name').textContent = current.gpu.state === 'VISIBLE' ? gpu[0].replace('NVIDIA GeForce ', '') : t('gpuScope');
  renderJobs(current); renderGates(current);
  renderWorkspace(); renderLinked();
}
function adminLink(route, execution) {
  const url = new URL('/admin/', location.origin); url.searchParams.set('lang', language);
  if (execution) url.searchParams.set('execution', execution);
  url.hash = route; return url.href;
}
function renderWorkspace() {
  const box = $('shared-workspace'); box.replaceChildren();
  const profile = current.workspace;
  if (!profile) { box.append(el('p', t('profileUnavailable'))); return; }
  const campaign = profile.campaigns.find(item => item.id === profile.activeCampaignId);
  const header = el('div', undefined, 'panel-title');
  const text = el('div'); text.append(el('h2', `${profile.profileName} · ${campaign?.name ?? ''}`), el('p', t('sharedProfileNote'), 'muted'));
  const configure = el('a', t('configureCampaign'), 'button secondary'); configure.href = adminLink('/campaigns');
  header.append(text, configure); box.append(header);
  const runs = profile.runs.filter(item => item.campaignId === profile.activeCampaignId && item.executionId).slice(-5).reverse();
  const list = el('div', undefined, 'shared-runs');
  for (const run of runs) {
    const url = new URL(location.href); url.searchParams.set('execution', run.executionId); url.searchParams.set('lang', language); url.hash = 'overview';
    const link = el('a', `${run.name} · ${run.executionId.slice(0, 8)}`, 'button secondary'); link.href = url.href; list.append(link);
  }
  box.append(list);
}
function renderLinked() {
  const box = $('linked-execution'); box.hidden = !linkedId; box.replaceChildren();
  if (!linkedId) return;
  box.append(el('div', t('linkedRun'), 'eyebrow'), el('h2', linked?.run?.name || t('controllerRun')), el('code', linkedId));
  if (linkedError) { box.append(el('p', t('linkedUnavailable'), 'muted')); return; }
  if (!linked) { box.append(el('p', t('checking'))); return; }
  box.append(el('p', t(linked.status.state), linked.receipt_verified ? 'good' : 'muted'));
  if (linked.campaign) box.append(el('p', `${linked.profile_name} · ${linked.campaign.name}`));
  const actions = el('div', undefined, 'shared-runs');
  const back = el('a', t('openSameRun'), 'button secondary'); back.href = adminLink('/live-execution', linkedId); actions.append(back);
  if (linked.receipt_verified && linked.receipt) {
    box.append(el('p', t('linkedVerified')));
    const downloadReceipt = el('a', t('downloadReceipt'), 'button');
    downloadReceipt.href = `/api/linked-execution/${linkedId}?download=receipt`;
    downloadReceipt.download = `receipt-${linkedId}.json`;
    actions.append(downloadReceipt);
  }
  box.append(actions);
}
async function refreshLinked() {
  if (!linkedId) return;
  try {
    if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(linkedId)) throw new Error('Invalid execution');
    const response = await fetch(`/api/linked-execution/${linkedId}`, {cache:'no-store', signal:AbortSignal.timeout(10000)});
    if (!response.ok) throw new Error('Unverified result');
    linked = await response.json(); linkedError = false;
  } catch { linked = null; linkedError = true; }
  renderLinked();
}
async function refresh() {
  if (refreshing) return;
  refreshing = true;
  try {
    const response = await fetch("/api/state", {signal: AbortSignal.timeout(10000)}); if (!response.ok) throw new Error(`HTTP ${response.status}`);
    current = await response.json();
    if (!profileLanguageRead) {
      profileLanguageRead = true;
      if (!supportedLanguage(queryLanguage) && supportedLanguage(current.workspace?.language)) {
        language = current.workspace.language; applyLanguage();
      }
    }
    connectionFailed = false; connectionError = null;
    renderState(); renderNotice();
    await refreshLinked();
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

document.addEventListener("keydown", event => { if (event.key === "Escape") document.querySelector(".language-help").open = false; });
document.addEventListener("pointerdown", event => { const help = document.querySelector(".language-help"); if (!help.contains(event.target)) help.open = false; });
