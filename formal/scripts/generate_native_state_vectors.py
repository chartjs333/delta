"""Concrete native COMMAND/ROUND_STATE codec samples; no transition admission claim."""

import argparse
import hashlib
import json
import re
import subprocess
from functools import cache
from pathlib import Path

import generate_native_vote_codec_vectors as vote
import generate_native_wal_lean as wal
from formal_artifacts import write_canonical_json
from native_admission_snapshot import decode_flat, require
from native_certificate_chain import NATIVE_SEMANTICS
from native_policy_wal import wal_entries

ROOT = wal.ROOT
FOLDER = ROOT / "formal/proposals/evidence/native-state-codec"
LEAN = ROOT / "formal/proofs/DeltaReduce/NativeStateCodecVectors.lean"
TARGET = ROOT / "formal/proposals/native-state-codec-vectors.json"
COMMAND_FIELDS = set(
    "actor_id body_hash command_kind formal_semantics_id height logical_tick "
    "request_id round_id schema_version type_name view".split()
)
PHASES = {"TICKETING_OPEN", "COMMITTED", "AVAILABLE", "ELIGIBLE", "AGGREGATED", "ABORTED"}


def decode_command(raw):
    """Small fixture reader; its 16KiB/4096 text limits are tooling restrictions."""
    require(type(raw) is bytes and 17 <= len(raw) <= 16384, "command byte bound")
    require(raw[:8] == b"DRC1\x01\x00\x00\x06", "command header")
    require(int.from_bytes(raw[8:12], "big") == len(raw) - 12, "command size")
    cursor = 12

    def take(n):
        nonlocal cursor
        require(n <= len(raw) - cursor, "truncated command")
        result = raw[cursor : cursor + n]
        cursor += n
        return result

    def text():
        require(take(1) == b"\x21", "command text tag")
        n = int.from_bytes(take(4), "big")
        require(n <= 4096, "fixture text bound")
        value = take(n)
        require(all(32 <= b <= 126 for b in value), "command ASCII")
        return value.decode("ascii")

    require(take(1) == b"\x31", "command map")
    require(int.from_bytes(take(4), "big") == 11, "command count")
    fields = {}
    for key in sorted(COMMAND_FIELDS):
        require(text() == key, "command key/order")
        fields[key] = text()
    require(cursor == len(raw), "command trailing bytes")
    require(fields["formal_semantics_id"] == NATIVE_SEMANTICS, "command semantics")
    require(fields["schema_version"] == "1.0.0", "command schema")
    require(fields["type_name"] == "COMMAND", "command name")
    for key in ["height", "logical_tick", "view"]:
        require(re.fullmatch(r"0|[1-9][0-9]*", fields[key]) is not None, "command decimal")
        require(int(fields[key]) < 2**64, "command integer bound")
    for key in ["actor_id", "command_kind", "request_id", "round_id"]:
        require(bool(fields[key]), "command empty identifier")
    require(re.fullmatch(r"sha256:[0-9a-f]{64}", fields["body_hash"]) is not None, "command ID")
    return fields


def decode_state(raw):
    fields = decode_flat(raw, 5)
    require(fields["phase"] in PHASES and bool(fields["round_id"]), "state phase/round")
    return fields


def original():
    row = wal.load()["after-state-command-retry"]
    entry = wal_entries(bytes.fromhex(row["wal_hex"]))[1]
    return [
        ("command", 6, entry["command"], decode_command(entry["command"])),
        ("recorded-next-state", 5, entry["state"], decode_state(entry["state"])),
        (
            "configured-initial-state",
            5,
            bytes.fromhex(row["initial_state_hex"]),
            decode_state(bytes.fromhex(row["initial_state_hex"])),
        ),
    ]


def envelope(kind, pairs):
    payload = b"\x31" + len(pairs).to_bytes(4, "big")
    for key, value in pairs:
        payload += vote.text(key)
        payload += b"\x10" + value.to_bytes(8, "big") if type(value) is int else vote.text(value)
    return b"DRC1\x01\x00" + kind.to_bytes(2, "big") + len(payload).to_bytes(4, "big") + payload


