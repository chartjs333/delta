"""Explicit guard between worker-local outputs and global distribution objects."""

from __future__ import annotations

from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.manifests import ArtifactRef

WORKER_LOCAL_MEDIA_TYPES = frozenset(
    {
        "application/vnd.deltareduce.local-round-completion+json;version=1",
        "application/vnd.deltareduce.normalized-contribution-candidate+json;version=1",
    }
)


def require_distribution_eligible(reference: ArtifactRef) -> ArtifactRef:
    if not isinstance(reference, ArtifactRef) or reference.media_type in WORKER_LOCAL_MEDIA_TYPES:
        raise DeltaError(
            ErrorCode.SCHEMA_INVALID,
            "WORKER_LOCAL_ARTIFACT_FORBIDDEN_IN_DISTRIBUTION_PLANE",
        )
    return reference
