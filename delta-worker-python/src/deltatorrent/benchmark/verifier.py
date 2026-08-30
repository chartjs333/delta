"""Offline verification of the immutable benchmark evidence graph."""

from __future__ import annotations

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

    def verify(self, bundle: EvidenceBundle) -> VerificationResult:
        manifest = self._object(
            self.store.read(bundle.manifest_ref), "EVIDENCE_MANIFEST_NOT_CANONICAL"
        )
        if manifest.get("benchmark_definition_id") != bundle.definition_id:
            raise VerificationError("EVIDENCE_MANIFEST_DEFINITION_MISMATCH")
        if manifest.get("complete") is not True:
            raise VerificationError("EVIDENCE_MANIFEST_INCOMPLETE")
        run_ids = [reference.content_id for reference in bundle.run_refs]
        if not run_ids or len(set(run_ids)) != len(run_ids):
            raise VerificationError("EVIDENCE_MANIFEST_RUN_SET_INVALID")
        if manifest.get("run_ids") != run_ids:
            raise VerificationError("EVIDENCE_MANIFEST_RUN_SET_MISMATCH")
        for reference in bundle.run_refs:
            run = self._object(self.store.read(reference), "RUN_MANIFEST_NOT_CANONICAL")
            if run.get("benchmark_definition_id") != bundle.definition_id:
                raise VerificationError("RUN_MANIFEST_DEFINITION_MISMATCH")
        evidence_ids: dict[str, str] = {}
        for kind, reference in bundle.evidence_refs:
            document = self._object(self.store.read(reference), "EVIDENCE_NOT_CANONICAL")
            if document.get("benchmark_definition_id") != bundle.definition_id:
                raise VerificationError("EVIDENCE_DEFINITION_MISMATCH")
            evidence_ids[kind] = reference.content_id
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
        if set(manifest_ids) != {"EFFICIENCY", "FORMAL", "QUALITY", "RESILIENCE", "SAFETY"}:
            raise VerificationError("EVIDENCE_MANIFEST_GRAPH_INVALID")
        if any(manifest_ids.get(kind) != content_id for kind, content_id in evidence_ids.items()):
            raise VerificationError("EVIDENCE_MANIFEST_GRAPH_INVALID")
        return VerificationResult(
            definition_id=bundle.definition_id,
            manifest_id=bundle.manifest_ref.content_id,
            verified_object_count=1 + len(bundle.run_refs) + len(bundle.evidence_refs),
        )
