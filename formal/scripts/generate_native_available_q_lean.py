"""Kernel components for original Q bytes and unauthenticated ledger inputs.

Reuses retained original004 bytes and previous native component observations.
No new native execution or whole-policy/manifest combined example is claimed.
"""

from __future__ import annotations

import copy
import re
from collections import Counter
from pathlib import Path

import generate_native_available_q as source
from formal_artifacts import write_canonical_json
from native_available_q import ledger_inputs
from native_source_artifacts import SourceError

ROOT = Path(__file__).resolve().parents[2]
LEAN = ROOT / "formal/proofs/DeltaReduce/NativeAvailableQVectors.lean"
TARGET = ROOT / "formal/proposals/native-available-q-lean-vectors.json"


def ascii_bytes(value):
    return "[" + ",".join(str(x) for x in value.encode("ascii")) + "]"


def texts(values):
    return "[" + ",".join(map(ascii_bytes, values)) + "]"


def permission(o):
    return (
        f"⟨{texts(o['permitted_ticket_ids'])},{texts(o['permitted_attester_ids'])},"
        f"{o['required_threshold']}⟩"
    )


def observation(o):
    c, a = o["commitment"], o["availability"]
    fields = [
        c["ticket_id"],
        c["commitment_id"],
        a["ticket_id"],
        a["commitment_id"],
        a["certificate_id"],
    ]
    return (
        "⟨"
        + ",".join(map(ascii_bytes, fields))
        + f",{texts(o['required_leaf_ids'])},{texts(a['covered_leaf_ids'])},"
        + f"{texts(a['attester_ids'])},{a['threshold']}⟩"
    )


def generate():
    source.source_blobs()  # verify retained complete native source boundary
    _, golden, base = source.fixture()
    cases = source.cases()
    leaves = [r["leaf_id"] for r in golden["manifest"]["value"]["shards"]]
    for name, change in (
        ("both-duplicate", lambda o: o["required_leaf_ids"].append(o["required_leaf_ids"][-1])),
        ("both-reversed", lambda o: o["required_leaf_ids"].reverse()),
        ("extra-leaf", lambda o: o["required_leaf_ids"].append("sha256:" + "f" * 64)),
    ):
        o = copy.deepcopy(base)
        change(o)
        o["availability"]["covered_leaf_ids"] = list(o["required_leaf_ids"])
        cases[name] = o
    lines = [
        "import DeltaReduce.NativePlanQCorpus",
        "import DeltaReduce.NativeManifestVectors",
        "import DeltaReduce.NativePlanCoefficientVectors",
        "",
        "/-! Original Q components; synthetic typed ledger observations, no signatures.",
        "No new combined whole-policy/manifest/proof execution or native run. -/",
        "namespace DeltaReduce.NativeAvailableQVectors",
        "open NativeAvailableQ",
        "open NativeReceiptBytes (Bytes)",
        "",
    ]
    results = []
    for index, (name, o) in enumerate(cases.items()):
        try:
            ledger_inputs(o)
            primitive = True
        except SourceError:
            primitive = False
        coverage = (
            Counter(o["required_leaf_ids"]) == Counter(leaves)
            and o["commitment"]["ticket_id"] == golden["manifest"]["value"]["ticket_id"]
        )
        lines += [
            f"def permission{index} : Permission := {permission(o)}",
            f"def observation{index} : Observation := {observation(o)}",
            f"theorem primitive{index} : {'¬ ' if not primitive else ''}Primitive "
            f"permission{index} observation{index} := by decide",
            f"theorem coverage{index} : {'¬ ' if not coverage else ''}Coverage "
            f"observation{index} NativeManifestVectors.bound := by decide",
            "",
        ]
        results.append({"index": index, "name": name, "primitive": primitive, "coverage": coverage})
    lines += [
        "theorem originalCoveredCount : observation0.covered.length = 5 :=",
        "  exactLeafCount primitive0 coverage0",
        "theorem everyOriginalLeaf (id : Bytes) : id ∈ observation0.covered ↔",
        "    id ∈ NativeManifestVectors.bound.manifest.refs.map (fun r => r.wire.leaf) :=",
        "  noMissingLeaf primitive0 coverage0 id",
    ]
    for i in range(5):
        lines += [
            f"theorem originalQRange{i} (v : Int)",
            f"    (hv : v ∈ NativeScaleVectors.bound{i}.block.frame.values) : |v| ≤ 32767 :=",
            f"  originalRange NativeManifestVectors.wholeManifest NativeScaleVectors.bound{i}",
            "    (List.mem_of_getElem? (show NativeManifestVectors.bound.blocks["
            f"{i}]? = some NativeScaleVectors.bound{i} from rfl)) v hv",
        ]
    lines += [
        "theorem actualFirstCoordinate : coordinate NativeManifestVectors.bound 0 0 "
        "= some 1 := by decide",
        "theorem missingBlock : coordinate NativeManifestVectors.bound 5 0 = none := by decide",
        "theorem missingCoordinate : coordinate NativeManifestVectors.bound 0 4 "
        "= none := by decide",
        "theorem originalForbiddenValue : NativeQBytes.decodePayload [0,128] = none := by decide",
        "theorem originalSignedEndpoints : NativeQBytes.decodePayload [1,128,255,127] =",
        "    some [-32767,32767] := by decide",
        "theorem originalPayloadProduct (v : Int)",
        "    (hv : v ∈ NativeScaleVectors.bound0.block.frame.values) :",
        "    |(4 : Int)*v| ≤ (NativeAccumulatorBinding.limit 64 : Int) := by",
        "  exact NativePlanCoefficients.productFits NativePlanCoefficientVectors.fits",
        "    (t := ⟨NativePlanCoefficientVectors.rows[1],4⟩) (by decide) v (originalQRange0 v hv)",
        "theorem missingInput {sha configRaw proofRaw profileRaw p permission t} :",
        "    NativePlanQCorpus.loadRows sha configRaw proofRaw profileRaw p permission "
        "[t] [] = none := rfl",
        "theorem extraInput {sha configRaw proofRaw profileRaw p permission i} :",
        "    NativePlanQCorpus.loadRows sha configRaw proofRaw profileRaw p permission "
        "[] [i] = none := rfl",
        "end DeltaReduce.NativeAvailableQVectors",
        "",
    ]
    text = "\n".join(lines)
    LEAN.write_text(text, encoding="utf-8", newline="\n")
    result = {
        "status": "ORIGINAL_Q_BYTES_WITH_UNAUTHENTICATED_TYPED_LEDGER_COMPONENTS",
        "source_commit": source.SOURCE,
        "boundary_sha256": source.BOUNDARY_PIN,
        "original_manifest": golden["manifest"]["content_id"],
        "original_q_blocks": 5,
        "original_coordinates": 36,
        "primitive_cases": results,
        "kernel_theorems": re.findall(r"^theorem (\w+)", text, re.M),
        "native_execution": False,
        "new_whole_policy_corpus_kernel_example": False,
        "native_export_authenticated": False,
        "availability_signatures_verified": False,
        "commitment_manifest_identity_authenticated": False,
        "formal_go": False,
        "gate_eligible": False,
    }
    write_canonical_json(TARGET, result)
    return result


if __name__ == "__main__":
    result = generate()
    print(len(result["primitive_cases"]), len(result["kernel_theorems"]))
