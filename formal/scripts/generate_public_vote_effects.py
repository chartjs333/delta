"""Reuse complete-state components to prove computed vote effects in the kernel."""

from pathlib import Path

from formal_artifacts import canonical_json_bytes, load_json_strict, sha256_file
from public_native_projection import PinnedFixtureSources
from public_state_projection import inventory, require
from public_state_storage import unpack

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "formal/proofs/DeltaReduce/PublicVoteEffectsCalculations.lean"
VECTORS = ROOT / "formal/proposals/public-arithmetic-vectors.json"


def generate(target=TARGET, vectors=VECTORS):
    doc = load_json_strict(vectors)
    trace = unpack(doc["positive"])
    mapped = [
        e
        for e in doc["legacy_correspondence"]
        if e["action_id"] in {"ACT-PARAM-VOTE", "ACT-APPLY-VOTE"}
    ]
    require(
        sha256_file(vectors)
        == load_json_strict(ROOT / "formal/proposals/public-state-lean-vectors.json")[
            "source_vectors_sha256"
        ],
        "SOURCE_STATE_PROOF_PIN",
    )
    require(len(mapped) == 9, "FIRST_VOTE_COVERAGE")
    sources = PinnedFixtureSources()
    for entry in mapped:
        p, n = entry["prior_state_index"], entry["next_state_index"]
        sources.bind_first(
            entry["legacy_event_index"], trace["states"][p], trace["states"][n], trace["actions"][p]
        )
    names = {}
    values = {}

    def intern(v):
        k = canonical_json_bytes(v)
        if k in names:
            return names[k]
        if v[0] == "set":
            for x in v[1]:
                intern(x)
        elif v[0] == "fun":
            for a, b in v[1]:
                intern(a)
                intern(b)
        n = "value" + str(len(names))
        names[k] = n
        values[n] = v
        return n

    for e in mapped:
        for pos in (e["prior_state_index"], e["next_state_index"]):
            for field in inventory():
                intern(trace["states"][pos]["state"]["variables"][field])

    def vn(v):
        return names[canonical_json_bytes(v)]

    def vals(xs):
        out = ".nil"
        for x in reversed(xs):
            out = f"(.cons {vn(x)} {out})"
        return out

    out = [
        "import DeltaReduce.PublicVoteEffects",
        "import DeltaReduce.PublicStateVectors",
        "namespace DeltaReduce.PublicVoteEffectsCalculations",
        "open PublicState PublicVoteEffects PublicStateValues "
        "PublicStateDocuments PublicStateVectors",
        "set_option Elab.async false",
        "set_option maxRecDepth 1000000",
        "set_option maxHeartbeats 0",
    ]
    for i, e in enumerate(mapped):
        p, n = e["prior_state_index"], e["next_state_index"]
        b = trace["states"][p]["state"]["variables"]
        a = trace["states"][n]["state"]["variables"]
        new = next(x for x in a["durableVotes"][1] if x not in b["durableVotes"][1])
        vd = {k[1]: v for k, v in new[1]}
        actor = vn(vd["validator"])
        kind = vd["kind"][1]
        field = "parameterVotes" if kind == "PARAMETER" else "applyVotes"
        out += [
            f"noncomputable def first{i} : First state{p} state{n} {actor} := "
            f"(extractFirst state{p} state{n} {actor}).get (by decide +kernel)",
            f"theorem extracted{i} : extractFirst state{p} state{n} {actor} = some first{i} "
            ":= Option.eq_some_of_isSome _",
            f"noncomputable def input{i} : Inputs state{p} first{i}.vote := "
            f"(readInputs state{p} first{i}.vote).get (by decide +kernel)",
            f"theorem read{i} : readInputs state{p} first{i}.vote = some input{i} "
            ":= Option.eq_some_of_isSome _",
        ]
        inserts = {}
        for group in ["durableVotes", "volatileVotes", field]:
            before, after = b[group], a[group]
            item = next(x for x in after[1] if x not in before[1])
            value = vn(item)
            key = (vn(before), value, vn(after))
            if key in inserts:
                continue
            label = f"insert{i}_{group}"
            inserts[key] = label
            out += [
                f"theorem {label} : Value.set (insert {value} {vals(before[1])}) "
                f"= {vn(after)} := by"
            ]
            for head in before[1]:
                hn = vn(head)
                less = canonical_json_bytes(item) < canonical_json_bytes(head)
                if less:
                    proof = f"by rw [encoded_{value},encoded_{hn}]; exact order_{value}_{hn}"
                    out += [
                        f"  rw [PublicVoteEffects.insertBefore (show {value} ≠ {hn} "
                        f"from by decide +kernel) ({proof})]"
                    ]
                    break
                else:
                    proof = (
                        f"by rw [encoded_{value},encoded_{hn}]; "
                        f"exact byteLessReverse order_{hn}_{value}"
                    )
                    out += [
                        f"  rw [PublicVoteEffects.insertAfter (show {value} ≠ {hn} "
                        f"from by decide +kernel) ({proof})]"
                    ]
            out += ["  rfl"]
        items = []
        for f in inventory():
            if f in ["durableVotes", "volatileVotes", field]:
                newitem = next(x for x in a[f][1] if x not in b[f][1])
                v = f"(.set (insert {vn(newitem)} {vals(b[f][1])}))"
            elif f == "durableSequence":
                # The input reader, not this literal, derives sequence. This equality is
                # subsequently checked by the kernel's definitional conversion.
                seq = next(v[1] for k, v in a[f][1] if k == vd["validator"])
                entries = ".nil"
                for k, v in reversed(b[f][1]):
                    entries = f"(.cons {vn(k)} {vn(v)} {entries})"
                v = f"(.function (update {actor} (.integer {seq}) {entries}))"
            else:
                v = vn(b[f])
            items.append(f'("{f}",{v})')
        out += [
            f"theorem rows{i} : state{n}.rows = (expected input{i}).rows := by",
            "  change state" + str(n) + ".rows = [" + ",".join(items) + "]",
            "  rw [" + ",".join(inserts.values()) + "]",
            "  rfl",
            f"theorem accepts{i} : (check state{p} state{n} {actor}).isSome = true "
            f":= checkFromComputed first{i} input{i} extracted{i} read{i} rows{i}",
        ]
    out += ["end DeltaReduce.PublicVoteEffectsCalculations"]
    target.write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    generate()
