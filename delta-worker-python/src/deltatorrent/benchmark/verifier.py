"""Offline verification of the immutable benchmark evidence graph."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from deltatorrent.artifacts.filesystem import FilesystemArtifactStore
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.benchmark.evidence import EvidenceBundle
from deltatorrent.protocol.canonical import canonical_json_bytes


class VerificationError(ValueError):
    """Stable fail-closed offline evidence verification error."""


_CONTENT_ID = re.compile(r"^sha256:[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class VerificationResult:
    definition_id: str
    manifest_id: str
    verified_object_count: int
    status: str = "PASS"


class OfflineVerifier:
    def __init__(self, store_root: Path) -> None:
        self.store = FilesystemArtifactStore(store_root)

    def _object(self, value: bytes, code: str) -> dict[str, object]:
        try:
            document = json.loads(value)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise VerificationError(code) from exc
        if not isinstance(document, dict) or canonical_json_bytes(document) != value:
            raise VerificationError(code)
        if document.get("formal_semantics_id") != FORMAL_SEMANTICS_ID:
            raise VerificationError("EVIDENCE_FORMAL_ID_MISMATCH")
        return document

    def _bytes_by_id(self, content_id: str) -> bytes:
        if _CONTENT_ID.fullmatch(content_id) is None:
            raise VerificationError("EVIDENCE_OBJECT_ID_INVALID")
        digest = content_id.removeprefix("sha256:")
        path = self.store.root / "objects" / "sha256" / digest[:2] / digest
        try:
            value = path.read_bytes()
        except FileNotFoundError as exc:
            raise VerificationError("EVIDENCE_OBJECT_MISSING") from exc
        if hashlib.sha256(value).hexdigest() != digest:
            raise VerificationError("EVIDENCE_OBJECT_HASH_MISMATCH")
        return value

    def _object_by_id(self, content_id: str, code: str) -> dict[str, object]:
        return self._object(self._bytes_by_id(content_id), code)

    def verify_manifest(self, manifest_id: str) -> VerificationResult:
        manifest = self._object_by_id(manifest_id, "EVIDENCE_MANIFEST_NOT_CANONICAL")
        if manifest.get("type_name") != "EVIDENCE_MANIFEST":
            raise VerificationError("EVIDENCE_MANIFEST_TYPE_INVALID")
        definition_id = manifest.get("benchmark_definition_id")
        if not isinstance(definition_id, str) or _CONTENT_ID.fullmatch(definition_id) is None:
            raise VerificationError("EVIDENCE_MANIFEST_DEFINITION_MISMATCH")
        if manifest.get("complete") is not True:
            raise VerificationError("EVIDENCE_MANIFEST_INCOMPLETE")
        run_ids = manifest.get("run_ids")
        if (
            not isinstance(run_ids, list)
            or not run_ids
            or any(
                not isinstance(item, str) or _CONTENT_ID.fullmatch(item) is None for item in run_ids
            )
            or len(set(run_ids)) != len(run_ids)
        ):
            raise VerificationError("EVIDENCE_MANIFEST_RUN_SET_INVALID")
        for run_id in run_ids:
            run = self._object_by_id(run_id, "RUN_MANIFEST_NOT_CANONICAL")
            if run.get("type_name") != "RUN_MANIFEST":
                raise VerificationError("RUN_MANIFEST_TYPE_INVALID")
            if run.get("benchmark_definition_id") != definition_id:
                raise VerificationError("RUN_MANIFEST_DEFINITION_MISMATCH")
        manifest_evidence = manifest.get("evidence")
        if not isinstance(manifest_evidence, list):
            raise VerificationError("EVIDENCE_MANIFEST_GRAPH_INVALID")
        if any(
            not isinstance(item, dict)
            or set(item) != {"content_id", "kind"}
            or _CONTENT_ID.fullmatch(str(item.get("content_id"))) is None
            for item in manifest_evidence
        ):
            raise VerificationError("EVIDENCE_MANIFEST_GRAPH_INVALID")
        pairs = [
            (str(item["kind"]), str(item["content_id"]))
            for item in manifest_evidence
            if isinstance(item, dict)
        ]
        if len({kind for kind, _ in pairs}) != len(pairs):
            raise VerificationError("EVIDENCE_MANIFEST_GRAPH_INVALID")
        manifest_ids = dict(pairs)
        expected_types = {
            "EFFICIENCY": "EFFICIENCY_EVIDENCE",
            "FORMAL": "FORMAL_EVIDENCE",
            "QUALITY": "QUALITY_EVIDENCE",
            "RESILIENCE": "RESILIENCE_EVIDENCE",
            "SAFETY": "SAFETY_EVIDENCE",
        }
        if set(manifest_ids) != set(expected_types):
            raise VerificationError("EVIDENCE_MANIFEST_GRAPH_INVALID")
        if len(set(manifest_ids.values())) != len(manifest_ids) or set(run_ids) & set(
            manifest_ids.values()
        ):
            raise VerificationError("EVIDENCE_MANIFEST_GRAPH_INVALID")
        for kind, content_id in manifest_ids.items():
            document = self._object_by_id(content_id, "EVIDENCE_NOT_CANONICAL")
            if document.get("type_name") != expected_types[kind]:
                raise VerificationError("EVIDENCE_TYPE_MISMATCH")
            if document.get("benchmark_definition_id") != definition_id:
                raise VerificationError("EVIDENCE_DEFINITION_MISMATCH")
            if kind == "FORMAL" and document.get("status") != "PASS":
                raise VerificationError("FORMAL_EVIDENCE_INVALID")
        return VerificationResult(
            definition_id=definition_id,
            manifest_id=manifest_id,
            verified_object_count=1 + len(run_ids) + len(manifest_ids),
        )

    def verify(self, bundle: EvidenceBundle) -> VerificationResult:
        self.store.read(bundle.manifest_ref)
        for reference in bundle.run_refs:
            self.store.read(reference)
        for _, reference in bundle.evidence_refs:
            self.store.read(reference)
        result = self.verify_manifest(bundle.manifest_ref.content_id)
        if result.definition_id != bundle.definition_id:
            raise VerificationError("EVIDENCE_MANIFEST_DEFINITION_MISMATCH")
        manifest = self._object_by_id(
            bundle.manifest_ref.content_id, "EVIDENCE_MANIFEST_NOT_CANONICAL"
        )
        run_ids = [reference.content_id for reference in bundle.run_refs]
        if manifest.get("run_ids") != run_ids:
            raise VerificationError("EVIDENCE_MANIFEST_RUN_SET_MISMATCH")
        evidence_ids = {kind: reference.content_id for kind, reference in bundle.evidence_refs}
        manifest_evidence = manifest.get("evidence")
        if not isinstance(manifest_evidence, list):
            raise VerificationError("EVIDENCE_MANIFEST_GRAPH_INVALID")
        manifest_ids = {
            str(item["kind"]): str(item["content_id"])
            for item in manifest_evidence
            if isinstance(item, dict)
        }
        if manifest_ids != evidence_ids:
            raise VerificationError("EVIDENCE_MANIFEST_GRAPH_INVALID")
        return result
