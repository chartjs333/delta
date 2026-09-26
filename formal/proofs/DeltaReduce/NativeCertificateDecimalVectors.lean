import DeltaReduce.NativeCertificateDecimal

/-! Finite actual MSVC certificate checks; not a general C++/Lean equivalence proof. -/
namespace DeltaReduce.NativeCertificateDecimalVectors
open NativeCertificateDecimal NativeReceiptBytes
theorem case0 : parse true [48] = some (0 : Int) := by decide
theorem case1 : parse true [49] = some (1 : Int) := by decide
theorem case2 : parse true [45,49] = none := by decide
theorem case3 : parse true [45,48] = none := by decide
theorem case4 : parse true [45,48,48] = some (0 : Int) := by decide
theorem case5 : parse true [45,48,48,48] = some (0 : Int) := by decide
theorem case6 : parse true [45,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48] = some (0 : Int) := by decide
theorem case7 : parse true [48,48] = none := by decide
theorem case8 : parse true [48,49] = none := by decide
theorem case9 : parse true [45,48,49] = none := by decide
theorem case10 : parse true [45,48,48,48,49] = none := by decide
theorem case11 : parse true [57,50,50,51,51,55,50,48,51,54,56,53,52,55,55,53,56,48,55] = some (9223372036854775807 : Int) := by decide
theorem case12 : parse true [57,50,50,51,51,55,50,48,51,54,56,53,52,55,55,53,56,48,56] = none := by decide
theorem case13 : parse true [45,57,50,50,51,51,55,50,48,51,54,56,53,52,55,55,53,56,48,56] = none := by decide
theorem case14 : parse true [45,57,50,50,51,51,55,50,48,51,54,56,53,52,55,55,53,56,48,57] = none := by decide
theorem case15 : parse true [45,48,57,50,50,51,51,55,50,48,51,54,56,53,52,55,55,53,56,48,56] = none := by decide
theorem case16 : parse true [45,48,57,50,50,51,51,55,50,48,51,54,56,53,52,55,55,53,56,48,57] = none := by decide
theorem case17 : parse true [] = none := by decide
theorem case18 : parse true [45] = none := by decide
theorem case19 : parse true [43,48] = none := by decide
theorem case20 : parse true [43,49] = none := by decide
theorem case21 : parse true [32,48] = none := by decide
theorem case22 : parse true [48,32] = none := by decide
theorem case23 : parse true [49,10] = none := by decide
theorem case24 : parse true [49,0] = none := by decide
theorem case25 : parse true [45,48,48,0] = none := by decide
theorem case26 : parse true [49,46,48] = none := by decide
theorem case27 : parse true [49,101,48] = none := by decide
theorem case28 : parse true [48,120,49] = none := by decide
theorem case29 : parse true [45,45,49] = none := by decide
theorem case30 : parse true [255] = none := by decide
theorem case31 : parse false [48] = some (0 : Int) := by decide
theorem case32 : parse false [49] = some (1 : Int) := by decide
theorem case33 : parse false [45,49] = some (-1 : Int) := by decide
theorem case34 : parse false [45,48] = none := by decide
theorem case35 : parse false [45,48,48] = some (0 : Int) := by decide
theorem case36 : parse false [45,48,48,48] = some (0 : Int) := by decide
theorem case37 : parse false [45,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48,48] = some (0 : Int) := by decide
theorem case38 : parse false [48,48] = none := by decide
theorem case39 : parse false [48,49] = none := by decide
theorem case40 : parse false [45,48,49] = some (-1 : Int) := by decide
theorem case41 : parse false [45,48,48,48,49] = some (-1 : Int) := by decide
theorem case42 : parse false [57,50,50,51,51,55,50,48,51,54,56,53,52,55,55,53,56,48,55] = some (9223372036854775807 : Int) := by decide
theorem case43 : parse false [57,50,50,51,51,55,50,48,51,54,56,53,52,55,55,53,56,48,56] = none := by decide
theorem case44 : parse false [45,57,50,50,51,51,55,50,48,51,54,56,53,52,55,55,53,56,48,56] = some (-9223372036854775808 : Int) := by decide
theorem case45 : parse false [45,57,50,50,51,51,55,50,48,51,54,56,53,52,55,55,53,56,48,57] = none := by decide
theorem case46 : parse false [45,48,57,50,50,51,51,55,50,48,51,54,56,53,52,55,55,53,56,48,56] = some (-9223372036854775808 : Int) := by decide
theorem case47 : parse false [45,48,57,50,50,51,51,55,50,48,51,54,56,53,52,55,55,53,56,48,57] = none := by decide
theorem case48 : parse false [] = none := by decide
theorem case49 : parse false [45] = none := by decide
theorem case50 : parse false [43,48] = none := by decide
theorem case51 : parse false [43,49] = none := by decide
theorem case52 : parse false [32,48] = none := by decide
theorem case53 : parse false [48,32] = none := by decide
theorem case54 : parse false [49,10] = none := by decide
theorem case55 : parse false [49,0] = none := by decide
theorem case56 : parse false [45,48,48,0] = none := by decide
theorem case57 : parse false [49,46,48] = none := by decide
theorem case58 : parse false [49,101,48] = none := by decide
theorem case59 : parse false [48,120,49] = none := by decide
theorem case60 : parse false [45,45,49] = none := by decide
theorem case61 : parse false [255] = none := by decide
theorem negativeZeroAccepted : parse true [45,48,48] = some 0 := by decide
theorem negativeZeroNotCanonical : ¬ Canonical [45,48,48] := by decide
theorem signedLeadingZeroAccepted : parse false [45,48,49] = some (-1) := by decide
theorem signedLeadingZeroNotCanonical : ¬ Canonical [45,48,49] := by decide
theorem notUniversalCanonical : ¬ (∀ raw n, parse true raw = some n → Canonical raw) := by intro h; exact negativeZeroNotCanonical (h [45,48,48] 0 negativeZeroAccepted)
theorem equalNumbersDifferentOriginals :
    check true [48] = some ⟨[48],0⟩ ∧
    check true [45,48,48] = some ⟨[45,48,48],0⟩ ∧
    (Checked.mk [48] 0) ≠ ⟨[45,48,48],0⟩ := by decide

end DeltaReduce.NativeCertificateDecimalVectors
