"""Unit tests for ModelDatasetBinding and contract-validated runner execution."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
from deltatorrent.data.base import (
    ContractCompatibilityError,
    DataPartition,
    DatasetDescriptor,
)
from deltatorrent.data.mnist import (
    DEMO_SEED,
    MNIST_DESCRIPTOR,
    MnistDatasetProvider,
)
from deltatorrent.data.registry import (
    DatasetRegistry,
    DatasetRegistryError,
)
from deltatorrent.domain.parameters import (
    FrozenOmissionPolicy,
    LogicalDType,
    ParameterSchema,
    ParameterSpec,
)
from deltatorrent.model_plugins import (
    DomainBindingSpec,
    EvaluationResult,
    LocalTrainingResult,
    ModelDatasetBinding,
    ModelPlugin,
    ModelPluginRegistry,
    ModelPluginRunner,
    ModelPluginRunnerError,
    PluginDescriptor,
    PluginRegistryError,
    bind_model_and_dataset,
    bind_model_dataset_domains,
    validate_model_dataset_capability,
)


def _synthetic_mnist_data() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Generate minimal synthetic MNIST arrays for test execution."""
    rng = np.random.Generator(np.random.PCG64(DEMO_SEED))
    train_images = rng.integers(0, 256, size=(40, 28, 28), dtype=np.uint8)
    train_labels = np.tile(np.arange(10, dtype=np.uint8), 4)

    test_images = rng.integers(0, 256, size=(20, 28, 28), dtype=np.uint8)
    test_labels = np.tile(np.arange(10, dtype=np.uint8), 2)
    return train_images, train_labels, test_images, test_labels


class DummyIncompatibleDatasetProvider:
    def __init__(
        self,
        sample_kind: str,
        target_kind: str,
        dataset_id: str = "incompatible-v1",
    ) -> None:
        self._sample_kind = sample_kind
        self._target_kind = target_kind
        self._dataset_id = dataset_id

    @property
    def dataset_id(self) -> str:
        return self._dataset_id

    def descriptor(self) -> DatasetDescriptor:
        return DatasetDescriptor(
            dataset_id=self._dataset_id,
            display_name="Incompatible Dataset",
            sample_kind=self._sample_kind,
            target_kind=self._target_kind,
            deterministic=True,
            supports_offline_cache=False,
        )

    def materialize(self, cache_dir: Any, *, allow_download: bool = True) -> dict[str, object]:
        return {
            "allow_download": allow_download,
            "cache_dir": str(cache_dir),
            "source_id": "sha256:" + "2" * 64,
        }

    def training_partition(self, partition_id: str) -> DataPartition:
        return DataPartition(
            partition_id=partition_id,
            samples=np.zeros(10),
            targets=np.zeros(10),
            metadata={},
        )

    def evaluation_data(self) -> tuple[np.ndarray, np.ndarray]:
        return np.zeros(10), np.zeros(10)


def test_bind_model_and_dataset_mnist_success() -> None:
    binding = bind_model_and_dataset(
        model_plugin_id="mnist-centroid-v1",
        dataset_id="mnist-v1",
    )
    assert isinstance(binding, ModelDatasetBinding)
    assert isinstance(binding.model_plugin, ModelPlugin)
    assert binding.model_plugin.plugin_id == "mnist-centroid-v1"
    assert binding.model_descriptor.plugin_id == "mnist-centroid-v1"
    assert binding.model_descriptor.sample_kind == "image/grayscale-28x28"
    assert binding.model_descriptor.target_kind == "class-id/0-9"

    assert isinstance(binding.dataset_provider, MnistDatasetProvider)
    assert binding.dataset_descriptor.dataset_id == "mnist-v1"
    assert binding.dataset_descriptor.sample_kind == "image/grayscale-28x28"
    assert binding.dataset_descriptor.target_kind == "class-id/0-9"


