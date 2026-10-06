"""T047/T053: local reference receipt, explicitly not complete qualification."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from formal.reference.non_isc import codec  # noqa: E402
from formal.reference.non_isc.authentication import authenticate  # noqa: E402
from formal.reference.non_isc.test_authentication import NonIscTests  # noqa: E402

OUT = ROOT / "formal/proposals/evidence/non-isc-source-v1"
PIN = "bb9fce957dae329701a8cd473a7148e198e1ca12"
CONTRACT = "docs/adr/0015-non-isc-authority-binding-v1.md"
CONTRACT_SHA = "f2e988d26a28ff8cedf74cc2265c535057e7ae37dc152002a853c75a0614710d"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    raw = subprocess.check_output(["git", "show", f"{PIN}:{CONTRACT}"], cwd=ROOT)
    if digest(raw) != CONTRACT_SHA:
        raise RuntimeError("Approved contract source mismatch")
    OUT.mkdir(parents=True, exist_ok=True)
    groups = {
        "non-isc": ["-m", "unittest", "formal.reference.non_isc.test_authentication", "-v"],
        "isc-regression": [
            "-m",
            "unittest",
            "formal.reference.isc_crypto.test_codec",
            "formal.reference.isc_crypto.test_signatures",
            "formal.reference.isc_crypto.test_public_vector",
            "formal.reference.isc_source.test_authentication",
            "-v",
        ],
        "source-audit": ["formal/proposals/isc-source-generation/audit_availability.py"],
    }
    checks = {}
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT), str(ROOT / "formal/reference/isc_crypto")]
    )
    for name, args in groups.items():
        run = subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=180,
        )
        log = run.stdout + run.stderr
        (OUT / (name + ".txt")).write_text(log, encoding="utf8", newline="\n")
        checks[name] = {"exit_code": run.returncode, "log_sha256": digest(log.encode())}
        if run.returncode:
            raise RuntimeError(log)
    NonIscTests.setUpClass()
    fixture = NonIscTests()
    vectors = []
    for kind in sorted(codec.KINDS):
        value = fixture.vote(kind)
        artifact = fixture.signed(value)
        verified = authenticate(fixture.authority, fixture.backend, artifact)
        record = codec.decode_artifact(artifact)
        vectors.append(
            {
                "kind": kind,
                "material": "PUBLIC_SYNTHETIC_NO_PRODUCTION_AUTHORITY",
                "vote_hex": verified.original_vote.hex(),
                "preimage_hex": codec.preimage(
                    record.registry_id, record.key_id, record.vote_bytes
                ).hex(),
                "artifact_hex": artifact.hex(),
                "vote_id": verified.vote_id,
                "artifact_id": verified.artifact_id,
            }
        )
    (OUT / "public-vectors.json").write_text(json.dumps(vectors, indent=2) + "\n", encoding="utf8")
    paths = sorted((ROOT / "formal/reference/non_isc").glob("*.py"))
    paths += [ROOT / "formal/reference/non_isc/README.md", Path(__file__)]
    paths += [Path(__file__).with_name("audit_availability.py")]
    # Include the unchanged imported primitive/grammar/registry sources, not
    # only the new wrapper files. Protocol/vector bytes never normalize.
    for directory in ("isc_crypto", "isc_source"):
        paths += sorted((ROOT / "formal/reference" / directory).glob("*.py"))
        paths += sorted((ROOT / "formal/reference" / directory).glob("*.json"))
    receipt = {
        "task_id": "ISC-S16-D01",
        "scope_revision": 5,
        "assignment_id": "91d05d0d-4fca-43e6-bd5e-7442d77e4ec0",
        "human_decision": "scope-decision-dff5cf14af975d7da34f29cfdc4a55c1",
        "approved_contract": {"commit": PIN, "path": CONTRACT, "sha256": CONTRACT_SHA},
        "reference_sources": {
            p.relative_to(ROOT).as_posix(): digest(p.read_bytes().replace(b"\r\n", b"\n"))
            for p in sorted(set(paths))
        },
        "source_hash_rule": (
            "UTF-8 tracked source text, CRLF to LF, matching Git blobs. "
            "Never applied to protocol/signature/vector binary bytes."
        ),
        "checks": checks,
        "vectors_sha256": digest((OUT / "public-vectors.json").read_bytes()),
        "source_audit_sha256": digest((OUT / "availability-boundary.json").read_bytes()),
        "result": "NON_ISC_SIGNATURE_REFERENCE_CHECKED_SOURCE_COMPOSITION_BLOCKED",
        "formal_status": "NO_GO",
        "r2_3": "OPEN",
        "qualification_limits": [
            "Reference byte/crypto component only; not all ADR0015 acceptance criteria.",
            "Pinned C Ed25519 runs from Python; cross-language codec qualification is open.",
            "No body/certificate/producer-cut or full source composition soundness theorem.",
            "Storage attestation source binding needs a semantic decision; no replacement exists.",
            "Full formal-check/mutant/refinement/report qualification is not run or claimed "
            "at this architecture STOP.",
            "Existing Lean/TLA/proofs and old reports remain unchanged; "
            "no concrete future sigma or deployment.",
        ],
    }
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf8")
    print(receipt["result"])


if __name__ == "__main__":
    main()
