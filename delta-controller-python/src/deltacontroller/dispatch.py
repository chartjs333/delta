"""Worker dispatch port and adapters for passing AuthorizedExecution bundles to Zone 3."""

from __future__ import annotations

from typing import Any, Protocol

from deltacontroller.errors import WorkerDispatchFailedError
from deltacontroller.schema import SchemaRegistry


class WorkerDispatchPort(Protocol):
    """Protocol for dispatching an AuthorizedExecution bundle to a worker runtime."""

    def dispatch(self, bundle: dict[str, Any]) -> dict[str, Any]:
        """Dispatch the bundle and return the initial execution status or worker acknowledgment."""
        ...


class MockWorkerDispatchPort:
    """Mock dispatch port recording dispatched bundles for testing and offline development."""

    def __init__(
        self, schema_registry: SchemaRegistry | None = None, auto_complete: bool = False
    ) -> None:
        self.schema_registry = schema_registry or SchemaRegistry()
        self.dispatched_bundles: list[dict[str, Any]] = []
        self.auto_complete = auto_complete

    def dispatch(self, bundle: dict[str, Any]) -> dict[str, Any]:
        # Preflight schema check of the bundle
        try:
            self.schema_registry.validate("authorized-execution", bundle)
        except Exception as exc:
            raise WorkerDispatchFailedError(
                f"Bundle failed authorized-execution schema validation: {exc}"
            ) from exc

        self.dispatched_bundles.append(bundle)
        execution_id = bundle["admission"]["execution_id"]
        intent_id = bundle["intent"]["intent_id"]

        return {
            "dispatched": True,
            "execution_id": execution_id,
            "intent_id": intent_id,
            "status": "RUNNING" if not self.auto_complete else "COMPLETED",
        }
