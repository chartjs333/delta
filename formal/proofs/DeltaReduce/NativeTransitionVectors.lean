import DeltaReduce.NativeTransition

import DeltaReduce.NativeStateCodecVectors

set_option maxRecDepth 32768

set_option maxHeartbeats 1000000

namespace DeltaReduce.NativeTransitionVectors

open NativeReceiptBytes NativeVoteBytes NativeStateBytes NativeTransition

def s0 : State := ⟨⟨1,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",1,ascii "0"⟩,0,1,0⟩

def c0 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_INPUT_FREEZE",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

def n0 : State := ⟨⟨1,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "1",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ELIGIBLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",1,ascii "0"⟩,1,1,0⟩

theorem step0 : step s0 c0 = some n0 := by decide

def s1 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "TICKETING_OPEN",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c1 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_ROUND_CONFIG",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

def n1 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "TICKETING_OPEN",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

theorem step1 : step s1 c1 = some n1 := by decide

def s2 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "TICKETING_OPEN",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c2 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ADVANCE_VIEW",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "1"⟩,1,11,1⟩

def n2 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "1",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "TICKETING_OPEN",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "1"⟩,1,1,1⟩

theorem step2 : step s2 c2 = some n2 := by decide

def s3 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "TICKETING_OPEN",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c3 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ACCEPT_COMMITMENT",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

def n3 : State := ⟨⟨0,2,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "1",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "COMMITTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,1,1,0⟩

theorem step3 : step s3 c3 = some n3 := by decide

def s4 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "TICKETING_OPEN",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c4 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ACCEPT_AVAILABILITY",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step4 : step s4 c4 = none := disabledReject s4 c4 .availability (by decide) (by decide)

def s5 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "TICKETING_OPEN",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c5 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_INPUT_FREEZE",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step5 : step s5 c5 = none := disabledReject s5 c5 .freeze (by decide) (by decide)

def s6 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "TICKETING_OPEN",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c6 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_AGGREGATE",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step6 : step s6 c6 = none := disabledReject s6 c6 .aggregate (by decide) (by decide)

def s7 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "TICKETING_OPEN",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c7 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "CERTIFY_ABORT",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

def n7 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "1",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ABORTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,1,1,0⟩

theorem step7 : step s7 c7 = some n7 := by decide

def s8 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "COMMITTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c8 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_ROUND_CONFIG",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step8 : step s8 c8 = none := disabledReject s8 c8 .config (by decide) (by decide)

def s9 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "COMMITTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c9 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ADVANCE_VIEW",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "1"⟩,1,11,1⟩

def n9 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "1",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "COMMITTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "1"⟩,1,1,1⟩

theorem step9 : step s9 c9 = some n9 := by decide

def s10 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "COMMITTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c10 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ACCEPT_COMMITMENT",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

def n10 : State := ⟨⟨0,2,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "1",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "COMMITTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,1,1,0⟩

theorem step10 : step s10 c10 = some n10 := by decide

def s11 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "COMMITTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c11 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ACCEPT_AVAILABILITY",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

def n11 : State := ⟨⟨1,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "1",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,1,1,0⟩

theorem step11 : step s11 c11 = some n11 := by decide

def s12 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "COMMITTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c12 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_INPUT_FREEZE",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step12 : step s12 c12 = none := disabledReject s12 c12 .freeze (by decide) (by decide)

def s13 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "COMMITTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c13 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_AGGREGATE",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step13 : step s13 c13 = none := disabledReject s13 c13 .aggregate (by decide) (by decide)

def s14 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "COMMITTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c14 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "CERTIFY_ABORT",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

def n14 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "1",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ABORTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,1,1,0⟩

theorem step14 : step s14 c14 = some n14 := by decide

def s15 : State := ⟨⟨1,2,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c15 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_ROUND_CONFIG",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step15 : step s15 c15 = none := disabledReject s15 c15 .config (by decide) (by decide)

def s16 : State := ⟨⟨1,2,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c16 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ADVANCE_VIEW",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "1"⟩,1,11,1⟩

def n16 : State := ⟨⟨1,2,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "1",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "1"⟩,1,1,1⟩

theorem step16 : step s16 c16 = some n16 := by decide

def s17 : State := ⟨⟨1,2,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c17 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ACCEPT_COMMITMENT",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step17 : step s17 c17 = none := disabledReject s17 c17 .commitment (by decide) (by decide)

def s18 : State := ⟨⟨1,2,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c18 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ACCEPT_AVAILABILITY",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

def n18 : State := ⟨⟨2,2,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "1",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,1,1,0⟩

theorem step18 : step s18 c18 = some n18 := by decide

def s19 : State := ⟨⟨1,2,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c19 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_INPUT_FREEZE",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

def n19 : State := ⟨⟨1,2,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "1",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ELIGIBLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,1,1,0⟩

theorem step19 : step s19 c19 = some n19 := by decide

