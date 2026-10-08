"""T047/T053: the existing two close policies must come from original config.

The diagnostic uses newly constructed public synthetic objects. It is not a
production-reachable full snapshot, a TLC counterexample or R2 qualification.
Only fresh synthetic fixtures are made, with their own full signed config and
dependent identities. No production object is changed or relabeled.
"""

# The standalone evidence runner bootstraps the repository import root.
# ruff: noqa: E402

import copy
import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from formal.reference.isc_crypto import codec as crypto
from formal.reference.isc_source import identity as isc
from formal.reference.non_isc import codec as non_isc
from formal.reference.profile_source import configuration as cfg
from formal.reference.profile_source import configuration_qc as qc
from formal.reference.profile_source import input_history as history
from formal.reference.profile_source import manifest_context as manifests
from formal.reference.profile_source import scheduling
from formal.reference.profile_source import source_prefix as source
from formal.reference.profile_source.test_input_history import InputHistoryTests
from formal.reference.storage_source import codec as storage
from formal.reference.storage_source.test_codec import StorageSourceTests
from formal.scripts import native_source_artifacts as native

OUT = ROOT / "formal/proposals/evidence/close-policy-source-binding"
N = "60c692f6e391f839829dfc64e93380db54cd507b"
P = "26eb02d0632435c9aa0d8ef44eb496b6fa73dd13"
S = "1438fa3d78ec99291475cf4660fd8c190ac01bb3"
OBSERVED = "90561a97de7f41f409bf22065ad6cdc9b3932458"
C = "4555479c65161a901dd6582dea80ebd2521bb025"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def original(commit, path):
    return subprocess.check_output(
        ["cmd.exe", "/d", "/c", "git", "cat-file", "blob", commit + ":" + path], cwd=ROOT
    )