def cases():
    rows = original()
    result = [(name, kind, raw, True) for name, kind, raw, _ in rows]
    changes = [
        [
            ("command_kind", "UNKNOWN_COMMAND", True),
            ("actor_id", "", False),
            ("request_id", "", False),
            ("round_id", "", False),
            ("command_kind", "", False),
            ("height", "00", False),
            ("logical_tick", "-1", False),
            ("view", "+1", False),
            ("logical_tick", "18446744073709551615", True),
            ("view", "18446744073709551616", False),
            ("body_hash", "sha256:" + "0" * 64, True),
            ("body_hash", "sha256:" + "A" * 64, False),
            ("formal_semantics_id", "sha256:" + "0" * 64, False),
            ("schema_version", "1.0.1", False),
            ("type_name", "ROUND_STATE", False),
            ("actor_id", b"\x7f", False),
        ],
        [
            ("phase", "UNKNOWN", False),
            ("round_id", "", False),
            ("phase", "ABORTED", True),
            ("phase", "TICKETING_OPEN", True),
            ("available_ticket_count", 2, False),
            ("committed_ticket_count", 0, False),
            ("ticket_count", 0, False),
            ("ticket_count", 2**32, False),
            ("ticket_count", 2**32 - 1, True),
            ("ticket_count", "1", False),
            ("durable_sequence", "0", True),
            ("durable_sequence", "01", False),
            ("height", "18446744073709551615", True),
            ("view", "18446744073709551616", False),
            ("config_id", "sha256:" + "A" * 64, False),
            ("parent_checkpoint_id", "", False),
            ("state_root", "sha256:" + "0" * 64, True),
            ("type_name", "COMMAND", False),
        ],
    ]
    for index, substitutions in enumerate(changes):
        name, kind, raw, fields = rows[index]
        pairs = sorted(fields.items())
        for n, (key, value, accepted) in enumerate(substitutions):
            changed = dict(fields)
            changed[key] = value
            result.append(
                (f"{name}-field-{n}-{key}", kind, envelope(kind, sorted(changed.items())), accepted)
            )
        for label, changed in [
            ("missing", pairs[:-1]),
            ("extra", [*pairs, ("zzz", "x")]),
            ("duplicate", pairs[:1] + pairs),
            ("reordered", [pairs[1], pairs[0], *pairs[2:]]),
        ]:
            result.append((name + "-" + label, kind, envelope(kind, changed), False))
        result += [
            (name + "-trailing", kind, raw + b"\0", False),
            (name + "-truncated", kind, raw[:-1], False),
        ]
        for label, offset, value in [("magic", 0, 0), ("type", 7, 3), ("map-tag", 12, 0x30)]:
            changed = bytearray(raw)
            changed[offset] = value
            result.append((name + "-" + label, kind, bytes(changed), False))
    return result


def harness():
    rows = ",\n".join(f'{{"{name}",{kind},"{raw.hex()}"}}' for name, kind, raw, _ in cases())
    return (
        r"""#include <delta/core/protocol.hpp>
#include <delta/core/canonical.hpp>
#include <iostream>
#include <iomanip>
#include <string>
namespace ca=delta::core::canonical;namespace pr=delta::core::protocol;
ca::Bytes unhex(const std::string& s){ca::Bytes b;for(std::size_t i=0;i<s.size();i+=2)
 b.push_back(static_cast<std::byte>(std::stoul(s.substr(i,2),nullptr,16)));return b;}
int main(){struct Case{const char* name;unsigned kind;const char* hex;};const Case cases[]={
"""
        + rows
        + r"""
};for(const auto& test:cases){const auto raw=unhex(test.hex);bool ok=false;std::string id;
 try{if(test.kind==6){auto c=pr::parse_command(raw);if(pr::encode(c)!=raw) return 3;}
 else{auto s=pr::parse_round_state(raw);if(pr::encode(s)!=raw)return 3;}
 id=ca::content_id(test.kind==6?ca::Type::command:ca::Type::round_state,raw);ok=true;
 }catch(const ca::DecodeError&){}catch(const pr::ProtocolError&){}
 std::cout<<"{\"name\":"<<std::quoted(test.name)<<",\"accepted\":"<<(ok?"true":"false")
 <<",\"content_id\":"<<std::quoted(id)<<"}\n";}}
"""
    )


@cache
def native_source_hashes():
    return {p: hashlib.sha256(raw).hexdigest() for p, raw in vote.previous.wal.sources().items()}


