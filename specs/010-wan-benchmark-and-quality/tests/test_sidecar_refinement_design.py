from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
FEATURE = ROOT / "specs/010-wan-benchmark-and-quality"
SCRIPTS = FEATURE / "scripts"
sys.path.insert(0, str(SCRIPTS))
import exactness_gate as gate  # noqa: E402
import verify_exactness_status as exact_status  # noqa: E402
import verify_sidecar_refinement_design as design  # noqa: E402


def design_document() -> dict[str, object]:
    return json.loads(design.DESIGN_PATH.read_text(encoding="utf-8"))


def test_design_document_passes() -> None:
    value = design_document()

    design.validate_design(value)


def test_design_loader_rejects_duplicate_json_key() -> None:
    raw = b'{"schema_version":"1.0.0","schema_version":"2.0.0"}'

    with pytest.raises(gate.ExactnessError, match="SIDECAR_JSON_DUPLICATE_KEY"):
        design.canonical_design_bytes(raw, "duplicate.json")


def test_repository_design_passes_without_source_commit() -> None:
    result = design.verify_repository(None)

    assert result["status"] == "PASS_SIDECAR_REFINEMENT_DESIGN_ONLY"
    assert result["selected_profile"] is None
    assert result["source"] is None


def test_historical_fail_source_remains_valid_and_pinned() -> None:
    source = gate.source_identity(design.HISTORICAL_FAIL_COMMIT)

    exact_status.validate_source(source)

    assert source["tree"] == design.HISTORICAL_FAIL_TREE


def test_design_source_rejects_merge_parent(monkeypatch: pytest.MonkeyPatch) -> None:
    commit = "1" * 40
    second_parent = "2" * 40
    monkeypatch.setattr(
        exact_status,
        "git_text",
        lambda *_arguments: f"{commit} {design.HISTORICAL_FAIL_COMMIT} {second_parent}",
    )

    with pytest.raises(gate.ExactnessError, match="DESIGN_SOURCE_PARENT"):
        exact_status.validate_single_parent(
            commit,
            design.HISTORICAL_FAIL_COMMIT,
            "DESIGN_SOURCE_PARENT",
        )


def test_design_layer_path_set_is_bounded_and_nonproduction() -> None:
    expected = {
        ".github/workflows/feature010-exactness.yml",
        "specs/010-wan-benchmark-and-quality/isolated-sidecar-refinement.md",
        "specs/010-wan-benchmark-and-quality/sidecar-refinement-design.json",
        "specs/010-wan-benchmark-and-quality/scripts/verify_exactness_status.py",
        "specs/010-wan-benchmark-and-quality/scripts/verify_sidecar_refinement_design.py",
        "specs/010-wan-benchmark-and-quality/tests/test_sidecar_refinement_design.py",
    }

    assert exact_status.DESIGN_PATHS == expected
    assert not any(path.startswith(exact_status.PROTECTED_PREFIXES) for path in expected)
    assert not any("/evidence/" in f"/{path}" for path in expected)


def test_rejects_authority_or_profile_promotion() -> None:
    value = design_document()
    value["authority"]["selected_profile"] = "ISOLATED_SIDECAR"  # type: ignore[index]
    value["authority"]["gate_a_qualified"] = True  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_AUTHORITY_BOUNDARY"):
        design.validate_design(value)


def test_rejects_new_formal_action_or_outcome() -> None:
    value = design_document()
    formal = value["formal_impact"]  # type: ignore[assignment]
    formal["new_externally_visible_action_ids"] = ["ACT-IPC-FAIL"]  # type: ignore[index]
    formal["new_failure_terminals"] = ["IPC_FAILED"]  # type: ignore[index]
    formal["new_deadline_semantics"] = ["ADAPTIVE_WATCHDOG_DEADLINE"]  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_FORMAL_IMPACT"):
        design.validate_design(value)


def test_rejects_java_wal_ownership() -> None:
    value = design_document()
    ipc = value["ipc_contract"]  # type: ignore[assignment]
    ipc["ownership"]["java"].append("WAL")  # type: ignore[index,union-attr]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_IPC_OWNERSHIP"):
        design.validate_design(value)


