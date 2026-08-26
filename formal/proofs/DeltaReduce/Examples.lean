import DeltaReduce.FixedPoint
import DeltaReduce.Quorum
import Mathlib.Tactic.NormNum

/-! Concrete PO instantiations used by the runtime profiles. -/

namespace DeltaReduce

def int64Max : ℤ := 9223372036854775807
def int128Max : ℤ := 170141183460469231731687303715884105727

example : (3 * 1 + 1 : ℕ) = 4 := by norm_num
example : (2 * 1 + 1 : ℕ) = 3 := by norm_num

example : (1024 : ℤ) * 32767 * 32767 ≤ int64Max := by
  norm_num [int64Max]

example : (1000000 : ℤ) * 2147483647 * 2147483647 ≤ int128Max := by
  norm_num [int128Max]

example : (2 : ℕ) * 2 = 4 := by norm_num

example (a q : ℤ) (ha : |a| ≤ 32767) (hq : |q| ≤ 32767) :
    |a * q| ≤ 32767 * 32767 := by
  exact signedProductBound a q 32767 32767 (by norm_num) (by norm_num) ha hq

end DeltaReduce
