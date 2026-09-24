"""Emit a finite, byte-exact Lean graph witness from the pinned synthetic fixture.

The decoder/hash lookup table is a finite example, NOT a verified ASCII parser
or a Lean SHA256 implementation. Every native payload field must be mapped.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/proposals"))
import native_binding as native  # noqa: E402

SOURCE = ROOT / "formal/fixtures/traces/native/normal-apply.json"
TARGET = ROOT / "formal/proofs/DeltaReduce/NativeGraphVectors.lean"
KINDS = dict(
    zip(
        (
            "AUTHORITY SCHEMA PROFILE PLAN MODEL OPTIMIZER ISC_PROJECTION "
            "EC_PROJECTION APC_PROJECTION Q_SHARD AGGREGATE_PROJECTION"
        ).split(),
        "authority schema profile plan model optimizer isc ec apc qShard aggregate".split(),
        strict=True,
    )
)


def string(value):
    return json.dumps(value, ensure_ascii=True)


def content_id(value):
    assert value.startswith("sha256:") and len(value) == 71
    return "[" + ",".join(str(b) for b in bytes.fromhex(value[7:])) + "]"


def array(values, convert=str):
    return "[" + ", ".join(convert(value) for value in values) + "]"


def record(value, cls, fields):
    assert set(value) == set(fields), (cls, set(value) ^ set(fields))
    return (
        "({ "
        + ", ".join(name + " := " + convert(value[key]) for key, (name, convert) in fields.items())
        + " } : "
        + cls
        + ")"
    )


def generate(source=SOURCE, target=TARGET):
    bundle = native.decode(source.read_bytes())
    store = {key: raw.encode("ascii") for key, raw in bundle["artifacts"].items()}
    for key, raw in store.items():
        native.require(native.digest(raw) == key, "NATIVE_ARTIFACT_ID")
    artifacts = {key: native.decode(raw) for key, raw in store.items()}
    snapshot = next(v for v in bundle["snapshots"].values() if v["action_id"] == "ACT-APPLY-VOTE")
    native.Witness(native.NativeAnchor(**snapshot["anchor"]), snapshot["authority"], store)
    names = {key: "a" + str(index) for index, key in enumerate(sorted(artifacts))}
    refs = {
        key: {
            "id": key,
            "kind": item["kind"],
            "length": len(bundle["artifacts"][key].encode("ascii")),
        }
        for key, item in artifacts.items()
    }

    def ref(value):
        native.require(value["id"] in refs, "ARTIFACT_MISSING")
        assert value == refs[value["id"]]
        return names[value["id"]] + "Ref"

    def rational(value):
        assert type(value) is list and len(value) == 2
        return (
            "({ numerator := "
            + str(value[0])
            + ", denominator := "
            + str(value[1])
            + " } : Rational)"
        )

    def fields(cls, mapping):
        return lambda value: record(value, cls, mapping)

    context = fields(
        "Context",
        {
            key: (name, convert)
            for key, name, convert in (
                ("round", "round", string),
                ("height", "height", str),
                ("view", "view", str),
                ("epoch", "epoch", string),
                ("hard_deadline", "hardDeadline", str),
                ("parent_checkpoint", "parentCheckpoint", string),
            )
        },
    )
    contribution = fields(
        "Contribution",
        {"ticket": ("ticket", string), "weight": ("weight", rational), "q": ("q", ref)},
    )
    assignment = fields(
        "Assignment",
        {
            "domain": ("domain", string),
            "shard": ("shard", string),
            "context": ("context", string),
            "denominator": ("denominator", str),
            "quantum": ("quantum", rational),
            "contributions": ("contributions", lambda xs: array(xs, contribution)),
        },
    )
    leaf = fields("Leaf", {"shard": ("shard", string), "q": ("q", ref)})
    commitment = fields(
        "Commitment",
        {
            "ticket": ("ticket", string),
            "domain": ("domain", string),
            "leaves": ("leaves", lambda xs: array(xs, leaf)),
        },
    )
    state = fields(
        "StateVector",
        {"schema": ("schema", ref), "quantum": ("quantum", rational), "values": ("values", array)},
    )
    body = fields(
        "ParameterBody",
        {
            "kind": ("kind", string),
            "authority_id": ("authorityId", content_id),
            "context": ("context", string),
            "domain": ("domain", string),
            "shard": ("shard", string),
            "denominator": ("denominator", str),
            "numerators": ("numerators", array),
            "input_leaf_ids": ("inputLeafIds", lambda xs: array(xs, content_id)),
        },
    )

    def payload(item):
        kind, value = item["kind"], item["payload"]
        if kind == "AUTHORITY":
            assert set(value) == set("context schema profile plan model optimizer parents".split())
            assert set(value["parents"]) == {"isc", "ec", "apc"}
            flat = {**{k: v for k, v in value.items() if k != "parents"}, **value["parents"]}
            return ".authority " + record(
                flat,
                "Authority",
                {
                    "context": ("context", context),
                    **{
                        k: (k, ref)
                        for k in "schema profile plan model optimizer isc ec apc".split()
                    },
                },
            )
        if kind == "SCHEMA":
            assert set(value) == {"coordinates", "shards"}
            shard = fields(
                "Shard",
                {"id": ("id", string), "offset": ("offset", str), "length": ("length", str)},
            )
            return (
                ".schema "
                + array(value["coordinates"], string)
                + " "
                + array(value["shards"], shard)
            )
        if kind == "PROFILE":
            weight = fields(
                "DomainWeight", {"domain": ("domain", string), "weight": ("weight", rational)}
            )
            return ".profile " + record(
                value,
                "Profile",
                {
                    "accumulator_bits": ("accumulatorBits", str),
                    "apply_quantum": ("applyQuantum", rational),
                    "domain_weights": ("domainWeights", lambda xs: array(xs, weight)),
                    "learning_rate": ("learningRate", rational),
                    "momentum": ("momentum", rational),
                    "weight_decay": ("weightDecay", rational),
                    "rounding": ("rounding", string),
                    "nesterov": ("nesterov", lambda v: "true" if v is True else "false"),
                    "output_range": ("outputRange", string),
                },
            )
        if kind == "PLAN":
            ticket = fields("Ticket", {"id": ("id", string), "domain": ("domain", string)})
            return ".plan " + record(
                value,
                "Plan",
                {
                    "schema": ("schema", ref),
                    "profile": ("profile", ref),
                    "tickets": ("tickets", lambda xs: array(xs, ticket)),
                    "assignments": ("assignments", lambda xs: array(xs, assignment)),
                },
            )
        if kind in {"MODEL", "OPTIMIZER"}:
            return "." + KINDS[kind] + " " + state(value)
        if kind == "ISC_PROJECTION":
            assert set(value) == {"members", "commitments"}
            return (
                ".isc "
                + array(value["members"], string)
                + " "
                + array(value["commitments"], commitment)
            )
        if kind == "EC_PROJECTION":
            assert set(value) == {"isc", "eligible"}
            return ".ec " + ref(value["isc"]) + " " + array(value["eligible"], string)
        if kind == "APC_PROJECTION":
            assert set(value) == {"ec", "plan"}
            return ".apc " + ref(value["ec"]) + " " + ref(value["plan"])
        if kind == "Q_SHARD":
            return ".qShard " + record(
                value,
                "QShard",
                {
                    "ticket": ("ticket", string),
                    "domain": ("domain", string),
                    "shard": ("shard", string),
                    "schema": ("schema", ref),
                    "quantum": ("quantum", rational),
                    "values": ("values", array),
                },
            )
        assert kind == "AGGREGATE_PROJECTION" and set(value) == {"authority_id", "parameters"}
        return (
            ".aggregate "
            + content_id(value["authority_id"])
            + " "
            + array(value["parameters"], body)
        )

    def children(item):
        value, kind = item["payload"], item["kind"]
        if kind == "AUTHORITY":
            return [value[k] for k in "schema profile plan model optimizer".split()] + [
                value["parents"][k] for k in ("isc", "ec", "apc")
            ]
        if kind == "PLAN":
            return [value["schema"], value["profile"]] + [
                c["q"] for a in value["assignments"] for c in a["contributions"]
            ]
        if kind in {"MODEL", "OPTIMIZER", "Q_SHARD"}:
            return [value["schema"]]
        if kind == "ISC_PROJECTION":
            return [leaf["q"] for c in value["commitments"] for leaf in c["leaves"]]
        if kind == "EC_PROJECTION":
            return [value["isc"]]
        if kind == "APC_PROJECTION":
            return [value["ec"], value["plan"]]
        return []

    lines = [
        "-- Generated by formal/scripts/generate_native_graph_vectors.py; DO NOT EDIT.",
        "-- Finite byte/decoder lookup example, not a general parser or SHA-256 proof.",
        "import DeltaReduce.ArithmeticBinding",
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 8000000",
        "namespace DeltaReduce.NativeGraphVectors",
        "open NativeBinding",
        "",
    ]
    for key, name in names.items():
        value = refs[key]
        lines.append(
            f"def {name}Ref : Ref := ⟨{content_id(key)}, "
            f".{KINDS[value['kind']]}, {value['length']}⟩"
        )
    for key, name in names.items():
        lines += [
            f"def {name}Bytes : Bytes := {array(bundle['artifacts'][key].encode('ascii'))}",
            f"def {name}Payload : Payload := {payload(artifacts[key])}",
        ]
    lines += [
        "def entries : List (Ref × Bytes × Payload) := ["  # noqa: RUF001 (Lean product)
        + ", ".join(f"({name}Ref, {name}Bytes, {name}Payload)" for name in names.values())
        + "]",
        "def store (id : ContentId) : Option Bytes := "
        "(entries.find? (fun e => e.1.id == id)).map (fun e => e.2.1)",
    ]
    authority = artifacts[snapshot["authority"]["id"]]["payload"]
    model = artifacts[authority["model"]["id"]]["payload"]["values"]
    optimizer = artifacts[authority["optimizer"]["id"]]["payload"]["values"]
    lines += [
        "def codec : Codec := {",
        "  hash := fun bytes => "
        "((entries.find? (fun e => e.2.1 == bytes)).map (fun e => e.1.id)).getD []",
        "  canonical := fun bytes => entries.any (fun e => e.2.1 == bytes)",
        "  decode := fun bytes => (entries.find? (fun e => e.2.1 == bytes)).map (fun e => e.2.2)",
        f"  valueHash := fun kind values => if kind == .model && values == {array(model)} "
        f"then {content_id(snapshot['anchor']['current_model_hash'])}",
        f"    else if kind == .optimizer && values == {array(optimizer)} "
        f"then {content_id(snapshot['anchor']['current_optimizer_hash'])} else []",
        "}",
    ]
    lines += [
        "theorem canonicalMember {bytes : Bytes} (h : codec.canonical bytes = true) :",
        "    bytes ∈ entries.map (fun e => e.2.1) := by",
        "  change entries.any (fun e => e.2.1 == bytes) = true at h",
        "  obtain ⟨e, member, equal⟩ := List.any_eq_true.mp h",
        "  have sameBytes : e.2.1 = bytes := by simpa using equal",
        "  exact sameBytes ▸ List.mem_map_of_mem (f := fun e => e.2.1) member",
        "-- Only the twelve accepted byte strings, not SHA-256 over arbitrary inputs.",
        "theorem fixtureCollisionFree : CollisionFree codec := by",
        "  have finite : ∀ a ∈ entries.map (fun e => e.2.1),",
        "      ∀ b ∈ entries.map (fun e => e.2.1), codec.hash a = codec.hash b → a = b := by",
        "    decide",
        "  intro a b acceptedA acceptedB sameHash",
        "  exact finite a (canonicalMember acceptedA) b (canonicalMember acceptedB) sameHash",
    ]
    for name in names.values():
        lines += [
            f"theorem {name}Resolved : Resolves codec store "
            f"{name}Ref {name}Bytes {name}Payload := by",
            "  constructor <;> decide",
        ]
    completed = set()
    while len(completed) < len(names):
        ready = [
            key
            for key in names
            if key not in completed and all(c["id"] in completed for c in children(artifacts[key]))
        ]
        assert ready, "cyclic or missing graph dependency"
        for key in ready:
            name = names[key]
            child_refs = children(artifacts[key])
            lines += [
                f"theorem {name}Complete : Complete codec store {name}Ref := by",
                f"  apply Complete.node {name}Resolved",
                "  intro index child edge",
                "  have member := List.mem_of_getElem? edge",
                f"  change child ∈ {array(child_refs, ref)} at member",
            ]
            if child_refs:
                lines.append("  simp only [List.mem_cons, List.not_mem_nil, or_false] at member")
                lines.append("  rcases member with " + " | ".join("h" for _ in child_refs))
                for child in child_refs:
                    lines += ["  · subst child", f"    exact {names[child['id']]}Complete"]
            else:
                lines += ["  exact False.elim (List.not_mem_nil member)"]
            completed.add(key)
    authority_name = names[snapshot["authority"]["id"]]
    aggregate_name = names[snapshot["anchor"]["aggregate_id"]]
    model_name = names[authority["model"]["id"]]
    optimizer_name = names[authority["optimizer"]["id"]]
    profile_name = names[authority["profile"]["id"]]
    plan_name = names[authority["plan"]["id"]]
    plan = artifacts[authority["plan"]["id"]]["payload"]
    q_names = [names[c["q"]["id"]] for a in plan["assignments"] for c in a["contributions"]]
    missing_q, substitute_q = q_names[:2]
    lines += [
        "-- Synthetic trust witnesses only; no native provenance or signature verification.",
        "def syntheticTrust : Trust := ⟨fun _ => True, fun _ => True, fun _ => True⟩",
        "def anchor : Anchor := {",
        f"  authority := {authority_name}Ref",
        f"  context := {context(authority['context'])}",
        f"  currentModelHash := {content_id(snapshot['anchor']['current_model_hash'])}",
        f"  currentOptimizerHash := {content_id(snapshot['anchor']['current_optimizer_hash'])}",
        f"  aggregate := some {aggregate_name}Ref",
        "}",
        "def fixtureBinding : Binding codec syntheticTrust anchor store := {",
        "  authenticatedAnchor := True.intro",
        "  authenticatedRecovery := True.intro",
        "  complete := by",
        "    intro r member",
        f"    change r ∈ [{authority_name}Ref, {aggregate_name}Ref] at member",
        "    simp only [List.mem_cons, List.not_mem_nil, or_false] at member",
        "    rcases member with h | h",
        f"    · subst r; exact {authority_name}Complete",
        f"    · subst r; exact {aggregate_name}Complete",
        f"  authorityBytes := {authority_name}Bytes",
        "  authority := "
        + payload(artifacts[snapshot["authority"]["id"]]).removeprefix(".authority "),
        f"  authorityResolved := {authority_name}Resolved",
        "  contextMatches := by decide",
        "  iscAuthenticated := True.intro",
        "  ecAuthenticated := True.intro",
        "  apcAuthenticated := True.intro",
        f"  modelBytes := {model_name}Bytes",
        f"  model := {state(artifacts[authority['model']['id']]['payload'])}",
        f"  modelWalk := .step {authority_name}Resolved (by decide) (.here {model_name}Resolved)",
        "  modelSchema := by decide",
        "  modelCurrent := by decide",
        f"  optimizerBytes := {optimizer_name}Bytes",
        f"  optimizer := {state(artifacts[authority['optimizer']['id']]['payload'])}",
        f"  optimizerWalk := .step {authority_name}Resolved (by decide) "
        f"(.here {optimizer_name}Resolved)",
        "  optimizerSchema := by decide",
        "  optimizerCurrent := by decide",
        f"  profileBytes := {profile_name}Bytes",
        f"  profile := {payload(artifacts[authority['profile']['id']]).removeprefix('.profile ')}",
        f"  profileWalk := .step {authority_name}Resolved (by decide) "
        f"(.here {profile_name}Resolved)",
        "  modelQuantum := by decide",
        "  optimizerQuantum := by decide",
        "  aggregateBound := by",
        "    intro r h",
        f"    have eq : {aggregate_name}Ref = r := Option.some.inj h",
        "    subst r",
        f"    exact ⟨True.intro, {aggregate_name}Bytes, _, {aggregate_name}Resolved⟩",
        "}",
        "theorem fixtureBindingExists : Nonempty (Binding codec syntheticTrust anchor store) "
        ":= ⟨fixtureBinding⟩",
        "theorem fixturePremises : CollisionFree codec ∧ "
        "Nonempty (Binding codec syntheticTrust anchor store) :=",
        "  ⟨fixtureCollisionFree, fixtureBindingExists⟩",
        "def missingStore (id : ContentId) : Option Bytes := "
        f"if id = {missing_q}Ref.id then none else store id",
        "theorem missingQRejected (bytes payload) : "
        f"¬ Resolves codec missingStore {missing_q}Ref bytes payload := by",
        "  intro resolved",
        "  have present := resolved.present",
        "  simp [missingStore] at present",
        "theorem incompleteAuthorityRejected : "
        f"¬ Complete codec missingStore {authority_name}Ref := by",
        "  intro complete",
        "  cases complete with",
        "  | node resolved children =>",
        f"    have eq := resolvedAtPresentBytes (knownBytes := {authority_name}Bytes) "
        f"(knownPayload := {authority_name}Payload) (by decide) (by decide) resolved",
        "    rcases eq with ⟨rfl, rfl⟩",
        f"    have plan := children 2 {plan_name}Ref (by decide)",
        "    cases plan with",
        "    | node planResolved planChildren =>",
        f"      have eq := resolvedAtPresentBytes (knownBytes := {plan_name}Bytes) "
        f"(knownPayload := {plan_name}Payload) (by decide) (by decide) planResolved",
        "      rcases eq with ⟨rfl, rfl⟩",
        f"      have q := planChildren 2 {missing_q}Ref (by decide)",
        "      cases q with",
        "      | node qResolved _ => exact missingQRejected _ _ qResolved",
        f"def wrongKind : Ref := {{ {authority_name}Ref with kind := .model }}",
        "theorem wrongKindRejected (bytes payload) : "
        "¬ Resolves codec store wrongKind bytes payload := by",
        "  intro resolved",
        f"  have eq := resolvedAtPresentBytes (knownBytes := {authority_name}Bytes) "
        f"(knownPayload := {authority_name}Payload) (by decide) (by decide) resolved",
        "  rcases eq with ⟨rfl, rfl⟩",
        f"  have mismatch : {authority_name}Payload.kind ≠ wrongKind.kind := by decide",
        "  exact mismatch resolved.kind",
        "def substitutedStore (id : ContentId) : Option Bytes := "
        f"if id = {missing_q}Ref.id then some {substitute_q}Bytes else store id",
        "theorem substitutedQRejected (bytes payload) : "
        f"¬ Resolves codec substitutedStore {missing_q}Ref bytes payload := by",
        "  intro resolved",
        f"  have eq := resolvedAtPresentBytes (knownBytes := {substitute_q}Bytes) "
        f"(knownPayload := {substitute_q}Payload) (by decide) (by decide) resolved",
        "  rcases eq with ⟨rfl, rfl⟩",
        f"  have mismatch : codec.hash {substitute_q}Bytes ≠ {missing_q}Ref.id := by decide",
        "  exact mismatch resolved.content",
    ]
    target.write_text(
        "\n".join([*lines, "end DeltaReduce.NativeGraphVectors", ""]),
        encoding="utf-8",
        newline="\n",
    )
    print(f"generated {len(names)} exact-byte typed graph nodes")


if __name__ == "__main__":
    generate()