def test_rejects_parallel_native_mutation() -> None:
    value = design_document()
    ipc = value["ipc_contract"]  # type: ignore[assignment]
    ipc["bounds"]["mutating_native_calls"] = 2  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_IPC_BOUNDS"):
        design.validate_design(value)


def test_rejects_unbounded_or_enlarged_frames_and_queues() -> None:
    value = design_document()
    ipc = value["ipc_contract"]  # type: ignore[assignment]
    ipc["bounds"]["control_envelope_bytes"] = 2**63  # type: ignore[index]
    ipc["bounds"]["ingress_queue_requests"] = 2**31  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_IPC_BOUNDS"):
        design.validate_design(value)


def test_rejects_copy_fallback_that_cannot_carry_maximum_logical_payload() -> None:
    value = design_document()
    bounds = value["ipc_contract"]["bounds"]  # type: ignore[index]
    bounds["max_inline_payload_bytes"] = bounds["max_logical_payload_bytes"] - 1  # type: ignore[index,operator]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_IPC_BOUNDS"):
        design.validate_design(value)


def test_rejects_descriptor_mismatch_downgrade() -> None:
    value = design_document()
    handshake = value["ipc_contract"]["descriptor_handshake"]  # type: ignore[index]
    handshake["major_version_rule"] = "NEGOTIATE_DOWN"  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_DESCRIPTOR_HANDSHAKE"):
        design.validate_design(value)

    value = design_document()
    handshake = value["ipc_contract"]["descriptor_handshake"]  # type: ignore[index]
    handshake["bounds_rule"] = "NEGOTIATE_LOWER_BOUNDS"  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_DESCRIPTOR_HANDSHAKE"):
        design.validate_design(value)


def test_rejects_magic_opcode_or_header_layout_mutation() -> None:
    value = design_document()
    framing = value["ipc_contract"]["canonical_framing"]  # type: ignore[index]
    framing["magic_ascii"] = "BADMAGIC"  # type: ignore[index]
    framing["message_type_values"]["SUBMIT_REQUEST"] = 34  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_FRAMING_BOUNDS"):
        design.validate_design(value)


def test_rejects_incomplete_descriptor_binding() -> None:
    value = design_document()
    handshake = value["ipc_contract"]["descriptor_handshake"]  # type: ignore[index]
    handshake["bound_fields"].remove("NESTED_C_ABI_DESCRIPTOR_SHA256")  # type: ignore[index,union-attr]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_DESCRIPTOR_HANDSHAKE"):
        design.validate_design(value)


def test_rejects_shared_memory_for_handshake_or_ack_transport() -> None:
    value = design_document()
    framing = value["ipc_contract"]["canonical_framing"]  # type: ignore[index]
    framing["flag_rules"].remove(  # type: ignore[index,union-attr]
        "MESSAGE_CARRIER_ELIGIBILITY_TABLE_ENFORCED_BEFORE_SHM_REFERENCE_RESOLUTION"
    )

    with pytest.raises(gate.ExactnessError, match="SIDECAR_FRAME_FLAG_RULES"):
        design.validate_design(value)


def test_rejects_wrong_opcode_flags_capacity_or_transport_sequence() -> None:
    value = design_document()
    framing = value["ipc_contract"]["canonical_framing"]  # type: ignore[index]
    framing["opcode_flag_requirements"]["SNAPSHOT_REQUEST"].append("READ_ONLY")  # type: ignore[index,union-attr]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_OPCODE_FLAG_REQUIREMENTS"):
        design.validate_design(value)

    value = design_document()
    framing = value["ipc_contract"]["canonical_framing"]  # type: ignore[index]
    framing["response_capacity_rule"] = "ANY_NONZERO_CAPACITY"  # type: ignore[index]
    with pytest.raises(gate.ExactnessError, match="SIDECAR_RESPONSE_CAPACITY_RULE"):
        design.validate_design(value)

    value = design_document()
    framing = value["ipc_contract"]["canonical_framing"]  # type: ignore[index]
    framing["sequence_rule"] = "MONOTONIC_BUT_GAPS_AND_ZERO_ALLOWED"  # type: ignore[index]
    with pytest.raises(gate.ExactnessError, match="SIDECAR_SEQUENCE_RULE"):
        design.validate_design(value)


