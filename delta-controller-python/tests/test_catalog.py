"""T013: Frozen catalog, ref integrity, and capability matrix validation."""

from __future__ import annotations

import pytest
from deltacontroller.catalog import FROZEN_CATALOG_REF, CatalogValidator
from deltacontroller.errors import (
    CatalogRefMismatchError,
    OperationScopeUnsupportedError,
    UnknownDatasetIdError,
    UnknownPluginIdError,
)


def test_valid_workload_passes_catalog_validation() -> None:
    validator = CatalogValidator()
    workload = {
        "catalog_backend_ref": FROZEN_CATALOG_REF,
        "model_plugin_id": "tabular-10gene-phenotype-v1",
        "dataset_id": "synthetic-10gene-cohort-v1",
        "requested_scope": "PLUGIN_BOUNDARY",
    }
    validator.validate(workload, "TRAIN_TICKET")  # Should not raise


def test_catalog_ref_mismatch_rejected() -> None:
    validator = CatalogValidator()
    workload = {
        "catalog_backend_ref": "0000000000000000000000000000000000000000",
        "model_plugin_id": "tabular-10gene-phenotype-v1",
        "dataset_id": "synthetic-10gene-cohort-v1",
        "requested_scope": "PLUGIN_BOUNDARY",
    }
    with pytest.raises(CatalogRefMismatchError) as exc_info:
        validator.validate(workload, "TRAIN_TICKET")
    assert exc_info.value.code == "ERR_CATALOG_REF_MISMATCH"


def test_unknown_plugin_id_rejected() -> None:
    validator = CatalogValidator()
    workload = {
        "catalog_backend_ref": FROZEN_CATALOG_REF,
        "model_plugin_id": "malicious-arbitrary-plugin",
        "dataset_id": "synthetic-10gene-cohort-v1",
        "requested_scope": "PLUGIN_BOUNDARY",
    }
    with pytest.raises(UnknownPluginIdError) as exc_info:
        validator.validate(workload, "TRAIN_TICKET")
    assert exc_info.value.code == "ERR_UNKNOWN_PLUGIN_ID"


def test_unknown_dataset_id_rejected() -> None:
    validator = CatalogValidator()
    workload = {
        "catalog_backend_ref": FROZEN_CATALOG_REF,
        "model_plugin_id": "tabular-10gene-phenotype-v1",
        "dataset_id": "unregistered-private-dataset",
        "requested_scope": "PLUGIN_BOUNDARY",
    }
    with pytest.raises(UnknownDatasetIdError) as exc_info:
        validator.validate(workload, "TRAIN_TICKET")
    assert exc_info.value.code == "ERR_UNKNOWN_DATASET_ID"


def test_train_ticket_wrong_scope_rejected() -> None:
    validator = CatalogValidator()
    # TRAIN_TICKET is restricted strictly to PLUGIN_BOUNDARY
    workload = {
        "catalog_backend_ref": FROZEN_CATALOG_REF,
        "model_plugin_id": "tabular-10gene-phenotype-v1",
        "dataset_id": "synthetic-10gene-cohort-v1",
        "requested_scope": "MODEL_DATASET_BINDING_ONLY",
    }
    with pytest.raises(OperationScopeUnsupportedError) as exc_info:
        validator.validate(workload, "TRAIN_TICKET")
    assert exc_info.value.code == "ERR_OPERATION_SCOPE_UNSUPPORTED"
