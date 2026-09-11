from __future__ import annotations

import copy
from typing import Any

import pytest
from deltatorrent.plugins.contract import (
    DeltaPlugin,
    PluginContractError,
    abstain_response,
    plugin_incompatible_response,
    validate_analyze_response,
    validate_plugin_manifest,
)


def _manifest() -> dict[str, Any]:
    return {
        "plugin_id": "example-plugin",
        "version": "0.1.0",
        "entrypoint": "example.plugin:DeltaPlugin",
        "contract": {
            "class": "DeltaPlugin",
            "methods": ["metadata", "health", "analyze"],
        },
        "compatible_delta_engines": [
            {
                "repository": "chartjs333/delta",
                "commit": "9e03b2c21a48729fbdd394c8628ea960a77d1c2f",
                "compatibility": "pinned",
            }
        ],
        "capabilities": ["example"],
        "failure_policy": {"mode": "fail-closed"},
        "artifact_identity": {
            "components": [
                {
                    "name": "model",
                    "path": "artifacts/model.json",
                    "sha256": "0" * 64,
                    "size_bytes": 1,
                }
            ]
        },
    }


class ExamplePlugin:
    def metadata(self) -> dict[str, Any]:
        return _manifest()

    def health(self) -> dict[str, Any]:
        return {"status": "ready"}

    def analyze(self, request: dict[str, Any]) -> dict[str, Any]:
        return abstain_response(["NOT_IMPLEMENTED"])


def test_delta_plugin_is_structural_protocol() -> None:
    assert isinstance(ExamplePlugin(), DeltaPlugin)


def test_manifest_requires_fail_closed_policy() -> None:
    manifest = _manifest()
    validate_plugin_manifest(manifest)

    bad = copy.deepcopy(manifest)
    bad["failure_policy"]["mode"] = "best-effort"
    with pytest.raises(PluginContractError, match="PLUGIN_FAILURE_POLICY_MUST_BE_FAIL_CLOSED"):
        validate_plugin_manifest(bad)


def test_manifest_rejects_bad_artifact_identity() -> None:
    manifest = _manifest()
    manifest["artifact_identity"]["components"][0]["sha256"] = "not-a-hash"

    with pytest.raises(PluginContractError, match="PLUGIN_ARTIFACT_SHA256_INVALID"):
        validate_plugin_manifest(manifest)


def test_generic_fail_closed_responses_validate() -> None:
    incompatible = plugin_incompatible_response(["HASH_MISMATCH"])
    abstained = abstain_response(["RUNTIME_UNAVAILABLE"])

    validate_analyze_response(incompatible)
    validate_analyze_response(abstained)
    assert incompatible["status"] == "PLUGIN_INCOMPATIBLE"
    assert abstained["status"] == "ABSTAIN"


def test_response_requires_reason_codes() -> None:
    response = abstain_response(["RUNTIME_UNAVAILABLE"])
    response["reason_codes"] = "RUNTIME_UNAVAILABLE"

    with pytest.raises(PluginContractError, match="PLUGIN_RESPONSE_REASON_CODES_INVALID"):
        validate_analyze_response(response)
