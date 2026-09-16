"""Unit tests for ModelPluginRegistry, PluginDescriptor, and extensibility proofs."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
from deltatorrent.domain.manifests import ArtifactRef
from deltatorrent.domain.parameters import (
    FrozenOmissionPolicy,
    LogicalDType,
    ParameterSchema,
    ParameterSpec,
)
from deltatorrent.domain.updates import NormalizedContributionCandidate
from deltatorrent.model_plugins import (
    EegBandpowerCentroidPlugin,
    EvaluationResult,
    LocalTrainingResult,
    MnistCentroidPlugin,
    ModelPlugin,
    ModelPluginRegistry,
    PluginDescriptor,
    PluginRegistryError,
    QloraModelPlugin,
    get_default_registry,
)
from deltatorrent.worker.drq1_producer import produce_drq1_shards


class DummyLinearPlugin:
    """Minimal second plugin implementation to prove generic extensibility."""

    @property
    def plugin_id(self) -> str:
        return "dummy-linear-v1"

    def parameter_schema(self) -> ParameterSchema:
        return ParameterSchema(
            parameters=(
                ParameterSpec(
                    name="dummy.linear",
                    shape=(10,),
                    logical_dtype=LogicalDType.FLOAT32,
                    trainable=True,
                ),
            ),
            tied_aliases={},
            frozen_omission_policy=FrozenOmissionPolicy.INCLUDE_ALL,
        )

    @property
    def tensor_order(self) -> tuple[str, ...]:
        return ("dummy.linear",)

    @property
    def total_elements(self) -> int:
        return 10

    def create_model(self, state: Any | None = None) -> Any:
        if state is None:
            return np.zeros(10, dtype=np.int64)
        return np.asarray(state, dtype=np.int64)

    def train_ticket(
        self,
        *,
        ticket_id: str,
        data: Any,
        parent_model: Any | None = None,
        **kwargs: Any,
    ) -> LocalTrainingResult:
        tensor = np.arange(10, dtype=np.float32)
        return LocalTrainingResult(
            ticket_id=ticket_id,
            tensors={"dummy.linear": tensor},
            metadata={"sample_count": 100},
        )

    def load_applied_checkpoint(
        self,
        checkpoint_values: Any,
        parent_model: Any | None = None,
    ) -> Any:
        arr = np.asarray(checkpoint_values, dtype=np.int64)
        if arr.size != 10:
            raise ValueError("INVALID_SHAPE")
        return arr

    def evaluate(self, model: Any, test_data: Any) -> EvaluationResult:
        return EvaluationResult(
            accuracy_ppm=1_000_000,
            loss=0.01,
            metrics={"score": 100},
        )


def _dummy_descriptor(plugin_id: str = "dummy-linear-v1") -> PluginDescriptor:
    return PluginDescriptor(
        plugin_id=plugin_id,
        display_name="Dummy Linear Model",
        model_family="linear",
        task_type="synthetic_regression",
        sample_kind="vector/fp32-10",
        target_kind="scalar/fp32",
        deterministic=True,
        supports_stage_c_real_drq1=True,
    )


def test_registry_register_and_get() -> None:
    registry = ModelPluginRegistry()
    descriptor = _dummy_descriptor("dummy-linear-v1")

    registry.register(descriptor=descriptor, factory=DummyLinearPlugin)

    assert registry.has_plugin("dummy-linear-v1") is True
    assert registry.has_plugin("nonexistent") is False

    plugin = registry.get("dummy-linear-v1")
    assert isinstance(plugin, ModelPlugin)
    assert plugin.plugin_id == "dummy-linear-v1"

    retrieved_desc = registry.get_descriptor("dummy-linear-v1")
    assert retrieved_desc == descriptor


def test_registry_get_returns_fresh_instances() -> None:
    registry = ModelPluginRegistry()
    descriptor = _dummy_descriptor("dummy-linear-v1")
    registry.register(descriptor=descriptor, factory=DummyLinearPlugin)

    plugin1 = registry.get("dummy-linear-v1")
    plugin2 = registry.get("dummy-linear-v1")
    assert plugin1 is not plugin2


def test_registry_rejects_duplicate_plugin_id() -> None:
    registry = ModelPluginRegistry()
    desc = _dummy_descriptor("dummy-linear-v1")
    registry.register(descriptor=desc, factory=DummyLinearPlugin)

    with pytest.raises(PluginRegistryError, match="DUPLICATE_PLUGIN_ID: dummy-linear-v1"):
        registry.register(descriptor=desc, factory=DummyLinearPlugin)


def test_registry_rejects_unknown_plugin_id() -> None:
    registry = ModelPluginRegistry()
    with pytest.raises(PluginRegistryError, match="UNKNOWN_PLUGIN_ID: nonexistent"):
        registry.get("nonexistent")

    with pytest.raises(PluginRegistryError, match="UNKNOWN_PLUGIN_ID: nonexistent"):
        registry.get_descriptor("nonexistent")


def test_registry_rejects_mismatched_descriptor_id() -> None:
    registry = ModelPluginRegistry()
    mismatched_desc = _dummy_descriptor("different-id")

    with pytest.raises(PluginRegistryError, match="DESCRIPTOR_PLUGIN_ID_MISMATCH"):
        registry.register(descriptor=mismatched_desc, factory=DummyLinearPlugin)


def test_registry_descriptors_deterministic_order() -> None:
    registry = ModelPluginRegistry()
    ids = ["zebra-v1", "alpha-v1", "beta-v1", "gamma-v1"]
    for pid in ids:
        desc = _dummy_descriptor(pid)

        # Simple factory producing matching plugin_id
        class NamedPlugin(DummyLinearPlugin):
            def __init__(self, assigned_id: str = pid) -> None:
                self._id = assigned_id

            @property
            def plugin_id(self) -> str:
                return self._id

        registry.register(descriptor=desc, factory=NamedPlugin)

    listed = registry.list_descriptors()
    assert [d.plugin_id for d in listed] == ["alpha-v1", "beta-v1", "gamma-v1", "zebra-v1"]


def test_registry_does_not_mutate_descriptor_state() -> None:
    registry = ModelPluginRegistry()
    desc = _dummy_descriptor("dummy-linear-v1")
    registry.register(descriptor=desc, factory=DummyLinearPlugin)

    retrieved = registry.get_descriptor("dummy-linear-v1")
    assert retrieved == desc

    # PluginDescriptor is frozen and cannot be modified
    with pytest.raises(AttributeError):
        retrieved.plugin_id = "mutated"  # type: ignore[misc]


def test_default_registry_contains_mnist_centroid() -> None:
    registry = get_default_registry()
    assert registry.has_plugin("mnist-centroid-v1") is True

    desc = registry.get_descriptor("mnist-centroid-v1")
    assert desc.plugin_id == "mnist-centroid-v1"
    assert desc.display_name == "MNIST Nearest Centroid"
    assert desc.model_family == "centroid"
    assert desc.task_type == "cv_classification"
    assert desc.sample_kind == "image/grayscale-28x28"
    assert desc.target_kind == "class-id/0-9"
    assert desc.deterministic is True
    assert desc.supports_stage_c_real_drq1 is True
    assert desc.parameter_schema_id is None

    plugin = registry.get("mnist-centroid-v1")
    assert isinstance(plugin, MnistCentroidPlugin)
    assert plugin.plugin_id == "mnist-centroid-v1"
    assert plugin.total_elements == 7850


def test_default_registry_contains_eeg_bandpower_centroid() -> None:
    registry = get_default_registry()
    assert registry.has_plugin("eeg-bandpower-centroid-v1") is True

    desc = registry.get_descriptor("eeg-bandpower-centroid-v1")
    assert desc.plugin_id == "eeg-bandpower-centroid-v1"
    assert desc.display_name == "EEG Bandpower Centroid Classifier"
    assert desc.model_family == "centroid"
    assert desc.task_type == "classification"
    assert desc.sample_kind == "eeg/bandpower-4ch-4band"
    assert desc.target_kind == "class-id/0-1"
    assert desc.deterministic is True
    assert desc.supports_stage_c_real_drq1 is False
    assert desc.parameter_schema_id is None

    plugin = registry.get("eeg-bandpower-centroid-v1")
    assert isinstance(plugin, EegBandpowerCentroidPlugin)
    assert plugin.plugin_id == "eeg-bandpower-centroid-v1"
    assert plugin.total_elements == 34


def test_default_registry_contains_qlora() -> None:
    registry = get_default_registry()
    assert registry.has_plugin("qlora-tiny-adapter-v1") is True

    desc = registry.get_descriptor("qlora-tiny-adapter-v1")
    assert desc.plugin_id == "qlora-tiny-adapter-v1"
    assert desc.display_name == "QLoRA Tiny Quantized Adapter"
    assert desc.model_family == "qlora"
    assert desc.task_type == "adapter_regression"
    assert desc.sample_kind == "vector/tiny-qlora-2d"
    assert desc.target_kind == "regression/vector-2d"
    assert desc.deterministic is True
    assert desc.supports_stage_c_real_drq1 is True
    plugin = registry.get("qlora-tiny-adapter-v1")
    assert isinstance(plugin, QloraModelPlugin)
    assert plugin.plugin_id == "qlora-tiny-adapter-v1"
    assert plugin.total_elements == 8
    assert desc.parameter_schema_id == plugin.parameter_schema().fingerprint


def test_extensibility_architectural_proof_dummy_plugin() -> None:
    """Architectural Proof:

    Adding a second model plugin requires ZERO modifications to the generic Delta
    runner/spine. The generic drq1_producer, Feature 004 envelopes, and evaluation
    pipeline work purely through ModelPlugin contracts.
    """
    registry = ModelPluginRegistry()
    dummy_desc = _dummy_descriptor("dummy-linear-v1")
    registry.register(descriptor=dummy_desc, factory=DummyLinearPlugin)

    # 1. Retrieve plugin from registry
    plugin = registry.get("dummy-linear-v1")
    assert isinstance(plugin, ModelPlugin)

    # 2. Worker executes local ticket training using the plugin
    local_result = plugin.train_ticket(ticket_id="ticket-042", data=None)
    assert isinstance(local_result, LocalTrainingResult)
    assert "dummy.linear" in local_result.tensors
    tensor = local_result.tensors["dummy.linear"]
    assert tensor.shape == (10,)

    # 3. Generic Delta spine packages the local tensor into canonical DRQ1 envelopes
    candidate = NormalizedContributionCandidate(
        ticket_id="ticket-042",
        domain_id="text",
        ticket_fingerprint="sha256:" + "a" * 64,
        completion_id="sha256:" + "b" * 64,
        parent_model_id="sha256:" + "c" * 64,
        parameter_schema_id="sha256:" + "d" * 64,
        optimizer_profile_id="sha256:" + "e" * 64,
        arithmetic_profile_id="sha256:" + "f" * 64,
        effective_steps=1,
        step_budget=1,
        normalization_denominator=1,
        normalized_delta=ArtifactRef(
            content_id="sha256:" + "0" * 64,
            media_type="application/vnd.safetensors",
            schema_id="SCHEMA-SAFETENSORS-V1",
            schema_version="1.0.0",
            byte_length=100,
            locator="tensors/delta.safetensors",
        ),
        tensor_order=("dummy.linear",),
    )

    scale_table = {
        "content_id": "sha256:" + "2" * 64,
        "segments": [
            {
                "segment_id": "dummy.linear",
                "element_count": 10,
                "quantum": {"numerator": 1, "denominator": 1000},
                "zero_point": 0,
            },
        ],
    }
    shard_plan = {
        "content_id": "sha256:" + "3" * 64,
        "entries": [
            {
                "ordinal": 0,
                "segment_id": "dummy.linear",
                "segment_offset": 0,
                "element_start": 0,
                "element_count": 10,
            },
        ],
    }

    # DRQ1 producer processes the new plugin tensors without ANY model-specific code
    shard_set = produce_drq1_shards(
        candidate=candidate,
        tensors=local_result.tensors,
        scale_table=scale_table,
        shard_plan=shard_plan,
        proof_instance_id="sha256:" + "0" * 64,
        round_config_id="sha256:" + "1" * 64,
    )

    assert shard_set.total_elements == 10
    assert len(shard_set.shards) == 1
    shard = shard_set.shard_by_ordinal(0)
    assert shard.element_count == 10
    assert len(shard.envelope) > 0

    # 4. Consensus checkpoint decode & evaluate using plugin
    applied_coords = np.arange(10, dtype=np.int64)
    model = plugin.load_applied_checkpoint(applied_coords)
    evaluation = plugin.evaluate(model, test_data=None)
    assert evaluation.accuracy_ppm == 1_000_000
    assert evaluation.loss == 0.01
