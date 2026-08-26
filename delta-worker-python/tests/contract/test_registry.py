from __future__ import annotations

import hashlib
import json
from pathlib import Path

from deltatorrent.domain.formal_compat import FORMAL_SEMANTICS_ID

ROOT = Path(__file__).resolve().parents[3]
PROTOCOL = ROOT / "delta-protocol"


def test_registry_paths_and_content_hashes() -> None:
    registry = json.loads((PROTOCOL / "registry.json").read_text(encoding="utf-8"))
    assert registry["formal_semantics_id"] == FORMAL_SEMANTICS_ID
    records = [*registry["schemas"], *registry["fixtures"], registry["action_registry"]]
    paths = [record["path"] for record in records]
    assert len(paths) == len(set(paths))
    assert [item["path"] for item in registry["schemas"]] == sorted(
        item["path"] for item in registry["schemas"]
    )
    assert [item["path"] for item in registry["fixtures"]] == sorted(
        item["path"] for item in registry["fixtures"]
    )
    for record in records:
        path = PROTOCOL / record["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]


def test_registry_media_and_schema_ids_are_unique() -> None:
    registry = json.loads((PROTOCOL / "registry.json").read_text(encoding="utf-8"))
    media_ids = [item["id"] for item in registry["media_types"]]
    schema_ids = [item["id"] for item in registry["schemas"]]
    assert len(media_ids) == len(set(media_ids))
    assert len(schema_ids) == len(set(schema_ids))
    assert {item["schema_id"] for item in registry["media_types"]} <= set(schema_ids)
