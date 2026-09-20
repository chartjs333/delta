from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from deltacontroller.errors import AuthenticationFailedError
from deltacontroller.runtime_config import (
    CONTRACT_SCHEMA_VERSION,
    FORMAL_SEMANTICS_ID,
    HTTP_PROTOCOL_ID,
    MAX_JSON_DEPTH,
    MAX_REQUEST_BYTES,
    DataDirectoryLease,
    HashedTokenAuthenticationPort,
    load_or_bootstrap_runtime_identity,
    load_working_version_config,
    validate_build_id,
)

BUILD_ID = "a" * 40


def test_build_id_is_exact_lowercase_git_sha() -> None:
    assert validate_build_id(BUILD_ID) == BUILD_ID
    with pytest.raises(ValueError, match="exact 40-character lowercase"):
        validate_build_id(BUILD_ID.upper())
    with pytest.raises(ValueError, match="exact 40-character lowercase"):
        validate_build_id(f" {BUILD_ID}")


def _descriptor() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "build_id_source": "required-cli-argument",
        "profile": "LOCAL_LOOPBACK",
        "protocol_id": HTTP_PROTOCOL_ID,
        "contract_schema_version": CONTRACT_SCHEMA_VERSION,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "bindings": {
            "host": "127.0.0.1",
            "port": 8765,
            "allowed_origins": ["http://127.0.0.1:8765"],
        },
        "limits": {
            "request_bytes": MAX_REQUEST_BYTES,
            "json_depth": MAX_JSON_DEPTH,
            "request_timeout_seconds": 30,
            "max_inflight_requests": 16,
            "request_queue_size": 16,
            "worker_queue_capacity": 4,
            "worker_processes": 1,
            "shutdown_grace_seconds": 30,
        },
        "identity": {
            "local_subject_id": "local.operator",
            "local_effective_roles": ["OPERATOR"],
        },
    }


def test_descriptor_binds_loopback_limits_and_immutable_ids(tmp_path: Path) -> None:
    path = tmp_path / "local.json"
    path.write_text(json.dumps(_descriptor()), encoding="utf-8")
    config = load_working_version_config(path)
    assert config.is_local
    assert config.bind_host == "127.0.0.1"
    assert config.request_limit_bytes == 10 * 1024 * 1024
    assert config.json_max_depth == 32
    assert config.formal_semantics_id == FORMAL_SEMANTICS_ID

    bad_bind = _descriptor()
    assert isinstance(bad_bind["bindings"], dict)
    bad_bind["bindings"]["host"] = "0.0.0.0"
    path.write_text(json.dumps(bad_bind), encoding="utf-8")
    with pytest.raises(ValueError, match=r"bind exactly 127\.0\.0\.1"):
        load_working_version_config(path)


@pytest.mark.parametrize("non_finite", [float("nan"), float("inf"), float("-inf")])
def test_descriptor_rejects_non_finite_timeout_numbers(tmp_path: Path, non_finite: float) -> None:
    descriptor = _descriptor()
    assert isinstance(descriptor["limits"], dict)
    descriptor["limits"]["request_timeout_seconds"] = non_finite
    path = tmp_path / "non-finite.json"
    path.write_text(json.dumps(descriptor), encoding="utf-8")

    with pytest.raises(ValueError, match="non-finite JSON number"):
        load_working_version_config(path)


def test_remote_descriptor_requires_https_origins(tmp_path: Path) -> None:
    descriptor = _descriptor()
    descriptor["profile"] = "REMOTE_TLS"
    assert isinstance(descriptor["bindings"], dict)
    descriptor["bindings"]["host"] = "0.0.0.0"
    path = tmp_path / "remote.json"
    path.write_text(json.dumps(descriptor), encoding="utf-8")
    with pytest.raises(ValueError, match="https"):
        load_working_version_config(path)


def test_origins_are_exact_authorities_and_local_cannot_trust_hostile_sites(
    tmp_path: Path,
) -> None:
    descriptor = _descriptor()
    assert isinstance(descriptor["bindings"], dict)
    descriptor["bindings"]["allowed_origins"] = [
        "http://127.0.0.1:8765",
        "https://attacker.invalid",
    ]
    path = tmp_path / "local-hostile-origin.json"
    path.write_text(json.dumps(descriptor), encoding="utf-8")
    with pytest.raises(ValueError, match="exactly its own loopback origin"):
        load_working_version_config(path)

    descriptor["profile"] = "REMOTE_TLS"
    descriptor["bindings"]["host"] = "0.0.0.0"
    descriptor["bindings"]["allowed_origins"] = ["https://admin.example.invalid/path"]
    path.write_text(json.dumps(descriptor), encoding="utf-8")
    with pytest.raises(ValueError, match="scheme and authority"):
        load_working_version_config(path)


