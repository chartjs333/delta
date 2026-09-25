"""Full typed state/first-vote vectors; no native authentication or Next proof."""

import copy
import hashlib
import json
from pathlib import Path

from formal_artifacts import (
    canonical_json_bytes,
    load_json_strict,
    sha256_file,
    write_canonical_json,
)
from generate_native_vote_vectors import content_id
from public_native_projection import PinnedFixtureSources
from public_state_projection import MODEL_VALUES, PROFILE, inventory, require
from public_state_storage import unpack

ROOT = Path(__file__).resolve().parents[2]
VECTORS = ROOT / "formal/proposals/public-arithmetic-vectors.json"
TARGET = ROOT / "formal/proofs/DeltaReduce/PublicStateVectors.lean"
VALUES_TARGET = TARGET.with_name("PublicStateValues.lean")
DOCUMENTS_TARGET = TARGET.with_name("PublicStateDocuments.lean")
LOADS_TARGET = TARGET.with_name("PublicStateLoads.lean")
EVIDENCE = ROOT / "formal/proposals/public-state-lean-vectors.json"


def quoted(value):
    return json.dumps(value, ensure_ascii=True)


def header_proofs(identity):
    """Compose small literal identity equations; never flatten a long proof goal."""
    lines, module_atoms, module_proofs = [], [], []
    for index, (name, digest) in enumerate(sorted(identity["modules"].items())):
        literal = quoted(name) + ":" + quoted(digest)
        atom = "asciiBytes " + quoted(literal)
        module_atoms.append(atom)
        proof = f"headerModule{index}"
        module_proofs.append(proof)
        lines.append(
            f"theorem {proof} : quoted {quoted(name)} ++ [58] ++ "
            f"quotedBytes ((idBytes {content_id('sha256:' + digest)}).drop 7) = "
            f"{atom} := by decide +kernel"
        )

    def object_proof(name, left, atoms, proofs):
        raw = f"raw{name}"
        lines.append(
            f"def {raw} : Bytes := [123] ++ List.intercalate [44] ["
            + ",".join(atoms)
            + "] ++ [125]"
        )
        pieces = "(Eq.refl ([] : List Bytes))"
        for proof in reversed(proofs):
            pieces = f"(congrPair List.cons {proof} {pieces})"
        lines.extend(
            [
                f"theorem {name} : {left} = {raw} := by",
                "  have parts := " + pieces,
                "  have assembled := congrArg (fun chunks : List Bytes => "
                "[123] ++ List.intercalate [44] chunks ++ [125]) parts",
                "  exact assembled",
            ]
        )
        return raw

    raw_modules = object_proof(
        "headerModules",
        "object (identity.modules.map (fun (name,hash) => "
        "(name,quotedBytes ((idBytes hash).drop 7))))",
        module_atoms,
        module_proofs,
    )
    cfg = "asciiBytes " + quoted(
        '"configuration_sha256":' + quoted(identity["configuration_sha256"])
    )
    sem = "asciiBytes " + quoted('"formal_semantics_id":' + quoted(identity["formal_semantics_id"]))
    mod = f'(asciiBytes "\\"modules\\":" ++ {raw_modules})'
    lines.extend(
        [
            'theorem headerConfig : quoted "configuration_sha256" ++ [58] ++ '
            f"quotedBytes ((idBytes identity.configuration).drop 7) = {cfg} := by decide +kernel",
            'theorem headerSemantics : quoted "formal_semantics_id" ++ [58] ++ '
            f"quotedBytes (idBytes identity.semantics) = {sem} := by decide +kernel",
            'theorem headerModuleKey : quoted "modules" ++ [58] = '
            'asciiBytes "\\"modules\\":" := by decide +kernel',
            'theorem headerModuleField : quoted "modules" ++ [58] ++ '
            "object (identity.modules.map (fun (name,hash) => "
            f"(name,quotedBytes ((idBytes hash).drop 7)))) = {mod} := by",
            "  have assembled := congrPair List.append headerModuleKey headerModules",
            "  exact assembled",
        ]
    )
    raw_identity = object_proof(
        "headerIdentity",
        "identityBytes identity",
        [cfg, sem, mod],
        ["headerConfig", "headerSemantics", "headerModuleField"],
    )
    lines.extend(
        [
            f"theorem headerProfile : quoted profile = asciiBytes {quoted(quoted(PROFILE))} "
            ":= by decide +kernel",
            f'def rawHeader : Bytes := asciiBytes "{{\\"model\\":" ++ {raw_identity} ++ '
            f'asciiBytes ",\\"profile\\":" ++ asciiBytes {quoted(quoted(PROFILE))} ++ '
            'asciiBytes ",\\"variables\\":"',
            "theorem headerExact : documentHeader identity = rawHeader := by",
            "  simp only [documentHeader,rawHeader,headerIdentity,headerProfile]",
        ]
    )
    expected_prefix = (
        '{"model":'
        + canonical_json_bytes(identity).decode("ascii")
        + ',"profile":'
        + quoted(PROFILE)
        + ',"variables":'
    )
    lines.append(
        f"theorem headerLength : rawHeader.length = {len(expected_prefix)} := by decide +kernel"
    )
    return lines


