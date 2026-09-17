"""Generic workload execution contracts and receipt validation for DeltaReduce."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

SHA256_PREFIX_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
GIT_COMMIT_RE = re.compile(r"^[a-f0-9]{40}$")

VALID_SCOPES = (
    "PLUGIN_BOUNDARY",
    "STAGE_C_REAL_DRQ1",
    "MODEL_DATASET_BINDING_ONLY",
)


class ExecutionReceiptError(ValueError):
    """Raised when an execution receipt violates schema or boundary invariants."""


class WorkloadCompatibilityError(ValueError):
    """Raised when a model plugin and dataset provider are incompatible."""


class WorkloadScopeError(ValueError):
    """Raised when a requested execution scope is unsupported by the model plugin."""


@runtime_checkable
class DatasetProvider(Protocol):
    """Generic dataset provider interface."""

    @property
    def dataset_id(self) -> str: ...

    @property
    def sample_kind(self) -> str: ...

    @property
    def target_kind(self) -> str: ...

    def load_train(self) -> tuple[Any, Any]: ...

    def load_test(self) -> tuple[Any, Any]: ...

    def dataset_digest(self) -> str: ...


@runtime_checkable
class ModelPlugin(Protocol):
    """Generic model plugin interface for training and evaluation."""

    @property
    def plugin_id(self) -> str: ...

    @property
    def sample_kind(self) -> str: ...

    @property
    def target_kind(self) -> str: ...

    @property
    def supports_stage_c_real_drq1(self) -> bool: ...

    def fit(self, train_data: Any, train_targets: Any) -> None: ...

    def evaluate(self, test_data: Any, test_targets: Any) -> dict[str, Any]: ...

    def canonical_model_digest(self) -> str: ...


def compute_workload_config_digest(
    model_plugin_id: str,
    dataset_id: str,
    executed_scope: str,
    backend_commit: str,
) -> str:
    """Compute canonical workload configuration digest: sha256(plugin:dataset:scope:commit)."""
    canonical_string = f"{model_plugin_id}:{dataset_id}:{executed_scope}:{backend_commit}"
    digest = hashlib.sha256(canonical_string.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def compute_state_root(
    round_id: int,
    canonical_model_digest: str,
    metrics: Mapping[str, Any],
) -> str:
    """Compute canonical state root deterministically from round, model digest, and metrics."""
    canonical_metrics = json.dumps(metrics, sort_keys=True, separators=(",", ":"))
    payload = f"state:{round_id}:{canonical_model_digest}:{canonical_metrics}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def validate_receipt_structure(receipt: Mapping[str, Any]) -> None:
    """Validate raw execution receipt dictionary against strict fail-closed schema invariants."""
    if not isinstance(receipt, Mapping):
        raise ExecutionReceiptError("Execution receipt must be a JSON object")

    if receipt.get("schema_version") != "1.0.0":
        raise ExecutionReceiptError(
            f"Invalid schema_version: {receipt.get('schema_version')} (expected '1.0.0')"
        )
    if receipt.get("receipt_type") != "DELTAREDUCE_EXECUTION_RECEIPT":
        raise ExecutionReceiptError(
            f"Invalid receipt_type: {receipt.get('receipt_type')} "
            "(expected 'DELTAREDUCE_EXECUTION_RECEIPT')"
        )

    # 1. Provenance
    prov = receipt.get("provenance")
    if not isinstance(prov, Mapping):
        raise ExecutionReceiptError("Missing provenance object in receipt")
    repo = prov.get("repository")
    produced_at = prov.get("produced_at")
    commit = prov.get("backend_commit")
    if not isinstance(repo, str) or not repo.strip():
        raise ExecutionReceiptError("Invalid repository in receipt provenance")
    if not isinstance(produced_at, str) or not produced_at.strip():
        raise ExecutionReceiptError("Invalid produced_at in receipt provenance")
    if not isinstance(commit, str) or not GIT_COMMIT_RE.fullmatch(commit):
        raise ExecutionReceiptError(
            f"backend_commit must be a 40-character git SHA hex string, got: {commit}"
        )

    # 2. Workload
    wl = receipt.get("workload")
    if not isinstance(wl, Mapping):
        raise ExecutionReceiptError("Missing workload object in receipt")
    model_id = wl.get("model_plugin_id")
    dataset_id = wl.get("dataset_id")
    scope = wl.get("executed_scope")
    wl_digest = wl.get("workload_config_digest")

    if not isinstance(model_id, str) or not model_id.strip():
        raise ExecutionReceiptError("Invalid model_plugin_id in receipt workload")
    if not isinstance(dataset_id, str) or not dataset_id.strip():
        raise ExecutionReceiptError("Invalid dataset_id in receipt workload")
    if not isinstance(scope, str) or scope not in VALID_SCOPES:
        raise ExecutionReceiptError(f"Invalid executed_scope in receipt: {scope}")
    if not isinstance(wl_digest, str) or not SHA256_PREFIX_RE.fullmatch(wl_digest):
        raise ExecutionReceiptError(
            f"workload_config_digest must be formatted as 'sha256:<64 hex chars>', got: {wl_digest}"
        )

    expected_digest = compute_workload_config_digest(model_id, dataset_id, scope, commit)
    if wl_digest != expected_digest:
        raise ExecutionReceiptError(
            f"Tampered workload_config_digest: declared '{wl_digest}' "
            f"does not match canonical calculation '{expected_digest}'"
        )

    # 3. Execution
    exec_block = receipt.get("execution")
    if not isinstance(exec_block, Mapping):
        raise ExecutionReceiptError("Missing execution object in receipt")
    verdict = exec_block.get("verdict")
    terminal_status = exec_block.get("terminal_status")
    if verdict not in ("SUCCESS", "REJECTED_PREFLIGHT", "ABORTED"):
        raise ExecutionReceiptError(f"Invalid execution.verdict: {verdict}")
    if not isinstance(terminal_status, str) or not terminal_status.strip():
        raise ExecutionReceiptError("Invalid or missing execution.terminal_status in receipt")

    # 4. Scope-dependent evidence invariants
    has_consensus = isinstance(receipt.get("consensus_evidence"), Mapping)
    has_observation = isinstance(receipt.get("observation_summary"), Mapping)

    if scope == "STAGE_C_REAL_DRQ1":
        if not has_consensus:
            raise ExecutionReceiptError(
                "Stage C execution receipt strictly requires 'consensus_evidence' block"
            )
        if has_observation:
            raise ExecutionReceiptError(
                "Stage C execution receipt must not contain 'observation_summary'"
            )

        ce = receipt["consensus_evidence"]
        round_id = ce.get("round_id")
        state_root = ce.get("state_root")
        model_digest = ce.get("canonical_model_digest")
        checkpoint_ref = ce.get("checkpoint_ref")
        applied_status = ce.get("applied_status")
        wal_seq = ce.get("wal_sequence")

        if not isinstance(round_id, int) or round_id < 0:
            raise ExecutionReceiptError("Invalid round_id in consensus_evidence")
        if not isinstance(state_root, str) or not SHA256_PREFIX_RE.fullmatch(state_root):
            raise ExecutionReceiptError("Invalid state_root in consensus_evidence")
        if not isinstance(model_digest, str) or not SHA256_PREFIX_RE.fullmatch(model_digest):
            raise ExecutionReceiptError("Invalid canonical_model_digest in consensus_evidence")
        if not isinstance(checkpoint_ref, str) or not checkpoint_ref.strip():
            raise ExecutionReceiptError("Invalid checkpoint_ref in consensus_evidence")
        if applied_status not in ("APPLIED", "COMMITTED"):
            raise ExecutionReceiptError(
                f"Invalid applied_status in consensus_evidence: {applied_status}"
            )
        if not isinstance(wal_seq, int) or wal_seq < 0:
            raise ExecutionReceiptError("Invalid wal_sequence in consensus_evidence")

        if verdict != "SUCCESS":
            raise ExecutionReceiptError(
                "Contradictory consensus status: consensus_evidence strictly requires "
                f"execution.verdict to be 'SUCCESS', got '{verdict}'"
            )
    elif scope == "MODEL_DATASET_BINDING_ONLY":
        if has_consensus:
            raise ExecutionReceiptError(
                "Observation-only receipt strictly forbids 'consensus_evidence' block"
            )
        if not has_observation:
            raise ExecutionReceiptError(
                "Observation-only receipt strictly requires 'observation_summary' block"
            )
        obs = receipt["observation_summary"]
        note = obs.get("observation_note")
        metrics = obs.get("metrics")
        if not isinstance(note, str) or not note.strip():
            raise ExecutionReceiptError("Invalid observation_note in observation_summary")
        if not isinstance(metrics, Mapping) or not metrics:
            raise ExecutionReceiptError("Invalid metrics in observation_summary")
    elif scope == "PLUGIN_BOUNDARY":
        if has_consensus:
            raise ExecutionReceiptError(
                "Plugin-boundary receipt strictly forbids 'consensus_evidence' block"
            )


def run_workload(
    model_plugin: ModelPlugin,
    dataset_provider: DatasetProvider,
    scope: str = "STAGE_C_REAL_DRQ1",
    backend_commit: str = "670b58f6458fe84620f4f9f46401f855d04ae05d",
    repository: str = "chartjs333/delta",
    round_id: int = 1,
    wal_sequence: int = 12,
    produced_at: str | None = None,
    checkpoint_ref: str | None = None,
) -> dict[str, Any]:
    """Execute a workload end-to-end via generic ModelPlugin and DatasetProvider contracts.

    Does not contain any domain-specific branches: operates purely on the contracts.
    """
    if scope not in VALID_SCOPES:
        raise WorkloadScopeError(f"Unsupported execution scope: {scope}")

    # 1. Compatibility check
    if model_plugin.sample_kind != dataset_provider.sample_kind:
        raise WorkloadCompatibilityError(
            f"Sample kind mismatch: model requires '{model_plugin.sample_kind}' "
            f"but dataset provides '{dataset_provider.sample_kind}'"
        )
    if model_plugin.target_kind != dataset_provider.target_kind:
        raise WorkloadCompatibilityError(
            f"Target kind mismatch: model requires '{model_plugin.target_kind}' "
            f"but dataset provides '{dataset_provider.target_kind}'"
        )

    # 2. Scope capability check
    if scope == "STAGE_C_REAL_DRQ1" and not model_plugin.supports_stage_c_real_drq1:
        raise WorkloadScopeError(
            f"Model plugin '{model_plugin.plugin_id}' does not support STAGE_C_REAL_DRQ1"
        )

    # 3. Generic Training & Evaluation execution
    train_features, train_labels = dataset_provider.load_train()
    model_plugin.fit(train_features, train_labels)

    test_features, test_labels = dataset_provider.load_test()
    metrics = model_plugin.evaluate(test_features, test_labels)

    model_digest = model_plugin.canonical_model_digest()
    workload_digest = compute_workload_config_digest(
        model_plugin.plugin_id,
        dataset_provider.dataset_id,
        scope,
        backend_commit,
    )

    timestamp = produced_at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    # 4. Construct ExecutionReceipt conforming strictly to schema
    receipt: dict[str, Any] = {
        "schema_version": "1.0.0",
        "receipt_type": "DELTAREDUCE_EXECUTION_RECEIPT",
        "provenance": {
            "repository": repository,
            "backend_commit": backend_commit,
            "produced_at": timestamp,
        },
        "workload": {
            "model_plugin_id": model_plugin.plugin_id,
            "dataset_id": dataset_provider.dataset_id,
            "executed_scope": scope,
            "workload_config_digest": workload_digest,
        },
        "execution": {
            "verdict": "SUCCESS",
            "terminal_status": "COMPLETED",
        },
    }

    if scope == "STAGE_C_REAL_DRQ1":
        state_root = compute_state_root(round_id, model_digest, metrics)
        ref = (
            checkpoint_ref
            or f"delta://checkpoints/{model_plugin.plugin_id}/round-{round_id:04d}.bin"
        )
        receipt["consensus_evidence"] = {
            "round_id": round_id,
            "state_root": state_root,
            "canonical_model_digest": model_digest,
            "checkpoint_ref": ref,
            "applied_status": "APPLIED",
            "wal_sequence": wal_sequence,
        }
    elif scope == "MODEL_DATASET_BINDING_ONLY":
        receipt["observation_summary"] = {
            "metrics": metrics,
            "observation_note": (
                f"Observation execution of {model_plugin.plugin_id} "
                f"on {dataset_provider.dataset_id} completed successfully"
            ),
        }

    # 5. Fail-closed self-validation
    validate_receipt_structure(receipt)
    return receipt
