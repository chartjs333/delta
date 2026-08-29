from __future__ import annotations

import json
from pathlib import Path

import pytest
from deltatorrent.qlora.manifests import ManifestError, load_import_request

FIXTURE = Path(__file__).parents[1] / "fixtures" / "models" / "tiny_qlora"


def test_tiny_import_is_pinned_hash_verified_and_offline() -> None:
    request = load_import_request(FIXTURE / "import.json", allowed_root=FIXTURE.parent)

    assert request.manifest.repository == "local/tiny-qlora-fixture"
    assert request.manifest.license_id == "CC0-1.0"
    assert request.manifest.redistribution_allowed
    assert request.local_files_only
    assert not request.trust_remote_code
    assert request.use_safetensors
    assert request.manifest.content_id.startswith("sha256:")


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ({"access_policy": "TOKEN_REQUIRED"}, "BASE_ACCESS_POLICY_REQUIRES_TOKEN"),
        ({"model_revision": "main"}, "BASE_REVISION_NOT_PINNED"),
        ({"formal_semantics_id": "sha256:" + "0" * 64}, "FORMAL_SEMANTICS_MISMATCH"),
    ],
)
def test_import_rejects_unsafe_provenance(
    tmp_path: Path, mutation: dict[str, object], code: str
) -> None:
    for source in FIXTURE.iterdir():
        if source.is_file():
            (tmp_path / source.name).write_bytes(source.read_bytes())
    value = json.loads((tmp_path / "import.json").read_text(encoding="utf-8"))
    value["base_manifest"].update(mutation)
    (tmp_path / "import.json").write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ManifestError, match=code):
        load_import_request(tmp_path / "import.json", allowed_root=tmp_path.parent)


def test_import_rejects_weight_hash_mismatch(tmp_path: Path) -> None:
    for source in FIXTURE.iterdir():
        if source.is_file():
            (tmp_path / source.name).write_bytes(source.read_bytes())
    (tmp_path / "base.safetensors.json").write_text("{}", encoding="utf-8")

    with pytest.raises(ManifestError, match="IMPORT_WEIGHT_HASH_MISMATCH"):
        load_import_request(tmp_path / "import.json", allowed_root=tmp_path.parent)


def test_import_rejects_pickle_extension(tmp_path: Path) -> None:
    for source in FIXTURE.iterdir():
        if source.is_file():
            (tmp_path / source.name).write_bytes(source.read_bytes())
    value = json.loads((tmp_path / "import.json").read_text(encoding="utf-8"))
    value["files"]["weights"] = ["base.pkl"]
    (tmp_path / "base.pkl").write_bytes(b"not-a-pickle")
    (tmp_path / "import.json").write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ManifestError, match="UNSAFE_MODEL_SERIALIZATION"):
        load_import_request(tmp_path / "import.json", allowed_root=tmp_path.parent)
