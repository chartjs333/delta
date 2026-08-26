"""Atomic immutable filesystem artifact store."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path, PurePosixPath

from deltatorrent.artifacts.canonical_json import canonical_json_bytes, sha256_content_id
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.manifests import ArtifactRef


class FilesystemArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def publish_bytes(
        self,
        value: bytes,
        *,
        media_type: str,
        schema_id: str,
        schema_version: str = "1.0.0",
    ) -> ArtifactRef:
        content_id = sha256_content_id(value)
        digest = content_id.removeprefix("sha256:")
        locator = f"objects/sha256/{digest[:2]}/{digest}"
        return self._publish_at(locator, value, media_type, schema_id, schema_version)

    def publish_json(
        self,
        value: object,
        *,
        media_type: str,
        schema_id: str,
        schema_version: str = "1.0.0",
    ) -> ArtifactRef:
        return self.publish_bytes(
            canonical_json_bytes(value),
            media_type=media_type,
            schema_id=schema_id,
            schema_version=schema_version,
        )

    def publish_named(
        self,
        locator: str,
        value: bytes,
        *,
        media_type: str,
        schema_id: str,
        schema_version: str = "1.0.0",
    ) -> ArtifactRef:
        return self._publish_at(locator, value, media_type, schema_id, schema_version)

    def _publish_at(
        self,
        locator: str,
        value: bytes,
        media_type: str,
        schema_id: str,
        schema_version: str,
    ) -> ArtifactRef:
        target = self._resolve_locator(locator)
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(value)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, target)
            except FileExistsError:
                existing = target.read_bytes()
                if existing != value:
                    raise DeltaError(
                        ErrorCode.ARTIFACT_IMMUTABLE_CONFLICT,
                        "immutable artifact locator already contains different bytes",
                        {"locator": locator},
                    ) from None
            self._sync_directory(target.parent)
        finally:
            temporary.unlink(missing_ok=True)

        content_id = sha256_content_id(value)
        reference = ArtifactRef(
            byte_length=len(value),
            content_id=content_id,
            locator=locator,
            media_type=media_type,
            schema_id=schema_id,
            schema_version=schema_version,
        )
        self.verify(reference)
        return reference

    def read(self, reference: ArtifactRef) -> bytes:
        path = self._resolve_locator(reference.locator)
        try:
            value = path.read_bytes()
        except FileNotFoundError as exc:
            raise DeltaError(
                ErrorCode.ARTIFACT_NOT_FOUND,
                "referenced artifact does not exist",
                {"content_id": reference.content_id},
            ) from exc
        if len(value) != reference.byte_length or sha256_content_id(value) != reference.content_id:
            raise DeltaError(
                ErrorCode.ARTIFACT_HASH_MISMATCH,
                "artifact bytes do not match the immutable reference",
                {"content_id": reference.content_id},
            )
        return value

    def verify(self, reference: ArtifactRef) -> None:
        self.read(reference)

    def cleanup_temporary_files(self) -> tuple[str, ...]:
        removed: list[str] = []
        for path in sorted(self.root.rglob(".*.tmp")):
            if path.is_file():
                removed.append(path.relative_to(self.root).as_posix())
                path.unlink()
        return tuple(removed)

    def _resolve_locator(self, locator: str) -> Path:
        pure = PurePosixPath(locator)
        if (
            not locator
            or "\\" in locator
            or pure.is_absolute()
            or ".." in pure.parts
            or "." in pure.parts
            or str(pure) != locator
        ):
            raise DeltaError(
                ErrorCode.INVALID_ARTIFACT_LOCATOR,
                "artifact locator must remain inside the store",
                {"locator": locator},
            )
        path = (self.root / Path(*pure.parts)).resolve()
        if not path.is_relative_to(self.root):
            raise DeltaError(ErrorCode.INVALID_ARTIFACT_LOCATOR, "artifact escaped store root")
        return path

    @staticmethod
    def _sync_directory(path: Path) -> None:
        if os.name == "nt":
            return
        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