def test_bind_model_and_dataset_incompatible_sample_kind_fail_closed() -> None:
    dataset_registry = DatasetRegistry()
    incompatible_provider = DummyIncompatibleDatasetProvider(
        sample_kind="text/token-sequence",
        target_kind="class-id/0-9",
        dataset_id="text-classification-v1",
    )
    dataset_registry.register(
        descriptor=incompatible_provider.descriptor(),
        factory=lambda: DummyIncompatibleDatasetProvider(
            sample_kind="text/token-sequence",
            target_kind="class-id/0-9",
            dataset_id="text-classification-v1",
        ),
    )

    with pytest.raises(ContractCompatibilityError, match="SAMPLE_KIND_MISMATCH"):
        bind_model_and_dataset(
            model_plugin_id="mnist-centroid-v1",
            dataset_id="text-classification-v1",
            dataset_registry=dataset_registry,
        )


def test_bind_model_and_dataset_incompatible_target_kind_fail_closed() -> None:
    dataset_registry = DatasetRegistry()
    incompatible_provider = DummyIncompatibleDatasetProvider(
        sample_kind="image/grayscale-28x28",
        target_kind="bounding-box/xywh",
        dataset_id="image-detection-v1",
    )
    dataset_registry.register(
        descriptor=incompatible_provider.descriptor(),
        factory=lambda: DummyIncompatibleDatasetProvider(
            sample_kind="image/grayscale-28x28",
            target_kind="bounding-box/xywh",
            dataset_id="image-detection-v1",
        ),
    )

    with pytest.raises(ContractCompatibilityError, match="TARGET_KIND_MISMATCH"):
        bind_model_and_dataset(
            model_plugin_id="mnist-centroid-v1",
            dataset_id="image-detection-v1",
            dataset_registry=dataset_registry,
        )


def test_bind_model_and_dataset_checks_descriptors_before_provider_get() -> None:
    calls = 0
    dataset_registry = DatasetRegistry()
    descriptor = DummyIncompatibleDatasetProvider(
        dataset_id="text-classification-v1",
        sample_kind="text/token-sequence",
        target_kind="class-id/0-9",
    ).descriptor()

    def factory() -> DummyIncompatibleDatasetProvider:
        nonlocal calls
        calls += 1
        return DummyIncompatibleDatasetProvider(
            sample_kind="text/token-sequence",
            target_kind="class-id/0-9",
            dataset_id="text-classification-v1",
        )

    dataset_registry.register(descriptor=descriptor, factory=factory)
    assert calls == 1  # registration validation only

    with pytest.raises(ContractCompatibilityError, match="SAMPLE_KIND_MISMATCH"):
        bind_model_and_dataset(
            model_plugin_id="mnist-centroid-v1",
            dataset_id="text-classification-v1",
            dataset_registry=dataset_registry,
        )

    assert calls == 1


def test_bind_model_and_dataset_unknown_model_rejected() -> None:
    with pytest.raises(PluginRegistryError, match="UNKNOWN_PLUGIN_ID: unknown-model-v1"):
        bind_model_and_dataset(
            model_plugin_id="unknown-model-v1",
            dataset_id="mnist-v1",
        )


def test_bind_model_and_dataset_unknown_dataset_rejected() -> None:
    with pytest.raises(DatasetRegistryError, match="UNKNOWN_DATASET_ID: unknown-dataset-v1"):
        bind_model_and_dataset(
            model_plugin_id="mnist-centroid-v1",
            dataset_id="unknown-dataset-v1",
        )


def test_model_dataset_binding_workflow_execution() -> None:
    train_images, train_labels, test_images, test_labels = _synthetic_mnist_data()
    provider = MnistDatasetProvider(
        train_images=train_images,
        train_labels=train_labels,
        test_images=test_images,
        test_labels=test_labels,
    )

    custom_dataset_registry = DatasetRegistry()
    custom_dataset_registry.register(
        descriptor=provider.descriptor(),
        factory=lambda: MnistDatasetProvider(
            train_images=train_images,
            train_labels=train_labels,
            test_images=test_images,
            test_labels=test_labels,
        ),
    )

    binding = bind_model_and_dataset(
        model_plugin_id="mnist-centroid-v1",
        dataset_id="mnist-v1",
        dataset_registry=custom_dataset_registry,
    )

    # 1. Train partition for worker-01 (digits 0, 1, 2)
    local_result = binding.train_ticket(
        ticket_id="ticket-001",
        partition_id="demo-mnist-worker-01",
    )
    assert isinstance(local_result, LocalTrainingResult)
    assert local_result.ticket_id == "ticket-001"
    assert "mnist.linear" in local_result.tensors
    tensor = local_result.tensors["mnist.linear"]
    assert tensor.shape == (7850,)
    assert tensor.dtype == np.float32

    # Presence flags for digits 0, 1, 2 should be active (1.0)
    presence = tensor[7840:]
    assert presence[0] == 1.0
    assert presence[1] == 1.0
    assert presence[2] == 1.0

    # 2. Evaluate applied model
    # Construct an applied checkpoint vector
    checkpoint_vector = tensor.astype(np.int64)
    evaluation = binding.evaluate_checkpoint(checkpoint_vector)
    assert isinstance(evaluation, EvaluationResult)
    assert evaluation.accuracy_ppm >= 0
    assert evaluation.metrics["total"] == 20


