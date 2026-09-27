"""Exact original manifest/corpus witnesses; finite hashes are NOT authentication."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from formal_artifacts import write_canonical_json
from generate_native_source_artifacts import BOUNDARY_PIN, fixture_store
from native_source_artifacts import canonical, require, resolve_q_source

ROOT = Path(__file__).resolve().parents[2]
LEAN = ROOT / "formal/proofs/DeltaReduce/NativeManifestVectors.lean"
TARGET = ROOT / "formal/proposals/native-manifest-vectors.json"


def generate() -> dict:
    store, golden, _ = fixture_store()
    identity = golden["manifest"]["content_id"]
    source = resolve_q_source(store, identity)
    doc = source.manifest
    raw = store[identity]
    require(canonical(doc) == raw, "MANIFEST_PREIMAGE")
    lines = [
        "import DeltaReduce.NativeManifestBinding",
        "import DeltaReduce.NativeShardPlanVectors",
        "namespace DeltaReduce.NativeManifestVectors",
        "open NativeReceiptBytes (Bytes)",
        "open NativeVoteBytes (ascii)",
        "open NativeManifestBinding",
        "set_option maxRecDepth 10000",
        "set_option maxHeartbeats 3000000",
    ]
    pool = {}

    def val(x, numeric=False):
        key = (str(x), numeric)
        if key not in pool:
            i = len(pool)
            pool[key] = i
            lines.append(f"def bytes{i} : Bytes := {list(str(x).encode())}")
            pred = "NativeVoteBytes.DecimalValid" if numeric else "NativeQJson.TextValid"
            lines.append(f"theorem valid{i} : {pred} bytes{i} := by decide")
        i = pool[key]
        return f"bytes{i}", f"valid{i}"

    refkeys = (
        "element_count element_start envelope_bytes leaf_id ordinal "
        "payload_bytes segment_id segment_offset"
    ).split()
    refs = []
    for i, row in enumerate(doc["shards"]):
        values = [val(row[k], k not in ["leaf_id", "segment_id"]) for k in refkeys]
        lines += [
            f"def refWire{i} : NativeManifestBytes.RefWire := ⟨"
            + ",".join(v[0] for v in values)
            + "⟩",
            f"theorem refSyntax{i} : NativeManifestBytes.RefSyntax refWire{i} := ⟨"
            + ",".join(v[1] for v in values)
            + "⟩",
            (
                f"def ref{i} : Ref := ⟨refWire{i},"
                f"NativeShardPlanVectors.plan.entries[{i}],"
                f"{row['envelope_bytes']}⟩"
            ),
            f"theorem refRead{i} : readRef refWire{i} = some ref{i} := by decide",
        ]
        refs.append(f"ref{i}")
    fieldnames = (
        "aggregation_steps commitment_root domain_id "
        "formal_semantics_id parameter_schema_id parent_checkpoint_id "
        "profile_id proof_instance_id round_config_id scale_table_id "
        "schema_version shard_plan_id shards ticket_id total_elements "
        "total_envelope_bytes total_payload_bytes type_name"
    ).split()
    values = []
    proofs = []
    for k in fieldnames:
        if k == "shards":
            values.append("[" + ",".join(f"refWire{i}" for i in range(5)) + "]")
            proofs += ["by decide", "?_"]
        else:
            v, p = val(doc[k], isinstance(doc[k], int))
            values.append(v)
            proofs.append(p)
    lines += [
        "def wire : NativeManifestBytes.Wire := ⟨" + ",".join(values) + "⟩",
        "theorem wireSyntax : NativeManifestBytes.Syntax wire := by",
        "  refine ⟨" + ",".join(proofs) + "⟩",
        "  change ∀ e ∈ ["
        + ",".join(f"refWire{i}" for i in range(5))
        + "], NativeManifestBytes.RefSyntax e",
        "  simp only [List.forall_mem_cons]",
        "  exact ⟨" + ",".join(f"refSyntax{i}" for i in range(5)) + ",by simp⟩",
    ]
    for i, row in enumerate(doc["shards"]):
        data = canonical(row)
        lines += [
            f"def originalRef{i} : Bytes := {list(data)}",
            f"theorem originalRefLength{i} : originalRef{i}.length = {len(data)} := rfl",
            (
                f"theorem originalRefEncoded{i} : "
                f"NativeManifestBytes.refBytes refWire{i} = "
                f"originalRef{i} := rfl"
            ),
        ]
    refs_expr = " ++ [44] ++ ".join(f"originalRef{i}" for i in range(5)) + " ++ [93]"
    lines += [
        f"def originalRefs : Bytes := {refs_expr}",
        "theorem originalRefsEncoded : NativeManifestBytes.refsBytes wire.refs "
        "= originalRefs := by",
        "  simp only [NativeManifestBytes.refsBytes,wire,NativeJsonSequence.encode,"
        + ",".join(f"originalRefEncoded{i}" for i in range(5))
        + ",originalRefs,List.append_assoc]",
    ]
    scalarproofs = []
    original_parts = ["[123]"]
    original_raw_parts = [b"{"]
    field_aliases = [
        "steps",
        "root",
        "domain",
        "semantics",
        "schema",
        "parent",
        "profile",
        "proof",
        "config",
        "scale",
        "version",
        "plan",
        "refs",
        "ticket",
        "total",
        "envelopes",
        "payloads",
        "kind",
    ]
    for i, key in enumerate(fieldnames):
        sep = b"}" if i == len(fieldnames) - 1 else b","
        if key == "shards":
            original_parts += ['ascii "\\"shards\\":["', "originalRefs", "[44]"]
            original_raw_parts += [b'"shards":' + canonical(doc[key]) + sep]
            continue
        data = canonical(key) + b":" + canonical(doc[key]) + sep
        original_parts += [f"originalField{i}"]
        original_raw_parts += [data]
        kind = "natural" if isinstance(doc[key], int) else "text"
        lines += [
            f"def originalField{i} : Bytes := {list(data)}",
            f"theorem originalFieldLength{i} : originalField{i}.length = {len(data)} := rfl",
            f'theorem originalFieldEncoded{i} : NativeScaleBytes.memberBytes "{key}" '
            f".{kind} wire.{field_aliases[i]} {sep[0]} = originalField{i} := rfl",
        ]
        scalarproofs.append(f"originalFieldEncoded{i}")
    require(b"".join(original_raw_parts) == raw, "MANIFEST_COMPONENT_BYTES")
    lines += [
        "def original : Bytes := " + " ++ ".join(original_parts),
        f"theorem originalLength : original.length = {len(raw)} := by",
        "  simp only [original,originalRefs,List.length_append,List.length_cons,List.length_nil,"
        + ",".join(f"originalRefLength{i}" for i in range(5))
        + ","
        + ",".join(f"originalFieldLength{i}" for i in range(18) if i != 12)
        + "]",
        "  rfl",
        "theorem originalEncoded : NativeManifestBytes.encode wire = original := by",
        "  simp only [NativeManifestBytes.encode,"
        + ",".join(scalarproofs)
        + ",originalRefsEncoded,original]",
    ]
    lines += [
        "theorem decodedWire : NativeManifestBytes.decode original = some wire := by",
        "  rw [← originalEncoded]",
        "  apply NativeManifestBytes.decodeEncoded wire wireSyntax",
        "  rw [originalEncoded,originalLength]; decide",
        "def manifest : Manifest := ⟨wire,[" + ",".join(refs) + "],2,36,4798,72⟩",
        "theorem interpretedManifest : interpret wire = some manifest := by",
        "  apply interpretFromSource",
        "  refine ⟨rfl,?_,by decide,by decide,by decide,by decide⟩",
        "  change readRefs ["
        + ",".join(f"refWire{i}" for i in range(5))
        + "] = some ["
        + ",".join(refs)
        + "]",
        "  simp only [readRefs,"
        + ",".join(f"refRead{i}" for i in range(5))
        + ",Bind.bind,Option.bind]",
    ]
    pairs = []

    def hashed(expr, data):
        out = "sha256:" + hashlib.sha256(data).hexdigest()
        pairs.append((expr, data, out))
        return len(pairs) - 1

    schema = hashed("NativeSchemaVectors.original", store[doc["parameter_schema_id"]])
    scale = hashed(
        "NativeScaleBinding.hashInput NativeScaleVectors.original",
        b"deltareduce.004.scale-table.v1\0" + store[doc["scale_table_id"]],
    )
    plan = hashed(
        "NativeShardPlanBinding.hashInput NativeShardPlanVectors.original",
        b"deltareduce.004.shard-plan.v1\0" + store[doc["shard_plan_id"]],
    )
    man = hashed("manifestInput original", b"deltareduce.004.manifest.v1\0" + raw)
    payloads = []
    leaves = []
    for i, r in enumerate(doc["shards"]):
        frame = store[r["leaf_id"]]
        payloads.append(
            hashed(f"NativeScaleVectors.bound{i}.block.frame.payload", frame[-r["payload_bytes"] :])
        )
        leaves.append(
            hashed(
                f"leafInput NativeQBytesVectors.frame{i}",
                b"deltareduce.004.shard-leaf.v1\0" + frame,
            )
        )
    layer = [r["leaf_id"] for r in doc["shards"]]
    nodes = []
    levels = []
    while len(layer) > 1:
        if len(layer) % 2:
            layer.append(layer[-1])
        nxt = []
        level_pairs = []
        for a, b in zip(layer[::2], layer[1::2], strict=True):
            data = b"deltareduce.004.merkle-node.v1\0" + bytes.fromhex(a[7:]) + bytes.fromhex(b[7:])
            key = hashed(str(list(data)), data)
            nodes.append(key)
            nxt.append(pairs[key][2])
            level_pairs.append((a, b, key))
        levels.append(level_pairs)
        layer = nxt
    require(layer[0] == doc["commitment_root"], "MERKLE_ROOT")
    for i, (expr, _, out) in enumerate(pairs):
        lines += [
            f"def hashInput{i} : Bytes := {expr}",
            f"def hashOutput{i} : Bytes := ascii {json.dumps(out)}",
            f"theorem hashLength{i} : hashInput{i}.length = {len(pairs[i][1])} := rfl",
        ]
    lines += [
        "/-- Finite exact-preimage SYNTHETIC adapter. NOT SHA or source authority. -/",
        "@[irreducible]",
        "def fixtureHash (raw : Bytes) : Bytes :=",
    ]
    groups = {}
    for i, (_, data, _) in enumerate(pairs):
        groups.setdefault(len(data), []).append(i)
    for length, indices in groups.items():
        lines += [f"  if raw.length = {length} then"]
        for i in indices:
            lines += [f"    if raw = hashInput{i} then hashOutput{i} else"]
        lines += ["    []", "  else"]
    lines += ["    []"]
    for i in range(len(pairs)):
        length = len(pairs[i][1])
        lines += [
            f"theorem hashChecked{i} : fixtureHash ({pairs[i][0]}) = hashOutput{i} := by",
            f"  change fixtureHash hashInput{i} = hashOutput{i}",
            "  unfold fixtureHash",
            f"  rw [hashLength{i}]",
        ]
        for other_length in groups:
            if other_length == length:
                break
            lines += [f"  rw [if_neg (by decide : ¬ ({length} = {other_length}))]"]
        lines += ["  rw [if_pos rfl]"]
        for j in groups[length]:
            if j == i:
                break
            lines += [f"  rw [if_neg (show hashInput{i} ≠ hashInput{j} from by decide)]"]
        lines += ["  rw [if_pos rfl]"]
    output_indices = {out: i for i, (_, _, out) in enumerate(pairs)}
    for a, b, key in [row for level in levels for row in level]:
        da = list(bytes.fromhex(a[7:]))
        db = list(bytes.fromhex(b[7:]))
        ia, ib = output_indices[a], output_indices[b]
        lines += [
            (
                f"theorem pairChecked{key} : "
                f"NativeManifestMerkle.pair fixtureHash "
                f"hashOutput{ia} hashOutput{ib} = some "
                f"hashOutput{key} :="
            ),
            (
                f"  NativeManifestMerkle.pairFromSource (da := "
                f"{da}) (db := {db}) (by decide) (by decide) "
                f"hashChecked{key} (by decide)"
            ),
        ]
    for n, level in enumerate(levels):
        inputs = leaves if n == 0 else [key for _, _, key in levels[n - 1]]
        outputs = [key for _, _, key in level]
        lines += [
            f"theorem levelChecked{n} : NativeManifestMerkle.level fixtureHash ["
            + ",".join(f"hashOutput{i}" for i in inputs)
            + "] = some ["
            + ",".join(f"hashOutput{i}" for i in outputs)
            + "] := by",
            "  simp only [NativeManifestMerkle.level,"
            + ",".join(f"pairChecked{i}" for i in outputs)
            + (
                ",Bind.bind,Option.bind,Option.map]"
                if len(inputs) % 2
                else ",Bind.bind,Option.bind]"
            ),
        ]
    lines += [
        "def planBound := NativeShardPlanVectors.bound",
        "theorem boundPlan : NativeShardPlanBinding.bind fixtureHash NativeSchemaVectors.original",
        "    NativeScaleVectors.original NativeShardPlanVectors.original = some planBound := by",
        "  apply NativeShardPlanBinding.bindFromSource",
        "  refine ⟨?_,NativeShardPlanVectors.decodedWire,NativeShardPlanVectors.interpretedPlan,",
        "    NativeShardPlanVectors.computedPlan,?_⟩",
        "  · apply NativeSchemaBinding.bindFromSource",
        (
            f"    exact ⟨NativeSchemaVectors.decodedSchema,"
            f"NativeScaleVectors.decodedTable,"
            f"hashChecked{schema},by decide,by decide⟩"
        ),
        f"  · exact ⟨rfl,rfl,rfl,rfl,rfl,hashChecked{scale}.symm,rfl,by decide⟩",
    ]
    for i in range(5):
        lines += [
            f"theorem scaleQ{i} : NativeScaleBinding.bind fixtureHash NativeScaleVectors.original",
            f"    NativeQBytesVectors.frame{i} = some NativeScaleVectors.bound{i} := by",
            "  apply NativeScaleBinding.bindFromSource",
            f"  exact ⟨NativeScaleVectors.decodedTable,NativeQHeaderVectors.joined{i},",
            f"    by decide,hashChecked{scale},rfl,rfl,rfl,by decide,by decide⟩",
            f"theorem leafLinks{i} : LeafLinks fixtureHash planBound wire ref{i}",
            f"    NativeQBytesVectors.frame{i} NativeScaleVectors.bound{i} := by",
            f"  refine ⟨rfl,?_,by decide,by decide,by decide,hashChecked{leaves[i]}⟩",
            "  unfold expectedHeader",
            f"  rw [hashChecked{payloads[i]}]",
            "  rfl",
        ]
    lines += [
        "def raws : List Bytes := ["
        + ",".join(f"NativeQBytesVectors.frame{i}" for i in range(5))
        + "]",
        "def blocks : List NativeScaleBinding.Bound := ["
        + ",".join(f"NativeScaleVectors.bound{i}" for i in range(5))
        + "]",
        (
            "theorem corpusChecked : corpus fixtureHash "
            "NativeScaleVectors.original planBound wire manifest.refs "
            "raws = some blocks := by"
        ),
        "  apply corpusFromSource",
        "  exact "
        + "".join(f".cons scaleQ{i} leafLinks{i} (" for i in range(5))
        + ".nil"
        + ")" * 5,
        (
            "theorem manifestLinks : Links fixtureHash "
            "NativeShardPlanVectors.original planBound manifest := by"
        ),
        f"  refine ⟨rfl,rfl,rfl,rfl,rfl,rfl,hashChecked{plan}.symm,?_⟩",
        "  decide",
        (
            "theorem rootChecked : NativeManifestMerkle.root fixtureHash "
            "(manifest.refs.map (fun r => r.wire.leaf)) = some wire.root "
            ":= by"
        ),
        "  unfold NativeManifestMerkle.root",
        "  rw [if_pos (by decide)]",
        "  change NativeManifestMerkle.tree fixtureHash 13 ["
        + ",".join(f"hashOutput{i}" for i in leaves)
        + "] = some wire.root",
        "  rw [NativeManifestMerkle.tree,levelChecked0]",
        "  dsimp only [Bind.bind,Option.bind]",
        "  rw [NativeManifestMerkle.tree,levelChecked1]",
        "  dsimp only [Bind.bind,Option.bind]",
        "  rw [NativeManifestMerkle.tree,levelChecked2]",
        "  dsimp only [Bind.bind,Option.bind]",
        "  rw [NativeManifestMerkle.tree,if_pos (by decide)]",
        "  rfl",
        "def bound : Bound := ⟨planBound,manifest,blocks⟩",
        (
            "theorem wholeManifest : bind fixtureHash "
            "NativeSchemaVectors.original NativeScaleVectors.original"
        ),
        f"    NativeShardPlanVectors.original original hashOutput{man} raws = some bound :=",
        "  bindFromSource ⟨boundPlan,decodedWire,interpretedManifest,manifestLinks,",
        f"    ⟨by decide,hashChecked{man}⟩,corpusChecked,rootChecked⟩",
        "theorem exactCompleteSizes : manifest.envelopes = (raws.map List.length).sum ∧",
        "    manifest.payloads = (blocks.map (fun q => q.block.frame.payload.length)).sum ∧",
        (
            "    manifest.total = (blocks.map (fun q => "
            "q.block.frame.values.length)).sum := exactTotals "
            "wholeManifest"
        ),
    ]
    cases = {
        "emptyManifest": "NativeManifestBytes.decode [] = none",
        "trailingComma": 'NativeManifestBytes.readRefs (ascii ",]") = none',
        "emptyTree": "NativeManifestMerkle.root fixtureHash [] = none",
        "fuelExhausted": "NativeManifestMerkle.tree fixtureHash 0 [wire.root] = none",
        "singletonTree": "NativeManifestMerkle.root (fun _ => []) [wire.root] = some wire.root",
        "rawDigestLength": (
            f"(NativeManifestMerkle.digest hashOutput{leaves[0]}).map List.length = some 32"
        ),
        "oddHex": 'NativeManifestMerkle.unhex (ascii "a") = none',
        "upperHex": 'NativeManifestMerkle.unhex (ascii "AA") = none',
        "invalidHashOutput": (
            f"NativeManifestMerkle.pair (fun _ => []) "
            f"hashOutput{leaves[0]} hashOutput{leaves[1]} = "
            f"none"
        ),
        "wrongEnvelope": (
            "¬ LeafLinks fixtureHash planBound wire "
            "{ref0 with envelope := 950} NativeQBytesVectors.frame0 "
            "NativeScaleVectors.bound0"
        ),
        "wrongTicket": (
            "¬ LeafLinks fixtureHash planBound "
            '{wire with ticket := ascii "wrong"} ref0 '
            "NativeQBytesVectors.frame0 NativeScaleVectors.bound0"
        ),
        "wrongProof": (
            "¬ LeafLinks fixtureHash planBound "
            "{wire with proof := wire.config} ref0 "
            "NativeQBytesVectors.frame0 NativeScaleVectors.bound0"
        ),
        "wrongConfig": (
            "¬ LeafLinks fixtureHash planBound "
            "{wire with config := wire.proof} ref0 "
            "NativeQBytesVectors.frame0 NativeScaleVectors.bound0"
        ),
        "wrongLeaf": (
            "¬ LeafLinks fixtureHash planBound wire "
            "{ref0 with wire := {refWire0 with leaf := wire.root}} "
            "NativeQBytesVectors.frame0 NativeScaleVectors.bound0"
        ),
        "wrongCount": (
            "¬ LeafLinks fixtureHash planBound wire "
            "{ref0 with entry := {ref0.entry with count := 5}} "
            "NativeQBytesVectors.frame0 NativeScaleVectors.bound0"
        ),
        "missingRef": (
            "¬ Links fixtureHash NativeShardPlanVectors.original "
            "planBound {manifest with refs := manifest.refs.drop 1}"
        ),
        "extraRef": (
            "¬ Links fixtureHash NativeShardPlanVectors.original "
            "planBound {manifest with refs := manifest.refs ++ [ref0]}"
        ),
        "reorderedRefs": (
            "¬ Links fixtureHash NativeShardPlanVectors.original "
            "planBound {manifest with refs := manifest.refs.reverse}"
        ),
        "wrongByteTotal": (
            "¬ Links fixtureHash NativeShardPlanVectors.original "
            "planBound {manifest with envelopes := 4799}"
        ),
        "wrongPayloadTotal": (
            "¬ Links fixtureHash NativeShardPlanVectors.original "
            "planBound {manifest with payloads := 73}"
        ),
        "wrongElementTotal": (
            "¬ Links fixtureHash NativeShardPlanVectors.original "
            "planBound {manifest with total := 35}"
        ),
        "zeroAggregation": (
            "¬ Links fixtureHash NativeShardPlanVectors.original "
            "planBound {manifest with steps := 0}"
        ),
        "wideAggregation": (
            "¬ Links fixtureHash NativeShardPlanVectors.original "
            "planBound {manifest with steps := 2^32}"
        ),
        "missingCorpusTail": "corpus fixtureHash [] planBound wire [ref0] [] = none",
        "extraCorpusTail": "corpus fixtureHash [] planBound wire [] [[]] = none",
    }
    bad_leaf = {
        "wrongEnvelope": 4,
        "wrongTicket": 1,
        "wrongProof": 1,
        "wrongConfig": 1,
        "wrongLeaf": 5,
        "wrongCount": 2,
    }
    bad_links = {
        "missingRef": 12,
        "extraRef": 12,
        "reorderedRefs": 12,
        "wrongByteTotal": 17,
        "wrongPayloadTotal": 15,
        "wrongElementTotal": 14,
        "zeroAggregation": 10,
        "wideAggregation": 11,
    }
    for name, prop in cases.items():
        if name in bad_leaf or name in bad_links:
            index = (bad_leaf | bad_links)[name]
            length = 6 if name in bad_leaf else 18
            names = ["bad" if i == index else "_" for i in range(length)]
            lines += [
                f"theorem {name} : {prop} := by",
                "  intro h",
                "  rcases h with ⟨" + ",".join(names) + "⟩",
            ]
            if name == "wrongLeaf":
                lines += [f"  rw [hashChecked{leaves[0]}] at bad"]
            if index == 1 and name in bad_leaf:
                lines += [
                    "  have mismatch := congrArg NativeQHeader.Wire."
                    + {"wrongTicket": "ticket", "wrongProof": "proof", "wrongConfig": "config"}[
                        name
                    ]
                    + " bad",
                    "  revert mismatch; decide",
                ]
            else:
                lines += ["  revert bad; decide"]
        else:
            lines += [f"theorem {name} : {prop} := by decide"]
    # An explicit missing parent/config preimage does not become authenticated by this layer.
    lines += ["end DeltaReduce.NativeManifestVectors", ""]
    result = {
        "scope": "COMPLETE_ORIGINAL_MANIFEST_CORPUS_UNDER_UNVERIFIED_HASH",
        "source_boundary_sha256": BOUNDARY_PIN,
        "formal_go": False,
        "native_execution": False,
        "native_recovery_proved": False,
        "hash_adapter_authenticated": False,
        "manifest_authority_proved": False,
        "manifest_id": identity,
        "manifest_bytes_hex": raw.hex(),
        "manifest": doc,
        "synthetic_hash_preimages": [
            {"bytes_hex": data.hex(), "content_id": out} for _, data, out in pairs
        ],
        "small_kernel_cases": list(cases),
        "missing_parent_preimage": doc["parent_checkpoint_id"] not in store,
    }
    LEAN.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    write_canonical_json(TARGET, result)
    return result


if __name__ == "__main__":
    generate()
