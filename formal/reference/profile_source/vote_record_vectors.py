"""Original kind-2 receipt join against the same complete static installed state."""

import re
from hashlib import sha256

from formal.reference.isc_w1.codec import Frame, decode_frame, encode_frame
from formal.reference.non_isc.codec import decode_vote
from formal.reference.profile_source.configuration_vectors import bytes_term as bs
from formal.reference.profile_source.installed_state_vectors import generate as installed


def generate():
    source, originals = installed()
    source = source.replace("import ProfileSelectedVote", "import ProfileVoteRecord")
    source = source.replace("InstalledStateVectors", "VoteRecordVectors")
    # Reuse the complete source definitions; the earlier qualifier retains its
    # independent static/fresh guard examples. These checks test the joined row.
    source = re.sub(
        r"^example\b[\s\S]*?(?=^(?:def |end |example |namespace |open |set_option )|\Z)",
        "",
        source,
        flags=re.MULTILINE,
    )
    policy = bytes.fromhex(originals["original_policy"])
    vote = bytes.fromhex(originals["original_vote"])
    preimage = b"deltareduce:003:vote:v2\0" + vote
    record = sha256(policy).hexdigest().encode()
    frame = Frame(1, 2, (vote, b"", b"", record))
    raw_frame = encode_frame(frame)
    assert decode_frame(raw_frame) == frame
    rows = {
        policy: sha256(policy).digest(),
        preimage: sha256(preimage).digest(),
        raw_frame[:-32]: raw_frame[-32:],
    }
    prefix = "def hash (raw : Bytes) : Bytes :=\n"
    assert source.count(prefix) == 1
    source = source.replace(
        prefix,
        prefix
        + "".join(f"  if raw = {bs(raw)} then {bs(digest)} else\n" for raw, digest in rows.items()),
    )
    lines = [
        f"def recordId : Bytes := {bs(record)}",
        "def entry : DeltaReduce.NativeWalBytes.Entry := ⟨1,2,vote,[],[],recordId⟩",
        "def row (previous : Nat) (seen : List Bytes) (e : DeltaReduce.NativeWalBytes.Entry) :=",
        "  VoteRecord.bind hash enrolled actor config state original sv originals "
        "facts previous seen e",
        "example : (row 0 [] entry).map (fun r => "
        "(r.receipt.frame,r.receipt.sequence,r.receipt.action))",
        "  = some (vote,1,1) := by decide +kernel",
        "example : (row 1 [] entry).isNone = true := by decide +kernel",
        "example : (row 0 [] {entry with kind := 3}).isNone = true := by decide +kernel",
        "example : (row 0 [] {entry with record := []}).isNone = true := by decide +kernel",
        "example : (row 0 [] {entry with state := state}).isNone = true := by decide +kernel",
        f"def context : Bytes := {bs(decode_vote(vote).original.context_id.encode())}",
        "example : (row 0 [context] entry).isNone = true := by decide +kernel",
        f"def originalWal : Bytes := {bs(raw_frame)}",
        "def fromWal (raw : Bytes) := VoteRecord.fromBytes hash enrolled actor "
        "config state original",
        "  sv originals facts 0 [] raw",
        "example : (fromWal originalWal).map (fun r => r.bound.receipt.frame) = some vote",
        "  := by decide +kernel",
        "example : (fromWal (originalWal ++ [0])).isNone = true := by decide +kernel",
        f"def alteredWal : Bytes := {bs(raw_frame[:-1] + bytes([raw_frame[-1] ^ 1]))}",
        "example : (fromWal alteredWal).isNone = true := by decide +kernel",
        "end VoteRecordVectors",
    ]
    source = source.replace("end VoteRecordVectors\n", "\n".join(lines) + "\n")
    originals = {
        **originals,
        "evidence_kind": "SYNTHETIC_ORIGINAL_VOTE_ROW_NOT_PRODUCER_HISTORY",
        "policy_record_id": record.decode(),
        "vote_id": "sha256:" + sha256(preimage).hexdigest(),
        "original_wal": raw_frame.hex(),
        "extra_sha256_preimages": {raw.hex(): hashed.hex() for raw, hashed in rows.items()},
    }
    return source, originals
