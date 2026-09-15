"""Integration tests for cross-domain model-dataset binding and contract validation."""

from __future__ import annotations

import numpy as np
import pytest
from deltatorrent.data.base import ContractCompatibilityError
from deltatorrent.model_plugins import (
    DomainBindingSpec,
    LocalTrainingResult,
    ModelPluginRunnerError,
    bind_model_and_dataset,
    bind_model_dataset_domains,
)
from deltatorrent.model_plugins.eeg_bandpower import TOTAL_ELEMENTS


def test_eeg_runner_binding_success() -> None:
    binding = bind_model_and_dataset(
        model_plugin_id="eeg-bandpower-centroid-v1",
        dataset_id="eeg-synthetic-bci-v1",
    )
    assert binding.model_descriptor.plugin_id == "eeg-bandpower-centroid-v1"
    assert binding.dataset_descriptor.dataset_id == "eeg-synthetic-bci-v1"
    assert binding.model_descriptor.sample_kind == "eeg/bandpower-4ch-4band"
    assert binding.dataset_descriptor.sample_kind == "eeg/bandpower-4ch-4band"

    # Materialize dataset
    meta = binding.materialize_dataset(cache_dir=None)
    assert meta["status"] == "materialized"

    # Train ticket for worker 01
    res = binding.train_ticket(
        ticket_id="ticket-eeg-test-01",
        partition_id="demo-eeg-worker-01",
    )
    assert isinstance(res, LocalTrainingResult)
    assert res.ticket_id == "ticket-eeg-test-01"
    assert "eeg.centroid" in res.tensors
    assert res.tensors["eeg.centroid"].shape == (34,)
    partition_metadata = res.metadata["data_partition_metadata"]
    ticket_context = partition_metadata["ticket_context"]
    assert isinstance(ticket_context, list)
    assert ticket_context[0]["session_id"].startswith("obs-demo-eeg-")
    assert ticket_context[0]["intervention_event_id"].startswith("evt-demo-eeg-")
    assert ticket_context[0]["data_window_id"].startswith("eegwin-demo-")
    assert ticket_context[0]["binding_schema_version"] == "1.0.0"
    assert ticket_context[0]["binding_assertion_id"].startswith("sha256:")
    assert ticket_context[0]["raw_data_hash"].startswith("sha256:")
    assert "point_id" not in ticket_context[0]
    assert "intervention_type" not in ticket_context[0]

    # Evaluate checkpoint
    checkpoint = np.zeros(TOTAL_ELEMENTS, dtype=np.int64)
    checkpoint[:16] = 2500
    checkpoint[16:32] = 7500
    checkpoint[32] = 1
    checkpoint[33] = 1

    eval_res = binding.evaluate_checkpoint(checkpoint)
    assert eval_res.accuracy_ppm >= 0
    assert eval_res.metrics["total"] == 40


def test_cross_domain_fail_closed_rejections() -> None:
    # Model: MNIST, Dataset: EEG
    with pytest.raises(ContractCompatibilityError, match="SAMPLE_KIND_MISMATCH") as exc_info:
        bind_model_and_dataset(
            model_plugin_id="mnist-centroid-v1",
            dataset_id="eeg-synthetic-bci-v1",
        )
    assert "image/grayscale-28x28" in str(exc_info.value)
    assert "eeg/bandpower-4ch-4band" in str(exc_info.value)

    # Model: EEG, Dataset: MNIST
    with pytest.raises(ContractCompatibilityError, match="SAMPLE_KIND_MISMATCH") as exc_info2:
        bind_model_and_dataset(
            model_plugin_id="eeg-bandpower-centroid-v1",
            dataset_id="mnist-v1",
        )
    assert "eeg/bandpower-4ch-4band" in str(exc_info2.value)
    assert "image/grayscale-28x28" in str(exc_info2.value)


def test_multi_domain_binding_structure_is_model_agnostic() -> None:
    domains = bind_model_dataset_domains(
        (
            DomainBindingSpec(
                domain_id="mnist-image",
                model_plugin_id="mnist-centroid-v1",
                dataset_id="mnist-v1",
                role="PRIMARY_DELTA_EXECUTION",
                execution_scope="STAGE_C_REAL_DRQ1",
            ),
            DomainBindingSpec(
                domain_id="eeg-bandpower",
                model_plugin_id="eeg-bandpower-centroid-v1",
                dataset_id="eeg-synthetic-bci-v1",
                role="PLUGIN_BINDING_SMOKE",
                execution_scope="MODEL_DATASET_BINDING_ONLY",
            ),
        )
    )

    assert domains.domain_ids == ("mnist-image", "eeg-bandpower")
    assert domains.get("mnist-image").model_descriptor.plugin_id == "mnist-centroid-v1"
    assert domains.get("eeg-bandpower").model_descriptor.plugin_id == ("eeg-bandpower-centroid-v1")

    descriptions = domains.describe()
    assert [item["domain_id"] for item in descriptions] == ["mnist-image", "eeg-bandpower"]
    assert descriptions[0]["execution_scope"] == "STAGE_C_REAL_DRQ1"
    assert descriptions[1]["execution_scope"] == "MODEL_DATASET_BINDING_ONLY"
    assert descriptions[1]["sample_kind"] == "eeg/bandpower-4ch-4band"
    assert descriptions[1]["total_elements"] == 34


def test_multi_domain_binding_fail_closed_on_invalid_domain_set() -> None:
    with pytest.raises(ModelPluginRunnerError, match="DOMAIN_BINDING_SET_EMPTY"):
        bind_model_dataset_domains(())

    with pytest.raises(ModelPluginRunnerError, match="DUPLICATE_DOMAIN_ID: duplicate"):
        bind_model_dataset_domains(
            (
                DomainBindingSpec(
                    domain_id="duplicate",
                    model_plugin_id="mnist-centroid-v1",
                    dataset_id="mnist-v1",
                ),
                DomainBindingSpec(
                    domain_id="duplicate",
                    model_plugin_id="eeg-bandpower-centroid-v1",
                    dataset_id="eeg-synthetic-bci-v1",
                ),
            )
        )

    with pytest.raises(ModelPluginRunnerError, match="UNKNOWN_DOMAIN_ID: missing"):
        bind_model_dataset_domains(
            (
                DomainBindingSpec(
                    domain_id="mnist-image",
                    model_plugin_id="mnist-centroid-v1",
                    dataset_id="mnist-v1",
                ),
            )
        ).get("missing")