def s20 : State := ⟨⟨1,2,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c20 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_AGGREGATE",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step20 : step s20 c20 = none := disabledReject s20 c20 .aggregate (by decide) (by decide)

def s21 : State := ⟨⟨1,2,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c21 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "CERTIFY_ABORT",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

def n21 : State := ⟨⟨1,2,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "1",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ABORTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,1,1,0⟩

theorem step21 : step s21 c21 = some n21 := by decide

def s22 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ELIGIBLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c22 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_ROUND_CONFIG",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step22 : step s22 c22 = none := disabledReject s22 c22 .config (by decide) (by decide)

def s23 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ELIGIBLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c23 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ADVANCE_VIEW",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "1"⟩,1,11,1⟩

def n23 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "1",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ELIGIBLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "1"⟩,1,1,1⟩

theorem step23 : step s23 c23 = some n23 := by decide

def s24 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ELIGIBLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c24 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ACCEPT_COMMITMENT",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step24 : step s24 c24 = none := disabledReject s24 c24 .commitment (by decide) (by decide)

def s25 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ELIGIBLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c25 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ACCEPT_AVAILABILITY",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step25 : step s25 c25 = none := disabledReject s25 c25 .availability (by decide) (by decide)

def s26 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ELIGIBLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c26 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_INPUT_FREEZE",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step26 : step s26 c26 = none := disabledReject s26 c26 .freeze (by decide) (by decide)

def s27 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ELIGIBLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c27 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_AGGREGATE",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

def n27 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "1",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AGGREGATED",ascii "round-vote-fixture",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",3,ascii "0"⟩,1,1,0⟩

theorem step27 : step s27 c27 = some n27 := by decide

def s28 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ELIGIBLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c28 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "CERTIFY_ABORT",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

def n28 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "1",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ABORTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,1,1,0⟩

theorem step28 : step s28 c28 = some n28 := by decide

def s29 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AGGREGATED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c29 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_ROUND_CONFIG",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step29 : step s29 c29 = none := disabledReject s29 c29 .config (by decide) (by decide)

def s30 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AGGREGATED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c30 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ADVANCE_VIEW",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "1"⟩,1,11,1⟩

theorem step30 : step s30 c30 = none := disabledReject s30 c30 .view (by decide) (by decide)

def s31 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AGGREGATED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c31 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ACCEPT_COMMITMENT",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step31 : step s31 c31 = none := disabledReject s31 c31 .commitment (by decide) (by decide)

def s32 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AGGREGATED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c32 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ACCEPT_AVAILABILITY",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step32 : step s32 c32 = none := disabledReject s32 c32 .availability (by decide) (by decide)

def s33 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AGGREGATED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c33 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_INPUT_FREEZE",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step33 : step s33 c33 = none := disabledReject s33 c33 .freeze (by decide) (by decide)

def s34 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AGGREGATED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c34 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_AGGREGATE",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step34 : step s34 c34 = none := disabledReject s34 c34 .aggregate (by decide) (by decide)

def s35 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AGGREGATED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c35 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "CERTIFY_ABORT",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step35 : step s35 c35 = none := disabledReject s35 c35 .abort (by decide) (by decide)

def s36 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ABORTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c36 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_ROUND_CONFIG",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step36 : step s36 c36 = none := disabledReject s36 c36 .config (by decide) (by decide)

def s37 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ABORTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c37 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ADVANCE_VIEW",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "1"⟩,1,11,1⟩

theorem step37 : step s37 c37 = none := disabledReject s37 c37 .view (by decide) (by decide)

def s38 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ABORTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c38 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ACCEPT_COMMITMENT",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step38 : step s38 c38 = none := disabledReject s38 c38 .commitment (by decide) (by decide)

def s39 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ABORTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c39 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ACCEPT_AVAILABILITY",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step39 : step s39 c39 = none := disabledReject s39 c39 .availability (by decide) (by decide)

def s40 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ABORTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c40 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_INPUT_FREEZE",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step40 : step s40 c40 = none := disabledReject s40 c40 .freeze (by decide) (by decide)

def s41 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ABORTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c41 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_AGGREGATE",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step41 : step s41 c41 = none := disabledReject s41 c41 .aggregate (by decide) (by decide)

def s42 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ABORTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",3,ascii "0"⟩,0,1,0⟩

def c42 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "CERTIFY_ABORT",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step42 : step s42 c42 = none := disabledReject s42 c42 .abort (by decide) (by decide)

def s43 : State := ⟨⟨1,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",1,ascii "0"⟩,0,1,0⟩

def c43 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_INPUT_FREEZE",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "other",ascii "0"⟩,1,11,0⟩

theorem step43 : step s43 c43 = none := disabledReject s43 c43 .freeze (by decide) (by decide)

def s44 : State := ⟨⟨1,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",1,ascii "0"⟩,0,1,0⟩

def c44 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_INPUT_FREEZE",ascii "2",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,2,11,0⟩