def test_rejects_payload_schema_or_wire_type_mutation() -> None:
    value = design_document()
    codec = value["ipc_contract"]["payload_codec"]  # type: ignore[index]
    codec["field_registry"]["SUBMIT_RESPONSE"].pop()  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_PAYLOAD_SCHEMA_ID"):
        design.validate_design(value)


def test_rejects_out_of_order_or_duplicate_payload_fields() -> None:
    value = design_document()
    registry = value["ipc_contract"]["payload_codec"]["field_registry"]  # type: ignore[index]
    registry["SUBMIT_REQUEST"][1] = "1:REQUEST_DIGEST:SHA256"  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_PAYLOAD_FIELD_ORDER"):
        design.validate_design(value)


def test_rejects_request_digest_without_operation_domain_separation() -> None:
    value = design_document()
    rules = value["ipc_contract"]["payload_codec"]["body_rules"]  # type: ignore[index]
    rules[10] = "REQUEST_DIGEST_HASHES_ONLY_OPERATION_TLVS"  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_PAYLOAD_RULES"):
        design.validate_design(value)


def test_rejects_shm_handshake_or_recursive_ack_carrier() -> None:
    value = design_document()
    eligibility = value["ipc_contract"]["payload_codec"]["carrier_eligibility"]  # type: ignore[index]
    eligibility["CLIENT_HELLO"] = "INLINE_OR_SHARED_MEMORY"  # type: ignore[index]
    eligibility["SHARED_MEMORY_ACK"] = "INLINE_OR_SHARED_MEMORY"  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_CARRIER_ELIGIBILITY"):
        design.validate_design(value)


def test_rejects_ambiguous_admission_sequence_or_absent_result_encoding() -> None:
    value = design_document()
    rules = value["ipc_contract"]["payload_codec"]["admission_encoding_rules"]  # type: ignore[index]
    rules.pop()  # type: ignore[union-attr]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_ADMISSION_ENCODING"):
        design.validate_design(value)


def test_rejects_raw_or_incomplete_nested_abi_descriptor() -> None:
    value = design_document()
    nested = value["ipc_contract"]["payload_codec"]["nested_c_abi_descriptor"]  # type: ignore[index]
    nested["fixed_prefix_layout"][0] = "0:64:RAW_C_STRUCT"  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_NESTED_ABI_DESCRIPTOR"):
        design.validate_design(value)


def test_rejects_effect_exposure_before_durability() -> None:
    value = design_document()
    sequence = value["ipc_contract"]["persist_before_expose"]  # type: ignore[index]
    sequence.remove("DURABILITY_BARRIER")  # type: ignore[union-attr]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_PERSIST_BEFORE_EXPOSE"):
        design.validate_design(value)


def test_rejects_treating_buffer_too_small_as_non_admission() -> None:
    value = design_document()
    sizing = value["ipc_contract"]["ffi_output_sizing"]  # type: ignore[index]
    sizing["buffer_too_small_may_follow_durable_submit"] = False  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_FFI_OUTPUT_SIZING"):
        design.validate_design(value)


def test_rejects_retained_borrowed_pointer_or_early_shm_effect() -> None:
    value = design_document()
    shared = value["ipc_contract"]["shared_memory"]  # type: ignore[index]
    shared["borrowed_pointer_lifetime"] = "RETAIN_AFTER_RETURN"  # type: ignore[index]
    shared["effect_publication_rule"] = "BEFORE_DURABILITY"  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_SHARED_MEMORY"):
        design.validate_design(value)


def test_rejects_shared_memory_slot_reuse_before_release() -> None:
    value = design_document()
    shared = value["ipc_contract"]["shared_memory"]  # type: ignore[index]
    shared["slot_reuse"] = "REUSE_BEFORE_RELEASE"  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_SHARED_MEMORY"):
        design.validate_design(value)


