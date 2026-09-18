"""Schema registry and Draft 2020-12 validator loading frozen contract schemas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, ClassVar

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
from referencing import Registry, Resource

from deltacontroller.errors import SchemaValidationError


def _find_contracts_root() -> Path:
    """Find the root contracts directory by searching upwards."""
    cur = Path(__file__).resolve().parent
    for parent in [cur, *cur.parents]:
        candidate = parent / "specs" / "admin-ui" / "step5c-controlled-live-execution" / "contracts"
        if candidate.exists() and (candidate / "schemas").exists():
            return candidate
    raise RuntimeError("Could not find step5c contracts directory in workspace")


class SchemaRegistry:
    """Loads and caches Step 5C JSON schemas from the frozen contracts repository."""

    SCHEMA_FILES: ClassVar[dict[str, str]] = {
        "execution-intent": "execution-intent.schema.json",
        "admission-record": "admission-record.schema.json",
        "authorized-execution": "authorized-execution.schema.json",
        "execution-status": "execution-status.schema.json",
        "preflight-error": "preflight-error.schema.json",
        "receipt-lineage": "execution-receipt-lineage-extension.schema.json",
    }

    def __init__(self, contracts_root: Path | None = None) -> None:
        self.contracts_root = contracts_root or _find_contracts_root()
        self.schemas_dir = self.contracts_root / "schemas"
        self._validators: dict[str, Draft202012Validator] = {}
        self._load_all()

    def _load_all(self) -> None:
        resources = []
        raw_schemas: dict[str, dict[str, Any]] = {}
        for alias, filename in self.SCHEMA_FILES.items():
            schema_path = self.schemas_dir / filename
            if not schema_path.exists():
                raise FileNotFoundError(f"Contract schema not found: {schema_path}")
            with schema_path.open("r", encoding="utf-8") as f:
                schema_doc = json.load(f)
            raw_schemas[alias] = schema_doc
            res = Resource.from_contents(schema_doc)
            resources.append((filename, res))
            if "$id" in schema_doc:
                resources.append((schema_doc["$id"], res))

        registry = Registry().with_resources(resources)
        for alias, schema_doc in raw_schemas.items():
            self._validators[alias] = Draft202012Validator(schema_doc, registry=registry)

    def validate(self, schema_alias: str, document: dict[str, Any]) -> None:
        """Validate a document against a loaded schema; raises typed SchemaValidationError."""
        validator = self._validators.get(schema_alias)
        if validator is None:
            loaded = list(self._validators.keys())
            raise KeyError(f"Unknown schema alias '{schema_alias}'. Loaded: {loaded}")

        errors = list(validator.iter_errors(document))
        if errors:
            first_err = errors[0]
            path = ".".join(str(p) for p in first_err.path) or "<root>"
            formatted_errors = [
                f"{'.'.join(str(p) for p in err.path) or '<root>'}: {err.message}"
                for err in errors[:5]
            ]
            raise SchemaValidationError(
                f"Validation failed for schema '{schema_alias}' at '{path}': {first_err.message}",
                details={
                    "schema": schema_alias,
                    "error_path": path,
                    "error_count": len(errors),
                    "all_errors": formatted_errors,
                },
            )