theorem step44 : step s44 c44 = none := disabledReject s44 c44 .freeze (by decide) (by decide)

def s45 : State := ⟨⟨1,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",1,ascii "0"⟩,0,1,0⟩

def c45 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_INPUT_FREEZE",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "1"⟩,1,11,1⟩

theorem step45 : step s45 c45 = none := disabledReject s45 c45 .freeze (by decide) (by decide)

def s46 : State := ⟨⟨1,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",1,ascii "0"⟩,0,1,0⟩

def c46 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "UNKNOWN_COMMAND",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step46 : step s46 c46 = none := unknownReject s46 c46 (by decide)

def s47 : State := ⟨⟨0,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",1,ascii "0"⟩,0,1,0⟩

def c47 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_INPUT_FREEZE",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step47 : step s47 c47 = none := disabledReject s47 c47 .freeze (by decide) (by decide)

def s48 : State := ⟨⟨1,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "18446744073709551615",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",1,ascii "0"⟩,18446744073709551615,1,0⟩

def c48 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_INPUT_FREEZE",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step48 : step s48 c48 = none := disabledReject s48 c48 .freeze (by decide) (by decide)

def s49 : State := ⟨⟨1,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "18446744073709551615",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "TICKETING_OPEN",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",1,ascii "0"⟩,18446744073709551615,1,0⟩

def c49 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_ROUND_CONFIG",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

def n49 : State := ⟨⟨1,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "18446744073709551615",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "TICKETING_OPEN",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",1,ascii "0"⟩,18446744073709551615,1,0⟩

theorem step49 : step s49 c49 = some n49 := by decide

def s50 : State := ⟨⟨1,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",1,ascii "0"⟩,0,1,0⟩

def c50 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ADVANCE_VIEW",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "2"⟩,1,11,2⟩

theorem step50 : step s50 c50 = none := disabledReject s50 c50 .view (by decide) (by decide)

def s51 : State := ⟨⟨1,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",1,ascii "18446744073709551615"⟩,0,1,18446744073709551615⟩

def c51 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ADVANCE_VIEW",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step51 : step s51 c51 = none := disabledReject s51 c51 .view (by decide) (by decide)

def s52 : State := ⟨⟨1,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "18446744073709551615",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",1,ascii "0"⟩,18446744073709551615,1,0⟩

def c52 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ADVANCE_VIEW",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "1"⟩,1,11,1⟩

theorem step52 : step s52 c52 = none := disabledReject s52 c52 .view (by decide) (by decide)

def s53 : State := ⟨⟨1,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "COMMITTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",1,ascii "0"⟩,0,1,0⟩

def c53 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ACCEPT_COMMITMENT",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step53 : step s53 c53 = none := disabledReject s53 c53 .commitment (by decide) (by decide)

def s54 : State := ⟨⟨1,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",1,ascii "0"⟩,0,1,0⟩

def c54 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ACCEPT_AVAILABILITY",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

theorem step54 : step s54 c54 = none := disabledReject s54 c54 .availability (by decide) (by decide)

def s55 : State := ⟨⟨1,4294967294,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "COMMITTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",4294967295,ascii "0"⟩,0,1,0⟩

def c55 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ACCEPT_COMMITMENT",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

def n55 : State := ⟨⟨1,4294967295,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "1",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "COMMITTED",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",4294967295,ascii "0"⟩,1,1,0⟩

theorem step55 : step s55 c55 = some n55 := by decide

def s56 : State := ⟨⟨4294967294,4294967295,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",4294967295,ascii "0"⟩,0,1,0⟩

def c56 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "ACCEPT_AVAILABILITY",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

def n56 : State := ⟨⟨4294967295,4294967295,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "1",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",4294967295,ascii "0"⟩,1,1,0⟩

theorem step56 : step s56 c56 = some n56 := by decide

def s57 : State := ⟨⟨1,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "18446744073709551614",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",1,ascii "0"⟩,18446744073709551614,1,0⟩

def c57 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_INPUT_FREEZE",ascii "1",ascii "11",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,11,0⟩

def n57 : State := ⟨⟨1,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "18446744073709551615",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ELIGIBLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",1,ascii "0"⟩,18446744073709551615,1,0⟩

theorem step57 : step s57 c57 = some n57 := by decide

def s58 : State := ⟨⟨1,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "0",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "AVAILABLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",1,ascii "0"⟩,0,1,0⟩

def c58 : Command := ⟨⟨ascii "validator-1",ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",ascii "FINALIZE_INPUT_FREEZE",ascii "1",ascii "0",ascii "freeze-after-isc",ascii "round-vote-fixture",ascii "0"⟩,1,0,0⟩

def n58 : State := ⟨⟨1,1,ascii "sha256:1111111111111111111111111111111111111111111111111111111111111111",ascii "1",ascii "1",ascii "sha256:2222222222222222222222222222222222222222222222222222222222222222",ascii "ELIGIBLE",ascii "round-vote-fixture",ascii "sha256:3333333333333333333333333333333333333333333333333333333333333333",1,ascii "0"⟩,1,1,0⟩

