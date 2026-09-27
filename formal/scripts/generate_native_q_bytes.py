"""Pin original DRQ1 bytes and generate compositional Lean decoder examples."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

from formal_artifacts import write_canonical_json
from generate_native_source_artifacts import BOUNDARY_PIN, fixture_store
from native_source_artifacts import canonical, read_drq1, require

ROOT = Path(__file__).resolve().parents[2]
LEAN = ROOT / "formal/proofs/DeltaReduce/NativeQBytesVectors.lean"
TARGET = ROOT / "formal/proposals/native-q-bytes-vectors.json"


def literal(values) -> str:
    return "[" + ", ".join(map(str, values)) + "]"


def generate() -> dict:
    _, golden, _ = fixture_store()
    lines = [
        "import DeltaReduce.NativeQBytes",
        "",
        "/-! Original pinned feature-004 bytes; framing/payload only, not authentication. -/",
        "namespace DeltaReduce.NativeQBytesVectors",
        "open NativeReceiptBytes (Bytes)",
        "open NativeQBytes",
        "set_option maxRecDepth 4000",
        "",
    ]
    rows = []
    for i, source in enumerate(golden["shards"]):
        raw = bytes.fromhex(source["envelope_hex"])
        header = bytes.fromhex(source["header_bytes_hex"])
        payload = bytes.fromhex(source["payload_hex"])
        prefix = struct.pack("<4sHHII", b"DRQ1", 1, 0, len(header), len(payload))
        require(raw == prefix + header + payload, "SOURCE_FRAME_SPLIT")
        require(header == canonical(source["header"]), "SOURCE_HEADER_PREIMAGE")
        parsed_header, values = read_drq1(raw)
        require(parsed_header == source["header"], "SOURCE_HEADER")
        require(len(values) == source["element_count"], "SOURCE_COUNT")
        rows.append(
            {
                "ordinal": i,
                "source_leaf_id": source["leaf_id"],
                "source_frame_sha256": hashlib.sha256(raw).hexdigest(),
                "source_frame_hex": raw.hex(),
                "header_hex": header.hex(),
                "payload_hex": payload.hex(),
                "values": list(values),
            }
        )
        lines += [
            f"def header{i} : Bytes := {literal(header)}",
            f"def payload{i} : Bytes := {literal(payload)}",
            f"def frame{i} : Bytes := {literal(prefix)} ++ header{i} ++ payload{i}",
            f"theorem headerLength{i} : header{i}.length = {len(header)} := by rfl",
            f"theorem payloadLength{i} : payload{i}.length = {len(payload)} := by rfl",
            f"theorem values{i} : decodePayload payload{i} = some {literal(values)} := by decide",
            f"theorem originalEncoding{i} : encodeFrame header{i} payload{i} = frame{i} := by",
            f"  unfold encodeFrame frame{i}",
            f"  rw [headerLength{i}, payloadLength{i}]",
            "  rfl",
            f"theorem originalDecoded{i} : decode frame{i} =",
            f"    some ⟨header{i}, payload{i}, {literal(values)}⟩ := by",
            f"  rw [← originalEncoding{i}]",
            f"  exact frameEncoded _ _ _ (by rw [headerLength{i}]; decide)",
            f"    (by rw [headerLength{i}]; decide) (by rw [payloadLength{i}]; decide)",
            f"    (by rw [payloadLength{i}]; decide) values{i}",
            "",
        ]
    require([v for row in rows for v in row["values"]] == golden["q_values"], "ALL_VALUES")
    cases = {
        "signedEndpoints": "decodePayload [1,128,255,127,255,255,0,0,1,0] = "
        "some [-32767,32767,-1,0,1]",
        "littleEndianOrder": "decodePayload [0,1,1,0] = some [256,1]",
        "zeroDuplicateRetention": "decodePayload [0,0,0,0,255,255,255,255] = some [0,0,-1,-1]",
        "emptyLowLevel": "decodePayload [] = some []",
        "forbiddenMinus32768": "decodePayload [0,128] = none",
        "forbiddenLater": "decodePayload [1,0,0,128,2,0] = none",
        "oddPayload": "decodePayload [1,0,2] = none",
        "emptyFrame": "decode [] = none",
        "emptyHeader": "decode (encodeFrame [] [1,0]) = none",
        "emptyPayload": "decode (encodeFrame [123,125] []) = none",
        "oddFrame": "decode (encodeFrame [123,125] [1]) = none",
        "trailingByte": "decode (encodeFrame [123,125] [1,0] ++ [0]) = none",
        "truncatedPayload": "decode ((encodeFrame [123,125] [1,0]).take 19) = none",
        "truncatedLength": "decode (magic ++ [1,0,0]) = none",
        "wrongVersion": "decode ([68,82,81,49,2,0,0,0,1,0,0,0,2,0,0,0,123,1,0]) = none",
        "wrongMagic": "decode ([68,82,81,50,1,0,0,0,1,0,0,0,2,0,0,0,123,1,0]) = none",
        "headerOverBound": "decode (magic ++ le 4 65537 ++ le 4 2 ++ [123,1,0]) = none",
        "payloadOverBound": "decode (magic ++ le 4 1 ++ le 4 1048578 ++ [123,1,0]) = none",
        "opaqueHeaderNotJson": "decode (encodeFrame [255] [1,0]) = some ⟨[255],[1,0],[1]⟩",
    }
    for name, proposition in cases.items():
        lines.append(f"theorem {name} : {proposition} := by decide")
    lines += [
        "",
        "/-- The original header's payload SHA is NOT checked by this layer. -/",
        "theorem changedPayloadWithOldHeaderAccepted :",
        "    decode (encodeFrame header0 [2,0,254,255,0,0,4,0]) =",
        "      some ⟨header0,[2,0,254,255,0,0,4,0],[2,-2,0,4]⟩ := by",
        "  exact frameEncoded _ _ _ (by rw [headerLength0]; decide)",
        "    (by rw [headerLength0]; decide) (by decide) (by decide) (by decide)",
        "",
        "end DeltaReduce.NativeQBytesVectors",
        "",
    ]
    LEAN.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    result = {
        "version": "deltareduce.original-drq1-lean.v1-candidate",
        "scope": "ORIGINAL_BYTE_FRAMING_AND_INT16_ONLY",
        "source_boundary_sha256": BOUNDARY_PIN,
        "native_reference_commit": "60c692f6e391f839829dfc64e93380db54cd507b",
        "formal_go": False,
        "native_execution": False,
        "native_export_authenticated": False,
        "header_json_sha_admission_proved": False,
        "full_native_recovery_proved": False,
        "rows": rows,
        "coordinate_count": sum(len(row["values"]) for row in rows),
        "small_kernel_cases": [*cases, "changedPayloadWithOldHeaderAccepted"],
        "lean_sha256": hashlib.sha256(LEAN.read_bytes()).hexdigest(),
    }
    write_canonical_json(TARGET, result)
    return result


if __name__ == "__main__":
    result = generate()
    print(json.dumps({"shards": len(result["rows"]), "coordinates": result["coordinate_count"]}))
