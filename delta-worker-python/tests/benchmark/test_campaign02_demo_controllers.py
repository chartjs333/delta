from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from deltatorrent.benchmark.campaign02_bootstrap import (
    BootstrapValidatorSet,
    SignedBootstrapMappingVote,
    WorkflowBootstrapMapping,
    verify_bootstrap_mapping,
)
from deltatorrent.benchmark.campaign02_demo_controllers import (
    DemoControllerError,
    generate_demo_controller_bundle,
    main,
    run_demo_quorum_smoke,
    verify_demo_controller_bundle,
)
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.protocol.canonical import sha256_content_id


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _mapping() -> WorkflowBootstrapMapping:
    workflow = b"name: synthetic demo bootstrap\n"
    blob_id = hashlib.sha1(
        b"blob " + str(len(workflow)).encode("ascii") + b"\0" + workflow
    ).hexdigest()
    return WorkflowBootstrapMapping.from_dict(
        {
            "bootstrap_commit": "1" * 40,
            "bootstrap_workflow_blob_id": blob_id,
            "bootstrap_workflow_content_id": sha256_content_id(workflow),
            "bootstrap_workflow_path": ".github/workflows/campaign02-stage-a-bootstrap.yml",
            "execution_authorized": False,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "qualified_source_commit": "2" * 40,
            "qualified_source_tree": "3" * 40,
            "repository": "example/demo",
            "schema_version": "1.0.0",
            "source_stage_a_workflow_content_id": "sha256:" + "4" * 64,
            "source_stage_a_workflow_path": (".github/workflows/benchmark-campaign02-stage-a.yml"),
            "type_name": "CAMPAIGN02_WORKFLOW_BOOTSTRAP_MAPPING",
        }
    )