def test_rejects_shared_memory_layout_or_memory_order_mutation() -> None:
    value = design_document()
    shared = value["ipc_contract"]["shared_memory"]  # type: ignore[index]
    shared["control_record_layout"][0] = "0:4:STATE:NON_ATOMIC_U32"  # type: ignore[index]
    shared["memory_order"].remove(  # type: ignore[index,union-attr]
        "PRODUCER_WRITES_METADATA_AND_COMPLETE_DATA_AND_DIGEST_BEFORE_RELEASE_STORE_PUBLISHED"
    )

    with pytest.raises(gate.ExactnessError, match="SIDECAR_SHARED_MEMORY"):
        design.validate_design(value)


def test_rejects_misordered_reference_or_ack_as_release_authority() -> None:
    value = design_document()
    shared = value["ipc_contract"]["shared_memory"]  # type: ignore[index]
    shared["reference_fields"] = [  # type: ignore[index]
        "REGION_ID",
        "GENERATION",
        "SLOT",
        "OFFSET",
        "LENGTH",
        "SHA256",
    ]
    shared["ack_frame_authority"] = "ACK_FRAME_ALONE_RELEASES_SLOT"  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_SHARED_MEMORY"):
        design.validate_design(value)


def test_rejects_stale_response_acceptance_or_new_retry_identity() -> None:
    value = design_document()
    retry = value["ipc_contract"]["retry_and_stale_response"]  # type: ignore[index]
    retry["stale_response"] = "ACCEPT_IF_HASH_MATCHES"  # type: ignore[index]
    retry["exact_retry"] = "NEW_REQUEST_ID_ALLOWED"  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_RETRY_STALE_RESPONSE"):
        design.validate_design(value)


def test_rejects_unfencing_live_timed_out_generation() -> None:
    value = design_document()
    retry = value["ipc_contract"]["retry_and_stale_response"]  # type: ignore[index]
    timeout = value["ipc_contract"]["timeout_and_crash_detection"]  # type: ignore[index]
    retry["generation_unfence_forbidden"] = False  # type: ignore[index]
    timeout["alive_after_timeout_resolution"] = "WAIT_AND_REUSE_GENERATION"  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_RETRY_STALE_RESPONSE"):
        design.validate_design(value)


def test_rejects_unbounded_or_consensus_driven_watchdog() -> None:
    value = design_document()
    timeout = value["ipc_contract"]["timeout_and_crash_detection"]  # type: ignore[index]
    timeout["request_watchdog_timeout_ms"] = 0  # type: ignore[index]
    timeout["timeout_clock"] = "CONSENSUS_LOGICAL_TIME"  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_TIMEOUT_CRASH_DETECTION"):
        design.validate_design(value)


def test_rejects_restart_without_journal_recovery_projection() -> None:
    value = design_document()
    projection = value["trace_projection"]  # type: ignore[assignment]
    projection[3]["projection"] = "ACT-RESTART_READY_IMMEDIATELY"  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_TRACE_PROJECTION"):
        design.validate_design(value)


def test_rejects_wrapper_synthesized_timer_or_transport_replay_action() -> None:
    value = design_document()
    projection = value["trace_projection"]  # type: ignore[assignment]
    projection[11]["projection"] = "ACT-MESSAGE-DELIVER"  # type: ignore[index]
    projection[13]["projection"] = "ACT-MESSAGE-REPLAY"  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_TRACE_PROJECTION"):
        design.validate_design(value)


def test_rejects_double_crash_projection_from_intent_and_confirmed_death() -> None:
    value = design_document()
    projection = value["trace_projection"]  # type: ignore[assignment]
    projection[7]["projection"] = "ACT-CRASH_ON_INTENT"  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_TRACE_PROJECTION"):
        design.validate_design(value)


def test_rejects_generic_native_trace_that_can_duplicate_lifecycle_actions() -> None:
    value = design_document()
    projection = value["trace_projection"]  # type: ignore[assignment]
    projection[10]["concrete_events"] = ["NATIVE_TRACE_EVENT"]  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_TRACE_PROJECTION"):
        design.validate_design(value)


