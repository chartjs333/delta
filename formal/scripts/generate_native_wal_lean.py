"""Generate DRW1 kernel examples from retained native WAL bytes; no new native run."""

import hashlib
import json
from pathlib import Path

from formal_artifacts import sha256_file, write_canonical_json
from native_policy_wal import bind_vote_entry, receipt, wal_entries

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
PIN = "d82c14dda8356bfebc1cc1febe3c2fd09c3393b467cc99bacd565b506a91d2ea"
LEAN = ROOT / "formal/proofs/DeltaReduce/NativeWalVectors.lean"
TARGET = ROOT / "formal/proposals/native-wal-vectors.json"


def load():
    if sha256_file(SOURCE) != PIN:
        raise ValueError("retained native WAL evidence changed")
    rows = {r["name"]: r for r in json.loads(SOURCE.read_bytes())["observed"]}
    for name in ["record", "after-state-command-retry"]:
        row = rows[name]
        entries = wal_entries(bytes.fromhex(row["wal_hex"]))
        bind_vote_entry(entries[0], bytes.fromhex(row["policy_hex"]))
        decoded = receipt(bytes.fromhex(row["receipt_hex"]))
        if entries[0]["command"] != decoded["frame"] or decoded["sequence"] != 1:
            raise ValueError("original receipt/frame/sequence differs")
    if rows["record"]["receipt_hex"] != rows["after-state-command-retry"]["receipt_hex"]:
        raise ValueError("historical retry changed receipt")
    for name in [
        "crash-durable-uncommitted",
        "crash-committed-unreturned",
        "crash-copied-unreturned",
    ]:
        if rows[name]["wal_hex"] != rows["record"]["wal_hex"] or rows[name]["receipt_hex"]:
            raise ValueError("unexposed surviving record mismatch")
    return rows


def lit(raw):
    return "[" + ",".join(map(str, raw)) + "]"