theorem step58 : step s58 c58 = some n58 := by decide

theorem text0 : textBytes (ascii "1") = [33,0,0,0,1,49] := by decide

theorem text1 : textBytes (ascii "1.0.0") = [33,0,0,0,5,49,46,48,46,48] := by decide

theorem text2 : textBytes (ascii "EFFECT_BATCH") = [33,0,0,0,12,69,70,70,69,67,84,95,66,65,84,67,72] := by decide

theorem text3 : textBytes (ascii "PERSIST_STATE") = [33,0,0,0,13,80,69,82,83,73,83,84,95,83,84,65,84,69] := by decide

theorem text4 : textBytes (ascii "PUBLISH_CERTIFICATE") = [33,0,0,0,19,80,85,66,76,73,83,72,95,67,69,82,84,73,70,73,67,65,84,69] := by decide

theorem text5 : textBytes (ascii "TRANSITION") = [33,0,0,0,10,84,82,65,78,83,73,84,73,79,78] := by decide

theorem text6 : textBytes (ascii "WAL_RECORD") = [33,0,0,0,10,87,65,76,95,82,69,67,79,82,68] := by decide

theorem text7 : textBytes (ascii "body_hash") = [33,0,0,0,9,98,111,100,121,95,104,97,115,104] := by decide

theorem text8 : textBytes (ascii "command_id") = [33,0,0,0,10,99,111,109,109,97,110,100,95,105,100] := by decide

theorem text9 : textBytes (ascii "effect:freeze-after-isc:01:persist") = [33,0,0,0,34,101,102,102,101,99,116,58,102,114,101,101,122,101,45,97,102,116,101,114,45,105,115,99,58,48,49,58,112,101,114,115,105,115,116] := by decide

theorem text10 : textBytes (ascii "effect:freeze-after-isc:02:publish") = [33,0,0,0,34,101,102,102,101,99,116,58,102,114,101,101,122,101,45,97,102,116,101,114,45,105,115,99,58,48,50,58,112,117,98,108,105,115,104] := by decide

theorem text11 : textBytes (ascii "effect_batch_id") = [33,0,0,0,15,101,102,102,101,99,116,95,98,97,116,99,104,95,105,100] := by decide

theorem text12 : textBytes (ascii "effect_id") = [33,0,0,0,9,101,102,102,101,99,116,95,105,100] := by decide

theorem text13 : textBytes (ascii "effects") = [33,0,0,0,7,101,102,102,101,99,116,115] := by decide

theorem text14 : textBytes (ascii "formal_semantics_id") = [33,0,0,0,19,102,111,114,109,97,108,95,115,101,109,97,110,116,105,99,115,95,105,100] := by decide

theorem text15 : textBytes (ascii "freeze-after-isc") = [33,0,0,0,16,102,114,101,101,122,101,45,97,102,116,101,114,45,105,115,99] := by decide

theorem text16 : textBytes (ascii "kind") = [33,0,0,0,4,107,105,110,100] := by decide

theorem text17 : textBytes (ascii "next_state_root") = [33,0,0,0,15,110,101,120,116,95,115,116,97,116,101,95,114,111,111,116] := by decide

theorem text18 : textBytes (ascii "prior_state_root") = [33,0,0,0,16,112,114,105,111,114,95,115,116,97,116,101,95,114,111,111,116] := by decide

theorem text19 : textBytes (ascii "record_kind") = [33,0,0,0,11,114,101,99,111,114,100,95,107,105,110,100] := by decide

theorem text20 : textBytes (ascii "request_id") = [33,0,0,0,10,114,101,113,117,101,115,116,95,105,100] := by decide

theorem text21 : textBytes (ascii "round-vote-fixture") = [33,0,0,0,18,114,111,117,110,100,45,118,111,116,101,45,102,105,120,116,117,114,101] := by decide

theorem text22 : textBytes (ascii "round_id") = [33,0,0,0,8,114,111,117,110,100,95,105,100] := by decide

theorem text23 : textBytes (ascii "schema_version") = [33,0,0,0,14,115,99,104,101,109,97,95,118,101,114,115,105,111,110] := by decide

theorem text24 : textBytes (ascii "sequence") = [33,0,0,0,8,115,101,113,117,101,110,99,101] := by decide

theorem text25 : textBytes (ascii "sha256:07dbf8e1288e09135b79adc79d38ecb281f165f83ed92e05875fc6b4edeb2979") = [33,0,0,0,71,115,104,97,50,53,54,58,48,55,100,98,102,56,101,49,50,56,56,101,48,57,49,51,53,98,55,57,97,100,99,55,57,100,51,56,101,99,98,50,56,49,102,49,54,53,102,56,51,101,100,57,50,101,48,53,56,55,53,102,99,54,98,52,101,100,101,98,50,57,55,57] := by decide

