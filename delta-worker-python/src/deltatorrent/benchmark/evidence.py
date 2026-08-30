"""Append-only content-addressed benchmark evidence graph construction."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from deltatorrent.artifacts.filesystem import FilesystemArtifactStore
from deltatorrent.benchmark.arms import RunObservation
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.domain.manifests import ArtifactRef

_MEDIA = {
    "EFFICIENCY": (
        "application/vnd.deltareduce.efficiency-evidence+json;version=1",
        "SCHEMA-EFFICIENCY-EVIDENCE-010-V1",
    ),
    "QUALITY": (
        "application/vnd.deltareduce.quality-evidence+json;version=1",
        "SCHEMA-QUALITY-EVIDENCE-010-V1",
    ),
    "RESILIENCE": (
        "application/vnd.deltareduce.resilience-evidence+json;version=1",
        "SCHEMA-RESILIENCE-EVIDENCE-010-V1",
    ),
    "RUN": (
        "application/vnd.deltareduce.run-manifest+json;version=1",
        "SCHEMA-RUN-MANIFEST-010-V1",
    ),
    "SAFETY": (
        "application/vnd.deltareduce.safety-evidence+json;version=1",
        "SCHEMA-SAFETY-EVIDENCE-010-V1",
    ),
}
_CONTENT_ID = re.compile(r"^sha256:[0-9a-f]{64}$")


class EvidenceError(ValueError):
    """Stable evidence graph construction error."""


@dataclass(frozen=True, slots=True)
class EvidenceBundle:
    definition_id: str
    run_refs: tuple[ArtifactRef, ...]
    evidence_refs: tuple[tuple[str, ArtifactRef], ...]
    manifest_ref: ArtifactRef

    @property
    def run_ids(self) -> tuple[str, ...]:
        return tuple(item.content_id for item in self.run_refs)


class EvidenceCollector:
    def __init__(self, root: Path) -> None:
        self.store = FilesystemArtifactStore(root)

    def _publish(self, kind: str, value: dict[str, object]) -> ArtifactRef:
        try:
            media_type, schema_id = _MEDIA[kind]
        except KeyError as exc:
            raise EvidenceError("EVIDENCE_KIND_INVALID") from exc
        return self.store.publish_json(value, media_type=media_type, schema_id=schema_id)

    def collect(
        self,
        *,
        definition_id: str,
        runs: tuple[RunObservation, ...],
        quality: dict[str, object],
        safety: dict[str, object],
        efficiency: dict[str, object],
        resilience: dict[str, object],
        formal_regression_id: str,
    ) -> EvidenceBundle:
        if (
            _CONTENT_ID.fullmatch(definition_id) is None
            or _CONTENT_ID.fullmatch(formal_regression_id) is None
        ):
            raise EvidenceError("EVIDENCE_IDENTITY_INVALID")
        if not runs or any(run.definition_id != definition_id for run in runs):
            raise EvidenceError("RUN_DEFINITION_MISMATCH")
        if len({run.content_id for run in runs}) != len(runs):
            raise EvidenceError("RUN_IDENTITY_DUPLICATE")
        if any(
            document.get("benchmark_definition_id") != definition_id
            for document in (quality, safety, efficiency, resilience)
        ):
            raise EvidenceError("EVIDENCE_DEFINITION_MISMATCH")
        run_refs = tuple(self._publish("RUN", run.manifest) for run in runs)
        evidence_refs = tuple(
            (kind, self._publish(kind, document))
            for kind, document in (
                ("QUALITY", quality),
                ("SAFETY", safety),
                ("EFFICIENCY", efficiency),
                ("RESILIENCE", resilience),
            )
        )
        manifest = {
            "benchmark_definition_id": definition_id,
            "complete": True,
            "evidence": [
                {"content_id": formal_regression_id, "kind": "FORMAL"},
                *[
                    {"content_id": reference.content_id, "kind": kind}
                    for kind, reference in evidence_refs
                ],
            ],
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "run_ids": [item.content_id for item in run_refs],
            "schema_version": "1.0.0",
            "type_name": "EVIDENCE_MANIFEST",
        }
        manifest_ref = self.store.publish_json(
            manifest,
            media_type="application/vnd.deltareduce.evidence-manifest+json;version=1",
            schema_id="SCHEMA-EVIDENCE-MANIFEST-010-V1",
        )
        return EvidenceBundle(definition_id, run_refs, evidence_refs, manifest_ref)
