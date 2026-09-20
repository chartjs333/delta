"""Fail-closed runtime configuration for the single-host working version."""

from __future__ import annotations

import hashlib
import hmac
import importlib
import json
import math
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Final, cast
from urllib.parse import urlsplit

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from deltacontroller.auth import AuthenticatedSubject, AuthenticationPort
from deltacontroller.errors import AuthenticationFailedError, AuthenticationRequiredError
from deltacontroller.gate import AdmissionSigningIdentity

FORMAL_SEMANTICS_ID: Final = (
    "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
)
HTTP_PROTOCOL_ID: Final = "deltareduce.step5c.http.v1"
CONTRACT_SCHEMA_VERSION: Final = "1.0.0"
RUNTIME_DESCRIPTOR_VERSION: Final = "1.0.0"
MAX_REQUEST_BYTES: Final = 10 * 1024 * 1024
MAX_JSON_DEPTH: Final = 32

_SHA1_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_FIXTURE_KEY_IDS = frozenset({"step5c-fixture-ed25519"})
_FIXTURE_ISSUER_IDS = frozenset({"step5c-fixture-controller"})


def _reject_non_finite_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number '{value}' is not permitted")


def _load_strict_json(payload: str) -> Any:
    return json.loads(payload, parse_constant=_reject_non_finite_json_constant)


@dataclass(frozen=True, slots=True)
class WorkingVersionConfig:
    """Validated deployment descriptor consumed by the HTTP host."""

    profile: str
    bind_host: str
    port: int
    allowed_origins: tuple[str, ...]
    request_limit_bytes: int
    json_max_depth: int
    request_timeout_seconds: float
    max_inflight_requests: int
    request_queue_size: int
    worker_queue_capacity: int
    worker_processes: int
    shutdown_grace_seconds: float
    local_subject_id: str
    local_effective_roles: tuple[str, ...]
    protocol_id: str
    contract_schema_version: str
    formal_semantics_id: str

    @property
    def is_local(self) -> bool:
        return self.profile == "LOCAL_LOOPBACK"


@dataclass(frozen=True, slots=True)
class RuntimeIdentity:
    """Controller signing identity and the exact Worker public trust-root file."""

    signing_identity: AdmissionSigningIdentity
    trust_roots_path: Path
    public_key_hex: str


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return cast(dict[str, Any], value)