theorem text26 : textBytes (ascii "sha256:5fa62e0f2fb5e6307941cd51015d3800d8842fdd4ee7cef0d5c3207b103fe17d") = [33,0,0,0,71,115,104,97,50,53,54,58,53,102,97,54,50,101,48,102,50,102,98,53,101,54,51,48,55,57,52,49,99,100,53,49,48,49,53,100,51,56,48,48,100,56,56,52,50,102,100,100,52,101,101,55,99,101,102,48,100,53,99,51,50,48,55,98,49,48,51,102,101,49,55,100] := by decide

theorem text27 : textBytes (ascii "sha256:7450387c92f0e90018c9feb90edbfcd7a46814972672b01015594dcd628d7533") = [33,0,0,0,71,115,104,97,50,53,54,58,55,52,53,48,51,56,55,99,57,50,102,48,101,57,48,48,49,56,99,57,102,101,98,57,48,101,100,98,102,99,100,55,97,52,54,56,49,52,57,55,50,54,55,50,98,48,49,48,49,53,53,57,52,100,99,100,54,50,56,100,55,53,51,51] := by decide

theorem text28 : textBytes (ascii "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6") = [33,0,0,0,71,115,104,97,50,53,54,58,99,99,57,56,102,49,53,97,99,50,48,102,99,51,101,100,50,54,53,99,98,55,54,54,56,50,99,97,49,53,97,57,51,54,101,50,52,54,54,48,97,54,53,49,101,50,98,56,102,56,49,54,51,56,97,98,98,51,50,54,53,99,98,54] := by decide

theorem text29 : textBytes (ascii "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc") = [33,0,0,0,71,115,104,97,50,53,54,58,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99] := by decide

theorem text30 : textBytes (ascii "sha256:f706ea371a9ef1cf0fdd4a3f02c3ec3918ec314a0b3688eac66a83b62ec9020f") = [33,0,0,0,71,115,104,97,50,53,54,58,102,55,48,54,101,97,51,55,49,97,57,101,102,49,99,102,48,102,100,100,52,97,51,102,48,50,99,51,101,99,51,57,49,56,101,99,51,49,52,97,48,98,51,54,56,56,101,97,99,54,54,97,56,51,98,54,50,101,99,57,48,50,48,102] := by decide

theorem text31 : textBytes (ascii "target_id") = [33,0,0,0,9,116,97,114,103,101,116,95,105,100] := by decide

theorem text32 : textBytes (ascii "type_name") = [33,0,0,0,9,116,121,112,101,95,110,97,109,101] := by decide

theorem text33 : textBytes (ascii "validator-1") = [33,0,0,0,11,118,97,108,105,100,97,116,111,114,45,49] := by decide

theorem text34 : textBytes (ascii "validators") = [33,0,0,0,10,118,97,108,105,100,97,116,111,114,115] := by decide

def priorId := ascii "sha256:07dbf8e1288e09135b79adc79d38ecb281f165f83ed92e05875fc6b4edeb2979"

def commandId := ascii "sha256:f706ea371a9ef1cf0fdd4a3f02c3ec3918ec314a0b3688eac66a83b62ec9020f"

def nextId := ascii "sha256:5fa62e0f2fb5e6307941cd51015d3800d8842fdd4ee7cef0d5c3207b103fe17d"

def effectsId := ascii "sha256:7450387c92f0e90018c9feb90edbfcd7a46814972672b01015594dcd628d7533"

def recordId := ascii "sha256:78573aea6aa59534a49e72480def31a45afd4e19c7753ad0d74a06a1639c46ed"

