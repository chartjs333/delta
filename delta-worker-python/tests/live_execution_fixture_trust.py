"""Explicit test-only trust configuration for frozen Step 5C fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from deltatorrent.live_execution.preflight import AuthorizedExecutionPreflight

_FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "admin-ui"
    / "step5c-controlled-live-execution"
    / "contracts"
    / "vectors"
    / "ed25519-fixture.json"
)
_FIXTURE = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
FIXTURE_KEY_ID = str(_FIXTURE["key_id"])
FIXTURE_PUBLIC_KEY_HEX = str(_FIXTURE["public_key_hex"])


def fixture_authorized_execution_preflight() -> AuthorizedExecutionPreflight:
    """Create preflight with explicit trust in the frozen test fixture only."""
    return AuthorizedExecutionPreflight(
        trusted_keys={FIXTURE_KEY_ID: FIXTURE_PUBLIC_KEY_HEX},
    )