def test_runner_mnist_through_registry() -> None:
    train_images, train_labels, test_images, test_labels = _synthetic_mnist_data()
    dataset_registry = DatasetRegistry()
    dataset_registry.register(
        descriptor=MNIST_DESCRIPTOR,
        factory=lambda: MnistDatasetProvider(
            train_images=train_images,
            train_labels=train_labels,
            test_images=test_images,
            test_labels=test_labels,
        ),
    )
    runner = ModelPluginRunner(
        plugin_id="mnist-centroid-v1",
        dataset_id="mnist-v1",
        dataset_registry=dataset_registry,
    )
    assert isinstance(runner.model_plugin, ModelPlugin)
    assert runner.model_descriptor.plugin_id == "mnist-centroid-v1"
    assert runner.dataset_descriptor.dataset_id == "mnist-v1"

    meta = runner.materialize_dataset()
    assert meta["type_name"] == "DELTAREDUCE_LOCAL_DEMO_MNIST_IN_MEMORY_SOURCE"

    res = runner.train_ticket(
        ticket_id="ticket-runner-mnist-01",
        partition_id="demo-mnist-worker-01",
    )
    assert isinstance(res, LocalTrainingResult)
    assert res.ticket_id == "ticket-runner-mnist-01"
    assert "mnist.linear" in res.tensors
    assert res.tensors["mnist.linear"].shape == (7850,)

    checkpoint = res.tensors["mnist.linear"].astype(np.int64)
    eval_res = runner.evaluate_checkpoint(checkpoint)
    assert isinstance(eval_res, EvaluationResult)
    assert eval_res.accuracy_ppm >= 0


def test_runner_qlora_through_registry() -> None:
    runner = ModelPluginRunner(
        plugin_id="qlora-tiny-adapter-v1",
        dataset_id="tiny-qlora-regression-v1",
    )
    assert isinstance(runner.model_plugin, ModelPlugin)
    assert runner.model_descriptor.plugin_id == "qlora-tiny-adapter-v1"
    assert runner.dataset_descriptor.dataset_id == "tiny-qlora-regression-v1"

    meta = runner.materialize_dataset()
    assert meta["status"] == "materialized"
    assert meta["dataset_id"] == "tiny-qlora-regression-v1"

    res = runner.train_ticket(
        ticket_id="ticket-runner-qlora-01",
        partition_id="demo-qlora-worker-01",
    )
    assert isinstance(res, LocalTrainingResult)
    assert res.ticket_id == "ticket-runner-qlora-01"
    assert "qlora.adapter.flat" in res.tensors
    assert res.tensors["qlora.adapter.flat"].shape == (8,)
    assert res.tensors["qlora.adapter.flat"].dtype == np.float32

    eval_res = runner.evaluate_checkpoint((0,) * 8)
    assert isinstance(eval_res, EvaluationResult)
    assert eval_res.loss is not None
    assert eval_res.metrics["evaluation_dataset_id"] == "tiny-qlora-regression-v1"