theorem effectPayloadBytes : effectPayload c0 priorId nextId = [49,0,0,0,8,33,0,0,0,7,101,102,102,101,99,116,115,48,0,0,0,2,49,0,0,0,4,33,0,0,0,9,98,111,100,121,95,104,97,115,104,33,0,0,0,71,115,104,97,50,53,54,58,53,102,97,54,50,101,48,102,50,102,98,53,101,54,51,48,55,57,52,49,99,100,53,49,48,49,53,100,51,56,48,48,100,56,56,52,50,102,100,100,52,101,101,55,99,101,102,48,100,53,99,51,50,48,55,98,49,48,51,102,101,49,55,100,33,0,0,0,9,101,102,102,101,99,116,95,105,100,33,0,0,0,34,101,102,102,101,99,116,58,102,114,101,101,122,101,45,97,102,116,101,114,45,105,115,99,58,48,49,58,112,101,114,115,105,115,116,33,0,0,0,4,107,105,110,100,33,0,0,0,13,80,69,82,83,73,83,84,95,83,84,65,84,69,33,0,0,0,9,116,97,114,103,101,116,95,105,100,33,0,0,0,11,118,97,108,105,100,97,116,111,114,45,49,49,0,0,0,4,33,0,0,0,9,98,111,100,121,95,104,97,115,104,33,0,0,0,71,115,104,97,50,53,54,58,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,99,33,0,0,0,9,101,102,102,101,99,116,95,105,100,33,0,0,0,34,101,102,102,101,99,116,58,102,114,101,101,122,101,45,97,102,116,101,114,45,105,115,99,58,48,50,58,112,117,98,108,105,115,104,33,0,0,0,4,107,105,110,100,33,0,0,0,19,80,85,66,76,73,83,72,95,67,69,82,84,73,70,73,67,65,84,69,33,0,0,0,9,116,97,114,103,101,116,95,105,100,33,0,0,0,10,118,97,108,105,100,97,116,111,114,115,33,0,0,0,19,102,111,114,109,97,108,95,115,101,109,97,110,116,105,99,115,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,99,99,57,56,102,49,53,97,99,50,48,102,99,51,101,100,50,54,53,99,98,55,54,54,56,50,99,97,49,53,97,57,51,54,101,50,52,54,54,48,97,54,53,49,101,50,98,56,102,56,49,54,51,56,97,98,98,51,50,54,53,99,98,54,33,0,0,0,15,110,101,120,116,95,115,116,97,116,101,95,114,111,111,116,33,0,0,0,71,115,104,97,50,53,54,58,53,102,97,54,50,101,48,102,50,102,98,53,101,54,51,48,55,57,52,49,99,100,53,49,48,49,53,100,51,56,48,48,100,56,56,52,50,102,100,100,52,101,101,55,99,101,102,48,100,53,99,51,50,48,55,98,49,48,51,102,101,49,55,100,33,0,0,0,16,112,114,105,111,114,95,115,116,97,116,101,95,114,111,111,116,33,0,0,0,71,115,104,97,50,53,54,58,48,55,100,98,102,56,101,49,50,56,56,101,48,57,49,51,53,98,55,57,97,100,99,55,57,100,51,56,101,99,98,50,56,49,102,49,54,53,102,56,51,101,100,57,50,101,48,53,56,55,53,102,99,54,98,52,101,100,101,98,50,57,55,57,33,0,0,0,10,114,101,113,117,101,115,116,95,105,100,33,0,0,0,16,102,114,101,101,122,101,45,97,102,116,101,114,45,105,115,99,33,0,0,0,8,114,111,117,110,100,95,105,100,33,0,0,0,18,114,111,117,110,100,45,118,111,116,101,45,102,105,120,116,117,114,101,33,0,0,0,14,115,99,104,101,109,97,95,118,101,114,115,105,111,110,33,0,0,0,5,49,46,48,46,48,33,0,0,0,9,116,121,112,101,95,110,97,109,101,33,0,0,0,12,69,70,70,69,67,84,95,66,65,84,67,72] := by

  simp only [effectPayload,persistFields,publishFields,effectFields,effectId,effectTail,NativeStateBytes.payload,NativeStateBytes.encodeFields,scalarBytes,nativeSemantics,c0,priorId,nextId,text1,text2,text3,text4,text7,text9,text10,text12,text13,text14,text15,text16,text17,text18,text20,text21,text22,text23,text25,text26,text28,text29,text31,text32,text33,text34]

  rfl

theorem effectBytes : encodeEffects c0 priorId nextId = NativeWalVectors.effects3 := by

  unfold encodeEffects; rw [effectPayloadBytes]; rfl

