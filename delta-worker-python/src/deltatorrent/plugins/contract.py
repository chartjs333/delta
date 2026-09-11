"""Runtime-neutral plugin contract for domain-specific DeltaReduce extensions."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any, Protocol, runtime_checkable

SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
GIT_COMMIT_RE = re.compile(r"^(?:[a-f0-9]{40}|[a-f0-9]{64})$")


class PluginContractError(ValueError):
    """Raised when a plugin manifest or response violates the generic contract."""


@runtime_checkable
class DeltaPlugin(Protocol):
    """Small structural API implemented by external domain plugins."""

    def metadata(self) -> dict[str, Any]: ...

    def health(self) -> dict[str, Any]: ...

    def analyze(self, request: dict[str, Any]) -> dict[str, Any]: ...


def plugin_incompatible_response(reason_codes: Sequence[str]) -> dict[str, Any]:
    """Return the generic fail-closed response for an incompatible plugin."""

    return {
        "ranking": [],
        "status": "PLUGIN_INCOMPATIBLE",
        "reason_codes": list(reason_codes),
        "artifact_identity": {},
        "evidence": {},
    }


def abstain_response(reason_codes: Sequence[str]) -> dict[str, Any]:
    """Return the generic fail-closed response for a runtime abstention."""

    return {
        "ranking": [],
        "status": "ABSTAIN",
        "reason_codes": list(reason_codes),
        "artifact_identity": {},
        "evidence": {},
    }


def validate_plugin_manifest(manifest: Mapping[str, Any]) -> None:
    required_top_level = (
        "plugin_id",
        "version",
        "entrypoint",
        "contract",
        "compatible_delta_engines",
        "capabilities",
        "failure_policy",
        "artifact_identity",
    )
    _require_keys(manifest, required_top_level, "manifest")

    failure_policy = _mapping(manifest["failure_policy"], "failure_policy")
    if failure_policy.get("mode") != "fail-closed":
        raise PluginContractError("PLUGIN_FAILURE_POLICY_MUST_BE_FAIL_CLOSED")

    contract = _mapping(manifest["contract"], "contract")
    methods = contract.get("methods")
    if not isinstance(methods, list) or set(methods) != {"metadata", "health", "analyze"}:
        raise PluginContractError("PLUGIN_CONTRACT_METHODS_INVALID")

    engines = manifest["compatible_delta_engines"]
    if not isinstance(engines, list) or not engines:
        raise PluginContractError("PLUGIN_COMPATIBLE_ENGINES_REQUIRED")
    for idx, engine in enumerate(engines):
        engine_map = _mapping(engine, f"compatible_delta_engines[{idx}]")
        _require_keys(engine_map, ("repository", "commit", "compatibility"), f"engine[{idx}]")
        commit = str(engine_map["commit"])
        if not GIT_COMMIT_RE.fullmatch(commit):
            raise PluginContractError("PLUGIN_ENGINE_COMMIT_INVALID")

    artifact_identity = _mapping(manifest["artifact_identity"], "artifact_identity")
    components = artifact_identity.get("components")
    if not isinstance(components, list) or not components:
        raise PluginContractError("PLUGIN_ARTIFACT_COMPONENTS_REQUIRED")
    for idx, component in enumerate(components):
        component_map = _mapping(component, f"artifact_identity.components[{idx}]")
        _require_keys(component_map, ("name", "path", "sha256", "size_bytes"), f"component[{idx}]")
        if not SHA256_RE.fullmatch(str(component_map["sha256"])):
            raise PluginContractError("PLUGIN_ARTIFACT_SHA256_INVALID")
        if not isinstance(component_map["size_bytes"], int) or component_map["size_bytes"] <= 0:
            raise PluginContractError("PLUGIN_ARTIFACT_SIZE_INVALID")


def validate_analyze_response(response: Mapping[str, Any]) -> None:
    _require_keys(
        response,
        ("ranking", "status", "reason_codes", "artifact_identity", "evidence"),
        "analyze_response",
    )
    if not isinstance(response["ranking"], list):
        raise PluginContractError("PLUGIN_RESPONSE_RANKING_MUST_BE_LIST")
    if not isinstance(response["status"], str) or not response["status"]:
        raise PluginContractError("PLUGIN_RESPONSE_STATUS_REQUIRED")
    if not isinstance(response["reason_codes"], list) or not all(
        isinstance(code, str) and code for code in response["reason_codes"]
    ):
        raise PluginContractError("PLUGIN_RESPONSE_REASON_CODES_INVALID")
    _mapping(response["artifact_identity"], "artifact_identity")
    _mapping(response["evidence"], "evidence")


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PluginContractError(f"{field.upper()}_MUST_BE_OBJECT")
    return value


def _require_keys(value: Mapping[str, Any], keys: Sequence[str], field: str) -> None:
    missing = [key for key in keys if key not in value]
    if missing:
        joined = ",".join(missing)
        raise PluginContractError(f"{field.upper()}_MISSING_REQUIRED_KEYS:{joined}")
