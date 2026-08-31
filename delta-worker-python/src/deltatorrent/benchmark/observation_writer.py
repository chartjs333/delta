"""Create-only typed observation publication for Campaign 02 measured runs."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from deltatorrent.benchmark.campaign02 import CampaignExecutionPlan, authorize_execution_class
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.benchmark.evaluators.common import MeasuredEvaluation
from deltatorrent.benchmark.measured_runner import (
    ComponentIdentity,
    RawArtifact,
    ScientificRun,
)
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id


class ObservationWriterError(ValueError):
    """Stable fail-closed observation publication rejection."""


def _fail(code: str) -> ObservationWriterError:
    return ObservationWriterError(code)


def _fsync_directory(path: Path) -> None:
    if os.name != "posix":
        return
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _safe_target(root: Path, target: Path) -> Path:
    root = root.resolve()
    candidate = target.absolute()
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise _fail("OBSERVATION_STORE_PATH_ESCAPE") from exc
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            raise _fail("OBSERVATION_STORE_SYMLINK_FORBIDDEN")
    return candidate


def _publish_create_only(root: Path, target: Path, payload: bytes) -> None:
    target = _safe_target(root, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    _safe_target(root, target.parent)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".candidate.", suffix=".tmp", dir=target.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, target, follow_symlinks=False)
        except FileExistsError:
            if target.is_symlink() or not target.is_file() or target.read_bytes() != payload:
                raise _fail("OBSERVATION_STORE_IMMUTABLE_CONFLICT") from None
            return
        _fsync_directory(target.parent)
    finally:
        temporary.unlink(missing_ok=True)


@dataclass(frozen=True, slots=True)
class PublicationReceipt:
    observation_id: str
    receipt_id: str
    observation_path: Path
    receipt_path: Path
    artifact_ids: tuple[str, ...]


class PrimaryObservationWriter:
    """Accepts typed runner outputs only; raw/manual observation JSON is forbidden."""

    def __init__(self, identity: ComponentIdentity, root: Path) -> None:
        if identity.component != "PRIMARY_OBSERVATION_WRITER":
            raise _fail("OBSERVATION_WRITER_IDENTITY_INVALID")
        self.identity = identity
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def publish_json(self, _value: bytes | dict[str, object]) -> None:
        raise _fail("OBSERVATION_MANUAL_JSON_FORBIDDEN")

    def _stage_artifact(self, artifact: RawArtifact, staging: Path) -> str:
        path = staging / artifact.name
        if path.exists():
            raise _fail("OBSERVATION_STAGING_NAME_DUPLICATE")
        with path.open("xb") as stream:
            stream.write(artifact.data)
            stream.flush()
            os.fsync(stream.fileno())
        raw = path.read_bytes()
        content_id = sha256_content_id(raw)
        if raw != artifact.data or content_id != artifact.content_id:
            raise _fail("OBSERVATION_STAGING_HASH_MISMATCH")
        target = self.root / "artifacts" / content_id.removeprefix("sha256:")
        _publish_create_only(self.root, target, raw)
        return content_id

    def publish(
        self,
        plan: CampaignExecutionPlan,
        authorization: dict[str, Any],
        scientific_run: ScientificRun,
        evaluations: tuple[MeasuredEvaluation, ...],
    ) -> PublicationReceipt:
        authorize_execution_class(authorization, plan)
        if (
            plan.writer_id != self.identity.content_id
            or plan.environment_id != self.identity.environment_id
            or plan.image_id != self.identity.image_id
            or plan.source_commit != self.identity.source_commit
            or plan.source_tree != self.identity.source_tree
            or scientific_run.plan_id != plan.content_id
            or scientific_run.runner_id != plan.runner_id
        ):
            raise _fail("OBSERVATION_WRITER_PLAN_IDENTITY_MISMATCH")
        if len(evaluations) != len(plan.evaluation_profile_ids):
            raise _fail("OBSERVATION_EVALUATION_SET_INCOMPLETE")
        expected = zip(
            plan.dataset_ids,
            plan.evaluation_profile_ids,
            plan.evaluation_implementation_ids,
            evaluations,
            strict=True,
        )
        for dataset_id, profile_id, implementation_id, evaluation in expected:
            context = evaluation.context
            if (
                context.execution_plan_id != plan.content_id
                or context.checkpoint_id != scientific_run.final_checkpoint_id
                or context.model_id != scientific_run.final_checkpoint_id
                or context.tokenizer_id != plan.tokenizer_id
                or context.environment_id != plan.environment_id
                or context.evaluator_profile_id != profile_id
                or context.evaluator_implementation_id != implementation_id
                or context.dataset_id != dataset_id
            ):
                raise _fail("OBSERVATION_EVALUATION_IDENTITY_MISMATCH")
            if canonical_json_bytes(json.loads(evaluation.canonical_bytes)) != (
                evaluation.canonical_bytes
            ):
                raise _fail("OBSERVATION_EVALUATION_NOT_CANONICAL")
        staging_root = self.root / "staging"
        staging_root.mkdir(parents=True, exist_ok=True)
        artifact_ids: list[str] = []
        with tempfile.TemporaryDirectory(prefix="publish-", dir=staging_root) as directory:
            staging = Path(directory)
            for artifact in scientific_run.raw_artifacts:
                artifact_ids.append(self._stage_artifact(artifact, staging))
            for evaluation in evaluations:
                artifact = RawArtifact(
                    name=f"{evaluation.evaluator_id}-{evaluation.content_id[7:23]}.json",
                    media_type=("application/vnd.deltareduce.measured-evaluation+json;version=1"),
                    data=evaluation.canonical_bytes,
                )
                artifact_ids.append(self._stage_artifact(artifact, staging))
        unique_artifact_ids = tuple(sorted(set(artifact_ids)))
        if not unique_artifact_ids:
            raise _fail("OBSERVATION_RAW_ARTIFACTS_MISSING")
        ticket_results = [
            {
                "certificate_ids": list(item.certificate_ids),
                "checkpoint_id": item.checkpoint_id,
                "contribution_id": item.contribution_id,
                "domain_id": item.domain_id,
                "optimizer_steps": item.optimizer_steps,
                "processed_tokens": item.processed_tokens,
                "ticket_id": item.ticket_id,
            }
            for item in scientific_run.ticket_measurements
        ]
        observation = {
            "arm_id": plan.arm_id,
            "benchmark_definition_id": plan.benchmark_definition_id,
            "campaign_id": plan.campaign_id,
            "dataset_ids": list(plan.dataset_ids),
            "definition_attestation_id": plan.definition_attestation_id,
            "environment_id": plan.environment_id,
            "evaluation_ids": [item.content_id for item in evaluations],
            "evaluation_implementation_ids": list(plan.evaluation_implementation_ids),
            "evaluation_runner_id": plan.evaluation_runner_id,
            "execution_authorization_id": plan.execution_authorization_id,
            "execution_class": plan.execution_class,
            "execution_plan_id": plan.content_id,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "hardware_id": plan.hardware_id,
            "image_id": plan.image_id,
            "model_artifact_id": scientific_run.final_checkpoint_id,
            "processed_tokens": scientific_run.processed_tokens,
            "raw_artifact_ids": list(unique_artifact_ids),
            "repetition": plan.repetition,
            "runner_id": plan.runner_id,
            "schema_version": "2.0.0",
            "seed": plan.seed,
            "source_class": (
                "MEASURED_HARDWARE"
                if plan.execution_class == "PRIMARY_MEASURED"
                else "NON_PRIMARY_SMOKE"
            ),
            "source_commit": plan.source_commit,
            "source_tree": plan.source_tree,
            "ticket_results": ticket_results,
            "tokenizer_id": plan.tokenizer_id,
            "type_name": "PRIMARY_RUN_OBSERVATION",
            "workload_id": plan.workload_id,
            "writer_id": plan.writer_id,
        }
        if observation["processed_tokens"] != plan.processed_tokens:
            raise _fail("OBSERVATION_PROCESSED_TOKENS_MISMATCH")
        observation_bytes = canonical_json_bytes(observation)
        observation_id = sha256_content_id(
            b"deltareduce.010.primary-run-observation.v2\0" + observation_bytes
        )
        observation_path = (
            self.root
            / "observations"
            / plan.content_id.removeprefix("sha256:")
            / f"{observation_id.removeprefix('sha256:')}.json"
        )
        _publish_create_only(self.root, observation_path, observation_bytes)
        receipt = {
            "artifact_ids": list(unique_artifact_ids),
            "create_only": True,
            "execution_plan_id": plan.content_id,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "observation_id": observation_id,
            "schema_version": "1.0.0",
            "status": "PUBLISHED",
            "type_name": "PRIMARY_OBSERVATION_RECEIPT",
            "writer_id": self.identity.content_id,
        }
        receipt_bytes = canonical_json_bytes(receipt)
        receipt_id = sha256_content_id(
            b"deltareduce.010.primary-observation-receipt.v1\0" + receipt_bytes
        )
        receipt_path = (
            self.root
            / "receipts"
            / plan.content_id.removeprefix("sha256:")
            / f"{receipt_id.removeprefix('sha256:')}.json"
        )
        _publish_create_only(self.root, receipt_path, receipt_bytes)
        return PublicationReceipt(
            observation_id=observation_id,
            receipt_id=receipt_id,
            observation_path=observation_path,
            receipt_path=receipt_path,
            artifact_ids=unique_artifact_ids,
        )