theorem walPayloadBytes : NativeStateBytes.payload (walFields c0 1 priorId commandId nextId effectsId) = [49,0,0,0,10,33,0,0,0,10,99,111,109,109,97,110,100,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,102,55,48,54,101,97,51,55,49,97,57,101,102,49,99,102,48,102,100,100,52,97,51,102,48,50,99,51,101,99,51,57,49,56,101,99,51,49,52,97,48,98,51,54,56,56,101,97,99,54,54,97,56,51,98,54,50,101,99,57,48,50,48,102,33,0,0,0,15,101,102,102,101,99,116,95,98,97,116,99,104,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,55,52,53,48,51,56,55,99,57,50,102,48,101,57,48,48,49,56,99,57,102,101,98,57,48,101,100,98,102,99,100,55,97,52,54,56,49,52,57,55,50,54,55,50,98,48,49,48,49,53,53,57,52,100,99,100,54,50,56,100,55,53,51,51,33,0,0,0,19,102,111,114,109,97,108,95,115,101,109,97,110,116,105,99,115,95,105,100,33,0,0,0,71,115,104,97,50,53,54,58,99,99,57,56,102,49,53,97,99,50,48,102,99,51,101,100,50,54,53,99,98,55,54,54,56,50,99,97,49,53,97,57,51,54,101,50,52,54,54,48,97,54,53,49,101,50,98,56,102,56,49,54,51,56,97,98,98,51,50,54,53,99,98,54,33,0,0,0,15,110,101,120,116,95,115,116,97,116,101,95,114,111,111,116,33,0,0,0,71,115,104,97,50,53,54,58,53,102,97,54,50,101,48,102,50,102,98,53,101,54,51,48,55,57,52,49,99,100,53,49,48,49,53,100,51,56,48,48,100,56,56,52,50,102,100,100,52,101,101,55,99,101,102,48,100,53,99,51,50,48,55,98,49,48,51,102,101,49,55,100,33,0,0,0,16,112,114,105,111,114,95,115,116,97,116,101,95,114,111,111,116,33,0,0,0,71,115,104,97,50,53,54,58,48,55,100,98,102,56,101,49,50,56,56,101,48,57,49,51,53,98,55,57,97,100,99,55,57,100,51,56,101,99,98,50,56,49,102,49,54,53,102,56,51,101,100,57,50,101,48,53,56,55,53,102,99,54,98,52,101,100,101,98,50,57,55,57,33,0,0,0,11,114,101,99,111,114,100,95,107,105,110,100,33,0,0,0,10,84,82,65,78,83,73,84,73,79,78,33,0,0,0,8,114,111,117,110,100,95,105,100,33,0,0,0,18,114,111,117,110,100,45,118,111,116,101,45,102,105,120,116,117,114,101,33,0,0,0,14,115,99,104,101,109,97,95,118,101,114,115,105,111,110,33,0,0,0,5,49,46,48,46,48,33,0,0,0,8,115,101,113,117,101,110,99,101,33,0,0,0,1,49,33,0,0,0,9,116,121,112,101,95,110,97,109,101,33,0,0,0,10,87,65,76,95,82,69,67,79,82,68] := by

  simp only [NativeStateBytes.payload,walFields,c0,decimal,NativeStateBytes.encodeFields,scalarBytes,nativeSemantics,priorId,commandId,nextId,effectsId,text0,text1,text5,text6,text8,text11,text14,text17,text18,text19,text21,text22,text23,text24,text25,text26,text27,text28,text30,text32]

  rfl

theorem recordBytes : encodeWal c0 1 priorId commandId nextId effectsId = NativeWalVectors.record3 := by

  unfold encodeWal encodeEnvelope; rw [walPayloadBytes]; rfl

def sha (b : Bytes) : Bytes :=

  if b = contentPreimage stateDomain NativeStateCodecVectors.raw3 then [7,219,248,225,40,142,9,19,91,121,173,199,157,56,236,178,129,241,101,248,62,217,46,5,135,95,198,180,237,235,41,121] else

  if b = contentPreimage commandDomain NativeWalVectors.command3 then [247,6,234,55,26,158,241,207,15,221,74,63,2,195,236,57,24,236,49,74,11,54,136,234,198,106,131,182,46,201,2,15] else

  if b = contentPreimage stateDomain NativeWalVectors.state3 then [95,166,46,15,47,181,230,48,121,65,205,81,1,93,56,0,216,132,47,221,78,231,206,240,213,195,32,123,16,63,225,125] else

  if b = contentPreimage effectDomain NativeWalVectors.effects3 then [116,80,56,124,146,240,233,0,24,201,254,185,14,219,252,215,164,104,20,151,38,114,176,16,21,89,77,205,98,141,117,51] else

  if b = contentPreimage walDomain NativeWalVectors.record3 then [120,87,58,234,106,165,149,52,164,158,114,72,13,239,49,164,90,253,78,25,199,117,58,208,215,74,6,161,99,156,70,237] else

  []

theorem hash0 : contentId sha stateDomain NativeStateCodecVectors.raw3 = some priorId := by

  unfold contentId sha

  rw [if_pos rfl]; rfl

theorem hash1 : contentId sha commandDomain NativeWalVectors.command3 = some commandId := by

  unfold contentId sha

  rw [if_neg (by decide : contentPreimage commandDomain NativeWalVectors.command3 ≠ contentPreimage stateDomain NativeStateCodecVectors.raw3)]

  rw [if_pos rfl]; rfl

theorem hash2 : contentId sha stateDomain NativeWalVectors.state3 = some nextId := by

  unfold contentId sha

  rw [if_neg (by decide : contentPreimage stateDomain NativeWalVectors.state3 ≠ contentPreimage stateDomain NativeStateCodecVectors.raw3)]

  rw [if_neg (by decide : contentPreimage stateDomain NativeWalVectors.state3 ≠ contentPreimage commandDomain NativeWalVectors.command3)]

  rw [if_pos rfl]; rfl

theorem hash3 : contentId sha effectDomain NativeWalVectors.effects3 = some effectsId := by

  unfold contentId sha

  rw [if_neg (by decide : contentPreimage effectDomain NativeWalVectors.effects3 ≠ contentPreimage stateDomain NativeStateCodecVectors.raw3)]

  rw [if_neg (by decide : contentPreimage effectDomain NativeWalVectors.effects3 ≠ contentPreimage commandDomain NativeWalVectors.command3)]

  rw [if_neg (by decide : contentPreimage effectDomain NativeWalVectors.effects3 ≠ contentPreimage stateDomain NativeWalVectors.state3)]

  rw [if_pos rfl]; rfl

