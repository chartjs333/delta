import Std

/-! Approved pre-append W1 sufficiency only. Not a bound on the complete
public state or a source-domain restriction inferred from public acceptance. -/
namespace DeltaReduce.ISCSourceV2.Budget

def sourceBytes (command state prior deliveries : Nat) : Nat :=
  76 + command + 71 + state + prior + deliveries
def candidateBytes (next certificate : Nat) : Nat := 16 + next + certificate
def walBytes (command state prior next certificate deliveries effects : Nat) : Nat :=
  72 + sourceBytes command state prior deliveries + candidateBytes next certificate + effects + 369
def resultBytes (certificate effects : Nat) : Nat := 12 + 369 + effects + certificate

theorem walSufficient {command state prior next certificate deliveries effects : Nat}
    (commandBound : command ≤ 65536) (stateBound : state ≤ 65536)
    (priorBound : prior ≤ 4194304) (nextBound : next ≤ 4194304)
    (certificateBound : certificate ≤ 4194304) (deliveryBound : deliveries ≤ 33554432)
    (effectBound : effects ≤ 1048576) :
    walBytes command state prior next certificate deliveries effects ≤ 47317596 ∧
    walBytes command state prior next certificate deliveries effects < 67108864 := by
  unfold walBytes sourceBytes candidateBytes
  omega

theorem outputSufficient {certificate effects : Nat}
    (certificateBound : certificate ≤ 4194304) (effectBound : effects ≤ 1048576) :
    resultBytes certificate effects ≤ 5243261 ∧
    resultBytes certificate effects < 16777216 := by
  unfold resultBytes
  omega

theorem logicalResponseSufficient {certificate effects metadata : Nat}
    (certificateBound : certificate ≤ 4194304) (effectBound : effects ≤ 1048576)
    (metadataBound : metadata ≤ 8192) :
    resultBytes certificate effects + metadata ≤ 5251453 ∧
    resultBytes certificate effects + metadata + 128 < 16785536 := by
  unfold resultBytes
  omega

end DeltaReduce.ISCSourceV2.Budget