def test_runner_eeg_binding_smoke_through_registry() -> None:
    runner = ModelPluginRunner(
        plugin_id="eeg-bandpower-centroid-v1",
        dataset_id="eeg-synthetic-bci-v1",
    )
    assert isinstance(runner.model_plugin, ModelPlugin)
    assert runner.model_descriptor.plugin_id == "eeg-bandpower-centroid-v1"
    assert runner.dataset_descriptor.dataset_id == "eeg-synthetic-bci-v1"

    meta = runner.materialize_dataset()
    assert meta["status"] == "materialized"

    res = runner.train_ticket(
        ticket_id="ticket-runner-eeg-01",
        partition_id="demo-eeg-worker-01",
    )
    assert isinstance(res, LocalTrainingResult)
    assert res.ticket_id == "ticket-runner-eeg-01"
    assert "eeg.centroid" in res.tensors
    assert res.tensors["eeg.centroid"].shape == (34,)

    # Ticket context provenance validation
    ticket_context = res.metadata["data_partition_metadata"]["ticket_context"]
    assert isinstance(ticket_context, list)
    assert len(ticket_context) > 0
    assert ticket_context[0]["session_id"].startswith("obs-demo-eeg-")
    assert ticket_context[0]["data_window_id"].startswith("eegwin-demo-")
    assert ticket_context[0]["intervention_event_id"].startswith("evt-demo-eeg-")
    assert ticket_context[0]["binding_assertion_id"].startswith("sha256:")
    assert ticket_context[0]["raw_data_hash"].startswith("sha256:")


def test_runner_fresh_plugin_and_provider_instances() -> None:
    r1 = ModelPluginRunner(plugin_id="mnist-centroid-v1", dataset_id="mnist-v1")
    r2 = ModelPluginRunner(plugin_id="mnist-centroid-v1", dataset_id="mnist-v1")
    assert r1.model_plugin is not r2.model_plugin
    assert r1.dataset_provider is not r2.dataset_provider
    assert r1.model_descriptor == r2.model_descriptor
    assert r1.dataset_descriptor == r2.dataset_descriptor


def test_runner_rejection_fail_closed() -> None:
    # Unknown plugin ID
    with pytest.raises(PluginRegistryError, match="UNKNOWN_PLUGIN_ID"):
        ModelPluginRunner(plugin_id="non-existent-plugin", dataset_id="mnist-v1")

    # Unknown dataset ID
    with pytest.raises(DatasetRegistryError, match="UNKNOWN_DATASET_ID"):
        ModelPluginRunner(plugin_id="mnist-centroid-v1", dataset_id="non-existent-dataset")

    # Empty plugin ID
    with pytest.raises(ModelPluginRunnerError, match="INVALID_PLUGIN_ID"):
        ModelPluginRunner(plugin_id="", dataset_id="mnist-v1")

    # Empty dataset ID
    with pytest.raises(ModelPluginRunnerError, match="INVALID_DATASET_ID"):
        ModelPluginRunner(plugin_id="mnist-centroid-v1", dataset_id="")

    # Incompatible sample_kind: MNIST model with QLoRA dataset
    with pytest.raises(ContractCompatibilityError, match="SAMPLE_KIND_MISMATCH"):
        ModelPluginRunner(
            plugin_id="mnist-centroid-v1",
            dataset_id="tiny-qlora-regression-v1",
        )

    # Incompatible sample_kind: QLoRA model with EEG dataset
    with pytest.raises(ContractCompatibilityError, match="SAMPLE_KIND_MISMATCH"):
        ModelPluginRunner(
            plugin_id="qlora-tiny-adapter-v1",
            dataset_id="eeg-synthetic-bci-v1",
        )


class DummyExtensibleModelPlugin(ModelPlugin):
    """Architectural proof: generic runner executes new plugins without runner modifications."""

    @property
    def plugin_id(self) -> str:
        return "dummy-extensible-v1"

    def parameter_schema(self) -> ParameterSchema:
        return ParameterSchema(
            parameters=(
                ParameterSpec(
                    name="dummy.param",
                    shape=(4,),
                    logical_dtype=LogicalDType.FLOAT32,
                    trainable=True,
                ),
            ),
            tied_aliases={},
            frozen_omission_policy=FrozenOmissionPolicy.INCLUDE_ALL,
        )

    @property
    def tensor_order(self) -> tuple[str, ...]:
        return ("dummy.param",)

    @property
    def total_elements(self) -> int:
        return 4

    def create_model(self, state: Any | None = None) -> Any:
        return np.zeros(4, dtype=np.float32)

    def train_ticket(
        self,
        *,
        ticket_id: str,
        data: Any,
        parent_model: Any | None = None,
        **kwargs: Any,
    ) -> LocalTrainingResult:
        return LocalTrainingResult(
            ticket_id=ticket_id,
            tensors={"dummy.param": np.ones(4, dtype=np.float32)},
            metadata={"status": "COMPLETE", "step": 1},
        )

    def load_applied_checkpoint(
        self,
        checkpoint_values: Any,
        parent_model: Any | None = None,
    ) -> Any:
        return np.asarray(checkpoint_values, dtype=np.float32)

    def evaluate(self, model: Any, test_data: Any = None) -> EvaluationResult:
        return EvaluationResult(
            accuracy_ppm=999_000,
            loss=0.001,
            metrics={"extensible_accuracy": 0.999},
        )