def literal_length(code, size):
    return f"(show ({code} : Bytes).length = {size} from by decide +kernel)"


def append_lengths(proofs):
    result = proofs[0]
    for proof in proofs[1:]:
        result = f"(byteAppendLength {result} {proof})"
    return result


def comma_lengths(proofs):
    if not proofs:
        return "(show (List.intercalate [44] ([] : List Bytes)).length = 0 from rfl)"
    result = f"(commaSingletonLength {proofs[-1]})"
    for proof in reversed(proofs[:-1]):
        result = f"(commaConsLength {proof} {result})"
    return result


def generate(target=TARGET, evidence=EVIDENCE, vectors=VECTORS):
    sources = PinnedFixtureSources()
    document = load_json_strict(vectors)
    trace = unpack(document["positive"])
    mapped = [
        e
        for e in document["legacy_correspondence"]
        if e["action_id"] in {"ACT-PARAM-VOTE", "ACT-APPLY-VOTE"}
    ]
    require(len(mapped) == 9, "LEAN_FIRST_VOTE_COVERAGE")
    # Validate ALL sources before writing either output.
    for entry in mapped:
        before, after = entry["prior_state_index"], entry["next_state_index"]
        require(after == before + 1, "LEAN_FIRST_ADJACENCY")
        sources.bind_first(
            entry["legacy_event_index"],
            trace["states"][before],
            trace["states"][after],
            trace["actions"][before],
        )
    identity = copy.deepcopy(sources.identity)
    # No semantic self-hash cycle: this is an explicitly synthetic encoding test
    # identity. Actual complete variable values/source/config bytes are retained.
    identity["formal_semantics_id"] = "sha256:" + "00" * 32
    lines = [
        "import DeltaReduce.PublicState",
        "import DeltaReduce.NativeVoteVectors",
        "namespace DeltaReduce.PublicStateValues",
        "open NativeBinding PublicState",
        "set_option Elab.async false",
        "set_option maxRecDepth 1000000",
        "set_option maxHeartbeats 0",
        "set_option linter.unusedSimpArgs false",
        "-- Synthetic semantic ID avoids hashing this file into its own literals.",
        "-- Finite SHA samples below are not general SHA or exporter authentication.",
        "def models : List String := [" + ",".join(quoted(x) for x in sorted(MODEL_VALUES)) + "]",
        "def identity : Identity := {",
        "  semantics := List.replicate 32 0",
        "  configuration := " + content_id("sha256:" + identity["configuration_sha256"]),
        "  modules := ["
        + ",".join(
            "(" + quoted(k) + "," + content_id("sha256:" + v) + ")"
            for k, v in sorted(identity["modules"].items())
        )
        + "] }",
    ]
    definitions, names = [], {}
    metrics = {}
    values_by_name, order_proofs = {}, set()

    def prove_order(left, right):
        proof = f"order_{left}_{right}"
        if proof in order_proofs:
            return proof
        order_proofs.add(proof)
        definitions.append(f"theorem {proof} : byteLess raw{left} raw{right} = true := by")
        a, b = values_by_name[left], values_by_name[right]
        require(canonical_json_bytes(a) < canonical_json_bytes(b), "LEAN_VALUE_ORDER")
        while True:
            an, bn = names[canonical_json_bytes(a)], names[canonical_json_bytes(b)]
            definitions.append(
                f"  simp only [raw{an},raw{bn},List.intercalate_cons_cons,"
                "List.intercalate_singleton,List.intercalate_nil,List.append_assoc,"
                "byteLessCommonPrefix]"
            )
            if a[0] != b[0] or a[0] not in {"set", "fun"}:
                break
            ac = a[1] if a[0] == "set" else [v for pair in a[1] for v in pair]
            bc = b[1] if b[0] == "set" else [v for pair in b[1] for v in pair]
            mismatch = next(((x, y) for x, y in zip(ac, bc, strict=False) if x != y), None)
            if mismatch is None:
                break
            a, b = mismatch
        definitions.append("  all_goals decide +kernel")
        return proof

    for index, field in enumerate(inventory()):
        definitions.append(
            f"theorem keyColon{index} : quoted {quoted(field)} ++ [58] = "
            f"asciiBytes {quoted(quoted(field) + ':')} := by decide +kernel"
        )

    def intern(value):
        nonlocal definitions
        key = canonical_json_bytes(value)
        if key in names:
            return names[key]
        tag, data = value
        if tag == "bool":
            expression = ".boolean " + str(data).lower()
        elif tag == "int":
            expression = ".integer (" + data + ")"
        elif tag in {"str", "model"}:
            expression = (".text " if tag == "str" else ".model ") + quoted(data)
        else:
            entries = (
                [intern(x) for x in data]
                if tag == "set"
                else [(intern(k), intern(v)) for k, v in data]
            )
            tail = ".nil"
            for item in reversed(entries):
                pair = item if tag == "set" else item[0] + " " + item[1]
                tail = "(.cons " + pair + " " + tail + ")"
            expression = (".set " if tag == "set" else ".function ") + tail
        name = f"value{len(names)}"
        names[key] = name
        values_by_name[name] = value
        definitions.append(f"def {name} : Value := {expression}")
        if tag in {"set", "fun"}:
            encoded = (
                ["raw" + x for x in entries]
                if tag == "set"
                else ["([91] ++ raw" + k + " ++ [44] ++ raw" + v + " ++ [93])" for k, v in entries]
            )
            raw_expression = (
                "asciiBytes "
                + quoted('["' + tag + '",[')
                + " ++ List.intercalate [44] ["
                + ",".join(encoded)
                + "] ++ [93,93]"
            )
        else:
            raw_expression = "asciiBytes " + quoted(key.decode("ascii"))
        definitions.append(f"def raw{name} : Bytes := {raw_expression}")
        definitions.append(f"theorem encoded_{name} : encode {name} = raw{name} := by")
        if tag in {"set", "fun"}:
            terms = (
                ["encode " + x for x in entries]
                if tag == "set"
                else [
                    "([91] ++ encode " + k + " ++ [44] ++ encode " + v + " ++ [93])"
                    for k, v in entries
                ]
            )
            children = entries if tag == "set" else [x for pair in entries for x in pair]
            definitions.append(
                "  change asciiBytes "
                + quoted('["' + tag + '",[')
                + " ++ List.intercalate [44] ["
                + ",".join(terms)
                + "] ++ [93,93] = _"
            )
            if children:
                definitions.append(
                    "  simp only ["
                    + ",".join("encoded_" + x for x in dict.fromkeys(children))
                    + "]"
                )
        definitions.append("  all_goals rfl")
        if tag in {"set", "fun"}:
            children = entries if tag == "set" else [x for pair in entries for x in pair]
            count = 1 + sum(metrics[x][0] for x in children)
            height = max((1 + metrics[x][1] for x in children), default=0)
            count_expression, depth_expression, canonical_expression = "0", "0", "true"
            for item in reversed(entries):
                if tag == "set":
                    count_expression = f"(nodes {item} + {count_expression})"
                    depth_expression = f"max (1 + depth {item}) ({depth_expression})"
                    canonical_expression = f"(canonical models {item} && {canonical_expression})"
                else:
                    key_name, value_name = item
                    count_expression = (
                        f"(nodes {key_name} + nodes {value_name} + {count_expression})"
                    )
                    depth_expression = (
                        f"max (max (1 + depth {key_name}) (1 + depth {value_name}))"
                        f" ({depth_expression})"
                    )
                    canonical_expression = (
                        f"(canonical models {key_name} && canonical models {value_name}"
                        f" && {canonical_expression})"
                    )
            ordered_names = entries if tag == "set" else [k for k, _ in entries]
            ordering = [
                prove_order(left, right)
                for index, left in enumerate(ordered_names)
                for right in ordered_names[index + 1 :]
            ]
            definitions += [
                f"theorem nodes_{name} : nodes {name} = {count} := by",
                f"  change 1 + {count_expression} = {count}",
                "  simp only [" + ",".join("nodes_" + x for x in dict.fromkeys(children)) + "]",
                "  all_goals decide +kernel",
                f"theorem depth_{name} : depth {name} = {height} := by",
                f"  change {depth_expression} = {height}",
                "  simp only [" + ",".join("depth_" + x for x in dict.fromkeys(children)) + "]",
                "  all_goals decide +kernel",
                f"theorem canonical_{name} : canonical models {name} = true := by",
                f"  change ({canonical_expression} && ordered ["
                + ",".join("encode " + x for x in ordered_names)
                + "]) = true",
                "  simp only ["
                + ",".join(
                    ["canonical_" + x for x in dict.fromkeys(children)]
                    + ["encoded_" + x for x in dict.fromkeys(ordered_names)]
                )
                + "]",
                "  simp only [ordered,List.all_cons,List.all_nil,"
                + ",".join([*ordering, "Bool.true_and"])
                + "]",
                "  all_goals decide +kernel",
            ]
        else:
            count, height = 1, 0
            definitions += [
                f"theorem nodes_{name} : nodes {name} = 1 := by rfl",
                f"theorem depth_{name} : depth {name} = 0 := by rfl",
                f"theorem canonical_{name} : canonical models {name} = true := by decide +kernel",
            ]
        metrics[name] = (count, height)
        definitions.append(f"theorem rawLength_{name} : raw{name}.length = {len(key)} := by")
        if tag in {"set", "fun"}:
            item_lengths = (
                ["rawLength_" + x for x in entries]
                if tag == "set"
                else [
                    append_lengths(
                        [
                            literal_length("[91]", 1),
                            "rawLength_" + k,
                            literal_length("[44]", 1),
                            "rawLength_" + v,
                            literal_length("[93]", 1),
                        ]
                    )
                    for k, v in entries
                ]
            )
            prefix = '["' + tag + '",['
            proof = append_lengths(
                [
                    literal_length("asciiBytes " + quoted(prefix), len(prefix)),
                    comma_lengths(item_lengths),
                    literal_length("[93,93]", 2),
                ]
            )
            definitions += ["  have assembled := " + proof, "  exact assembled"]
        else:
            definitions.append("  decide +kernel")
        return name

    state_lines, state_names, samples, cases, pairs = [], {}, [], {}, []
    byte_proofs = {}
    sample_lengths = {}
    state_rows = {}
    for entry in mapped:
        for position in [entry["prior_state_index"], entry["next_state_index"]]:
            if position in state_names:
                continue
            name = f"state{position}"
            state_names[position] = name
            state = trace["states"][position]["state"]
            rows = [(k, intern(state["variables"][k])) for k in inventory()]
            state_rows[position] = rows
            state_lines.append(
                f"def {name} : State := ⟨["
                + ",".join(f"({quoted(k)}, {v})" for k, v in rows)
                + "], by decide⟩"
            )
            encoded_rows = [
                "(asciiBytes " + quoted(quoted(k) + ":") + " ++ raw" + v + ")" for k, v in rows
            ]
            state_lines.append(
                f"def variables{position} : Bytes := [123] ++ List.intercalate [44] ["
                + ",".join(encoded_rows)
                + "] ++ [125]"
            )
            cases[f"completeVariables{position}"] = f"variableBytes {name} = variables{position}"
            pieces = "(Eq.refl ([] : List Bytes))"
            for index, (_, value) in reversed(list(enumerate(rows))):
                piece = f"(congrPair List.append keyColon{index} encoded_{value})"
                pieces = f"(congrPair List.cons {piece} {pieces})"
            byte_proofs[f"completeVariables{position}"] = (
                "  have pieces := " + pieces + "\n"
                "  have assembled := congrArg (fun chunks : List Bytes => "
                "[123] ++ List.intercalate [44] chunks ++ [125]) pieces\n"
                "  exact assembled"
            )
            synthetic = {**state, "model": identity}
            raw = canonical_json_bytes(synthetic).decode("ascii")
            sample_lengths[position] = len(PROFILE) + 1 + len(raw)
            digest = "sha256:" + hashlib.sha256(PROFILE.encode() + b"\0" + raw.encode()).hexdigest()
            prefix = (
                '{"model":'
                + canonical_json_bytes(identity).decode("ascii")
                + ',"profile":'
                + quoted(PROFILE)
                + ',"variables":'
            )
            require(
                prefix.encode() + canonical_json_bytes(state["variables"]) + b"}" == raw.encode(),
                "PREIMAGE_FRAGMENT_ENCODING",
            )
            state_lines += [
                f"def bytes{position} : Bytes := rawHeader ++ variables{position} ++ [125]",
                f"def root{position} : ContentId := {content_id(digest)}",
                f"def observation{position} : Observation := ⟨profile, identity,"
                f" {name}.rows, bytes{position}, root{position}⟩",
            ]
            variable_length = len(canonical_json_bytes(state["variables"]))
            row_lengths = [
                append_lengths(
                    [
                        literal_length("asciiBytes " + quoted(quoted(k) + ":"), len(quoted(k)) + 1),
                        "rawLength_" + v,
                    ]
                )
                for k, v in rows
            ]
            variables_length_proof = append_lengths(
                [
                    literal_length("[123]", 1),
                    comma_lengths(row_lengths),
                    literal_length("[125]", 1),
                ]
            )
            state_lines += [
                f"theorem variableLength{position} : variables{position}.length = "
                f"{variable_length} := by",
                "  have assembled := " + variables_length_proof,
                "  exact assembled",
                f"theorem documentLength{position} : bytes{position}.length = {len(raw)} := by",
                "  have assembled := "
                + append_lengths(
                    [
                        "headerLength",
                        f"variableLength{position}",
                        literal_length("[125]", 1),
                    ]
                ),
                "  exact assembled",
            ]
            samples.append((position, name))
    message_index, message_observation = next(
        (index, observation)
        for index, observation in enumerate(trace["states"])
        if observation["state"]["variables"]["messages"][1]
    )
    unexpected_messages = message_observation["state"]["variables"]["messages"]
    require(
        unexpected_messages
        != trace["states"][mapped[0]["next_state_index"]]["state"]["variables"]["messages"],
        "LEAN_COUNTERCHECK_MUST_CHANGE_MESSAGES",
    )
    message_value = intern(unexpected_messages)
    state_lines.append(f"def unexpectedMessages : Value := {message_value}")
    value_lines = [*lines, *definitions, "end DeltaReduce.PublicStateValues", ""]
    lines = [
        "import DeltaReduce.PublicStateValues",
        "namespace DeltaReduce.PublicStateDocuments",
        "open NativeBinding PublicState PublicStateValues",
        "set_option Elab.async false",
        "set_option maxRecDepth 1000000",
        "set_option maxHeartbeats 0",
        "set_option linter.unusedSimpArgs false",
        *header_proofs(identity),
        *state_lines,
    ]
    early_cases = set(byte_proofs)
    for name in byte_proofs:
        lines.append(f"theorem {name} : {cases[name]} := by\n" + byte_proofs[name])
    for position, _ in samples:
        lines.append(
            f"theorem encodedDocument{position} : documentBytes identity state{position} "
            f"= bytes{position} := by\n"
            f"  have parts := congrPair List.append headerExact completeVariables{position}\n"
            "  have assembled := congrArg (fun bytes : Bytes => bytes ++ [125]) parts\n"
            "  exact assembled"
        )
    require(len(set(sample_lengths.values())) == len(samples), "FINITE_SAMPLE_LENGTHS_UNIQUE")
    lines += ["def sha256 (bytes : Bytes) : ContentId :="]
    lines += [
        f"  if bytes.length = {sample_lengths[p]} then "
        f"(if bytes = asciiBytes profile ++ [0] ++ bytes{p} then root{p} else []) else"
        for p, _ in samples
    ]
    lines += ["  []"]
    document_lines = [*lines, "end DeltaReduce.PublicStateDocuments", ""]
    lines = [
        "import DeltaReduce.PublicStateDocuments",
        "namespace DeltaReduce.PublicStateLoads",
        "open NativeBinding PublicState PublicStateValues PublicStateDocuments",
        "set_option Elab.async false",
        "set_option maxRecDepth 1000000",
        "set_option maxHeartbeats 0",
        "set_option linter.unusedSimpArgs false",
    ]
    complete_pairs = {}
    for index, entry in enumerate(mapped):
        if sources.trace["events"][entry["legacy_event_index"]]["actor_id"] != "validator-1":
            continue
        before, after = entry["prior_state_index"], entry["next_state_index"]
        complete_pairs[f"first{index}CompleteProjection"] = (before, after)
        for position in [before, after]:
            hash_steps = ["  unfold sha256"]
            for earlier, _ in samples:
                if earlier == position:
                    break
                hash_steps += [
                    f"  have different{earlier} : (asciiBytes profile ++ [0] ++ "
                    f"bytes{position}).length ≠ {sample_lengths[earlier]} := by "
                    f"rw [sampleLength{position}]; decide +kernel",
                    f"  rw [if_neg different{earlier}]",
                ]
            hash_steps += [f"  rw [if_pos sampleLength{position}]", "  exact if_pos rfl"]
            values = [value for _, value in state_rows[position]]
            shape = "true"
            count_expression = "0"
            for value in reversed(values):
                shape = f"((canonical models {value} && decide (depth {value} ≤ 64)) && {shape})"
                count_expression = f"(nodes {value} + {count_expression})"
            lines += [
                f"theorem sampleLength{position} : "
                f"(asciiBytes profile ++ [0] ++ bytes{position}).length = "
                f"{sample_lengths[position]} := by\n"
                "  have assembled := "
                + append_lengths(
                    [
                        literal_length("asciiBytes profile", len(PROFILE)),
                        literal_length("[0]", 1),
                        f"documentLength{position}",
                    ]
                )
                + "\n  exact assembled",
                f"theorem sampleHash{position} : sha256 (preimage identity state{position}) "
                f"= root{position} := by\n  simp only [preimage, encodedDocument{position}]"
                + "\n"
                + "\n".join(hash_steps),
                f"theorem shape{position} : "
                f"(state{position}.rows.all (fun (_,v) => canonical models v && "
                "decide (depth v ≤ 64))) = true := by",
                f"  change {shape} = true",
                "  simp only ["
                + ",".join(
                    ["canonical_" + x for x in dict.fromkeys(values)]
                    + ["depth_" + x for x in dict.fromkeys(values)]
                )
                + "]",
                "  all_goals decide +kernel",
                f"theorem nodeBound{position} : "
                f"(state{position}.rows.map (fun (_,v) => nodes v)).sum ≤ 250000 := by",
                f"  change {count_expression} ≤ 250000",
                "  simp only [" + ",".join("nodes_" + x for x in dict.fromkeys(values)) + "]",
                "  all_goals decide +kernel",
                f"theorem admissible{position} : admissible models identity sha256 "
                f"observation{position} state{position} := by",
                f"  exact ⟨rfl, rfl, by decide +kernel, shape{position}, nodeBound{position},",
                f"    encodedDocument{position}.symm, by change bytes{position}.length ≤ 4194304; "
                f"rw [documentLength{position}]; decide +kernel, "
                f"by decide +kernel, sampleHash{position}⟩",
                f"def loaded{position} : Loaded models identity sha256 observation{position} := "
                f"⟨state{position}, rfl, admissible{position}⟩",
            ]
    load_lines = [*lines, "end DeltaReduce.PublicStateLoads", ""]
    lines = [
        "import DeltaReduce.PublicStateLoads",
        "namespace DeltaReduce.PublicStateVectors",
        "open NativeBinding PublicState PublicStateValues PublicStateDocuments PublicStateLoads",
        "set_option Elab.async false",
        "set_option maxRecDepth 1000000",
        "set_option maxHeartbeats 0",
        "set_option linter.unusedSimpArgs false",
    ]
    for i, entry in enumerate(mapped):
        before, after = entry["prior_state_index"], entry["next_state_index"]
        event = sources.trace["events"][entry["legacy_event_index"]]
        actor = "v" + event["actor_id"].split("-")[-1]
        call = f'extractFirst state{before} state{after} (.model "{actor}")'
        lines.append(f"def first{i} := {call}")
        cases[f"first{i}ExtractsOriginalSequence"] = (
            f"(first{i}.map (fun p => p.next.data.sequence)) = some {event['durable_sequence']}"
        )
        # Three representative entire load/identity/preimage paths (original 5/6/8).
        if actor == "v1":
            cases[f"first{i}CompleteProjection"] = (
                f"((projectFirst models identity sha256 observation{before} observation{after}"
                ' (.model "v1")).isSome) = true'
            )
            cases[f"originalDocument{before}"] = (
                f"documentBytes identity state{before} = bytes{before}"
            )
            pairs.append({"prior": before, "next": after, "sequence": event["durable_sequence"]})
    first_before, first_after = pairs[0]["prior"], pairs[0]["next"]
    lines += [
        f"abbrev initialState := state{first_before}",
        f"abbrev nextState := state{first_after}",
        f"abbrev original := observation{first_before}",
        "def replace (state : State) (name : String) (value : Value) : State :=",
        (
            "  ⟨state.rows.map (fun (k,v) => (k,if k = name then value else "
            "v)), by simpa [List.map_map, Function.comp_def] using "
            "state.complete⟩"
        ),
        (
            "def reencode (state : State) : Observation := { original with "
            "rows := state.rows, bytes := documentBytes identity state, root "
            ":= List.replicate 32 7 }"
        ),
        (
            "-- Deliberately collision-full test adapter: validation failures "
            "must not rely on a stale hash."
        ),
        (
            "def rehashed (state : State) := load models identity (fun _ => "
            "List.replicate 32 7) (reencode state)"
        ),
        "def mapping : IdentityMap := {",
        '  actor := fun v => if v = .model "v1" then some "validator-1" else none',
        (
            '  checkpoint := fun v => if v = .model "parent1" then some '
            "NativeVoteVectors.parameterAnchor.context.parentCheckpoint else "
            "none"
        ),
        (
            '  height := fun v => if v = .model "h1" then some '
            "NativeVoteVectors.parameterAnchor.context.height else none"
        ),
        (
            '  epoch := fun v => if v = .model "epoch1" then some '
            "NativeVoteVectors.parameterAnchor.context.epoch else none }"
        ),
        (
            "def originalNative := first0.map (fun p => (bindNativeFrame "
            "mapping p NativeVoteVectors.parameterAnchor "
            "NativeVoteVectors.metadata0).isSome)"
        ),
    ]
    cases.update(
        {
            "originalNativeFrame": "originalNative = some true",
            "missingActorMapping": (
                "(first0.map (fun p => (bindNativeFrame { mapping with actor := "
                "fun _ => none } p NativeVoteVectors.parameterAnchor "
                "NativeVoteVectors.metadata0).isSome)) = some false"
            ),
            "wrongNativeClock": (
                "(first0.map (fun p => (bindNativeFrame mapping p "
                "NativeVoteVectors.parameterAnchor { NativeVoteVectors.metadata0 "
                "with logicalTime := 0 }).isSome)) = some false"
            ),
            "oldSnapshotProfileRejected": (
                "(load models identity sha256 { original with version := "
                '"deltareduce.native-snapshot-witness.v1" }).isSome = false'
            ),
            "wrongSourceRejected": (
                "(load models identity sha256 { original with identity := { "
                "identity with modules := [] } }).isSome = false"
            ),
            "wrongConfigRejected": (
                "(load models identity sha256 { original with identity := { "
                "identity with configuration := List.replicate 32 3 } }).isSome = "
                "false"
            ),
            "wrongRootRejected": (
                "(load models identity sha256 { original with root := [] }).isSome = false"
            ),
            "wrongBytesRejected": (
                "(load models identity sha256 { original with bytes := [] }).isSome = false"
            ),
            "missingVariableRejected": (
                "(loadRows (initialState.rows.filter (fun row => row.1 != "
                '"messages"))).isSome = false'
            ),
            "duplicateVariableRejected": (
                '(loadRows (("messages", .set .nil) :: initialState.rows)).isSome = false'
            ),
            "reversedVariablesRejected": "(loadRows initialState.rows.reverse).isSome = false",
            "duplicateSetRejected": (
                '(rehashed (replace initialState "alive" (.set (.cons (.model '
                '"v1") (.cons (.model "v1") .nil))))).isSome = false'
            ),
            "unconfiguredModelRejected": (
                '(rehashed (replace initialState "currentCheckpoint" (.model '
                '"alien"))).isSome = false'
            ),
            "nonASCIIRejected": (
                '(rehashed (replace initialState "phase" (.text "é"))).isSome = false'
            ),
            "stringModelDistinct": 'encode (.model "v1") ≠ encode (.text "v1")',
            "setFunctionDistinct": "encode (.set .nil) ≠ encode (.function .nil)",
            "boolIntDistinct": "encode (.boolean true) ≠ encode (.integer 1)",
            "falseSequenceRejected": (
                '(extract (replace initialState "durableSequence" (.function '
                '(.cons (.model "v1") (.integer 0) .nil))) (.model "v1")).isSome '
                "= false"
            ),
            "recoveringRejected": (
                '(extract (replace initialState "recoveryState" (.function (.cons '
                '(.model "v1") (.text "RECOVERING") .nil))) (.model "v1")).isSome '
                "= false"
            ),
            "staleParentRejected": (
                '(extractFirst (replace initialState "currentCheckpoint" (.model '
                '"next1")) nextState (.model "v1")).isSome = false'
            ),
            "noAppendRejected": (
                '(extractFirst initialState initialState (.model "v1")).isSome = false'
            ),
            "wrongActorRejected": (
                '(extractFirst initialState nextState (.model "v2")).isSome = false'
            ),
            "inactiveRejected": (
                '(extract (replace initialState "phase" (.text "ABORTED")) '
                '(.model "v1")).isSome = false'
            ),
            "notAliveRejected": (
                '(extract (replace initialState "alive" (.set .nil)) (.model "v1")).isSome = false'
            ),
            "extractionAloneDoesNotValidateMessages": (
                '(replace nextState "messages" unexpectedMessages).read "messages" ≠ '
                'nextState.read "messages" ∧ (extractFirst initialState (replace '
                'nextState "messages" unexpectedMessages) (.model "v1")).isSome = true'
            ),
        }
    )
    for name, claim in cases.items():
        if name in early_cases:
            continue
        if name in complete_pairs:
            before, after = complete_pairs[name]
            proof = (
                f"\n  simp only [projectFirst, loadProvided loaded{before}, "
                f"loadProvided loaded{after}, Option.bind_some]"
                "\n  decide +kernel"
            )
        elif name.startswith("originalDocument"):
            position = name.removeprefix("originalDocument")
            proof = f" exact encodedDocument{position}"
        elif name == "wrongRootRejected":
            proof = (
                "\n  cases checked : load models identity sha256 "
                "{ original with root := [] } with\n"
                "  | none => rfl\n"
                "  | some loaded =>\n"
                "    have impossible : (0 : Nat) = 32 := "
                "loaded.checked.2.2.2.2.2.2.2.1\n"
                "    cases impossible"
            )
        elif name == "wrongBytesRejected":
            proof = (
                "\n  cases checked : load models identity sha256 "
                "{ original with bytes := [] } with\n"
                "  | none => rfl\n"
                "  | some loaded =>\n"
                "    have empty : ([] : Bytes) = documentBytes identity loaded.state := "
                "loaded.checked.2.2.2.2.2.1\n"
                "    have head : (documentBytes identity loaded.state).head? = some 123 := rfl\n"
                "    rw [← empty] at head\n"
                "    cases head"
            )
        else:
            proof = " decide +kernel"
        lines.append(f"theorem {name} : {claim} := by{proof}")
    lines += ["end DeltaReduce.PublicStateVectors", ""]
    result = {
        "scope": "COMPLETE_TYPED_STATE_AND_FIRST_VOTE_EXTRACTION_NOT_NEXT_OR_NATIVE_RECOVERY",
        "semantic_id_in_lean_examples": "SYNTHETIC_ZERO_TO_AVOID_SELF_HASH_CYCLE",
        "native_export_authenticated": False,
        "source_vectors_sha256": sha256_file(vectors),
        "countercheck_message_source_state": message_index,
        "fields": list(inventory()),
        "complete_states": len(samples),
        "first_votes": len(mapped),
        "component_byte_lemmas": len(names),
        "field_prefix_lemmas": len(inventory()),
        "full_load_pairs": pairs,
        "cases": cases,
    }
    lines = [
        "noncomputable " + line if line.startswith(("def ", "abbrev ")) else line for line in lines
    ]
    value_lines = [
        "noncomputable " + line if line.startswith(("def ", "abbrev ")) else line
        for line in value_lines
        if line != "  simp only []"
    ]
    target.with_name("PublicStateValues.lean").write_text(
        "\n".join(value_lines), encoding="utf-8", newline="\n"
    )
    for name, module_lines in [
        ("PublicStateDocuments", document_lines),
        ("PublicStateLoads", load_lines),
    ]:
        module_lines = [
            "noncomputable " + line if line.startswith(("def ", "abbrev ")) else line
            for line in module_lines
        ]
        target.with_name(name + ".lean").write_text(
            "\n".join(module_lines), encoding="utf-8", newline="\n"
        )
    target.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    write_canonical_json(evidence, result)
    return result


if __name__ == "__main__":
    result = generate()
    print(len(result["cases"]), "Lean kernel cases; native recovery remains open")