def diagnostic(choice):
    InputHistoryTests.setUpClass()
    x = InputHistoryTests()
    x.setUp()
    # Build a fresh two-ticket configuration and all dependent new artifacts.
    # No frozen fixture/signature/QC is edited or relabeled.
    value = cfg.decode(x.config)
    value["ticket_count"] = 2
    value["domain_ticket_counts"][0]["ticket_count"] = 2
    value["availability_policy"]["close_policy"] = choice
    config = cfg.encode(value)
    config_id = crypto.content_id(cfg.DOMAIN, config)
    artifacts = {}

    def put(kind, obj):
        raw = native.canonical(obj)
        key = native.content_id(raw, native.DOMAINS[kind])
        artifacts[key] = raw
        return key

    docs = {kind: (key, manifests.decode(raw)) for kind, key, raw in x.manifest.original_sources}
    for kind in ("schema", "profile", "scale", "plan"):
        key, obj = docs[kind]
        assert put(kind, obj) == key
    fixed = copy.deepcopy(docs["config"][1])
    fixed["base_round_config_id"] = config_id
    fixed_id = put("config", fixed)
    proof = copy.deepcopy(docs["proof"][1])
    proof["config_id"] = fixed_id
    proof_id = put("proof", proof)
    manifest = manifests.decode(x.manifest.original_manifest)
    manifest.update(round_config_id=fixed_id, proof_instance_id=proof_id)
    shard_bytes, refs = [], []
    for old_raw, old_ref in zip(x.raws, manifest["shards"], strict=True):
        header_size = int.from_bytes(old_raw[8:12], "little")
        header = manifests.decode(old_raw[16 : 16 + header_size])
        payload = old_raw[16 + header_size :]
        header.update(round_config_id=fixed_id, proof_instance_id=proof_id)
        hb = native.canonical(header)
        raw = struct.pack("<4sHHII", b"DRQ1", 1, 0, len(hb), len(payload)) + hb + payload
        refs.append(
            {
                **old_ref,
                "leaf_id": native.content_id(raw, native.DOMAINS["leaf"]),
                "envelope_bytes": len(raw),
            }
        )
        shard_bytes.append(raw)
    manifest.update(
        shards=refs,
        commitment_root=native.merkle_root([r["leaf_id"] for r in refs]),
        total_envelope_bytes=sum(map(len, shard_bytes)),
    )
    mid = put("manifest", manifest)
    resolved = manifests.resolve(artifacts, x.f.boot.formal_semantics_id, mid)
    for i, raw in enumerate(shard_bytes):
        manifests.read_q(artifacts, x.f.boot.formal_semantics_id, mid, i, raw)
    context = {
        **{k: x.plan.value[k] for k in ("parameter_schema_id", "parent_checkpoint_id")},
        "arithmetic_profile_id": resolved.profile_id,
        "round_config_id": config_id,
    }
    policy = scheduling.decode(x.plan.policies[0])
    policy.update(context, ticket_count=2, token_cursor_end=32)
    p = x.plan.value
    plan = scheduling.plan(
        (scheduling.canonical(policy),),
        context,
        p["assignment_policy_id"],
        p["capability_snapshot_root"],
        [(d["worker_id"], d["decision_id"]) for d in p["decisions"]],
        p["lease_policy"],
        x.f.boot.formal_semantics_id,
    )
    events = []

    def add(action, raw, inputs=(), actor=None):
        events.append(
            source.Event(
                len(events),
                actor or x.actor,
                action,
                raw,
                inputs,
                (),
                b"synthetic-diagnostic-descriptor",
            )
        )

    x.x.raw, x.x.body = config, value
    deliveries = tuple(x.x.delivery(i + 1, name) for i, name in enumerate(x.x.names))
    certificate = {
        **x.x.qc,
        "body_hash": config_id,
        "vote_ids": [
            crypto.content_id(non_isc.VOTE_DOMAIN, d.event.vote_frame) for d in deliveries
        ],
    }
    add("ACT-CONFIG-PROPOSE", config, (x.f.declaration,))
    for d in deliveries:
        add("ACT-MESSAGE-DELIVER", d.original_artifact)
    add("ACT-CONFIG-FINALIZE", qc.encode(certificate))
    for raw in plan.tickets:
        add("ACT-TICKET-ISSUE", raw, (plan.original, *plan.policies))
    add("ACT-COMMIT", artifacts[mid], (*artifacts.values(), plan.tickets[0]), "worker-1")
    commitment = history.ledger.Commitment(resolved.ticket_id, resolved.commitment_id)
    _, ac_context = manifests.bind_context(
        x.f.boot, x.f.storage_boot, config, x.f.declaration, artifacts, mid, commitment
    )
    sf = StorageSourceTests()
    sf.common, sf.value = storage.load(ac_context.common_bytes), ac_context
    ac, gs = sf.witness(
        sorted((leaf, f"storage-{n}") for leaf, _ in ac_context.required_leaves for n in (1, 2, 3))
    )
    for raw in gs:
        add("ACT-MESSAGE-DELIVER", raw)
    add("ACT-AVAIL-FINALIZE", ac, tuple(artifacts.values()))
    tuples = (
        isc.InputTuple(
            storage.content_id(storage.CERTIFICATE_DOMAIN, ac),
            resolved.commitment_id,
            resolved.domain_id,
            resolved.ticket_id,
        ),
    )
    body = isc.Body(
        x.f.boot.formal_semantics_id,
        resolved.profile_id,
        int(value["height"]),
        resolved.schema_id,
        config_id,
        value["round_id"],
        x.f.boot.validator_epoch_id,
        int(value["view"]),
        resolved.parent_id,
        isc.input_root(tuples),
        tuples,
    )
    add("ACT-INPUT-CLOSE", isc.body_preimage(body))
    result = history.reconstruct(
        tuple(events),
        x.f.boot,
        x.f.storage_boot,
        x.f.backend,
        plan,
        config,
        x.f.declaration,
        actor=x.actor,
    )
    outcome = {
        "closed_bodies": len(result.closed),
        "unresolved_original_indices": [e.index for e in result.unresolved],
        "last_disposition": result.dispositions[-1][1],
        "retained_events": len(result.ledger.events),
        "accepted_ac": len(result.ledger.availabilities),
    }
    omit = choice == "OMIT_UNAVAILABLE"
    assert len(result.closed) == int(omit)
    assert outcome["unresolved_original_indices"] == ([] if omit else [len(events) - 1])
    assert outcome["accepted_ac"] == 1 and outcome["retained_events"] == len(events)
    return {
        "classification": "SYNTHETIC_COMPONENT_DIAGNOSTIC_NOT_FULL_PRODUCTION_HISTORY",
        "configured_tickets": [scheduling.decode(raw)["ticket_id"] for raw in plan.tickets],
        "accepted_ac_tickets": [resolved.ticket_id],
        "original_config_hex": config.hex(),
        "config_id": config_id,
        "closed_body_hex": isc.body_preimage(body).hex(),
        "b": isc.body_id(body),
        "original_event_bytes": [
            {
                "index": e.index,
                "action": e.action,
                "actor": e.actor,
                "raw_sha256": sha(e.original),
                "input_sha256": [sha(raw) for raw in e.inputs],
            }
            for e in events
        ],
        "policy_from_authenticated_original_config": choice,
        "outcome": outcome,
        "limitations": [
            "No full genesis/lease/phase/durability claim",
            "No executed production or TLC counterexample",
            "ABORT-required is the normative close-policy branch, not an emitted AbortQC",
            "Fresh synthetic configs have different signed bytes and dependent IDs; "
            "there is no free close-policy argument and no legacy relabeling",
        ],
    }