class DummyExtensibleDatasetProvider:
    """Architectural proof: generic runner executes new datasets without runner modifications."""

    @property
    def dataset_id(self) -> str:
        return "dummy-extensible-dataset-v1"

    def descriptor(self) -> DatasetDescriptor:
        return DatasetDescriptor(
            dataset_id="dummy-extensible-dataset-v1",
            display_name="Extensible Dummy Dataset",
            sample_kind="stream/dummy-data",
            target_kind="target/dummy-scalar",
            deterministic=True,
            supports_offline_cache=False,
        )

    def materialize(
        self,
        cache_dir: Any = None,
        *,
        allow_download: bool = True,
    ) -> dict[str, object]:
        return {"status": "materialized", "dataset_id": "dummy-extensible-dataset-v1"}

    def training_partition(self, partition_id: str) -> DataPartition:
        return DataPartition(
            partition_id=partition_id,
            samples=np.zeros((5, 2)),
            targets=np.zeros(5),
            metadata={"source": "dummy"},
        )

    def evaluation_data(self) -> tuple[np.ndarray, np.ndarray]:
        return np.zeros((5, 2)), np.zeros(5)


def test_runner_extensibility_with_dummy_plugin_and_provider() -> None:
    # Register dummy plugin and dataset into isolated test registries
    test_model_registry = ModelPluginRegistry()
    dummy_descriptor = PluginDescriptor(
        plugin_id="dummy-extensible-v1",
        display_name="Extensible Dummy Plugin",
        model_family="dummy",
        task_type="dummy_task",
        sample_kind="stream/dummy-data",
        target_kind="target/dummy-scalar",
        deterministic=True,
        supports_stage_c_real_drq1=False,
        parameter_schema_id="sha256:" + "f" * 64,
    )
    test_model_registry.register(dummy_descriptor, DummyExtensibleModelPlugin)

    test_dataset_registry = DatasetRegistry()
    test_dataset_registry.register(
        descriptor=DummyExtensibleDatasetProvider().descriptor(),
        factory=DummyExtensibleDatasetProvider,
    )

    # Instantiate runner with completely new plugin/provider without runner edits
    runner = ModelPluginRunner(
        plugin_id="dummy-extensible-v1",
        dataset_id="dummy-extensible-dataset-v1",
        model_registry=test_model_registry,
        dataset_registry=test_dataset_registry,
    )

    meta = runner.materialize_dataset()
    assert meta["status"] == "materialized"

    train_res = runner.train_ticket(
        ticket_id="ticket-ext-01",
        partition_id="part-01",
    )
    assert train_res.ticket_id == "ticket-ext-01"
    assert "dummy.param" in train_res.tensors
    assert np.array_equal(train_res.tensors["dummy.param"], np.ones(4, dtype=np.float32))

    eval_res = runner.evaluate(None)
    assert eval_res.accuracy_ppm == 999_000

    ckpt_res = runner.evaluate_checkpoint((1, 2, 3, 4))
    assert ckpt_res.accuracy_ppm == 999_000