def test_rejects_pre_init_root_or_java_lifecycle_action_synthesis() -> None:
    value = design_document()
    projection = value["trace_projection"]  # type: ignore[assignment]
    projection[0]["projection"] = "STUTTER_WITH_FORMAL_ROOT"  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_TRACE_PROJECTION"):
        design.validate_design(value)

    value = design_document()
    invariants = value["trace_projection_invariants"]  # type: ignore[assignment]
    invariants["runtime_consensus_action_synthesis_by_java_forbidden"] = False  # type: ignore[index]
    with pytest.raises(gate.ExactnessError, match="SIDECAR_TRACE_PROJECTION_INVARIANTS"):
        design.validate_design(value)


def test_rejects_state_changing_or_effect_exposing_stutter() -> None:
    value = design_document()
    invariants = value["trace_projection_invariants"]  # type: ignore[assignment]
    invariants["stutter_state_root_rule"] = "ROOT_MAY_CHANGE"  # type: ignore[index]
    invariants["stutter_new_effect_identity_exposed"] = True  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_TRACE_PROJECTION_INVARIANTS"):
        design.validate_design(value)


def test_rejects_new_effect_identity_on_lost_response_reemission() -> None:
    value = design_document()
    invariants = value["trace_projection_invariants"]  # type: ignore[assignment]
    invariants["lost_response_reexposure_rule"] = "MAY_CREATE_NEW_EFFECT_IDENTITY"  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_TRACE_PROJECTION_INVARIANTS"):
        design.validate_design(value)


def test_rejects_asymmetric_comparison_inputs() -> None:
    value = design_document()
    comparison = value["comparison_plan"]  # type: ignore[assignment]
    comparison["identical_pair_fields"].remove("CANONICAL_INPUT_BYTES")  # type: ignore[index,union-attr]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_COMPARISON_PAIRING"):
        design.validate_design(value)


def test_rejects_same_length_comparison_semantic_substitution() -> None:
    value = design_document()
    comparison = value["comparison_plan"]  # type: ignore[assignment]
    fields = comparison["identical_pair_fields"]  # type: ignore[index]
    index = fields.index("CANONICAL_INPUT_BYTES")  # type: ignore[union-attr]
    fields[index] = "CANONICAL_OUTPUT_BYTES"  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_DESIGN_CONTENT_ID"):
        design.validate_design(value)


def test_rejects_missing_hard_gate_or_adaptive_offered_load() -> None:
    value = design_document()
    comparison = value["comparison_plan"]  # type: ignore[assignment]
    comparison["hard_gates_common"].pop()  # type: ignore[index,union-attr]
    comparison["aggregation"]["fixed_offered_load_ops_per_second"] = 0  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_COMMON_HARD_GATES"):
        design.validate_design(value)


def test_rejects_post_hoc_selection_rule_or_early_selection() -> None:
    value = design_document()
    selection = value["profile_selection_rule"]  # type: ignore[assignment]
    selection["selected_profile"] = "EMBEDDED_FFM"  # type: ignore[index]
    selection["sidecar_p99_fixed_load_latency_ratio_bps_max"] = 20_000  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_PROFILE_SELECTION_RULE"):
        design.validate_design(value)


def test_rejects_closing_historical_blockers() -> None:
    value = design_document()
    lineage = value["historical_lineage"]  # type: ignore[assignment]
    lineage["open_tasks"].remove("T028")  # type: ignore[index,union-attr]
    lineage["historical_fail_rewritten"] = True  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_HISTORICAL_LINEAGE"):
        design.validate_design(value)


def test_comparison_mutations_do_not_change_source_document() -> None:
    original = design_document()
    changed = copy.deepcopy(original)
    changed["comparison_plan"]["missing_evidence_rule"] = "IMPUTE_MEDIAN"  # type: ignore[index]

    with pytest.raises(gate.ExactnessError, match="SIDECAR_MISSING_EVIDENCE"):
        design.validate_design(changed)
    design.validate_design(original)
