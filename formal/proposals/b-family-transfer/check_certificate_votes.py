"""T047/T053: qualify original certificate/delivery-cut source joins, without full R2.3 claims."""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
BUILD = ROOT / "formal/build/profile-certificate-votes"
OUT = ROOT / "formal/proposals/evidence/profile-certificate-votes"
LEAN = Path(os.environ.get("FAMILY_LEAN", "D:/formal-tools-20260920/lean/bin/lean.exe"))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    src, objects = BUILD / "source", BUILD / "objects"
    OUT.mkdir(parents=True, exist_ok=True)
    sources, order, checks = {}, [], []

    def visit(name):
        if name in order or name in {"Init", "Std"}:
            return
        if name.startswith("DeltaReduce."):
            path = ROOT / "formal/proofs" / (name.replace(".", "/") + ".lean")
        elif name in {"SourcePolicy", "SourceVote"}:
            path = ROOT / "formal/proposals/isc-source-generation" / (name + ".lean")
        elif name.startswith("Profile") and re.fullmatch(r"Profile[A-Za-z]+", name):
            path = Path(__file__).with_name(name + ".lean")
        else:
            raise RuntimeError("Unexpected project dependency " + name)
        raw = path.read_bytes().replace(b"\r\n", b"\n")
        sources[path.relative_to(ROOT).as_posix()] = digest(raw)
        if re.search(
            r"\b(sorry|axiom)\b",
            re.sub(r"/-.*?-/|--[^\n]*", "", raw.decode(), flags=re.DOTALL),
        ):
            raise RuntimeError("Unproved source declaration " + name)
        for child in re.findall(r"^import\s+(\S+)", raw.decode(), re.MULTILINE):
            visit(child)
        destination = src / (name.replace(".", "/") + ".lean")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
        order.append(name)

    def run(command, name, cwd=ROOT, env=None):
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf8",
                timeout=300,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            partial = error.stdout or b""
            if isinstance(partial, bytes):
                partial = partial.decode("utf8", errors="replace")
            (OUT / name).write_text("TIMEOUT 300s\n" + partial, encoding="utf8", newline="\n")
            raise
        log = result.stdout + result.stderr
        (OUT / name).write_text(log, encoding="utf8", newline="\n")
        checks.append(
            {
                "log": name,
                "exit_code": result.returncode,
                "sha256": digest(log.encode()),
            }
        )
        if result.returncode:
            raise RuntimeError("Qualification failed " + name)
        return log

    visit("ProfileCertificateVotes")
    visit("ProfilePlanMembers")
    visit("ProfileSelectedVote")
    visit("ProfileCurrent")
    environment = dict(os.environ, LEAN_PATH=str(objects))
    version = run([str(LEAN), "--version"], "lean-version.txt").strip()
    for name in order:
        output = objects / (name.replace(".", "/") + ".olean")
        output.parent.mkdir(parents=True, exist_ok=True)
        run(
            [str(LEAN), "-o", str(output), name.replace(".", "/") + ".lean"],
            "module-" + name + ".txt",
            src,
            environment,
        )

    raw = Path(__file__).with_name("ProfileCertificateVotes.lean").read_text(encoding="utf8")
    declarations = re.findall(r"^(?:def|theorem) (\w+)", raw, re.MULTILINE)
    required = {
        "boundSource",
        "boundComplete",
        "eachSignerHasOriginal",
        "preservesWitness",
        "distinctWitnessesStayDistinct",
        "originalSource",
        "wholeCount",
        "everyOriginalAt",
        "futureDeliveryDoesNotChangeCut",
        "eventBound",
        "eventComplete",
        "originalFinalizationCut",
    }
    if not required <= set(declarations):
        raise RuntimeError("Required certificate source result missing")
    audit = "import ProfileCertificateVotes\n" + "".join(
        "#print axioms DeltaReduce.ProfileSource.CertificateVotes." + name + "\n"
        for name in declarations
    )
    member_source = Path(__file__).with_name("ProfilePlanMembers.lean").read_text(encoding="utf8")
    member_declarations = re.findall(r"^(?:def|theorem) (\w+)", member_source, re.MULTILINE)
    audit = (
        "import ProfilePlanMembers\n"
        + audit
        + "".join(
            "#print axioms DeltaReduce.ProfileSource.PlanMembers." + name + "\n"
            for name in member_declarations
        )
    )
    state_declarations = {}
    for module in ("InstalledState", "SelectedVote", "Current"):
        content = Path(__file__).with_name("Profile" + module + ".lean").read_text(encoding="utf8")
        names = re.findall(r"^(?:def|theorem) (\w+)", content, re.MULTILINE)
        state_declarations[module] = names
        audit = "import Profile" + module + "\n" + audit
        audit += "".join(
            "#print axioms DeltaReduce.ProfileSource." + module + "." + name + "\n"
            for name in names
        )
    (src / "Audit.lean").write_text(audit, encoding="utf8", newline="\n")
    log = run([str(LEAN), "Audit.lean"], "axioms.txt", src, environment)
    if any(
        "DeltaReduce.ProfileSource.CertificateVotes." + name not in log for name in declarations
    ):
        raise RuntimeError("Incomplete axiom audit output")
    if any(
        "DeltaReduce.ProfileSource.PlanMembers." + name not in log for name in member_declarations
    ):
        raise RuntimeError("Incomplete member axiom audit output")
    for module, names in state_declarations.items():
        if any("DeltaReduce.ProfileSource." + module + "." + name not in log for name in names):
            raise RuntimeError("Incomplete state axiom audit output")
    for group in re.findall(r"depends on axioms:\s*\[([^]]*)\]", log):
        if set(group.replace(" ", "").replace("\n", "").split(",")) - {
            "propext",
            "Classical.choice",
            "Quot.sound",
            "",
        }:
            raise RuntimeError("Unexpected axiom " + group)
    sources["generated/Audit.lean"] = digest(audit.encode())

    from formal.reference.profile_source.certificate_vote_vectors import generate

    vectors, originals = generate()
    (src / "CertificateVoteVectors.lean").write_text(vectors, encoding="utf8", newline="\n")
    (OUT / "originals.json").write_text(
        json.dumps(originals, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    run(
        [
            str(LEAN),
            "-o",
            str(objects / "CertificateVoteVectors.olean"),
            "CertificateVoteVectors.lean",
        ],
        "kernel-vectors.txt",
        src,
        environment,
    )
    sources["generated/CertificateVoteVectors.lean"] = digest(vectors.encode())
    # Build the original synthetic definitions afresh. Their prior independent
    # examples are qualified by profile-source-components; this runner checks
    # the new full typed join, without reusing opaque cached .olean artifacts.
    from importlib import import_module

    for module, stem in (
        ("input_section_vectors", "InputSectionVectors"),
        ("lineage_vectors", "LineageVectors"),
        ("eligibility_vectors", "EligibilityVectors"),
        ("plan_vectors", "PlanVectors"),
        ("parameter_vectors", "ParameterVectors"),
        ("aggregate_vectors", "AggregateVectors"),
        ("apply_vectors", "ApplyVectors"),
        ("collections_vectors", "CollectionsVectors"),
    ):
        original, _ = import_module("formal.reference.profile_source." + module).generate()
        definitions = re.sub(
            r"^example\b[\s\S]*?(?=^(?:def |end |example |namespace |open |set_option )|\Z)",
            "",
            original,
            flags=re.MULTILINE,
        )
        if re.search(r"^example\b", definitions, re.MULTILINE):
            raise RuntimeError("Unexpected generated example partition")
        (src / (stem + ".lean")).write_text(definitions, encoding="utf8", newline="\n")
        sources["generated/" + stem + ".lean"] = digest(definitions.encode())
        run(
            [str(LEAN), "-o", str(objects / (stem + ".olean")), stem + ".lean"],
            "definitions-" + stem + ".txt",
            src,
            environment,
        )
    from formal.reference.profile_source.typed_certificate_vectors import generate as typed_vectors

    typed = typed_vectors()
    (src / "TypedCertificateVectors.lean").write_text(typed, encoding="utf8", newline="\n")
    run([str(LEAN), "TypedCertificateVectors.lean"], "typed-join.txt", src, environment)
    sources["generated/TypedCertificateVectors.lean"] = digest(typed.encode())
    from formal.reference.profile_source.installed_state_vectors import (
        generate as installed_vectors,
    )

    installed, state_originals = installed_vectors()
    (src / "InstalledStateVectors.lean").write_text(installed, encoding="utf8", newline="\n")
    (OUT / "installed-state.json").write_text(
        json.dumps(state_originals, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    run([str(LEAN), "InstalledStateVectors.lean"], "installed-state.txt", src, environment)
    sources["generated/InstalledStateVectors.lean"] = digest(installed.encode())
    from formal.reference.profile_source.current_vectors import generate as current_vectors

    modules, current, current_originals = current_vectors()
    for stem, text in modules.items():
        definitions = re.sub(
            r"^example\b[\s\S]*?(?=^(?:def |end |example |namespace |open |set_option )|\Z)",
            "",
            text,
            flags=re.MULTILINE,
        )
        if re.search(r"^example\b", definitions, re.MULTILINE):
            raise RuntimeError("Unexpected current fixture example partition")
        (src / (stem + ".lean")).write_text(definitions, encoding="utf8", newline="\n")
        sources["generated/" + stem + ".lean"] = digest(definitions.encode())
        run(
            [str(LEAN), "-o", str(objects / (stem + ".olean")), stem + ".lean"],
            "definitions-" + stem + ".txt",
            src,
            environment,
        )
    (src / "CurrentVectors.lean").write_text(current, encoding="utf8", newline="\n")
    (OUT / "current.json").write_text(
        json.dumps(current_originals, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    sources["generated/CurrentVectors.lean"] = digest(current.encode())
    # Each exact kernel assertion gets a fresh process so elaboration of a
    # preceding full-state example does not retain its large reduction graph.
    # The definitions and all original assertions remain identical; none is
    # weakened, evaluated only with #eval, or dropped to fit memory/time.
    pattern = r"^example\b[\s\S]*?(?=^(?:def |end |example |namespace |open |set_option )|\Z)"
    assertions = re.findall(pattern, current, flags=re.MULTILINE)
    if len(assertions) != 5:
        raise RuntimeError("Changed complete current assertion inventory")
    definitions = re.sub(pattern, "", current, flags=re.MULTILINE)
    (src / "CurrentDefinitions.lean").write_text(definitions, encoding="utf8", newline="\n")
    sources["generated/CurrentDefinitions.lean"] = digest(definitions.encode())
    run(
        [str(LEAN), "-o", str(objects / "CurrentDefinitions.olean"), "CurrentDefinitions.lean"],
        "current-definitions.txt",
        src,
        environment,
    )
    for index, assertion in enumerate(assertions):
        case = (
            "import CurrentDefinitions\nopen DeltaReduce.ProfileSource\n"
            "set_option maxRecDepth 30000\nset_option maxHeartbeats 8000000\n"
            "namespace CurrentVectors\n" + assertion + "end CurrentVectors\n"
        )
        name = "CurrentCase" + str(index) + ".lean"
        (src / name).write_text(case, encoding="utf8", newline="\n")
        sources["generated/" + name] = digest(case.encode())
        run([str(LEAN), name], "current-case-" + str(index) + ".txt", src, environment)
    paths = [
        "formal/reference/profile_source/certificate_vote_vectors.py",
        "formal/reference/profile_source/typed_certificate_vectors.py",
        "formal/reference/profile_source/installed_state_vectors.py",
        "formal/reference/profile_source/current_vectors.py",
        *(
            "formal/reference/profile_source/" + name + "_vectors.py"
            for name in (
                "input_section",
                "lineage",
                "eligibility",
                "plan",
                "parameter",
                "aggregate",
                "apply",
                "collections",
            )
        ),
        str(Path(__file__).relative_to(ROOT)),
    ]
    run([sys.executable, "-m", "ruff", "check", *paths], "ruff.txt")
    run([sys.executable, "-m", "ruff", "format", "--check", *paths], "ruff-format.txt")
    # Pin complete reference inputs used by the generator/native cross-check.
    for folder in (
        "profile_source",
        "isc_source",
        "isc_crypto",
        "isc_w1",
        "storage_source",
        "non_isc",
    ):
        for path in sorted((ROOT / "formal/reference" / folder).iterdir()):
            if path.suffix not in {".py", ".json"}:
                continue
            sources[path.relative_to(ROOT).as_posix()] = digest(
                path.read_bytes().replace(b"\r\n", b"\n")
            )
    for path in (
        Path(__file__),
        ROOT / "delta-protocol/fixtures/004/cross-language/golden-v1.json",
        ROOT / "delta-protocol/fixtures/007/cross-language/golden-v1.json",
    ):
        sources[path.relative_to(ROOT).as_posix()] = digest(
            path.read_bytes().replace(b"\r\n", b"\n")
        )

    receipt = {
        "task_ids": ["T047", "T053", "ISC-S16-D01"],
        "assignment_id": "13069d7e-a148-475a-bd49-9885bf2f283d",
        "scope_revision": 13,
        "result": "CERTIFICATE_ORIGINAL_CUT_COMPONENT_CHECKED",
        "formal_status": "NO_GO",
        "r2_3": "OPEN",
        "reviewed_r2_closure": False,
        "lean": version,
        "sources": sources,
        "checks": checks,
        "artifacts": {
            name: digest((OUT / name).read_bytes())
            for name in ("originals.json", "installed-state.json", "current.json")
        },
        "audited_declarations": declarations,
        "audited_member_declarations": member_declarations,
        "audited_state_declarations": state_declarations,
        "source_hash_rule": "Git LF source text; protocol originals retained without normalization",
        "established": [
            "Typed EC/APC/PARAMETER/ROOT/APPLY targets retain original C and native body/context",
            "Exact signer set at each original finalization cut; no later witness replacement",
            "Every original delivery and repeated/distinct vote occurrence is retained",
            "Original event action/bytes/position determine receiver and quorum cut",
            "Full decoded collection targets compose with original-cut quorums",
            "Original member/weight arithmetic rows use b parents while retaining c witnesses",
            "One complete installed-policy byte join preserves full snapshot and candidate list",
            "Fresh vote guards enforce current parent/physical sequence "
            "and retain arithmetic refusal",
            "Every pointer row retains original full finalized APPLY, vector preimages and parent",
        ],
        "not_established": [
            "Initial origin, phase/delivery/finality/durability source composition",
            "Complete O state relation, totality or reviewed R2.3 closure",
            "Named recovery theorem, full formal gates or production GO",
        ],
        "evidence_kind": "SYNTHETIC_BYTE_QUORUM_COMPONENT_NOT_AUTHENTIC_HISTORY",
    }
    (OUT / "receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    print(receipt["result"], flush=True)


if __name__ == "__main__":
    main()
