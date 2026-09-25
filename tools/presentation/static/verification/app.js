import {scenarios, translate} from './i18n.mjs';

const $ = id => document.getElementById(id);
const el = (tag, text, cls) => { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; if (cls) node.className = cls; return node; };
const preference = 'delta-presentation-language';
let saved;
try { saved = localStorage.getItem(preference); } catch { /* Storage is optional. */ }
const url = new URL(location.href);
let language = (url.searchParams.get('lang') || saved) === 'ru' ? 'ru' : 'en';
const t = key => translate(language, key);
let selected = /^[a-f0-9]{32}$/.test(url.searchParams.get('run') || '') ? url.searchParams.get('run') : null;
let current = null;
let connected = false;
let submitting = false;
let error = '';
let signature = '';
let generation = 0;
const verified = new Map();
const vector = values => `[${values.join(', ')}]`;
const busy = () => submitting || Boolean(current?.active_job);
const activeJob = () => current?.jobs.find(job => job.id === current.active_job);
const selectedJob = () => current?.jobs.find(job => job.id === selected && job.kind === 'verification');

function applyLanguage() {
  document.documentElement.lang = language;
  document.title = `DeltaReduce · ${t('lab')}`;
  $('language').value = language;
  $('language').setAttribute('aria-label', t('language'));
  document.querySelector('nav').setAttribute('aria-label',t('navigation'));
  document.querySelector('.pipeline').setAttribute('aria-label',t('computation'));
  document.querySelectorAll('[data-t]').forEach(node => { node.textContent = t(node.dataset.t); });
  document.querySelectorAll('.hint summary').forEach(node => { node.setAttribute('aria-label', t('help')); });
  const links = {home:`/?lang=${language}`, admin:`/admin/?lang=${language}#/live-execution`, guide:`/admin/?lang=${language}#/guide`, nodes:`/node-training/?lang=${language}`};
  document.querySelectorAll('[data-link]').forEach(node => { node.href = links[node.dataset.link]; });
  try { localStorage.setItem(preference, language); } catch { /* Keep the selected language in the URL. */ }
  const next = new URL(location.href); next.searchParams.set('lang', language);
  history.replaceState(null, '', next);
  signature = '';
  render();
}

$('language').addEventListener('change', event => { language = event.target.value === 'ru' ? 'ru' : 'en'; applyLanguage(); });
document.addEventListener('keydown', event => { if (event.key === 'Escape') document.querySelectorAll('.hint[open]').forEach(node => { node.open = false; }); });
$('run-all').addEventListener('click', () => start('all'));

function selectRun(id) {
  selected = id;
  const next = new URL(location.href); next.searchParams.set('run', id);
  history.replaceState(null, '', next);
  signature = '';
  render();
}

async function start(scenario) {
  if (busy() || !connected) return;
  submitting = true; error = ''; render();
  try {
    const response = await fetch(`/api/verify/${scenario}`, {method:'POST', headers:{'Content-Type':'application/json','X-Delta-Presentation':'1'}, body:'{}'});
    const value = await response.json();
    if (!response.ok) throw new Error(response.status === 409 ? t('busy') : value.error || `HTTP ${response.status}`);
    selected = value.id;
    current = {...current, active_job:value.id, jobs:[value, ...(current?.jobs || []).filter(item => item.id !== value.id)]};
    selectRun(value.id);
  } catch (failure) { error = failure.message; }
  finally { submitting = false; signature = ''; render(); }
}

async function integrity(job) {
  const value = job.result;
  if (!value?.canonical_report || !value.report_sha256 || !crypto.subtle) return false;
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value.canonical_report));
  const hex = [...new Uint8Array(digest)].map(byte => byte.toString(16).padStart(2,'0')).join('');
  // Render the hashed report, never a separately substituted report object.
  const report = JSON.parse(value.canonical_report);
  if (hex !== value.report_sha256 || report.scope !== 'FORMAL_REFERENCE_DEMO' || report.native_execution !== false || report.gate_eligible !== false || report.manifest_sha256 !== '2bf8ea7c39444703973d360bbd18da736fafed68d05e62c19327bf7698f48ae2') return false;
  return report;
}

function reason(code) {
  return t(({ACCEPTED:'reasonAccept',IDENTICAL:'reasonRepeat',ARITHMETIC_RESULT_MISMATCH:'reasonResult',ARTIFACT_BYTES:'reasonBytes',ARTIFACT_MISSING:'reasonMissing',PARENT_MODEL:'reasonParent'})[code] || code);
}

function renderCases(report) {
  $('cases').replaceChildren();
  for (const [id, title, description] of scenarios) {
    const result = report?.cases.find(item => item.scenario === id);
    const card = el('article', undefined, `case${result ? result.matches_expectation ? ' pass' : ' fail' : ''}`);
    card.dataset.scenario = id;
    const icon = el('span', result ? result.matches_expectation ? '✓' : '!' : '◇', 'case-icon');
    icon.setAttribute('aria-hidden','true');
    const content = el('div', undefined, 'case-content');
    content.append(el('h3',t(title)),el('p',t(description)));
    const outcome = el('div', undefined, 'case-result');
    outcome.append(el('span',result ? t(result.matches_expectation ? result.outcome === 'REJECTED' ? 'rejected' : result.outcome === 'IDENTICAL' ? 'identical' : 'accepted' : 'mismatch') : t('pending')));
    if (result) {
      const details = el('details'); details.append(el('summary',t('details')),el('p',reason(result.observed)),el('code',result.observed),el('pre',JSON.stringify(result.detail,null,2)));
      content.append(outcome,details);
    } else content.append(outcome);
    const run = el('button',t('run'),'button secondary');
    run.disabled = busy() || !connected;
    run.setAttribute('aria-label',`${t('run')}: ${t(title)}`);
    run.addEventListener('click',()=>start(id));
    card.append(icon,content,run); $('cases').append(card);
  }
  $('score').textContent = report ? `${report.cases.filter(item=>item.matches_expectation).length} / ${report.cases.length}` : '0 / 7';
}