def test_runner_corrupt_ticket_context_fail_closed() -> None:
    # Provider returning partition with mismatched ticket_context length
    class CorruptContextDatasetProvider:
        @property
        def dataset_id(self) -> str:
            return "corrupt-context-dataset-v1"

        def descriptor(self) -> DatasetDescriptor:
            return DatasetDescriptor(
                dataset_id="corrupt-context-dataset-v1",
                display_name="Corrupt Context Dataset",
                sample_kind="stream/dummy-data",
                target_kind="target/dummy-scalar",
                deterministic=True,
                supports_offline_cache=False,
            )

        def materialize(
            self, cache_dir: Any = None, *, allow_download: bool = True
        ) -> dict[str, object]:
            return {"status": "materialized"}

        def training_partition(self, partition_id: str) -> DataPartition:
            # 5 samples, but only 2 context entries (cardinality mismatch)
            return DataPartition(
                partition_id=partition_id,
                samples=np.zeros((5, 2)),
                targets=np.zeros(5),
                metadata={
                    "ticket_context": [
                        {
                            "session_id": "s1",
                            "data_window_id": "w1",
                            "intervention_event_id": "e1",
                        },
                        {
                            "session_id": "s2",
                            "data_window_id": "w2",
                            "intervention_event_id": "e2",
                        },
                    ]
                },
            )

        def evaluation_data(self) -> tuple[np.ndarray, np.ndarray]:
            return np.zeros((5, 2)), np.zeros(5)

    test_model_registry = ModelPluginRegistry()
    dummy_descriptor = PluginDescriptor(
        plugin_id="dummy-extensible-v1",
        display_name="Extensible Dummy Plugin",
        model_family="dummy",
        task_type="dummy_task",
        sample_kind="stream/dummy-data",
        target_kind="target/dummy-scalar",
        deterministic=True,
        supports_stage_c_real_drq1=False,
        parameter_schema_id="sha256:" + "f" * 64,
    )
    test_model_registry.register(dummy_descriptor, DummyExtensibleModelPlugin)

    test_dataset_registry = DatasetRegistry()
    test_dataset_registry.register(
        descriptor=CorruptContextDatasetProvider().descriptor(),
        factory=CorruptContextDatasetProvider,
    )

    runner = ModelPluginRunner(
        plugin_id="dummy-extensible-v1",
        dataset_id="corrupt-context-dataset-v1",
        model_registry=test_model_registry,
        dataset_registry=test_dataset_registry,
    )

    with pytest.raises(ModelPluginRunnerError, match="TICKET_CONTEXT_COUNT_MISMATCH"):
        runner.train_ticket(ticket_id="t1", partition_id="p1")


def test_runner_capability_validation_fail_closed() -> None:
    # Dummy plugin has supports_stage_c_real_drq1 = False
    test_model_registry = ModelPluginRegistry()
    dummy_descriptor = PluginDescriptor(
        plugin_id="dummy-extensible-v1",
        display_name="Extensible Dummy Plugin",
        model_family="dummy",
        task_type="dummy_task",
        sample_kind="stream/dummy-data",
        target_kind="target/dummy-scalar",
        deterministic=True,
        supports_stage_c_real_drq1=False,
        parameter_schema_id="sha256:" + "f" * 64,
    )
    test_model_registry.register(dummy_descriptor, DummyExtensibleModelPlugin)

    test_dataset_registry = DatasetRegistry()
    test_dataset_registry.register(
        descriptor=DummyExtensibleDatasetProvider().descriptor(),
        factory=DummyExtensibleDatasetProvider,
    )

    # Requesting STAGE_C_REAL_DRQ1 on dummy plugin must fail closed
    spec = DomainBindingSpec(
        domain_id="dummy-domain",
        model_plugin_id="dummy-extensible-v1",
        dataset_id="dummy-extensible-dataset-v1",
        role="PRIMARY_DELTA_EXECUTION",
        execution_scope="STAGE_C_REAL_DRQ1",
    )
    with pytest.raises(ModelPluginRunnerError, match="CAPABILITY_MISMATCH"):
        bind_model_dataset_domains(
            (spec,),
            model_registry=test_model_registry,
            dataset_registry=test_dataset_registry,
        )


