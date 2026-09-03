"""Verify Campaign 02 default-branch bootstrap registration and runtime provenance."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from deltatorrent.benchmark.campaign02_bootstrap import (
    BootstrapRuntimeProvenance,
    BootstrapValidatorSet,
    SignedBootstrapMappingVote,
    WorkflowBootstrapMapping,
    WorkflowRegistrationReceipt,
    verify_bootstrap_mapping,
    verify_bootstrap_runtime,
    verify_registration_receipt,
)
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id


def load_canonical(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict) or raw not in {
        canonical_json_bytes(value),
        canonical_json_bytes(value) + b"\n",
    }:
        raise ValueError("CAMPAIGN02_BOOTSTRAP_ARTIFACT_NONCANONICAL")
    return value


def git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ("git", "-C", str(root), *arguments),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def verify(arguments: argparse.Namespace) -> dict[str, object]:
    mapping = WorkflowBootstrapMapping.from_dict(load_canonical(arguments.mapping))
    validator_set = BootstrapValidatorSet.from_dict(load_canonical(arguments.validator_set))
    votes = tuple(
        SignedBootstrapMappingVote.from_dict(load_canonical(path)) for path in arguments.vote
    )
    verified = verify_bootstrap_mapping(mapping, validator_set=validator_set, votes=votes)
    registration = WorkflowRegistrationReceipt.from_dict(load_canonical(arguments.registration))
    verify_registration_receipt(verified, registration)
    source_head = git(arguments.qualified_source_root, "rev-parse", "HEAD")
    source_tree = git(arguments.qualified_source_root, "show", "-s", "--format=%T", "HEAD")
    bootstrap_head = git(arguments.bootstrap_root, "rev-parse", "HEAD")
    source_workflow = arguments.qualified_source_root / mapping.source_stage_a_workflow_path
    bootstrap_workflow = arguments.bootstrap_root / mapping.bootstrap_workflow_path
    bootstrap_blob = git(
        arguments.bootstrap_root,
        "rev-parse",
        f"{mapping.bootstrap_commit}:{mapping.bootstrap_workflow_path}",
    )
    if (
        bootstrap_head != mapping.bootstrap_commit
        or source_head != mapping.qualified_source_commit
        or source_tree != mapping.qualified_source_tree
        or sha256_content_id(source_workflow.read_bytes())
        != mapping.source_stage_a_workflow_content_id
        or bootstrap_blob != mapping.bootstrap_workflow_blob_id
        or sha256_content_id(bootstrap_workflow.read_bytes())
        != mapping.bootstrap_workflow_content_id
    ):
        raise ValueError("CAMPAIGN02_BOOTSTRAP_CHECKOUT_BINDING_MISMATCH")
    provenance = BootstrapRuntimeProvenance(
        repository=arguments.repository,
        workflow_id=registration.workflow_id,
        workflow_path=mapping.bootstrap_workflow_path,
        workflow_ref=arguments.workflow_ref,
        workflow_sha=arguments.workflow_sha,
        workflow_blob_id=bootstrap_blob,
        workflow_content_id=sha256_content_id(bootstrap_workflow.read_bytes()),
        run_id=arguments.run_id,
        run_attempt=arguments.run_attempt,
        event_name=arguments.event_name,
        dispatch_ref=arguments.dispatch_ref,
        github_sha=arguments.github_sha,
        qualified_source_commit=source_head,
        qualified_source_tree=source_tree,
        source_stage_a_workflow_content_id=sha256_content_id(source_workflow.read_bytes()),
    )
    verify_bootstrap_runtime(verified, provenance)
    return {
        "bootstrap_mapping_attestation_id": verified.content_id,
        "bootstrap_mapping_id": mapping.content_id,
        "execution_authorized": False,
        "observations": 0,
        "registration_receipt_id": registration.content_id,
        "status": "PASS",
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--mapping", type=Path, required=True)
    result.add_argument("--validator-set", type=Path, required=True)
    result.add_argument("--vote", type=Path, action="append", required=True)
    result.add_argument("--registration", type=Path, required=True)
    result.add_argument("--bootstrap-root", type=Path, required=True)
    result.add_argument("--qualified-source-root", type=Path, required=True)
    result.add_argument("--repository", required=True)
    result.add_argument("--workflow-ref", required=True)
    result.add_argument("--workflow-sha", required=True)
    result.add_argument("--run-id", type=int, required=True)
    result.add_argument("--run-attempt", type=int, required=True)
    result.add_argument("--event-name", required=True)
    result.add_argument("--dispatch-ref", required=True)
    result.add_argument("--github-sha", required=True)
    return result


def main() -> int:
    value = verify(parser().parse_args())
    print(canonical_json_bytes(value).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