def _require_int(value: Any, label: str, *, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if value < minimum or value > maximum:
        raise ValueError(f"{label} must be in [{minimum}, {maximum}]")
    return int(value)


def _require_number(value: Any, label: str, *, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    try:
        number = float(value)
    except OverflowError as exc:
        raise ValueError(f"{label} must be in [{minimum}, {maximum}]") from exc
    if not math.isfinite(number) or number < minimum or number > maximum:
        raise ValueError(f"{label} must be in [{minimum}, {maximum}]")
    return number


def load_working_version_config(path: Path | str) -> WorkingVersionConfig:
    """Load and validate one immutable working-version deployment descriptor."""
    descriptor_path = Path(path).resolve()
    try:
        document = _require_object(
            _load_strict_json(descriptor_path.read_text(encoding="utf-8")),
            "deployment descriptor",
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read deployment descriptor '{descriptor_path}': {exc}") from exc

    if document.get("schema_version") != RUNTIME_DESCRIPTOR_VERSION:
        raise ValueError(
            f"deployment descriptor schema_version must be {RUNTIME_DESCRIPTOR_VERSION}"
        )
    if document.get("build_id_source") != "required-cli-argument":
        raise ValueError("deployment descriptor build_id_source must be required-cli-argument")

    bindings = _require_object(document.get("bindings"), "bindings")
    limits = _require_object(document.get("limits"), "limits")
    identity = _require_object(document.get("identity"), "identity")
    profile = document.get("profile")
    if profile not in {"LOCAL_LOOPBACK", "REMOTE_TLS"}:
        raise ValueError("profile must be LOCAL_LOOPBACK or REMOTE_TLS")

    bind_host = bindings.get("host")
    if not isinstance(bind_host, str) or not bind_host:
        raise ValueError("bindings.host must be a non-empty string")
    if profile == "LOCAL_LOOPBACK" and bind_host != "127.0.0.1":
        raise ValueError("LOCAL_LOOPBACK profile must bind exactly 127.0.0.1")

    port = _require_int(bindings.get("port"), "bindings.port", minimum=1, maximum=65535)
    raw_origins = bindings.get("allowed_origins")
    if not isinstance(raw_origins, list) or not raw_origins:
        raise ValueError("bindings.allowed_origins must be a non-empty array")
    origins: list[str] = []
    for origin in raw_origins:
        if not isinstance(origin, str) or not origin or "*" in origin:
            raise ValueError("allowed origins must be exact non-wildcard strings")
        normalized_origin = origin
        try:
            parsed_origin = urlsplit(normalized_origin)
            parsed_port = parsed_origin.port
        except ValueError as exc:
            raise ValueError(f"invalid allowed origin '{origin}'") from exc
        if (
            parsed_origin.hostname is None
            or parsed_origin.username is not None
            or parsed_origin.password is not None
            or parsed_origin.path
            or parsed_origin.query
            or parsed_origin.fragment
        ):
            raise ValueError("allowed origins must contain only a scheme and authority")
        if profile == "REMOTE_TLS" and parsed_origin.scheme != "https":
            raise ValueError("REMOTE_TLS allowed origins must use https://")
        if parsed_port is not None and not 1 <= parsed_port <= 65535:
            raise ValueError("allowed origin port must be in [1, 65535]")
        origins.append(normalized_origin)
    if len(set(origins)) != len(origins):
        raise ValueError("bindings.allowed_origins must not contain duplicates")
    if profile == "LOCAL_LOOPBACK":
        expected_origin = "http://127.0.0.1" + ("" if port == 80 else f":{port}")
        if origins != [expected_origin]:
            raise ValueError(
                f"LOCAL_LOOPBACK requires exactly its own loopback origin '{expected_origin}'"
            )

    protocol_id = document.get("protocol_id")
    schema_version = document.get("contract_schema_version")
    formal_id = document.get("formal_semantics_id")
    if protocol_id != HTTP_PROTOCOL_ID:
        raise ValueError(f"protocol_id must be {HTTP_PROTOCOL_ID}")
    if schema_version != CONTRACT_SCHEMA_VERSION:
        raise ValueError(f"contract_schema_version must be {CONTRACT_SCHEMA_VERSION}")
    if formal_id != FORMAL_SEMANTICS_ID:
        raise ValueError("formal_semantics_id does not match the accepted Formal GO")

    request_limit = _require_int(
        limits.get("request_bytes"), "limits.request_bytes", minimum=1, maximum=MAX_REQUEST_BYTES
    )
    if request_limit != MAX_REQUEST_BYTES:
        raise ValueError(f"limits.request_bytes must be exactly {MAX_REQUEST_BYTES}")
    json_depth = _require_int(
        limits.get("json_depth"), "limits.json_depth", minimum=1, maximum=MAX_JSON_DEPTH
    )
    if json_depth != MAX_JSON_DEPTH:
        raise ValueError(f"limits.json_depth must be exactly {MAX_JSON_DEPTH}")

    subject_id = identity.get("local_subject_id")
    roles = identity.get("local_effective_roles")
    if not isinstance(subject_id, str) or not subject_id.strip():
        raise ValueError("identity.local_subject_id must be a non-empty string")
    if not isinstance(roles, list) or not roles or not all(isinstance(role, str) for role in roles):
        raise ValueError("identity.local_effective_roles must be a non-empty string array")

    return WorkingVersionConfig(
        profile=profile,
        bind_host=bind_host,
        port=port,
        allowed_origins=tuple(origins),
        request_limit_bytes=request_limit,
        json_max_depth=json_depth,
        request_timeout_seconds=_require_number(
            limits.get("request_timeout_seconds"),
            "limits.request_timeout_seconds",
            minimum=1,
            maximum=120,
        ),
        max_inflight_requests=_require_int(
            limits.get("max_inflight_requests"),
            "limits.max_inflight_requests",
            minimum=1,
            maximum=1024,
        ),
        request_queue_size=_require_int(
            limits.get("request_queue_size"),
            "limits.request_queue_size",
            minimum=1,
            maximum=1024,
        ),
        worker_queue_capacity=_require_int(
            limits.get("worker_queue_capacity"),
            "limits.worker_queue_capacity",
            minimum=1,
            maximum=128,
        ),
        worker_processes=_require_int(
            limits.get("worker_processes"),
            "limits.worker_processes",
            minimum=1,
            maximum=32,
        ),
        shutdown_grace_seconds=_require_number(
            limits.get("shutdown_grace_seconds"),
            "limits.shutdown_grace_seconds",
            minimum=0,
            maximum=300,
        ),
        local_subject_id=subject_id,
        local_effective_roles=tuple(roles),
        protocol_id=protocol_id,
        contract_schema_version=schema_version,
        formal_semantics_id=formal_id,
    )


def validate_build_id(build_id: str) -> str:
    """Require the exact Git commit used by Controller and Worker provenance."""
    if not _SHA1_PATTERN.fullmatch(build_id):
        raise ValueError("build_id must be an exact 40-character lowercase Git SHA")
    return build_id


def _atomic_write(path: Path, payload: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        os.chmod(temporary_path, mode)
        with os.fdopen(descriptor, "wb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary_path, path)
        os.chmod(path, mode)
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        temporary_path.unlink(missing_ok=True)
        raise


def _load_trust_roots(path: Path) -> tuple[str, str, str]:
    try:
        document = _require_object(
            _load_strict_json(path.read_text(encoding="utf-8")), "trust roots"
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read Worker trust roots '{path}': {exc}") from exc
    if set(document) != {"schema_version", "issuer_id", "keys"}:
        raise ValueError("Worker trust roots must use the exact runtime schema")
    if document.get("schema_version") != "1.0.0":
        raise ValueError("Worker trust roots schema_version must be 1.0.0")
    issuer_id = document.get("issuer_id")
    keys = document.get("keys")
    if not isinstance(issuer_id, str) or not issuer_id or issuer_id in _FIXTURE_ISSUER_IDS:
        raise ValueError("Worker trust roots require a non-fixture issuer_id")
    if not isinstance(keys, list) or len(keys) != 1 or not isinstance(keys[0], dict):
        raise ValueError("Worker trust roots must contain exactly one explicit key")
    if set(keys[0]) != {"key_id", "algorithm", "public_key_hex"}:
        raise ValueError("Worker trust-root key must use the exact runtime schema")
    key_id = keys[0].get("key_id")
    algorithm = keys[0].get("algorithm")
    public_key_hex = keys[0].get("public_key_hex")
    if not isinstance(key_id, str) or not key_id or key_id in _FIXTURE_KEY_IDS:
        raise ValueError("Worker trust roots require a non-fixture key_id")
    if algorithm != "ED25519":
        raise ValueError("Worker trust root algorithm must be ED25519")
    if not isinstance(public_key_hex, str) or not _SHA256_PATTERN.fullmatch(public_key_hex):
        raise ValueError("Worker Ed25519 public key must be exactly 32 bytes of lowercase hex")
    return issuer_id, key_id, public_key_hex


def load_or_bootstrap_runtime_identity(
    *,
    data_dir: Path,
    allow_local_bootstrap: bool,
    signing_key_path: Path | None = None,
    trust_roots_path: Path | None = None,
) -> RuntimeIdentity:
    """Load explicit Controller/Worker trust material, or bootstrap a local-only identity."""
    resolved_data_dir = data_dir.resolve()
    resolved_data_dir.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(resolved_data_dir, 0o700)
    except OSError:
        pass

    key_path = (signing_key_path or (resolved_data_dir / "controller-signing-key.pem")).resolve()
    roots_path = (trust_roots_path or (resolved_data_dir / "worker-trust-roots.json")).resolve()
    key_exists = key_path.is_file()
    roots_exist = roots_path.is_file()

    if key_exists != roots_exist:
        raise ValueError(
            "Controller signing key and Worker trust roots must both exist or both be absent"
        )
    if not key_exists:
        if not allow_local_bootstrap:
            raise ValueError(
                "Explicit Controller signing key and Worker trust roots are required; "
                "local bootstrap was not authorized"
            )
        private_key = Ed25519PrivateKey.generate()
        public_key_hex = private_key.public_key().public_bytes_raw().hex()
        key_id = f"working-version-{hashlib.sha256(bytes.fromhex(public_key_hex)).hexdigest()[:16]}"
        issuer_id = "delta-working-version-local"
        private_payload = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        roots_document = {
            "schema_version": "1.0.0",
            "issuer_id": issuer_id,
            "keys": [
                {
                    "key_id": key_id,
                    "algorithm": "ED25519",
                    "public_key_hex": public_key_hex,
                }
            ],
        }
        _atomic_write(key_path, private_payload, 0o600)
        _atomic_write(
            roots_path,
            (json.dumps(roots_document, sort_keys=True, separators=(",", ":")) + "\n").encode(
                "utf-8"
            ),
            0o600,
        )

    try:
        loaded_key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
    except (OSError, ValueError, TypeError) as exc:
        raise ValueError(f"Cannot load Controller signing key '{key_path}': {exc}") from exc
    if not isinstance(loaded_key, Ed25519PrivateKey):
        raise ValueError("Controller signing key must be Ed25519")

    issuer_id, key_id, trusted_public_hex = _load_trust_roots(roots_path)
    actual_public_hex = loaded_key.public_key().public_bytes_raw().hex()
    if not hmac.compare_digest(actual_public_hex, trusted_public_hex):
        raise ValueError("Controller signing key does not match the explicit Worker trust root")

    signing_identity = AdmissionSigningIdentity(
        private_key=loaded_key,
        key_id=key_id,
        issuer_id=issuer_id,
    )
    return RuntimeIdentity(
        signing_identity=signing_identity,
        trust_roots_path=roots_path,
        public_key_hex=trusted_public_hex,
    )


class HashedTokenAuthenticationPort(AuthenticationPort):
    """Remote authentication backed by explicit SHA-256 token fingerprints."""

    def __init__(self, subjects_by_token_sha256: dict[str, AuthenticatedSubject]) -> None:
        if not subjects_by_token_sha256:
            raise ValueError("At least one remote token fingerprint is required")
        for fingerprint in subjects_by_token_sha256:
            if not _SHA256_PATTERN.fullmatch(fingerprint):
                raise ValueError("Remote token fingerprints must be 64 lowercase hex characters")
        self._subjects = dict(subjects_by_token_sha256)

    @classmethod
    def from_file(cls, path: Path | str) -> HashedTokenAuthenticationPort:
        config_path = Path(path).resolve()
        try:
            document = _require_object(
                _load_strict_json(config_path.read_text(encoding="utf-8")),
                "remote auth config",
            )
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Cannot read remote auth config '{config_path}': {exc}") from exc
        if set(document) != {"schema_version", "token_subjects"}:
            raise ValueError("remote auth config must use the exact runtime schema")
        if document.get("schema_version") != "1.0.0":
            raise ValueError("remote auth config schema_version must be 1.0.0")
        entries = document.get("token_subjects")
        if not isinstance(entries, list) or not entries:
            raise ValueError("remote auth config token_subjects must be a non-empty array")
        subjects: dict[str, AuthenticatedSubject] = {}
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != {
                "token_sha256",
                "subject_id",
                "effective_roles",
            }:
                raise ValueError("remote auth token_subjects entries must use the exact schema")
            fingerprint = entry.get("token_sha256")
            subject_id = entry.get("subject_id")
            roles = entry.get("effective_roles")
            if not isinstance(fingerprint, str):
                raise ValueError("remote auth entry requires token_sha256")
            if not isinstance(subject_id, str) or not subject_id:
                raise ValueError("remote auth entry requires subject_id")
            if (
                not isinstance(roles, list)
                or not roles
                or not all(isinstance(role, str) for role in roles)
            ):
                raise ValueError("remote auth entry requires effective_roles")
            if fingerprint in subjects:
                raise ValueError("duplicate remote token fingerprint")
            subjects[fingerprint] = AuthenticatedSubject(
                subject_id=subject_id,
                authenticated_via="TOKEN",
                effective_roles=list(roles),
            )
        return cls(subjects)

    def authenticate(self, credentials: dict[str, Any] | None) -> AuthenticatedSubject:
        if not credentials:
            raise AuthenticationRequiredError("Bearer authentication is required")
        if credentials.get("type") != "TOKEN":
            raise AuthenticationFailedError("Unsupported remote authentication mechanism")
        token = credentials.get("token")
        if not isinstance(token, str) or not token:
            raise AuthenticationFailedError("Missing bearer token")
        fingerprint = hashlib.sha256(token.encode("utf-8")).hexdigest()
        subject = self._subjects.get(fingerprint)
        if subject is None:
            raise AuthenticationFailedError("Invalid or unknown bearer token")
        return subject


class DataDirectoryLease:
    """Cross-platform exclusive process lease for one durable Controller data directory."""

    def __init__(self, data_dir: Path | str, *, build_id: str) -> None:
        self.data_dir = Path(data_dir).resolve()
        self.build_id = validate_build_id(build_id)
        self._stream: BinaryIO | None = None
        self._owner_path = self.data_dir / "runtime-owner.json"

    def acquire(self) -> None:
        if self._stream is not None:
            raise RuntimeError("Data directory lease is already held")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        lock_path = self.data_dir / ".controller.lock"
        stream = lock_path.open("a+b")
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                msvcrt: Any = importlib.import_module("msvcrt")
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                fcntl: Any = importlib.import_module("fcntl")
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            stream.close()
            raise RuntimeError(
                f"Durable data directory is already owned by another process: {self.data_dir}"
            ) from exc
        self._stream = stream
        owner = {
            "schema_version": "1.0.0",
            "pid": os.getpid(),
            "build_id": self.build_id,
            "data_dir": str(self.data_dir),
        }
        _atomic_write(
            self._owner_path,
            (json.dumps(owner, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"),
            0o600,
        )

    def release(self) -> None:
        stream = self._stream
        if stream is None:
            return
        self._owner_path.unlink(missing_ok=True)
        try:
            stream.seek(0)
            if os.name == "nt":
                msvcrt: Any = importlib.import_module("msvcrt")
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl: Any = importlib.import_module("fcntl")
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        finally:
            stream.close()
            self._stream = None

    def __enter__(self) -> DataDirectoryLease:
        self.acquire()
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.release()
