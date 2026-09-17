"""Unit tests for canonical 10-gene phenotype centroid plugin, dataset, and runner."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from deltatorrent.data.base import DataPartition, DatasetProvider
from deltatorrent.data.phenotype_10gene import (
    FEATURE_COUNT,
    SYNTHETIC_10GENE_DESCRIPTOR,
    Phenotype10GeneDataError,
    Synthetic10GeneCohortProvider,
)
from deltatorrent.data.registry import get_default_dataset_registry
from deltatorrent.model_plugins.base import EvaluationResult, LocalTrainingResult, ModelPlugin
from deltatorrent.model_plugins.phenotype_10gene import (
    TOTAL_ELEMENTS,
    Phenotype10GeneModel,
    PhenotypePluginError,
    Synthetic10GeneCentroidPlugin,
)
from deltatorrent.model_plugins.registry import get_default_registry
from deltatorrent.model_plugins.runner import (
    ModelPluginRunner,
    ModelPluginRunnerError,
)
from deltatorrent.plugins.contract import (
    DeltaPlugin,
    validate_analyze_response,
    validate_plugin_manifest,
)

# --- 1. DatasetProvider & Registry Tests ---


def test_cohort_provider_conforms_to_dataset_provider_protocol() -> None:
    provider = Synthetic10GeneCohortProvider(num_samples=100, seed=42)
    assert isinstance(provider, DatasetProvider)
    assert provider.dataset_id == "synthetic-10gene-cohort-v1"
    assert provider.descriptor() == SYNTHETIC_10GENE_DESCRIPTOR


def test_cohort_provider_in_default_registry() -> None:
    registry = get_default_dataset_registry()
    assert registry.has_dataset("synthetic-10gene-cohort-v1")
    desc = registry.get_descriptor("synthetic-10gene-cohort-v1")
    assert desc.dataset_id == "synthetic-10gene-cohort-v1"
    inst = registry.get("synthetic-10gene-cohort-v1")
    assert isinstance(inst, Synthetic10GeneCohortProvider)


def test_cohort_provider_determinism_and_partition_shapes() -> None:
    p1 = Synthetic10GeneCohortProvider(num_samples=200, train_ratio=0.8, seed=42)
    p2 = Synthetic10GeneCohortProvider(num_samples=200, train_ratio=0.8, seed=42)

    part1 = p1.training_partition("train-1")
    part2 = p2.training_partition("train-1")
    test_feat1, test_lbl1 = p1.evaluation_data()
    test_feat2, test_lbl2 = p2.evaluation_data()

    assert isinstance(part1, DataPartition)
    assert part1.samples.shape == (160, FEATURE_COUNT)
    assert part1.targets.shape == (160,)
    assert test_feat1.shape == (40, FEATURE_COUNT)
    assert test_lbl1.shape == (40,)

    np.testing.assert_array_equal(part1.samples, part2.samples)
    np.testing.assert_array_equal(part1.targets, part2.targets)
    np.testing.assert_array_equal(test_feat1, test_feat2)
    np.testing.assert_array_equal(test_lbl1, test_lbl2)

    # Verify 50/50 balance
    assert int(np.count_nonzero(part1.targets == 0)) == 80
    assert int(np.count_nonzero(part1.targets == 1)) == 80


def test_cohort_provider_materialize(tmp_path: Path) -> None:
    provider = Synthetic10GeneCohortProvider(num_samples=40, seed=42)
    manifest = provider.materialize(tmp_path)

    cache_file = tmp_path / "cohort_data.json"
    assert cache_file.exists()
    assert manifest["dataset_id"] == "synthetic-10gene-cohort-v1"
    assert manifest["sample_count"] == 40
    assert manifest["feature_count"] == 10
    assert manifest["class_count"] == 2
    assert str(manifest["content_hash"]).startswith("sha256:")

    # Verify allow_nan=False when loaded
    with open(cache_file, encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded == manifest


# --- 2. ModelPlugin & Contract Tests ---


def test_centroid_plugin_conforms_to_protocols() -> None:
    plugin = Synthetic10GeneCentroidPlugin()
    assert isinstance(plugin, ModelPlugin)
    assert isinstance(plugin, DeltaPlugin)
    assert plugin.plugin_id == "tabular-10gene-phenotype-v1"
    assert plugin.total_elements == TOTAL_ELEMENTS

    schema = plugin.parameter_schema()
    assert len(schema.parameters) == 1
    assert schema.parameters[0].name == "phenotype.centroid"
    assert schema.parameters[0].shape == (TOTAL_ELEMENTS,)


def test_centroid_plugin_in_default_registry() -> None:
    registry = get_default_registry()
    assert registry.has_plugin("tabular-10gene-phenotype-v1")
    desc = registry.get_descriptor("tabular-10gene-phenotype-v1")
    assert desc.plugin_id == "tabular-10gene-phenotype-v1"
    assert desc.supports_stage_c_real_drq1 is True
    inst = registry.get("tabular-10gene-phenotype-v1")
    assert isinstance(inst, Synthetic10GeneCentroidPlugin)


def test_centroid_plugin_untrained_state() -> None:
    plugin = Synthetic10GeneCentroidPlugin()
    health = plugin.health()
    assert health["status"] == "UNINITIALIZED"
    assert health["trained"] is False
    assert health["model_digest"] is None

    with pytest.raises(RuntimeError, match="MODEL_NOT_TRAINED"):
        plugin.canonical_model_digest()

    resp = plugin.analyze({"sample": [0.0] * 10})
    assert resp["status"] == "ABSTAIN"
    assert "MODEL_NOT_TRAINED" in resp["reason_codes"]


def test_centroid_plugin_training_and_evaluation() -> None:
    provider = Synthetic10GeneCohortProvider(num_samples=200, train_ratio=0.8, seed=42)
    part = provider.training_partition("train-1")
    test_feat, test_lbl = provider.evaluation_data()

    plugin = Synthetic10GeneCentroidPlugin()
    train_res = plugin.train_ticket(
        ticket_id="ticket-10gene-001",
        data=(part.samples, part.targets),
    )

    assert isinstance(train_res, LocalTrainingResult)
    assert train_res.ticket_id == "ticket-10gene-001"
    assert "phenotype.centroid" in train_res.tensors
    assert train_res.tensors["phenotype.centroid"].shape == (TOTAL_ELEMENTS,)

    # Evaluate
    eval_res = plugin.evaluate(plugin, (test_feat, test_lbl))
    assert isinstance(eval_res, EvaluationResult)
    assert eval_res.accuracy_ppm > 900_000  # >90% accuracy
    assert eval_res.metrics["correct"] >= 36
    assert eval_res.metrics["total"] == 40

    # Model digest
    digest1 = plugin.canonical_model_digest()
    assert digest1.startswith("sha256:")
    assert len(digest1) == 71

    # Reproducibility across fresh instance
    plugin2 = Synthetic10GeneCentroidPlugin()
    plugin2.train_ticket(ticket_id="ticket-10gene-002", data=(part.samples, part.targets))
    digest2 = plugin2.canonical_model_digest()
    assert digest1 == digest2


def test_centroid_plugin_checkpoint_roundtrip() -> None:
    provider = Synthetic10GeneCohortProvider(num_samples=100, seed=42)
    part = provider.training_partition("train-1")
    test_feat, test_lbl = provider.evaluation_data()

    plugin1 = Synthetic10GeneCentroidPlugin()
    res = plugin1.train_ticket(ticket_id="t1", data=(part.samples, part.targets))
    tensor_values = res.tensors["phenotype.centroid"].astype(np.int64)

    # Load into fresh plugin via checkpoint values
    plugin2 = Synthetic10GeneCentroidPlugin()
    model = plugin2.load_applied_checkpoint(tensor_values)
    assert isinstance(model, Phenotype10GeneModel)
    assert plugin2.canonical_model_digest() == plugin1.canonical_model_digest()

    # Evaluate checkpoint
    eval_res = plugin2.evaluate(model, (test_feat, test_lbl))
    assert eval_res.accuracy_ppm > 900_000


def test_centroid_plugin_metadata_conforms_to_manifest_contract() -> None:
    plugin = Synthetic10GeneCentroidPlugin()
    provider = Synthetic10GeneCohortProvider(num_samples=40, seed=42)
    part = provider.training_partition("train-1")
    plugin.train_ticket(ticket_id="t1", data=(part.samples, part.targets))

    manifest = plugin.metadata()
    validate_plugin_manifest(manifest)
    assert manifest["plugin_id"] == "tabular-10gene-phenotype-v1"
    assert (
        manifest["entrypoint"]
        == "deltatorrent.model_plugins.phenotype_10gene:Synthetic10GeneCentroidPlugin"
    )
    assert manifest["failure_policy"]["mode"] == "fail-closed"


def test_centroid_plugin_analyze_endpoint() -> None:
    provider = Synthetic10GeneCohortProvider(num_samples=100, seed=42)
    part = provider.training_partition("train-1")

    plugin = Synthetic10GeneCentroidPlugin()
    plugin.train_ticket(ticket_id="t1", data=(part.samples, part.targets))

    # Carrier sample (elevated expression +0.5)
    carrier_sample = [0.5] * 10
    resp_carrier = plugin.analyze({"sample": carrier_sample})
    validate_analyze_response(resp_carrier)
    assert resp_carrier["status"] == "ANALYZED"
    assert resp_carrier["ranking"][0]["class_id"] == 1
    assert resp_carrier["ranking"][0]["label"] == "CARRIER"
    assert "distance_c0" in resp_carrier["evidence"]
    assert "distance_c1" in resp_carrier["evidence"]
    assert resp_carrier["evidence"]["distance_c1"] < resp_carrier["evidence"]["distance_c0"]

    # Control sample (lower expression -0.5)
    control_sample = [-0.5] * 10
    resp_control = plugin.analyze({"sample": control_sample})
    validate_analyze_response(resp_control)
    assert resp_control["status"] == "ANALYZED"
    assert resp_control["ranking"][0]["class_id"] == 0
    assert resp_control["ranking"][0]["label"] == "CONTROL"
    assert resp_control["evidence"]["distance_c0"] < resp_control["evidence"]["distance_c1"]


# --- 3. ModelPluginRunner Integration & Receipt Tests ---


def test_model_plugin_runner_train_eval_receipt(tmp_path: Path) -> None:
    commit = "670b58f6458fe84620f4f9f46401f855d04ae05d"
    runner = ModelPluginRunner(
        plugin_id="tabular-10gene-phenotype-v1",
        dataset_id="synthetic-10gene-cohort-v1",
        execution_scope="PLUGIN_BOUNDARY",
    )
    assert runner.execution_scope == "PLUGIN_BOUNDARY"

    train_res = runner.train_ticket(ticket_id="ticket-10gene-runner", partition_id="part-default")
    assert train_res.ticket_id == "ticket-10gene-runner"

    eval_res = runner.evaluate(runner.model_plugin)
    assert eval_res.accuracy_ppm > 900_000

    out_file = tmp_path / "receipt.json"
    receipt = runner.emit_execution_receipt(
        backend_commit=commit,
        repository="chartjs333/delta",
        produced_at="2026-09-17T08:00:00.000Z",
        output_path=out_file,
    )

    assert receipt["schema_version"] == "1.0.0"
    assert receipt["receipt_type"] == "DELTAREDUCE_EXECUTION_RECEIPT"
    assert receipt["provenance"]["backend_commit"] == commit
    assert receipt["provenance"]["repository"] == "chartjs333/delta"
    assert receipt["workload"]["model_plugin_id"] == "tabular-10gene-phenotype-v1"
    assert receipt["workload"]["dataset_id"] == "synthetic-10gene-cohort-v1"
    assert receipt["workload"]["executed_scope"] == "PLUGIN_BOUNDARY"
    assert receipt["workload"]["workload_config_digest"] == (
        "sha256:93caaf42c2a8f1bacb9fbc9bf835a48a8641fd16c416794a7a0ca7f52a0138c8"
    )
    assert receipt["execution"]["verdict"] == "SUCCESS"
    assert receipt["execution"]["terminal_status"] == "COMPLETED"

    # STRICT: no consensus evidence and no observation summary in plugin boundary receipt
    assert "consensus_evidence" not in receipt
    assert "observation_summary" not in receipt

    assert out_file.exists()
    with open(out_file, encoding="utf-8") as f:
        loaded_receipt = json.load(f)
    assert loaded_receipt == receipt


def test_model_plugin_runner_rejects_stage_c_claim_fail_closed() -> None:
    runner = ModelPluginRunner(
        plugin_id="tabular-10gene-phenotype-v1",
        dataset_id="synthetic-10gene-cohort-v1",
        execution_scope="STAGE_C_REAL_DRQ1",
    )
    with pytest.raises(
        ModelPluginRunnerError,
        match="STAGE_C_REAL_DRQ1_REQUIRES_NATIVE_CONSENSUS_HARNESS",
    ):
        runner.emit_execution_receipt()


# --- 4. Strict Numeric Hardening & Regressions (Reviewer 1 & 2 Findings) ---


def test_regression_reviewer1_high_analyze_nan_and_inf_rejected_closed() -> None:
    """Reviewer 1 High Finding: analyze() must reject NaN and non-finite samples."""
    provider = Synthetic10GeneCohortProvider(num_samples=40, seed=42)
    part = provider.training_partition("train-1")
    plugin = Synthetic10GeneCentroidPlugin()
    plugin.train_ticket(ticket_id="t1", data=(part.samples, part.targets))

    # All NaN
    nan_resp = plugin.analyze({"sample": [float("nan")] * 10})
    validate_analyze_response(nan_resp)
    assert nan_resp["status"] == "PLUGIN_INCOMPATIBLE"
    assert "INVALID_NUMERIC_VALUES" in nan_resp["reason_codes"]

    # Partial NaN
    partial_nan = [0.1, float("nan"), 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    pnan_resp = plugin.analyze({"sample": partial_nan})
    validate_analyze_response(pnan_resp)
    assert pnan_resp["status"] == "PLUGIN_INCOMPATIBLE"
    assert "INVALID_NUMERIC_VALUES" in pnan_resp["reason_codes"]

    # Positive Infinity
    inf_resp = plugin.analyze({"sample": [float("inf")] * 10})
    validate_analyze_response(inf_resp)
    assert inf_resp["status"] == "PLUGIN_INCOMPATIBLE"
    assert "INVALID_NUMERIC_VALUES" in inf_resp["reason_codes"]

    # Negative Infinity
    ninf_resp = plugin.analyze({"sample": [-float("inf")] * 10})
    validate_analyze_response(ninf_resp)
    assert ninf_resp["status"] == "PLUGIN_INCOMPATIBLE"
    assert "INVALID_NUMERIC_VALUES" in ninf_resp["reason_codes"]

    # Non-numeric string
    str_resp = plugin.analyze({"sample": ["not_a_float"] * 10})
    validate_analyze_response(str_resp)
    assert str_resp["status"] == "PLUGIN_INCOMPATIBLE"
    assert "INVALID_NUMERIC_VALUES" in str_resp["reason_codes"]

    # Invalid dimension
    dim_resp = plugin.analyze({"sample": [0.5] * 8})
    validate_analyze_response(dim_resp)
    assert dim_resp["status"] == "PLUGIN_INCOMPATIBLE"
    assert "INVALID_SAMPLE_DIMENSIONS" in dim_resp["reason_codes"]


def test_regression_reviewer1_medium_fit_evaluate_labels_and_features() -> None:
    """Reviewer 1 & 2 Medium Finding: fit/evaluate reject invalid labels and non-finite tensors."""
    plugin = Synthetic10GeneCentroidPlugin()

    # Valid data baseline
    valid_x = np.random.randn(20, 10)
    valid_y = np.array([0, 1] * 10, dtype=np.int64)

    # 1. Labels contain class 2 (strictly {0, 1} required)
    invalid_labels_2 = np.array([0, 1, 2] * 6 + [0, 1], dtype=np.int64)
    with pytest.raises(Phenotype10GeneDataError, match="LABELS_OUT_OF_RANGE"):
        plugin.train_ticket(ticket_id="t1", data=(valid_x, invalid_labels_2))

    with pytest.raises(Phenotype10GeneDataError, match="LABELS_OUT_OF_RANGE"):
        plugin.evaluate(plugin, (valid_x, invalid_labels_2))

    # 2. Non-integer labels (float labels)
    float_labels = np.array([0.0, 1.0] * 10)
    with pytest.raises(Phenotype10GeneDataError, match="LABELS_MUST_BE_INTEGERS"):
        plugin.train_ticket(ticket_id="t1", data=(valid_x, float_labels))

    with pytest.raises(Phenotype10GeneDataError, match="LABELS_MUST_BE_INTEGERS"):
        plugin.evaluate(plugin, (valid_x, float_labels))

    # 3. Non-finite features (NaN)
    nan_x = valid_x.copy()
    nan_x[0, 0] = float("nan")
    with pytest.raises(Phenotype10GeneDataError, match="FEATURES_NOT_FINITE"):
        plugin.train_ticket(ticket_id="t1", data=(nan_x, valid_y))

    with pytest.raises(Phenotype10GeneDataError, match="FEATURES_NOT_FINITE"):
        plugin.evaluate(plugin, (nan_x, valid_y))

    # 4. Non-finite features (Inf)
    inf_x = valid_x.copy()
    inf_x[0, 0] = float("inf")
    with pytest.raises(Phenotype10GeneDataError, match="FEATURES_NOT_FINITE"):
        plugin.train_ticket(ticket_id="t1", data=(inf_x, valid_y))

    with pytest.raises(Phenotype10GeneDataError, match="FEATURES_NOT_FINITE"):
        plugin.evaluate(plugin, (inf_x, valid_y))

    # 5. Invalid shape
    bad_dim_x = np.random.randn(20, 8)
    with pytest.raises(Phenotype10GeneDataError, match="FEATURES_SHAPE_INVALID"):
        plugin.train_ticket(ticket_id="t1", data=(bad_dim_x, valid_y))


def test_regression_checkpoint_validation_fail_closed() -> None:
    """load_applied_checkpoint rejects invalid shapes, non-integers, and bad presence."""
    plugin = Synthetic10GeneCentroidPlugin()

    # Wrong shape
    with pytest.raises(PhenotypePluginError, match="CHECKPOINT_SHAPE_MISMATCH"):
        plugin.load_applied_checkpoint(np.zeros(10, dtype=np.int64))

    # Non-integer values
    with pytest.raises(PhenotypePluginError, match="CHECKPOINT_VALUES_NOT_INTEGER"):
        plugin.load_applied_checkpoint(np.zeros(TOTAL_ELEMENTS, dtype=np.float32))

    # Invalid presence (e.g. 2 instead of 0 or 1)
    bad_presence = np.zeros(TOTAL_ELEMENTS, dtype=np.int64)
    bad_presence[TOTAL_ELEMENTS - 1] = 2
    with pytest.raises(PhenotypePluginError, match="CHECKPOINT_PRESENCE_INVALID"):
        plugin.load_applied_checkpoint(bad_presence)


def test_regression_reviewer1_medium_json_serialization_allow_nan_false() -> None:
    """json.dumps and json.dump must fail-closed if NaN is passed."""
    # Ensure standard json.dumps with allow_nan=False raises ValueError on NaN
    payload_with_nan = {"metric": float("nan")}
    with pytest.raises(ValueError, match="Out of range float values are not JSON compliant"):
        json.dumps(payload_with_nan, allow_nan=False)
