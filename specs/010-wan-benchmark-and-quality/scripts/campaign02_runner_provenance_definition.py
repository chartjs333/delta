"""Construct the immutable post-PR19 Campaign 02 Definition v4 package."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[3]
SCRIPTS: Final = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / "delta-worker-python/src"))

import campaign02_runner_definition as previous  # noqa: E402
from deltatorrent.benchmark.campaign02_binding import (  # noqa: E402
    QualifiedRuntimeLineage,
)
from deltatorrent.benchmark.campaign02_execution_identities import (  # noqa: E402
    StageExecutionIdentityManifest,
)
from deltatorrent.benchmark.definition import (  # noqa: E402
    FORMAL_SEMANTICS_ID,
    BenchmarkDefinition,
)
from deltatorrent.protocol.canonical import (  # noqa: E402
    canonical_json_bytes,
    sha256_content_id,
)

QUALIFIED_SOURCE: Final = "b97fd541a7ef7f100b8ff1ccf4ced61aa2880de2"
QUALIFIED_TREE: Final = "354bd4cae74e568b8489b667aeb4e88f36de57e0"
SUPERSEDED_DEFINITION_ID: Final = (
    "sha256:3844edbdcfc402ca3fbd54f9a2e4dfab965a8a7280a6ccd3dad70611e88ee803"
)
PR19_REVIEWED_HEAD: Final = "c9a2da487eb6637200e45dbbd56d84b30704d38e"
PR17_MERGE: Final = "881301d8443c667a478617cc663d1450aee9777a"
CONFIG: Final = ROOT / "configs/benchmark/campaign-02"
REPORTS: Final = ROOT / "reports/benchmark/campaigns/campaign-02"
EVIDENCE: Final = ROOT / "specs/010-wan-benchmark-and-quality/evidence"

EXACT_PATH: Final = EVIDENCE / "campaign-02-runner-provenance-exact-source-qualification.json"
HARDWARE_PATH: Final = EVIDENCE / "campaign-02-runner-provenance-hardware-qualification.json"
CI_RECEIPT_PATH: Final = EVIDENCE / "campaign-02-runner-provenance-exact-source-ci-receipt.json"
DATASETS_PATH: Final = CONFIG / "definition-dataset-manifest-v3.json"
METRICS_PATH: Final = CONFIG / "definition-metrics-v4.json"
IDENTITIES_PATH: Final = CONFIG / "stage-execution-identities-v3.json"
LINEAGE_PATH: Final = CONFIG / "qualified-runtime-lineage-v4.json"
DEFINITION_PATH: Final = CONFIG / "definition-v4.json"
AUTHORIZATION_PATH: Final = REPORTS / "definition-construction-authorization-v4.json"
METHODOLOGY_PATH: Final = REPORTS / "methodology-diff-v4.json"
READINESS_PATH: Final = REPORTS / "definition-readiness-v4.json"
SUPERSESSION_RESOLUTION_PATH: Final = (
    REPORTS / "definition-supersession-executable-provenance-resolution.json"
)
ORIGINAL_SUPERSESSION_PATH: Final = REPORTS / "definition-supersession-executable-provenance.json"

previous.legacy.QUALIFIED_SOURCE = QUALIFIED_SOURCE
previous.legacy.QUALIFIED_TREE = QUALIFIED_TREE
previous.legacy.REMEDIATION_MERGE = PR17_MERGE


class RunnerProvenanceDefinitionError(RuntimeError):
    """Stable fail-closed Definition v4 construction error."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RunnerProvenanceDefinitionError(code)


def load_document(path: Path) -> dict[str, object]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RunnerProvenanceDefinitionError(f"DOCUMENT_INVALID:{path.name}") from exc
    require(
        isinstance(value, dict)
        and raw in {canonical_json_bytes(value), canonical_json_bytes(value) + b"\n"},
        f"DOCUMENT_NONCANONICAL:{path.name}",
    )
    return value


