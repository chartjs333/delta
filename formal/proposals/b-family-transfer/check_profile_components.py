"""T047/T053: reproducible profile source components, NOT R2.3 closure or Formal GO."""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
BUILD = ROOT / "formal/build/profile-source-components"
OUT = ROOT / "formal/proposals/evidence/profile-source-components"
LEAN = Path(os.environ.get("FAMILY_LEAN", "D:/formal-tools-20260920/lean/bin/lean.exe"))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    src, objects = BUILD / "source", BUILD / "objects"
    sources, order, checks = {}, [], []

    def visit(name):
        if name in order or name in {"Init", "Std"}:
            return
        if name == "SourcePolicy":
            path = ROOT / "formal/proposals/isc-source-generation/SourcePolicy.lean"
        elif name in {"ProfileSource", "ProfileControl", "ProfileManifest"}:
            path = Path(__file__).with_name(name + ".lean")
        else:
            path = ROOT / "formal/proofs" / (name.replace(".", "/") + ".lean")
        if name not in {
            "ProfileSource",
            "ProfileControl",
            "ProfileManifest",
            "SourcePolicy",
        } and not name.startswith("DeltaReduce."):
            raise RuntimeError("Unqualified import " + name)
        raw = path.read_bytes().replace(b"\r\n", b"\n")
        sources[path.relative_to(ROOT).as_posix()] = digest(raw)
        for child in re.findall(r"^import\s+(\S+)", raw.decode(), re.M):
            visit(child)
        destination = src / (name.replace(".", "/") + ".lean")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
        order.append(name)

    def run(command, log_name, cwd=ROOT, env=None):
        proc = subprocess.run(
            command, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf8", timeout=300
        )
        log = proc.stdout + proc.stderr
        (OUT / log_name).write_text(log, encoding="utf8", newline="\n")
        checks.append(
            {"log": log_name, "exit_code": proc.returncode, "sha256": digest(log.encode())}
        )
        if proc.returncode or "sorryAx" in log or "declaration uses 'sorry'" in log:
            raise RuntimeError(log)
        return log

    visit("ProfileControl")
    visit("ProfileManifest")
    visit("SourcePolicy")
    environment = dict(os.environ, LEAN_PATH=str(objects))
    version = subprocess.check_output([str(LEAN), "--version"], text=True).strip()
    if "version 4.32.1" not in version:
        raise RuntimeError("Unqualified Lean version " + version)
    for name in order:
        target = objects / (name.replace(".", "/") + ".olean")
        target.parent.mkdir(parents=True, exist_ok=True)
        run(
            [str(LEAN), "-o", str(target), name.replace(".", "/") + ".lean"],
            name + ".txt",
            src,
            environment,
        )
        print("checked " + name, flush=True)
    names = [
        "resolvedOriginal",
        "resolvedDigest",
        "substitutionRequiresDigestCollision",
        "resolveAllLength",
        "resolveAllPosition",
        "repeatedOccurrenceKept",
        "checkedOrigin",
        "Wal.annotationRetainsOriginals",
        "Wal.annotationLength",
        "Wal.annotationAppend",
        "Wal.position",
        "Wal.mixed1232",
        "Wal.distinctPhysicalPositions",
        "Wal.noEntryCollapse",
        "Control.checked",
        "Control.complete",
        "Control.originalBytesCannotBeSubstituted",
        "Control.rootFieldsExact",
        "Control.profileIndependentOfImportedVersion",
    ]
    audit = "import ProfileControl\nimport ProfileManifest\nimport SourcePolicy\n" + "".join(
        "#print axioms DeltaReduce.ProfileSource." + name + "\n" for name in names
    )
    audit += "".join(
        "#print axioms DeltaReduce.ProfileManifest." + name + "\n"
        for name in (
            "checked",
            "complete",
            "originalBytes",
            "completeOrderedReferences",
            "completeOrderedRoot",
            "originalPlan",
            "atUseExistingBinding",
            "existingBindingReusable",
            "atUseOriginalLengths",
            "Observations.decodedOriginalBinding",
            "Observations.existingBindingComplete",
            "Observations.eventPrefixRetained",
            "Observations.stepProvenance",
            "Observations.runProvenance",
            "Observations.selectedCoordinates",
            "Observations.runRetainsAllEvents",
            "Observations.selectedOriginalPosition",
            "Observations.selectedActualBinding",
            "Observations.processLostCannotReuse",
            "Observations.releaseCannotReuse",
            "Observations.externalLossRetainsOwned",
            "Observations.failedReadRetainsOwned",
        )
    )
    audit += "".join(
        "#print axioms DeltaReduce.ISCSourceV2." + name + "\n"
        for name in (
            "boundCertificateSource",
            "bindCertificateComplete",
            "boundOrderedMerkle",
            "boundOriginalTuples",
            "boundExplicitParent",
            "boundSignerQuorum",
            "noncanonicalCertificateRejected",
            "merkleLevelComplete",
            "merkleFuelComplete",
            "approvedInputBoundComplete",
            "snapshotLineageRetained",
            "fullPolicyOutsideSnapshotRetained",
        )
    )
    (src / "Audit.lean").write_text(audit, encoding="utf8", newline="\n")
    log = run([str(LEAN), "Audit.lean"], "axioms.txt", src, environment)
    for group in re.findall(r"depends on axioms:\s*\[([^]]*)\]", log, re.S):
        if set(group.replace("\n", "").replace(" ", "").split(",")) - {
            "",
            "propext",
            "Classical.choice",
            "Quot.sound",
        }:
            raise RuntimeError("Unexpected axiom " + group)
    from formal.reference.profile_source.control_vectors import generate

    vector_source, vector_originals = generate()
    (src / "ControlVectors.lean").write_text(vector_source, encoding="utf8", newline="\n")
    (OUT / "control-originals.json").write_text(
        json.dumps(vector_originals, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    run([str(LEAN), "ControlVectors.lean"], "control-vectors.txt", src, environment)
    sources["generated/ControlVectors.lean"] = digest(vector_source.encode())
    from formal.reference.profile_source.isc_vectors import generate as generate_isc

    isc_source, isc_originals = generate_isc()
    (src / "ISCVectors.lean").write_text(isc_source, encoding="utf8", newline="\n")
    (OUT / "isc-originals.json").write_text(
        json.dumps(isc_originals, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    run([str(LEAN), "ISCVectors.lean"], "isc-vectors.txt", src, environment)
    sources["generated/ISCVectors.lean"] = digest(isc_source.encode())
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "formal/reference/profile_source",
            "-t",
            ".",
            "-v",
        ],
        "reference-tests.txt",
    )
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "formal/reference/isc_source",
            "-t",
            ".",
            "-v",
        ],
        "isc-reference-tests.txt",
    )
    paths = [
        "formal/reference/profile_source",
        "formal/reference/isc_source",
        str(Path(__file__).relative_to(ROOT)),
    ]
    run([sys.executable, "-m", "ruff", "check", *paths], "ruff.txt")
    run([sys.executable, "-m", "ruff", "format", "--check", *paths], "ruff-format.txt")
    inputs = [
        *sorted((ROOT / "formal/reference/profile_source").glob("*.py")),
        ROOT / "formal/proposals/b-family-transfer/profile-v1.schema.json",
        ROOT / "formal/reference/profile_source/README.md",
        Path(__file__),
        ROOT / "formal/scripts/native_source_artifacts.py",
        ROOT / "delta-protocol/fixtures/004/cross-language/golden-v1.json",
        ROOT / "delta-protocol/fixtures/local-round/parameter-schema-v1.json",
        ROOT / "docs/adr/evidence/0014-isc-commitment-profile-v1-vectors.json",
        *sorted((ROOT / "delta-protocol/schemas/004").glob("*.json")),
    ]
    # Every imported project reference component is pinned, including synthetic
    # fixture inputs. No cached result substitutes for the current source hashes.
    for directory in ("isc_crypto", "isc_source", "isc_w1", "non_isc", "storage_source"):
        inputs.extend(
            p
            for p in sorted((ROOT / "formal/reference" / directory).iterdir())
            if p.suffix in (".py", ".json")
        )
    for path in inputs:
        sources[path.relative_to(ROOT).as_posix()] = digest(
            path.read_bytes().replace(b"\r\n", b"\n")
        )
    backend = json.loads(
        (ROOT / "formal/reference/isc_crypto/library-provenance.json").read_text()
    )["dll"]["sha256"]
    if digest(Path(os.environ["ISC_SODIUM_DLL"]).read_bytes()) != backend:
        raise RuntimeError("Unqualified crypto backend")
    receipt = {
        "task_ids": ["T047", "T053", "ISC-S16-D01"],
        "scope_revision": 13,
        "assignment_id": "13069d7e-a148-475a-bd49-9885bf2f283d",
        "result": "PROFILE_BYTE_AUTHORITY_AND_WAL_COMPONENTS_CHECKED",
        "formal_status": "NO_GO",
        "r2_3": "OPEN",
        "reviewed_r2_closure": False,
        "lean": version,
        "backend_sha256": backend,
        "source_hash_rule": "Git LF source text; protocol originals retained without normalization",
        "sources": sources,
        "checks": checks,
        "established": [
            "Closed canonical profile fields, independent raw inventory, exact refs and floor",
            "Separate anchor/cut/target journals retain original bytes; anchor may precede tip",
            "Bootstrap/initial-config authority, full RoundConfig with R/E and signed QC join",
            "Mixed slots and S-RANK retain original votes and unsigned durable intents",
            "General Lean original reference/position/multiplicity and rank injectivity lemmas",
            "Kernel whole control-byte binding and closed root names; synthetic raw vectors",
            "Source-derived storage context: whole config + original metadata + commitment root",
            "O ledger facet retains every delivery/attempt; no physical-presence premise",
            "Metadata/data-use Lean join reuses existing full ordered unsplit vector binding",
            "Original CONFIG event cut and first witness, late/repeat inventory retained",
            "Complete source event/input materialization with original cut/target positions",
            "Future whole ISC C bytes and policy tree, exact b/c, explicit parent and tuple root",
            "Merkle fuel completeness for all existing 100000 tuples; no 4096 manifest cap",
            "W1 whole byte output join: exact predecessor, all deliveries, P1/C/effects/receipt",
            "O actual read ownership from complete prefix; general binding, release/crash refusal",
        ],
        "not_established": [
            "Profile JSON/CONFIG/QC codecs are not yet joined to a complete Lean source decoder",
            "Full native origin from genesis; signatures do not prove finalization origin",
            "Complete O state relation, totality, initial/incomplete and ABORT composition",
            "Reviewed R2.3, named recovery theorem, full formal gates or production GO",
        ],
        "evidence_kind": "REFERENCE_SYNTHETIC_COMPONENTS_NOT_PRODUCTION_CAPTURE",
    }
    (OUT / "receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    print(receipt["result"], flush=True)


if __name__ == "__main__":
    main()
