"""Small Lean components from retained original membership and synthetic weights.

No new whole-policy execution, native run, authenticated SHA or proof preimage
for the original008 APC is supplied. Existing full byte vectors are reused.
"""

from __future__ import annotations

import re
from pathlib import Path

import generate_native_plan_weights as source
from formal_artifacts import write_canonical_json
from native_source_artifacts import require

ROOT = Path(__file__).resolve().parents[2]
LEAN = ROOT / "formal/proofs/DeltaReduce/NativePlanCoefficientVectors.lean"
TARGET = ROOT / "formal/proposals/native-plan-coefficient-vectors.json"


def ascii_bytes(value):
    return "[" + ",".join(str(x) for x in value.encode("ascii")) + "]"


def list_of(values):
    return "[" + ",".join(values) + "]"


def member(t, e):
    values = [
        t[k] for k in ("availability_certificate_id", "commitment_id", "domain_id", "ticket_id")
    ]
    tup = "⟨" + ",".join(map(ascii_bytes, values)) + "⟩"
    ent = (
        f"⟨{int(e['accepted'])},{ascii_bytes(e['domain_id'])},"
        f"{int(e['gamma']['numerator'])},{e['gamma']['denominator']},"
        f"{ascii_bytes(e['reason_code'])},{ascii_bytes(e['ticket_id'])}⟩"
    )
    return f"⟨{tup},{ent}⟩"


