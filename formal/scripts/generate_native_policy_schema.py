"""Emit the explicit source-inventoried policy grammar for the Lean interpreter."""

from pathlib import Path

from native_policy_codec import SCHEMAS, vector_shape

ROOT = Path(__file__).resolve().parents[2]


def name(s):
    return "fmt" + "".join(x.capitalize() for x in s.split("_"))


def format_of(kind):
    if kind == "text":
        return ".text"
    if kind == "bool":
        return ".boolean"
    if kind in {"u32", "u64", "i64"}:
        return ".uint " + ("4" if kind == "u32" else "8")
    vector = vector_shape(kind)
    if vector:
        item, bound = vector
        return f".vector {bound} ({format_of(item)})"
    return name(kind)


def generate():
    lines = [
        "import DeltaReduce.NativePolicyCodec",
        "",
        "/-! Generated pinned DVPOL001 field inventory. Not policy admission. -/",
        "namespace DeltaReduce.NativePolicySchema",
        "open NativePolicyCodec",
        "",
    ]
    for key, fields in SCHEMAS.items():
        expr = ".end"
        for field, kind in reversed(fields):
            expr = f'.field "{field}" ({format_of(kind)}) ({expr})'
        lines += [f"def {name(key)} : Format :=", "  " + expr, ""]
    lines += ["end DeltaReduce.NativePolicySchema", ""]
    (ROOT / "formal/proofs/DeltaReduce/NativePolicySchema.lean").write_text(
        "\n".join(lines), encoding="utf-8", newline="\n"
    )


def lean_value(kind, value):
    if kind == "text":
        return ".text [" + ",".join(str(b) for b in value.encode()) + "]"
    if kind == "bool":
        return ".number " + str(int(value))
    if kind in {"u32", "u64", "i64"}:
        return ".number " + str(value % 2**64)
    vector = vector_shape(kind)
    if vector:
        return ".items [" + ",".join("(" + lean_value(vector[0], v) + ")" for v in value) + "]"
    expr = ".end"
    for key, t in reversed(SCHEMAS[kind]):
        expr = ".pair (" + lean_value(t, value[key]) + ") (" + expr + ")"
    return expr


