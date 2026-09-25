"""Nine complete-state/native first-vote bindings; synthetic registry, not export."""

from formal_artifacts import load_json_strict, sha256_file, write_canonical_json
from public_native_projection import VERSION, PinnedFixtureSources, projection_id
from public_state_projection import ROOT, require
from public_state_storage import unpack

VECTORS = ROOT / "formal/proposals/public-arithmetic-vectors.json"
TARGET = ROOT / "formal/proposals/public-native-projection.json"


def generate(target=TARGET):
    sources = PinnedFixtureSources()
    document = load_json_strict(VECTORS)
    trace = unpack(document["positive"])
    mapped = [
        e
        for e in document["legacy_correspondence"]
        if e["action_id"] in {"ACT-PARAM-VOTE", "ACT-APPLY-VOTE"}
    ]
    expected = [
        i
        for i, e in enumerate(sources.trace["events"])
        if e["action_id"] in {"ACT-PARAM-VOTE", "ACT-APPLY-VOTE"}
    ]
    require([e["legacy_event_index"] for e in mapped] == expected, "PROJECTION_EVENT_COVERAGE")
    bindings = []
    for entry in mapped:
        before, after = entry["prior_state_index"], entry["next_state_index"]
        require(after == before + 1, "PROJECTION_ADJACENCY")
        value = sources.bind_first(
            entry["legacy_event_index"],
            trace["states"][before],
            trace["states"][after],
            trace["actions"][before],
        )
        bindings.append(
            {
                "id": projection_id(value),
                "prior_state_index": before,
                "next_state_index": after,
                "value": value,
            }
        )
    result = {
        "projection_version": VERSION,
        "status": "CHECKED_FINITE_CORRESPONDENCE_NOT_NATIVE_AUTHORITY",
        "native_export_authenticated": False,
        "state_vectors_sha256": sha256_file(VECTORS),
        "legacy_trace_check": sources.checked,
        "bindings": bindings,
        "remaining": [
            "Independently authenticated exporter/projection registry",
            "General Lean/native complete-state recovery refinement",
            "Physical WAL/decoder/hash and arbitrary initial/failure/repair adapters",
        ],
    }
    write_canonical_json(target, result)
    return result


if __name__ == "__main__":
    result = generate()
    print(
        len(result["bindings"]),
        "first arithmetic bindings; native export authentication remains false",
    )