def generate():
    original = source.generate()  # verifies retained native sources first
    store, docs = source.synthetic_case()
    apc_id, edges = source.put_graph(store, docs)
    from native_plan_weights import resolve_plan_weights

    result = resolve_plan_weights(store, apc_id, edges)
    require([r["coefficient"] for r in result.rows] == [0, 4, 6], "COEFFICIENTS")
    members = [
        member(t, e) for t, e in zip(docs["ISC"]["tuples"], docs["EC"]["entries"], strict=True)
    ]
    weights = [
        f"⟨{int(w['alpha']['numerator'])},{w['alpha']['denominator']},{ascii_bytes(w['ticket_id'])}⟩"
        for w in docs["APC"]["weights"]
    ]
    buckets = [
        f"⟨{ascii_bytes(b['bucket_id'])},{ascii_bytes(b['ticket_id'])}⟩"
        for b in docs["APC"]["bucket_assignments"]
    ]
    text = """import DeltaReduce.NativePlanCoefficients
import DeltaReduce.NativePlanVectors
import DeltaReduce.NativeAccumulatorVectors

/-! Reused original components plus explicitly separate synthetic numeric rows.
No original missing proof is fabricated; no complete policy/proof execution. -/
namespace DeltaReduce.NativePlanCoefficientVectors
open NativeReceiptBytes (Bytes)
open NativePlanMembers NativePlanCoefficients

"""
    text += "def allMembers : List Member := " + list_of(members) + "\n"
    text += "def weights : List NativePlan.Weight := " + list_of(weights) + "\n"
    text += "def buckets : List NativePlan.Bucket := " + list_of(buckets) + "\n"
    text += (
        "def rows : List Row := "
        + list_of(f"⟨{m},{w},{b}⟩" for m, w, b in zip(members[:3], weights, buckets, strict=True))
        + "\n"
    )
    p = result.accumulator
    text += (
        "def numbers : NativeAccumulatorBinding.Numbers := "
        f"⟨{p.coefficient_max},{p.contribution_max},{p.denominator},"
        f"{p.product},{p.prefix},{p.final},64,64⟩\n"
    )
    text += """
theorem originalParents : CrossParents NativePlanVectors.finalEdge := by decide
theorem originalHasOneRow : (derive NativePlanVectors.finalEdge).map List.length =
    some 1 := by decide
theorem originalProofStillDifferent : NativePlanVectors.certificate.common.accumulator ≠
    NativeAccumulatorVectors.id1 := by decide

theorem fullAlignment : align (allMembers.map Member.input) (allMembers.map Member.eligibility) =
    some allMembers := by decide
theorem fullAttach : attach (eligible allMembers) weights buckets = some rows := by decide
theorem rejectedIsRetained : allMembers.length = 4 ∧ (eligible allMembers).length = 3 := by decide
theorem actualCoefficients : (terms numbers rows).map Term.coefficient = [0,4,6] := by decide
theorem fits : PlanFits numbers rows := by decide
theorem domainA : (inDomain (NativeVoteBytes.ascii "domain-a") (terms numbers rows)).map
    Term.coefficient = [0,4] := by decide
theorem domainB : (inDomain (NativeVoteBytes.ascii "domain-b") (terms numbers rows)).map
    Term.coefficient = [6] := by decide
theorem nonminimalDenominator : numbers.denominator = 12 ∧ Nat.lcm 3 2 = 6 := by decide
theorem gammaKept : (rows.map (fun r => r.member.eligibility.denominator)) = [7,7,7] := by decide
theorem zeroStillCounts : NativeAccumulatorBinding.NumericValid
    { numbers with count := 2, prefixBound := 393204, finalBound := 393204 } ∧
    ¬ PlanFits { numbers with count := 2, prefixBound := 393204, finalBound := 393204 }
      rows := by decide
theorem coefficientBoundFails : ¬ WeightFits { numbers with coefficient := 3 } rows[2]! := by decide
theorem wrongDenominator : ¬ WeightFits { numbers with denominator := 5 } rows[1]! := by decide
theorem denominatorNotChosen : ¬ WeightFits { numbers with denominator := 24 } rows[1]! := by decide
theorem zeroDenominator : ¬ PlanFits { numbers with denominator := 0 } rows := by decide
theorem missingWeight : attach (eligible allMembers) weights.tail buckets = none := by decide
theorem extraWeight : attach (eligible allMembers) (weights ++ weights) buckets = none := by decide
theorem reversedWeights : attach (eligible allMembers) weights.reverse buckets = none := by decide
theorem missingBucket : attach (eligible allMembers) weights buckets.tail = none := by decide
theorem reversedBuckets : attach (eligible allMembers) weights buckets.reverse = none := by decide
theorem rejectedCannotReceiveWeight : attach allMembers weights buckets = none := by decide
theorem missingEc : align (allMembers.map Member.input)
    (allMembers.map Member.eligibility).tail = none := by decide
theorem extraIsc : align ((allMembers.map Member.input) ++ (allMembers.map Member.input))
    (allMembers.map Member.eligibility) = none := by decide
theorem wrongDomain : ¬ SameMember { rows[0]!.member.input with domain := [120] }
    rows[0]!.member.eligibility := by decide
theorem invalidAccepted : ¬ SameMember rows[0]!.member.input
    { rows[0]!.member.eligibility with accepted := 2 } := by decide
theorem crossParentNowRejects : ¬ CrossParents
    { NativePlanVectors.finalEdge with certificate := NativePlanVectors.crossIscPlan } := by decide
def changedSeed := { NativePlanVectors.finalEdge with ec :=
  { NativePlanVectors.finalEdge.ec with seedId := [] } }
theorem missingPrimitiveSeedEdge : ¬ CrossParents changedSeed := by decide
def duplicateTicket := { NativePlanVectors.finalEdge with parent :=
  { NativePlanVectors.finalEdge.parent with certificate :=
    { NativePlanVectors.finalEdge.parent.certificate with body :=
      { NativePlanVectors.finalEdge.parent.certificate.body with tuples :=
        NativePlanVectors.finalEdge.parent.certificate.body.tuples ++
        NativePlanVectors.finalEdge.parent.certificate.body.tuples } } } }
theorem duplicateIscRejected : ¬ CrossParents duplicateTicket := by decide
def wrongNorm := { NativePlanVectors.finalEdge with ec :=
  { NativePlanVectors.finalEdge.ec with norm :=
    { NativePlanVectors.finalEdge.ec.norm with evidence :=
      { NativePlanVectors.finalEdge.ec.norm.evidence with entries := [] } } } }
theorem missingNormMembership : ¬ CrossParents wrongNorm := by decide
theorem badDigestWidth : contentHash (fun _ => [0]) [] = [] := by decide
end DeltaReduce.NativePlanCoefficientVectors
"""
    # Inhabited is deliberately unnecessary for formal rows: use explicit
    # component expressions instead of partial default-valued lookup.
    for i in range(3):
        text = text.replace(f"rows[{i}]!", f"(⟨{members[i]},{weights[i]},{buckets[i]}⟩ : Row)")
    cases = re.findall(r"^theorem (\w+)", text, re.M)
    LEAN.write_text(text, encoding="utf-8", newline="\n")
    write_canonical_json(
        TARGET,
        {
            "status": "ORIGINAL_MEMBER_COMPONENTS_AND_SEPARATE_SYNTHETIC_COEFFICIENTS",
            "original_apc": original["original_members"]["plan_id"],
            "original_weight_join_failure": original["original_weight_join_failure"],
            "synthetic_apc": apc_id,
            "synthetic_coefficients": [r["coefficient"] for r in result.rows],
            "synthetic_denominator": p.denominator,
            "synthetic_domains": list(result.domains),
            "small_kernel_cases": cases,
            "formal_go": False,
            "native_execution": False,
            "hash_adapter_authenticated": False,
            "whole_policy_proof_kernel_example": False,
            "q_values_joined": False,
        },
    )


if __name__ == "__main__":
    generate()