def test_descriptor_scope_validation_helper_is_authoritative() -> None:
    mnist_model = PluginDescriptor(
        plugin_id="mnist-capable-v1",
        display_name="MNIST Capable",
        model_family="centroid",
        task_type="classification",
        sample_kind="image/grayscale-28x28",
        target_kind="class-id/0-9",
        deterministic=True,
        supports_stage_c_real_drq1=True,
    )
    mnist_dataset = MNIST_DESCRIPTOR
    validate_model_dataset_capability(
        model_descriptor=mnist_model,
        dataset_descriptor=mnist_dataset,
        requested_scope="STAGE_C_REAL_DRQ1",
    )

    eeg_model = PluginDescriptor(
        plugin_id="eeg-observation-v1",
        display_name="EEG Observation",
        model_family="centroid",
        task_type="classification",
        sample_kind="eeg/bandpower-4ch-4band",
        target_kind="class-id/0-1",
        deterministic=True,
        supports_stage_c_real_drq1=False,
    )
    eeg_dataset = DatasetDescriptor(
        dataset_id="eeg-v1",
        display_name="EEG",
        sample_kind="eeg/bandpower-4ch-4band",
        target_kind="class-id/0-1",
        deterministic=True,
        supports_offline_cache=False,
    )
    with pytest.raises(ModelPluginRunnerError, match="CAPABILITY_MISMATCH"):
        validate_model_dataset_capability(
            model_descriptor=eeg_model,
            dataset_descriptor=eeg_dataset,
            requested_scope="STAGE_C_REAL_DRQ1",
        )

    with pytest.raises(ContractCompatibilityError, match="SAMPLE_KIND_MISMATCH"):
        validate_model_dataset_capability(
            model_descriptor=mnist_model,
            dataset_descriptor=eeg_dataset,
            requested_scope="PLUGIN_BOUNDARY",
        )

    with pytest.raises(ModelPluginRunnerError, match="INVALID_EXECUTION_SCOPE"):
        validate_model_dataset_capability(
            model_descriptor=mnist_model,
            dataset_descriptor=mnist_dataset,
            requested_scope="CUSTOM_SCOPE",
        )


def test_single_runner_execution_scope_and_capability_checks() -> None:
    # 1. Default execution_scope is PLUGIN_BOUNDARY
    runner_mnist = ModelPluginRunner(
        plugin_id="mnist-centroid-v1",
        dataset_id="mnist-v1",
    )
    assert runner_mnist.execution_scope == "PLUGIN_BOUNDARY"

    # 2. Explicit STAGE_C_REAL_DRQ1 succeeds for Stage C capable plugins (MNIST & QLoRA)
    runner_mnist_stagec = ModelPluginRunner(
        plugin_id="mnist-centroid-v1",
        dataset_id="mnist-v1",
        execution_scope="STAGE_C_REAL_DRQ1",
    )
    assert runner_mnist_stagec.execution_scope == "STAGE_C_REAL_DRQ1"

    runner_qlora_stagec = ModelPluginRunner(
        plugin_id="qlora-tiny-adapter-v1",
        dataset_id="tiny-qlora-regression-v1",
        execution_scope="STAGE_C_REAL_DRQ1",
    )
    assert runner_qlora_stagec.execution_scope == "STAGE_C_REAL_DRQ1"

    # 3. Explicit MODEL_DATASET_BINDING_ONLY succeeds for EEG
    runner_eeg_binding = ModelPluginRunner(
        plugin_id="eeg-bandpower-centroid-v1",
        dataset_id="eeg-synthetic-bci-v1",
        execution_scope="MODEL_DATASET_BINDING_ONLY",
    )
    assert runner_eeg_binding.execution_scope == "MODEL_DATASET_BINDING_ONLY"

    # 4. Fail-closed: EEG does NOT support STAGE_C_REAL_DRQ1
    with pytest.raises(ModelPluginRunnerError, match="CAPABILITY_MISMATCH"):
        ModelPluginRunner(
            plugin_id="eeg-bandpower-centroid-v1",
            dataset_id="eeg-synthetic-bci-v1",
            execution_scope="STAGE_C_REAL_DRQ1",
        )

    # 5. Fail-closed: Invalid execution_scope string
    with pytest.raises(ModelPluginRunnerError, match="INVALID_EXECUTION_SCOPE"):
        ModelPluginRunner(
            plugin_id="mnist-centroid-v1",
            dataset_id="mnist-v1",
            execution_scope="UNSUPPORTED_CUSTOM_SCOPE",
        )
