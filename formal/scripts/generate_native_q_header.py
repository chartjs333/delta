"""Generate source-pinned compositional DRQ1 header proofs, not source authority."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from formal_artifacts import write_canonical_json
from generate_native_source_artifacts import BOUNDARY_PIN, fixture_store
from native_source_artifacts import canonical, read_drq1, require

ROOT = Path(__file__).resolve().parents[2]
LEAN = ROOT / "formal/proofs/DeltaReduce/NativeQHeaderVectors.lean"
TARGET = ROOT / "formal/proposals/native-q-header-vectors.json"
DECL = ROOT / "formal/proposals/evidence/native-q-header/native-shard-header.hpp"
DECL_SHA = "1d0466d5729c6a47dcea5a52fdf5b7e2de77f9e3a838e97096f1fb97f8640ec3"
FIELDS = [
    ("countRaw", "element_count"),
    ("startRaw", "element_start"),
    ("semantics", "formal_semantics_id"),
    ("ordinalRaw", "ordinal"),
    ("schema", "parameter_schema_id"),
    ("payloadHash", "payload_sha256"),
    ("profile", "profile_id"),
    ("proof", "proof_instance_id"),
    ("config", "round_config_id"),
    ("scale", "scale_table_id"),
    ("segment", "segment_id"),
    ("offsetRaw", "segment_offset"),
    ("plan", "shard_plan_id"),
    ("ticket", "ticket_id"),
]


def generate() -> dict:
    require(hashlib.sha256(DECL.read_bytes()).hexdigest() == DECL_SHA, "NATIVE_HEADER_DECLARATION")
    _, golden, _ = fixture_store()
    lines = [
        "import DeltaReduce.NativeQHeader",
        "import DeltaReduce.NativeQBytesVectors",
        "",
        "/-! Original header bytes; no payload SHA, source graph or exporter authentication. -/",
        "namespace DeltaReduce.NativeQHeaderVectors",
        "open NativeVoteBytes (ascii ContentId)",
        "open NativeQHeader",
        "set_option maxRecDepth 4000",
        "set_option maxHeartbeats 1000000",
        "",
    ]
    pool = {}
    for row in golden["shards"]:
        for _name, key in FIELDS:
            value = str(row["header"][key])
            if value not in pool:
                pool[value] = len(pool)
    for value in ["1.0.0", "ENCODED_INT16_SHARD"]:
        pool.setdefault(value, len(pool))
    for value, n in pool.items():
        literal = "[" + ",".join(str(b) for b in value.encode("ascii")) + "]"
        kind = "natural" if value.isdigit() else "text"
        lines += [
            f"def bytes{n} : NativeReceiptBytes.Bytes := {literal}",
            f"theorem value{n} : NativeQJson.ValueValid .{kind} bytes{n} := by decide",
        ]
        if value.startswith("sha256:"):
            lines.append(f"theorem id{n} : ContentId bytes{n} := by decide")
        if not value.startswith("sha256:") and not value.isdigit():
            lines.append(f"theorem token{n} : Token bytes{n} := by decide")
    rows = []
    for i, row in enumerate(golden["shards"]):
        raw = bytes.fromhex(row["envelope_hex"])
        h, values = read_drq1(raw)
        require(h == row["header"], "ORIGINAL_HEADER_VALUE")
        require(canonical(h).hex() == row["header_bytes_hex"], "ORIGINAL_HEADER_PREIMAGE")
        require(len(h) == 16, "ORIGINAL_HEADER_FIELDS")
        require(len(values) == h["element_count"], "ORIGINAL_COUNT")
        values_literal = "[" + ",".join(map(str, values)) + "]"
        lines += [
            f"def wire{i} : Wire := {{",
            ",\n".join(f"  {name} := bytes{pool[str(h[key])]}" for name, key in FIELDS),
            "}",
            f"def header{i} : Header := ⟨wire{i},{h['element_count']},{h['element_start']},"
            f"{h['ordinal']},{h['segment_offset']}⟩",
            f"theorem sourceBytes{i} : encode wire{i} = NativeQBytesVectors.header{i} := by rfl",
            f"theorem fieldValues{i} : ∀ f ∈ fields wire{i}, "
            "NativeQJson.ValueValid f.kind f.value := by",
            "  simp only [fields, List.forall_mem_cons]",
            "  exact ⟨"
            + ", ".join(f"value{pool[str(h[key])]}" for key in sorted(h))
            + ", by simp⟩",
            f"theorem ids{i} : ∀ b ∈ [wire{i}.semantics,wire{i}.schema,wire{i}.payloadHash,",
            f"    wire{i}.profile,wire{i}.proof,wire{i}.config,"
            f"wire{i}.scale,wire{i}.plan], ContentId b := by",
            "  simp only [List.forall_mem_cons]",
            "  exact ⟨"
            + ", ".join(
                f"id{pool[h[key]]}"
                for key in [
                    "formal_semantics_id",
                    "parameter_schema_id",
                    "payload_sha256",
                    "profile_id",
                    "proof_instance_id",
                    "round_config_id",
                    "scale_table_id",
                    "shard_plan_id",
                ]
            )
            + ", by simp⟩",
            f"theorem wireValid{i} : WireValid wire{i} := by",
            f"  refine ⟨fieldValues{i}, ?_, ids{i}, rfl, rfl, "
            f"token{pool[h['segment_id']]}, token{pool[h['ticket_id']]}⟩",
            f"  rw [sourceBytes{i}, NativeQBytesVectors.headerLength{i}]",
            "  decide",
            f"theorem valid{i} : Valid header{i} := by",
            f"  exact ⟨wireValid{i}, by decide, by decide, by decide, by decide,",
            "    by decide, by decide, by decide, by decide⟩",
            f"theorem decoded{i} : decode NativeQBytesVectors.header{i} = some header{i} := by",
            f"  rw [← sourceBytes{i}]",
            f"  exact decodeEncoded header{i} valid{i}",
            f"theorem joined{i} : join NativeQBytesVectors.frame{i} =",
            f"    some ⟨⟨NativeQBytesVectors.header{i},NativeQBytesVectors.payload{i},"
            f"{values_literal}⟩,header{i}⟩ := by",
            f"  exact joinFromComputed NativeQBytesVectors.originalDecoded{i} decoded{i} rfl",
            "",
        ]
        rows.append(
            {
                "ordinal": i,
                "source_leaf_id": row["leaf_id"],
                "header_sha256": hashlib.sha256(canonical(h)).hexdigest(),
                "header": h,
                "values": list(values),
                "source_frame_sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    cases = {
        "leadingZero": 'NativeQJson.readValue .natural 44 (ascii "00,") = none',
        "negativeZero": 'NativeQJson.readValue .natural 44 (ascii "-0,") = none',
        "negativeOne": 'NativeQJson.readValue .natural 44 (ascii "-1,") = none',
        "plusSign": 'NativeQJson.readValue .natural 44 (ascii "+1,") = none',
        "fractionalNumber": 'NativeQJson.readValue .natural 44 (ascii "1.0,") = none',
        "exponentNumber": 'NativeQJson.readValue .natural 44 (ascii "1e0,") = none',
        "booleanNumber": 'NativeQJson.readValue .natural 44 (ascii "true,") = none',
        "overflowNumber": "NativeQJson.readValue .natural 44 "
        '(ascii "18446744073709551616,") = none',
        "maximumUint64": 'NativeQJson.readValue .natural 44 (ascii "18446744073709551615,") = '
        'some (ascii "18446744073709551615",[])',
        "escapedText": "NativeQJson.readValue .text 44 [34,92,117,48,48,54,49,34,44] = none",
        "controlText": "NativeQJson.readValue .text 44 [34,10,34,44] = none",
        "nonAsciiText": "NativeQJson.readValue .text 44 [34,255,34,44] = none",
        "missingQuote": "NativeQJson.readValue .text 44 [34,97,44] = none",
        "nonJsonHeaderRejected": "decode [255] = none",
        "badNumericWire": 'interpret {wire0 with countRaw := ascii "01"} = none',
        "overflowOffsetWire": "interpret {wire0 with offsetRaw := "
        'ascii "18446744073709551616"} = none',
        "wrongVersion": "fromValues (((fields wire0).map NativeQJson.Field.value).set 10 "
        '(ascii "2.0.0")) = none',
        "wrongType": "fromValues (((fields wire0).map NativeQJson.Field.value).set 15 "
        '(ascii "Q_SHARD")) = none',
        "invalidTokenEscape": 'Token (ascii "a\\\\b") = False',
        "invalidTokenSpace": 'Token (ascii "a b") = False',
        "upperHexNotContentId": 'ContentId (ascii "sha256:' + "A" * 64 + '") = False',
    }
    for name, raw in {
        "duplicateKey": '{"element_count":1,"element_count":2}',
        "extraFirstKey": '{"extra":1,"element_count":1}',
        "wrongFirstOrder": '{"element_start":0,"element_count":1}',
        "outerWhitespace": ' {"element_count":1}',
        "quotedNumber": '{"element_count":"1"}',
        "missingFields": '{"element_count":1}',
    }.items():
        cases[name] = f"readWire (ascii {json.dumps(raw)}) = none"
    for name in ["invalidTokenEscape", "invalidTokenSpace", "upperHexNotContentId"]:
        cases[name] = "¬ " + cases[name].removesuffix(" = False")
    for name, proposition in cases.items():
        lines.append(f"theorem {name} : {proposition} := by decide")
    lines += [
        "",
        "/-- Metadata/count interpretation still does not authenticate payload SHA. -/",
        "theorem changedPayloadWithOldShaStillAccepted :",
        "    join (NativeQBytes.encodeFrame NativeQBytesVectors.header0 [2,0,254,255,0,0,4,0]) =",
        "      some ⟨⟨NativeQBytesVectors.header0,[2,0,254,255,0,0,4,0],[2,-2,0,4]⟩,header0⟩ := by",
        "  exact joinFromComputed NativeQBytesVectors.changedPayloadWithOldHeaderAccepted "
        "decoded0 rfl",
        "",
        "end DeltaReduce.NativeQHeaderVectors",
        "",
    ]
    LEAN.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    result = {
        "version": "deltareduce.original-drq1-header-lean.v1-candidate",
        "scope": "ORIGINAL_CANONICAL_HEADER_AND_VECTOR_COUNT_NOT_SOURCE_ADMISSION",
        "source_boundary_sha256": BOUNDARY_PIN,
        "native_header_declaration_sha256": DECL_SHA,
        "native_reference_commit": "60c692f6e391f839829dfc64e93380db54cd507b",
        "formal_go": False,
        "native_execution": False,
        "native_export_authenticated": False,
        "payload_sha_proved": False,
        "source_graph_admission_proved": False,
        "full_native_recovery_proved": False,
        "rows": rows,
        "small_kernel_cases": [*cases, "changedPayloadWithOldShaStillAccepted"],
        "lean_sha256": hashlib.sha256(LEAN.read_bytes()).hexdigest(),
    }
    write_canonical_json(TARGET, result)
    return result


if __name__ == "__main__":
    result = generate()
    print(
        json.dumps(
            {"headers": len(result["rows"]), "small_cases": len(result["small_kernel_cases"])}
        )
    )