def validate(data):
    require(data["source_commit"] == vote.SOURCE, "native source commit")
    require(data["source_sha256"] == native_source_hashes(), "native source hashes")
    require(data["compiler_flags"] == vote.previous.wal.FLAGS, "native compile flags")
    expected = cases()
    require(len(data["observed"]) == len(expected), "state codec case count")
    for row, (name, kind, raw, accepted) in zip(data["observed"], expected, strict=True):
        domain = b"command" if kind == 6 else b"round-state"
        identifier = (
            "sha256:" + hashlib.sha256(b"deltareduce:003:" + domain + b":v1\0" + raw).hexdigest()
        )
        require(type(row["accepted"]) is bool, "status type")
        require(
            row
            == {"name": name, "accepted": accepted, "content_id": identifier if accepted else ""},
            "native codec mismatch: " + name,
        )
    return data["observed"]


def cross_check(vcvars):
    blobs = vote.previous.wal.sources()
    build = ROOT / "formal/build/native-state-codec"
    build.mkdir(parents=True, exist_ok=True)
    FOLDER.mkdir(parents=True, exist_ok=True)
    for name, raw in blobs.items():
        path = build / (
            "include/" + name.split("/include/")[1] if "/include/" in name else Path(name).name
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    source = harness()
    (build / "harness.cpp").write_text(source, encoding="utf-8", newline="\n")
    units = [
        "delta-core-cpp/src/canonical.cpp",
        "delta-core-cpp/src/sha256.cpp",
        "delta-core-cpp/src/protocol.cpp",
    ]
    cmd = '@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b 1\ncl '
    cmd += (
        vote.previous.wal.FLAGS + " /Iinclude harness.cpp " + " ".join(Path(p).name for p in units)
    )
    cmd += " /Fe:state.exe\nexit /b %errorlevel%\n"
    (build / "compile.cmd").write_text(cmd, encoding="utf-8", newline="\r\n")
    r = subprocess.run(
        ["cmd", "/d", "/c", str(build / "compile.cmd")], cwd=build, capture_output=True
    )
    log = (r.stdout + r.stderr).decode("utf-8")
    (FOLDER / "compile.txt").write_text(
        "\n".join(x.rstrip() for x in log.splitlines()).rstrip() + "\n",
        encoding="utf-8",
        newline="\n",
    )
    require(r.returncode == 0, "native state codec compilation")
    output = subprocess.check_output([str(build / "state.exe")], cwd=build, timeout=90).decode(
        "ascii"
    )
    result = {
        "source_commit": vote.SOURCE,
        "source_sha256": {p: hashlib.sha256(b).hexdigest() for p, b in blobs.items()},
        "compiler": re.search(r"Optimizing Compiler Version ([0-9.]+) for x64", log)[1],
        "compiler_flags": vote.previous.wal.FLAGS,
        "unmodified_translation_units": units,
        "observed": [json.loads(line) for line in output.splitlines()],
        "native_codec_execution": True,
        "native_runtime_execution": False,
        "arithmetic_execution": False,
        "native_export_authenticated": False,
        "gate_eligible": False,
    }
    validate(result)
    (FOLDER / "harness.cpp").write_text(source, encoding="utf-8", newline="\n")
    write_canonical_json(FOLDER / "cpp-cross-check.json", result)


def generate():
    native = validate(json.loads((FOLDER / "cpp-cross-check.json").read_bytes()))
    originals = original()
    lines = [
        "import DeltaReduce.NativeStateBytes",
        "import DeltaReduce.NativeWalScanVectors",
        "set_option maxRecDepth 32768",
        "set_option maxHeartbeats 1000000",
        "namespace DeltaReduce.NativeStateCodecVectors",
        "open NativeReceiptBytes NativeVoteBytes NativeStateBytes",
    ]
    texts = sorted(
        {
            str(v)
            for _, _, _, fields in originals
            for pair in fields.items()
            for v in pair
            if type(v) is str
        }
    )
    lemmas = {}
    for index, value in enumerate(texts):
        lemmas[value] = f"text{index}"
        lines.append(
            f"theorem text{index} : textBytes (ascii {json.dumps(value)}) = "
            f"{wal.lit(vote.text(value))} := by decide"
        )
    for i, (_, kind, raw, fields) in enumerate(originals, 1):
        is_command = kind == 6
        keys = (
            [
                "actor_id",
                "body_hash",
                "command_kind",
                "height",
                "logical_tick",
                "request_id",
                "round_id",
                "view",
            ]
            if is_command
            else [
                "available_ticket_count",
                "committed_ticket_count",
                "config_id",
                "durable_sequence",
                "height",
                "parent_checkpoint_id",
                "phase",
                "round_id",
                "state_root",
                "ticket_count",
                "view",
            ]
        )
        typ, field_fn, enc_fn, valid_fn = (
            ("Command", "commandFields", "encodeCommand", "CommandValid")
            if is_command
            else ("State", "stateFields", "encodeState", "StateValid")
        )
        args = [
            str(fields[k]) if type(fields[k]) is int else "ascii " + json.dumps(fields[k])
            for k in keys
        ]
        raw_expr = (
            "NativeWalVectors.command3"
            if i == 1
            else "NativeWalVectors.state3"
            if i == 2
            else wal.lit(raw)
        )
        numbers = [
            fields[k]
            for k in (
                ["height", "logical_tick", "view"]
                if is_command
                else ["durable_sequence", "height", "view"]
            )
        ]
        lines += [
            f"def wire{i} : Wire{typ} := ⟨" + ",".join(args) + "⟩",
            f"def value{i} : {typ} := ⟨wire{i}," + ",".join(numbers) + "⟩",
            f"def raw{i} : Bytes := {raw_expr}",
            f"theorem payload{i} : NativeStateBytes.payload ({field_fn} wire{i}) = "
            f"{wal.lit(raw[12:])} := by",
            f"  simp only "
            f"[NativeStateBytes.payload,{field_fn},wire{i},NativeStateBytes.encodeFields,scalarBytes,nativeSemantics,"
            + ",".join(
                lemmas[v]
                for v in sorted({v for pair in fields.items() for v in pair if type(v) is str})
            )
            + "]",
            "  rfl",
            f"theorem bytes{i} : {enc_fn} wire{i} = raw{i} := by",
            f"  unfold {enc_fn} encodeEnvelope; rw [payload{i}]; rfl",
            f"theorem frame{i} : EnvelopeValid {kind} ({field_fn} wire{i}) := by",
            "  constructor; · decide",
            f"  change ({enc_fn} wire{i}).length ≤ maxEnvelope; rw [bytes{i}]; decide",
            f"theorem valid{i} : {valid_fn} value{i} := ⟨frame{i},"
            + ",".join(["by decide"] * (8 if is_command else 11))
            + "⟩",
            f"theorem parsed{i} : decode{typ} raw{i} = some value{i} :=",
            f"  {'command' if is_command else 'state'}FromBytes value{i} raw{i} valid{i} bytes{i}",
        ]
        domain = "commandDomain" if is_command else "stateDomain"
        domain_bytes = (
            b"deltareduce:003:" + (b"command" if is_command else b"round-state") + b":v1\0"
        )
        digest = hashlib.sha256(domain_bytes + raw).digest()
        identifier = next(r["content_id"] for r in native if r["name"] == originals[i - 1][0])
        lines += [
            f"def sha{i} (b : Bytes) : Bytes := if b = contentPreimage {domain} "
            f"raw{i} then {wal.lit(digest)} else []",
            f"theorem nativeId{i} : contentId sha{i} {domain} raw{i} = some (ascii "
            f"{json.dumps(identifier)}) := by",
            f"  simp only [contentId,sha{i},↓reduceIte]; rfl",
        ]
    lines += [
        "theorem nativeEntryParsed : inspectEntry NativeWalVectors.entry3 = some "
        "(value1,value2) :=",
        "  entryFromComponents NativeWalVectors.entry3 value1 value2 rfl parsed1 parsed2",
        "theorem nativeAllEntrySequence : NativeWalVectors.entry3.sequence = 2 ∧ "
        "value2.sequence = 1 := by decide",
        "theorem scannedOriginalCommand : NativeWalVectors.entry3.sequence = 2 ∧ "
        "NativeWalVectors.entry3.kind = 1 ∧",
        "    NativeWalBytes.encode NativeWalScanVectors.sha "
        "NativeWalVectors.entry3 = NativeWalVectors.raw3 ∧",
        "    encodeCommand value1.wire = NativeWalVectors.entry3.command ∧ "
        "encodeState value2.wire = NativeWalVectors.entry3.state :=",
        "  scannedCommandOrigin NativeWalScanVectors.sha "
        "NativeWalScanVectors.stream NativeWalScanVectors.fullResult",
        "    1 ⟨NativeWalVectors.entry3,NativeWalVectors.raw3⟩ value1 value2 "
        "NativeWalScanVectors.checkedNativeStream rfl nativeEntryParsed",
        "theorem nativeVoteCannotBeStateCommand : inspectEntry "
        "NativeWalVectors.entry2 = none := by decide",
    ]
    for index, (field, expression) in enumerate(
        [
            ("actor", "[]"),
            ("commandKind", "[]"),
            ("request", "[]"),
            ("round", "[]"),
            ("height", 'ascii "00"'),
            ("tick", 'ascii "-1"'),
            ("view", 'ascii "18446744073709551616"'),
            ("body", 'ascii "sha256:bad"'),
        ]
    ):
        lines.append(
            f"theorem commandReject{index} : interpretCommand "
            f"{{wire1 with {field} := {expression}}} = none := by decide"
        )
    for index, (field, expression) in enumerate(
        [
            ("available", "2"),
            ("committed", "0"),
            ("total", "0"),
            ("total", "256^4"),
            ("phase", 'ascii "UNKNOWN"'),
            ("round", "[]"),
            ("sequence", 'ascii "01"'),
            ("view", 'ascii "18446744073709551616"'),
            ("parent", "[]"),
            ("config", "[]"),
            ("root", "[]"),
        ]
    ):
        lines.append(
            f"theorem stateReject{index} : interpretState "
            f"{{wire2 with {field} := {expression}}} = none := by decide"
        )
    lines += [
        "theorem commandKindIsNotAdmission : (interpretCommand {wire1 with "
        'commandKind := ascii "UNKNOWN_COMMAND"}).isSome = true := by decide',
        "theorem changedRootCanParse : (interpretState {wire2 with root := ascii "
        '"sha256:0000000000000000000000000000000000000000000000000000000000000000"}'
        ").isSome = true := by decide",
        "theorem maximumTime : (interpretCommand {wire1 with tick := ascii "
        '"18446744073709551615"}).isSome = true := by decide',
        "theorem maximumCount : (interpretState {wire2 with total := "
        "256^4-1}).isSome = true := by decide",
        "theorem zeroStateSequenceAllowed : (interpretState {wire2 with sequence "
        ':= ascii "0"}).isSome = true := by decide',
        'theorem unsignedTagRequired : readScalar .uint (textBytes (ascii "1")) '
        "= none := by decide",
        "theorem unsignedUsesEightBytes : readScalar .uint ([16]++be 8 "
        "4294967296) = some (.uint 4294967296,[]) := by decide",
        "theorem truncatedUnsigned : readScalar .uint ([16]++be 4 1) = none := by decide",
        "theorem wrongCommandType : readCommand (header 5 ++ sizedBytes "
        "(NativeStateBytes.payload (commandFields wire1))) = none := by decide",
        "theorem commandTrailingByte : decodeCommand (raw1++[0]) = none := by decide",
        "theorem stateTrailingByte : decodeState (raw2++[0]) = none := by decide",
        "theorem commandFieldsWrongConstants : commandValues ((commandFields "
        "wire1).map Prod.snd |>.set 3 (.text [])) = none := by decide",
        "theorem stateFieldsWrongConstants : stateValues ((stateFields "
        "wire2).map Prod.snd |>.set 4 (.text [])) = none := by decide",
        "end DeltaReduce.NativeStateCodecVectors",
    ]
    LEAN.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    write_canonical_json(
        TARGET,
        {
            "scope": "CONCRETE_NATIVE_CODECS_NOT_STATE_TRANSITION_OR_FULL_RECOVERY",
            "formal_go": False,
            "native_codec_cases": [
                {"name": n, "kind": k, "bytes_hex": b.hex(), "accepted": a}
                for n, k, b, a in cases()
            ],
            "original": [
                {"name": n, "kind": k, "bytes_hex": b.hex(), "fields": f}
                for n, k, b, f in originals
            ],
            "native_export_authenticated": False,
            "native_transition_proved": False,
        },
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cross-check", type=Path)
    args = parser.parse_args()
    if args.cross_check:
        cross_check(args.cross_check)
    generate()
    print("native state codec vectors generated")


if __name__ == "__main__":
    main()
