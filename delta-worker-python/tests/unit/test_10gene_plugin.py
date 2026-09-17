"""Unit tests for the 10-gene phenotype centroid plugin and workload runner."""

from __future__ import annotations

import copy
from typing import Any

import pytest
import torch
from deltatorrent.plugins.contract import (
    DeltaPlugin,
    validate_analyze_response,
    validate_plugin_manifest,
)
from deltatorrent.plugins.phenotype_10gene import (
    Synthetic10GeneCentroidPlugin,
    Synthetic10GeneCohortProvider,
    run_10gene_workload,
)
from deltatorrent.plugins.workload import (
    DatasetProvider,
    ExecutionReceiptError,
    ModelPlugin,
    WorkloadCompatibilityError,
    WorkloadScopeError,
    compute_workload_config_digest,
    run_workload,
    validate_receipt_structure,
)


def test_cohort_provider_conforms_to_dataset_provider_protocol() -> None:
    provider = Synthetic10GeneCohortProvider(num_samples=100, seed=42)
    assert isinstance(provider, DatasetProvider)
    assert provider.dataset_id == "synthetic-10gene-cohort-v1"
    assert provider.sample_kind == "tabular/genomic-10gene-vector"
    assert provider.target_kind == "class-id/0-1"


def test_cohort_provider_determinism_and_shapes() -> None:
    p1 = Synthetic10GeneCohortProvider(num_samples=100, train_ratio=0.8, seed=123)
    p2 = Synthetic10GeneCohortProvider(num_samples=100, train_ratio=0.8, seed=123)

    x_train1, y_train1 = p1.load_train()
    x_train2, y_train2 = p2.load_train()
    x_test1, y_test1 = p1.load_test()
    x_test2, y_test2 = p2.load_test()

    assert x_train1.shape == (80, 10)
    assert y_train1.shape == (80,)
    assert x_test1.shape == (20, 10)
    assert y_test1.shape == (20,)

    assert torch.equal(x_train1, x_train2)
    assert torch.equal(y_train1, y_train2)
    assert torch.equal(x_test1, x_test2)
    assert torch.equal(y_test1, y_test2)
    assert p1.dataset_digest() == p2.dataset_digest()

    # Verify class balance
    assert (y_train1 == 0).sum().item() == 40
    assert (y_train1 == 1).sum().item() == 40


def test_cohort_provider_domain_validation() -> None:
    provider = Synthetic10GeneCohortProvider(num_samples=40, seed=42)
    x_train, y_train = provider.load_train()

    # Valid
    provider.validate_sample(x_train, y_train)

    # Invalid feature dimensions
    with pytest.raises(ValueError, match="Features must have shape"):
        provider.validate_sample(torch.randn(10, 5), torch.zeros(10, dtype=torch.int64))

    # Invalid target values (non-binary)
    with pytest.raises(ValueError, match="Targets must be binary"):
        provider.validate_sample(torch.randn(10, 10), torch.tensor([0, 1, 2, 0, 1, 0, 1, 0, 1, 0]))


def test_centroid_plugin_conforms_to_protocols() -> None:
    plugin = Synthetic10GeneCentroidPlugin()
    assert isinstance(plugin, ModelPlugin)
    assert isinstance(plugin, DeltaPlugin)
    assert plugin.plugin_id == "tabular-10gene-phenotype-v1"
    assert plugin.sample_kind == "tabular/genomic-10gene-vector"
    assert plugin.target_kind == "class-id/0-1"
    assert plugin.supports_stage_c_real_drq1 is True
    assert plugin.is_trained is False


def test_centroid_plugin_untrained_abstains() -> None:
    plugin = Synthetic10GeneCentroidPlugin()
    assert plugin.health()["status"] == "UNINITIALIZED"

    with pytest.raises(RuntimeError, match="Cannot compute digest for untrained model"):
        plugin.canonical_model_digest()

    resp = plugin.analyze({"sample": [0.0] * 10})
    assert resp["status"] == "ABSTAIN"
    assert "MODEL_NOT_TRAINED" in resp["reason_codes"]


def test_centroid_plugin_fitting_and_high_accuracy() -> None:
    provider = Synthetic10GeneCohortProvider(num_samples=200, train_ratio=0.8, seed=42)
    x_train, y_train = provider.load_train()
    x_test, y_test = provider.load_test()

    plugin = Synthetic10GeneCentroidPlugin()
    plugin.fit(x_train, y_train)
    assert plugin.is_trained is True

    metrics = plugin.evaluate(x_test, y_test)
    assert metrics["accuracy"] >= 0.90
    assert metrics["macro_f1"] >= 0.90

    digest1 = plugin.canonical_model_digest()
    assert digest1.startswith("sha256:")
    assert len(digest1) == 71

    # Reproducibility
    plugin2 = Synthetic10GeneCentroidPlugin()
    plugin2.fit(x_train, y_train)
    digest2 = plugin2.canonical_model_digest()
    assert digest1 == digest2


def test_centroid_plugin_metadata_conforms_to_registry_contract() -> None:
    plugin = Synthetic10GeneCentroidPlugin()
    provider = Synthetic10GeneCohortProvider(num_samples=40, seed=42)
    plugin.fit(*provider.load_train())

    manifest = plugin.metadata()
    validate_plugin_manifest(manifest)
    assert manifest["plugin_id"] == "tabular-10gene-phenotype-v1"
    assert manifest["failure_policy"]["mode"] == "fail-closed"


