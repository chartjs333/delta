"""Kernel cases from retained native decimal observations, with exact original bytes."""

from pathlib import Path

import check_native_certificate_decimal as native
from formal_artifacts import load_json_strict
from generate_native_wal_lean import lit

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "formal/proofs/DeltaReduce/NativeCertificateDecimalVectors.lean"


def generate():
    document = native.verify_document(load_json_strict(native.RESULT))
    native.parse_output((native.FOLDER / "native-output.txt").read_text("ascii"))
    output = [
        "import DeltaReduce.NativeCertificateDecimal",
        "",
        "/-! Finite actual MSVC certificate checks; not a general C++/Lean equivalence proof. -/",
        "namespace DeltaReduce.NativeCertificateDecimalVectors",
        "open NativeCertificateDecimal NativeReceiptBytes",
    ]
    for index, row in enumerate(document["rows"]):
        nonnegative = "true" if row["kind"] == "NORM" else "false"
        raw = bytes.fromhex(row["input_hex"])
        expected = f"some ({int(raw)} : Int)" if row["accepted"] else "none"
        output.append(
            f"theorem case{index} : parse {nonnegative} {lit(raw)} = {expected} := by decide"
        )
    output += [
        "theorem negativeZeroAccepted : parse true [45,48,48] = some 0 := by decide",
        "theorem negativeZeroNotCanonical : ¬ Canonical [45,48,48] := by decide",
        "theorem signedLeadingZeroAccepted : parse false [45,48,49] = some (-1) := by decide",
        "theorem signedLeadingZeroNotCanonical : ¬ Canonical [45,48,49] := by decide",
        "theorem notUniversalCanonical : ¬ (∀ raw n, parse true raw = some n → "
        "Canonical raw) := by intro h; exact negativeZeroNotCanonical "
        "(h [45,48,48] 0 negativeZeroAccepted)",
        "theorem equalNumbersDifferentOriginals :",
        "    check true [48] = some ⟨[48],0⟩ ∧",
        "    check true [45,48,48] = some ⟨[45,48,48],0⟩ ∧",
        "    (Checked.mk [48] 0) ≠ ⟨[45,48,48],0⟩ := by decide",
        "",
        "end DeltaReduce.NativeCertificateDecimalVectors",
    ]
    return "\n".join(output) + "\n"


if __name__ == "__main__":
    TARGET.write_text(generate(), encoding="utf-8", newline="\n")
    print("GENERATED_NATIVE_DECIMAL_COUNTERCHECKS_NOT_CANONICAL_ADMISSION")
