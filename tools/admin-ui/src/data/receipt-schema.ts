import {
  VALID_SCOPES,
  type ExecutionScopeName,
} from "./descriptors-catalog";

export interface ReceiptProvenance {
  readonly repository: string;
  readonly backend_commit: string;
  readonly catalog_backend_ref?: string;
  readonly producer_commit?: string;
  readonly produced_at: string;
}

export interface ReceiptWorkload {
  readonly model_plugin_id: string;
  readonly dataset_id: string;
  readonly executed_scope: ExecutionScopeName;
  readonly workload_config_digest: string;
}

export interface ReceiptExecution {
  readonly verdict: "SUCCESS" | "REJECTED_PREFLIGHT" | "ABORTED";
  readonly terminal_status: string;
}

export interface ConsensusEvidence {
  readonly round_id: number;
  readonly state_root: string;
  readonly canonical_model_digest: string;
  readonly checkpoint_ref: string;
  readonly applied_status: "APPLIED" | "COMMITTED";
  readonly wal_sequence: number;
}

export interface ReferenceAnchor {
  readonly reference_anchor_declared: boolean;
  readonly anchor_description: string;
  readonly declared_baseline_metric: string | number;
}

export interface ObservationSummary {
  readonly metrics: Readonly<Record<string, number | string>>;
  readonly observation_note: string;
}

export interface ExecutionReceipt {
  readonly schema_version: "1.0.0";
  readonly receipt_type: "DELTAREDUCE_EXECUTION_RECEIPT";
  readonly provenance: ReceiptProvenance;
  readonly workload: ReceiptWorkload;
  readonly execution: ReceiptExecution;
  readonly consensus_evidence?: ConsensusEvidence;
  readonly reference_anchor?: ReferenceAnchor;
  readonly observation_summary?: ObservationSummary;
}

export type ReceiptState =
  | "NO_RECEIPT"
  | "RECEIPT_LOADED_UNBOUND"
  | "STRUCTURALLY_VALID_BOUND_RECEIPT"
  | "REJECTED";

export type EvidenceType =
  | "UNATTESTED_CONSENSUS_RECORD"
  | "UNATTESTED_PLUGIN_BOUNDARY_RECORD"
  | "OBSERVATION_RECORD"
  | "REFERENCE_ANCHOR";

export interface BindingEvaluationResult {
  readonly state: "STRUCTURALLY_VALID_BOUND_RECEIPT" | "RECEIPT_LOADED_UNBOUND";
  readonly evidenceType?: EvidenceType;
  readonly expectedDigest: string;
  readonly actualDigest: string;
  readonly reason?: string;
}

export class ReceiptValidationError extends Error {
  constructor(message: string) {
    super(`RECEIPT_VALIDATION_ERROR: ${message}`);
    this.name = "ReceiptValidationError";
  }
}

/**
 * Standard SHA-256 implementation in pure TypeScript.
 * Zero external dependencies, fully synchronous, compatible with offline boundary.
 */
export function sha256Sync(ascii: string): string {
  function rightRotate(value: number, amount: number): number {
    return (value >>> amount) | (value << (32 - amount));
  }

  const mathPow = Math.pow;
  const maxWord = mathPow(2, 32);
  const words: number[] = [];
  const asciiBitLength = ascii.length * 8;

  const hash: number[] = [];
  const k: number[] = [];
  let primeCounter = 0;

  const isComposite: Record<number, number> = {};
  for (let candidate = 2; primeCounter < 64; candidate++) {
    if (!isComposite[candidate]) {
      for (let i = 0; i < 313; i += candidate) {
        isComposite[i] = candidate;
      }
      hash[primeCounter] = (mathPow(candidate, 0.5) * maxWord) | 0;
      k[primeCounter++] = (mathPow(candidate, 1 / 3) * maxWord) | 0;
    }
  }

  let formattedAscii = ascii + "\x80";
  while ((formattedAscii.length % 64) - 56) formattedAscii += "\x00";
  for (let i = 0; i < formattedAscii.length; i++) {
    const j = formattedAscii.charCodeAt(i);
    words[i >> 2] |= j << ((3 - (i % 4)) * 8);
  }
  words[words.length] = (asciiBitLength / maxWord) | 0;
  words[words.length] = asciiBitLength;

  for (let j = 0; j < words.length; ) {
    const w = words.slice(j, (j += 16));
    const oldHash = hash.slice(0);

    for (let i = 0; i < 64; i++) {
      const w15 = w[i - 15];
      const w2 = w[i - 2];

      const a = hash[0];
      const e = hash[4];
      const temp1 =
        hash[7] +
        (rightRotate(e, 6) ^ rightRotate(e, 11) ^ rightRotate(e, 25)) +
        ((e & hash[5]) ^ (~e & hash[6])) +
        k[i] +
        (w[i] =
          i < 16
            ? w[i]
            : (w[i - 16] +
                (rightRotate(w15, 7) ^ rightRotate(w15, 18) ^ (w15 >>> 3)) +
                w[i - 7] +
                (rightRotate(w2, 17) ^ rightRotate(w2, 19) ^ (w2 >>> 10))) |
              0);

      const temp2 =
        (rightRotate(a, 2) ^ rightRotate(a, 13) ^ rightRotate(a, 22)) +
        ((a & hash[1]) ^ (a & hash[2]) ^ (hash[1] & hash[2]));

      hash[7] = hash[6];
      hash[6] = hash[5];
      hash[5] = hash[4];
      hash[4] = (hash[3] + temp1) | 0;
      hash[3] = hash[2];
      hash[2] = hash[1];
      hash[1] = hash[0];
      hash[0] = (temp1 + temp2) | 0;
    }

    for (let i = 0; i < 8; i++) {
      hash[i] = (hash[i] + oldHash[i]) | 0;
    }
  }

  let result = "";
  for (let i = 0; i < 8; i++) {
    for (let j = 3; j >= 0; j--) {
      const b = (hash[i] >> (j * 8)) & 255;
      result += (b < 16 ? "0" : "") + b.toString(16);
    }
  }
  return result;
}

