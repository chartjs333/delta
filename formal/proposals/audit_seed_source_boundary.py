"""T047/T053: read-only immutable contract inventory, not a seed implementation."""

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "formal/proposals/evidence/profile-seed-source-boundary"
N = "60c692f6e391f839829dfc64e93380db54cd507b"
P = "26eb02d0632435c9aa0d8ef44eb496b6fa73dd13"
A = "bb9fce957dae329701a8cd473a7148e198e1ca12"
EC = "f1a9963eabb5cb61f936ad1ad41f45e870acd43e"
W = "47d75279d23441f5c10ed523bdea172b257e8bef"
D = "6ef27068b88c712245febb5584ebbf7763c3a66e"
PATTERN = re.compile(r"seed|beacon|reveal|randomness", re.I)
SUFFIXES = {".cpp", ".hpp", ".h", ".java", ".py", ".md", ".json", ".tla", ".lean"}
ROOTS = [
    "delta-core-cpp/src",
    "delta-core-cpp/include",
    "delta-runtime-cpp/src",
    "delta-runtime-cpp/include",
    "delta-ffi/src",
    "delta-ffi/include",
    "delta-node-java/src/main",
    "specs/008-certificates-and-consensus",
    "specs/003-bft-round-state-machine",
    "docs/adr",
    "orchestration/sprints/isc-s16-continuous/handoffs",
    "orchestration/sprints/isc-s16-continuous/scope-requests",
]


def git(*args):
    return subprocess.check_output(["cmd.exe", "/d", "/c", "git", *args], cwd=ROOT)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    refs = [N, P, A, EC, W, D]
    trees, contents, hits = {}, {}, []
    for commit in refs:
        trees[commit] = git("rev-parse", commit + ":").decode().strip()
        rows = git("ls-tree", "-r", commit, "--", *ROOTS).decode().splitlines()
        for row in rows:
            _mode, kind, rest = row.split(" ", 2)
            oid, path = rest.split("\t", 1)
            if kind != "blob" or Path(path).suffix not in SUFFIXES:
                continue
            if oid not in contents:
                raw = git("cat-file", "blob", oid)
                text = raw.decode("utf8", errors="replace")
                lines = [
                    {"line": i, "text": line[:800], "truncated": len(line) > 800}
                    for i, line in enumerate(text.splitlines(), 1)
                    if PATTERN.search(line)
                ]
                contents[oid] = {"bytes": len(raw), "sha256": digest(raw), "hits": lines}
            hits.append({"commit": commit, "path": path, "blob": oid})
    exact = [
        (N, "delta-core-cpp/include/delta/certificates/contracts.hpp"),
        (N, "delta-core-cpp/src/certificates/contracts.cpp"),
        (N, "delta-core-cpp/src/certificates/verifier.cpp"),
        (N, "delta-core-cpp/src/robust/plan.cpp"),
        (N, "delta-core-cpp/tests/certificates_test.cpp"),
        (N, "specs/008-certificates-and-consensus/spec.md"),
        (N, "specs/008-certificates-and-consensus/plan.md"),
        (N, "specs/008-certificates-and-consensus/runtime-profile.md"),
        (N, "specs/008-certificates-and-consensus/task-map.md"),
        (N, "specs/008-certificates-and-consensus/evidence/native-execution.json"),
        (N, "specs/008-certificates-and-consensus/evidence/certificate-refinement.json"),
        (P, "docs/adr/0013-snapshot-provenance-profile-v1.md"),
        (A, "docs/adr/0015-non-isc-authority-binding-v1.md"),
        (
            EC,
            "orchestration/sprints/isc-s16-continuous/handoffs/ISC-S16-FIRST-EC-PRODUCER-SOURCE-v1.md",
        ),
        (W, "formal/proofs/DeltaReduce/NativeSeedTranscript.lean"),
        (W, "formal/proofs/DeltaReduce/NativeSeedTranscriptVectors.lean"),
        (W, "formal/proposals/native-seed-transcript-proof.md"),
        (W, "formal/proposals/b-family-transfer/ProfileLineage.lean"),
        (W, "formal/reference/profile_source/lineage_vectors.py"),
        (W, "formal/tla/DeltaReduceCertificates.tla"),
    ]
    sources = []
    for i, (commit, path) in enumerate(exact):
        raw = git("show", commit + ":" + path)
        name = f"source-{i:02d}" + Path(path).suffix
        (OUT / name).write_bytes(raw)
        sources.append({"commit": commit, "path": path, "sha256": digest(raw), "copy": name})
    corpus = {
        "pattern": PATTERN.pattern,
        "roots": ROOTS,
        "trees": trees,
        "files": hits,
        "blobs": contents,
    }
    (OUT / "corpus.json").write_text(json.dumps(corpus, indent=2) + "\n", encoding="utf8")
    result = {
        "task_ids": ["T047", "T053", "ISC-S16-D01"],
        "result": "NO_CONCRETE_SEED_EVIDENCE_VERIFIER_IN_SELECTED_CORPUS",
        "finding_method": "Manual applicability review of the immutable source inventory; "
        "keyword matches alone are not an absence proof",
        "sources": sources,
        "corpus_sha256": digest((OUT / "corpus.json").read_bytes()),
        "limits": [
            "Contract coverage/source inspection, not execution of a forged production history",
            "Not a proof that an unsupplied external selected seed contract cannot exist",
            "Seed shape/parent checks and ordering evidence remain valid within their scope",
            "No new seed algorithm, signing domain, trust root, predicate or implementation",
        ],
    }
    (OUT / "audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
    print(
        json.dumps(
            {
                "result": result["result"],
                "roots_checked": len(refs),
                "file_versions": len(hits),
                "distinct_blobs": len(contents),
            }
        )
    )


if __name__ == "__main__":
    main()
