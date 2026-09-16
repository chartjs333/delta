"""ModelPlugin registry: Safe, static management of model plugin implementations."""

from __future__ import annotations

from collections.abc import Callable
from typing import Final

from deltatorrent.model_plugins.base import ModelPlugin, PluginDescriptor
from deltatorrent.model_plugins.eeg_bandpower import EegBandpowerCentroidPlugin
from deltatorrent.model_plugins.mnist_centroid import MnistCentroidPlugin
from deltatorrent.model_plugins.qlora import QLORA_PARAMETER_SCHEMA_ID, QloraModelPlugin


class PluginRegistryError(ValueError):
    """Stable error raised when a model plugin registry operation fails."""


class ModelPluginRegistry:
    """Registry maintaining registered ModelPlugin factories and descriptors.

    Adheres to strict safety boundaries:
    - No dynamic imports or code evaluation from UI/REST calls.
    - Explicit registration with immutable descriptors.
    - No plugin execution during descriptor listing.
    - Deterministic ordering on listing.
    - get() returns fresh ModelPlugin instances.
    """

    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], ModelPlugin]] = {}
        self._descriptors: dict[str, PluginDescriptor] = {}

    def register(
        self,
        descriptor: PluginDescriptor,
        factory: Callable[[], ModelPlugin],
    ) -> None:
        """Register a model plugin factory with its immutable descriptor."""
        plugin_id = descriptor.plugin_id
        if not plugin_id or not isinstance(plugin_id, str):
            raise PluginRegistryError("INVALID_PLUGIN_ID")
        if plugin_id in self._descriptors:
            raise PluginRegistryError(f"DUPLICATE_PLUGIN_ID: {plugin_id}")
        sample = factory()
        if not isinstance(sample, ModelPlugin):
            raise PluginRegistryError("FACTORY_NOT_MODEL_PLUGIN")
        if sample.plugin_id != plugin_id:
            raise PluginRegistryError(
                f"DESCRIPTOR_PLUGIN_ID_MISMATCH: descriptor={plugin_id} "
                f"vs factory={sample.plugin_id}"
            )
        self._descriptors[plugin_id] = descriptor
        self._factories[plugin_id] = factory

    def get(self, plugin_id: str) -> ModelPlugin:
        """Instantiate and return a fresh ModelPlugin instance by its unique plugin_id."""
        if plugin_id not in self._factories:
            raise PluginRegistryError(f"UNKNOWN_PLUGIN_ID: {plugin_id}")
        plugin = self._factories[plugin_id]()
        if plugin.plugin_id != plugin_id:
            raise PluginRegistryError(
                f"PLUGIN_INSTANCE_ID_MISMATCH: expected {plugin_id}, got {plugin.plugin_id}"
            )
        return plugin

    def get_descriptor(self, plugin_id: str) -> PluginDescriptor:
        """Retrieve the immutable PluginDescriptor for a registered plugin."""
        if plugin_id not in self._descriptors:
            raise PluginRegistryError(f"UNKNOWN_PLUGIN_ID: {plugin_id}")
        return self._descriptors[plugin_id]

    def list_descriptors(self) -> tuple[PluginDescriptor, ...]:
        """Return all registered plugin descriptors in deterministic sorted order."""
        return tuple(self._descriptors[plugin_id] for plugin_id in sorted(self._descriptors.keys()))

    def has_plugin(self, plugin_id: str) -> bool:
        """Return True if plugin_id is registered."""
        return plugin_id in self._descriptors


MNIST_CENTROID_DESCRIPTOR: Final[PluginDescriptor] = PluginDescriptor(
    plugin_id="mnist-centroid-v1",
    display_name="MNIST Nearest Centroid",
    model_family="centroid",
    task_type="cv_classification",
    sample_kind="image/grayscale-28x28",
    target_kind="class-id/0-9",
    deterministic=True,
    supports_stage_c_real_drq1=True,
    parameter_schema_id=None,
)

EEG_BANDPOWER_DESCRIPTOR: Final[PluginDescriptor] = PluginDescriptor(
    plugin_id="eeg-bandpower-centroid-v1",
    display_name="EEG Bandpower Centroid Classifier",
    model_family="centroid",
    task_type="classification",
    deterministic=True,
    supports_stage_c_real_drq1=False,
    sample_kind="eeg/bandpower-4ch-4band",
    target_kind="class-id/0-1",
    parameter_schema_id=None,
)

QLORA_DESCRIPTOR: Final[PluginDescriptor] = PluginDescriptor(
    plugin_id="qlora-tiny-adapter-v1",
    display_name="QLoRA Tiny Quantized Adapter",
    model_family="qlora",
    task_type="adapter_regression",
    sample_kind="vector/tiny-qlora-2d",
    target_kind="regression/vector-2d",
    deterministic=True,
    supports_stage_c_real_drq1=True,
    parameter_schema_id=QLORA_PARAMETER_SCHEMA_ID,
)


def build_default_registry() -> ModelPluginRegistry:
    """Construct a new ModelPluginRegistry pre-populated with baseline plugins."""
    registry = ModelPluginRegistry()
    registry.register(
        descriptor=MNIST_CENTROID_DESCRIPTOR,
        factory=MnistCentroidPlugin,
    )
    registry.register(
        descriptor=EEG_BANDPOWER_DESCRIPTOR,
        factory=EegBandpowerCentroidPlugin,
    )
    registry.register(
        descriptor=QLORA_DESCRIPTOR,
        factory=QloraModelPlugin,
    )
    return registry


_DEFAULT_REGISTRY: Final[ModelPluginRegistry] = build_default_registry()


def get_default_registry() -> ModelPluginRegistry:
    """Return the shared global default ModelPluginRegistry instance."""
    return _DEFAULT_REGISTRY