/**
 * Computes canonical workload config digest:
 * sha256(model_plugin_id:dataset_id:executed_scope:backend_commit)
 */
export function computeWorkloadConfigDigest(
  modelPluginId: string,
  datasetId: string,
  executedScope: ExecutionScopeName,
  backendCommit: string
): string {
  const canonicalString = `${modelPluginId}:${datasetId}:${executedScope}:${backendCommit}`;
  return `sha256:${sha256Sync(canonicalString)}`;
}

/**
 * Validates raw execution receipt with strict fail-closed cross-field invariants.
 */
export function validateExecutionReceipt(raw: unknown): ExecutionReceipt {
  if (typeof raw !== "object" || raw === null) {
    throw new ReceiptValidationError("Execution receipt must be a JSON object");
  }
  const obj = raw as Record<string, unknown>;

  if (obj.schema_version !== "1.0.0") {
    throw new ReceiptValidationError(
      `Invalid schema_version: ${String(obj.schema_version)} (expected '1.0.0')`
    );
  }
  if (obj.receipt_type !== "DELTAREDUCE_EXECUTION_RECEIPT") {
    throw new ReceiptValidationError(
      `Invalid receipt_type: ${String(obj.receipt_type)} (expected 'DELTAREDUCE_EXECUTION_RECEIPT')`
    );
  }

  // 1. Provenance
  if (typeof obj.provenance !== "object" || obj.provenance === null) {
    throw new ReceiptValidationError("Missing provenance object in receipt");
  }
  const prov = obj.provenance as Record<string, unknown>;
  if (
    typeof prov.repository !== "string" ||
    !prov.repository.trim() ||
    typeof prov.produced_at !== "string" ||
    !prov.produced_at.trim()
  ) {
    throw new ReceiptValidationError("Invalid repository or produced_at in receipt provenance");
  }
  if (
    typeof prov.backend_commit !== "string" ||
    !/^[0-9a-f]{40}$/u.test(prov.backend_commit)
  ) {
    throw new ReceiptValidationError(
      `backend_commit must be a 40-character git SHA hex string, got: ${String(prov.backend_commit)}`
    );
  }
  if (prov.catalog_backend_ref !== undefined) {
    if (
      typeof prov.catalog_backend_ref !== "string" ||
      !/^[0-9a-f]{40}$/u.test(prov.catalog_backend_ref)
    ) {
      throw new ReceiptValidationError(
        `catalog_backend_ref must be a 40-character git SHA hex string if present, got: ${String(prov.catalog_backend_ref)}`
      );
    }
    if (prov.catalog_backend_ref !== prov.backend_commit) {
      throw new ReceiptValidationError(
        `catalog_backend_ref (${String(prov.catalog_backend_ref)}) must match backend_commit (${String(prov.backend_commit)})`
      );
    }
  }
  if (prov.producer_commit !== undefined) {
    if (
      typeof prov.producer_commit !== "string" ||
      !/^[0-9a-f]{40}$/u.test(prov.producer_commit)
    ) {
      throw new ReceiptValidationError(
        `producer_commit must be a 40-character git SHA hex string if present, got: ${String(prov.producer_commit)}`
      );
    }
  }

  // 2. Workload
  if (typeof obj.workload !== "object" || obj.workload === null) {
    throw new ReceiptValidationError("Missing workload object in receipt");
  }
  const wl = obj.workload as Record<string, unknown>;
  if (
    typeof wl.model_plugin_id !== "string" ||
    !wl.model_plugin_id.trim() ||
    typeof wl.dataset_id !== "string" ||
    !wl.dataset_id.trim()
  ) {
    throw new ReceiptValidationError("Invalid model_plugin_id or dataset_id in receipt workload");
  }
  if (
    typeof wl.executed_scope !== "string" ||
    !VALID_SCOPES.includes(wl.executed_scope as ExecutionScopeName)
  ) {
    throw new ReceiptValidationError(
      `Invalid executed_scope in receipt: '${String(wl.executed_scope)}'`
    );
  }
  const executedScope = wl.executed_scope as ExecutionScopeName;

  if (
    typeof wl.workload_config_digest !== "string" ||
    !/^sha256:[0-9a-f]{64}$/u.test(wl.workload_config_digest)
  ) {
    throw new ReceiptValidationError(
      `workload_config_digest must be formatted as 'sha256:<64 hex chars>', got: ${String(wl.workload_config_digest)}`
    );
  }

  // Canonical digest integrity verification
  const expectedCanonicalDigest = computeWorkloadConfigDigest(
    wl.model_plugin_id,
    wl.dataset_id,
    executedScope,
    prov.backend_commit
  );
  if (wl.workload_config_digest !== expectedCanonicalDigest) {
    throw new ReceiptValidationError(
      `Tampered workload_config_digest: declared '${wl.workload_config_digest}' does not match canonical calculation '${expectedCanonicalDigest}'`
    );
  }

  // 3. Execution
  if (typeof obj.execution !== "object" || obj.execution === null) {
    throw new ReceiptValidationError("Missing execution object in receipt");
  }
  const exec = obj.execution as Record<string, unknown>;
  if (
    exec.verdict !== "SUCCESS" &&
    exec.verdict !== "REJECTED_PREFLIGHT" &&
    exec.verdict !== "ABORTED"
  ) {
    throw new ReceiptValidationError(`Invalid execution.verdict: ${String(exec.verdict)}`);
  }
  if (typeof exec.terminal_status !== "string" || !exec.terminal_status.trim()) {
    throw new ReceiptValidationError("Invalid or missing execution.terminal_status in receipt");
  }

  // 4. Cross-Field Invariants on Consensus Evidence vs Observation vs Scopes
  const hasConsensusEvidence =
    typeof obj.consensus_evidence === "object" && obj.consensus_evidence !== null;
  const hasObservationSummary =
    typeof obj.observation_summary === "object" && obj.observation_summary !== null;

  if (executedScope === "STAGE_C_REAL_DRQ1") {
    if (!hasConsensusEvidence) {
      throw new ReceiptValidationError(
        "Stage C execution receipt strictly requires 'consensus_evidence' block"
      );
    }
    if (hasObservationSummary) {
      throw new ReceiptValidationError(
        "Stage C execution receipt must not contain 'observation_summary'"
      );
    }

    const ce = obj.consensus_evidence as Record<string, unknown>;
    if (
      typeof ce.round_id !== "number" ||
      !Number.isInteger(ce.round_id) ||
      ce.round_id < 0 ||
      typeof ce.state_root !== "string" ||
      !/^sha256:[0-9a-f]{64}$/u.test(ce.state_root) ||
      typeof ce.canonical_model_digest !== "string" ||
      !/^sha256:[0-9a-f]{64}$/u.test(ce.canonical_model_digest) ||
      typeof ce.checkpoint_ref !== "string" ||
      !ce.checkpoint_ref.trim() ||
      (ce.applied_status !== "APPLIED" && ce.applied_status !== "COMMITTED") ||
      typeof ce.wal_sequence !== "number" ||
      !Number.isInteger(ce.wal_sequence) ||
      ce.wal_sequence < 0
    ) {
      throw new ReceiptValidationError(
        "Invalid consensus_evidence fields: state_root and canonical_model_digest must be formatted as 'sha256:<64 hex chars>'"
      );
    }

    if (exec.verdict !== "SUCCESS") {
      throw new ReceiptValidationError(
        `Contradictory consensus status: consensus_evidence with applied_status '${ce.applied_status}' strictly requires execution.verdict to be 'SUCCESS', got '${exec.verdict}'`
      );
    }
  } else if (executedScope === "MODEL_DATASET_BINDING_ONLY") {
    if (hasConsensusEvidence) {
      throw new ReceiptValidationError(
        "Observation-only receipt strictly forbids 'consensus_evidence' block"
      );
    }
    if (!hasObservationSummary) {
      throw new ReceiptValidationError(
        "Observation-only receipt strictly requires 'observation_summary' block"
      );
    }

    const obs = obj.observation_summary as Record<string, unknown>;
    if (
      typeof obs.observation_note !== "string" ||
      !obs.observation_note.trim() ||
      typeof obs.metrics !== "object" ||
      obs.metrics === null ||
      Object.keys(obs.metrics).length === 0
    ) {
      throw new ReceiptValidationError("Invalid observation_summary in observation receipt");
    }
  } else if (executedScope === "PLUGIN_BOUNDARY") {
    if (hasConsensusEvidence) {
      throw new ReceiptValidationError(
        "Plugin-boundary receipt strictly forbids 'consensus_evidence' block"
      );
    }
  }

  // 5. Reference Anchor Validation
  if (obj.reference_anchor !== undefined && obj.reference_anchor !== null) {
    if (typeof obj.reference_anchor !== "object") {
      throw new ReceiptValidationError("Invalid reference_anchor in receipt");
    }
    const ra = obj.reference_anchor as Record<string, unknown>;
    if (
      typeof ra.reference_anchor_declared !== "boolean" ||
      typeof ra.anchor_description !== "string" ||
      !ra.anchor_description.trim() ||
      (typeof ra.declared_baseline_metric !== "string" &&
        typeof ra.declared_baseline_metric !== "number")
    ) {
      throw new ReceiptValidationError("Invalid reference_anchor fields in receipt");
    }
  }

  return raw as ExecutionReceipt;
}