theorem hash4 : contentId sha walDomain NativeWalVectors.record3 = some recordId := by

  unfold contentId sha

  rw [if_neg (by decide : contentPreimage walDomain NativeWalVectors.record3 ≠ contentPreimage stateDomain NativeStateCodecVectors.raw3)]

  rw [if_neg (by decide : contentPreimage walDomain NativeWalVectors.record3 ≠ contentPreimage commandDomain NativeWalVectors.command3)]

  rw [if_neg (by decide : contentPreimage walDomain NativeWalVectors.record3 ≠ contentPreimage stateDomain NativeWalVectors.state3)]

  rw [if_neg (by decide : contentPreimage walDomain NativeWalVectors.record3 ≠ contentPreimage effectDomain NativeWalVectors.effects3)]

  rw [if_pos rfl]; rfl

theorem originalStateBytes : encodeState n0.wire = NativeWalVectors.state3 := NativeStateCodecVectors.bytes2

theorem originalPriorBytes : encodeState s0.wire = NativeStateCodecVectors.raw3 := NativeStateCodecVectors.bytes3

theorem originalCommandBytes : encodeCommand c0.wire = NativeWalVectors.command3 := NativeStateCodecVectors.bytes1

theorem originalEffectsValid : EffectsValid c0 priorId nextId := by

  refine ⟨by decide,by decide,by decide,by decide,by decide,by decide,by decide,?_⟩

  rw [effectBytes]; decide

theorem originalWalValid : WalValid c0 1 priorId commandId nextId effectsId := by

  refine ⟨by decide,by decide,by decide,by decide,by decide,by decide,by decide,?_⟩

  change (encodeWal c0 1 priorId commandId nextId effectsId).length ≤ maxEnvelope

  rw [recordBytes]; decide

def nativeOutput : Output := ⟨n0,NativeWalVectors.state3,NativeWalVectors.effects3,NativeWalVectors.record3,priorId,commandId,nextId,effectsId,recordId⟩

theorem nativeBuilt : Built sha s0 c0 n0 nativeOutput := by

  refine ⟨rfl,originalStateBytes.symm,?_,?_,hash2,originalEffectsValid,effectBytes.symm,hash3,originalWalValid,recordBytes.symm,hash4⟩

  · rw [originalPriorBytes]; exact hash0

  · rw [originalCommandBytes]; exact hash1

theorem nativeExecuted : execute sha s0 c0 = some nativeOutput := executeFromComponents sha s0 c0 n0 nativeOutput step0 nativeBuilt

theorem nativeBytesExecuted : fromBytes sha NativeStateCodecVectors.raw3 NativeWalVectors.command3 = some nativeOutput :=

  bytesFromComponents sha _ _ s0 c0 nativeOutput NativeStateCodecVectors.parsed3 NativeStateCodecVectors.parsed1 nativeExecuted

theorem originalEntryRecomputed : replayEntry sha NativeStateCodecVectors.raw3 NativeWalVectors.entry3 = some nativeOutput :=

  replayFromComputed sha _ _ _ rfl nativeBytesExecuted ⟨rfl,rfl,rfl⟩

theorem originalWalStateCounters : NativeWalVectors.entry3.sequence = 2 ∧ nativeOutput.next.sequence = 1 := by decide

theorem changedStateRejected : replayEntry sha NativeStateCodecVectors.raw3 {NativeWalVectors.entry3 with state := []} = none :=

  replayRejectChanged nativeBytesExecuted (Or.inl (by decide))

theorem changedEffectsRejected : replayEntry sha NativeStateCodecVectors.raw3 {NativeWalVectors.entry3 with effects := []} = none :=

  replayRejectChanged nativeBytesExecuted (Or.inr (Or.inl (by decide)))

theorem changedInnerWalRejected : replayEntry sha NativeStateCodecVectors.raw3 {NativeWalVectors.entry3 with record := []} = none :=

  replayRejectChanged nativeBytesExecuted (Or.inr (Or.inr (by decide)))

theorem voteIsNotTransition : replayEntry sha NativeStateCodecVectors.raw3 NativeWalVectors.entry2 = none := by simp [replayEntry,NativeWalVectors.entry2]

theorem missingDigestRejects : build (fun _ => []) s0 c0 n0 = none := by simp [build,contentId]

theorem allSevenRegistered : actions.map NativeTransition.actionName = ([ascii "FINALIZE_ROUND_CONFIG",ascii "ADVANCE_VIEW",ascii "ACCEPT_COMMITMENT",ascii "ACCEPT_AVAILABILITY",ascii "FINALIZE_INPUT_FREEZE",ascii "FINALIZE_AGGREGATE",ascii "CERTIFY_ABORT"] : List Bytes) := rfl

end DeltaReduce.NativeTransitionVectors