def test_generated_bundle_is_explicitly_non_authoritative_and_self_consistent(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "controllers"
    generated = generate_demo_controller_bundle(destination)
    verified = verify_demo_controller_bundle(destination)
    manifest = _read_json(destination / "demo-controller-manifest.json")
    admin_ui_register = _read_json(destination / "controller-register.demo.json")
    validator_document = _read_json(destination / "bootstrap-validator-set.demo.json")
    validator_set = BootstrapValidatorSet.from_dict(validator_document)

    assert generated == verified
    assert generated.validator_set_id == validator_set.content_id
    assert manifest["environment"] == "LOCAL_DEMO_ONLY"
    assert manifest["authoritative"] is False
    assert manifest["governance_eligible"] is False
    assert manifest["execution_authorized"] is False
    assert manifest["valid_for_demo_testing"] is True
    assert manifest["valid_for_campaign02_governance"] is False
    assert validator_document["execution_authorized"] is False
    assert validator_document["f_b"] == 1
    assert validator_document["quorum_threshold"] == 3
    assert len(validator_document["validators"]) == 4  # type: ignore[arg-type]
    assert admin_ui_register["authority_class"] == "LOCAL_FIXTURE"
    assert admin_ui_register["demo_mode"] is True
    assert admin_ui_register["status"] == "DEMO_VALID_FOR_TESTING"
    assert admin_ui_register["governance_eligible"] is False
    assert admin_ui_register["execution_authorized"] is False
    assert len(admin_ui_register["controllers"]) == 4  # type: ignore[arg-type]
    assert all(item.startswith("demo-campaign02-signer-") for item in generated.signer_ids)


def test_generated_private_keys_are_unique_and_match_public_validator_set(tmp_path: Path) -> None:
    destination = tmp_path / "controllers"
    generate_demo_controller_bundle(destination)
    validator_set = BootstrapValidatorSet.from_dict(
        _read_json(destination / "bootstrap-validator-set.demo.json")
    )
    private_keys: list[bytes] = []
    for index in range(1, 5):
        signer_id = f"demo-campaign02-signer-{index:02d}"
        private_path = destination / "private" / f"{signer_id}.demo-controller-private.pem"
        private_key = serialization.load_pem_private_key(private_path.read_bytes(), password=None)
        assert isinstance(private_key, Ed25519PrivateKey)
        public_key = private_key.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        assert public_key == validator_set.validator(signer_id).public_key
        private_keys.append(
            private_key.private_bytes(
                serialization.Encoding.Raw,
                serialization.PrivateFormat.Raw,
                serialization.NoEncryption(),
            )
        )
    assert len(set(private_keys)) == 4


def test_demo_keys_can_exercise_production_mapping_quorum_verification(tmp_path: Path) -> None:
    destination = tmp_path / "controllers"
    generate_demo_controller_bundle(destination)
    validator_set = BootstrapValidatorSet.from_dict(
        _read_json(destination / "bootstrap-validator-set.demo.json")
    )
    mapping = _mapping()
    votes: list[SignedBootstrapMappingVote] = []
    for index in range(1, 4):
        signer_id = f"demo-campaign02-signer-{index:02d}"
        private_path = destination / "private" / f"{signer_id}.demo-controller-private.pem"
        private_key = serialization.load_pem_private_key(private_path.read_bytes(), password=None)
        assert isinstance(private_key, Ed25519PrivateKey)
        unsigned = SignedBootstrapMappingVote(
            mapping_id=mapping.content_id,
            validator_set_id=validator_set.content_id,
            signer_id=signer_id,
            submitted_at=datetime(2030, 1, 1, tzinfo=UTC),
            signature=b"\0" * 64,
        )
        votes.append(
            SignedBootstrapMappingVote(
                mapping_id=unsigned.mapping_id,
                validator_set_id=unsigned.validator_set_id,
                signer_id=unsigned.signer_id,
                submitted_at=unsigned.submitted_at,
                signature=private_key.sign(unsigned.message),
            )
        )

    verified = verify_bootstrap_mapping(
        mapping,
        validator_set=validator_set,
        votes=tuple(votes),
    )
    assert verified.signer_ids == tuple(f"demo-campaign02-signer-{i:02d}" for i in range(1, 4))


def test_presentation_smoke_exercises_positive_and_negative_production_paths(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "controllers"
    generate_demo_controller_bundle(destination)
    result = run_demo_quorum_smoke(destination).document
    assert result["demo_status"] == "DEMO_PASS"
    assert result["authoritative"] is False
    assert result["governance_eligible"] is False
    assert result["execution_authorized"] is False
    assert result["keys_cryptographically_valid"] is True
    assert result["valid_for_demo_testing"] is True
    assert result["valid_for_campaign02_governance"] is False
    assert result["checks"] == {
        "forged_signature_rejected": "PASS",
        "production_parser_compatibility": "PASS",
        "three_of_four_quorum_verified": "PASS",
        "two_of_four_quorum_rejected": "PASS",
    }


def test_generator_refuses_to_overwrite_existing_output(tmp_path: Path) -> None:
    destination = tmp_path / "controllers"
    generate_demo_controller_bundle(destination)
    with pytest.raises(DemoControllerError, match="OUTPUT_ALREADY_EXISTS"):
        generate_demo_controller_bundle(destination)


def test_verifier_rejects_authority_marker_tampering(tmp_path: Path) -> None:
    destination = tmp_path / "controllers"
    generate_demo_controller_bundle(destination)
    manifest_path = destination / "demo-controller-manifest.json"
    manifest = _read_json(manifest_path)
    manifest["governance_eligible"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(DemoControllerError, match="MANIFEST_BOUNDARY_INVALID"):
        verify_demo_controller_bundle(destination)


def test_verifier_rejects_admin_ui_demo_marker_tampering(tmp_path: Path) -> None:
    destination = tmp_path / "controllers"
    generate_demo_controller_bundle(destination)
    register_path = destination / "controller-register.demo.json"
    register = _read_json(register_path)
    register["status"] = "ACTIVE"
    register_path.write_text(json.dumps(register), encoding="utf-8")
    with pytest.raises(DemoControllerError, match="ADMIN_UI_REGISTER_DIGEST_MISMATCH"):
        verify_demo_controller_bundle(destination)


def test_bundle_contains_no_votes_attestations_or_authority_artifacts(tmp_path: Path) -> None:
    destination = tmp_path / "controllers"
    generate_demo_controller_bundle(destination)
    names = {path.name.lower() for path in destination.rglob("*")}
    forbidden_fragments = ("vote", "signature", "attestation", "approval", "definition", "resultqc")
    assert not any(fragment in name for name in names for fragment in forbidden_fragments)


def test_cli_prints_only_public_summary(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    destination = tmp_path / "controllers"
    assert main(["generate", "--output-dir", str(destination)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["governance_eligible"] is False
    assert output["execution_authorized"] is False
    assert "private" not in json.dumps(output).lower()
    assert main(["verify", "--output-dir", str(destination)]) == 0


def test_one_command_demo_reports_non_authoritative_pass(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    destination = tmp_path / "commission-demo"
    assert main(["demo", "--output-dir", str(destination)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["demo_status"] == "DEMO_PASS"
    assert output["checks"]["three_of_four_quorum_verified"] == "PASS"
    assert output["execution_authorized"] is False
    assert output["keys_cryptographically_valid"] is True
    assert output["valid_for_demo_testing"] is True
    assert output["valid_for_campaign02_governance"] is False
    assert "signature_base64" not in json.dumps(output)


def test_pretty_demo_keeps_non_authoritative_boundary_visible(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    destination = tmp_path / "commission-pretty"
    assert main(["demo", "--output-dir", str(destination), "--pretty"]) == 0
    output = capsys.readouterr().out
    assert "PASS (4/4)" in output
    assert "PASS (3/4)" in output
    assert "LOCAL_DEMO_ONLY" in output
    assert "Governance eligibility:       NO" in output
    assert "Execution authorization:      NO" in output
    assert "Overall demo result:          DEMO_PASS" in output
