"""Kernel input descriptors for exact Profile-v1 bytes, not valid native histories."""

from formal.reference.profile_source import metadata as m
from formal.reference.profile_source.test_metadata import Package


def byte_list(value):
    return "[" + ",".join(str(b) for b in value.encode("ascii")) + "]"


def node(value):
    if type(value) is str:
        return f"(.text {byte_list(value)})"
    if type(value) is bool:
        return f"(.boolean {str(value).lower()})"
    if type(value) is list:
        result = ".nil"
        for item in reversed(value):
            result = f"(.cons {node(item)} {result})"
        return f"(.array {result})"
    if type(value) is dict:
        return f"(.object {fields(value)})"
    raise TypeError("The approved profile has no number/null JSON values")


def fields(value):
    result = ".nil"
    for key, item in reversed(sorted(value.items())):
        result = f"(.cons {byte_list(key)} {node(item)} {result})"
    return result


def generate():
    p = Package()
    activate = p.activate()
    anchor = {**activate, "kind": "ANCHOR"}
    examples = [
        ("bootstrap", p.boot),
        ("manifest", p.manifest),
        ("sourceIndex", p.index),
        ("init", p.record),
        ("activate", activate),
        ("anchor", anchor),
    ]
    lines = [
        "import ProfileControl",
        "-- Synthetic bytes only; QC/history placeholders are NOT legal source evidence.",
        "open DeltaReduce.ProfileSource.Control DeltaReduce.NativeVoteBytes",
        "set_option maxRecDepth 20000",
        "set_option maxHeartbeats 4000000",
        "namespace ProfileControlVectors",
    ]
    records = []
    for i, (kind, value) in enumerate(examples):
        raw = m.canonical(value)
        # Reparse the originals, not an independent alternate descriptor fixture.
        parsed = m.load(raw)
        lines += [
            f"def descriptor{i} : Fields := {fields(parsed)}",
            f"def original{i} : DeltaReduce.NativeReceiptBytes.Bytes := "
            + byte_list(raw.decode("ascii")),
            f"example : check .{kind} descriptor{i} original{i} = some descriptor{i} := by decide",
            f"example : check .{kind} descriptor{i} (original{i} ++ [32]) = none := by decide",
        ]
        duplicate = b'{"profile_id":"other",' + raw[1:]
        lines.append(
            f"example : check .{kind} descriptor{i} {byte_list(duplicate.decode())} "
            "= none := by decide"
        )
        invalid = {**parsed, "profile_id": "unapproved-profile"}
        lines += [
            f"def wrong{i} : Fields := {fields(invalid)}",
            f"example : check .{kind} wrong{i} (encode (.object wrong{i})) = none := by decide",
        ]
        records.append({"kind": kind, "original_hex": raw.hex(), "raw_id": m.raw_id(raw)})
    # Canonicality rejects duplicate keys inside nested objects too, even when
    # the attacker supplies a matching typed descriptor and matching bytes.
    lines += [
        'def duplicate : Fields := .cons (ascii "x") (.boolean true) '
        '(.cons (ascii "x") (.boolean false) .nil)',
        "example : canonicalFields duplicate = false := by decide",
        "example : canonical (.array (.cons (.object duplicate) .nil)) = false := by decide",
        "end ProfileControlVectors",
    ]
    return "\n".join(lines) + "\n", records
