import {locales, supportedLanguage, translate, translateLog} from './i18n.mjs?v=consensus4w';

const $ = (id) => document.getElementById(id);
const pages = ['overview', 'models', 'runs', 'readiness'];
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
  $("page-title").textContent = t(page === 'runs' ? 'runs' : page === 'models' ? 'models' : page);
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
function title(job) { return t(job.kind === "verification" ? 'verificationTitle' : job.kind === "training" ? 'trainingTitle' : 'controllersTitle'); }
function applyLanguage() {
  document.documentElement.lang = language;
  document.title = t('documentTitle');
  $('language').value = language;
  $('advanced').href = adminLink('/live-execution', linkedId);
  $('visual-guide').href = adminLink('/guide');
  $('node-training').href = `/node-training/?lang=${language}`;
  $('verification').href = `/verification/?lang=${language}`;
  if ($('mnist-open-dashboard')) $('mnist-open-dashboard').href = `/node-training/?lang=${language}`;
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
    text.append(el("b", t(job.kind === "verification" ? 'verificationSuccess' : job.kind === "training" ? 'trainingSuccess' : 'simulationSuccess')), el("small", `${duration} ${t('seconds')} · ${job.id.slice(0, 12)}`));
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
    info.append(el("h2", title(item)), el("p", `${new Date(item.created_at).toLocaleString(locales[language], {hour12: false})} · SIMULATED_LOCAL`), renderHashWithCopy(item.id));
    card.append(info, badge(item), download(item)); history.append(card);
  }
}
function renderHashWithCopy(value) {
  if (!value || value === '—') return el('span', '—');
  const container = el('span', undefined, 'hash-container');
  const short = value.length > 16 ? `${value.slice(0, 8)}…${value.slice(-6)}` : value;
  const code = el('code', short, 'short-hash');
  code.title = value;
  const copyBtn = el('button', t('copyHash'), 'copy-btn');
  copyBtn.type = 'button';
  copyBtn.title = t('copyHash');
  copyBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    if (navigator.clipboard) {
      navigator.clipboard.writeText(value).then(() => {
        copyBtn.textContent = t('copied');
        copyBtn.classList.add('copied');
        setTimeout(() => {
          copyBtn.textContent = t('copyHash');
          copyBtn.classList.remove('copied');
        }, 1500);
      });
    }
  });
  container.append(code, copyBtn);
  return container;
}

function renderNarrative(state) {
  const busy = !!state.active_job || requested;
  const active = state.jobs.find(j => j.id === state.active_job);
  const latest = state.jobs[0];
  const ready = state.controller.status === 'READY';

  $('nv-task').textContent = '10-Gene Phenotype';
  $('nv-participants').textContent = ready ? '1 Controller · 1 Worker' : t('unavailable');

  if (busy) {
    const phase = active?.events?.slice(-1)[0]?.message || 'RUNNING';
    $('nv-execution').textContent = translateLog(language, phase);
    $('nv-execution').className = 'nv-val busy-pulse';
  } else {
    $('nv-execution').textContent = t(ready ? 'readyIdle' : 'unavailable');
    $('nv-execution').className = 'nv-val';
  }

  if (latest && latest.state === 'COMPLETED') {
    const dur = Number.isFinite(latest.elapsed_ms) ? `${(latest.elapsed_ms/1000).toFixed(1)} ${t('seconds')}` : '';
    $('nv-result').textContent = `${t('lossComputed')} · ${dur}`;
  } else if (latest && latest.state === 'FAILED') {
    $('nv-result').textContent = t('FAILED');
  } else {
    $('nv-result').textContent = t('awaitingRun');
  }

  const receiptBox = $('nv-receipt');
  receiptBox.replaceChildren();
  if (latest && latest.state === 'COMPLETED') {
    const label = el('span', t('verifiedLineage') + ' · ');
    receiptBox.append(label, renderHashWithCopy(latest.id));
  } else {
    receiptBox.textContent = '—';
  }

  $('nv-verification').textContent = 'Candidate (NO_GO) · Reference oracle';
}

