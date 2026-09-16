# The embedded localized web asset intentionally contains long CSS/JS lines and Cyrillic text.
# ruff: noqa: E501, RUF001
"""Loopback-only browser workspace for the isolated MNIST demonstration."""

from __future__ import annotations

import json
import secrets
import threading
import uuid
import webbrowser
from collections.abc import Mapping
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, ClassVar, cast
from urllib.parse import urlsplit

from deltatorrent.benchmark.mnist_delta_nodes import (
    NODE_COUNT,
    REQUIRED_VOTE_KINDS,
    TRACE_SCOPE,
    TYPED_CERTIFICATE_VERIFIER,
    VOTE_QUORUM_COMPONENT,
)
from deltatorrent.benchmark.mnist_demo import (
    MnistDemoError,
    _dataset_catalog,
    _model_plugin_catalog,
    run_mnist_demo,
)
from deltatorrent.data.base import ContractCompatibilityError
from deltatorrent.data.registry import get_default_dataset_registry
from deltatorrent.model_plugins.registry import get_default_registry as get_default_model_registry
from deltatorrent.model_plugins.runner import (
    VALID_EXECUTION_SCOPES,
    ModelPluginRunnerError,
    validate_model_dataset_capability,
)

WORKSPACE_HTML = r"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DeltaReduce · Распределённый MNIST</title>
  <style>
    :root {
      color-scheme: dark;
      font-family: Inter, "Segoe UI", system-ui, sans-serif;
      --bg: #07111d;
      --panel: #0e1d2c;
      --panel-2: #13273a;
      --line: #274159;
      --text: #f4f8fc;
      --muted: #9bb0c4;
      --cyan: #55d6e8;
      --green: #4ee29a;
      --amber: #ffc857;
      --red: #ff7185;
    }
    * { box-sizing: border-box; }
    body { margin: 0; background: radial-gradient(circle at 85% 0, #123752, var(--bg) 34%); color: var(--text); }
    main { width: min(1220px, calc(100% - 32px)); margin: auto; padding: 28px 0 70px; }
    header { display: flex; justify-content: space-between; align-items: center; gap: 18px; margin-bottom: 22px; }
    .brand { font-weight: 850; letter-spacing: .02em; }
    .mode { padding: 7px 11px; border: 1px solid #256f72; border-radius: 999px; color: #7ff4df; background: #0b2b31; font-size: 12px; font-weight: 800; }
    .hero { display: grid; grid-template-columns: 1.7fr .8fr; gap: 20px; padding: 30px; border: 1px solid var(--line); border-radius: 22px; background: linear-gradient(135deg, #102942, #0c1826); box-shadow: 0 24px 80px #0007; }
    h1 { margin: 8px 0 12px; font-size: clamp(34px, 5vw, 62px); line-height: .98; letter-spacing: -.04em; }
    h2 { margin: 0 0 16px; font-size: 24px; }
    h3 { margin: 0 0 8px; font-size: 16px; }
    p { color: var(--muted); line-height: 1.55; }
    button { border: 0; border-radius: 12px; cursor: pointer; font: inherit; font-weight: 800; }
    #run { width: 100%; min-height: 68px; padding: 14px 20px; color: #03251b; background: linear-gradient(135deg, #79f0b4, #42cde5); font-size: 18px; box-shadow: 0 12px 35px #42cde533; }
    #run:disabled { cursor: wait; filter: grayscale(.45); opacity: .7; }
    .hero-note { margin: 14px 0 0; font-size: 13px; }
    .panel { margin-top: 20px; padding: 22px; border: 1px solid var(--line); border-radius: 18px; background: #0b1927e8; }
    .status-grid { display: grid; grid-template-columns: 1fr auto; gap: 12px; align-items: center; }
    .progress { height: 10px; overflow: hidden; border-radius: 999px; background: #182b3c; }
    .progress > div { width: 0; height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--green), var(--cyan)); transition: width .35s ease; }
    #stage { color: var(--cyan); font-weight: 750; }
    .events { display: grid; gap: 7px; margin-top: 14px; color: var(--muted); font-size: 13px; }
    .event { display: flex; gap: 9px; }
    .event::before { content: "✓"; color: var(--green); font-weight: 900; }
    #results[hidden], #status-panel[hidden] { display: none; }
    .kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-top: 20px; }
    .kpi { padding: 20px; border: 1px solid var(--line); border-radius: 16px; background: var(--panel); }
    .kpi-label { color: var(--muted); font-size: 13px; }
    .kpi-value { margin-top: 7px; font-size: 31px; font-weight: 900; }
    .ok { color: var(--green); }
    .warn { color: var(--amber); }
    .flow { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
    .node { position: relative; padding: 17px; border: 1px solid #2b4f66; border-radius: 14px; background: var(--panel-2); }
    .node::after { content: "↓ signed canonical int16 delta"; position: absolute; left: 0; right: 0; bottom: -27px; color: var(--cyan); text-align: center; font-size: 10px; }
    .node-digits { display: flex; gap: 5px; flex-wrap: wrap; margin: 12px 0; }
    .digit-pill { display: grid; place-items: center; width: 28px; height: 28px; border-radius: 8px; color: #062634; background: var(--cyan); font-weight: 900; }
    .node-meta { color: var(--muted); font-size: 12px; }
    .aggregate { width: min(480px, 100%); margin: 46px auto 0; padding: 17px; border: 1px solid #2c7557; border-radius: 14px; text-align: center; background: #0d2c25; }
    .execution-path { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
    .execution-step { position: relative; min-height: 92px; padding: 14px; border: 1px solid #2b4f66; border-radius: 12px; background: var(--panel-2); }
    .execution-step::after { content: "→"; position: absolute; right: -10px; top: 35%; z-index: 2; color: var(--green); font-weight: 900; }
    .execution-step:nth-child(3n)::after, .execution-step:last-child::after { content: ""; }
    .execution-kind { margin-top: 7px; color: var(--muted); font-size: 11px; }
    .switches { display: flex; flex-wrap: wrap; gap: 9px; margin-bottom: 20px; }
    .switches button { padding: 10px 14px; color: var(--muted); background: #142536; }
    .switches button.active { color: #06251c; background: var(--green); }
    .legend { display: flex; gap: 18px; margin: 8px 0 18px; color: var(--muted); font-size: 12px; }
    .legend span::before { content: ""; display: inline-block; width: 10px; height: 10px; margin-right: 6px; border-radius: 3px; background: var(--cyan); }
    .legend .candidate::before { background: var(--green); }
    .legend .candidate.failure::before { background: var(--amber); }
    .chart { display: grid; gap: 11px; }
    .bar-row { display: grid; grid-template-columns: 26px 1fr 78px; gap: 10px; align-items: center; }
    .bars { position: relative; height: 28px; border-radius: 8px; background: #142536; overflow: hidden; }
    .bar { position: absolute; left: 0; height: 50%; transition: width .5s ease; }
    .bar.central { top: 0; background: var(--cyan); opacity: .62; }
    .bar.candidate { bottom: 0; background: var(--green); }
    .bar.failure { background: var(--amber); }
    .bar-value { color: var(--muted); font-variant-numeric: tabular-nums; text-align: right; font-size: 12px; }
    .failure-note { margin-top: 16px; padding: 14px; border-left: 4px solid var(--amber); background: #2a230f; color: #ffe3a1; }
    .gallery { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }
    .sample { padding: 12px; border: 1px solid var(--line); border-radius: 14px; background: var(--panel-2); text-align: center; }
    .sample.wrong { border-color: #784356; }
    canvas { width: 100%; max-width: 132px; aspect-ratio: 1; image-rendering: pixelated; border-radius: 10px; background: #02070c; }
    .sample-label { margin-top: 8px; font-size: 12px; color: var(--muted); }
    .table-wrap { overflow-x: auto; }
    .binding-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
    .binding-item { padding: 15px; border: 1px solid #2b4f66; border-radius: 12px; background: var(--panel-2); }
    .binding-label { color: var(--muted); font-size: 12px; }
    .binding-value { margin-top: 6px; font-size: 18px; font-weight: 850; }
    .binding-code { margin-top: 6px; color: var(--cyan); font-size: 12px; overflow-wrap: anywhere; }
    .temporal-chain { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin: 16px 0; }
    .temporal-step { min-height: 94px; padding: 14px; border: 1px solid #2b4f66; border-radius: 12px; background: var(--panel-2); }
    .temporal-step strong { display: block; margin-bottom: 8px; }
    .temporal-step span { color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }
    .observation-layout { display: grid; grid-template-columns: .82fr 1.28fr; gap: 12px; }
    .observation-card { padding: 16px; border: 1px solid #33485c; border-radius: 12px; background: #151e27; }
    .observation-card h3 { margin-bottom: 14px; }
    .observation-row { display: grid; grid-template-columns: 1fr auto; gap: 12px; margin-top: 10px; color: var(--muted); font-size: 13px; }
    .observation-row strong { color: var(--text); text-align: right; }
    .eeg-card { min-height: 198px; }
    .eeg-title { display: flex; justify-content: space-between; gap: 12px; margin-bottom: 8px; font-size: 13px; }
    .eeg-title span { color: var(--muted); }
    .eeg-svg { width: 100%; height: 132px; display: block; }
    .model-observations { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 12px; }
    .model-observation { padding: 13px; border: 1px solid #33485c; border-radius: 10px; background: #111b25; }
    .model-observation-title { color: var(--muted); font-size: 12px; }
    .model-observation-finding { margin-top: 8px; font-weight: 850; }
    .model-observation-confidence { margin-top: 4px; color: var(--muted); font-size: 12px; }
    .observation-note { margin-top: 16px; padding: 14px; border-radius: 10px; background: #202326; color: #dbe5ee; font-size: 13px; line-height: 1.45; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 12px; border-bottom: 1px solid var(--line); text-align: left; font-size: 13px; }
    th { color: var(--muted); }
    .boundary { border-color: #685c2c; background: #251f0e; }
    .boundary strong { color: var(--amber); }
    .error { color: #ffd5dc; border-color: #713040; background: #2b121a; }
    footer { margin-top: 24px; color: #71869a; font-size: 12px; text-align: center; }
    @media (max-width: 820px) {
      .hero { grid-template-columns: 1fr; }
      .kpis, .flow, .execution-path, .binding-grid, .temporal-chain, .model-observations { grid-template-columns: repeat(2, 1fr); }
      .observation-layout { grid-template-columns: 1fr; }
      .gallery { grid-template-columns: repeat(2, 1fr); }
    }
    @media (max-width: 520px) {
      .kpis, .flow, .execution-path, .binding-grid, .temporal-chain, .model-observations { grid-template-columns: 1fr; }
      .gallery { grid-template-columns: 1fr 1fr; }
    }
  </style>
</head>
<body>
<main>
  <header>
    <div class="brand">Δ DeltaReduce</div>
    <div class="mode">LOCAL DEMO ONLY · НЕ GOVERNANCE</div>
  </header>
  <section class="hero">
    <div>
      <div>Распределённое обучение, которое можно увидеть</div>
      <h1>Четыре узла.<br>Десять цифр.<br>Один результат.</h1>
      <p>Настоящий MNIST, непересекающиеся локальные шарды и общий test set. Вклады
         проходят через Delta vote/QC и отдельный Stage C REAL_DRQ1 путь до Apply/WAL.</p>
    </div>
    <div>
      <button id="run">Запустить демо</button>
      <p class="hero-note">Первый запуск проверит и при необходимости загрузит 11 МБ
        закреплённых gzip-файлов. Последующие запуски работают из локального кэша.</p>
    </div>
  </section>

  <section id="status-panel" class="panel" hidden>
    <div class="status-grid"><strong id="stage">Подготовка</strong><span id="percent">0%</span></div>
    <div class="progress"><div id="progress-bar"></div></div>
    <div id="message"></div>
    <div id="events" class="events"></div>
  </section>

  <section id="results" hidden>
    <div class="kpis">
      <div class="kpi"><div class="kpi-label">Централизованная точность</div><div id="central-accuracy" class="kpi-value"></div></div>
      <div class="kpi"><div class="kpi-label">Распределённая точность</div><div id="distributed-accuracy" class="kpi-value ok"></div></div>
      <div class="kpi"><div class="kpi-label">Совпадение модели</div><div id="model-match" class="kpi-value ok"></div></div>
      <div class="kpi"><div class="kpi-label">Delta terminal</div><div id="delta-terminal" class="kpi-value ok"></div></div>
    </div>

    <section class="panel">
      <h2>ModelPlugin ↔ DatasetProvider</h2>
      <p>Модель и данные выбираются как независимые registry-записи. Перед запуском
         worker-ов runner проверяет совпадение sample/target contract.</p>
      <div class="binding-grid">
        <div class="binding-item">
          <div class="binding-label">ModelPlugin</div>
          <div id="model-plugin-name" class="binding-value"></div>
          <div id="model-plugin-id" class="binding-code"></div>
        </div>
        <div class="binding-item">
          <div class="binding-label">DatasetProvider</div>
          <div id="dataset-provider-name" class="binding-value"></div>
          <div id="dataset-provider-id" class="binding-code"></div>
        </div>
        <div class="binding-item">
          <div class="binding-label">Contract</div>
          <div id="binding-contract" class="binding-value ok"></div>
          <div id="binding-kinds" class="binding-code"></div>
        </div>
      </div>
    </section>

    <section class="panel">
      <h2>Мульти-доменная структура</h2>
      <p>Демо теперь строит один registry-backed multi-domain contract. Requested scope
         отделён от verified evidence: capability можно показать заранее, но APPLIED/WAL/checkpoint
         показываются только из receipt текущего запуска. QLoRA anchor остаётся historical reference,
         а EEG проверяет model/data boundary без consensus claim.</p>
      <div id="multi-domain-grid" class="binding-grid"></div>
    </section>

    <section class="panel">
      <h2>EEG плагин подключён к той же границе</h2>
      <p>В этом же запуске проверяется второй домен: синтетические EEG-окна проходят через
         DatasetProvider и ModelPlugin. Каждое окно привязано к конкретному InterventionEvent
         через immutable ID/hash context. Это registry/worker smoke, не Stage C claim.</p>
      <div class="binding-grid">
        <div class="binding-item">
          <div class="binding-label">EEG ModelPlugin</div>
          <div id="eeg-plugin-name" class="binding-value"></div>
          <div id="eeg-plugin-id" class="binding-code"></div>
        </div>
        <div class="binding-item">
          <div class="binding-label">Smoke evaluation</div>
          <div id="eeg-plugin-accuracy" class="binding-value ok"></div>
          <div id="eeg-plugin-workers" class="binding-code"></div>
        </div>
        <div class="binding-item">
          <div class="binding-label">Boundary</div>
          <div id="eeg-plugin-boundary" class="binding-value warn"></div>
          <div id="eeg-plugin-kinds" class="binding-code"></div>
        </div>
      </div>
    </section>

    <section class="panel">
      <h2>Intervention EEG Explorer</h2>
      <div class="observation-layout">
        <article class="observation-card">
          <h3>Event metadata</h3>
          <div class="observation-row"><span>Point</span><strong id="obs-point"></strong></div>
          <div class="observation-row"><span>Side</span><strong id="obs-side"></strong></div>
          <div class="observation-row"><span>Event</span><strong id="obs-event"></strong></div>
          <div class="observation-row"><span>Decision</span><strong id="obs-binding"></strong></div>
          <div class="observation-row"><span>Provider</span><strong id="obs-source"></strong></div>
        </article>
        <article class="observation-card eeg-card">
          <div class="eeg-title"><strong>EEG Timeline</strong><span>baseline → t=0 → post-event</span></div>
          <svg class="eeg-svg" viewBox="0 0 560 140" role="img" aria-label="EEG window around intervention event">
            <path d="M32 74 L56 54 L80 88 L104 56 L128 82 L152 58 L176 78 L200 56 L224 92 L248 66 L272 78 L296 62 L320 72 L344 48 L368 88 L392 54 L416 84 L440 58 L464 82 L488 62 L512 86 L536 70" fill="none" stroke="#4e9b21" stroke-width="3" />
            <line x1="312" y1="26" x2="312" y2="116" stroke="#ffd45e" stroke-width="2" stroke-dasharray="5 6" />
            <text x="288" y="22" fill="#f4f8fc" font-size="11">event t=0</text>
            <text x="42" y="126" fill="#dbe5ee" font-size="11">baseline</text>
            <text x="488" y="126" fill="#dbe5ee" font-size="11">post</text>
          </svg>
        </article>
      </div>
      <h3>Response</h3>
      <div id="observation-models" class="model-observations"></div>
      <div class="observation-note">
        This view records an observed association between a clinician/protocol-defined intervention
        event and EEG windows. It does not select a treatment point or prescribe an intervention.
      </div>
    </section>

    <section class="panel">
      <h2>Binding Provenance</h2>
      <p>Физиологическое окно связано не с именем точки напрямую, а с конкретным
         InterventionEvent. BindingProvider предлагает PROPOSED assertions, BindingAuthority
         принимает решение, а DatasetProvider материализует только accepted bindings.</p>
      <div class="temporal-chain">
        <div class="temporal-step"><strong>InterventionEvent</strong><span id="temporal-event-id"></span></div>
        <div class="temporal-step"><strong>ObservationSession</strong><span id="temporal-session-id"></span></div>
        <div class="temporal-step"><strong>EegWindow</strong><span id="temporal-window-id"></span></div>
        <div class="temporal-step"><strong>BindingAssertion</strong><span id="temporal-assertion-id"></span></div>
        <div class="temporal-step"><strong>BindingDecision</strong><span id="temporal-decision-id"></span></div>
        <div class="temporal-step"><strong>ResolvedBindingSet</strong><span id="temporal-resolved-id"></span></div>
        <div class="temporal-step"><strong>DataPartition</strong><span id="temporal-ticket-context"></span></div>
      </div>
      <div class="binding-grid">
        <div class="binding-item">
          <div class="binding-label">Assertions</div>
          <div id="temporal-binding-count" class="binding-value ok"></div>
          <div id="temporal-window-count" class="binding-code"></div>
        </div>
        <div class="binding-item">
          <div class="binding-label">Contract</div>
          <div id="temporal-binding-contract" class="binding-value"></div>
          <div id="temporal-binding-schema" class="binding-code"></div>
        </div>
        <div class="binding-item">
          <div class="binding-label">Delta boundary</div>
          <div id="temporal-binding-boundary" class="binding-value warn"></div>
          <div id="temporal-binding-safety" class="binding-code"></div>
        </div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Worker</th><th>Event / point</th><th>Window</th><th>Decision</th><th>Binding</th></tr></thead>
          <tbody id="temporal-binding-rows"></tbody>
        </table>
      </div>
    </section>

    <section class="panel">
      <h2>Данные остаются на четырёх узлах</h2>
      <p>Каждый Python worker читает только собственный шард и формирует локальный
        квантованный вклад. Необработанные изображения между узлами не передаются.</p>
      <div id="nodes" class="flow"></div>
      <div class="aggregate"><strong>Детерминированное объединение</strong><br><span id="aggregate-copy"></span></div>
    </section>

    <section class="panel">
      <h2>Фактический execution path</h2>
      <p>Карточки ниже строятся из проверенного trace текущего запуска. Только зелёная
         цепочка до <strong>APPLIED</strong> допускает показ результата.</p>
      <div id="execution-steps" class="execution-path"></div>
    </section>

    <section class="panel">
      <h2>Покажи различия по цифрам</h2>
      <div class="switches">
        <button id="healthy-view" class="active">Все 4 узла</button>
        <button id="failure-view">Отказ и восстановление</button>
      </div>
      <div class="legend"><span>Централизованно</span><span id="selected-legend" class="candidate">Распределённо, 4/4</span></div>
      <div id="digit-chart" class="chart"></div>
      <div id="failure-note" class="failure-note" hidden></div>
    </section>

    <section class="panel">
      <h2>Что модель увидела на общем test set</h2>
      <p>По одному фактическому примеру каждой цифры. Изображения рисуются из измеренного
        отчёта, а не из заранее подготовленного макета.</p>
      <div id="gallery" class="gallery"></div>
    </section>

    <section class="panel">
      <h2>Фактические измерения</h2>
      <div class="table-wrap"><table><thead><tr><th>Контур</th><th>Образцы</th><th>Время</th><th>Передано</th></tr></thead><tbody id="measurements"></tbody></table></div>
    </section>

    <section class="panel boundary">
      <strong>Честная граница демонстрации.</strong>
       <p>Это локальный loopback deployment adapter поверх неизменённых библиотек Delta,
          а не готовый production node, TLS/WAN или multi-region запуск. Ed25519 защищает
          demo-транспорт; native vote signatures остаются локальными content-ID placeholders.
          Демо не создаёт DefinitionQC, ResultQC, Feature 010 GO или полномочий Campaign 02.</p>
    </section>
  </section>
  <footer>MNIST: LeCun, Cortes, Burges · исходные gzip-файлы проверяются по SHA-256</footer>
</main>
<script nonce="__CSP_NONCE__">
  const demoToken = __DEMO_TOKEN__;
  const runButton = document.getElementById('run');
  const statusPanel = document.getElementById('status-panel');
  const results = document.getElementById('results');
  const stage = document.getElementById('stage');
  const percent = document.getElementById('percent');
  const message = document.getElementById('message');
  const progressBar = document.getElementById('progress-bar');
  const events = document.getElementById('events');
  let currentReport = null;

  const formatAccuracy = ppm => `${(ppm / 10000).toFixed(2)}%`;
  const formatBytes = bytes => bytes >= 1048576
    ? `${(bytes / 1048576).toFixed(1)} МБ`
    : `${(bytes / 1024).toFixed(1)} КБ`;

  function renderNodes(report) {
    const target = document.getElementById('nodes');
    target.replaceChildren();
    report.distributed.nodes.forEach(node => {
      const card = document.createElement('article');
      card.className = 'node';
      const title = document.createElement('h3');
      title.textContent = node.node_id;
      const digits = document.createElement('div');
      digits.className = 'node-digits';
      node.allowed_digits.forEach(value => {
        const pill = document.createElement('span');
        pill.className = 'digit-pill';
        pill.textContent = value;
        digits.appendChild(pill);
      });
      const meta = document.createElement('div');
      meta.className = 'node-meta';
      meta.textContent = `${node.label_counts.reduce((a, b) => a + b, 0).toLocaleString('ru-RU')} локальных изображений · PID ${node.process_id}`;
      card.append(title, digits, meta);
      target.appendChild(card);
    });
  }

  function renderExecutionPath(report) {
    const target = document.getElementById('execution-steps');
    target.replaceChildren();
    report.delta_execution.components.forEach(step => {
      const card = document.createElement('article');
      card.className = 'execution-step';
      const title = document.createElement('strong');
      title.textContent = `${step.sequence}. ${step.component}`;
      const kind = document.createElement('div');
      kind.className = 'execution-kind';
      kind.textContent = `${step.implementation_class} · ${step.status}`;
      card.append(title, kind);
      target.appendChild(card);
    });
    const stageC = document.createElement('article');
    stageC.className = 'execution-step';
    const title = document.createElement('strong');
    title.textContent = 'REAL_DRQ1 Stage C / Feature008';
    const kind = document.createElement('div');
    kind.className = 'execution-kind';
    kind.textContent = `${report.stage_c_execution.worker_count} worker DRQ1 → ${report.stage_c_execution.missing_work_policy_result} → ${report.stage_c_execution.outcome}`;
    stageC.append(title, kind);
    target.appendChild(stageC);
  }

  function renderBinding(report) {
    document.getElementById('model-plugin-name').textContent = report.model.display_name;
    document.getElementById('model-plugin-id').textContent = report.model.plugin_id;
    document.getElementById('dataset-provider-name').textContent = report.dataset.display_name;
    document.getElementById('dataset-provider-id').textContent = report.dataset.dataset_id;
    document.getElementById('binding-contract').textContent = report.model_dataset_binding.contract_compatibility;
    document.getElementById('binding-kinds').textContent = `${report.model_dataset_binding.sample_kind} → ${report.model_dataset_binding.target_kind}`;
  }

  function renderEegShowcase(report) {
    const eeg = report.plugin_showcase.eeg_bandpower;
    const firstContext = eeg.workers[0].first_ticket_context;
    document.getElementById('eeg-plugin-name').textContent = eeg.display_name;
    document.getElementById('eeg-plugin-id').textContent = `${eeg.model_plugin_id} + ${eeg.dataset_id}`;
    document.getElementById('eeg-plugin-accuracy').textContent = formatAccuracy(eeg.mean_local_accuracy_ppm);
    document.getElementById('eeg-plugin-workers').textContent = `${eeg.worker_count} EEG partitions · ${eeg.total_elements} checkpoint coords`;
    document.getElementById('eeg-plugin-boundary').textContent = eeg.plugin_scope;
    document.getElementById('eeg-plugin-kinds').textContent = `${eeg.sample_kind} → ${eeg.target_kind}; event ${firstContext.intervention_event_id}; window ${firstContext.data_window_id}; decision ${firstContext.binding_decision_id.slice(0, 19)}…; Stage C claim: ${eeg.delta_stage_c_execution_claimed}`;
  }

  function renderTemporalBinding(report) {
    const binding = report.plugin_showcase.eeg_bandpower.temporal_binding;
    const first = binding.examples[0];
    document.getElementById('temporal-event-id').textContent = `${first.intervention_event_id} · ${first.point_id}`;
    document.getElementById('temporal-session-id').textContent = first.session_id;
    document.getElementById('temporal-window-id').textContent = `${first.data_window_id} · ${first.relation}`;
    document.getElementById('temporal-assertion-id').textContent = first.binding_assertion_id;
    document.getElementById('temporal-decision-id').textContent = `${first.authority_decision} · ${first.binding_decision_id}`;
    document.getElementById('temporal-resolved-id').textContent = first.resolved_binding_set_id;
    document.getElementById('temporal-ticket-context').textContent = 'IDs/hashes only';
    document.getElementById('temporal-binding-count').textContent = `${binding.accepted_count} accepted`;
    document.getElementById('temporal-window-count').textContent = `${binding.window_count} windows · ${binding.event_count} events`;
    document.getElementById('temporal-binding-contract').textContent = 'event_id equality';
    document.getElementById('temporal-binding-schema').textContent = `${binding.binding_layer} · schema ${binding.assertion_schema_version}`;
    document.getElementById('temporal-binding-boundary').textContent = binding.delta_spine_knows_medical_semantics ? 'LEAK' : 'NO MEDICAL SEMANTICS';
    document.getElementById('temporal-binding-safety').textContent = `provider ${binding.binding_provider_type}; rejected ${binding.rejected_count}; review ${binding.review_count}`;

    const rows = document.getElementById('temporal-binding-rows');
    rows.replaceChildren();
    binding.examples.forEach(example => {
      const row = document.createElement('tr');
      const worker = document.createElement('td');
      worker.textContent = example.partition_id;
      const event = document.createElement('td');
      event.textContent = `${example.intervention_event_id} / ${example.point_id}`;
      const windowCell = document.createElement('td');
      windowCell.textContent = `${example.data_window_id} · ${example.relation}`;
      const decision = document.createElement('td');
      decision.textContent = `${example.authority_decision} · ${example.reason_code}`;
      const assertion = document.createElement('td');
      assertion.textContent = `${example.binding_assertion_id.slice(0, 19)}… / ${example.binding_decision_id.slice(0, 19)}…`;
      row.append(worker, event, windowCell, decision, assertion);
      rows.appendChild(row);
    });
  }

  function renderObservationView(report) {
    const eeg = report.plugin_showcase.eeg_bandpower;
    const binding = eeg.temporal_binding;
    const response = eeg.observation_demo.response;
    const first = binding.examples[0];
    document.getElementById('obs-point').textContent = first.point_id;
    document.getElementById('obs-side').textContent = first.laterality.toUpperCase();
    document.getElementById('obs-event').textContent = first.intervention_event_id;
    document.getElementById('obs-binding').textContent = first.authority_decision;
    document.getElementById('obs-source').textContent = `${first.binding_provider_type} → ${first.binding_authority_id}`;

    const models = [
      {
        title: 'Bandpower response',
        finding: response.observation,
        confidence: `alpha Δ ${response.alpha_delta_ppm} ppm · beta Δ ${response.beta_delta_ppm} ppm`,
      },
      {
        title: eeg.display_name,
        finding: `${formatAccuracy(eeg.mean_local_accuracy_ppm)} local smoke`,
        confidence: `actual plugin · ${eeg.model_plugin_id}`,
      },
      {
        title: 'Clinical boundary',
        finding: response.clinical_conclusion_claimed ? 'clinical claim present' : 'observations only',
        confidence: response.recommendation_claimed ? 'recommendation claim present' : 'no recommendation',
      },
    ];
    const target = document.getElementById('observation-models');
    target.replaceChildren();
    models.forEach(item => {
      const card = document.createElement('article');
      card.className = 'model-observation';
      const title = document.createElement('div');
      title.className = 'model-observation-title';
      title.textContent = item.title;
      const finding = document.createElement('div');
      finding.className = 'model-observation-finding';
      finding.textContent = item.finding;
      const confidence = document.createElement('div');
      confidence.className = 'model-observation-confidence';
      confidence.textContent = item.confidence;
      card.append(title, finding, confidence);
      target.appendChild(card);
    });
  }

  function renderMultiDomain(report) {
    const target = document.getElementById('multi-domain-grid');
    target.replaceChildren();
    report.multi_domain.domains.forEach(domain => {
      const card = document.createElement('article');
      card.className = 'binding-item';
      const label = document.createElement('div');
      label.className = 'binding-label';
      label.textContent = domain.role;
      const value = document.createElement('div');
      value.className = `binding-value${domain.delta_stage_c_execution_claimed ? ' ok' : ' warn'}`;
      value.textContent = domain.domain_id;
      const code = document.createElement('div');
      code.className = 'binding-code';
      const requested = domain.requested_execution_scope || 'UNSPECIFIED_REQUEST';
      const evidence = domain.verified_execution_evidence || 'NO_VERIFIED_EXECUTION_EVIDENCE';
      const capability = domain.supports_stage_c_real_drq1 ? 'Stage C capable' : 'no Stage C capability';
      const stage = domain.live_consensus_claimed_in_this_run
        ? `${domain.stage_c_execution_mode} → ${domain.stage_c_outcome}`
        : `requested ${requested}; evidence ${evidence}; ${capability}`;
      code.textContent = `${domain.model_plugin_id} + ${domain.dataset_id}; ${stage}; ${domain.sample_kind} → ${domain.target_kind}`;
      card.append(label, value, code);
      target.appendChild(card);
    });
  }

  function renderChart(report, failure) {
    const central = report.centralized.evaluation.per_digit;
    const candidate = failure
      ? report.failure_simulation.evaluation.per_digit
      : report.distributed.evaluation.per_digit;
    const chart = document.getElementById('digit-chart');
    chart.replaceChildren();
    for (let digit = 0; digit < 10; digit += 1) {
      const row = document.createElement('div');
      row.className = 'bar-row';
      const label = document.createElement('strong');
      label.textContent = digit;
      const bars = document.createElement('div');
      bars.className = 'bars';
      const reference = document.createElement('div');
      reference.className = 'bar central';
      reference.style.width = `${central[digit].accuracy_ppm / 10000}%`;
      const selected = document.createElement('div');
      selected.className = `bar candidate${failure ? ' failure' : ''}`;
      selected.style.width = `${candidate[digit].accuracy_ppm / 10000}%`;
      bars.append(reference, selected);
      const values = document.createElement('div');
      values.className = 'bar-value';
      const delta = (candidate[digit].accuracy_ppm - central[digit].accuracy_ppm) / 10000;
      values.textContent = `${formatAccuracy(candidate[digit].accuracy_ppm)} (${delta >= 0 ? '+' : ''}${delta.toFixed(2)})`;
      row.append(label, bars, values);
      chart.appendChild(row);
    }
    const note = document.getElementById('failure-note');
    const selectedLegend = document.getElementById('selected-legend');
    selectedLegend.classList.toggle('failure', failure);
    selectedLegend.textContent = failure ? 'validator-04: crash → replay → APPLIED' : 'Распределённо, 4/4';
    note.hidden = !failure;
    note.textContent = failure
      ? `validator-04 остановлен после durable Apply vote, затем восстановил journal и переиграл тот же vote. Итог: ${report.failure_simulation.status}; модель после recovery совпадает.`
      : '';
  }

  function drawDigit(canvas, pixels) {
    const context = canvas.getContext('2d');
    const image = context.createImageData(28, 28);
    pixels.forEach((value, index) => {
      image.data[index * 4] = value;
      image.data[index * 4 + 1] = value;
      image.data[index * 4 + 2] = value;
      image.data[index * 4 + 3] = 255;
    });
    context.putImageData(image, 0, 0);
  }

  function renderGallery(report, failure) {
    const gallery = document.getElementById('gallery');
    gallery.replaceChildren();
    report.examples.forEach(example => {
      const prediction = failure
        ? example.failure_prediction
        : example.distributed_prediction;
      const card = document.createElement('article');
      card.className = `sample${prediction === example.digit ? '' : ' wrong'}`;
      const canvas = document.createElement('canvas');
      canvas.width = 28;
      canvas.height = 28;
      const label = document.createElement('div');
      label.className = 'sample-label';
      label.textContent = `истина ${example.digit} · ${failure ? 'после recovery' : 'модель'} ${prediction}`;
      card.append(canvas, label);
      gallery.appendChild(card);
      drawDigit(canvas, example.pixels);
    });
  }

  function renderMeasurements(report) {
    const body = document.getElementById('measurements');
    body.replaceChildren();
    const totalPayload = report.distributed.nodes.reduce((sum, node) => sum + node.shared_contribution_bytes, 0);
    const rows = [
      ['Централизованный baseline', report.centralized.samples_seen, report.centralized.training_ms, 'локальная память'],
      ['4 MNIST worker-процесса', report.distributed.samples_seen, report.distributed.training_ms, formatBytes(totalPayload)],
      ['Java Netty loopback', 28, 'в составе прогона', '28 signed relay receipts'],
      ['Native Delta nodes', 4, 'в составе прогона', '24 votes → 24 QC results → APPLIED'],
      ['Stage C REAL_DRQ1', report.stage_c_execution.worker_count, 'checkpoint advanced', report.stage_c_execution.missing_work_policy_result],
      ['Crash/restart validator-04', 1, 'в составе прогона', report.failure_simulation.status],
    ];
    rows.forEach(values => {
      const row = document.createElement('tr');
      values.forEach((value, index) => {
        const cell = document.createElement('td');
        cell.textContent = index === 1 && typeof value === 'number'
          ? value.toLocaleString('ru-RU')
          : index === 2 && typeof value === 'number' ? `${value.toFixed(1)} мс` : value;
        row.appendChild(cell);
      });
      body.appendChild(row);
    });
  }

  function renderResult(report) {
    currentReport = report;
    document.getElementById('central-accuracy').textContent = formatAccuracy(report.centralized.evaluation.accuracy_ppm);
    document.getElementById('distributed-accuracy').textContent = formatAccuracy(report.distributed.evaluation.accuracy_ppm);
    document.getElementById('model-match').textContent = report.distributed.exact_model_match_with_centralized ? 'ПОБАЙТНО' : 'НЕТ';
    document.getElementById('delta-terminal').textContent = `${report.delta_execution.terminal_outcome} · ${report.stage_c_execution.execution_mode}`;
    document.getElementById('aggregate-copy').textContent = `Model artifact path: 24 durable votes → 24 Netty-fed QC results → Apply. Stage C evidence: ${report.stage_c_execution.worker_count} DRQ1 contributions → exact ISC ${report.stage_c_execution.isc_ticket_count}/4 → ${report.stage_c_execution.outcome}; checkpoint advanced.`;
    renderBinding(report);
    renderMultiDomain(report);
    renderEegShowcase(report);
    renderObservationView(report);
    renderTemporalBinding(report);
    renderNodes(report);
    renderExecutionPath(report);
    renderChart(report, false);
    renderGallery(report, false);
    renderMeasurements(report);
    results.hidden = false;
    results.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function updateStatus(snapshot) {
    statusPanel.hidden = false;
    stage.textContent = snapshot.stage;
    percent.textContent = `${snapshot.percent}%`;
    progressBar.style.width = `${snapshot.percent}%`;
    message.textContent = snapshot.message;
    events.replaceChildren();
    snapshot.events.slice(-5).forEach(text => {
      const item = document.createElement('div');
      item.className = 'event';
      item.textContent = text;
      events.appendChild(item);
    });
  }

  async function poll() {
    const response = await fetch('/api/status', { cache: 'no-store' });
    const snapshot = await response.json();
    updateStatus(snapshot);
    if (snapshot.error) {
      statusPanel.classList.add('error');
      runButton.disabled = false;
      runButton.textContent = 'Повторить демо';
      return;
    }
    if (snapshot.running) {
      setTimeout(poll, 450);
      return;
    }
    runButton.disabled = false;
    runButton.textContent = 'Запустить ещё раз';
    if (snapshot.result) renderResult(snapshot.result);
  }

  runButton.addEventListener('click', async () => {
    runButton.disabled = true;
    runButton.textContent = 'Демо выполняется…';
    results.hidden = true;
    statusPanel.classList.remove('error');
    const response = await fetch('/api/run', {
      method: 'POST',
      headers: { 'X-Demo-Token': demoToken },
    });
    if (!response.ok && response.status !== 409) {
      message.textContent = 'Не удалось запустить локальный demo runner.';
      runButton.disabled = false;
      return;
    }
    await poll();
  });

  document.getElementById('healthy-view').addEventListener('click', event => {
    if (!currentReport) return;
    document.getElementById('failure-view').classList.remove('active');
    event.currentTarget.classList.add('active');
    renderChart(currentReport, false);
    renderGallery(currentReport, false);
  });
  document.getElementById('failure-view').addEventListener('click', event => {
    if (!currentReport) return;
    document.getElementById('healthy-view').classList.remove('active');
    event.currentTarget.classList.add('active');
    renderChart(currentReport, true);
    renderGallery(currentReport, true);
  });
</script>
</body>
</html>
"""


def _workspace_catalog() -> dict[str, object]:
    """Return read-only registry descriptors and compatibility matrix for UI consumers."""
    model_plugins = _model_plugin_catalog()
    datasets = _dataset_catalog()
    model_registry = get_default_model_registry()
    dataset_registry = get_default_dataset_registry()
    model_descriptors = model_registry.list_descriptors()
    dataset_descriptors = dataset_registry.list_descriptors()
    compatibility: list[dict[str, object]] = []
    for model_descriptor in model_descriptors:
        for dataset_descriptor in dataset_descriptors:
            requested_scope_allowed: dict[str, bool] = {}
            for scope in VALID_EXECUTION_SCOPES:
                try:
                    validate_model_dataset_capability(
                        model_descriptor=model_descriptor,
                        dataset_descriptor=dataset_descriptor,
                        requested_scope=scope,
                    )
                except (ContractCompatibilityError, ModelPluginRunnerError):
                    requested_scope_allowed[scope] = False
                else:
                    requested_scope_allowed[scope] = True
            compatibility.append(
                {
                    "contract_compatible": requested_scope_allowed["PLUGIN_BOUNDARY"],
                    "dataset_id": dataset_descriptor.dataset_id,
                    "model_plugin_id": model_descriptor.plugin_id,
                    "requested_scope_allowed": requested_scope_allowed,
                    "supports_stage_c_real_drq1": (model_descriptor.supports_stage_c_real_drq1),
                }
            )
    return {
        "compatibility": compatibility,
        "datasets": datasets,
        "model_plugins": model_plugins,
        "register_exposed": False,
        "type_name": "DELTAREDUCE_WORKSPACE_PLUGIN_DATASET_CATALOG",
    }


def _validate_workspace_report(value: object) -> dict[str, object]:
    """Reject any report that cannot prove the displayed real-Delta path."""
    if not isinstance(value, dict):
        raise MnistDemoError("MNIST_WORKSPACE_REPORT_INVALID")
    delta = value.get("delta_execution")
    distributed = value.get("distributed")
    execution_path = value.get("execution_path")
    failure = value.get("failure_simulation")
    model = value.get("model")
    dataset = value.get("dataset")
    binding = value.get("model_dataset_binding")
    multi_domain = value.get("multi_domain")
    registry = value.get("registry")
    showcase = value.get("plugin_showcase")
    eeg_showcase = showcase.get("eeg_bandpower") if isinstance(showcase, dict) else None
    stage_c = value.get("stage_c_execution")
    multi_domain_domains = multi_domain.get("domains") if isinstance(multi_domain, dict) else None
    if (
        value.get("type_name") != "DELTAREDUCE_LOCAL_MNIST_DEMO_REPORT"
        or value.get("schema_version") != "2.0.0"
        or value.get("demo_status") != "DEMO_PASS"
        or value.get("environment") != "LOCAL_DEMO_ONLY"
        or value.get("authoritative") is not False
        or value.get("governance_eligible") is not False
        or value.get("execution_authorized") is not False
        or value.get("feature_010_go_claimed") is not False
        or not isinstance(delta, dict)
        or not isinstance(distributed, dict)
        or not isinstance(execution_path, dict)
        or not isinstance(failure, dict)
        or not isinstance(model, dict)
        or not isinstance(dataset, dict)
        or not isinstance(binding, dict)
        or not isinstance(multi_domain, dict)
        or not isinstance(multi_domain_domains, list)
        or not isinstance(registry, dict)
        or not isinstance(showcase, dict)
        or not isinstance(eeg_showcase, dict)
        or not isinstance(showcase.get("qlora_adapter"), dict)
        or not isinstance(stage_c, dict)
    ):
        raise MnistDemoError("MNIST_WORKSPACE_REPORT_INVALID")
    qlora_showcase = cast(dict[str, Any], showcase["qlora_adapter"])
    mnist_domain = next(
        (
            item
            for item in multi_domain_domains
            if isinstance(item, dict) and item.get("domain_id") == "mnist-image"
        ),
        None,
    )
    qlora_domain = next(
        (
            item
            for item in multi_domain_domains
            if isinstance(item, dict) and item.get("domain_id") == "qlora-adapter"
        ),
        None,
    )
    eeg_domain = next(
        (
            item
            for item in multi_domain_domains
            if isinstance(item, dict) and item.get("domain_id") == "eeg-bandpower"
        ),
        None,
    )
    model_catalog = registry.get("model_plugins")
    dataset_catalog = registry.get("datasets")
    eeg_workers = eeg_showcase.get("workers")
    qlora_workers = qlora_showcase.get("workers")
    first_eeg_worker = (
        eeg_workers[0]
        if isinstance(eeg_workers, list) and eeg_workers and isinstance(eeg_workers[0], dict)
        else None
    )
    first_qlora_worker = (
        qlora_workers[0]
        if isinstance(qlora_workers, list) and qlora_workers and isinstance(qlora_workers[0], dict)
        else None
    )
    first_eeg_context = (
        first_eeg_worker.get("first_ticket_context") if isinstance(first_eeg_worker, dict) else None
    )
    temporal_binding = (
        eeg_showcase.get("temporal_binding") if isinstance(eeg_showcase, dict) else None
    )
    observation_demo = (
        eeg_showcase.get("observation_demo") if isinstance(eeg_showcase, dict) else None
    )
    observation_response = (
        observation_demo.get("response") if isinstance(observation_demo, dict) else None
    )
    temporal_examples = (
        temporal_binding.get("examples") if isinstance(temporal_binding, dict) else None
    )
    first_temporal_example = (
        temporal_examples[0]
        if isinstance(temporal_examples, list)
        and temporal_examples
        and isinstance(temporal_examples[0], dict)
        else None
    )
    components = delta.get("components")
    toolchain = delta.get("toolchain")
    source_snapshot = toolchain.get("source_snapshot") if isinstance(toolchain, dict) else None
    required_components = (
        "deltatorrent.benchmark.mnist_demo",
        "io.deltareduce.demo.MnistDeltaNettyRelay",
        "delta::runtime::CertificateVoteRuntime",
        VOTE_QUORUM_COMPONENT,
        TYPED_CERTIFICATE_VERIFIER,
        "delta::robust::build_plan",
        "delta::robust::reduce_parameter_shard",
        "delta::apply::compute_candidate",
        "delta::runtime::CurrentPointerStore",
    )
    phase_execution = delta.get("phase_execution")
    certificates = delta.get("quorum_certificates")
    current_pointer = delta.get("current_pointer")
    if (
        delta.get("status") != "PASS"
        or delta.get("terminal_outcome") != "APPLIED"
        or delta.get("classification") != "LOCAL_DEMO_ONLY"
        or delta.get("authoritative") is not False
        or delta.get("governance_eligible") is not False
        or delta.get("execution_authorized") is not False
        or delta.get("formal_refinement_claimed") is not False
        or delta.get("semantic_completeness_claimed") is not False
        or delta.get("trace_scope") != TRACE_SCOPE
        or delta.get("python_cross_node_aggregation_performed") is not False
        or delta.get("python_vote_quorum_assembly_performed") is not False
        or delta.get("demo_owned_aggregation") is not False
        or delta.get("distributed_orchestrator_received_node_local_numeric_arrays") is not False
        or delta.get("contributions_bound_netty_to_native") is not True
        or delta.get("aggregation_authority") != "delta::robust::reduce_parameter_shard"
        or delta.get("protocol_scope") != "MNIST_WORKLOAD_TO_APPLIED_LOCAL_DELTA"
        or delta.get("vote_quorum_component") != VOTE_QUORUM_COMPONENT
        or delta.get("typed_certificate_verifier") != TYPED_CERTIFICATE_VERIFIER
        or delta.get("native_cryptographic_signatures_verified") is not False
        or delta.get("certificate_signature_semantics") != "CONTENT_ID_PLACEHOLDER_LOCAL_DEMO_ONLY"
        or delta.get("phase_ordering_enforced") is not True
        or distributed.get("native_runtime_terminal") != "APPLIED"
        or distributed.get("parallel_processes_observed") != 4
        or distributed.get("worker_processes_required") != 4
        or distributed.get("exact_model_match_with_centralized") is not True
        or distributed.get("applied_model_file_sha256") != delta.get("applied_model_file_sha256")
        or distributed.get("stage_c_execution_mode") != "REAL_DRQ1"
        or distributed.get("stage_c_checkpoint_advanced") is not True
        or execution_path.get("trace_id") != delta.get("execution_path_id")
        or execution_path.get("acceptance_status") != "PASS"
        or execution_path.get("aggregation_owner") != "delta::robust::reduce_parameter_shard"
        or execution_path.get("terminal_outcome") != "APPLIED"
        or execution_path.get("centralized_baseline_isolated_from_delta_inputs") is not True
        or execution_path.get("demo_owned_aggregation") is not False
        or execution_path.get("existing_delta_node_interfaces") is not True
        or execution_path.get("mnist_is_workload_only") is not True
        or execution_path.get("phase_ordering_enforced") is not True
        or execution_path.get("protocol_scope") != "MNIST_WORKLOAD_TO_APPLIED_LOCAL_DELTA"
        or execution_path.get("distributed_orchestrator_received_node_local_numeric_arrays")
        is not False
        or execution_path.get("four_distinct_worker_processes_observed") is not True
        or execution_path.get("stage_c_execution_mode") != "REAL_DRQ1"
        or execution_path.get("stage_c_checkpoint_advanced") is not True
        or execution_path.get("stage_c_synthetic_fallback") is not False
        or stage_c.get("type_name") != "MNIST_STAGEC_REAL_DRQ1_EXECUTION_EVIDENCE"
        or stage_c.get("execution_mode") != "REAL_DRQ1"
        or stage_c.get("worker_count") != 4
        or stage_c.get("isc_ticket_count") != 4
        or stage_c.get("outcome") != "APPLIED"
        or stage_c.get("missing_work_policy_result") != "FULL_QUORUM_DELIVERED_EXACT_ISC"
        or stage_c.get("checkpoint_advanced") is not True
        or stage_c.get("synthetic_fallback") is not False
        or stage_c.get("python_cross_node_aggregation_performed") is not False
        or stage_c.get("java_ml_arithmetic_performed") is not False
        or stage_c.get("stage_c_checkpoint_accuracy_claimed") is not False
        or stage_c.get("demo_domains_are_protocol_qualification_only") is not True
        or model.get("plugin_id") != "mnist-centroid-v1"
        or model.get("sample_kind") != "image/grayscale-28x28"
        or model.get("target_kind") != "class-id/0-9"
        or dataset.get("dataset_id") != "mnist-v1"
        or dataset.get("sample_kind") != "image/grayscale-28x28"
        or dataset.get("target_kind") != "class-id/0-9"
        or binding.get("type_name") != "DELTAREDUCE_MODEL_DATASET_BINDING_EVIDENCE"
        or binding.get("model_plugin_id") != model.get("plugin_id")
        or binding.get("dataset_id") != dataset.get("dataset_id")
        or binding.get("sample_kind") != model.get("sample_kind")
        or binding.get("sample_kind") != dataset.get("sample_kind")
        or binding.get("target_kind") != model.get("target_kind")
        or binding.get("target_kind") != dataset.get("target_kind")
        or binding.get("contract_compatibility") != "PASS"
        or binding.get("runner_boundary") != "ModelDatasetBinding"
        or multi_domain.get("type_name") != "DELTAREDUCE_MULTI_DOMAIN_DEMO_STRUCTURE"
        or multi_domain.get("model_dataset_runner") != "MultiDomainBinding"
        or multi_domain.get("domain_count") != 3
        or multi_domain.get("delta_stage_c_domain_count") != 1
        or multi_domain.get("active_stage_c_domain_id") != "mnist-image"
        or multi_domain.get("cross_domain_aggregation_performed") is not False
        or multi_domain.get("registry_backed") is not True
        or multi_domain.get("stage_c_support_scope") != "MNIST_LIVE_STAGE_C_QLORA_ANCHOR_EEG_SMOKE"
        or multi_domain.get("protocol_scope")
        != "MULTI_DOMAIN_PLUGIN_STRUCTURE_WITH_SINGLE_DOMAIN_LIVE_STAGE_C"
        or len(multi_domain_domains) != 3
        or not isinstance(mnist_domain, dict)
        or not isinstance(qlora_domain, dict)
        or not isinstance(eeg_domain, dict)
        or mnist_domain.get("model_plugin_id") != "mnist-centroid-v1"
        or mnist_domain.get("dataset_id") != "mnist-v1"
        or mnist_domain.get("role") != "PRIMARY_DELTA_EXECUTION"
        or mnist_domain.get("requested_execution_scope") != "STAGE_C_REAL_DRQ1"
        or mnist_domain.get("verified_execution_evidence") != "LIVE_STAGE_C_APPLIED_RECEIPT"
        or mnist_domain.get("delta_stage_c_execution_claimed") is not True
        or mnist_domain.get("live_consensus_claimed_in_this_run") is not True
        or mnist_domain.get("checkpoint_accuracy_claimed_from_stage_c") is not False
        or mnist_domain.get("python_cross_node_aggregation_performed") is not False
        or mnist_domain.get("raw_samples_shared_outside_provider") is not False
        or mnist_domain.get("stage_c_execution_mode") != "REAL_DRQ1"
        or mnist_domain.get("stage_c_outcome") != "APPLIED"
        or mnist_domain.get("worker_count") != 4
        or qlora_domain.get("model_plugin_id") != "qlora-tiny-adapter-v1"
        or qlora_domain.get("dataset_id") != "tiny-qlora-regression-v1"
        or qlora_domain.get("role") != "PRIMARY_DELTA_EXECUTION"
        or qlora_domain.get("requested_execution_scope") != "STAGE_C_REAL_DRQ1"
        or qlora_domain.get("verified_execution_evidence")
        != "NO_LIVE_EXECUTION_EVIDENCE_IN_CURRENT_WORKSPACE_RUN"
        or qlora_domain.get("reference_anchor_evidence") != "REFERENCE_CONFORMANCE_ANCHOR_DECLARED"
        or qlora_domain.get("reference_anchor_is_current_workspace_receipt") is not False
        or qlora_domain.get("delta_stage_c_execution_claimed") is not False
        or qlora_domain.get("live_consensus_claimed_in_this_run") is not False
        or qlora_domain.get("reference_trajectory_anchor")
        != "437558d886d4fc7aac4d8a72f2e4d69696fab7f7"
        or qlora_domain.get("supports_stage_c_real_drq1") is not True
        or qlora_domain.get("checkpoint_accuracy_claimed_from_stage_c") is not False
        or qlora_domain.get("python_cross_node_aggregation_performed") is not False
        or qlora_domain.get("raw_samples_shared_outside_provider") is not False
        or qlora_domain.get("stage_c_execution_mode") is not None
        or qlora_domain.get("stage_c_outcome") is not None
        or qlora_domain.get("worker_count") != 4
        or qlora_domain.get("total_elements") != 8
        or eeg_domain.get("model_plugin_id") != "eeg-bandpower-centroid-v1"
        or eeg_domain.get("dataset_id") != "eeg-synthetic-bci-v1"
        or eeg_domain.get("role") != "PLUGIN_BINDING_SMOKE"
        or eeg_domain.get("requested_execution_scope") != "MODEL_DATASET_BINDING_ONLY"
        or eeg_domain.get("verified_execution_evidence") != "LOCAL_PLUGIN_WORKER_SMOKE"
        or eeg_domain.get("delta_stage_c_execution_claimed") is not False
        or eeg_domain.get("live_consensus_claimed_in_this_run") is not False
        or eeg_domain.get("supports_stage_c_real_drq1") is not False
        or eeg_domain.get("checkpoint_accuracy_claimed_from_stage_c") is not False
        or eeg_domain.get("python_cross_node_aggregation_performed") is not False
        or eeg_domain.get("raw_samples_shared_outside_provider") is not False
        or eeg_domain.get("stage_c_execution_mode") is not None
        or eeg_domain.get("stage_c_outcome") is not None
        or eeg_domain.get("worker_count") != 4
        or eeg_domain.get("total_elements") != 34
        or not isinstance(model_catalog, list)
        or not isinstance(dataset_catalog, list)
        or not any(
            isinstance(item, dict) and item.get("plugin_id") == "qlora-tiny-adapter-v1"
            for item in model_catalog
        )
        or not any(
            isinstance(item, dict) and item.get("dataset_id") == "tiny-qlora-regression-v1"
            for item in dataset_catalog
        )
        or not any(
            isinstance(item, dict) and item.get("plugin_id") == "eeg-bandpower-centroid-v1"
            for item in model_catalog
        )
        or not any(
            isinstance(item, dict) and item.get("dataset_id") == "eeg-synthetic-bci-v1"
            for item in dataset_catalog
        )
        or qlora_showcase.get("type_name") != "DELTAREDUCE_QLORA_PLUGIN_SHOWCASE"
        or qlora_showcase.get("model_plugin_id") != "qlora-tiny-adapter-v1"
        or qlora_showcase.get("dataset_id") != "tiny-qlora-regression-v1"
        or qlora_showcase.get("sample_kind") != "vector/tiny-qlora-2d"
        or qlora_showcase.get("target_kind") != "regression/vector-2d"
        or qlora_showcase.get("runner_boundary") != "ModelDatasetBinding"
        or qlora_showcase.get("contract_compatibility") != "PASS"
        or qlora_showcase.get("worker_count") != 4
        or qlora_showcase.get("total_elements") != 8
        or qlora_showcase.get("delta_stage_c_execution_claimed") is not False
        or qlora_showcase.get("live_consensus_claimed_in_this_run") is not False
        or qlora_showcase.get("supports_stage_c_real_drq1") is not True
        or qlora_showcase.get("reference_anchor_declared") is not True
        or qlora_showcase.get("reference_trajectory_anchor")
        != "437558d886d4fc7aac4d8a72f2e4d69696fab7f7"
        or qlora_showcase.get("verified_execution_evidence")
        != "NO_LIVE_EXECUTION_EVIDENCE_IN_CURRENT_WORKSPACE_RUN"
        or qlora_showcase.get("reference_anchor_evidence")
        != "REFERENCE_CONFORMANCE_ANCHOR_DECLARED"
        or qlora_showcase.get("reference_anchor_is_current_workspace_receipt") is not False
        or qlora_showcase.get("python_cross_node_aggregation_performed") is not False
        or qlora_showcase.get("raw_samples_shared_outside_provider") is not False
        or not isinstance(qlora_workers, list)
        or len(qlora_workers) != 4
        or not isinstance(first_qlora_worker, dict)
        or eeg_showcase.get("type_name") != "DELTAREDUCE_EEG_PLUGIN_SHOWCASE"
        or eeg_showcase.get("model_plugin_id") != "eeg-bandpower-centroid-v1"
        or eeg_showcase.get("dataset_id") != "eeg-synthetic-bci-v1"
        or eeg_showcase.get("sample_kind") != "eeg/bandpower-4ch-4band"
        or eeg_showcase.get("target_kind") != "class-id/0-1"
        or eeg_showcase.get("runner_boundary") != "ModelDatasetBinding"
        or eeg_showcase.get("contract_compatibility") != "PASS"
        or eeg_showcase.get("worker_count") != 4
        or eeg_showcase.get("total_elements") != 34
        or eeg_showcase.get("delta_stage_c_execution_claimed") is not False
        or eeg_showcase.get("python_cross_node_aggregation_performed") is not False
        or eeg_showcase.get("raw_eeg_shared_outside_provider") is not False
        or not isinstance(eeg_workers, list)
        or len(eeg_workers) != 4
        or not isinstance(first_eeg_worker, dict)
        or first_eeg_worker.get("ticket_context_count") != 40
        or first_eeg_worker.get("point_semantics_in_ticket_context") is not False
        or not isinstance(first_eeg_context, dict)
        or not isinstance(temporal_binding, dict)
        or not isinstance(observation_demo, dict)
        or not isinstance(observation_response, dict)
        or not isinstance(temporal_examples, list)
        or len(temporal_examples) != 4
        or not isinstance(first_temporal_example, dict)
        or temporal_binding.get("type_name") != "DELTAREDUCE_TEMPORAL_EVENT_BINDING_EVIDENCE"
        or temporal_binding.get("binding_layer")
        != "deltatorrent.data.binding.BindingProvider/BindingAuthority/ResolvedBindingSet"
        or temporal_binding.get("assertion_schema_version") != "1.0.0"
        or temporal_binding.get("assertion_count") != 160
        or temporal_binding.get("accepted_count") != 160
        or temporal_binding.get("rejected_count") != 0
        or temporal_binding.get("review_count") != 0
        or temporal_binding.get("window_count") != 160
        or temporal_binding.get("event_count") != 4
        or temporal_binding.get("binding_provider_id") != "eeg-window-rule-provider-v1"
        or temporal_binding.get("binding_provider_type") != "RULE"
        or temporal_binding.get("binding_authority_id") != "eeg-demo-binding-authority-v1"
        or not str(temporal_binding.get("resolved_binding_set_id", "")).startswith("sha256:")
        or temporal_binding.get("relation_contract")
        != "EegWindow.intervention_event_id == InterventionEvent.intervention_event_id"
        or temporal_binding.get("point_id_exposed_to_ticket_context") is not False
        or temporal_binding.get("model_plugin_creates_intervention_event") is not False
        or temporal_binding.get("delta_spine_knows_medical_semantics") is not False
        or temporal_binding.get("ticket_context_contains_ids_hashes_only") is not True
        or observation_demo.get("type_name") != "DELTAREDUCE_EEG_OBSERVATION_DEMO"
        or observation_demo.get("event_id") != "evt-demo-eeg-01"
        or observation_demo.get("clinical_conclusion_claimed") is not False
        or observation_demo.get("recommendation_claimed") is not False
        or observation_demo.get("delta_spine_modified") is not False
        or observation_demo.get("binding_semantics_in_delta") is not False
        or observation_response.get("type_name") != "DELTAREDUCE_EEG_RESPONSE_ANALYSIS_RESULT"
        or observation_response.get("intervention_event_id") != "evt-demo-eeg-01"
        or observation_response.get("clinical_conclusion_claimed") is not False
        or observation_response.get("recommendation_claimed") is not False
        or first_temporal_example.get("binding_assertion_id")
        != first_eeg_context.get("binding_assertion_id")
        or first_temporal_example.get("binding_decision_id")
        != first_eeg_context.get("binding_decision_id")
        or first_temporal_example.get("resolved_binding_set_id")
        != first_eeg_context.get("resolved_binding_set_id")
        or first_temporal_example.get("data_window_id") != first_eeg_context.get("data_window_id")
        or first_temporal_example.get("intervention_event_id")
        != first_eeg_context.get("intervention_event_id")
        or first_temporal_example.get("session_id") != first_eeg_context.get("session_id")
        or first_temporal_example.get("raw_data_hash") != first_eeg_context.get("raw_data_hash")
        or first_temporal_example.get("binding_provider_id") != "eeg-window-rule-provider-v1"
        or first_temporal_example.get("binding_provider_type") != "RULE"
        or first_temporal_example.get("binding_status") != "PROPOSED"
        or first_temporal_example.get("binding_authority_id") != "eeg-demo-binding-authority-v1"
        or first_temporal_example.get("authority_decision") != "ACCEPTED"
        or first_temporal_example.get("reason_code") != "RULE_EVENT_WINDOW_CONTEXT_MATCH"
        or first_temporal_example.get("point_id") != "TCM-ST36"
        or first_temporal_example.get("point_source") != "InterventionEvent.point_id"
        or first_temporal_example.get("laterality") != "left"
        or first_temporal_example.get("intervention_type") != "acupuncture_injection"
        or first_temporal_example.get("protocol_id") != "protocol-demo-eeg-st36-v1"
        or not str(first_temporal_example.get("ticket_id", "")).startswith("eeg-ticket-")
        or not str(first_temporal_example.get("partition_id", "")).startswith("demo-eeg-worker-")
        or set(first_eeg_context)
        != {
            "acquisition_profile_id",
            "binding_assertion_id",
            "binding_authority_id",
            "binding_decision_id",
            "binding_schema_version",
            "data_window_id",
            "intervention_event_id",
            "preprocessing_profile_id",
            "raw_data_hash",
            "resolved_binding_set_id",
            "session_id",
        }
        or not str(first_eeg_context.get("binding_assertion_id", "")).startswith("sha256:")
        or not str(first_eeg_context.get("binding_decision_id", "")).startswith("sha256:")
        or not str(first_eeg_context.get("resolved_binding_set_id", "")).startswith("sha256:")
        or first_eeg_context.get("binding_schema_version") != "1.0.0"
        or not str(first_eeg_context.get("session_id", "")).startswith("obs-demo-eeg-")
        or not str(first_eeg_context.get("intervention_event_id", "")).startswith("evt-demo-eeg-")
        or not str(first_eeg_context.get("data_window_id", "")).startswith("eegwin-demo-")
        or not str(first_eeg_context.get("raw_data_hash", "")).startswith("sha256:")
        or failure.get("status") != "RECOVERED_AND_APPLIED"
        or failure.get("replay_observed") is not True
        or failure.get("terminal_outcome") != "APPLIED"
        or not isinstance(components, list)
        or len(components) != len(required_components)
        or not isinstance(phase_execution, list)
        or len(phase_execution) != len(REQUIRED_VOTE_KINDS)
        or not isinstance(certificates, list)
        or len(certificates) != len(REQUIRED_VOTE_KINDS)
        or not isinstance(current_pointer, dict)
        or not isinstance(source_snapshot, dict)
        or source_snapshot.get("no_hidden_aggregation_static_gate") != "PASS"
        or source_snapshot.get("semantic_completeness_claimed") is not False
    ):
        raise MnistDemoError("MNIST_WORKSPACE_DELTA_EVIDENCE_INVALID")
    observed_components: list[str] = []
    for expected_sequence, component in enumerate(components, start=1):
        if (
            not isinstance(component, dict)
            or component.get("sequence") != expected_sequence
            or component.get("status") != "PASS"
            or not isinstance(component.get("component"), str)
            or not isinstance(component.get("evidence"), dict)
        ):
            raise MnistDemoError("MNIST_WORKSPACE_DELTA_COMPONENT_INVALID")
        observed_components.append(str(component["component"]))
    if tuple(observed_components) != required_components:
        raise MnistDemoError("MNIST_WORKSPACE_DELTA_COMPONENT_MISSING")

    expected_phase_fields = {
        "body_hash",
        "certifying_nodes",
        "delivered_vote_count_per_receiver",
        "execution_order",
        "parent_gate_enforced",
        "phase",
        "position",
        "proposal_component",
        "qc_durable_finalize_action_id",
        "required_parent_typed_certificate_id",
        "required_parent_vote_quorum_id",
        "transport_component",
        "typed_certificate_action_id",
        "typed_certificate_id",
        "typed_certificate_verification_after_vote_quorum",
        "typed_certificate_verifier",
        "validated_parent_typed_certificate_ids",
        "validated_parent_vote_quorum_ids",
        "vote_action_id",
        "vote_frames_relayed_per_receiver",
        "vote_persistence_component",
        "vote_quorum_action_id",
        "vote_quorum_component",
        "vote_quorum_id",
    }
    expected_execution_order = [
        "typed_body_proposed",
        "vote_persisted",
        "four_netty_deliveries",
        "generic_vote_quorum_validated",
        "typed_certificate_verified",
        "generic_qc_durably_finalized",
    ]
    expected_vote_actions = (
        "ACT-ISC-VOTE",
        "ACT-EC-VOTE",
        "ACT-APC-VOTE",
        "ACT-PARAM-VOTE",
        "ACT-ROOT-VOTE",
        "ACT-APPLY-VOTE",
    )
    expected_proposal_components = (
        "delta::certificates::InputSetCertificate",
        "delta::robust::build_plan",
        "delta::robust::build_plan",
        "delta::robust::reduce_parameter_shard",
        "delta::certificates::aggregate_merkle_root",
        "delta::apply::compute_candidate",
    )
    expected_trace_kinds = (
        "ISC",
        "EC",
        "APC",
        "PARAMETER_SHARD_QC",
        "AGGREGATE_ROOT_QC",
        "APPLY_QC",
    )
    typed_certificate_ids: list[str] = []
    vote_quorum_ids: list[str] = []

    def content_id(item: object) -> str | None:
        if not isinstance(item, str) or not item.startswith("sha256:"):
            return None
        digest = item[7:]
        return (
            item
            if len(digest) == 64 and all(char in "0123456789abcdef" for char in digest)
            else None
        )

    for index, (phase, certificate) in enumerate(zip(phase_execution, certificates, strict=True)):
        if not isinstance(phase, dict) or not isinstance(certificate, dict):
            raise MnistDemoError("MNIST_WORKSPACE_DELTA_PHASE_INVALID")
        typed_certificate_id = content_id(phase.get("typed_certificate_id"))
        vote_quorum_id = content_id(phase.get("vote_quorum_id"))
        expected_parent_typed_id = typed_certificate_ids[-1] if typed_certificate_ids else None
        expected_parent_quorum_id = vote_quorum_ids[-1] if vote_quorum_ids else None
        if (
            set(phase) != expected_phase_fields
            or phase.get("phase") != REQUIRED_VOTE_KINDS[index]
            or phase.get("position") != index + 1
            or phase.get("body_hash") != typed_certificate_id
            or typed_certificate_id is None
            or vote_quorum_id is None
            or typed_certificate_id == vote_quorum_id
            or typed_certificate_id in vote_quorum_ids
            or vote_quorum_id in typed_certificate_ids
            or phase.get("required_parent_typed_certificate_id") != expected_parent_typed_id
            or phase.get("required_parent_vote_quorum_id") != expected_parent_quorum_id
            or phase.get("validated_parent_typed_certificate_ids") != typed_certificate_ids
            or phase.get("validated_parent_vote_quorum_ids") != vote_quorum_ids
            or phase.get("parent_gate_enforced") is not True
            or phase.get("execution_order") != expected_execution_order
            or phase.get("proposal_component") != expected_proposal_components[index]
            or phase.get("vote_action_id") != expected_vote_actions[index]
            or phase.get("vote_persistence_component") != "delta::runtime::CertificateVoteRuntime"
            or phase.get("transport_component") != "io.deltareduce.demo.MnistDeltaNettyRelay"
            or phase.get("delivered_vote_count_per_receiver") != NODE_COUNT
            or phase.get("vote_frames_relayed_per_receiver") != NODE_COUNT
            or phase.get("vote_quorum_action_id") != "OBS-CURRENT-VOTE-QUORUM-VALIDATED"
            or phase.get("vote_quorum_component") != VOTE_QUORUM_COMPONENT
            or phase.get("typed_certificate_action_id") != "OBS-TYPED-CERT-VERIFIED-AFTER-QC"
            or phase.get("typed_certificate_verifier") != TYPED_CERTIFICATE_VERIFIER
            or phase.get("typed_certificate_verification_after_vote_quorum") is not True
            or phase.get("qc_durable_finalize_action_id") != "OBS-CURRENT-QC-DURABLY-FINALIZED"
            or phase.get("certifying_nodes") != NODE_COUNT
            or set(certificate)
            != {"body_hash", "context_id", "kind", "qc_id", "signer_count", "threshold"}
            or certificate.get("kind") != REQUIRED_VOTE_KINDS[index]
            or not isinstance(certificate.get("context_id"), str)
            or not str(certificate["context_id"]).startswith(f"{expected_trace_kinds[index]}:")
            or certificate.get("body_hash") != typed_certificate_id
            or certificate.get("qc_id") != vote_quorum_id
            or certificate.get("signer_count") != NODE_COUNT
            or certificate.get("threshold") != 3
        ):
            raise MnistDemoError("MNIST_WORKSPACE_DELTA_PHASE_INVALID")
        typed_certificate_ids.append(typed_certificate_id)
        vote_quorum_ids.append(vote_quorum_id)
    if (
        len(set(typed_certificate_ids)) != len(typed_certificate_ids)
        or len(set(vote_quorum_ids)) != len(vote_quorum_ids)
        or not set(typed_certificate_ids).isdisjoint(vote_quorum_ids)
        or delta.get("apply_qc_id") != typed_certificate_ids[-1]
        or current_pointer.get("apply_qc_id") != typed_certificate_ids[-1]
        or current_pointer.get("disposition") != "ADVANCED"
        or current_pointer.get("height") != 1
    ):
        raise MnistDemoError("MNIST_WORKSPACE_DELTA_PHASE_INVALID")
    return value


class WorkspaceState:
    """Thread-safe state shared by the local HTTP handler and one demo worker."""

    def __init__(
        self,
        repository_root: Path,
        cache_dir: Path,
        output_root: Path,
        *,
        allow_download: bool,
    ) -> None:
        self._repository_root = repository_root
        self._cache_dir = cache_dir
        self._output_root = output_root
        self._allow_download = allow_download
        self._lock = threading.Lock()
        self._running = False
        self._stage = "Готово к запуску"
        self._percent = 0
        self._message = "Нажмите «Запустить демо»"
        self._events: list[str] = []
        self._error: str | None = None
        self._result: dict[str, object] | None = None
        self._last_output_dir: str | None = None

    def start(self) -> bool:
        """Start one background run, rejecting concurrent button presses."""
        with self._lock:
            if self._running:
                return False
            self._running = True
            self._stage = "Запуск"
            self._percent = 1
            self._message = "Инициализируем изолированный workspace"
            self._events = []
            self._error = None
            self._result = None
        worker = threading.Thread(target=self._execute, name="mnist-demo-runner", daemon=True)
        worker.start()
        return True

    def _progress(self, stage: str, percent: int, message: str) -> None:
        with self._lock:
            if message != self._message:
                self._events.append(message)
            self._stage = stage
            self._percent = percent
            self._message = message

    def _execute(self) -> None:
        run_stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        run_dir = self._output_root / f"run-{run_stamp}-{uuid.uuid4().hex[:8]}"
        try:
            result = run_mnist_demo(
                self._repository_root,
                self._cache_dir,
                run_dir,
                allow_download=self._allow_download,
                progress=self._progress,
            )
            report = _validate_workspace_report(
                json.loads(result.report_json.read_text(encoding="utf-8"))
            )
            with self._lock:
                self._result = report
                self._last_output_dir = str(result.output_dir)
        except (MnistDemoError, OSError, ValueError) as exc:
            with self._lock:
                self._error = str(exc)
                self._stage = "Ошибка"
                self._message = str(exc)
        finally:
            with self._lock:
                self._running = False

    def snapshot(self) -> dict[str, object]:
        """Return a JSON-safe immutable snapshot for the local browser."""
        with self._lock:
            return {
                "error": self._error,
                "events": list(self._events),
                "last_output_dir": self._last_output_dir,
                "message": self._message,
                "percent": self._percent,
                "result": self._result,
                "running": self._running,
                "stage": self._stage,
            }


class WorkspaceRequestHandler(BaseHTTPRequestHandler):
    """Small fixed-route HTTP surface bound only to the loopback interface."""

    state: ClassVar[WorkspaceState]
    demo_token: ClassVar[str]
    csp_nonce: ClassVar[str]

    def _write(self, status: HTTPStatus, payload: bytes, content_type: str) -> None:
        self.send_response(status.value)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; "
            f"script-src 'nonce-{self.csp_nonce}'; "
            "style-src 'unsafe-inline'; connect-src 'self'; img-src 'self' data:",
        )
        self.end_headers()
        self.wfile.write(payload)

    def _json(self, status: HTTPStatus, value: Mapping[str, object]) -> None:
        payload = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self._write(status, payload, "application/json; charset=utf-8")

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/":
            page = WORKSPACE_HTML.replace(
                "__DEMO_TOKEN__",
                json.dumps(self.demo_token),
            ).replace("__CSP_NONCE__", self.csp_nonce)
            self._write(HTTPStatus.OK, page.encode("utf-8"), "text/html; charset=utf-8")
            return
        if path == "/api/status":
            self._json(HTTPStatus.OK, self.state.snapshot())
            return
        if path == "/api/catalog":
            self._json(HTTPStatus.OK, _workspace_catalog())
            return
        if path == "/favicon.ico":
            self._write(HTTPStatus.NO_CONTENT, b"", "image/x-icon")
            return
        self._json(HTTPStatus.NOT_FOUND, {"error": "NOT_FOUND"})

    def do_POST(self) -> None:
        path = urlsplit(self.path).path
        content_length = self.headers.get("Content-Length", "0")
        try:
            body_size = int(content_length)
        except ValueError:
            self._json(HTTPStatus.BAD_REQUEST, {"error": "INVALID_CONTENT_LENGTH"})
            return
        if body_size != 0:
            self._json(HTTPStatus.BAD_REQUEST, {"error": "REQUEST_BODY_NOT_ALLOWED"})
            return
        if path != "/api/run":
            self._json(HTTPStatus.NOT_FOUND, {"error": "NOT_FOUND"})
            return
        supplied_token = self.headers.get("X-Demo-Token", "")
        if not secrets.compare_digest(supplied_token, self.demo_token):
            self._json(HTTPStatus.FORBIDDEN, {"error": "DEMO_TOKEN_INVALID"})
            return
        if not self.state.start():
            self._json(HTTPStatus.CONFLICT, {"error": "DEMO_ALREADY_RUNNING"})
            return
        self._json(HTTPStatus.ACCEPTED, {"status": "STARTED"})

    def log_message(self, _format: str, *_args: Any) -> None:
        return


def serve_workspace(
    repository_root: Path,
    cache_dir: Path,
    output_root: Path,
    *,
    allow_download: bool,
    host: str = "127.0.0.1",
    port: int = 0,
    open_browser: bool = False,
) -> None:
    """Serve the one-button demo on loopback until interrupted by the operator."""
    if host != "127.0.0.1":
        raise MnistDemoError("MNIST_WORKSPACE_MUST_BIND_LOOPBACK")
    root = repository_root.resolve(strict=True)
    cache = cache_dir if cache_dir.is_absolute() else root / cache_dir
    outputs = output_root if output_root.is_absolute() else root / output_root
    outputs = outputs.resolve(strict=False)
    outputs.mkdir(parents=True, exist_ok=True)
    if outputs.is_symlink() or not outputs.is_dir():
        raise MnistDemoError("MNIST_WORKSPACE_OUTPUT_ROOT_INVALID")
    state = WorkspaceState(
        root,
        cache.resolve(strict=False),
        outputs,
        allow_download=allow_download,
    )
    token = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(24)
    handler_type = type(
        "BoundWorkspaceRequestHandler",
        (WorkspaceRequestHandler,),
        {"csp_nonce": nonce, "demo_token": token, "state": state},
    )
    server = ThreadingHTTPServer((host, port), handler_type)
    actual_port = int(server.server_address[1])
    url = f"http://{host}:{actual_port}/"
    print("DeltaReduce MNIST workspace: LOCAL_DEMO_ONLY")
    print(f"Open: {url}")
    print("Stop: Ctrl+C")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        print("MNIST demo workspace stopped.")
    finally:
        server.server_close()
