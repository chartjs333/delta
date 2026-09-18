"""T015: Resource grants, concurrency limits, and quota enforcement."""

from __future__ import annotations

import pytest
from deltacontroller.errors import QuotaExceededError
from deltacontroller.quota import CEILING_MAX_MEMORY_BYTES, QuotaManager


def test_concurrency_limit_rejected() -> None:
    manager = QuotaManager(max_concurrency=2)
    intent = {"execution_constraints": {"timeout_seconds": 300}}

    # When active count reaches max_concurrency
    with pytest.raises(QuotaExceededError) as exc_info:
        manager.evaluate_grants(intent, current_active_count=2)
    assert exc_info.value.code == "ERR_QUOTA_EXCEEDED"


def test_timeout_exceeding_max_rejected() -> None:
    manager = QuotaManager(max_timeout_seconds=1800)
    intent = {"execution_constraints": {"timeout_seconds": 3600}}

    with pytest.raises(QuotaExceededError) as exc_info:
        manager.evaluate_grants(intent, current_active_count=0)
    assert exc_info.value.code == "ERR_QUOTA_EXCEEDED"


def test_allow_downloads_unconditionally_denied() -> None:
    manager = QuotaManager(policy_allow_downloads=False)
    # Intent maliciously requests allow_downloads=True
    intent = {
        "execution_constraints": {
            "requested_allow_downloads": True,
            "timeout_seconds": 600,
        }
    }
    grants = manager.evaluate_grants(intent, current_active_count=0)
    # Gate policy strictly overrides and denies downloads
    assert grants.allow_downloads is False
    assert grants.timeout_seconds == 600


def test_default_memory_above_absolute_ceiling_rejected() -> None:
    manager = QuotaManager(default_memory_bytes=CEILING_MAX_MEMORY_BYTES + 1)

    with pytest.raises(QuotaExceededError) as exc_info:
        manager.evaluate_grants({}, current_active_count=0)

    assert exc_info.value.details["max_memory"] == CEILING_MAX_MEMORY_BYTES


def test_raised_configured_ceiling_cannot_bypass_absolute_ceiling() -> None:
    manager = QuotaManager(
        default_memory_bytes=CEILING_MAX_MEMORY_BYTES + 1,
        ceiling_memory_bytes=CEILING_MAX_MEMORY_BYTES + 1,
    )

    with pytest.raises(QuotaExceededError):
        manager.evaluate_grants({}, current_active_count=0)


def test_default_memory_above_lower_configured_ceiling_rejected() -> None:
    manager = QuotaManager(
        default_memory_bytes=2 * 1024,
        ceiling_memory_bytes=1024,
    )

    with pytest.raises(QuotaExceededError):
        manager.evaluate_grants({}, current_active_count=0)


def test_memory_at_absolute_ceiling_is_allowed() -> None:
    manager = QuotaManager(
        default_memory_bytes=CEILING_MAX_MEMORY_BYTES,
        ceiling_memory_bytes=CEILING_MAX_MEMORY_BYTES,
    )

    grants = manager.evaluate_grants({}, current_active_count=0)

    assert grants.max_memory_bytes == CEILING_MAX_MEMORY_BYTES
