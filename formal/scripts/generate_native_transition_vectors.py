"""Pinned native summary-command reconstruction; not full protocol recovery."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

import generate_native_state_vectors as codec
from formal_artifacts import write_canonical_json
from native_admission_snapshot import require

ROOT = codec.ROOT
FOLDER = ROOT / "formal/proposals/evidence/native-transition"
LEAN = ROOT / "formal/proofs/DeltaReduce/NativeTransitionVectors.lean"
TARGET = ROOT / "formal/proposals/native-transition-vectors.json"
NAMES = [
    "FINALIZE_ROUND_CONFIG",
    "ADVANCE_VIEW",
    "ACCEPT_COMMITMENT",
    "ACCEPT_AVAILABILITY",
    "FINALIZE_INPUT_FREEZE",
    "FINALIZE_AGGREGATE",
    "CERTIFY_ABORT",
]
ACTIONS = ["config", "view", "commitment", "availability", "freeze", "aggregate", "abort"]
ERRORS = [
    "round_mismatch",
    "height_mismatch",
    "view_mismatch",
    "unsupported_command",
    "illegal_phase",
    "ticket_limit_reached",
    "availability_limit_reached",
    "input_set_empty",
    "terminal_state",
    "durable_sequence_overflow",
]


class Rejection(ValueError):
    pass


def rule(s, c):
    def check(p, e):
        if not p:
            raise Rejection(e)

    check(c["round_id"] == s["round_id"], "round_mismatch")
    check(c["height"] == s["height"], "height_mismatch")
    k = c["command_kind"]
    phase = s["phase"]
    n = dict(s)
    if k != "ADVANCE_VIEW":
        check(c["view"] == s["view"], "view_mismatch")
    if k == "FINALIZE_ROUND_CONFIG":
        check(phase == "TICKETING_OPEN", "illegal_phase")
        return n
    check(phase not in ["AGGREGATED", "ABORTED"], "terminal_state")
    if k == "ADVANCE_VIEW":
        check(int(s["view"]) < 2**64 - 1 and int(c["view"]) == int(s["view"]) + 1, "view_mismatch")
        n["view"] = c["view"]
    elif k == "ACCEPT_COMMITMENT":
        check(phase in ["TICKETING_OPEN", "COMMITTED"], "illegal_phase")
        check(s["committed_ticket_count"] < s["ticket_count"], "ticket_limit_reached")
        n["committed_ticket_count"] += 1
        n["phase"] = "COMMITTED"
    elif k == "ACCEPT_AVAILABILITY":
        check(phase in ["COMMITTED", "AVAILABLE"], "illegal_phase")
        check(
            s["available_ticket_count"] < s["committed_ticket_count"], "availability_limit_reached"
        )
        n["available_ticket_count"] += 1
        n["phase"] = "AVAILABLE"
    elif k == "FINALIZE_INPUT_FREEZE":
        check(phase == "AVAILABLE", "illegal_phase")
        check(s["available_ticket_count"] > 0, "input_set_empty")
        n["phase"] = "ELIGIBLE"
    elif k == "FINALIZE_AGGREGATE":
        check(phase == "ELIGIBLE", "illegal_phase")
        n["phase"] = "AGGREGATED"
        n["state_root"] = c["body_hash"]
    elif k == "CERTIFY_ABORT":
        n["phase"] = "ABORTED"
    else:
        raise Rejection("unsupported_command")
    check(int(s["durable_sequence"]) < 2**64 - 1, "durable_sequence_overflow")
    n["durable_sequence"] = str(int(s["durable_sequence"]) + 1)
    return n


def value(v):
    if isinstance(v, str):
        return codec.vote.text(v)
    if type(v) is int:
        return b"\x10" + v.to_bytes(8, "big")
    if type(v) is list:
        return b"\x30" + len(v).to_bytes(4, "big") + b"".join(map(value, v))
    assert type(v) is dict
    return (
        b"\x31"
        + len(v).to_bytes(4, "big")
        + b"".join(codec.vote.text(k) + value(v[k]) for k in sorted(v))
    )


def envelope(kind, fields):
    body = value(fields)
    return b"DRC1\x01\x00" + kind.to_bytes(2, "big") + len(body).to_bytes(4, "big") + body


def identifier(domain, raw):
    return (
        "sha256:"
        + hashlib.sha256(b"deltareduce:003:" + domain.encode() + b":v1\0" + raw).hexdigest()
    )


def outputs(s, c):
    prior = envelope(5, s)
    command = envelope(6, c)
    codec.decode_state(prior)
    codec.decode_command(command)
    n = rule(s, c)
    state = envelope(5, n)
    pi = identifier("round-state", prior)
    ci = identifier("command", command)
    ni = identifier("round-state", state)
    effects = {
        "effects": [
            {
                "body_hash": ni,
                "effect_id": "effect:" + c["request_id"] + ":01:persist",
                "kind": "PERSIST_STATE",
                "target_id": c["actor_id"],
            },
            {
                "body_hash": c["body_hash"],
                "effect_id": "effect:" + c["request_id"] + ":02:publish",
                "kind": "PUBLISH_CERTIFICATE",
                "target_id": "validators",
            },
        ],
        "formal_semantics_id": codec.NATIVE_SEMANTICS,
        "next_state_root": ni,
        "prior_state_root": pi,
        "request_id": c["request_id"],
        "round_id": c["round_id"],
        "schema_version": "1.0.0",
        "type_name": "EFFECT_BATCH",
    }
    eff = envelope(7, effects)
    ei = identifier("effect-batch", eff)
    record = {
        "command_id": ci,
        "effect_batch_id": ei,
        "formal_semantics_id": codec.NATIVE_SEMANTICS,
        "next_state_root": ni,
        "prior_state_root": pi,
        "record_kind": "TRANSITION",
        "round_id": c["round_id"],
        "schema_version": "1.0.0",
        "sequence": n["durable_sequence"],
        "type_name": "WAL_RECORD",
    }
    rec = envelope(8, record)
    ri = identifier("wal-record", rec)
    return (
        {
            "state_hex": state.hex(),
            "effects_hex": eff.hex(),
            "record_hex": rec.hex(),
            "prior_id": pi,
            "command_id": ci,
            "next_id": ni,
            "effects_id": ei,
            "record_id": ri,
        },
        n,
        effects,
        record,
    )


def cases():
    original = codec.original()
    basec = original[0][3]
    bases = original[2][3]
    result = [("original-freeze", dict(bases), dict(basec))]
    for phase in ["TICKETING_OPEN", "COMMITTED", "AVAILABLE", "ELIGIBLE", "AGGREGATED", "ABORTED"]:
        for kind in NAMES:
            s = {
                **bases,
                "phase": phase,
                "ticket_count": 3,
                "committed_ticket_count": 1,
                "available_ticket_count": 0,
            }
            if phase == "AVAILABLE":
                s["available_ticket_count"] = 1
                s["committed_ticket_count"] = 2
            c = {**basec, "command_kind": kind, "view": "1" if kind == "ADVANCE_VIEW" else "0"}
            result.append((phase + "-" + kind, s, c))
    for name, sc, cc in [
        ("wrong-round", {}, {"round_id": "other"}),
        ("wrong-height", {}, {"height": "2"}),
        ("wrong-view", {}, {"view": "1"}),
        ("unknown", {}, {"command_kind": "UNKNOWN_COMMAND"}),
        ("empty-freeze", {"available_ticket_count": 0}, {}),
        ("sequence-overflow", {"durable_sequence": str(2**64 - 1)}, {}),
        (
            "config-max-sequence",
            {"phase": "TICKETING_OPEN", "durable_sequence": str(2**64 - 1)},
            {"command_kind": "FINALIZE_ROUND_CONFIG"},
        ),
        ("view-jump", {}, {"command_kind": "ADVANCE_VIEW", "view": "2"}),
        ("view-max", {"view": str(2**64 - 1)}, {"command_kind": "ADVANCE_VIEW", "view": "0"}),
        (
            "view-sequence-overflow",
            {"durable_sequence": str(2**64 - 1)},
            {"command_kind": "ADVANCE_VIEW", "view": "1"},
        ),
        ("tickets-full", {"phase": "COMMITTED"}, {"command_kind": "ACCEPT_COMMITMENT"}),
        ("availability-full", {}, {"command_kind": "ACCEPT_AVAILABILITY"}),
        (
            "uint32-last-commit",
            {"phase": "COMMITTED", "ticket_count": 2**32 - 1, "committed_ticket_count": 2**32 - 2},
            {"command_kind": "ACCEPT_COMMITMENT"},
        ),
        (
            "uint32-last-availability",
            {
                "ticket_count": 2**32 - 1,
                "committed_ticket_count": 2**32 - 1,
                "available_ticket_count": 2**32 - 2,
            },
            {"command_kind": "ACCEPT_AVAILABILITY"},
        ),
        ("last-sequence", {"durable_sequence": str(2**64 - 2)}, {}),
        ("old-clock-core-allows", {}, {"logical_tick": "0"}),
    ]:
        result.append((name, {**bases, **sc}, {**basec, **cc}))
    return result


def expected():
    rows = []
    for name, s, c in cases():
        try:
            o, _, _, _ = outputs(s, c)
            rows.append({"name": name, "accepted": True, "error": "", **o})
        except Rejection as e:
            rows.append({"name": name, "accepted": False, "error": str(e)})
    return rows


def harness():
    rows = ",\n".join(
        "{"
        + ",".join(json.dumps(x) for x in [name, envelope(5, s).hex(), envelope(6, c).hex()])
        + "}"
        for name, s, c in cases()
    )
    return (
        (
            "#include <delta/core/transition.hpp>\n#include <delta/core/cano"
            "nical.hpp>\n#include <iostream>\n#include <iomanip>\n#include <ss"
            "tream>\n#include <string>\nnamespace ca=delta::core::canonical;n"
            "amespace tr=delta::core::transition;\nca::Bytes unhex(const std"
            "::string& s){ca::Bytes b;for(std::size_t i=0;i<s.size();i+=2)b"
            ".push_back(static_cast<std::byte>(std::stoul(s.substr(i,2),nul"
            "lptr,16)));return b;}\nstd::string hex(const ca::Bytes& b){std:"
            ":ostringstream s;for(auto v:b)s<<std::hex<<std::setfill('0')<<"
            "std::setw(2)<<std::to_integer<unsigned>(v);return s.str();}\nin"
            "t main(){struct Case{const char* name;const char* state;const "
            "char* command;};const Case cases[]={\n"
        )
        + rows
        + (
            '\n};const char* errors[]={"round_mismatch","height_mismatch","v'
            'iew_mismatch","unsupported_command","illegal_phase","ticket_li'
            'mit_reached","availability_limit_reached","input_set_empty","t'
            'erminal_state","durable_sequence_overflow"};\nfor(const auto& c'
            ':cases){std::cout<<"{\\"name\\":\\""<<c.name<<"\\"";\ntry{auto r=tr'
            '::apply(unhex(c.state),unhex(c.command));std::cout<<",\\"accept'
            'ed\\":true,\\"error\\":\\"\\"";\nstd::cout<<",\\"state_hex\\":\\""<<hex'
            '(r.next_state_bytes)<<"\\",\\"effects_hex\\":\\""<<hex(r.effect_ba'
            'tch_bytes)<<"\\",\\"record_hex\\":\\""<<hex(r.wal_record_bytes)<<"'
            '\\"";\nstd::cout<<",\\"prior_id\\":\\""<<r.prior_state_id<<"\\",\\"co'
            'mmand_id\\":\\""<<r.command_id<<"\\",\\"next_id\\":\\""<<r.next_stat'
            'e_id<<"\\",\\"effects_id\\":\\""<<r.effect_batch_id<<"\\",\\"record_'
            'id\\":\\""<<r.wal_record_id<<"\\"";\n}catch(const tr::TransitionEr'
            'ror& e){std::cout<<",\\"accepted\\":false,\\"error\\":\\""<<errors['
            'static_cast<unsigned>(e.code())]<<"\\"";}\ncatch(const std::exce'
            'ption&){std::cout<<",\\"accepted\\":false,\\"error\\":\\"UNEXPECTED'
            '_PARSE_OR_OTHER_ERROR\\"";}\nstd::cout<<"}\\n";}}\n'
        )
    )


def validate(data):
    require(data["source_commit"] == codec.vote.SOURCE, "source commit")
    require(data["source_sha256"] == codec.native_source_hashes(), "source hashes")
    require(data["compiler_flags"] == codec.vote.previous.wal.FLAGS, "compiler flags")
    require(
        data["unmodified_translation_units"]
        == [
            "delta-core-cpp/src/" + n + ".cpp"
            for n in ["canonical", "sha256", "protocol", "transition"]
        ],
        "translation units",
    )
    require(
        data["native_core_transition_execution"] is True
        and all(
            data[k] is False
            for k in [
                "native_runtime_execution",
                "arithmetic_execution",
                "native_export_authenticated",
                "gate_eligible",
            ]
        ),
        "scope claims",
    )
    require(data["observed"] == expected(), "native transition comparison")
    require(all(type(r["accepted"]) is bool for r in data["observed"]), "status type")
    old = codec.wal.wal_entries(
        bytes.fromhex(codec.wal.load()["after-state-command-retry"]["wal_hex"])
    )[1]
    original = data["observed"][0]
    for key, field in [
        ("state_hex", "state"),
        ("effects_hex", "effects"),
        ("record_hex", "record"),
    ]:
        require(bytes.fromhex(original[key]) == old[field], "original WAL " + field)
    return data["observed"]


def cross_check(vcvars):
    blobs = codec.vote.previous.wal.sources()
    build = ROOT / "formal/build/native-transition"
    build.mkdir(parents=True, exist_ok=True)
    FOLDER.mkdir(parents=True, exist_ok=True)
    for name, raw in blobs.items():
        p = build / (
            "include/" + name.split("/include/")[1] if "/include/" in name else Path(name).name
        )
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
    source = harness()
    (build / "harness.cpp").write_text(source, encoding="utf-8", newline="\n")
    units = [
        "delta-core-cpp/src/" + n + ".cpp"
        for n in ["canonical", "sha256", "protocol", "transition"]
    ]
    cmd = (
        '@echo off\ncall "'
        + str(vcvars)
        + '" >nul\nif errorlevel 1 exit /b 1\ncl '
        + codec.vote.previous.wal.FLAGS
        + " /Iinclude harness.cpp "
        + " ".join(Path(p).name for p in units)
        + " /Fe:transition.exe\nexit /b %errorlevel%\n"
    )
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
    require(r.returncode == 0, "native compilation")
    output = subprocess.check_output([str(build / "transition.exe")], cwd=build, timeout=90).decode(
        "ascii"
    )
    data = {
        "source_commit": codec.vote.SOURCE,
        "source_sha256": codec.native_source_hashes(),
        "compiler": re.search(r"Optimizing Compiler Version ([0-9.]+) for x64", log)[1],
        "compiler_flags": codec.vote.previous.wal.FLAGS,
        "unmodified_translation_units": units,
        "observed": [json.loads(line) for line in output.splitlines()],
        "native_core_transition_execution": True,
        "native_runtime_execution": False,
        "arithmetic_execution": False,
        "native_export_authenticated": False,
        "gate_eligible": False,
    }
    validate(data)
    (FOLDER / "harness.cpp").write_text(source, encoding="utf-8", newline="\n")
    write_canonical_json(FOLDER / "cpp-cross-check.json", data)


def lean_state(s):
    keys = [
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
    args = [str(s[k]) if type(s[k]) is int else "ascii " + json.dumps(s[k]) for k in keys]
    return (
        "⟨⟨"
        + ",".join(args)
        + "⟩,"
        + ",".join(s[k] for k in ["durable_sequence", "height", "view"])
        + "⟩"
    )


def lean_command(c):
    keys = [
        "actor_id",
        "body_hash",
        "command_kind",
        "height",
        "logical_tick",
        "request_id",
        "round_id",
        "view",
    ]
    return (
        "⟨⟨"
        + ",".join("ascii " + json.dumps(c[k]) for k in keys)
        + "⟩,"
        + ",".join(c[k] for k in ["height", "logical_tick", "view"])
        + "⟩"
    )


def generate():
    native = validate(json.loads((FOLDER / "cpp-cross-check.json").read_bytes()))
    lines = [
        "import DeltaReduce.NativeTransition",
        "import DeltaReduce.NativeStateCodecVectors",
        "set_option maxRecDepth 32768",
        "set_option maxHeartbeats 1000000",
        "namespace DeltaReduce.NativeTransitionVectors",
        "open NativeReceiptBytes NativeVoteBytes NativeStateBytes NativeTransition",
    ]
    for i, ((_, s, c), row) in enumerate(zip(cases(), native, strict=True)):
        lines += [
            f"def s{i} : State := " + lean_state(s),
            f"def c{i} : Command := " + lean_command(c),
        ]
        if row["accepted"]:
            n = rule(s, c)
            lines += [
                f"def n{i} : State := " + lean_state(n),
                f"theorem step{i} : step s{i} c{i} = some n{i} := by decide",
            ]
        elif c["command_kind"] not in NAMES:
            lines += [
                f"theorem step{i} : step s{i} c{i} = none := unknownReject s{i} c{i} (by decide)"
            ]
        else:
            action = ACTIONS[NAMES.index(c["command_kind"])]
            lines += [
                f"theorem step{i} : step s{i} c{i} = none := "
                f"disabledReject s{i} c{i} .{action} (by decide) (by decide)"
            ]
    # All complete bytes below are the original runtime WAL command output.
    o, _, effects, record = outputs(cases()[0][1], cases()[0][2])
    textset = set()

    def collect(v):
        if isinstance(v, str):
            textset.add(v)
        elif isinstance(v, list):
            for x in v:
                collect(x)
        elif isinstance(v, dict):
            for k, x in v.items():
                collect(k)
                collect(x)

    collect(effects)
    effect_texts = set(textset)
    textset.clear()
    collect(record)
    record_texts = set(textset)
    textset.update(effect_texts)
    indices = {t: i for i, t in enumerate(sorted(textset))}
    for i, t in enumerate(sorted(textset)):
        lines.append(
            f"theorem text{i} : textBytes (ascii {json.dumps(t)}) = "
            f"{codec.wal.lit(codec.vote.text(t))} := by decide"
        )
    lines += [
        f"def priorId := ascii {json.dumps(o['prior_id'])}",
        f"def commandId := ascii {json.dumps(o['command_id'])}",
        f"def nextId := ascii {json.dumps(o['next_id'])}",
        f"def effectsId := ascii {json.dumps(o['effects_id'])}",
        f"def recordId := ascii {json.dumps(o['record_id'])}",
    ]
    unfold = (
        "effectPayload,persistFields,publishFields,effectFields,effectI"
        "d,effectTail,NativeStateBytes.payload,encodeFields,scalarBytes"
        ",nativeSemantics,c0,priorId,nextId"
    )
    lines += [
        "theorem effectPayloadBytes : effectPayload c0 priorId nextId = "
        + codec.wal.lit(bytes.fromhex(o["effects_hex"])[12:])
        + " := by",
        "  simp only ["
        + unfold
        + ","
        + ",".join(f"text{indices[t]}" for t in sorted(effect_texts))
        + "]",
        "  rfl",
        "theorem effectBytes : encodeEffects c0 priorId nextId = NativeWalVectors.effects3 := by",
        "  unfold encodeEffects; rw [effectPayloadBytes]; rfl",
    ]
    lines += [
        "theorem walPayloadBytes : NativeStateBytes.payload "
        "(walFields c0 1 priorId commandId nextId effectsId) = "
        + codec.wal.lit(bytes.fromhex(o["record_hex"])[12:])
        + " := by",
        (
            "  simp only [NativeStateBytes.payload,walFields,c0,decimal,enc"
            "odeFields,scalarBytes,nativeSemantics,priorId,commandId,nextId"
            ",effectsId,"
        )
        + ",".join(f"text{indices[t]}" for t in sorted(record_texts))
        + "]",
        "  rfl",
        (
            "theorem recordBytes : encodeWal c0 1 priorId commandId nextId "
            "effectsId = NativeWalVectors.record3 := by"
        ),
        "  unfold encodeWal encodeEnvelope; rw [walPayloadBytes]; rfl",
    ]
    # Proof composition / hash adapters appended separately below.
    lines += tail(o)
    lines += ["end DeltaReduce.NativeTransitionVectors"]
    lines = [
        line.replace(",encodeFields,", ",NativeStateBytes.encodeFields,").replace(
            "actions.map actionName", "actions.map NativeTransition.actionName"
        )
        for line in lines
    ]
    LEAN.write_text("\n\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    write_canonical_json(
        TARGET,
        {
            "scope": "PINNED_NATIVE_SUMMARY_TRANSITION_NOT_PUBLIC_PROTOCOL_OR_RUNTIME_RECOVERY",
            "formal_go": False,
            "native_runtime_execution": False,
            "native_export_authenticated": False,
            "cases": [
                {
                    "name": name,
                    "prior_hex": envelope(5, s).hex(),
                    "command_hex": envelope(6, c).hex(),
                    "expected": row,
                }
                for (name, s, c), row in zip(cases(), native, strict=True)
            ],
        },
    )


def tail(o):
    pairs = [
        (
            "stateDomain",
            "NativeStateCodecVectors.raw3",
            "priorId",
            "round-state",
            codec.original()[2][2],
        ),
        (
            "commandDomain",
            "NativeWalVectors.command3",
            "commandId",
            "command",
            codec.original()[0][2],
        ),
        (
            "stateDomain",
            "NativeWalVectors.state3",
            "nextId",
            "round-state",
            bytes.fromhex(o["state_hex"]),
        ),
        (
            "effectDomain",
            "NativeWalVectors.effects3",
            "effectsId",
            "effect-batch",
            bytes.fromhex(o["effects_hex"]),
        ),
        (
            "walDomain",
            "NativeWalVectors.record3",
            "recordId",
            "wal-record",
            bytes.fromhex(o["record_hex"]),
        ),
    ]
    lines = ["def sha (b : Bytes) : Bytes :="]
    for domain, raw, _, d, bs in pairs:
        digest = hashlib.sha256(b"deltareduce:003:" + d.encode() + b":v1\0" + bs).digest()
        lines.append(f"  if b = contentPreimage {domain} {raw} then {codec.wal.lit(digest)} else")
    lines.append("  []")
    for i, (domain, raw, key, _, _) in enumerate(pairs):
        lines += [
            f"theorem hash{i} : contentId sha {domain} {raw} = some {key} := by",
            "  unfold contentId sha",
        ]
        for prior_domain, prior_raw, _, _, _ in pairs[:i]:
            lines.append(
                f"  rw [if_neg (by decide : contentPreimage {domain} {raw} ≠ "
                f"contentPreimage {prior_domain} {prior_raw})]"
            )
        lines += ["  rw [if_pos rfl]; rfl"]
    lines += [
        (
            "theorem originalStateBytes : encodeState n0.wire = NativeWalVe"
            "ctors.state3 := NativeStateCodecVectors.bytes2"
        ),
        (
            "theorem originalPriorBytes : encodeState s0.wire = NativeState"
            "CodecVectors.raw3 := NativeStateCodecVectors.bytes3"
        ),
        (
            "theorem originalCommandBytes : encodeCommand c0.wire = NativeW"
            "alVectors.command3 := NativeStateCodecVectors.bytes1"
        ),
        "theorem originalEffectsValid : EffectsValid c0 priorId nextId := by",
        "  refine ⟨by decide,by decide,by decide,by decide,by decide,by decide,by decide,?_⟩",
        "  rw [effectBytes]; decide",
        "theorem originalWalValid : WalValid c0 1 priorId commandId nextId effectsId := by",
        "  refine ⟨by decide,by decide,by decide,by decide,by decide,by decide,by decide,?_⟩",
        "  change (encodeWal c0 1 priorId commandId nextId effectsId).length ≤ maxEnvelope",
        "  rw [recordBytes]; decide",
        (
            "def nativeOutput : Output := ⟨n0,NativeWalVectors.state3,Nativ"
            "eWalVectors.effects3,NativeWalVectors.record3,priorId,commandI"
            "d,nextId,effectsId,recordId⟩"
        ),
        "theorem nativeBuilt : Built sha s0 c0 n0 nativeOutput := by",
        (
            "  refine ⟨rfl,originalStateBytes.symm,?_,?_,hash2,originalEffe"
            "ctsValid,effectBytes.symm,hash3,originalWalValid,recordBytes.s"
            "ymm,hash4⟩"
        ),
        "  · rw [originalPriorBytes]; exact hash0",
        "  · rw [originalCommandBytes]; exact hash1",
        (
            "theorem nativeExecuted : execute sha s0 c0 = some nativeOutput"
            " := executeFromComponents sha s0 c0 n0 nativeOutput step0 nati"
            "veBuilt"
        ),
        (
            "theorem nativeBytesExecuted : fromBytes sha NativeStateCodecVe"
            "ctors.raw3 NativeWalVectors.command3 = some nativeOutput :="
        ),
        (
            "  bytesFromComponents sha _ _ s0 c0 nativeOutput NativeStateCo"
            "decVectors.parsed3 NativeStateCodecVectors.parsed1 nativeExecu"
            "ted"
        ),
        (
            "theorem originalEntryRecomputed : replayEntry sha NativeStateC"
            "odecVectors.raw3 NativeWalVectors.entry3 = some nativeOutput :"
            "="
        ),
        "  replayFromComputed sha _ _ _ rfl nativeBytesExecuted ⟨rfl,rfl,rfl⟩",
        (
            "theorem originalWalStateCounters : NativeWalVectors.entry3.seq"
            "uence = 2 ∧ nativeOutput.next.sequence = 1 := by decide"
        ),
        (
            "theorem changedStateRejected : replayEntry sha NativeStateCode"
            "cVectors.raw3 {NativeWalVectors.entry3 with state := []} = non"
            "e :="
        ),
        "  replayRejectChanged nativeBytesExecuted (Or.inl (by decide))",
        (
            "theorem changedEffectsRejected : replayEntry sha NativeStateCo"
            "decVectors.raw3 {NativeWalVectors.entry3 with effects := []} ="
            " none :="
        ),
        "  replayRejectChanged nativeBytesExecuted (Or.inr (Or.inl (by decide)))",
        (
            "theorem changedInnerWalRejected : replayEntry sha NativeStateC"
            "odecVectors.raw3 {NativeWalVectors.entry3 with record := []} ="
            " none :="
        ),
        "  replayRejectChanged nativeBytesExecuted (Or.inr (Or.inr (by decide)))",
        (
            "theorem voteIsNotTransition : replayEntry sha NativeStateCodec"
            "Vectors.raw3 NativeWalVectors.entry2 = none := by simp [replay"
            "Entry,NativeWalVectors.entry2]"
        ),
        (
            "theorem missingDigestRejects : build (fun _ => []) s0 c0 n0 = "
            "none := by simp [build,contentId]"
        ),
        "theorem allSevenRegistered : actions.map actionName = (["
        + ",".join("ascii " + json.dumps(n) for n in NAMES)
        + "] : List Bytes) := rfl",
    ]
    return lines


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cross-check", type=Path)
    args = parser.parse_args()
    if args.cross_check:
        cross_check(args.cross_check)
    generate()
    print("native transition vectors generated", len(cases()))


if __name__ == "__main__":
    main()
