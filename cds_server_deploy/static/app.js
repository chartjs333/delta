/**
 * DeltaReduce Demo v1.0: Clinical Decision Support Prototype
 * Client Application Logic (Vanilla JS)
 */

document.addEventListener("DOMContentLoaded", () => {
  let CURRENT_STATE = null;
  let EXAMPLES = [];

  // Dynamic API Base URL resolution for Gateway / Reverse Proxy deployments (e.g. /delta-reduce-demo/)
  function getApiBaseUrl() {
    if (window.API_BASE_PATH !== undefined) {
      return window.API_BASE_PATH.replace(/\/+$/, "");
    }
    let path = window.location.pathname || "";
    path = path.replace(/\/([^\/]*\.[^\/]*)$/, ""); // strip index.html or similar filename
    path = path.replace(/\/+$/, ""); // strip trailing slashes
    return path;
  }
  const API_BASE = getApiBaseUrl();

  const clinicalTextArea = document.getElementById("clinicalText");
  const btnAnalyze = document.getElementById("btnAnalyze");
  const btnClear = document.getElementById("btnClear");
  const btnRecalculate = document.getElementById("btnRecalculate");
  const presetsContainer = document.getElementById("presetsContainer");

  // Load Status and Examples on Startup
  fetchStatus();
  fetchExamples();

  // Event Listeners
  btnAnalyze.addEventListener("click", () => handleAnalyze());
  btnClear.addEventListener("click", () => {
    clinicalTextArea.value = "";
    clinicalTextArea.focus();
  });
  btnRecalculate.addEventListener("click", () => handleRecalculate());

  async function fetchStatus() {
    try {
      const resp = await fetch(`${API_BASE}/api/status`);
      if (resp.ok) {
        const data = await resp.json();
        if (data.nlp_model) {
          const headerModel = document.getElementById("headerModelName");
          if (headerModel) headerModel.textContent = data.nlp_model;
          const stage1 = document.getElementById("stage1Model");
          if (stage1) stage1.textContent = `${data.nlp_model} (Schema 1.1)`;
          const auditModel = document.getElementById("auditModel");
          if (auditModel) auditModel.textContent = data.nlp_model;
        }
      }
    } catch (e) {
      // Non-critical
    }
  }

  async function fetchExamples() {
    try {
      const resp = await fetch(`${API_BASE}/api/examples`);
      if (resp.ok) {
        EXAMPLES = await resp.json();
        renderPresets(EXAMPLES);
        // Load first example by default
        if (EXAMPLES.length > 0) {
          selectExample(EXAMPLES[0]);
        }
      }
    } catch (err) {
      console.warn("Using inline preset fallback", err);
    }
  }

  function renderPresets(examples) {
    if (!examples || examples.length === 0) return;
    presetsContainer.innerHTML = "";

    examples.forEach((ex, idx) => {
      const card = document.createElement("button");
      card.className = `preset-card ${idx === 0 ? "active" : ""} ${ex.id === "case_5_conflict" ? "alert-card" : ""}`;
      card.setAttribute("data-id", ex.id);

      let tagClass = "green";
      if (ex.id === "case_2_gch1") tagClass = "amber";
      else if (ex.id === "case_3_atp13a2") tagClass = "purple";
      else if (ex.id === "case_4_gba1") tagClass = "red";
      else if (ex.id === "case_5_conflict") tagClass = "rose";

      card.innerHTML = `
        <div class="preset-head">
          <span class="preset-tag ${tagClass}">${escapeHtml(ex.badge || "Clinical Case")}</span>
          <span class="preset-gene">${escapeHtml(ex.title.split(":")[0])}</span>
        </div>
        <div class="preset-desc">${escapeHtml(ex.description || ex.title)}</div>
      `;

      card.addEventListener("click", () => {
        document.querySelectorAll(".preset-card").forEach(c => c.classList.remove("active"));
        card.classList.add("active");
        selectExample(ex);
      });

      presetsContainer.appendChild(card);
    });
  }

  function selectExample(ex) {
    clinicalTextArea.value = ex.text;
    handleAnalyze();
  }

  async function handleAnalyze() {
    const text = clinicalTextArea.value.trim();
    if (!text) {
      alert("Please enter a clinical case narrative.");
      return;
    }

    btnAnalyze.disabled = true;
    btnAnalyze.innerHTML = `<span class="btn-icon">⏳</span> <span class="btn-label">Analyzing...</span>`;

    // Visual Stepper Progression
    resetStepper();
    await animateStep(1);

    try {
      await animateStep(2);
      const resp = await fetch(`${API_BASE}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });

      await animateStep(3);
      await animateStep(4);

      if (!resp.ok) {
        throw new Error(`Server returned HTTP ${resp.status}`);
      }

      const data = await resp.json();
      await animateStep(5);

      CURRENT_STATE = data;
      renderReport(data);

    } catch (err) {
      alert(`Analysis failed: ${err.message}`);
      console.error(err);
    } finally {
      btnAnalyze.disabled = false;
      btnAnalyze.innerHTML = `<span class="btn-icon">⚡</span> <span class="btn-label">Analyze Case</span>`;
    }
  }

  async function handleRecalculate() {
    if (!CURRENT_STATE) return;

    btnRecalculate.disabled = true;
    btnRecalculate.textContent = "🔄 Recalculating...";

    // Harvest current clinician edits from the UI table
    const tableBody = document.getElementById("featuresTableBody");
    const rows = tableBody.querySelectorAll("tr");

    const updatedFeatures = [];
    rows.forEach(r => {
      const id = r.getAttribute("data-id");
      const featObj = (CURRENT_STATE.clinical_features || []).find(f => f.id === id);
      if (featObj) {
        const statusSelect = r.querySelector(".status-select");
        const subjectSelect = r.querySelector(".subject-select");
        const isConfirmed = r.querySelector(".btn-confirm").classList.contains("active");

        featObj.status = statusSelect ? statusSelect.value : featObj.status;
        featObj.subject = subjectSelect ? subjectSelect.value : featObj.subject;
        featObj.clinician_confirmed = isConfirmed;

        updatedFeatures.push(featObj);
      }
    });

    CURRENT_STATE.clinical_features = updatedFeatures;

    try {
      const resp = await fetch(`${API_BASE}/api/recalculate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(CURRENT_STATE)
      });

      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }

      const updated = await resp.json();
      CURRENT_STATE = updated;
      renderReport(updated);

    } catch (err) {
      alert(`Recalculation failed: ${err.message}`);
      console.error(err);
    } finally {
      btnRecalculate.disabled = false;
      btnRecalculate.textContent = "🔄 Recompute Analysis";
    }
  }

  function renderReport(data) {
    if (!data) return;

    // 1. Safety Alerts
    renderSafetyAlerts(data.safety_alerts || []);

    // 2. Abstention Banner
    const abstentionCard = document.getElementById("abstentionCard");
    const abstentionReason = document.getElementById("abstentionReason");
    if ((data.abstention && data.abstention.is_withheld) || data.status === "ABSTAIN") {
      abstentionCard.style.display = "block";
      abstentionReason.textContent = (data.abstention && data.abstention.reason) || "Interpretation withheld: available information is insufficient or extraction failed.";
    } else {
      abstentionCard.style.display = "none";
    }

    // 3. Extracted Clinical Features Table
    renderFeaturesTable(data.clinical_features || []);

    // 4. Molecular Findings Table
    renderMolecularTable(data.molecular_findings || null);

    // 5. Differential Diagnosis (Phenotype Model)
    renderClassifierSafety(data.classifier_safety || null);
    renderPhenotypeRanking(data.phenotype_ranking, data.phenotype_model_status);

    // 6. Molecular Evidence & Concordance
    renderConcordance(data.molecular_findings, data.concordance);

    // 7. Technical Audit Trail
    renderAuditTrail(data.audit_trail);
  }

  function renderSafetyAlerts(alerts) {
    const list = document.getElementById("safetyAlertsList");
    const badge = document.getElementById("safetyBadge");
    list.innerHTML = "";

    let hasDanger = false;
    let hasWarning = false;

    if (!alerts || alerts.length === 0) {
      list.innerHTML = `<div class="alert-item success"><span class="alert-icon">✓</span><div class="alert-content"><strong>No critical conflicts detected</strong><p>All assertions satisfy formal constraints.</p></div></div>`;
      badge.className = "status-pill green";
      badge.textContent = "Verified Safe";
      return;
    }

    alerts.forEach(a => {
      const item = document.createElement("div");
      item.className = `alert-item ${a.type || "warning"}`;
      
      let icon = "⚠";
      if (a.type === "success") icon = "✓";
      else if (a.type === "danger") { icon = "🛑"; hasDanger = true; }
      else if (a.type === "warning") { hasWarning = true; }

      item.innerHTML = `
        <span class="alert-icon">${icon}</span>
        <div class="alert-content">
          <strong>${escapeHtml(a.title)}</strong>
          <p>${escapeHtml(a.detail)}</p>
        </div>
      `;
      list.appendChild(item);
    });

    if (hasDanger) {
      badge.className = "status-pill rose";
      badge.textContent = "Review Required";
    } else if (hasWarning) {
      badge.className = "status-pill amber";
      badge.textContent = "Advisory Alerts";
    } else {
      badge.className = "status-pill green";
      badge.textContent = "Verified Safe";
    }
  }

  function renderFeaturesTable(features) {
    const tbody = document.getElementById("featuresTableBody");
    tbody.innerHTML = "";

    if (!features || features.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 20px;">No clinical features extracted from current text.</td></tr>`;
      return;
    }

    features.forEach(f => {
      const tr = document.createElement("tr");
      tr.setAttribute("data-id", f.id);

      const isConfirmed = (f.clinician_confirmed !== false);

      tr.innerHTML = `
        <td>
          <strong style="color: var(--text-primary);">${escapeHtml(f.feature)}</strong>
          <div style="font-size: 0.72rem; color: var(--text-muted); font-family: var(--font-mono);">${escapeHtml(f.concept || "")}</div>
        </td>
        <td>
          <select class="select-clean status-select">
            <option value="Present" ${f.status === "Present" ? "selected" : ""}>Present</option>
            <option value="Absent" ${f.status === "Absent" ? "selected" : ""}>Absent</option>
            <option value="Possible" ${f.status === "Possible" ? "selected" : ""}>Possible</option>
            <option value="Uncertain" ${f.status === "Uncertain" ? "selected" : ""}>Uncertain</option>
          </select>
        </td>
        <td>
          <select class="select-clean subject-select">
            <option value="Patient" ${f.subject === "Patient" ? "selected" : ""}>Patient</option>
            <option value="Father" ${f.subject === "Father" ? "selected" : ""}>Father</option>
            <option value="Mother" ${f.subject === "Mother" ? "selected" : ""}>Mother</option>
            <option value="Sister" ${f.subject === "Sister" ? "selected" : ""}>Sister</option>
            <option value="Brother" ${f.subject === "Brother" ? "selected" : ""}>Brother</option>
            <option value="Relative" ${f.subject === "Relative" ? "selected" : ""}>Relative</option>
          </select>
        </td>
        <td>
          <span class="source-quote" title="${escapeHtml(f.source_text)}">"${escapeHtml(f.source_text)}"</span>
        </td>
        <td style="text-align: center;">
          <div style="display: inline-flex; gap: 4px;">
            <button class="review-btn confirm btn-confirm ${isConfirmed ? "active" : ""}" title="Confirm fact">✓</button>
            <button class="review-btn reject btn-reject ${!isConfirmed ? "active" : ""}" title="Exclude fact">✕</button>
          </div>
        </td>
      `;

      // Wire review buttons
      const btnConf = tr.querySelector(".btn-confirm");
      const btnRej = tr.querySelector(".btn-reject");

      btnConf.addEventListener("click", () => {
        btnConf.classList.add("active");
        btnRej.classList.remove("active");
        tr.style.opacity = "1";
      });

      btnRej.addEventListener("click", () => {
        btnRej.classList.add("active");
        btnConf.classList.remove("active");
        tr.style.opacity = "0.45";
      });

      tbody.appendChild(tr);
    });
  }

  function renderMolecularTable(mol) {
    const tbody = document.getElementById("molecularTableBody");
    tbody.innerHTML = "";

    if (!mol || mol.gene === "Unknown / Not provided" && mol.raw_input === "Unknown / Not provided") {
      tbody.innerHTML = `
        <tr>
          <td><span class="badge-unknown">Unknown / Not provided</span></td>
          <td><span class="badge-unknown">Unknown / Not provided</span></td>
          <td><span class="badge-unknown">Unknown / Not provided</span></td>
          <td><span class="badge-unknown">Unknown / Not provided</span></td>
          <td><span class="badge-unknown">Unknown / Not provided</span></td>
          <td><span class="badge-unknown">Unknown / Not provided</span></td>
          <td><span class="badge-unknown">Unknown / Not provided</span></td>
          <td><span class="badge-unknown">Unknown / Not provided</span></td>
          <td><span class="badge-unknown">None</span></td>
        </tr>
      `;
      return;
    }

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong style="color: var(--cyan-400); font-family: var(--font-mono); font-size: 0.95rem;">${escapeHtml(mol.gene)}</strong></td>
      <td><code style="font-family: var(--font-mono); color: var(--amber-400);">${escapeHtml(mol.raw_input)}</code></td>
      <td><code style="font-family: var(--font-mono); color: var(--emerald-400); font-weight: 600;">${escapeHtml(mol.normalized_hgvs)}</code></td>
      <td><span style="font-family: var(--font-mono); font-size: 0.8rem;">${escapeHtml(mol.transcript)}</span></td>
      <td><span class="preset-tag green">${escapeHtml(mol.classification)}</span></td>
      <td>${escapeHtml(mol.zygosity)}</td>
      <td>${escapeHtml(mol.parental_origin)}</td>
      <td>${escapeHtml(mol.phase)}</td>
      <td><span class="source-quote" title="${escapeHtml(mol.source)}">${escapeHtml(mol.source)}</span></td>
    `;
    tbody.appendChild(tr);
  }

  function renderPhenotypeRanking(ranking, statusText) {
    const list = document.getElementById("phenotypeRankingList");
    list.innerHTML = "";

    if (!ranking || ranking.length === 0) {
      list.innerHTML = `<div style="color: var(--text-muted); font-size: 0.88rem; padding: 14px; text-align: center; border: 1px dashed var(--border); border-radius: 8px; background: rgba(255,255,255,0.02);">
        <strong style="display:block; color: var(--amber-400); margin-bottom: 4px;">⚠️ ${escapeHtml(statusText || "Phenotype model unavailable")}</strong>
        <span>No neural ranking available or clinical findings insufficient.</span>
      </div>`;
      return;
    }

    ranking.forEach((r, idx) => {
      const item = document.createElement("div");
      item.className = "ranking-item";
      item.innerHTML = `
        <div class="ranking-row">
          <div class="ranking-gene-group">
            <span class="ranking-rank">#${idx + 1}</span>
            <span class="ranking-gene">${escapeHtml(r.gene)}</span>
            <span class="ranking-name">&bull; ${escapeHtml(r.full_name)} (${escapeHtml(r.inheritance)})</span>
          </div>
          <span class="ranking-score">${r.score_pct.toFixed(1)}%</span>
        </div>
        <div class="ranking-bar-track">
          <div class="ranking-bar-fill" style="width: ${Math.max(4, r.score_pct)}%;"></div>
        </div>
      `;
      list.appendChild(item);
    });
  }

  function renderClassifierSafety(safety) {
    const box = document.getElementById("classifierSafetySummary");
    const statusEl = document.getElementById("classifierSafetyStatus");
    const candidateEl = document.getElementById("classifierTopCandidate");
    const scoreEl = document.getElementById("classifierScore");
    const reasonsEl = document.getElementById("classifierReasonCodes");
    if (!box || !statusEl || !candidateEl || !scoreEl || !reasonsEl) return;

    const status = safety && safety.status ? safety.status : "PENDING";
    const reasonCodes = safety && Array.isArray(safety.reason_codes) ? safety.reason_codes : [];
    statusEl.textContent = status;
    candidateEl.textContent = safety && safety.top_candidate ? safety.top_candidate : "N/A";
    scoreEl.textContent = safety && safety.classifier_score_pct !== null && safety.classifier_score_pct !== undefined
      ? `${Number(safety.classifier_score_pct).toFixed(1)}%`
      : "N/A";
    box.className = `classifier-safety-summary ${status === "DEFINITIVE_GENE" ? "definitive" : status === "AMBIGUOUS_GENE_CLUSTER" ? "ambiguous" : "abstain"}`;
    reasonsEl.innerHTML = "";
    if (reasonCodes.length > 0) {
      reasonCodes.forEach(code => {
        const pill = document.createElement("span");
        pill.className = "reason-code-pill";
        pill.textContent = code;
        reasonsEl.appendChild(pill);
      });
    } else {
      const pill = document.createElement("span");
      pill.className = "reason-code-pill muted";
      pill.textContent = "NO_SAFETY_DOWNGRADE";
      reasonsEl.appendChild(pill);
    }
  }

  function renderConcordance(mol, concordance) {
    const badge = document.getElementById("concordanceBadge");
    const details = document.getElementById("molecularEvidenceDetails");
    const box = document.getElementById("concordanceBox");

    // Details box
    if (!mol || mol.gene === "Unknown / Not provided") {
      details.innerHTML = `
        <div class="evidence-fact-row">
          <span>Detected Variant:</span>
          <strong>None reported</strong>
        </div>
        <div class="evidence-fact-row">
          <span>Status:</span>
          <strong>Phenotype analysis only</strong>
        </div>
      `;
    } else {
      details.innerHTML = `
        <div class="evidence-fact-row">
          <span>Gene & Variant:</span>
          <strong>${escapeHtml(mol.normalized_hgvs || mol.gene)}</strong>
        </div>
        <div class="evidence-fact-row">
          <span>Reported Classification:</span>
          <strong>${escapeHtml(mol.classification)}</strong>
        </div>
        <div class="evidence-fact-row">
          <span>Zygosity / Phase:</span>
          <strong>${escapeHtml(mol.zygosity)} &bull; ${escapeHtml(mol.phase)}</strong>
        </div>
      `;
    }

    // Concordance box
    const status = concordance ? concordance.status : "PENDING";
    const isDiscordant = concordance && concordance.discordance_detected;

    if (isDiscordant) {
      badge.className = "status-pill rose";
      badge.textContent = "Discordance Detected";

      box.className = "concordance-status-box discordant";
      let reasonsHtml = "";
      if (concordance.reasons && concordance.reasons.length > 0) {
        reasonsHtml = `<ul class="discordance-list">${concordance.reasons.map(r => `<li>${escapeHtml(r)}</li>`).join("")}</ul>`;
      }
      box.innerHTML = `
        <div class="discordance-title">
          <span>⚠ Genotype–phenotype discordance detected</span>
        </div>
        <div>The identified molecular variant contradicts typical clinical or onset features:</div>
        ${reasonsHtml}
      `;
    } else if (status === "HIGH") {
      badge.className = "status-pill green";
      badge.textContent = "High Concordance";

      box.className = "concordance-status-box high";
      box.innerHTML = `
        <strong>✓ High Genotype–Phenotype Concordance</strong>
        <p style="margin-top: 4px;">The identified variant in <strong>${escapeHtml(mol.gene)}</strong> perfectly matches the primary clinical presentation and inheritance pattern.</p>
      `;
    } else if (status === "MODERATE") {
      badge.className = "status-pill cyan";
      badge.textContent = "Moderate Concordance";

      box.className = "concordance-status-box moderate";
      box.innerHTML = `
        <strong>Genotype–Phenotype Concordance: Moderate</strong>
        <p style="margin-top: 4px;">Detected variant in <strong>${escapeHtml(mol.gene)}</strong> is consistent with clinical findings, ranking among leading differential possibilities.</p>
      `;
    } else {
      badge.className = "status-pill gray";
      badge.textContent = status;

      box.className = "concordance-status-box";
      box.innerHTML = `
        <span>Concordance Status: <strong>${escapeHtml(status)}</strong></span>
      `;
    }
  }

  function renderAuditTrail(audit) {
    if (!audit) return;
    const modelName = audit.model || "deepseek-v4-flash";
    document.getElementById("auditModel").textContent = modelName;
    const headerModel = document.getElementById("headerModelName");
    if (headerModel) headerModel.textContent = modelName;
    const stage1 = document.getElementById("stage1Model");
    if (stage1) stage1.textContent = `${modelName} (Schema 1.1)`;

    document.getElementById("auditSchema").textContent = `${audit.schema || "1.1"} (Typed Contract)`;
    document.getElementById("auditCompleteness").textContent = audit.completeness_gate_status || "PASS";
    document.getElementById("auditFormalGate").textContent = audit.formal_gate_status || "PASS";
    document.getElementById("auditCore").textContent = audit.revision_core || "Revision 6.2";

    const tbody = document.getElementById("auditTableBody");
    tbody.innerHTML = "";

    const lineage = audit.lineage || [];
    document.getElementById("auditBadge").textContent = `${lineage.length} Observations Verified`;

    lineage.forEach(item => {
      const tr = document.createElement("tr");
      const isApproved = (item.formal_gate === "APPROVED");

      tr.innerHTML = `
        <td><code>${escapeHtml(item.id)}</code></td>
        <td><span class="source-quote" title="${escapeHtml(item.raw_span)}">"${escapeHtml(item.raw_span)}"</span></td>
        <td><strong>${escapeHtml(item.predicate)}</strong>: ${escapeHtml(item.concept || "")}</td>
        <td>${escapeHtml(item.subject)}</td>
        <td>
          <span class="preset-tag ${isApproved ? "green" : "rose"}">${escapeHtml(item.formal_gate)}</span>
        </td>
        <td>
          ${item.errors && item.errors.length > 0 ? `<span style="color: var(--rose-400);">${escapeHtml(item.errors.join("; "))}</span>` : `<span style="color: var(--emerald-400);">Constraint invariant satisfied</span>`}
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  function resetStepper() {
    for (let i = 1; i <= 5; i++) {
      const step = document.getElementById(`step${i}`);
      if (step) {
        step.className = "step-item";
      }
    }
  }

  async function animateStep(stepNum) {
    for (let i = 1; i < stepNum; i++) {
      const prev = document.getElementById(`step${i}`);
      if (prev) prev.className = "step-item completed";
    }
    const curr = document.getElementById(`step${stepNum}`);
    if (curr) curr.className = "step-item active";
    await new Promise(r => setTimeout(r, 120));
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
