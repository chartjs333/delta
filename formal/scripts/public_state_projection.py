"""Complete candidate state identities and production-TLA replay, not native refinement."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from formal_artifacts import (
    canonical_json_bytes,
    derive_formal_semantics_id,
    discover_semantic_artifacts,
    load_json_strict,
    semantic_text_sha256,
    sha256_file,
)

ROOT = Path(__file__).resolve().parents[2]
PROFILE = "deltareduce.full-public-state.v1-candidate"
CONFIG = ROOT / "formal/proposals/public-state-replay.cfg"
MODULES = (
    "DeltaReduce",
    "DeltaReduceArithmetic",
    "DeltaReduceTypes",
    "DeltaReduceQuorums",
    "DeltaReduceTickets",
    "DeltaReduceAvailability",
    "DeltaReduceCertificates",
    "DeltaReduceReduceApply",
    "DeltaReduceFailures",
    "DeltaReducePublicState",
)
MODEL_VALUES = frozenset(
    "v1 v2 v3 v4 h1 epoch1 configA configB w1 t1 d1 data1 parent1 schema1 profile1 "
    "s1 shard1 content1 seed1 norm1 coeff1 apply1 next1 model1 optimizer1".split()
)
ACTIONS = frozenset(
    (
        "ProposeRoundConfigAction",
        "PersistConfigVoteAction",
        "SendVoteEnvelopeAction",
        "DeliverVoteEnvelopeAction",
        "FinalizeRoundConfigAction",
        "CrashAfterPersistAction",
        "RestartAction",
        "RecoverJournalAction",
        "STUTTER",
    )
)
MAX_BYTES = 4 * 1024 * 1024
MAX_ITEMS = 100_000
MAX_DEPTH = 64


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def inventory(root: Path = ROOT) -> tuple[str, ...]:
    types = (root / "formal/tla/DeltaReduceTypes.tla").read_text(encoding="utf-8")
    types = re.sub(r"\\\*[^\n]*", "", types)
    declared = re.search(r"VARIABLES\s+(.*?)\n\s*\w+\s*==", types, re.S)
    grouped = re.search(r"ProtocolVariables ==\s*<<(.*?)>>", types, re.S)
    require(declared is not None and grouped is not None, "MODEL_INVENTORY")
    declarations = re.findall(r"\b[a-z]\w*\b", declared[1])
    names = re.findall(r"\b[a-z]\w*\b", grouped[1])
    projection = (root / "formal/tla/DeltaReducePublicState.tla").read_text(encoding="utf-8")
    fields = re.findall(r'"([a-z]\w*)"', projection.split("ProjectedPublicState ==")[0])
    pairs = re.findall(r"(\w+)\s*\|->\s*(\w+)", projection)
    matches = re.findall(r"/\\ (\w+) = state\.(\w+)", projection)
    require(len(names) == len(set(names)) == 64, "PROFILE_REVIEW_REQUIRED")
    require(sorted(declarations) == sorted(names) == sorted(fields), "INCOMPLETE_PROJECTION")
    expected = sorted((name, name) for name in names)
    require(sorted(pairs) == expected == sorted(matches), "PROJECTION_VARIABLE_SUBSTITUTION")
    return tuple(sorted(names))


def model_identity() -> dict[str, Any]:
    registry = load_json_strict(ROOT / "formal/reports/formal-id-registry.json")
    return {
        "formal_semantics_id": derive_formal_semantics_id(
            registry["formal_semantics_version"], discover_semantic_artifacts(ROOT)
        ),
        "configuration_sha256": sha256_file(CONFIG),
        "modules": {
            name: semantic_text_sha256(ROOT / f"formal/tla/{name}.tla") for name in MODULES
        },
    }


def canonical_value(value: Any, depth: int = 0, budget: list[int] | None = None) -> Any:
    """Reject aliases instead of silently normalizing an untrusted preimage."""
    if budget is None:
        budget = [MAX_ITEMS]
    budget[0] -= 1
    require(depth <= MAX_DEPTH and budget[0] >= 0, "VALUE_LIMIT")
    require(type(value) is list and len(value) == 2, "TAGGED_VALUE")
    tag, content = value
    require(type(tag) is str, "VALUE_TAG")
    if tag == "bool":
        require(type(content) is bool, "BOOLEAN")
    elif tag == "int":
        require(
            type(content) is str and re.fullmatch(r"0|-?[1-9][0-9]*", content) is not None,
            "INTEGER",
        )
    elif tag == "str":
        require(
            type(content) is str and all(32 <= ord(c) <= 126 for c in content), "STRING_PROFILE"
        )
    elif tag == "model":
        require(type(content) is str and content in MODEL_VALUES, "MODEL_VALUE")
    elif tag in {"set", "fun"}:
        require(type(content) is list and len(content) <= MAX_ITEMS, "COLLECTION")
        keys = []
        for item in content:
            if tag == "fun":
                require(type(item) is list and len(item) == 2, "FUNCTION_PAIR")
                key, result = item
                canonical_value(result, depth + 1, budget)
            else:
                key = item
            canonical_value(key, depth + 1, budget)
            keys.append(canonical_json_bytes(key))
        require(keys == sorted(set(keys)), "DUPLICATE_OR_UNORDERED")
    else:
        raise ValueError("UNSUPPORTED_VALUE")
    return value


def state_preimage(document: dict[str, Any], identity: dict[str, Any] | None = None) -> bytes:
    require(
        type(document) is dict and set(document) == {"profile", "model", "variables"},
        "STATE_FIELDS",
    )
    require(document["profile"] == PROFILE, "STATE_PROFILE")
    require(
        document["model"] == (model_identity() if identity is None else identity), "MODEL_IDENTITY"
    )
    values = document["variables"]
    require(type(values) is dict and set(values) == set(inventory()), "STATE_COMPLETENESS")
    budget = [MAX_ITEMS]
    for value in values.values():
        canonical_value(value, budget=budget)
    encoded = canonical_json_bytes(document)
    require(len(encoded) <= MAX_BYTES, "STATE_BYTE_LIMIT")
    return PROFILE.encode("ascii") + b"\0" + encoded


def state_root(document: dict[str, Any], identity: dict[str, Any] | None = None) -> str:
    return "sha256:" + hashlib.sha256(state_preimage(document, identity)).hexdigest()


def check_observation(observation: Any, identity: dict[str, Any]) -> dict[str, Any]:
    require(
        type(observation) is dict and set(observation) == {"state", "root"}, "OBSERVATION_FIELDS"
    )
    require(observation["root"] == state_root(observation["state"], identity), "STATE_ROOT")
    return observation["state"]["variables"]


def tla_value(value: Any) -> str:
    canonical_value(value)
    tag, content = value
    if tag == "bool":
        return "TRUE" if content else "FALSE"
    if tag == "int":
        require(-2147483648 <= int(content) <= 2147483647, "TLC_INTEGER_RANGE")
        return content
    if tag == "str":
        return json.dumps(content, ensure_ascii=True)
    if tag == "model":
        return "witnessValue_" + content
    if tag == "set":
        return "{" + ", ".join(tla_value(v) for v in content) + "}"
    if not content:
        return "[key \\in {} |-> 0]"
    # TLC :> and @@ construct general finite functions, including records/sequences.
    return "(" + " @@ ".join(f"({tla_value(k)} :> {tla_value(v)})" for k, v in content) + ")"


def replay_sources(trace: Any) -> tuple[str, str]:
    require(type(trace) is dict and set(trace) == {"profile", "states", "actions"}, "TRACE_FIELDS")
    require(trace["profile"] == PROFILE, "TRACE_PROFILE")
    states, actions = trace["states"], trace["actions"]
    require(type(states) is list and 1 <= len(states) <= 64, "TRACE_SIZE")
    require(type(actions) is list and len(actions) == len(states) - 1, "ACTION_COUNT")
    require(all(type(a) is str and a in ACTIONS for a in actions), "ACTION_VOCABULARY")
    identity = model_identity()
    checked = [check_observation(s, identity) for s in states]
    records = [
        "[" + ",\n".join(f"{name} |-> {tla_value(s[name])}" for name in inventory()) + "]"
        for s in checked
    ]
    selected = [
        f"witnessIndex = {i} -> " + ("UNCHANGED ProtocolVariables" if a == "STUTTER" else a)
        for i, a in enumerate(actions, 1)
    ]
    selected.append("OTHER -> UNCHANGED ProtocolVariables")
    module = (
        "---- MODULE FullStateReplay ----\nEXTENDS DeltaReducePublicState\nCONSTANTS "
        + ", ".join("witnessValue_" + name for name in sorted(MODEL_VALUES))
        + "\nVARIABLE witnessIndex\nReplayStates == <<\n"
        + ",\n".join(records)
        + ">>\n"
        "WitnessInit == witnessIndex = 1 /\\ MatchesPublicState(ReplayStates[1])\n"
        "WitnessNext == /\\ witnessIndex < Len(ReplayStates)\n"
        "               /\\ witnessIndex' = witnessIndex + 1\n"
        + "".join(
            f"               /\\ {name}' = ReplayStates[witnessIndex + 1].{name}\n"
            for name in inventory()
        )
        + "WitnessInitialOK == witnessIndex # 1 \\/ Init\n"
        "WitnessTypes == TypeOK\n"
        "WitnessAllowed == [][Next]_ProtocolVariables\n"
        "WitnessSelected == CASE " + "\n [] ".join(selected) + "\n"
        "WitnessLabelled == [][WitnessSelected]_<<ProtocolVariables, witnessIndex>>\n====\n"
    )
    # This registered config is reviewed source, not supplied executable TLA.
    cfg = CONFIG.read_text(encoding="utf-8")
    require(cfg.startswith("CONSTANTS\n"), "CONFIG_PROFILE")
    require(
        not re.search(
            r"^(SPECIFICATION|INIT|NEXT|SYMMETRY|CONSTRAINT|VIEW|INVARIANT|PROPERTY)\b", cfg, re.M
        ),
        "CONFIG_OVERRIDE",
    )
    cfg += "\n" + "\n".join(f"    witnessValue_{name} = {name}" for name in sorted(MODEL_VALUES))
    cfg += (
        "\nINIT WitnessInit\nNEXT WitnessNext\n"
        "INVARIANTS WitnessInitialOK WitnessTypes\n"
        "PROPERTIES WitnessAllowed WitnessLabelled\nCHECK_DEADLOCK FALSE\n"
    )
    return module, cfg
