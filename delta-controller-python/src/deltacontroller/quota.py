"""Resource grant allocation, concurrency limiting, and quota enforcement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from deltacontroller.errors import QuotaExceededError

DEFAULT_MAX_MEMORY_BYTES = 2 * 1024 * 1024 * 1024  # 2 GiB
CEILING_MAX_MEMORY_BYTES = 8 * 1024 * 1024 * 1024  # 8 GiB
DEFAULT_TIMEOUT_SECONDS = 900  # 15 minutes
MAX_TIMEOUT_SECONDS = 3600  # 1 hour
DEFAULT_MAX_CONCURRENCY = 4  # Max 4 concurrent active workloads


@dataclass(frozen=True)
class ResourceGrants:
    """Immutable resource grants assigned by the Authorization Gate."""

    max_memory_bytes: int
    timeout_seconds: int
    allow_downloads: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_memory_bytes": self.max_memory_bytes,
            "timeout_seconds": self.timeout_seconds,
            "allow_downloads": self.allow_downloads,
        }


class QuotaManager:
    """Manages concurrency limits and allocates policy-bound resource grants."""

    def __init__(
        self,
        max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
        default_memory_bytes: int = DEFAULT_MAX_MEMORY_BYTES,
        ceiling_memory_bytes: int = CEILING_MAX_MEMORY_BYTES,
        default_timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        max_timeout_seconds: int = MAX_TIMEOUT_SECONDS,
        policy_allow_downloads: bool = False,
    ) -> None:
        self.max_concurrency = max_concurrency
        self.default_memory_bytes = default_memory_bytes
        self.ceiling_memory_bytes = ceiling_memory_bytes
        self.default_timeout_seconds = default_timeout_seconds
        self.max_timeout_seconds = max_timeout_seconds
        self.policy_allow_downloads = policy_allow_downloads

    def evaluate_grants(
        self,
        intent_doc: dict[str, Any],
        current_active_count: int,
    ) -> ResourceGrants:
        """Evaluate resource grants and check limits before admitting an execution.

        Raises:
            QuotaExceededError (ERR_QUOTA_EXCEEDED) if concurrency or resource limits are breached.
        """
        if (
            self.default_memory_bytes < 1
            or self.default_memory_bytes > self.ceiling_memory_bytes
            or self.ceiling_memory_bytes > CEILING_MAX_MEMORY_BYTES
        ):
            msg = (
                "Configured memory grant is outside the fail-closed policy bounds: "
                f"default={self.default_memory_bytes}, "
                f"configured_ceiling={self.ceiling_memory_bytes}, "
                f"absolute_ceiling={CEILING_MAX_MEMORY_BYTES}"
            )
            raise QuotaExceededError(
                msg,
                details={
                    "default_memory": self.default_memory_bytes,
                    "configured_ceiling": self.ceiling_memory_bytes,
                    "max_memory": CEILING_MAX_MEMORY_BYTES,
                },
            )

        # 1. Concurrency limit check
        if current_active_count >= self.max_concurrency:
            msg = (
                f"Concurrency limit reached: {current_active_count} active executions "
                f"(maximum allowed: {self.max_concurrency})"
            )
            raise QuotaExceededError(
                msg,
                details={
                    "current_active": current_active_count,
                    "max_concurrency": self.max_concurrency,
                },
            )

        constraints = intent_doc.get("execution_constraints", {})
        requested_timeout = constraints.get("timeout_seconds")

        if requested_timeout is not None:
            if requested_timeout > self.max_timeout_seconds:
                msg = (
                    f"Requested timeout {requested_timeout}s exceeds maximum allowed limit "
                    f"{self.max_timeout_seconds}s"
                )
                raise QuotaExceededError(
                    msg,
                    details={
                        "requested_timeout": requested_timeout,
                        "max_timeout": self.max_timeout_seconds,
                    },
                )
            timeout = requested_timeout
        else:
            timeout = self.default_timeout_seconds

        # Memory allocation
        memory = self.default_memory_bytes

        # Downloads policy: controller unconditionally enforces isolation
        allow_downloads = self.policy_allow_downloads

        return ResourceGrants(
            max_memory_bytes=memory,
            timeout_seconds=timeout,
            allow_downloads=allow_downloads,
        )