def raw_id(path: Path) -> str:
    return sha256_content_id(path.read_bytes())


def tracked_bytes(commit: str, path: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{path}"),
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout


def verify_historical_identity_files(
    identities: StageExecutionIdentityManifest, identity_name: str
) -> None:
    identity = identities.identity(identity_name)
    entries: list[object] = []
    for field in ("executable_hashes", "workflow_hashes"):
        value = identity.value.get(field)
        require(isinstance(value, list), "DEFINITION_V4_IDENTITY_HASH_SET_INVALID")
        entries.extend(value)
    require(bool(entries), "DEFINITION_V4_IDENTITY_HASH_SET_INVALID")
    for item in entries:
        require(
            isinstance(item, dict)
            and isinstance(item.get("path"), str)
            and isinstance(item.get("content_id"), str),
            "DEFINITION_V4_IDENTITY_HASH_ENTRY_INVALID",
        )
        assert isinstance(item, dict)
        path = str(item["path"])
        require(
            sha256_content_id(tracked_bytes(QUALIFIED_SOURCE, path)) == item["content_id"],
            f"DEFINITION_V4_HISTORICAL_SOURCE_DRIFT:{path}",
        )


def object_id(value: object, domain: str) -> str:
    return sha256_content_id(domain.encode() + b"\0" + canonical_json_bytes(value))


def source_artifact_id(exact: dict[str, object], path: str) -> str:
    source = exact.get("source")
    require(isinstance(source, dict), "EXACT_SOURCE_MISSING")
    artifacts = source.get("artifacts")
    require(isinstance(artifacts, list), "EXACT_SOURCE_ARTIFACTS_MISSING")
    matches = [item for item in artifacts if isinstance(item, dict) and item.get("path") == path]
    require(len(matches) == 1, f"SOURCE_ARTIFACT_MISSING:{path}")
    content_id = matches[0].get("sha256")
    require(isinstance(content_id, str), f"SOURCE_ARTIFACT_ID_INVALID:{path}")
    return content_id


def qualification() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    exact = load_document(EXACT_PATH)
    hardware = load_document(HARDWARE_PATH)
    receipt = load_document(CI_RECEIPT_PATH)
    expected_source = {"commit": QUALIFIED_SOURCE, "tree": QUALIFIED_TREE}
    require(
        exact.get("status") == "PASS"
        and hardware.get("status") == "PASS"
        and receipt.get("status") == "PASS"
        and exact.get("source", {}).get("commit") == QUALIFIED_SOURCE  # type: ignore[union-attr]
        and exact.get("source", {}).get("tree") == QUALIFIED_TREE  # type: ignore[union-attr]
        and hardware.get("source") == expected_source
        and receipt.get("source") == expected_source,
        "RUNNER_PROVENANCE_QUALIFICATION_NOT_PASS",
    )
    require(
        receipt.get("exact_source_qualification_id") == raw_id(EXACT_PATH)
        and receipt.get("hardware_qualification_id") == raw_id(HARDWARE_PATH)
        and receipt.get("primary_execution_authorized") is False
        and receipt.get("primary_scientific_execution_count") == 0
        and receipt.get("scientific_observations_created") is False,
        "RUNNER_PROVENANCE_QUALIFICATION_RECEIPT_INVALID",
    )
    return exact, hardware, receipt


def wrapped_identity(domain: str, value: dict[str, object]) -> dict[str, object]:
    return {
        "content_id": object_id(value, domain),
        "identity_domain": domain,
        "value": value,
    }


def stage_identities(exact: dict[str, object]) -> StageExecutionIdentityManifest:
    gpu = exact.get("gpu_environment")
    components = exact.get("components")
    require(isinstance(gpu, dict), "GPU_ENVIRONMENT_MISSING")
    require(isinstance(components, dict), "QUALIFIED_COMPONENTS_MISSING")

    def hashes(*paths: str) -> list[dict[str, str]]:
        return [{"content_id": source_artifact_id(exact, path), "path": path} for path in paths]

    def implementation_id(value: dict[str, object]) -> str:
        implementation = {
            "entrypoints": value.get("entrypoints"),
            "executable_hashes": value.get("executable_hashes"),
            "workflow_hashes": value.get("workflow_hashes"),
        }
        return object_id(implementation, "deltareduce.010.campaign02-stage-implementation.v1")

    def qualified_component(name: str) -> dict[str, object]:
        item = components.get(name)
        require(isinstance(item, dict), f"QUALIFIED_COMPONENT_MISSING:{name}")
        value = item.get("value")
        content_id = item.get("content_id")
        require(
            isinstance(value, dict)
            and isinstance(content_id, str)
            and object_id(value, "deltareduce.010.primary-component.v1") == content_id,
            f"QUALIFIED_COMPONENT_INVALID:{name}",
        )
        return {
            "content_id": content_id,
            "identity_domain": "deltareduce.010.primary-component.v1",
            "value": value,
        }

    common = {
        "campaign_id": "campaign-02",
        "environment_id": gpu["environment_id"],
        "execution_authorized": False,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "hardware_id": gpu["hardware_id"],
        "image_id": gpu["image_id"],
        "schema_version": "3.0.0",
        "source_commit": QUALIFIED_SOURCE,
        "source_tree": QUALIFIED_TREE,
    }
    exactness: dict[str, object] = {
        **common,
        "allowed_role": "EXACTNESS_RUNNER",
        "entrypoints": ["deltatorrent.benchmark.campaign02_exactness.run_stage_a"],
        "executable_hashes": hashes(
            "delta-worker-python/src/deltatorrent/benchmark/campaign02.py",
            "delta-worker-python/src/deltatorrent/benchmark/campaign02_binding.py",
            "delta-worker-python/src/deltatorrent/benchmark/campaign02_exactness.py",
            "delta-worker-python/src/deltatorrent/benchmark/campaign02_execution_identities.py",
            "delta-worker-python/src/deltatorrent/benchmark/campaign02_stage_a_evidence.py",
            "delta-worker-python/src/deltatorrent/benchmark/campaign02_stage_execution.py",
            "delta-worker-python/src/deltatorrent/benchmark/stage_authorization.py",
            "specs/010-wan-benchmark-and-quality/scripts/campaign02_stage_a_control.py",
        ),
        "implementation_class": (
            "deltatorrent.benchmark.campaign02_exactness.Campaign02ExactnessEvidenceRunner"
        ),
        "role": "EXACTNESS_RUNNER",
        "source_class": "MEASURED_CI_WORKFLOW",
        "workflow_default_ref": "refs/heads/main",
        "workflow_hashes": hashes(".github/workflows/benchmark-campaign02-stage-a.yml"),
        "workflow_path": ".github/workflows/benchmark-campaign02-stage-a.yml",
        "workflow_repository": "chartjs333/delta",
    }
    exactness["implementation_id"] = implementation_id(exactness)
    network: dict[str, object] = {
        **common,
        "allowed_role": "NETWORK_FAULT_RUNNER",
        "entrypoints": ["deltatorrent.benchmark.campaign02_network_fault.run_stage_c"],
        "executable_hashes": hashes(
            "delta-worker-python/src/deltatorrent/benchmark/campaign02.py",
            "delta-worker-python/src/deltatorrent/benchmark/campaign02_binding.py",
            "delta-worker-python/src/deltatorrent/benchmark/campaign02_execution_identities.py",
            "delta-worker-python/src/deltatorrent/benchmark/campaign02_network_fault.py",
            "delta-worker-python/src/deltatorrent/benchmark/campaign02_stage_execution.py",
            "delta-worker-python/src/deltatorrent/benchmark/fault_profiles.py",
            "delta-worker-python/src/deltatorrent/benchmark/network_profiles.py",
            "delta-worker-python/src/deltatorrent/benchmark/stage_authorization.py",
        ),
        "implementation_class": (
            "deltatorrent.benchmark.campaign02_network_fault.Campaign02NetworkFaultRunner"
        ),
        "role": "NETWORK_FAULT_RUNNER",
        "source_class": "MEASURED_HARDWARE",
        "workflow_hashes": [],
    }
    network["implementation_id"] = implementation_id(network)
    exactness_item = wrapped_identity(
        "deltareduce.010.campaign02-stage-role-identity.v3", exactness
    )
    network_item = wrapped_identity("deltareduce.010.campaign02-stage-role-identity.v3", network)
    scientific_item = qualified_component("scientific_runner")
    evaluation_item = qualified_component("evaluation_runner")
    writer_item = qualified_component("observation_writer")
    multi_role = {
        **common,
        "allowed_roles": ["EXACTNESS_RUNNER", "NETWORK_FAULT_RUNNER", "SCIENTIFIC_RUNNER"],
        "role_identity_ids": {
            "EXACTNESS_RUNNER": exactness_item["content_id"],
            "NETWORK_FAULT_RUNNER": network_item["content_id"],
            "SCIENTIFIC_RUNNER": scientific_item["content_id"],
        },
        "type_name": "CAMPAIGN02_MULTI_ROLE_RUNNER_IDENTITY",
    }

    def control_identity(
        *, component: str, entrypoint: str, paths: tuple[str, ...]
    ) -> dict[str, object]:
        return {
            **common,
            "component": component,
            "entrypoint": entrypoint,
            "executable_hashes": hashes(*paths),
            "type_name": "CAMPAIGN02_CONTROL_COMPONENT_IDENTITY",
        }

    native = control_identity(
        component="CAMPAIGN02_NATIVE_FEATURE008_VERIFIER",
        entrypoint="delta_verify_certificate_chain_v1",
        paths=(
            "delta-core-cpp/src/certificates/verifier.cpp",
            "delta-ffi/src/certificate_chain_abi.cpp",
        ),
    )
    signed = control_identity(
        component="CAMPAIGN02_SIGNED_STAGE_AUTHORIZATION_VERIFIER",
        entrypoint="deltatorrent.benchmark.stage_authorization.verify_stage_authorization_proof",
        paths=("delta-worker-python/src/deltatorrent/benchmark/stage_authorization.py",),
    )
    analyzer: dict[str, object] = {
        **control_identity(
            component="CAMPAIGN02_STAGE_GATE_ANALYZER",
            entrypoint="deltatorrent.benchmark.campaign02_stage_execution.execute_stage",
            paths=(
                "delta-worker-python/src/deltatorrent/benchmark/campaign02_execution_identities.py",
                "delta-worker-python/src/deltatorrent/benchmark/campaign02_stage_a_evidence.py",
                "delta-worker-python/src/deltatorrent/benchmark/campaign02_stage_execution.py",
                "delta-worker-python/src/deltatorrent/benchmark/stage_authorization.py",
            ),
        ),
        "entrypoints": ["deltatorrent.benchmark.campaign02_stage_execution.execute_stage"],
        "implementation_class": (
            "deltatorrent.benchmark.campaign02_stage_execution.Campaign02StageGateFinalizer"
        ),
        "source_class": "MEASURED_CONTROL_PLANE",
        "workflow_default_ref": "refs/heads/main",
        "workflow_hashes": hashes(".github/workflows/benchmark-campaign02-stage-a.yml"),
        "workflow_path": ".github/workflows/benchmark-campaign02-stage-a.yml",
        "workflow_repository": "chartjs333/delta",
    }
    analyzer["implementation_id"] = implementation_id(analyzer)
    receipt = control_identity(
        component="CAMPAIGN02_TYPED_STAGE_GATE_RECEIPT_VERIFIER",
        entrypoint=(
            "deltatorrent.benchmark.stage_authorization.StageGateReceipt.from_canonical_bytes"
        ),
        paths=(
            "delta-worker-python/src/deltatorrent/benchmark/campaign02_stage_execution.py",
            "delta-worker-python/src/deltatorrent/benchmark/stage_authorization.py",
        ),
    )
    raw = {
        "campaign_id": "campaign-02",
        "execution_authorized": False,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "identities": {
            "evaluation_runner": evaluation_item,
            "exactness_runner": exactness_item,
            "multi_role_runner": wrapped_identity(
                "deltareduce.010.campaign02-multi-role-runner.v3", multi_role
            ),
            "native_feature008_verifier": wrapped_identity(
                "deltareduce.010.campaign02-native-feature008-verifier.v2", native
            ),
            "network_fault_runner": network_item,
            "observation_writer": writer_item,
            "scientific_runner": scientific_item,
            "signed_stage_authorization_verifier": wrapped_identity(
                "deltareduce.010.campaign02-signed-stage-authorization-verifier.v2", signed
            ),
            "stage_gate_analyzer": wrapped_identity(
                "deltareduce.010.campaign02-stage-gate-analyzer.v3", analyzer
            ),
            "typed_gate_receipt_verifier": wrapped_identity(
                "deltareduce.010.campaign02-typed-stage-gate-receipt-verifier.v2", receipt
            ),
        },
        "schema_version": "3.0.0",
        "source_commit": QUALIFIED_SOURCE,
        "source_tree": QUALIFIED_TREE,
        "type_name": "CAMPAIGN02_STAGE_EXECUTION_IDENTITIES",
    }
    return StageExecutionIdentityManifest.from_dict(raw)


def runtime_lineage(
    exact: dict[str, object],
    identities: StageExecutionIdentityManifest,
    arms: tuple[object, ...],
) -> QualifiedRuntimeLineage:
    base = previous.legacy.runtime_lineage(exact, identities.raw, arms)  # type: ignore[arg-type]
    return QualifiedRuntimeLineage(
        source_commit=base.source_commit,
        source_tree=base.source_tree,
        environment_id=base.environment_id,
        image_id=base.image_id,
        hardware_id=base.hardware_id,
        runner_id=None,
        evaluation_runner_id=identities.identity_id("evaluation_runner"),
        writer_id=identities.identity_id("observation_writer"),
        model_id=base.model_id,
        parent_checkpoint_id=base.parent_checkpoint_id,
        tokenizer_id=base.tokenizer_id,
        dataset_ids=base.dataset_ids,
        evaluation_profile_ids=base.evaluation_profile_ids,
        evaluation_implementation_ids=base.evaluation_implementation_ids,
        certified_plan_bindings=base.certified_plan_bindings,
        stage_execution_identities_id=identities.content_id,
        exactness_runner_id=identities.identity_id("exactness_runner"),
        scientific_runner_id=identities.identity_id("scientific_runner"),
        network_fault_runner_id=identities.identity_id("network_fault_runner"),
        schema_version="4.0.0",
    )


def construction_authorization(
    exact: dict[str, object], hardware: dict[str, object], receipt: dict[str, object]
) -> dict[str, object]:
    return {
        "approved_task_ids": ["C2-034", "C2-035", "C2-036", "C2-037"],
        "definition_construction_authorized": True,
        "execution_authorization": {
            "c2_024_authorized": False,
            "feature_011_authorized": False,
            "primary_execution_authorized": False,
            "real_wan_authorized": False,
            "result_qc_authorized": False,
            "stage_a_authorized": False,
            "stage_b_authorized": False,
            "stage_c_authorized": False,
        },
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "governance_review": {
            "pull_request": 19,
            "reviewed_head": PR19_REVIEWED_HEAD,
            "verdict": "CHANGES_REQUIRED_REPLACEMENT_DEFINITION_AFTER_C2_037",
        },
        "qualification": {
            "ci_receipt_id": raw_id(CI_RECEIPT_PATH),
            "exact_source_qualification_id": raw_id(EXACT_PATH),
            "hardware_qualification_id": raw_id(HARDWARE_PATH),
            "workflow_run_id": receipt["workflow_run_id"],
        },
        "qualified_source": exact["source"],
        "schema_version": "4.0.0",
        "status": "APPROVED_FOR_REPLACEMENT_DEFINITION_CONSTRUCTION_ONLY",
        "superseded_definition_id": SUPERSEDED_DEFINITION_ID,
        "type_name": "CAMPAIGN02_DEFINITION_CONSTRUCTION_AUTHORIZATION",
    }


def readiness(
    definition: BenchmarkDefinition,
    lineage: QualifiedRuntimeLineage,
    identities: StageExecutionIdentityManifest,
    authorization: dict[str, object],
    methodology: dict[str, object],
) -> dict[str, object]:
    return {
        "authorization": authorization["execution_authorization"],
        "benchmark_definition_id": definition.content_id,
        "c2_023": {
            "definition_attestation": "ABSENT",
            "independent_votes_present": 0,
            "private_keys_committed": False,
            "status": "AWAITING_NEW_GOVERNANCE_REVIEW",
        },
        "c2_024_status": "NOT_AUTHORIZED",
        "definition_construction_authorization_id": sha256_content_id(
            canonical_json_bytes(authorization)
        ),
        "definition_created": True,
        "execution_authorization": "ABSENT",
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "methodology_diff_id": sha256_content_id(canonical_json_bytes(methodology)),
        "next_required_gate": "GOVERNANCE_REVIEW_BEFORE_C2_023",
        "plan_catalog": {
            "authoritative_catalog_created": False,
            "reason": "VERIFIED_DEFINITION_ATTESTATION_REQUIRED",
            "status": "NOT_CONSTRUCTED",
        },
        "primary_observations_created": 0,
        "qualified_runtime_lineage_id": lineage.content_id,
        "qualified_source": {"commit": QUALIFIED_SOURCE, "tree": QUALIFIED_TREE},
        "schema_version": "4.0.0",
        "stage_execution_identities_id": identities.content_id,
        "stage_a_default_branch_registration": "REQUIRED_BEFORE_C2_024",
        "status": "DEFINITION_V4_CREATED_AWAITING_GOVERNANCE_REVIEW",
        "superseded_definition_id": SUPERSEDED_DEFINITION_ID,
        "type_name": "CAMPAIGN02_DEFINITION_READINESS",
    }


def supersession_resolution(definition: BenchmarkDefinition) -> dict[str, object]:
    original = load_document(ORIGINAL_SUPERSESSION_PATH)
    require(
        original.get("superseded_definition_id") == SUPERSEDED_DEFINITION_ID
        and original.get("replacement_definition_id") is None
        and original.get("status") == "SUPERSEDED_BEFORE_ATTESTATION"
        and original.get("votes") == original.get("observations") == 0
        and original.get("attestation") == "ABSENT",
        "ORIGINAL_SUPERSESSION_INVALID",
    )
    return {
        "attestation": "ABSENT",
        "campaign_id": "campaign-02",
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "observations": 0,
        "original_supersession_record_id": raw_id(ORIGINAL_SUPERSESSION_PATH),
        "replacement_definition_id": definition.content_id,
        "schema_version": "1.0.0",
        "status": "REPLACEMENT_DEFINITION_CONSTRUCTED_AWAITING_GOVERNANCE_REVIEW",
        "superseded_definition_id": SUPERSEDED_DEFINITION_ID,
        "type_name": "CAMPAIGN02_DEFINITION_SUPERSESSION_RESOLUTION",
        "votes": 0,
    }


def validate_package(
    definition: BenchmarkDefinition,
    lineage: QualifiedRuntimeLineage,
    identities: StageExecutionIdentityManifest,
) -> None:
    require(
        definition.raw["schema_version"] == "4.0.0"
        and lineage.schema_version == "4.0.0"
        and identities.schema_version == "3.0.0"
        and definition.content_id != SUPERSEDED_DEFINITION_ID
        and definition.source_commit == lineage.source_commit == QUALIFIED_SOURCE
        and definition.source_tree == lineage.source_tree == QUALIFIED_TREE
        and definition.qualified_runtime_lineage_id == lineage.content_id
        and definition.stage_execution_identities_id == identities.content_id
        and lineage.stage_execution_identities_id == identities.content_id,
        "DEFINITION_V4_BINDING_INVALID",
    )
    require(
        lineage.exactness_runner_id == identities.identity_id("exactness_runner")
        and lineage.scientific_runner_id == identities.identity_id("scientific_runner")
        and lineage.network_fault_runner_id == identities.identity_id("network_fault_runner")
        and lineage.evaluation_runner_id == identities.identity_id("evaluation_runner")
        and lineage.writer_id == identities.identity_id("observation_writer")
        and len(lineage.certified_plan_bindings) == 36,
        "DEFINITION_V4_RUNTIME_LINEAGE_INVALID",
    )
    verify_historical_identity_files(identities, "exactness_runner")
    verify_historical_identity_files(identities, "network_fault_runner")
    verify_historical_identity_files(identities, "stage_gate_analyzer")


def documents() -> dict[Path, dict[str, object]]:
    exact, hardware, receipt = qualification()
    workload_id = str(
        previous.legacy.load_workload_contract(CONFIG / "workload-v2.json").content_id
    )
    arms_document = previous.legacy.arms_document(workload_id)
    arms = previous.legacy.arm_specs(arms_document)
    identities = stage_identities(exact)
    datasets = previous.legacy.dataset_manifest(exact)
    metrics = previous.legacy.metrics_document(exact, identities.raw)
    lineage = runtime_lineage(exact, identities, arms)
    definition_value = previous.legacy.definition_document(
        exact, arms_document, datasets, metrics, lineage
    )
    definition_value.update(
        {
            "schema_version": "4.0.0",
            "stage_execution_identities_id": identities.content_id,
        }
    )
    definition = BenchmarkDefinition.from_dict(definition_value)
    validate_package(definition, lineage, identities)
    authorization = construction_authorization(exact, hardware, receipt)
    methodology = previous.legacy.methodology_diff(definition, metrics, identities.raw)
    methodology.update(
        {
            "replacement_reason": "PR19_EXECUTABLE_AND_WORKFLOW_PROVENANCE_REMEDIATION",
            "schema_version": "4.0.0",
            "superseded_definition_id": SUPERSEDED_DEFINITION_ID,
        }
    )
    return {
        DATASETS_PATH: datasets,
        METRICS_PATH: metrics,
        IDENTITIES_PATH: identities.raw,
        LINEAGE_PATH: lineage.document,
        DEFINITION_PATH: definition.raw,
        AUTHORIZATION_PATH: authorization,
        METHODOLOGY_PATH: methodology,
        READINESS_PATH: readiness(definition, lineage, identities, authorization, methodology),
        SUPERSESSION_RESOLUTION_PATH: supersession_resolution(definition),
    }


def expected_outputs() -> dict[Path, bytes]:
    return {path: canonical_json_bytes(value) + b"\n" for path, value in documents().items()}


def write_outputs() -> None:
    for path, value in expected_outputs().items():
        require(not path.exists(), f"DEFINITION_V4_OUTPUT_EXISTS:{path.name}")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(value)


def check_outputs() -> None:
    for path, expected in expected_outputs().items():
        require(path.is_file() and path.read_bytes() == expected, f"OUTPUT_DRIFT:{path.name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    if arguments.write:
        write_outputs()
    else:
        check_outputs()
    definition = BenchmarkDefinition.from_dict(load_document(DEFINITION_PATH))
    print(
        canonical_json_bytes(
            {
                "definition_id": definition.content_id,
                "independent_votes_present": 0,
                "output_count": len(expected_outputs()),
                "primary_execution_authorized": False,
                "source_commit": QUALIFIED_SOURCE,
                "status": "PASS",
            }
        ).decode()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
