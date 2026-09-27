"""Original config/proof kernel components; synthetic hashes are not authority."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from formal_artifacts import write_canonical_json
from generate_native_accumulator_source import BOUNDARY_PIN, originals
from generate_native_source_artifacts import fixture_store
from native_accumulator_source import resolve_bound_q_source, theorem_metadata
from native_source_artifacts import PROFILE, canonical, require

ROOT = Path(__file__).resolve().parents[2]
LEAN = ROOT / "formal/proofs/DeltaReduce/NativeAccumulatorVectors.lean"
TARGET = ROOT / "formal/proposals/native-accumulator-lean-vectors.json"
CONFIG = (
    "width:accumulator_width_bits base:base_round_config_id coefficient:coefficient_abs_max "
    "semantics:formal_semantics_id count:max_eligible_contributions schema:parameter_schema_id "
    "profile:profile_id q:q_abs_max scale:scale_table_id version:schema_version "
    "plan:shard_plan_id kind:type_name"
).split()
PROOF = (
    "coefficient:coefficient_abs_max denominator:common_denominator config:config_id "
    "finalBound:final_abs_bound semantics:formal_semantics_id lean:lean_artifact_sha256 "
    "count:max_eligible_contributions prefixBound:max_incremental_prefix_abs "
    "product:product_abs_bound productWidth:product_width_bits profile:profile_id q:q_abs_max "
    "result:result scale:scale_table_id version:schema_version "
    "width:selected_accumulator_width_bits kind:type_name"
).split()


def generate() -> dict:
    originals()
    store, golden, _ = fixture_store()
    checked = resolve_bound_q_source(store, golden["manifest"]["content_id"])
    accumulator = checked.accumulator
    config = json.loads(store[accumulator.config_id])
    proof = json.loads(store[accumulator.proof_id])
    theorem_bytes = b'"theorems":' + canonical(theorem_metadata()) + b","
    lines = [
        "import DeltaReduce.NativeAccumulatorBinding",
        "namespace DeltaReduce.NativeAccumulatorVectors",
        "open NativeReceiptBytes (Bytes)",
        "open NativeVoteBytes (ascii)",
        "open NativeAccumulatorBinding",
        "set_option maxRecDepth 10000",
        "set_option maxHeartbeats 3000000",
    ]
    documents = []
    for name, doc, fields, identity in [
        ("Config", config, CONFIG, accumulator.config_id),
        ("Proof", proof, PROOF, accumulator.proof_id),
    ]:
        prefix = name.lower()
        values, valid, chunks, chunks_data, encoded, lengths = [], [], ["[123]"], [b"{"], [], []
        for i, field in enumerate(fields):
            alias, key = field.split(":")
            value = doc[key]
            natural = type(value) is int
            kind = "natural" if natural else "text"
            symbol = f"{prefix}Value{i}"
            lines += [
                f"def {symbol} : Bytes := {list(str(value).encode())}",
                f"theorem {symbol}Valid : NativeQJson.ValueValid .{kind} {symbol} := by decide",
            ]
            values.append(symbol)
            valid.append(symbol + "Valid")
            if name == "Proof" and alias == "kind":
                chunks.append("NativeAccumulatorBytes.theoremBytes")
                chunks_data.append(theorem_bytes)
                lines.append(
                    "theorem theoremLength : NativeAccumulatorBytes.theoremBytes.length = "
                    f"{len(theorem_bytes)} := rfl"
                )
                lengths.append("theoremLength")
            sep = b"}" if i == len(fields) - 1 else b","
            raw = canonical(key) + b":" + canonical(value) + sep
            chunk = f"{prefix}Field{i}"
            chunks.append(chunk)
            chunks_data.append(raw)
            lines += [
                f"def {chunk} : Bytes := {list(raw)}",
                f"theorem {chunk}Length : {chunk}.length = {len(raw)} := rfl",
                f'theorem {chunk}Encoded : NativeScaleBytes.memberBytes "{key}" '
                f".{kind} {symbol} {sep[0]} = {chunk} := rfl",
            ]
            lengths.append(chunk + "Length")
            encoded.append(chunk + "Encoded")
        raw = store[identity]
        require(b"".join(chunks_data) == raw, "ORIGINAL_COMPONENT_PREIMAGE")
        lines += [
            f"def {prefix} : NativeAccumulatorBytes.{name} := ⟨" + ",".join(values) + "⟩",
            f"theorem {prefix}Syntax : NativeAccumulatorBytes.{name}Syntax {prefix} := ⟨"
            + ",".join(valid)
            + "⟩",
            f"def {prefix}Original : Bytes := " + " ++ ".join(chunks),
            f"theorem {prefix}Length : {prefix}Original.length = {len(raw)} := by",
            f"  simp only [{prefix}Original,List.length_append,List.length_cons,List.length_nil,"
            + ",".join(lengths)
            + "]",
            f"theorem {prefix}Encoded : NativeAccumulatorBytes.encode{name} {prefix} = "
            f"{prefix}Original := by",
            f"  simp only [NativeAccumulatorBytes.encode{name},{prefix},"
            + ",".join(encoded)
            + f",{prefix}Original]",
            f"theorem {prefix}Decoded : NativeAccumulatorBytes.decode{name} {prefix}Original = "
            f"some {prefix} := by",
            f"  rw [← {prefix}Encoded]",
            f"  apply NativeAccumulatorBytes.decode{name}Encoded _ {prefix}Syntax",
            f"  rw [{prefix}Encoded,{prefix}Length]; decide",
        ]
        documents.append({"kind": name, "id": identity, "bytes_hex": raw.hex(), "value": doc})

    profile_raw = store[PROFILE]
    # Full immutable profile constant must be byte-exact, not merely share an ID.
    binding = (ROOT / "formal/proofs/DeltaReduce/NativeAccumulatorBinding.lean").read_text()
    profile_literal = binding.split("def workerProfileBytes : Bytes := ", 1)[1].splitlines()[0]
    require(bytes(json.loads(profile_literal)) == profile_raw, "IMMUTABLE_PROFILE_PREIMAGE")
    lines.append(f"theorem profileLength : workerProfileBytes.length = {len(profile_raw)} := rfl")
    n = accumulator
    lines += [
        "def numbers : Numbers := ⟨"
        + ",".join(
            map(
                str,
                [
                    n.coefficient_max,
                    n.contribution_max,
                    n.denominator,
                    n.product,
                    n.prefix,
                    n.final,
                    n.product_bits,
                    n.accumulator_bits,
                ],
            )
        )
        + "⟩",
        "theorem numericValid : NumericValid numbers := by decide",
        "theorem numericDecoded : readNumbers proof = some numbers := by",
        "  apply numbersFromSource",
        "  exact ⟨by decide,by decide,by decide,by decide,by decide,"
        "by decide,by decide,by decide,numericValid⟩",
        "theorem metadata : Metadata config proof := by decide",
        "def bound : Bound := ⟨config,proof,numbers⟩",
    ]
    hashes = []
    for i, (expr, raw, domain, identity) in enumerate(
        [
            ("configOriginal", store[n.config_id], "fixedpoint-config", n.config_id),
            ("proofOriginal", store[n.proof_id], "proof-instance", n.proof_id),
            ("workerProfileBytes", profile_raw, "profile", PROFILE),
        ]
    ):
        preimage = f"deltareduce.004.{domain}.v1".encode() + b"\0" + raw
        require("sha256:" + hashlib.sha256(preimage).hexdigest() == identity, "ORIGINAL_SHA")
        function = ["configInput", "proofInput", "profileInput"][i]
        lines += [
            f"def input{i} : Bytes := {function} {expr}",
            f"def id{i} : Bytes := {list(identity.encode())}",
            f"theorem inputLength{i} : input{i}.length = {len(preimage)} := by",
            f"  simp only [input{i},{function},List.length_append,List.length_cons,List.length_nil,"
            + ["configLength", "proofLength", "profileLength"][i]
            + "]",
            "  rfl",
        ]
        hashes.append({"bytes_hex": preimage.hex(), "id": identity})
    lines += ["@[irreducible]", "def fixtureHash (raw : Bytes) : Bytes :="]
    for i, row in enumerate(hashes):
        lines.append(
            f"  if raw.length = {len(bytes.fromhex(row['bytes_hex']))} then "
            f"(if raw = input{i} then id{i} else []) else"
        )
    lines.append("  []")
    for i in range(3):
        lines += [
            f"theorem hash{i} : fixtureHash input{i} = id{i} := by",
            f"  simp only [fixtureHash,inputLength{i}]",
            "  simp",
        ]
    lines += [
        "theorem loaded : load fixtureHash configOriginal proofOriginal workerProfileBytes "
        "id1 = some bound := by",
        "  apply loadFromSource",
        "  refine ⟨configDecoded,proofDecoded,numericDecoded,metadata,rfl,?_,?_,by decide,hash1⟩",
        "  · exact hash2",
        "  · exact hash0",
        "theorem exactInferredHeadroom : headroom numbers = 0 := by decide",
        "theorem actualComputedBounds : numbers.product = 2147483646 ∧ "
        "numbers.prefixBound = 9223372026117357570 := ⟨rfl,rfl⟩",
    ]
    # Small kernel evaluations exercise arithmetic and parsing separately from the
    # original large proof body. No synthetic metadata example is native execution.
    cases = {
        "signed128Endpoint": (
            'number i128 (ascii "170141183460469231731687303715884105727") = some i128'
        ),
        "signed128Overflow": 'number i128 (ascii "170141183460469231731687303715884105728") = none',
        "unsigned64Endpoint": 'number u64 (ascii "18446744073709551615") = some u64',
        "unsigned64Overflow": 'number u64 (ascii "18446744073709551616") = none',
        "leadingZero": 'number i128 (ascii "01") = none',
        "negativeZero": 'number i128 (ascii "-0") = none',
        "negativeAlternate": 'number i128 (ascii "-01") = none',
        "plusSign": 'number i128 (ascii "+1") = none',
        "emptyNumber": "number i128 [] = none",
        "badWidth": "¬ NumericValid { numbers with accumulatorBits := 65 }",
        "wrongProduct": "¬ NumericValid { numbers with product := numbers.product+1 }",
        "wrongPrefix": "¬ NumericValid { numbers with prefixBound := numbers.prefixBound+1 }",
        "zeroCoefficient": "¬ NumericValid { numbers with coefficient := 0 }",
        "zeroCount": "¬ NumericValid { numbers with count := 0 }",
        "zeroDenominator": "¬ NumericValid { numbers with denominator := 0 }",
        "exactDenominatorNotLCM": "NumericValid { numbers with denominator := 7 }",
        "finalBelowPrefix": "¬ NumericValid { numbers with finalBound := numbers.prefixBound-1 }",
        "nonzeroHeadroom": "NumericValid { numbers with finalBound := numbers.finalBound+1 }",
        "inclusive64Final": "NumericValid { numbers with finalBound := i64 }",
        "separateAccumulatorWidth": (
            "¬ NumericValid { numbers with finalBound := i64+1, productBits := 128 }"
        ),
        "wideProductNarrowAccumulator": (
            "¬ NumericValid ⟨i64,1,1,32767*i64,32767*i64,32767*i64,128,64⟩"
        ),
        "narrowProductWideAccumulator": (
            "¬ NumericValid ⟨i64,1,1,32767*i64,32767*i64,32767*i64,64,128⟩"
        ),
        "wideBoth": "NumericValid ⟨i64,1,1,32767*i64,32767*i64,32767*i64,128,128⟩",
        "missingAuthorityReference": "¬ Metadata { config with base := [] } proof",
        "wrongConfigCount": '¬ Metadata { config with count := ascii "1" } proof',
        "wrongHistoricalLean": "¬ Metadata config { proof with lean := [] }",
        "passStringInsufficient": 'readNumbers { proof with product := ascii "0" } = none',
        "unknownMetadata": 'NativeAccumulatorBytes.decodeConfig (ascii "{}") = none',
        "missingTheorems": (
            "NativeReceiptBytes.consume NativeAccumulatorBytes.theoremBytes "
            '(ascii "\\"theorems\\":[],") = none'
        ),
    }
    for name, claim in cases.items():
        lines.append(f"theorem {name} : {claim} := by decide")
    lines.append("end DeltaReduce.NativeAccumulatorVectors")
    text = "\n".join(lines) + "\n"
    LEAN.write_text(text, encoding="utf-8", newline="\n")
    result = {
        "scope": "ORIGINAL_CONFIG_PROOF_UNDER_UNVERIFIED_HASH_NOT_NATIVE_AUTHENTICATION",
        "formal_go": False,
        "native_execution": False,
        "native_export_authenticated": False,
        "hash_adapter_authenticated": False,
        "native_recovery_proved": False,
        "boundary_sha256": BOUNDARY_PIN,
        "original_documents": documents,
        "original_profile_id": PROFILE,
        "original_profile_bytes_hex": profile_raw.hex(),
        "synthetic_hash_preimages": hashes,
        "small_kernel_cases": list(cases),
        "headroom_scope": "UNIQUE_ADMISSIBLE_VALUE_NOT_SERIALIZED_OBSERVATION",
        "missing_base_preimage": config["base_round_config_id"] not in store,
        "full_corpus_kernel_example": False,
        "lean_sha256": hashlib.sha256(text.encode()).hexdigest(),
    }
    write_canonical_json(TARGET, result)
    return result


if __name__ == "__main__":
    result = generate()
    print(
        json.dumps({"status": "GENERATED", "small_kernel_cases": len(result["small_kernel_cases"])})
    )
