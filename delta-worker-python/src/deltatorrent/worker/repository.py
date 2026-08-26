"""Atomic ticket claim and immutable terminal-outcome repository."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any

from deltatorrent.artifacts.canonical_json import canonical_json_bytes
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.tickets import DomainPureWorkTicket


class ClaimDisposition(StrEnum):
    CLAIMED = "CLAIMED"
    REPLAY = "REPLAY"


@dataclass(frozen=True, slots=True)
class ClaimDecision:
    disposition: ClaimDisposition
    outcome: dict[str, Any] | None = None


class TicketResultRepository:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.claims = self.root / "claims"
        self.outcomes = self.root / "outcomes"
        self.claims.mkdir(parents=True, exist_ok=True)
        self.outcomes.mkdir(parents=True, exist_ok=True)

    def claim(
        self,
        ticket: DomainPureWorkTicket,
        *,
        recover_incomplete: bool = False,
    ) -> ClaimDecision:
        claim_path = self.claims / f"{ticket.ticket_id}.json"
        expected = canonical_json_bytes(
            {
                "schema_version": "1.0.0",
                "ticket_fingerprint": ticket.fingerprint,
                "ticket_id": ticket.ticket_id,
            }
        )
        if self._create_once(claim_path, expected):
            return ClaimDecision(ClaimDisposition.CLAIMED)
        try:
            actual = claim_path.read_bytes()
        except OSError as exc:
            raise DeltaError(ErrorCode.TICKET_ALREADY_IN_PROGRESS, "TICKET_CLAIM_RACE") from exc
        if actual != expected:
            raise DeltaError(
                ErrorCode.TICKET_ID_CONFLICT,
                "TICKET_ID_REUSED_WITH_DIFFERENT_FINGERPRINT",
                {"ticket_id": ticket.ticket_id},
            )
        outcome = self._read_outcome(ticket.ticket_id)
        if outcome is None:
            if recover_incomplete:
                return ClaimDecision(ClaimDisposition.CLAIMED)
            raise DeltaError(
                ErrorCode.TICKET_ALREADY_IN_PROGRESS,
                "TICKET_ALREADY_IN_PROGRESS",
                {"ticket_id": ticket.ticket_id},
            )
        return ClaimDecision(ClaimDisposition.REPLAY, outcome)

    def complete(self, ticket: DomainPureWorkTicket, outcome: dict[str, Any]) -> None:
        claim_path = self.claims / f"{ticket.ticket_id}.json"
        if not claim_path.is_file():
            raise DeltaError(ErrorCode.TICKET_ID_CONFLICT, "TICKET_OUTCOME_WITHOUT_CLAIM")
        encoded = canonical_json_bytes(outcome)
        path = self.outcomes / f"{ticket.ticket_id}.json"
        if not self._create_once(path, encoded) and path.read_bytes() != encoded:
            raise DeltaError(ErrorCode.TICKET_ID_CONFLICT, "TICKET_OUTCOME_CONFLICT")

    def _read_outcome(self, ticket_id: str) -> dict[str, Any] | None:
        path = self.outcomes / f"{ticket_id}.json"
        if not path.is_file():
            return None
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DeltaError(ErrorCode.TICKET_ID_CONFLICT, "TICKET_OUTCOME_INVALID") from exc
        if not isinstance(value, dict):
            raise DeltaError(ErrorCode.TICKET_ID_CONFLICT, "TICKET_OUTCOME_INVALID")
        return dict(MappingProxyType(value))

    @staticmethod
    def _create_once(path: Path, value: bytes) -> bool:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        try:
            descriptor = os.open(path, flags, 0o600)
        except FileExistsError:
            return False
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(value)
                stream.flush()
                os.fsync(stream.fileno())
        except Exception:
            path.unlink(missing_ok=True)
            raise
        if os.name != "nt":
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        return True
