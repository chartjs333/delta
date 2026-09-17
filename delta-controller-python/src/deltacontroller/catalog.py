"""Frozen catalog, capability matrix, and operation scope validation."""

from __future__ import annotations

from typing import Any

from deltacontroller.errors import (
    CatalogRefMismatchError,
    OperationScopeUnsupportedError,
    UnknownDatasetIdError,
    UnknownPluginIdError,
)

FROZEN_CATALOG_REF = "670b58f6458fe84620f4f9f46401f855d04ae05d"

DEFAULT_KNOWN_PLUGINS = frozenset(
    {
        "tabular-10gene-phenotype-v1",
    }
)

DEFAULT_KNOWN_DATASETS = frozenset(
    {
        "synthetic-10gene-cohort-v1",
    }
)

ALLOWED_CAPABILITY_MATRIX: dict[str, frozenset[str]] = {
    "TRAIN_TICKET": frozenset({"PLUGIN_BOUNDARY"}),
    "EVALUATE_CHECKPOINT": frozenset({"PLUGIN_BOUNDARY", "MODEL_DATASET_BINDING_ONLY"}),
    "MATERIALIZE_DATASET": frozenset({"PLUGIN_BOUNDARY", "MODEL_DATASET_BINDING_ONLY"}),
}


class CatalogValidator:
    """Validates workloads and operations against the frozen catalog and capability matrix."""

    def __init__(
        self,
        catalog_backend_ref: str = FROZEN_CATALOG_REF,
        known_plugins: frozenset[str] | set[str] | None = None,
        known_datasets: frozenset[str] | set[str] | None = None,
        capability_matrix: dict[str, frozenset[str]] | None = None,
    ) -> None:
        self.catalog_backend_ref = catalog_backend_ref
        if known_plugins is not None:
            self.known_plugins = frozenset(known_plugins)
        else:
            self.known_plugins = DEFAULT_KNOWN_PLUGINS
        if known_datasets is not None:
            self.known_datasets = frozenset(known_datasets)
        else:
            self.known_datasets = DEFAULT_KNOWN_DATASETS
        self.capability_matrix = capability_matrix or ALLOWED_CAPABILITY_MATRIX

    def validate(self, workload: dict[str, Any], operation: str) -> None:
        """Validate catalog backend ref, plugin ID, dataset ID, and operation/scope capability."""
        # 1. Catalog backend ref parity
        declared_ref = workload.get("catalog_backend_ref")
        if declared_ref != self.catalog_backend_ref:
            msg = (
                f"Workload catalog_backend_ref '{declared_ref}' does not match "
                f"frozen catalog ref '{self.catalog_backend_ref}'"
            )
            raise CatalogRefMismatchError(
                msg,
                details={"declared_ref": declared_ref, "expected_ref": self.catalog_backend_ref},
            )

        # 2. Known model plugin ID
        model_plugin_id = workload.get("model_plugin_id")
        if model_plugin_id not in self.known_plugins:
            raise UnknownPluginIdError(
                f"Model plugin ID '{model_plugin_id}' not found in frozen catalog",
                details={
                    "model_plugin_id": model_plugin_id,
                    "known_plugins": sorted(self.known_plugins),
                },
            )

        # 3. Known dataset ID
        dataset_id = workload.get("dataset_id")
        if dataset_id not in self.known_datasets:
            raise UnknownDatasetIdError(
                f"Dataset ID '{dataset_id}' not found in frozen catalog",
                details={"dataset_id": dataset_id, "known_datasets": sorted(self.known_datasets)},
            )

        # 4. Operation capability matrix
        if operation not in self.capability_matrix:
            raise OperationScopeUnsupportedError(
                f"Operation '{operation}' is not supported by capability matrix",
                details={
                    "operation": operation,
                    "supported_operations": sorted(self.capability_matrix.keys()),
                },
            )

        requested_scope = workload.get("requested_scope")
        allowed_scopes = self.capability_matrix[operation]
        if requested_scope not in allowed_scopes:
            msg = (
                f"Operation '{operation}' does not support scope '{requested_scope}'. "
                f"Allowed scopes: {sorted(allowed_scopes)}"
            )
            raise OperationScopeUnsupportedError(
                msg,
                details={
                    "operation": operation,
                    "requested_scope": requested_scope,
                    "allowed_scopes": sorted(allowed_scopes),
                },
            )