def main():
    paths = {
        N: [
            "delta-protocol/schemas/003/protocol-types-v1.json",
            "delta-core-cpp/include/delta/core/consensus.hpp",
            "delta-core-cpp/src/consensus.cpp",
            "delta-core-cpp/src/certificates/vote_admission.cpp",
            "specs/000-formal-tla-spec/failure-semantics.md",
            "specs/003-bft-round-state-machine/spec.md",
        ],
        P: ["docs/adr/0013-snapshot-provenance-profile-v1.md"],
        S: ["docs/adr/0016-storage-availability-source-binding-v1.md"],
        OBSERVED: ["docs/adr/0018-authenticated-availability-contract-v1.md"],
        C: [
            "formal/scripts/native_input_ledger.py",
            "formal/proofs/DeltaReduce/PublicAuthority.lean",
            "formal/tla/DeltaReduceCertificates.tla",
            "docs/adr/0014-isc-producer-integration-v1.md",
        ],
        "12326b892690705b7141fcd32bf3f32cf07d092e": [
            "formal/proposals/retention-policy-source-binding-v1.md"
        ],
    }
    sources = []
    for commit, names in paths.items():
        for path in names:
            raw = original(commit, path)
            sources.append(
                {"commit": commit, "path": path, "sha256": sha(raw), "byte_length": len(raw)}
            )
    protocol = json.loads(original(N, paths[N][0]))
    fields = [
        v["name"]
        for v in next(t for t in protocol["types"] if t["type_name"] == "ROUND_CONFIG")["fields"]
    ]
    assert len(fields) == 22 and "availability_policy" not in fields
    diagnostics = {name: diagnostic(name) for name in ("OMIT_UNAVAILABLE", "ABORT_ON_INCOMPLETE")}
    assert (
        diagnostics["OMIT_UNAVAILABLE"]["config_id"]
        != diagnostics["ABORT_ON_INCOMPLETE"]["config_id"]
    )
    assert diagnostics["OMIT_UNAVAILABLE"]["b"] != diagnostics["ABORT_ON_INCOMPLETE"]["b"]
    current_sources = []
    for base in (
        "formal/reference/profile_source",
        "formal/reference/storage_source",
        "formal/reference/non_isc",
        "formal/reference/isc_source",
        "formal/reference/isc_crypto",
    ):
        for path in sorted((ROOT / base).glob("*.py")):
            raw = path.read_bytes()
            current_sources.append({"path": path.relative_to(ROOT).as_posix(), "sha256": sha(raw)})
    current_sources.append(
        {
            "path": Path(__file__).relative_to(ROOT).as_posix(),
            "sha256": sha(Path(__file__).read_bytes()),
        }
    )
    out = {
        "task_ids": ["T047", "T053"],
        "kind": "SOURCE_BINDING_AUDIT_NOT_QUALIFICATION",
        "sources": sources,
        "native_round_config_fields": fields,
        "current_source_sha256": current_sources,
        "diagnostics": diagnostics,
        "r2_3": "OPEN",
        "formal_status": "NO_GO",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "audit.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf8")
    print(
        json.dumps(
            {
                "diagnostics": {k: v["outcome"] for k, v in diagnostics.items()},
                "r2_3": "OPEN",
                "formal_status": "NO_GO",
            }
        )
    )


if __name__ == "__main__":
    main()
