"""Immutable preregistration store and definition governance workflow."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from deltatorrent.benchmark.definition import BenchmarkDefinition
from deltatorrent.benchmark.review import GovernanceAttestation
from deltatorrent.protocol.canonical import canonical_json_bytes


class PreregistrationError(ValueError):
    """Stable fail-closed preregistration error."""


@dataclass(frozen=True, slots=True)
class PreregisteredDefinition:
    definition: BenchmarkDefinition
    attestation: GovernanceAttestation

    def __post_init__(self) -> None:
        if self.attestation.purpose != "DEFINITION":
            raise PreregistrationError("DEFINITION_ATTESTATION_PURPOSE_INVALID")
        if self.attestation.body_id != self.definition.content_id:
            raise PreregistrationError("DEFINITION_ATTESTATION_ID_MISMATCH")


class PreregistrationStore:
    """Create-only definition store; existing bytes can only be replayed exactly."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def seal(self, preregistration: PreregisteredDefinition) -> Path:
        digest = preregistration.definition.content_id.removeprefix("sha256:")
        target = self.root / f"{digest}.json"
        value = canonical_json_bytes(
            {
                "attestation": preregistration.attestation.to_dict(),
                "definition": preregistration.definition.raw,
            }
        )
        try:
            descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            if target.read_bytes() != value:
                raise PreregistrationError("PREREGISTRATION_IMMUTABLE_CONFLICT") from None
            return target
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        return target