/**
 * Evaluates binding of a valid receipt against the active workload selector parameters.
 */
export function evaluateReceiptBinding(
  receipt: ExecutionReceipt,
  currentModelId: string,
  currentDatasetId: string,
  currentScope: ExecutionScopeName,
  catalogBackendRef: string,
  catalogRepository: string
): BindingEvaluationResult {
  const expectedDigest = computeWorkloadConfigDigest(
    currentModelId,
    currentDatasetId,
    currentScope,
    catalogBackendRef
  );
  const actualDigest = receipt.workload.workload_config_digest;

  const matches =
    receipt.provenance.repository === catalogRepository &&
    receipt.workload.model_plugin_id === currentModelId &&
    receipt.workload.dataset_id === currentDatasetId &&
    receipt.workload.executed_scope === currentScope &&
    actualDigest === expectedDigest;

  if (!matches) {
    let reason = "Workload configuration digest mismatch";
    if (receipt.provenance.repository !== catalogRepository) {
      reason = `Receipt repository '${receipt.provenance.repository}' does not match active catalog repository '${catalogRepository}'`;
    } else if (receipt.workload.model_plugin_id !== currentModelId) {
      reason = `Receipt model '${receipt.workload.model_plugin_id}' does not match selected model '${currentModelId}'`;
    } else if (receipt.workload.dataset_id !== currentDatasetId) {
      reason = `Receipt dataset '${receipt.workload.dataset_id}' does not match selected dataset '${currentDatasetId}'`;
    } else if (receipt.workload.executed_scope !== currentScope) {
      reason = `Receipt scope '${receipt.workload.executed_scope}' does not match selected scope '${currentScope}'`;
    } else if (actualDigest !== expectedDigest) {
      reason = `Receipt backend commit does not match active catalog reference`;
    }

    return {
      state: "RECEIPT_LOADED_UNBOUND",
      expectedDigest,
      actualDigest,
      reason,
    };
  }

  let evidenceType: EvidenceType = "UNATTESTED_CONSENSUS_RECORD";
  if (receipt.workload.executed_scope === "MODEL_DATASET_BINDING_ONLY") {
    evidenceType = "OBSERVATION_RECORD";
  } else if (receipt.workload.executed_scope === "PLUGIN_BOUNDARY") {
    evidenceType = "UNATTESTED_PLUGIN_BOUNDARY_RECORD";
  } else if (receipt.reference_anchor && !receipt.consensus_evidence) {
    evidenceType = "REFERENCE_ANCHOR";
  }

  return {
    state: "STRUCTURALLY_VALID_BOUND_RECEIPT",
    evidenceType,
    expectedDigest,
    actualDigest,
  };
}
