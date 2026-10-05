"""ISC-S16-D01 / T047 T053: source-generation compatibility audit, never GO.
Freshly checks existing Lean declarations; creates no theorem or protocol rule.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "26eb02d0632435c9aa0d8ef44eb496b6fa73dd13"
NATIVE = "60c692f6e391f839829dfc64e93380db54cd507b"
BUILD = ROOT / "formal/build/isc-s16-source-generation-audit"
OUT = ROOT / "formal/proposals/evidence/isc-s16-source-generation"
LEAN = Path(os.environ.get("FAMILY_LEAN", "D:/formal-tools-20260920/lean/bin/lean.exe"))


def blob(commit, path):
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def run():
    BUILD.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    pins = {}

    def source(commit, path):
        raw = blob(commit, path)
        pins[f"{commit}:{path}"] = digest(raw)
        return raw.decode("utf-8")

    profile = source(BASE, "docs/adr/0013-snapshot-provenance-profile-v1.md")
    assert "60c692f6e391f839829dfc64e93380db54cd507b" in profile
    capsule = source(BASE, "docs/adr/0014-isc-finalization-wal-capsule-v1.md")
    assert "snapshot.input_set_certificates` и **b**" in capsule
    native = source(NATIVE, "delta-core-cpp/src/certificates/vote_admission.cpp")
    assert re.search(
        r"require_subset\(\s*snapshot.finalized_input_set_ids,\s*snapshot.input_set_certificates,\s*input_qc_id,",
        native,
    )
    runtime = source(NATIVE, "delta-runtime-cpp/src/runtime.cpp")
    assert "entry.wal_record_bytes == vote_policy_identity_" in runtime
    for name in (
        "0014-isc-contract-freeze-v1.md",
        "0014-isc-producer-integration-v1.md",
        "0014-isc-production-contract-amendment-v1.md",
        "0013-r2-3-implementation-plan.md",
    ):
        source(BASE, "docs/adr/" + name)
    source(BASE, "formal/proofs/DeltaReduce/NativeConfigReplay.lean")
    fixture_path = "formal/proposals/native-certificate-chain-vectors.json"
    fixture = json.loads(source(BASE, fixture_path))
    # Existing codecs only; prevent silently checking different working sources.
    for name in ("native_certificate_chain.py", "native_isc_body.py", "formal_artifacts.py"):
        raw = blob(BASE, "formal/scripts/" + name)
        live = (ROOT / "formal/scripts" / name).read_bytes()
        assert live.replace(b"\r\n", b"\n") == raw.replace(b"\r\n", b"\n")
        pins[f"{BASE}:formal/scripts/{name}"] = digest(raw)
    sys.path.insert(0, str(ROOT / "formal/scripts"))
    from native_certificate_chain import decode_certificate, voted_body

    c = fixture["components"]["certificates"]["ISC"]["id"]
    raw = fixture["artifact_ascii"][c].encode("ascii")
    cert = decode_certificate(raw, c, "INPUT_SET_CERTIFICATE")
    b = voted_body(cert)["body_id"]
    assert b == fixture["components"]["bodies"]["ISC"] and b != c
    assert set([c]).issubset({c}) and not set([b]).issubset({c})
    # Rebuild exact original transitive closure, no reuse of cached oleans.
    seen, order, external = set(), [], set()
    src, objects = BUILD / "source", BUILD / "objects"

    def visit(name):
        if name in seen:
            return
        seen.add(name)
        if name == "Std":
            external.add(name)
            return
        assert name.startswith("DeltaReduce.")
        path = "formal/proofs/" + name.replace(".", "/") + ".lean"
        text = source(BASE, path)
        for child in re.findall(r"^import\s+(\S+)", text, re.M):
            visit(child)
        dst = src / (name.replace(".", "/") + ".lean")
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text, encoding="utf-8", newline="\n")
        order.append(name)

    visit("DeltaReduce.NativeIscCertificateVectors")
    env = dict(os.environ, LEAN_PATH=str(objects))
    version = subprocess.check_output([str(LEAN), "--version"], text=True).strip()
    assert "version 4.32.1" in version
    commands = []
    for name in order:
        rel = name.replace(".", "/")
        target = objects / (rel + ".olean")
        target.parent.mkdir(parents=True, exist_ok=True)
        cmd = [str(LEAN), "-o", str(target), rel + ".lean"]
        result = subprocess.run(
            cmd, cwd=src, env=env, text=True, encoding="utf-8", capture_output=True, timeout=240
        )
        log = result.stdout + result.stderr
        log_path = OUT / (name + ".txt")
        log_path.write_text(log, encoding="utf-8", newline="\n")
        assert result.returncode == 0 and "sorryAx" not in log, (name, log)
        commands.append(
            {
                "module": name,
                "exit_code": result.returncode,
                "source_sha256": pins[f"{BASE}:formal/proofs/{rel}.lean"],
                "log_sha256": digest(log_path.read_bytes()),
            }
        )
        print("checked existing " + name, flush=True)
    audit = src / "Audit.lean"
    audit.write_text(
        "import DeltaReduce.NativeIscCertificateVectors\n"
        "#print axioms DeltaReduce.NativeIscCertificateVectors.bodyIdIsNotFinalizedQc\n"
        "#print axioms DeltaReduce.NativeIscCertificateVectors.distinctIds\n"
        "#print axioms DeltaReduce.NativeFinalizedIscSection.noInventedFinalized\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [str(LEAN), "Audit.lean"],
        cwd=src,
        env=env,
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=120,
    )
    log = result.stdout + result.stderr
    assert result.returncode == 0 and "sorryAx" not in log, log
    (OUT / "axioms.txt").write_text(log, encoding="utf-8", newline="\n")
    evidence = {
        "task_id": "ISC-S16-D01",
        "requirements": ["T047", "T053"],
        "source_base": BASE,
        "native_source_pin": NATIVE,
        "source_sha256": pins,
        "status": "SOURCE_GENERATION_JOIN_UNQUALIFIED",
        "formal_status": "NO_GO",
        "r2_3": "OPEN",
        "scope_revision": 2,
        "r2_3_authorized": True,
        "fixture_provenance": fixture["provenance"],
        "diagnostic": {
            "certificate_id_c": c,
            "body_id_b": b,
            "certificate_count": 1,
            "finalized_count": 1,
            "legacy_membership_c": True,
            "cross_generation_membership_b": False,
            "original_signers": cert["signer_ids"],
            "old_objects_unchanged": True,
        },
        "claim": (
            "Existing c-based finalized-section predicate rejects direct substitution of b; "
            "W1 specifies b only for its future semantics generation. "
            "This diagnostic does not instantiate that future generation or prove "
            "a reachable production/profile counterexample."
        ),
        "existing_theorems_rechecked": [
            "DeltaReduce.NativeIscCertificateVectors.bodyIdIsNotFinalizedQc",
            "DeltaReduce.NativeIscCertificateVectors.distinctIds",
            "DeltaReduce.NativeFinalizedIscSection.noInventedFinalized",
        ],
        "lean_version": version,
        "lean_commands": commands,
        "external_imports": sorted(external),
        "axiom_log_sha256": digest((OUT / "axioms.txt").read_bytes()),
        "native_runtime_executed": False,
        "new_proof_or_semantics_created": False,
        "profile_reachability_counterexample_claimed": False,
        "r2_1_r2_2_reopened": False,
        "sigma_next_assigned": False,
        "complete_source_origin_proved": False,
        "full_state_bounds_proved": False,
        "formal_go_claimed": False,
        "independent_attestation_claimed": False,
    }
    (OUT / "audit.json").write_text(
        json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": evidence["status"],
                "diagnostic": evidence["diagnostic"],
                "kernel_axiom_audit": log,
            }
        )
    )


if __name__ == "__main__":
    run()