def generate():
    rows = load()
    lines = [
        "import DeltaReduce.NativeWalBytes",
        "import DeltaReduce.NativeVoteCodecVectors",
        "set_option maxRecDepth 8192",
        "set_option maxHeartbeats 1000000",
        "namespace DeltaReduce.NativeWalVectors",
        "open NativeReceiptBytes NativeWalBytes",
    ]
    data = []
    for i, (name, index) in enumerate(
        [("record", 0), ("after-state-command-retry", 0), ("after-state-command-retry", 1)], 1
    ):
        row = rows[name]
        stream = bytes.fromhex(row["wal_hex"])
        entries = wal_entries(stream)
        offset = 0
        frames = []
        while offset < len(stream):
            size = int.from_bytes(stream[offset + 8 : offset + 12], "big")
            frames.append(stream[offset : offset + size])
            offset += size
        raw, e = frames[index], entries[index]
        for field in ["command", "state", "effects", "record"]:
            value = (
                "NativeReceiptVectors.frame2"
                if field == "command" and index == 0
                else lit(e[field])
            )
            lines.append(f"def {field}{i} : Bytes := {value}")
        lines += [
            f"def entry{i} : Entry := "
            f"⟨{e['sequence']},{e['kind']},command{i},state{i},effects{i},record{i}⟩",
            f"def rawPrefix{i} : Bytes := "
            + lit(raw[:28])
            + f" ++ command{i} ++ "
            + lit(len(e["state"]).to_bytes(4, "big"))
            + f" ++ state{i} ++ "
            + lit(len(e["effects"]).to_bytes(4, "big"))
            + f" ++ effects{i} ++ "
            + lit(len(e["record"]).to_bytes(4, "big"))
            + f" ++ record{i}",
            f"def digest{i} : Bytes := {lit(raw[-32:])}",
            f"def raw{i} : Bytes := rawPrefix{i} ++ digest{i}",
            f"theorem valid{i} : NativeWalBytes.Valid entry{i} := by decide",
            f"theorem preimage{i} : preimage entry{i} = rawPrefix{i} := by rfl",
        ]
        if index == 0:
            policy = bytes.fromhex(row["policy_hex"])
            lines += [
                f"def policy{i} : Bytes := {lit(policy)}",
                f"def policyDigest{i} : Bytes := {lit(hashlib.sha256(policy).digest())}",
                f"def sha{i} (b : Bytes) : Bytes := if b = rawPrefix{i} then digest{i} "
                f"else if b = policy{i} then policyDigest{i} else "
                f"NativeVoteCodecVectors.fixtureSHA2 b",
            ]
        else:
            lines.append(
                f"def sha{i} (b : Bytes) : Bytes := if b = rawPrefix{i} then digest{i} else []"
            )
        lines += [
            f"theorem digestSize{i} : (sha{i} (preimage entry{i})).length = 32 := "
            f"by rw [preimage{i}]; rfl",
            f"theorem exact{i} : NativeWalBytes.encode sha{i} entry{i} = raw{i} := by",
            f"  unfold NativeWalBytes.encode; rw [preimage{i}]; rfl",
            f"theorem decoded{i} : NativeWalBytes.decode sha{i} raw{i} = some entry{i} :=",
            f"  decodeFromBytes sha{i} entry{i} raw{i} valid{i} digestSize{i} exact{i}",
        ]
        if index == 0:
            lines += [
                f"theorem policyBound{i} : policyId sha{i} policy{i} = some record{i} := by decide",
                f"theorem voteHash{i} : NativeVoteBytes.voteId sha{i} "
                f"NativeReceiptVectors.frame2 = some "
                f"NativeReceiptVectors.receipt2.voteId := by decide",
                f"theorem receiptLinked{i} : NativeVoteBytes.ReceiptLinked sha{i} "
                f"NativeReceiptVectors.receipt2 NativeVoteCodecVectors.vote2 :=",
                f"  ⟨rfl,rfl,rfl,voteHash{i}⟩",
                f"theorem semanticReceipt{i} : NativeVoteBytes.decodeReceipt "
                f"sha{i} NativeReceiptVectors.nativeBytes2 = some "
                f"(NativeReceiptVectors.receipt2,NativeVoteCodecVectors.vote2) := by",
                f"  have bound := NativeVoteBytes.bindingFromComponents sha{i} "
                f"NativeReceiptVectors.receipt2 NativeVoteCodecVectors.vote2 "
                f"NativeVoteCodecVectors.parsed2 receiptLinked{i}",
                f"  exact NativeVoteBytes.receiptFromNativeBytes sha{i} "
                f"NativeReceiptVectors.receipt2 NativeVoteCodecVectors.vote2 "
                f"NativeReceiptVectors.nativeBytes2 NativeReceiptVectors.valid2 "
                f"bound NativeReceiptVectors.exactBytes2",
                f"theorem link{i} : ReceiptLink sha{i} policy{i} entry{i} "
                f"NativeReceiptVectors.receipt2 := ⟨rfl,rfl,rfl,rfl,rfl,policyBound{i}⟩",
                f"theorem fullBinding{i} : NativeWalBytes.bindReceipt sha{i} "
                f"policy{i} raw{i} NativeReceiptVectors.nativeBytes2 = some "
                f"(entry{i},NativeReceiptVectors.receipt2,NativeVoteCodecVectors.vote2) :=",
                f"  bindFromComponents sha{i} policy{i} raw{i} "
                f"NativeReceiptVectors.nativeBytes2 entry{i} "
                f"NativeReceiptVectors.receipt2 NativeVoteCodecVectors.vote2 "
                f"decoded{i} semanticReceipt{i} link{i}",
            ]
        data.append(
            {
                "name": name,
                "index": index,
                "sequence": e["sequence"],
                "kind": e["kind"],
                "frame_hex": raw.hex(),
            }
        )
    lines += [
        "theorem allEntriesOrdered : orderedFrom 1 [entry2,entry3] = true := by decide",
        "theorem reorderedRejects : orderedFrom 1 [entry3,entry2] = false := by decide",
        "theorem missingEntryRejects : orderedFrom 1 [entry3] = false := by decide",
        "theorem repeatedEntryRejects : orderedFrom 1 [entry2,entry2] = false := by decide",
        "theorem gapRejects : orderedFrom 1 [entry2,{entry3 with sequence := 3}] "
        "= false := by decide",
        "theorem retryKeepsOriginalSequence : entry2.sequence = 1 ∧ "
        "entry3.sequence = 2 := by decide",
        "def tiny : Entry := ⟨0,2,[1],[],[],[]⟩",
        "def tinySHA (_ : Bytes) : Bytes := List.replicate 32 0",
        "theorem structuralZeroSequenceAccepted : NativeWalBytes.decode tinySHA "
        "(NativeWalBytes.encode tinySHA tiny) = some tiny :=",
        "  decodeEncoded tinySHA tiny (by decide) (by decide)",
        "theorem zeroSequenceRuntimeRejects : orderedFrom 1 [tiny] = false := by decide",
        "theorem emptyPolicyStructurallyAllowed : Shape tiny := by decide",
        "theorem emptyPolicyCannotBindReceipt : ¬ ReceiptLink tinySHA [] tiny "
        "NativeReceiptVectors.receipt2 := by decide",
        "theorem shortWrongMagicIsTorn : scanHead tinySHA [0] = .torn := by decide",
        "theorem emptyScanDone : scanHead tinySHA [] = .done := by decide",
        "theorem fullWrongMagicCorrupt : scanHead tinySHA (List.replicate 12 0) "
        "= .corrupt := by decide",
        "theorem sizeTooSmallCorrupt : scanHead tinySHA (NativeWalBytes.header "
        "++ be 4 71) = .corrupt := by decide",
        "theorem sizeTooLargeCorrupt : scanHead tinySHA (NativeWalBytes.header "
        "++ be 4 (64*1024*1024+1)) = .corrupt := by decide",
        "theorem declaredMissingBodyTorn : scanHead tinySHA "
        "(NativeWalBytes.header ++ be 4 72) = .torn := by decide",
        "theorem voteStateForbidden : ¬ Shape {tiny with state := [1]} := by decide",
        "theorem voteEffectsForbidden : ¬ Shape {tiny with effects := [1]} := by decide",
        "theorem missingCommandForbidden : ¬ Shape {tiny with command := []} := by decide",
        "theorem unknownKindForbidden : ¬ Shape {tiny with kind := 3} := by decide",
        "theorem transitionMissingRecordForbidden : ¬ Shape ⟨1,1,[1],[2],[3],[]⟩ := by decide",
        "theorem badChecksumRejects : NativeWalBytes.decode (fun _ => []) "
        "(NativeWalBytes.encode tinySHA tiny) = none := by decide",
        "theorem policyLengthDifferentFromVoteId : (NativeVoteBytes.hexBytes "
        "(List.replicate 32 0)).length = 64 := by decide",
        "end DeltaReduce.NativeWalVectors",
    ]
    LEAN.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    write_canonical_json(
        TARGET,
        {
            "status": "PASS_RETAINED_NATIVE_BYTES_AND_CONDITIONAL_CODEC",
            "native_evidence_sha256": PIN,
            "new_native_execution": False,
            "native_export_authenticated": False,
            "gate_eligible": False,
            "hash_adapter": "FINITE_EXACT_PREIMAGE_LOOKUP_NOT_SHA_PROOF",
            "full_native_recovery": False,
            "entries": data,
            "unexposed_complete_records": 3,
            "known_partial_scan": "TORN_NOT_PROOF_OF_AUTHENTICATED_ABSENCE",
        },
    )


if __name__ == "__main__":
    generate()
