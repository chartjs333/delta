"""Create-only primary execution plans and fail-closed external runner admission."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from deltatorrent.benchmark.arms import ArmSpec, MetricSample, RunObservation
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID, BenchmarkDefinition
from deltatorrent.benchmark.preregistration import PreregisteredDefinition
from deltatorrent.benchmark.primary import ExecutionPlan, PrimaryRunError, adapter_for
from deltatorrent.benchmark.reconciliation import ReconciliationError, reconcile
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

_CONTENT_ID: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_ID: Final = re.compile(r"^[0-9a-f]{40}$")
_ENVIRONMENT_FIELDS: Final = {
    "abi_descriptor_id",
    "accelerator",
    "compiler_id",
    "dependency_lock_ids",
    "formal_semantics_id",
    "hardware_id",
    "image_id",
    "jdk_id",
    "netty_id",
    "os_id",
    "python_id",
    "schema_version",
    "source_commit",
    "source_tree",
    "time_sync_status",
    "type_name",
}
_OBSERVATION_FIELDS: Final = {
    "execution_plan_id",
    "formal_semantics_id",
    "metric_samples",
    "run_manifest",
    "schema_version",
    "type_name",
}
_RUN_MANIFEST_FIELDS: Final = {
    "arm_id",
    "benchmark_definition_id",
    "bytes_sent",
    "certificate_ids",
    "checkpoint_id",
    "copy_fallback_bytes",
    "domain_ticket_counts",
    "environment_manifest_id",
    "evaluation_artifact_ids",
    "fault_profile_id",
    "formal_semantics_id",
    "gpu_peak_reserved_bytes",
    "gpu_utilization_ppm",
    "host_offload_bytes",
    "model_artifact_id",
    "namespace",
    "network_profile_id",
    "output_ids",
    "parent_checkpoint_id",
    "phase_latencies",
    "processed_tokens",
    "protocol_hash",
    "repetition",
    "schema_version",
    "seed",
    "terminal_outcome",
    "ticket_plan_id",
    "total_us",
    "type_name",
    "useful_compute_us",
    "zero_copy_eligible",
    "zero_copy_hits",
}


class PrimaryExecutorError(ValueError):
    """Stable planning, runner, or measured-observation rejection."""


def _fail(code: str) -> PrimaryExecutorError:
    return PrimaryExecutorError(code)


def _integer(value: object, code: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise _fail(code)
    return value


def _string(value: object, code: str) -> str:
    if not isinstance(value, str) or not value:
        raise _fail(code)
    return value


def _content_id(value: object, code: str) -> str:
    result = _string(value, code)
    if _CONTENT_ID.fullmatch(result) is None:
        raise _fail(code)
    return result


def _content_ids(value: object, code: str, *, minimum: int = 0) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) < minimum:
        raise _fail(code)
    result = tuple(_content_id(item, code) for item in value)
    if len(set(result)) != len(result):
        raise _fail(f"{code}_DUPLICATE")
    return result


def _canonical_object(path: Path, code: str) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _fail(code) from exc
    if not isinstance(value, dict) or canonical_json_bytes(value) != raw:
        raise _fail(code)
    return value, raw


@dataclass(frozen=True, slots=True)
class PrimaryEnvironment:
    raw: dict[str, Any]
    canonical_bytes: bytes

    @property
    def content_id(self) -> str:
        return sha256_content_id(self.canonical_bytes)

    @classmethod
    def load(cls, path: Path, definition: BenchmarkDefinition) -> PrimaryEnvironment:
        value, raw = _canonical_object(path, "PRIMARY_ENVIRONMENT_INVALID")
        if (
            set(value) != _ENVIRONMENT_FIELDS
            or value.get("type_name") != "ENVIRONMENT_MANIFEST"
            or value.get("schema_version") != "1.0.0"
            or value.get("formal_semantics_id") != FORMAL_SEMANTICS_ID
        ):
            raise _fail("PRIMARY_ENVIRONMENT_INVALID")
        for field in (
            "abi_descriptor_id",
            "compiler_id",
            "hardware_id",
            "image_id",
            "jdk_id",
            "netty_id",
            "os_id",
            "python_id",
        ):
            _content_id(value.get(field), "PRIMARY_ENVIRONMENT_IDENTITY_INVALID")
        dependencies = _content_ids(
            value.get("dependency_lock_ids"),
            "PRIMARY_ENVIRONMENT_DEPENDENCIES_INVALID",
            minimum=1,
        )
        source_commit = _string(value.get("source_commit"), "PRIMARY_ENVIRONMENT_SOURCE_INVALID")
        source_tree = _string(value.get("source_tree"), "PRIMARY_ENVIRONMENT_SOURCE_INVALID")
        if _COMMIT_ID.fullmatch(source_commit) is None or _COMMIT_ID.fullmatch(source_tree) is None:
            raise _fail("PRIMARY_ENVIRONMENT_SOURCE_INVALID")
        if value.get("time_sync_status") not in {"BOUNDED", "NOT_APPLICABLE"}:
            raise _fail("PRIMARY_ENVIRONMENT_TIME_SYNC_INVALID")
        _string(value.get("accelerator"), "PRIMARY_ENVIRONMENT_ACCELERATOR_INVALID")
        expected = {
            "abi_descriptor_id": definition.raw["abi_descriptor_id"],
            "compiler_id": definition.raw["compiler_profile_id"],
            "image_id": definition.raw["image_id"],
            "jdk_id": definition.raw["jdk_profile_id"],
            "netty_id": definition.raw["netty_profile_id"],
            "python_id": definition.raw["python_profile_id"],
            "source_commit": definition.source_commit,
            "source_tree": definition.source_tree,
        }
        if any(value.get(field) != wanted for field, wanted in expected.items()):
            raise _fail("PRIMARY_ENVIRONMENT_DEFINITION_MISMATCH")
        if dependencies != tuple(definition.raw["dependency_lock_ids"]):
            raise _fail("PRIMARY_ENVIRONMENT_DEFINITION_MISMATCH")
        return cls(value, raw)


@dataclass(frozen=True, slots=True)
class PrimaryExecutionSet:
    definition: BenchmarkDefinition
    attestation_id: str
    environment: PrimaryEnvironment
    plans: tuple[ExecutionPlan, ...]

    @property
    def definition_id(self) -> str:
        return self.definition.content_id

    @property
    def index(self) -> dict[str, object]:
        return {
            "benchmark_definition_id": self.definition_id,
            "definition_attestation_id": self.attestation_id,
            "environment_manifest_id": self.environment.content_id,
            "execution_class": "PRIMARY_MEASURED_REQUIRED",
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "limitations": [
                "PLANS_ARE_NOT_PRIMARY_EVIDENCE",
                "WAN_AND_FAULT_EVIDENCE_REQUIRES_SEPARATE_MEASURED_SCENARIOS",
            ],
            "plan_ids": [item.content_id for item in self.plans],
            "schema_version": "1.0.0",
            "status": "PLANNED_NOT_EXECUTED",
            "type_name": "PRIMARY_EXECUTION_INDEX",
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(canonical_json_bytes(self.index))


def build_execution_set(
    preregistration: PreregisteredDefinition,
    arms: tuple[ArmSpec, ...],
    environment: PrimaryEnvironment,
) -> PrimaryExecutionSet:
    definition = preregistration.definition
    if not definition.primary:
        raise _fail("PRIMARY_EXECUTOR_REQUIRES_PRIMARY_DEFINITION")
    if tuple(item.content_id for item in arms) != definition.arm_ids:
        raise _fail("PRIMARY_EXECUTOR_ARM_SET_MISMATCH")
    if any(not item.mandatory for item in arms):
        raise _fail("PRIMARY_EXECUTOR_OPTIONAL_ARM_FORBIDDEN")
    profiles = {item.deployment_profile for item in arms}
    if not {"EMBEDDED_FFM", "ISOLATED_SIDECAR"} <= profiles:
        raise _fail("PRIMARY_EXECUTOR_ISOLATION_COVERAGE_MISSING")
    try:
        plans = tuple(
            adapter_for(arm).plan(
                definition,
                arm,
                environment_manifest_id=environment.content_id,
                network_profile_id=definition.network_profile_ids[0],
                fault_profile_id=definition.fault_profile_ids[0],
                seed=seed,
                repetition=repetition,
            )
            for arm in arms
            for repetition, seed in enumerate(definition.seeds, start=1)
        )
    except PrimaryRunError as exc:
        raise _fail(str(exc)) from exc
    if len({item.content_id for item in plans}) != len(plans):
        raise _fail("PRIMARY_EXECUTION_PLAN_DUPLICATE")
    attestation_id = sha256_content_id(canonical_json_bytes(preregistration.attestation.to_dict()))
    return PrimaryExecutionSet(definition, attestation_id, environment, plans)


def plan_record(plan: ExecutionPlan) -> dict[str, object]:
    return {
        "content_id": plan.content_id,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "schema_version": "1.0.0",
        "type_name": "PRIMARY_EXECUTION_PLAN",
        "value": plan.document,
    }


def observation_record(plan: ExecutionPlan, observation: RunObservation) -> dict[str, object]:
    admitted = _admit_observation(plan, observation)
    return {
        "execution_plan_id": plan.content_id,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "metric_samples": [
            {"metric_id": item.metric_id, "unit": item.unit, "value": item.value}
            for item in admitted.samples
        ],
        "run_manifest": admitted.manifest,
        "schema_version": "1.0.0",
        "type_name": "PRIMARY_RUN_OBSERVATION",
    }


def _admit_observation(plan: ExecutionPlan, observation: RunObservation) -> RunObservation:
    try:
        return adapter_for(plan.arm).admit(plan, observation)
    except PrimaryRunError as exc:
        raise _fail(str(exc)) from exc


def _metric_samples(value: object) -> tuple[MetricSample, ...]:
    if not isinstance(value, list) or not value:
        raise _fail("PRIMARY_OBSERVATION_METRICS_INVALID")
    result: list[MetricSample] = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"metric_id", "unit", "value"}:
            raise _fail("PRIMARY_OBSERVATION_METRICS_INVALID")
        result.append(
            MetricSample(
                _string(item.get("metric_id"), "PRIMARY_OBSERVATION_METRICS_INVALID"),
                _integer(item.get("value"), "PRIMARY_OBSERVATION_METRICS_INVALID"),
                _string(item.get("unit"), "PRIMARY_OBSERVATION_METRICS_INVALID"),
            )
        )
    if len({item.metric_id for item in result}) != len(result):
        raise _fail("PRIMARY_OBSERVATION_METRICS_DUPLICATE")
    return tuple(result)


def _domain_counts(value: object) -> tuple[tuple[str, int], ...]:
    if not isinstance(value, list) or not value:
        raise _fail("PRIMARY_OBSERVATION_DOMAINS_INVALID")
    result: list[tuple[str, int]] = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"count", "domain_id"}:
            raise _fail("PRIMARY_OBSERVATION_DOMAINS_INVALID")
        result.append(
            (
                _string(item.get("domain_id"), "PRIMARY_OBSERVATION_DOMAINS_INVALID"),
                _integer(item.get("count"), "PRIMARY_OBSERVATION_DOMAINS_INVALID"),
            )
        )
    if len({domain for domain, _ in result}) != len(result):
        raise _fail("PRIMARY_OBSERVATION_DOMAINS_DUPLICATE")
    return tuple(result)


def _phase_latencies(value: object) -> tuple[tuple[str, int], ...]:
    if not isinstance(value, list):
        raise _fail("PRIMARY_OBSERVATION_PHASES_INVALID")
    result: list[tuple[str, int]] = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"microseconds", "phase_id"}:
            raise _fail("PRIMARY_OBSERVATION_PHASES_INVALID")
        result.append(
            (
                _string(item.get("phase_id"), "PRIMARY_OBSERVATION_PHASES_INVALID"),
                _integer(item.get("microseconds"), "PRIMARY_OBSERVATION_PHASES_INVALID"),
            )
        )
    if len({phase for phase, _ in result}) != len(result):
        raise _fail("PRIMARY_OBSERVATION_PHASES_DUPLICATE")
    return tuple(result)


def parse_observation(
    path: Path,
    plan: ExecutionPlan,
) -> tuple[RunObservation, bytes]:
    value, raw = _canonical_object(path, "PRIMARY_OBSERVATION_INVALID")
    if (
        set(value) != _OBSERVATION_FIELDS
        or value.get("type_name") != "PRIMARY_RUN_OBSERVATION"
        or value.get("schema_version") != "1.0.0"
        or value.get("formal_semantics_id") != FORMAL_SEMANTICS_ID
        or value.get("execution_plan_id") != plan.content_id
    ):
        raise _fail("PRIMARY_OBSERVATION_INVALID")
    manifest = value.get("run_manifest")
    if (
        not isinstance(manifest, dict)
        or set(manifest) != _RUN_MANIFEST_FIELDS
        or manifest.get("type_name") != "RUN_MANIFEST"
        or manifest.get("schema_version") != "1.0.0"
        or manifest.get("formal_semantics_id") != FORMAL_SEMANTICS_ID
    ):
        raise _fail("PRIMARY_RUN_MANIFEST_INVALID")
    try:
        observation = RunObservation(
            definition_id=_content_id(
                manifest.get("benchmark_definition_id"), "PRIMARY_RUN_MANIFEST_INVALID"
            ),
            arm=plan.arm,
            environment_manifest_id=_content_id(
                manifest.get("environment_manifest_id"), "PRIMARY_RUN_MANIFEST_INVALID"
            ),
            network_profile_id=_content_id(
                manifest.get("network_profile_id"), "PRIMARY_RUN_MANIFEST_INVALID"
            ),
            fault_profile_id=_content_id(
                manifest.get("fault_profile_id"), "PRIMARY_RUN_MANIFEST_INVALID"
            ),
            seed=_integer(manifest.get("seed"), "PRIMARY_RUN_MANIFEST_INVALID"),
            repetition=_integer(
                manifest.get("repetition"), "PRIMARY_RUN_MANIFEST_INVALID", minimum=1
            ),
            processed_tokens=_integer(
                manifest.get("processed_tokens"), "PRIMARY_RUN_MANIFEST_INVALID"
            ),
            domain_ticket_counts=_domain_counts(manifest.get("domain_ticket_counts")),
            terminal_outcome=_string(
                manifest.get("terminal_outcome"), "PRIMARY_RUN_MANIFEST_INVALID"
            ),
            protocol_hash=_content_id(
                manifest.get("protocol_hash"), "PRIMARY_RUN_MANIFEST_INVALID"
            ),
            checkpoint_id=_content_id(
                manifest.get("checkpoint_id"), "PRIMARY_RUN_MANIFEST_INVALID"
            ),
            ticket_plan_id=_content_id(
                manifest.get("ticket_plan_id"), "PRIMARY_RUN_MANIFEST_INVALID"
            ),
            parent_checkpoint_id=_content_id(
                manifest.get("parent_checkpoint_id"), "PRIMARY_RUN_MANIFEST_INVALID"
            ),
            certificate_ids=_content_ids(
                manifest.get("certificate_ids"), "PRIMARY_RUN_MANIFEST_INVALID"
            ),
            model_artifact_id=_content_id(
                manifest.get("model_artifact_id"), "PRIMARY_RUN_MANIFEST_INVALID"
            ),
            evaluation_artifact_ids=_content_ids(
                manifest.get("evaluation_artifact_ids"),
                "PRIMARY_RUN_MANIFEST_INVALID",
                minimum=1,
            ),
            samples=_metric_samples(value.get("metric_samples")),
            phase_latencies_us=_phase_latencies(manifest.get("phase_latencies")),
            bytes_sent=_integer(manifest.get("bytes_sent"), "PRIMARY_RUN_MANIFEST_INVALID"),
            useful_compute_us=_integer(
                manifest.get("useful_compute_us"), "PRIMARY_RUN_MANIFEST_INVALID"
            ),
            total_us=_integer(manifest.get("total_us"), "PRIMARY_RUN_MANIFEST_INVALID"),
            zero_copy_eligible=_integer(
                manifest.get("zero_copy_eligible"), "PRIMARY_RUN_MANIFEST_INVALID"
            ),
            zero_copy_hits=_integer(manifest.get("zero_copy_hits"), "PRIMARY_RUN_MANIFEST_INVALID"),
            copy_fallback_bytes=_integer(
                manifest.get("copy_fallback_bytes"), "PRIMARY_RUN_MANIFEST_INVALID"
            ),
            gpu_utilization_ppm=_integer(
                manifest.get("gpu_utilization_ppm"), "PRIMARY_RUN_MANIFEST_INVALID"
            ),
            gpu_peak_reserved_bytes=_integer(
                manifest.get("gpu_peak_reserved_bytes"), "PRIMARY_RUN_MANIFEST_INVALID"
            ),
            host_offload_bytes=_integer(
                manifest.get("host_offload_bytes"), "PRIMARY_RUN_MANIFEST_INVALID"
            ),
        )
    except ValueError as exc:
        raise _fail(str(exc)) from exc
    admitted = _admit_observation(plan, observation)
    if manifest.get("arm_id") != plan.arm.content_id or manifest != admitted.manifest:
        raise _fail("PRIMARY_RUN_MANIFEST_DERIVATION_MISMATCH")
    return admitted, raw


def _write_create_only(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        try:
            existing = path.read_bytes()
        except OSError as exc:
            raise _fail("PRIMARY_EXECUTION_STORE_READ_FAILED") from exc
        if existing != value:
            raise _fail("PRIMARY_EXECUTION_IMMUTABLE_CONFLICT") from None
        return
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


class PrimaryExecutionStore:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def stage(self, execution: PrimaryExecutionSet) -> Path:
        _write_create_only(
            self.root / "environment-manifest.json", execution.environment.canonical_bytes
        )
        for plan in execution.plans:
            digest = plan.content_id.removeprefix("sha256:")
            _write_create_only(
                self.root / "plans" / f"{digest}.json",
                canonical_json_bytes(plan_record(plan)),
            )
        target = self.root / "execution-index.json"
        _write_create_only(target, canonical_json_bytes(execution.index))
        return target

    def plan_path(self, plan: ExecutionPlan) -> Path:
        return self.root / "plans" / f"{plan.content_id.removeprefix('sha256:')}.json"

    def observation_path(self, plan: ExecutionPlan) -> Path:
        return self.root / "runs" / plan.content_id.removeprefix("sha256:") / "observation.json"

    def admit_file(self, plan: ExecutionPlan, path: Path) -> RunObservation:
        observation, raw = parse_observation(path, plan)
        _write_create_only(self.observation_path(plan), raw)
        return observation

    def collect(
        self,
        execution: PrimaryExecutionSet,
        paths: tuple[Path, ...],
    ) -> tuple[RunObservation, ...]:
        self.stage(execution)
        by_id = {plan.content_id: plan for plan in execution.plans}
        collected: list[RunObservation] = []
        seen: set[str] = set()
        for path in paths:
            value, _ = _canonical_object(path, "PRIMARY_OBSERVATION_INVALID")
            plan_id = _content_id(
                value.get("execution_plan_id"), "PRIMARY_OBSERVATION_PLAN_INVALID"
            )
            if plan_id in seen:
                raise _fail("PRIMARY_OBSERVATION_PLAN_DUPLICATE")
            seen.add(plan_id)
            try:
                plan = by_id[plan_id]
            except KeyError as exc:
                raise _fail("PRIMARY_OBSERVATION_PLAN_UNKNOWN") from exc
            collected.append(self.admit_file(plan, path))
        return tuple(collected)

    def load_complete(self, execution: PrimaryExecutionSet) -> tuple[RunObservation, ...]:
        self.stage(execution)
        runs: list[RunObservation] = []
        for plan in execution.plans:
            path = self.observation_path(plan)
            if not path.is_file():
                raise _fail("PRIMARY_RUN_SET_INCOMPLETE")
            observation, _ = parse_observation(path, plan)
            runs.append(observation)
        try:
            reconcile(execution.definition, tuple(runs))
        except ReconciliationError as exc:
            raise _fail(str(exc)) from exc
        return tuple(runs)

    def execute_plan(
        self,
        plan: ExecutionPlan,
        runner: tuple[str, ...],
        *,
        timeout_seconds: int,
    ) -> RunObservation:
        if not runner or any(not item for item in runner):
            raise _fail("PRIMARY_RUNNER_COMMAND_INVALID")
        if timeout_seconds < 1:
            raise _fail("PRIMARY_RUNNER_TIMEOUT_INVALID")
        plan_path = self.plan_path(plan)
        if not plan_path.is_file():
            raise _fail("PRIMARY_EXECUTION_PLAN_NOT_STAGED")
        verify_plan_record(plan_path, plan)
        existing = self.observation_path(plan)
        if existing.is_file():
            observation, _ = parse_observation(existing, plan)
            return observation
        run_dir = existing.parent
        run_dir.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".observation.", suffix=".tmp", dir=run_dir
        )
        os.close(descriptor)
        temporary = Path(temporary_name)
        temporary.unlink(missing_ok=True)
        try:
            try:
                process = subprocess.run(
                    (*runner, str(plan_path), str(temporary)),
                    capture_output=True,
                    check=False,
                    timeout=timeout_seconds,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise _fail("PRIMARY_RUNNER_EXECUTION_FAILED") from exc
            if process.returncode != 0:
                raise _fail(f"PRIMARY_RUNNER_EXIT_{process.returncode}")
            if not temporary.is_file():
                raise _fail("PRIMARY_RUNNER_OBSERVATION_MISSING")
            return self.admit_file(plan, temporary)
        finally:
            temporary.unlink(missing_ok=True)

    def execute_all(
        self,
        execution: PrimaryExecutionSet,
        runner: tuple[str, ...],
        *,
        timeout_seconds: int,
    ) -> tuple[RunObservation, ...]:
        self.stage(execution)
        return tuple(
            self.execute_plan(plan, runner, timeout_seconds=timeout_seconds)
            for plan in execution.plans
        )


def write_observation(path: Path, plan: ExecutionPlan, observation: RunObservation) -> None:
    """Runner helper used by trusted adapters to emit exactly one canonical observation."""
    _write_create_only(path, canonical_json_bytes(observation_record(plan, observation)))


def verify_plan_record(path: Path, plan: ExecutionPlan) -> str:
    value, raw = _canonical_object(path, "PRIMARY_EXECUTION_PLAN_INVALID")
    if value != plan_record(plan) or sha256_content_id(
        canonical_json_bytes(value)
    ) != sha256_content_id(raw):
        raise _fail("PRIMARY_EXECUTION_PLAN_INVALID")
    return plan.content_id


def hash_file(path: Path) -> str:
    """Content identity for runner-side raw artifacts without interpreting their bytes."""
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise _fail("PRIMARY_RUNNER_ARTIFACT_UNREADABLE") from exc
    return f"sha256:{digest}"
