"""Disk-backed presentation metadata, separate from Controller/protocol state."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
EXECUTION = re.compile(UUID + r"\Z", re.I)
MAX_BYTES = 300_000


def default_profile() -> dict[str, Any]:
    return {
        "version": 1,
        "profileName": "Local presentation",
        "language": "en",
        "controllerDocument": None,
        "campaigns": [{"id": "presentation", "name": "Presentation"}],
        "activeCampaignId": "presentation",
        "runs": [],
        "workload": {
            "model_plugin_id": "tabular-10gene-phenotype-v1",
            "dataset_id": "synthetic-10gene-cohort-v1",
            "requested_scope": "PLUGIN_BOUNDARY",
            "catalog_backend_ref": "670b58f6458fe84620f4f9f46401f855d04ae05d",
        },
    }


def parse_json(raw: bytes) -> Any:
    if len(raw) > MAX_BYTES:
        raise ValueError("PROFILE_TOO_LARGE")

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("DUPLICATE_KEY")
            result[key] = value
        return result

    def invalid(value):
        raise ValueError("NONFINITE_JSON")

    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)


def validate_profile(data: Any) -> None:
    if (
        not isinstance(data, dict)
        or set(data)
        != {
            "version",
            "profileName",
            "language",
            "controllerDocument",
            "campaigns",
            "activeCampaignId",
            "workload",
            "runs",
        }
        or data["version"] != 1
    ):
        raise ValueError("INVALID_PROFILE")

    def text(value, limit):
        return isinstance(value, str) and 0 < len(value.strip()) <= limit

    def workload(value):
        return value == {
            "model_plugin_id": "tabular-10gene-phenotype-v1",
            "dataset_id": "synthetic-10gene-cohort-v1",
            "requested_scope": "PLUGIN_BOUNDARY",
            "catalog_backend_ref": "670b58f6458fe84620f4f9f46401f855d04ae05d",
        }

    if not text(data["profileName"], 80) or data["language"] not in {"en", "ru"}:
        raise ValueError("INVALID_PROFILE")
    document = data["controllerDocument"]
    if document is not None:
        if not isinstance(document, str) or len(document) > 100_000:
            raise ValueError("INVALID_CONTROLLER_DOCUMENT")
        # Definitions may contain public identities; credentials are not a profile field.
        if re.search(
            r"PRIVATE KEY|\"(?:password|secret|private_key|token|api_key)\"\s*:", document, re.I
        ):
            raise ValueError("CREDENTIALS_NOT_ALLOWED_IN_PROFILE")
        if not isinstance(parse_json(document.encode()), dict):
            raise ValueError("INVALID_CONTROLLER_DOCUMENT")
    campaigns, runs = data["campaigns"], data["runs"]
    if not isinstance(campaigns, list) or not 1 <= len(campaigns) <= 30:
        raise ValueError("INVALID_CAMPAIGNS")
    ids = set()
    for item in campaigns:
        if not isinstance(item, dict) or set(item) != {"id", "name"} or not text(item["name"], 80):
            raise ValueError("INVALID_CAMPAIGN")
        identifier = item["id"]
        if (
            not isinstance(identifier, str)
            or not re.fullmatch(r"[a-zA-Z0-9-]{1,64}", identifier)
            or identifier in ids
        ):
            raise ValueError("INVALID_CAMPAIGN_ID")
        ids.add(identifier)
    if data["activeCampaignId"] not in ids or not workload(data["workload"]):
        raise ValueError("INVALID_SELECTION")
    if not isinstance(runs, list) or len(runs) > 100:
        raise ValueError("INVALID_RUNS")
    intents = set()
    for run in runs:
        required = {
            "intentId",
            "intentDigest",
            "campaignId",
            "name",
            "workload",
            "operation",
            "createdAt",
        }
        if not isinstance(run, dict) or set(run) not in (required, required | {"executionId"}):
            raise ValueError("INVALID_RUN")
        if (
            not isinstance(run["intentId"], str)
            or not EXECUTION.fullmatch(run["intentId"])
            or run["intentId"] in intents
        ):
            raise ValueError("INVALID_INTENT_ID")
        intents.add(run["intentId"])
        if (
            not isinstance(run["intentDigest"], str)
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", run["intentDigest"])
            or run["campaignId"] not in ids
            or not text(run["name"], 80)
            or not workload(run["workload"])
            or not text(run["createdAt"], 64)
            or run["operation"]
            not in {"TRAIN_TICKET", "EVALUATE_CHECKPOINT", "MATERIALIZE_DATASET"}
        ):
            raise ValueError("INVALID_RUN_BINDING")
        if "executionId" in run and (
            not isinstance(run["executionId"], str) or not EXECUTION.fullmatch(run["executionId"])
        ):
            raise ValueError("INVALID_EXECUTION_ID")


def read_profile(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"revision": 0, "data": None}
    payload = parse_json(path.read_bytes())
    if (
        not isinstance(payload, dict)
        or set(payload) != {"revision", "data"}
        or type(payload["revision"]) is not int
        or payload["revision"] < 1
    ):
        raise ValueError("INVALID_SAVED_PROFILE")
    validate_profile(payload["data"])
    return payload


def save_profile(path: Path, payload: Any) -> dict[str, Any]:
    """Caller holds Presentation.lock; revision prevents lost updates across tabs."""
    if (
        not isinstance(payload, dict)
        or set(payload) != {"revision", "data"}
        or type(payload["revision"]) is not int
    ):
        raise ValueError("INVALID_PROFILE_REQUEST")
    current = read_profile(path)
    if payload["revision"] != current["revision"]:
        raise FileExistsError("PROFILE_REVISION_CONFLICT")
    validate_profile(payload["data"])
    result = {"revision": current["revision"] + 1, "data": payload["data"]}
    raw = json.dumps(result, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode()
    if len(raw) > MAX_BYTES:
        raise ValueError("PROFILE_TOO_LARGE")
    temporary = path.with_suffix(".next.json")
    with temporary.open("wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    return result
