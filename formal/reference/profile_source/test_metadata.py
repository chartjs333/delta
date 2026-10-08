"""Original-byte, floor and inventory checks. Synthetic metadata, NOT a valid QC/history."""

import copy
import unittest
from dataclasses import replace

from formal.reference.isc_crypto.codec import CodecError
from formal.reference.profile_source import metadata as m


def identifier(label):
    return m.raw_id(label.encode("ascii"))


def ref(raw):
    return {
        "schema_version": "1.0.0",
        "schema_id": "SCHEMA-PROFILE-TEST-V1",
        "media_type": "application/octet-stream",
        "byte_length": str(len(raw)),
        "content_id": m.raw_id(raw),
        "locator": m.raw_id(raw)[7:],
    }


def header(kind):
    return {"type_name": kind, "schema_version": "1", "profile_id": m.PROFILE}


def frame(record):
    raw = m.canonical(record)
    return len(raw).to_bytes(4, "big") + raw + bytes.fromhex(m.document_id(raw, "TRUST_RECORD")[7:])


class Package:
    """Deliberately does not fabricate an authenticated production capture."""

    def __init__(self):
        self.raw = [
            b"genesis",
            b"configuration",
            b"QC",
            b"candidate",
            b"snapshot",
            b"journal",
            b"delivery",
        ]
        self.artifacts = tuple(sorted((m.raw_id(raw), raw) for raw in self.raw))
        self.table = sorted((ref(raw) for raw in self.raw), key=lambda x: x["content_id"])
        self.anchor = {
            "height": "1",
            **{k: identifier(k) for k in ("checkpoint_id", "optimizer_id", "apply_qc_id")},
        }
        self.context = {
            "origin_id": identifier("origin"),
            "validator_epoch_id": identifier("epoch"),
            "local_validator_id": "v0",
        }
        self.boot = {
            **header("BOOTSTRAP"),
            **self.context,
            "genesis_ref": ref(b"genesis"),
            "initial_config_ref": ref(b"configuration"),
            "validators": [
                {"validator_id": f"v{i}", "key_ref": identifier(f"key{i}"), "roles": ["validator"]}
                for i in range(4)
            ],
            "quorum_threshold": "3",
            "initial_anchor": self.anchor,
            **{key: identifier(key) for key in m.PINS},
        }
        self.boot_raw = m.canonical(self.boot)
        self.journals = [
            {
                "actor_id": "v0",
                "journal_id": "consensus",
                "ref": ref(b"journal"),
                "entry_count": "1",
                "first_sequence": "1",
                "last_sequence": "1",
            }
        ]
        self.event = {
            "actor_id": "v1",
            "action_id": "DeliverVoteEnvelope",
            "original_ref": ref(b"delivery"),
            "input_refs": [ref(b"configuration")],
            "dependencies": [],
        }
        self.index = {
            **header("SOURCE_INDEX"),
            **self.context,
            "genesis_ref": ref(b"genesis"),
            "events": [self.event, copy.deepcopy(self.event)],
            "artifacts": self.table,
            "original_journal_refs": self.journals,
        }
        self.index_raw = m.canonical(self.index)
        self.record = {
            **header("TRUST_RECORD"),
            "ordinal": "0",
            "previous_record_id": "GENESIS",
            "bootstrap_id": m.document_id(self.boot_raw, "BOOTSTRAP"),
            "kind": "INIT",
            "anchor": self.anchor,
            "journal_cuts": self.journals,
        }
        self.trust = m.PrimitiveTrust(
            m.raw_id(self.boot_raw),
            m.raw_id(self.index_raw),
            tuple(sorted((key, self.boot[key]) for key in m.PINS)),
            self.boot_raw,
            frame(self.record),
            (("v0", "consensus", b"journal"),),
        )
        self.manifest = {
            **header("MANIFEST"),
            **self.context,
            "bootstrap_id": self.record["bootstrap_id"],
            **{key: self.boot[key] for key in ("formal_semantics_id", "schema_set_id")},
            "anchor": self.anchor,
            "apply_qc_ref": ref(b"QC"),
            "apply_candidate_ref": ref(b"candidate"),
            "snapshot_ref": ref(b"snapshot"),
            "source_index_ref": ref(self.index_raw),
            "cut_event_index": "1",
            "target_event_index": "2",
            "journals": [
                {
                    "actor_id": row["actor_id"],
                    "journal_id": row["journal_id"],
                    "cut": {k: v for k, v in row.items() if k not in ("actor_id", "journal_id")},
                    "target": {k: v for k, v in row.items() if k not in ("actor_id", "journal_id")},
                }
                for row in self.journals
            ],
            "artifacts": self.table,
        }

    def check(self):
        return m.check_metadata(
            self.trust, m.canonical(self.manifest), self.index_raw, self.artifacts
        )

    def activate(self, height="2"):
        updated = {**self.anchor, "height": height, "checkpoint_id": identifier("later")}
        row = {
            **self.record,
            "kind": "ACTIVATE",
            "ordinal": "1",
            "previous_record_id": m.document_id(m.canonical(self.record), "TRUST_RECORD"),
            "anchor": updated,
            "generation_id": identifier("generation"),
            "manifest_id": identifier("manifest"),
        }
        self.trust = replace(self.trust, trusted_log=self.trust.trusted_log + frame(row))
        return row


