"""Mixed original journal/context vectors; not candidate or producer authority."""

from dataclasses import replace

from formal.reference.isc_crypto import codec as c
from formal.reference.non_isc import codec as n
from formal.reference.profile_source.configuration_vectors import bytes_term
from formal.reference.profile_source.test_votes import VoteIntentTests
from formal.reference.profile_source.vote_vectors import wire_term


def generate():
    VoteIntentTests.setUpClass()
    f = VoteIntentTests()
    f.setUp()
    first = n.decode_vote(f.first)
    second = replace(first.original, durable_sequence=4, context_id="sha256:" + "6" * 64)
    last = n.encode_vote(n.NonIscVote(second, first.kind))
    journal = f.journal(last)
    result = f.check(journal, ())
    assert [i.public_ordinal for i in result] == [1, 2]
    assert [i.original_vote for i in result] == [f.first, last]
    lines = [
        "import ProfileVoteJournal",
        "open DeltaReduce.ProfileSource",
        "open DeltaReduce.NativeReceiptBytes (Bytes)",
        "open DeltaReduce.NativeVoteBytes (ascii)",
        "set_option maxRecDepth 20000",
        "set_option maxHeartbeats 4000000",
        "namespace JournalVectors",
    ]
    for i, item in enumerate(result):
        vote = item.vote
        lines.extend(
            (
                f"def w{i} : Vote.WireVote := {wire_term(item.kind, vote)}",
                f"def v{i} : Vote.Vote := ⟨w{i},{vote.durable_sequence},{vote.height},{vote.view}⟩",
            )
        )
    for i, position in enumerate(journal.positions):
        frame = position.decoded
        if frame.kind == 3:
            # The existing Entry carrier has four sections, while the kind-3
            # framing is qualified separately. Its whole raw frame is retained
            # in the non-vote command carrier, not accepted as a kind-2 payload.
            sections = (position.original, b"", b"", b"")
        else:
            sections = frame.sections
        values = ",".join(bytes_term(raw) for raw in sections)
        lines.append(
            f"def e{i} : DeltaReduce.NativeWalBytes.Entry := "
            f"⟨{frame.sequence},{frame.kind},{values}⟩"
        )
    lines.extend(
        (
            "def originals := [e0,e1,e2,e3]",
            "def intents : List Journal.Intent := [⟨e1,v0,1⟩,⟨e3,v1,2⟩]",
            "theorem scanned : Journal.scan w0.semantics w0.epoch w0.validator [] 0 originals = "
            "some intents := by decide +kernel",
            "example : intents.map Journal.Intent.entry = "
            "originals.filter (fun e => e.kind == 2) := "
            "Journal.originalEntries (Journal.sound scanned)",
            "example : intents[0]?.map Journal.Intent.ordinal = some 1 := rfl",
            "example : intents[1]?.map Journal.Intent.ordinal = some 2 := rfl",
            "example : Journal.scan w0.semantics w0.epoch w0.validator [] 0 "
            "[e0,{e1 with sequence := 1},e2,e3] = none := by decide +kernel",
            "example : Journal.scan w0.semantics w0.epoch w0.validator [] 0 "
            "[{e0 with kind := 4}] = none := by decide +kernel",
        )
    )
    bad_originals = []
    for i, (kind, changed) in enumerate(
        [
            (first.kind, replace(first.original, durable_sequence=4)),
            (first.kind, replace(first.original, durable_sequence=4, round_id="other")),
            (first.kind, replace(first.original, durable_sequence=4, view=1)),
            (first.kind, replace(first.original, durable_sequence=4, height=2)),
            ("EC", replace(first.original, durable_sequence=4)),
        ]
    ):
        raw = n.encode_vote(n.NonIscVote(changed, kind))
        try:
            f.check(f.journal(raw), ())
        except c.CodecError:
            pass
        else:
            raise AssertionError("Second original slot reopened native vote key")
        lines.extend(
            (
                f"def bad{i} : Bytes := {bytes_term(raw)}",
                "example : Journal.scan w0.semantics w0.epoch w0.validator [] 0 "
                f"[e0,e1,e2,{{e3 with command := bad{i}}}] = none := by decide +kernel",
            )
        )
        bad_originals.append({"kind": kind, "original_vote_hex": raw.hex()})
    lines.append("end JournalVectors")
    return "\n".join(lines) + "\n", {
        "original_journal_hex": journal.original.hex(),
        "signed_physical_slots": [2, 4],
        "public_ordinals": [1, 2],
        "same_context_second_slots": bad_originals,
        "not_established": "candidate admission, kind1/3 permission, barriers or producer origin",
    }
