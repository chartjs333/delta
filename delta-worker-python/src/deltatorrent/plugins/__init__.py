"""Generic DeltaReduce plugin contract primitives."""

from deltatorrent.plugins.contract import (
    DeltaPlugin,
    PluginContractError,
    abstain_response,
    plugin_incompatible_response,
    validate_analyze_response,
    validate_plugin_manifest,
)
from deltatorrent.plugins.workload import (
    DatasetProvider,
    ExecutionReceiptError,
    ModelPlugin,
    WorkloadCompatibilityError,
    WorkloadScopeError,
    compute_state_root,
    compute_workload_config_digest,
    run_workload,
    validate_receipt_structure,
)

__all__ = [
    "DatasetProvider",
    "DeltaPlugin",
    "ExecutionReceiptError",
    "ModelPlugin",
    "PluginContractError",
    "WorkloadCompatibilityError",
    "WorkloadScopeError",
    "abstain_response",
    "compute_state_root",
    "compute_workload_config_digest",
    "plugin_incompatible_response",
    "run_workload",
    "validate_analyze_response",
    "validate_plugin_manifest",
    "validate_receipt_structure",
]