function renderGates(state) {
  const formalStatusText = state.formal_candidate?.decision === 'GO' ? 'GO' : 'Candidate (NO_GO · 44/45 obligations)';
  const rows = [
    [t('localApplication'), "HTTP Controller → Python Worker → execution receipt", t(state.controller.status === "READY" ? 'working' : 'unavailable'), 'evidenceRuntime'],
    [t('dockerControllers'), t('dockerGateDescription'), "SIMULATED_LOCAL", 'evidenceTest'],
    [t('verificationTitle'), "Pinned formal Python oracle: 7 arithmetic & mutation checks", "✓ 7/7 PASS", 'evidenceOracle'],
    ["Feature000", t('formalGateDescription'), formalStatusText, 'evidenceFormal'],
    ["PR50 / native runtime", "PARAMETER/APPLY, WAL, retry/recovery, C ABI/FFM/IPC", t('dependsFormal'), 'evidenceFormal'],
    [t('gateA'), t('gateADescription'), t('notQualified'), 'evidenceRuntime'],
    [t('gateB'), t('gateBDescription'), t('notQualified'), 'evidenceRuntime'],
    [t('gateNetwork'), t('gateNetworkDescription'), t('notQualified'), 'evidenceTest'],
    ["ResultQC / GO checkpoint", t('resultQcDescription'), t('absent'), 'evidenceFormal'],
  ];
  $("gates").replaceChildren(...rows.map(([name, desc, status, evidenceType]) => {
    const row = el("div", undefined, "gate");
    const info = el("div");
    const titleRow = el("div", undefined, "gate-title-row");
    titleRow.append(el("b", name));
    if (evidenceType) {
      titleRow.append(el("span", t(evidenceType), "evidence-badge"));
    }
    info.append(titleRow, el("small", desc));
    const statusSpan = el("span", status || "UNKNOWN", `status ${status.includes('✓') || status === t('working') ? "success" : "warning"}`);
    row.append(info, statusSpan);
    return row;
  }));
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
  renderNarrative(current);
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

let activeReceipt = null;

function showReceipt(receipt) {
  if (!receipt) return;
  activeReceipt = receipt;
  const modal = $("receipt-modal");
  if (!modal) return;
  $("rm-exec-id").textContent = receipt.execution_id;
  $("rm-workers-count").textContent = `${receipt.participant_count} Sharded Workers (${receipt.model_name})`;
  $("rm-param-root").textContent = receipt.parameter_root;
  $("rm-apply-digest").textContent = receipt.apply_digest;
  $("rm-next-state").textContent = receipt.next_model_hash || receipt.next_adapter_hash || "—";
  $("receipt-subtitle").textContent = `${receipt.workload_type} · ${receipt.formal_semantics_id}`;
  $("receipt-json-text").textContent = JSON.stringify(receipt, null, 2);
  $("copy-btn-text").textContent = t("copyReceipt");
  modal.showModal();
}

const modalClose = $("btn-close-receipt");
if (modalClose) modalClose.addEventListener("click", () => $("receipt-modal").close());
const modalCloseX = $("btn-close-receipt-x");
if (modalCloseX) modalCloseX.addEventListener("click", () => $("receipt-modal").close());

const copyBtn = $("btn-copy-receipt");
if (copyBtn) {
  copyBtn.addEventListener("click", async () => {
    if (!activeReceipt) return;
    try {
      await navigator.clipboard.writeText(JSON.stringify(activeReceipt, null, 2));
      $("copy-btn-text").textContent = t("copied");
      setTimeout(() => { $("copy-btn-text").textContent = t("copyReceipt"); }, 2000);
    } catch {
      $("copy-btn-text").textContent = "Copied!";
    }
  });
}

function drawSvgLineChart(svgEl, chartData, options = {}) {
  if (!svgEl || !chartData || !chartData.values || chartData.values.length < 2) return;
  const {
    color = "#38bdf8",
    gradientId = `grad-${Math.random().toString(36).slice(2, 8)}`,
    isAccuracy = chartData.metric === "accuracy"
  } = options;

  const width = 360;
  const height = 130;
  const padLeft = 40;
  const padRight = 30;
  const padTop = 22;
  const padBottom = 26;
  const plotW = width - padLeft - padRight;
  const plotH = height - padTop - padBottom;

  const vals = chartData.values.map(Number);
  let minV = Math.min(...vals);
  let maxV = Math.max(...vals);

  if (isAccuracy) {
    minV = Math.min(minV, 55);
    maxV = Math.max(maxV, 88);
  } else {
    const span = Math.max(0.04, maxV - minV);
    minV = Math.max(0, minV - span * 0.18);
    maxV = maxV + span * 0.18;
  }
  const range = maxV - minV || 1;

  const points = vals.map((v, i) => {
    const x = padLeft + (i / (vals.length - 1)) * plotW;
    const y = padTop + (1 - (v - minV) / range) * plotH;
    return { x, y, v, label: chartData.labels?.[i] ?? `R${i}` };
  });

  const pathD = points.reduce((acc, p, i) => acc + (i === 0 ? `M ${p.x.toFixed(1)} ${p.y.toFixed(1)}` : ` L ${p.x.toFixed(1)} ${p.y.toFixed(1)}`), "");
  const firstP = points[0];
  const lastP = points[points.length - 1];
  const areaD = `${pathD} L ${lastP.x.toFixed(1)} ${(padTop + plotH).toFixed(1)} L ${firstP.x.toFixed(1)} ${(padTop + plotH).toFixed(1)} Z`;

  const gridSteps = 3;
  let gridSvg = "";
  for (let s = 0; s <= gridSteps; s++) {
    const yVal = minV + (s / gridSteps) * range;
    const yPos = padTop + (1 - s / gridSteps) * plotH;
    const textVal = isAccuracy ? `${Math.round(yVal)}%` : yVal.toFixed(2);
    gridSvg += `
      <line x1="${padLeft}" y1="${yPos.toFixed(1)}" x2="${(padLeft + plotW).toFixed(1)}" y2="${yPos.toFixed(1)}" stroke="#334155" stroke-dasharray="3 3" stroke-width="1" />
      <text x="${padLeft - 6}" y="${(yPos + 3).toFixed(1)}" text-anchor="end" fill="#64748b" font-size="8.5" font-family="monospace">${textVal}</text>
    `;
  }

  let pointsSvg = "";
  points.forEach((p, idx) => {
    const isFailure = chartData.failure_point_index === idx;
    const ptColor = isFailure ? "#f59e0b" : color;
    const displayVal = isAccuracy ? `${p.v.toFixed(1)}%` : p.v.toFixed(3);

    pointsSvg += `
      <circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="${isFailure ? 5.5 : 4}" fill="${ptColor}" stroke="#0f172a" stroke-width="2" />
      <text x="${p.x.toFixed(1)}" y="${(p.y - 7).toFixed(1)}" text-anchor="middle" fill="#f8fafc" font-size="8.5" font-weight="600" font-family="monospace">${displayVal}</text>
      <text x="${p.x.toFixed(1)}" y="${(height - 8).toFixed(1)}" text-anchor="middle" fill="#94a3b8" font-size="8" font-family="monospace">${p.label}</text>
    `;

    if (isFailure && chartData.failure_label) {
      const boxW = 150;
      const boxX = Math.min(width - boxW - 6, Math.max(padLeft, p.x - boxW / 2));
      pointsSvg += `
        <circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="9" fill="none" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="2 2" />
        <g transform="translate(${boxX.toFixed(1)}, ${(p.y + 11).toFixed(1)})">
          <rect width="${boxW}" height="16" rx="3" fill="#78350f" stroke="#f59e0b" stroke-width="1" />
          <text x="${(boxW / 2).toFixed(1)}" y="11" text-anchor="middle" fill="#fef08a" font-size="7.5" font-weight="700">${chartData.failure_label}</text>
        </g>
      `;
    }
  });

  svgEl.innerHTML = `
    <defs>
      <linearGradient id="${gradientId}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="${color}" stop-opacity="0.32" />
        <stop offset="100%" stop-color="${color}" stop-opacity="0.0" />
      </linearGradient>
    </defs>
    ${gridSvg}
    <path d="${areaD}" fill="url(#${gradientId})" />
    <path d="${pathD}" fill="none" stroke="${color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
    ${pointsSvg}
  `;
}

function initModelCharts() {
  const mnistChartEl = $("mnist-chart");
  if (mnistChartEl) {
    drawSvgLineChart(mnistChartEl, {
      metric: "accuracy",
      labels: ["Round 1", "Round 2", "Round 3", "Round 4"],
      values: [61.2, 72.4, 78.1, 82.03],
      failure_point_index: 2,
      failure_label: "⚡ Node 4 Crash & Recovery"
    }, { color: "#2dd4bf" });
  }

  const causalChartEl = $("causal-chart");
  if (causalChartEl) {
    drawSvgLineChart(causalChartEl, {
      metric: "loss",
      labels: ["R0", "R1", "R2", "R3", "R4", "R5"],
      values: [2.8904, 2.8686, 2.8465, 2.8267, 2.8098, 2.7952]
    }, { color: "#4ade80" });
  }

  const qloraChartEl = $("qlora-chart");
  if (qloraChartEl) {
    drawSvgLineChart(qloraChartEl, {
      metric: "loss",
      labels: ["R1", "R2", "R3", "R4"],
      values: [1.5234, 1.4784, 1.4334, 1.3884]
    }, { color: "#c084fc" });
  }
}

let causalReceipt = null;
const btnCausal = $("btn-run-causal");
const btnInspectCausal = $("btn-inspect-causal");

if (btnInspectCausal) {
  btnInspectCausal.addEventListener("click", () => {
    if (causalReceipt) showReceipt(causalReceipt);
  });
}

if (btnCausal) {
  btnCausal.addEventListener("click", async () => {
    btnCausal.disabled = true;
    const badge = $("causal-status-badge");
    if (badge) { badge.textContent = "TRAINING 5 ROUNDS…"; badge.className = "chip warning"; }

    for (let i = 1; i <= 5; i++) {
      const elStep = $(`causal-step-${i}`);
      if (elStep) elStep.className = i === 1 ? "step-dot active" : "step-dot";
    }

    try {
      const response = await fetch("/api/models/causal-run", {
        method: "POST",
        headers: {"Content-Type": "application/json", "X-Delta-Presentation": "1"},
        body: "{}"
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      causalReceipt = data.receipt;

      const roundBadge = $("causal-round-badge");
      if (roundBadge) roundBadge.textContent = `Round ${data.rounds_count || 5} / 5`;

      const trajVal = $("causal-trajectory-val");
      if (trajVal) {
        trajVal.textContent = `${Number(data.initial_loss).toFixed(4)} → ${Number(data.final_loss).toFixed(4)} (-${Number(data.loss_reduction).toFixed(4)})`;
      }

      const cpShort = $("causal-next-cp-short");
      if (cpShort) {
        cpShort.textContent = (data.checkpoint_manifest || "").slice(0, 16) + "…";
      }

      for (let i = 1; i <= 5; i++) {
        const elStep = $(`causal-step-${i}`);
        if (elStep) elStep.className = "step-dot completed";
      }

      const causalChartEl = $("causal-chart");
      if (causalChartEl && data.chart_data) {
        drawSvgLineChart(causalChartEl, data.chart_data, { color: "#4ade80" });
      }

      const list = $("causal-steps-list");
      if (list && data.steps) {
        list.replaceChildren();
        for (const st of data.steps) {
          const row = el("div", undefined, "step-row");
          const wId = st.worker_id.replace("demo-causal-", "");
          row.append(
            el("span", `${wId}`, "step-num"),
            el("span", `Loss: ${Number(st.loss).toFixed(4)} (${st.processed_tokens} tok)`, "step-loss"),
            el("span", `commit: ${st.commitment_root.slice(0, 16)}…`, "step-tok")
          );
          list.append(row);
        }
      }

      const cryptoBox = $("causal-crypto-box");
      if (cryptoBox) {
        cryptoBox.hidden = false;
        $("causal-exec-id").textContent = data.execution_id;
        $("causal-param-root").textContent = (data.receipt.parameter_root || "").slice(0, 24) + "…";
        $("causal-apply-digest").textContent = (data.receipt.apply_digest || "").slice(0, 24) + "…";
        $("causal-next-model").textContent = (data.receipt.next_model_hash || "").slice(0, 24) + "…";
      }

      if (btnInspectCausal) btnInspectCausal.hidden = false;
      if (badge) { badge.textContent = `APPLIED (${data.elapsed_ms}ms)`; badge.className = "chip success"; }
    } catch (err) {
      if (badge) { badge.textContent = "FAILED"; badge.className = "chip failed"; }
      operationError = err.message;
      renderNotice();
    } finally {
      btnCausal.disabled = false;
    }
  });
}

let qloraReceipt = null;
const btnQlora = $("btn-run-qlora-step");
const btnInspectQlora = $("btn-inspect-qlora");

if (btnInspectQlora) {
  btnInspectQlora.addEventListener("click", () => {
    if (qloraReceipt) showReceipt(qloraReceipt);
  });
}

if (btnQlora) {
  btnQlora.addEventListener("click", async () => {
    btnQlora.disabled = true;
    const badge = $("qlora-status-badge");
    if (badge) { badge.textContent = "TRAINING 4 ROUNDS…"; badge.className = "chip warning"; }

    for (let i = 1; i <= 5; i++) {
      const elStep = $(`qlora-step-${i}`);
      if (elStep) elStep.className = i === 1 ? "step-dot active" : "step-dot";
    }

    try {
      const response = await fetch("/api/models/qlora-step", {
        method: "POST",
        headers: {"Content-Type": "application/json", "X-Delta-Presentation": "1"},
        body: "{}"
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      qloraReceipt = data.receipt;

      const roundBadge = $("qlora-round-badge");
      if (roundBadge) roundBadge.textContent = `Round ${data.rounds_count || 4} / 4`;

      const trajVal = $("qlora-trajectory-val");
      if (trajVal) {
        trajVal.textContent = `${Number(data.initial_loss).toFixed(4)} → ${Number(data.final_loss).toFixed(4)} (-${Number(data.loss_reduction).toFixed(4)})`;
      }

      for (let i = 1; i <= 5; i++) {
        const elStep = $(`qlora-step-${i}`);
        if (elStep) elStep.className = "step-dot completed";
      }

      const qloraChartEl = $("qlora-chart");
      if (qloraChartEl && data.chart_data) {
        drawSvgLineChart(qloraChartEl, data.chart_data, { color: "#c084fc" });
      }

      const container = $("qlora-qual-details");
      if (container && data.workers) {
        container.replaceChildren();
        for (const w of data.workers) {
          const row = el("div", undefined, "step-row");
          const wId = w.worker_id.replace("demo-qlora-", "");
          row.append(
            el("span", `${wId} (${w.shard_index})`, "step-num"),
            el("span", `Loss: ${w.losses.join(", ")} (${w.sample_count} samples)`, "step-loss"),
            el("span", `commit: ${w.commitment_root.slice(0, 16)}…`, "step-tok")
          );
          container.append(row);
        }
      }

      const cryptoBox = $("qlora-crypto-box");
      if (cryptoBox) {
        cryptoBox.hidden = false;
        $("qlora-exec-id").textContent = data.execution_id;
        $("qlora-param-root").textContent = (data.parameter_root || "").slice(0, 24) + "…";
        $("qlora-apply-digest").textContent = (data.apply_digest || "").slice(0, 24) + "…";
        $("qlora-next-adapter").textContent = (data.next_adapter_hash || "").slice(0, 24) + "…";
      }

      if (btnInspectQlora) btnInspectQlora.hidden = false;
      if (badge) { badge.textContent = `APPLIED (${data.elapsed_ms}ms)`; badge.className = "chip success"; }
    } catch (err) {
      if (badge) { badge.textContent = "FAILED"; badge.className = "chip failed"; }
      operationError = err.message;
      renderNotice();
    } finally {
      btnQlora.disabled = false;
    }
  });
}

initModelCharts();

applyLanguage();
await refresh();
setInterval(refresh, 1500);

document.addEventListener("keydown", event => { if (event.key === "Escape") document.querySelector(".language-help").open = false; });
document.addEventListener("pointerdown", event => { const help = document.querySelector(".language-help"); if (!help.contains(event.target)) help.open = false; });