function renderReport(job, report) {
  const set = (id,text) => { $(id).textContent = text; };
  for (const id of ['parent-model','parent-optimizer','artifact-count','domain-shards','parameter-values','converted-values','arithmetic','quantum','next-model','next-optimizer','model-change','learning-rate','report-hash','computation-hash','source-commit']) set(id,'—');
  $('download').hidden = !report;
  $('raw-report').textContent = report ? JSON.stringify(report,null,2) : '';
  set('result-label', report ? `${t('baseline')} · ${(report.elapsed_us/1000).toFixed(1)} ${t('ms')}` : t('awaiting'));
  set('integrity', report ? t('integrityOK') : job?.result ? t('integrityChecking') : '');
  if (!report) return;
  const {inputs,computation,conversions} = report;
  set('parent-model',vector(inputs.parent_model)); set('parent-optimizer',vector(inputs.optimizer));
  set('artifact-count',inputs.artifact_count); set('domain-shards',`${inputs.domain_count} / ${inputs.shard_count}`);
  set('parameter-values',vector(computation.parameters.flatMap(body=>body.numerators)));
  set('converted-values',vector(conversions.flatMap(body=>body.values)));
  set('arithmetic',`INT${inputs.profile.accumulator_bits}`); set('quantum',inputs.profile.apply_quantum.join(' / '));
  set('next-model',vector(computation.apply.next_model)); set('next-optimizer',vector(computation.apply.next_optimizer));
  set('model-change',vector(computation.apply.next_model.map((value,index)=>value-inputs.parent_model[index])));
  set('learning-rate',inputs.profile.learning_rate.join(' / '));
  set('report-hash',job.result.report_sha256); set('computation-hash',report.computation_sha256); set('source-commit',report.source.source_commit);
  $('download').href = `/api/report/${job.id}`; $('download').download = `delta-verification-${job.id}.json`;
}

function renderHistory() {
  const jobs = (current?.jobs || []).filter(job=>job.kind==='verification').slice(0,8);
  $('history').replaceChildren();
  if (!jobs.length) { $('history').append(el('div',t('empty'),'empty')); return; }
  for (const job of jobs) {
    const row = el('div',undefined,'history-row');
    const details = el('div');
    const title = job.scenario === 'all' ? t('all') : t(scenarios.find(item=>item[0]===job.scenario)?.[1] || job.scenario);
    details.append(el('b',`${title} · ${t(job.state)}`),el('small',`${new Date(job.created_at).toLocaleString(language==='ru'?'ru-RU':'en-GB')} · ${job.id.slice(0,12)}`));
    const view = el('button',t('view'),'button secondary'); view.disabled = selected === job.id; view.addEventListener('click',()=>selectRun(job.id));
    row.append(details,view); $('history').append(row);
  }
}

function render() {
  $('run-all').disabled = busy() || !connected;
  $('run-all').textContent = t(activeJob()?.kind === 'verification' || submitting ? 'running' : 'runAll');
  $('connection').textContent = t(!connected ? current ? 'offline' : 'connecting' : busy() ? activeJob()?.kind === 'verification' || submitting ? 'running' : 'busy' : 'ready');
  const job = selectedJob();
  const failure = error || (job?.state === 'FAILED' ? `${t('serverError')} ${job.error || ''}` : '');
  $('error').textContent = failure; $('error').hidden = !failure;
  const key = JSON.stringify([language,selected,job?.updated_at,current?.active_job,connected,submitting,current?.jobs.map(item=>[item.id,item.state])]);
  if (signature === key) return;
  signature = key;
  const version = ++generation;
  const known = job?.result ? verified.get(job.result.report_sha256) : null;
  renderCases(known || null); renderReport(job,known || null); renderHistory();
  if (job?.result && !known) {
    integrity(job).then(report => {
      if (version !== generation) return;
      if (!report) { $('integrity').textContent = t('integrityBad'); $('error').textContent = t('integrityBad'); $('error').hidden = false; return; }
      verified.set(job.result.report_sha256,report);
      renderCases(report); renderReport(job,report);
    }).catch(()=>{ if(version===generation) { $('integrity').textContent=t('integrityBad'); } });
  }
}

async function refresh() {
  try {
    const response = await fetch('/api/state',{cache:'no-store'});
    if(!response.ok) throw new Error(`HTTP ${response.status}`);
    current = await response.json(); connected = true;
    if (!selected) selected = current.jobs.find(job=>job.kind==='verification')?.id || null;
  } catch { connected = false; }
  render();
  setTimeout(refresh,1500);
}

applyLanguage(); refresh();