def generate_vectors():
    from native_policy_codec import HEADER, encode_value

    def minimal(kind):
        if kind == "text":
            return ""
        if kind == "bool":
            return False
        if kind in {"u32", "u64", "i64"}:
            return 0
        if vector_shape(kind):
            return []
        return {k: minimal(t) for k, t in SCHEMAS[kind]}

    p = minimal("policy")
    p.update(validator_ids=[""], role=1, configured_abort_reason="HARD_DEADLINE")
    c = minimal("candidate")
    c["action"] = 1
    p["candidates"] = [c]
    tree = lean_value("policy", p)
    body = "[" + ",".join(str(b) for b in encode_value("policy", p)) + "]"
    lines = [
        "import DeltaReduce.NativePolicyBytes",
        "",
        "/-! Small mathematical codec examples; no native startup authority. -/",
        "namespace DeltaReduce.NativePolicyCodecVectors",
        "open NativePolicyCodec NativePolicySchema NativePolicyBytes NativeReceiptBytes",
        "set_option maxRecDepth 10000",
        "set_option maxHeartbeats 1000000",
        "",
        "def tree : Value := " + tree,
        "def body : Bytes := " + body,
        (
            "theorem exactEncoding : NativePolicyCodec.encode fmtPolicy t"
            "ree = some body := by decide"
        ),
        "theorem fullTreeInverse : NativePolicyCodec.decode fmtPolicy body = some tree :=",
        "  NativePolicyCodec.encoded exactEncoding",
        (
            "theorem completeMinimalRead : (decodePolicy (NativePolicyByt"
            "es.header ++ body)).isSome = true := by decide"
        ),
        "theorem emptyFrame : (decodePolicy []).isNone = true := by decide",
        (
            "theorem truncatedFrame : (decodePolicy ((NativePolicyBytes.h"
            "eader ++ body).take 32)).isNone = true := by decide"
        ),
        (
            "theorem trailingFrame : (decodePolicy (NativePolicyBytes.hea"
            "der ++ body ++ [0])).isNone = true := by decide"
        ),
        (
            "theorem wrongHeader : (decodePolicy ([0] ++ (NativePolicyByt"
            "es.header ++ body).drop 1)).isNone = true := by decide"
        ),
        "theorem signedMinimum : signed64 (2^63) = -(2^63 : Int) := by decide",
        "theorem signedMaximum : signed64 (2^63-1) = (2^63-1 : Int) := by decide",
        "theorem signedMinusOne : signed64 (2^64-1) = -1 := by decide",
        "theorem nonBoolean : (parse .boolean [2]).isNone = true := by decide",
        "theorem asciiControl : (parse .text [0,0,0,1,31]).isNone = true := by decide",
        "theorem asciiHigh : (parse .text [0,0,0,1,128]).isNone = true := by decide",
        "theorem textTooLong : (parse .text [0,0,16,1]).isNone = true := by decide",
        (
            "theorem vectorTooLong : (parse (.vector 2 .boolean) [0,0,0,3"
            ",0,0,0]).isNone = true := by decide"
        ),
        (
            "theorem uintOverflow : (NativePolicyCodec.encode (.uint 4) ("
            ".number (2^32))).isNone = true := by decide"
        ),
        (
            "theorem uintMax : parse (.uint 8) [255,255,255,255,255,255,2"
            "55,255] = some (.number (2^64-1),[]) := by rfl"
        ),
        (
            "theorem duplicatesRetained : parse (.vector 100000 .text) [0"
            ",0,0,2,0,0,0,1,97,0,0,0,1,97] = some (.items [.text [97],.te"
            "xt [97]],[]) := by rfl"
        ),
        (
            "theorem reverseOrderRetained : parse (.vector 100000 .text) "
            "[0,0,0,2,0,0,0,1,122,0,0,0,1,97] = some (.items [.text [122]"
            ",.text [97]],[]) := by rfl"
        ),
        (
            "theorem rationalZeroRetained : (NativePolicyCodec.decode fmt"
            "Rational (be 8 0 ++ be 8 0)).isSome = true := by decide"
        ),
        "theorem asciiLexPrefix : bytesLT [97] [97,98] = true := by decide",
        "theorem asciiLexReverse : bytesLT [122] [97] = false := by decide",
        "theorem emptyValidators : strictly bytesLT ([] : List Bytes) = true := by decide",
        "theorem duplicateValidators : strictly bytesLT [[97],[97]] = false := by decide",
        'theorem invalidReason : ascii "NO_ABORT" ∉ reasons := by decide',
    ]
    import copy

    mutations = [
        ("wrongRole", lambda v: v.update(role=0), False),
        ("noValidators", lambda v: v.update(validator_ids=[]), False),
        ("noCandidates", lambda v: v.update(candidates=[]), False),
        ("wrongAction", lambda v: v["candidates"][0].update(action=10), False),
        (
            "unorderedDeadlineStillParses",
            lambda v: v.update(soft_deadline_tick=10, hard_deadline_tick=1),
            True,
        ),
    ]
    for label, edit, accept in mutations:
        v = copy.deepcopy(p)
        edit(v)
        raw = "[" + ",".join(str(b) for b in HEADER + encode_value("policy", v)) + "]"
        lines += [
            f"theorem {label} : (decodePolicy {raw}).isSome = {str(accept).lower()} := by decide"
        ]
    lines += ["end DeltaReduce.NativePolicyCodecVectors", ""]
    (ROOT / "formal/proofs/DeltaReduce/NativePolicyCodecVectors.lean").write_text(
        "\n".join(lines), encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    generate()
    generate_vectors()