def test_local_identity_bootstrap_is_explicit_and_restart_stable(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="bootstrap was not authorized"):
        load_or_bootstrap_runtime_identity(data_dir=tmp_path, allow_local_bootstrap=False)

    first = load_or_bootstrap_runtime_identity(
        data_dir=tmp_path,
        allow_local_bootstrap=True,
    )
    assert first.trust_roots_path.is_file()
    assert (tmp_path / "controller-signing-key.pem").is_file()
    assert "fixture" not in first.signing_identity.key_id
    assert (
        first.public_key_hex
        == first.signing_identity.private_key.public_key().public_bytes_raw().hex()
    )

    restarted = load_or_bootstrap_runtime_identity(
        data_dir=tmp_path,
        allow_local_bootstrap=False,
    )
    assert restarted.public_key_hex == first.public_key_hex
    assert restarted.signing_identity.key_id == first.signing_identity.key_id


def test_identity_fails_closed_when_worker_root_does_not_match(tmp_path: Path) -> None:
    identity = load_or_bootstrap_runtime_identity(
        data_dir=tmp_path,
        allow_local_bootstrap=True,
    )
    roots = json.loads(identity.trust_roots_path.read_text(encoding="utf-8"))
    roots["keys"][0]["public_key_hex"] = "00" * 32
    identity.trust_roots_path.write_text(json.dumps(roots), encoding="utf-8")
    with pytest.raises(ValueError, match="does not match"):
        load_or_bootstrap_runtime_identity(
            data_dir=tmp_path,
            allow_local_bootstrap=False,
        )


def test_controller_and_worker_require_the_same_exact_trust_root_shape(tmp_path: Path) -> None:
    identity = load_or_bootstrap_runtime_identity(
        data_dir=tmp_path,
        allow_local_bootstrap=True,
    )
    roots = json.loads(identity.trust_roots_path.read_text(encoding="utf-8"))
    roots["unreviewed_metadata"] = True
    identity.trust_roots_path.write_text(json.dumps(roots), encoding="utf-8")
    with pytest.raises(ValueError, match="exact runtime schema"):
        load_or_bootstrap_runtime_identity(
            data_dir=tmp_path,
            allow_local_bootstrap=False,
        )


def test_remote_auth_stores_only_fingerprint_and_ignores_claimed_roles(tmp_path: Path) -> None:
    opaque_value = "unit-test-opaque-value"
    fingerprint = hashlib.sha256(opaque_value.encode()).hexdigest()
    auth_path = tmp_path / "remote-auth.json"
    auth_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "token_subjects": [
                    {
                        "token_sha256": fingerprint,
                        "subject_id": "remote.operator",
                        "effective_roles": ["OPERATOR"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    port = HashedTokenAuthenticationPort.from_file(auth_path)
    subject = port.authenticate({"type": "TOKEN", "token": opaque_value, "roles": ["AUDITOR"]})
    assert subject.subject_id == "remote.operator"
    assert subject.effective_roles == ["OPERATOR"]
    with pytest.raises(AuthenticationFailedError):
        port.authenticate({"type": "TOKEN", "token": "wrong"})

    document = json.loads(auth_path.read_text(encoding="utf-8"))
    document["token_subjects"][0]["unexpected_field"] = True
    auth_path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="entries must use the exact schema"):
        HashedTokenAuthenticationPort.from_file(auth_path)


def test_data_directory_has_one_process_owner(tmp_path: Path) -> None:
    first = DataDirectoryLease(tmp_path, build_id=BUILD_ID)
    second = DataDirectoryLease(tmp_path, build_id=BUILD_ID)
    first.acquire()
    try:
        with pytest.raises(RuntimeError, match="already owned"):
            second.acquire()
        owner = json.loads((tmp_path / "runtime-owner.json").read_text(encoding="utf-8"))
        assert owner["build_id"] == BUILD_ID
    finally:
        first.release()
    second.acquire()
    second.release()