class MetadataTests(unittest.TestCase):
    def test_retains_originals_and_repeated_deliveries(self):
        p = Package()
        result = p.check()
        self.assertIs(result.original_artifacts, p.artifacts)
        self.assertIs(result.original_own_journals, p.trust.own_journals)
        self.assertEqual(result.source_index_bytes, p.index_raw)
        self.assertEqual(len(m.load(result.source_index_bytes)["events"]), 2)
        self.assertEqual((result.cut, result.target), (1, 2))
        # Metadata acceptance is expressly NOT certificate authentication.
        self.assertIn((m.raw_id(b"QC"), b"QC"), result.original_artifacts)

    def test_import_cannot_select_bootstrap_or_verifier(self):
        for key in m.PINS:
            p = Package()
            p.boot[key] = identifier("attacker-selected")
            p.trust = replace(p.trust, bootstrap=m.canonical(p.boot))
            with self.assertRaisesRegex(CodecError, "bootstrap raw digest"):
                p.check()
            p.trust = replace(p.trust, bootstrap_raw_sha256=m.raw_id(p.trust.bootstrap))
            with self.assertRaisesRegex(CodecError, "approved verifier"):
                p.check()

    def test_cannot_collapse_original_source_occurrences(self):
        p = Package()
        p.index["events"].pop()
        p.index_raw = m.canonical(p.index)
        p.manifest["source_index_ref"] = ref(p.index_raw)
        p.manifest["target_event_index"] = "1"
        with self.assertRaisesRegex(CodecError, "original source inventory"):
            p.check()

    def test_exact_artifacts_not_hash_label_only(self):
        p = Package()
        for altered in (
            p.artifacts[:-1],
            (*p.artifacts, p.artifacts[-1]),
            tuple(reversed(p.artifacts)),
            tuple((key, raw + b"x") for key, raw in p.artifacts),
        ):
            with self.assertRaises(CodecError):
                m.check_metadata(p.trust, m.canonical(p.manifest), p.index_raw, altered)
        p.manifest["snapshot_ref"] = {**p.manifest["snapshot_ref"], "schema_id": "SCHEMA-OTHER-V1"}
        with self.assertRaisesRegex(CodecError, "descriptor"):
            p.check()

    def test_floor_exact_not_old_valid_or_new_unpinned(self):
        p = Package()
        row = p.activate()
        with self.assertRaisesRegex(CodecError, "latest independently trusted floor"):
            p.check()
        p.manifest["anchor"] = row["anchor"]
        self.assertEqual(p.check().floor, row["anchor"])
        p.manifest["anchor"] = {**row["anchor"], "height": "3"}
        with self.assertRaisesRegex(CodecError, "latest independently trusted floor"):
            p.check()

    def test_trusted_tail_never_truncated_or_reset(self):
        p = Package()
        row = p.activate()
        p.manifest["anchor"] = row["anchor"]
        intact = p.trust.trusted_log
        for raw in (
            b"",
            intact + b"x",
            intact[:-1],
            intact[:-32] + b"x" * 32,
            frame(p.record) + frame(p.record),
        ):
            p.trust = replace(p.trust, trusted_log=raw)
            with self.assertRaises(CodecError):
                p.check()

    def test_anchor_prefix_need_not_be_latest_own_vote_tip(self):
        p = Package()
        empty = {"ref": ref(b""), "entry_count": "0", "first_sequence": "0", "last_sequence": "0"}
        p.record["journal_cuts"] = [{"actor_id": "v0", "journal_id": "consensus", **empty}]
        p.trust = replace(p.trust, trusted_log=frame(p.record))
        p.manifest["journals"][0]["cut"] = empty
        result = p.check()
        self.assertEqual(result.original_own_journals[0][2], b"journal")
        p.record["journal_cuts"][0]["ref"] = ref(b"not a prefix")
        p.record["journal_cuts"][0].update(entry_count="1", first_sequence="1", last_sequence="1")
        p.trust = replace(p.trust, trusted_log=frame(p.record))
        with self.assertRaisesRegex(CodecError, "original journal prefix"):
            p.check()

    def test_independent_own_journal_is_not_imported_or_remote(self):
        for own in ((), (("v0", "consensus", b""),), (("v1", "consensus", b"journal"),)):
            p = Package()
            p.trust = replace(p.trust, own_journals=own)
            with self.assertRaises(CodecError):
                p.check()

    def test_canonical_wire_before_typed_construction(self):
        p = Package()
        good = p.index_raw
        bad = [
            good + b"\n",
            b"\xef\xbb\xbf" + good,
            b" " + good,
            good.replace(b'"schema_version":"1"', b'"schema_version":1'),
            good.replace(b'"schema_version":"1"', b'"schema_version":null'),
            b'{"schema_version":"1",' + good[1:],
            good.replace(b'"dependencies":[]', b'"dependencies":["0"]', 1),
        ]
        for raw in bad:
            with self.assertRaises(CodecError):
                m.validate(raw, "SOURCE_INDEX")
        self.assertEqual(m.canonical(m.load(good)), good)

    def test_namespace_counters_are_not_interchanged(self):
        row = Package().journals[0]
        m.cuts([{**row, "first_sequence": "0", "last_sequence": "0"}])
        m.cuts([{**row, "first_sequence": "17", "last_sequence": "17"}])
        with self.assertRaises(CodecError):
            m.cuts([{**row, "first_sequence": "17", "last_sequence": "18"}])
        # Actual native record kind/sequence checks are a required later join.


if __name__ == "__main__":
    unittest.main()