def test_centroid_plugin_analyze_endpoint() -> None:
    plugin = Synthetic10GeneCentroidPlugin()
    provider = Synthetic10GeneCohortProvider(num_samples=40, seed=42)
    plugin.fit(*provider.load_train())

    # Carrier-like sample (+0.5 across all genes)
    carrier_sample = [0.5] * 10
    resp = plugin.analyze({"sample": carrier_sample})
    validate_analyze_response(resp)
    assert resp["status"] == "ANALYZED"
    assert resp["ranking"][0]["class_id"] == 1
    assert resp["ranking"][0]["label"] == "CARRIER"

    # Incompatible sample length
    bad_resp = plugin.analyze({"sample": [0.5] * 8})
    assert bad_resp["status"] == "PLUGIN_INCOMPATIBLE"
    assert "INVALID_SAMPLE_DIMENSIONS" in bad_resp["reason_codes"]


def test_run_10gene_workload_stage_c_receipt() -> None:
    commit = "670b58f6458fe84620f4f9f46401f855d04ae05d"
    receipt = run_10gene_workload(
        scope="STAGE_C_REAL_DRQ1",
        backend_commit=commit,
        repository="chartjs333/delta",
        round_id=1,
        wal_sequence=12,
        produced_at="2026-09-17T08:00:00.000Z",
        seed=42,
    )

    validate_receipt_structure(receipt)

    assert receipt["schema_version"] == "1.0.0"
    assert receipt["receipt_type"] == "DELTAREDUCE_EXECUTION_RECEIPT"
    assert receipt["provenance"]["backend_commit"] == commit
    assert receipt["provenance"]["repository"] == "chartjs333/delta"
    assert receipt["workload"]["model_plugin_id"] == "tabular-10gene-phenotype-v1"
    assert receipt["workload"]["dataset_id"] == "synthetic-10gene-cohort-v1"
    assert receipt["workload"]["executed_scope"] == "STAGE_C_REAL_DRQ1"

    expected_digest = compute_workload_config_digest(
        "tabular-10gene-phenotype-v1",
        "synthetic-10gene-cohort-v1",
        "STAGE_C_REAL_DRQ1",
        commit,
    )
    assert receipt["workload"]["workload_config_digest"] == expected_digest

    assert receipt["execution"]["verdict"] == "SUCCESS"
    assert receipt["execution"]["terminal_status"] == "COMPLETED"

    ce = receipt["consensus_evidence"]
    assert ce["round_id"] == 1
    assert ce["applied_status"] == "APPLIED"
    assert ce["wal_sequence"] == 12
    assert ce["checkpoint_ref"] == "delta://checkpoints/tabular-10gene-phenotype-v1/round-0001.bin"
    assert ce["state_root"].startswith("sha256:")
    assert ce["canonical_model_digest"].startswith("sha256:")

    assert "observation_summary" not in receipt


def test_run_10gene_workload_observation_receipt() -> None:
    commit = "670b58f6458fe84620f4f9f46401f855d04ae05d"
    receipt = run_10gene_workload(
        scope="MODEL_DATASET_BINDING_ONLY",
        backend_commit=commit,
    )
    validate_receipt_structure(receipt)
    assert "observation_summary" in receipt
    assert "consensus_evidence" not in receipt


def test_workload_compatibility_rejection() -> None:
    class IncompatibleDataset:
        @property
        def dataset_id(self) -> str:
            return "incompatible-mnist-v1"

        @property
        def sample_kind(self) -> str:
            return "image/mnist-28x28"

        @property
        def target_kind(self) -> str:
            return "class-id/0-9"

        def load_train(self) -> tuple[Any, Any]:
            return (torch.randn(10, 28, 28), torch.zeros(10))

        def load_test(self) -> tuple[Any, Any]:
            return (torch.randn(10, 28, 28), torch.zeros(10))

        def dataset_digest(self) -> str:
            return "sha256:" + "0" * 64

    plugin = Synthetic10GeneCentroidPlugin()
    with pytest.raises(WorkloadCompatibilityError, match="Sample kind mismatch"):
        run_workload(plugin, IncompatibleDataset())  # type: ignore[arg-type]


def test_workload_unsupported_scope_rejection() -> None:
    class SmokeOnlyPlugin(Synthetic10GeneCentroidPlugin):
        @property
        def supports_stage_c_real_drq1(self) -> bool:
            return False

    plugin = SmokeOnlyPlugin()
    provider = Synthetic10GeneCohortProvider(num_samples=40)

    with pytest.raises(WorkloadScopeError, match="does not support STAGE_C_REAL_DRQ1"):
        run_workload(plugin, provider, scope="STAGE_C_REAL_DRQ1")


def test_tampered_receipt_detection() -> None:
    receipt = run_10gene_workload()
    tampered = copy.deepcopy(receipt)
    tampered["workload"]["workload_config_digest"] = "sha256:" + "f" * 64

    with pytest.raises(ExecutionReceiptError, match="Tampered workload_config_digest"):
        validate_receipt_structure(tampered)
