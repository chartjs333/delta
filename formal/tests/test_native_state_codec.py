"""Source-pinned concrete native state/command codecs, not transition authority."""

import copy
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_state_vectors as codec  # noqa: E402
from native_policy_wal import wal_entries  # noqa: E402


class NativeStateCodecTests(unittest.TestCase):
    def test_exact_reproduction(self):
        with tempfile.TemporaryDirectory() as d:
            lean, target = Path(d) / "vectors.lean", Path(d) / "vectors.json"
            with mock.patch.object(codec, "LEAN", lean), mock.patch.object(codec, "TARGET", target):
                codec.generate()
            self.assertEqual(lean.read_bytes(), codec.LEAN.read_bytes())
            self.assertEqual(target.read_bytes(), codec.TARGET.read_bytes())

    def test_original_wal_fields_and_sequences(self):
        row = codec.wal.load()["after-state-command-retry"]
        entries = wal_entries(bytes.fromhex(row["wal_hex"]))
        rows = codec.original()
        self.assertEqual(rows[0][2], entries[1]["command"])
        self.assertEqual(rows[1][2], entries[1]["state"])
        self.assertEqual(rows[2][2].hex(), row["initial_state_hex"])
        self.assertEqual(entries[1]["sequence"], 2)
        self.assertEqual(rows[1][3]["durable_sequence"], "1")

    def test_native_observations(self):
        data = json.loads((codec.FOLDER / "cpp-cross-check.json").read_bytes())
        rows = codec.validate(data)
        self.assertEqual(len(rows), 55)
        self.assertEqual(sum(r["accepted"] for r in rows), 12)
        changed = copy.deepcopy(data)
        changed["observed"][0]["accepted"] = False
        with self.assertRaisesRegex(ValueError, "native codec mismatch"):
            codec.validate(changed)

    def test_command_bounds_and_constants(self):
        _, kind, _, fields = codec.original()[0]
        for key, value in [
            ("height", "00"),
            ("logical_tick", "18446744073709551616"),
            ("actor_id", ""),
            ("formal_semantics_id", "sha256:" + "0" * 64),
        ]:
            changed = dict(fields, **{key: value})
            with self.assertRaises(ValueError):
                codec.decode_command(codec.envelope(kind, sorted(changed.items())))
        fields["command_kind"] = "UNKNOWN_COMMAND"
        self.assertEqual(codec.decode_command(codec.envelope(kind, sorted(fields.items()))), fields)

    def test_state_bounds_and_admission_gap(self):
        _, kind, _, fields = codec.original()[1]
        for key, value in [
            ("ticket_count", 2**32),
            ("ticket_count", "1"),
            ("available_ticket_count", 2),
            ("phase", "UNKNOWN"),
        ]:
            with self.assertRaises(ValueError):
                codec.decode_state(
                    codec.envelope(kind, sorted(dict(fields, **{key: value}).items()))
                )
        fields["state_root"] = "sha256:" + "0" * 64
        self.assertEqual(codec.decode_state(codec.envelope(kind, sorted(fields.items()))), fields)

    def test_forged_source_metadata_rejects(self):
        original = json.loads((codec.FOLDER / "cpp-cross-check.json").read_bytes())
        for key, value in [
            ("source_commit", "0" * 40),
            ("source_sha256", {}),
            ("compiler_flags", "/O2"),
        ]:
            changed = dict(original, **{key: value})
            with self.assertRaisesRegex(ValueError, "native source|native compile"):
                codec.validate(changed)

    def test_substituted_original_rejects_before_output(self):
        with tempfile.TemporaryDirectory() as d:
            source, output = Path(d) / "source.json", Path(d) / "new.lean"
            source.write_bytes(b"{}")
            with (
                mock.patch.object(codec.wal, "SOURCE", source),
                mock.patch.object(codec, "LEAN", output),
            ):
                with self.assertRaisesRegex(ValueError, "retained native WAL evidence changed"):
                    codec.generate()
            self.assertFalse(output.exists())

    def test_mandatory_modules_and_native_field_inventory(self):
        project = (ROOT / "formal/proofs/DeltaReduce.lean").read_text()
        audit = (ROOT / "formal/proofs/DeltaReduce/AxiomAudit.lean").read_text()
        for module in ["NativeStateBytes", "NativeStateCodecVectors"]:
            self.assertIn("import DeltaReduce." + module, project)
            source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text()
            for name in re.findall(r"^(?:def|abbrev|theorem) ([\w.]+)", source, re.M):
                self.assertIn("#print axioms DeltaReduce." + module + "." + name, audit)
        source = (ROOT / "formal/proofs/DeltaReduce/NativeStateBytes.lean").read_text()
        native = codec.vote.previous.wal.sources()["delta-core-cpp/src/protocol.cpp"].decode()
        for name, expected in [
            ("commandFields", codec.COMMAND_FIELDS),
            ("stateFields", codec.decode_state(codec.original()[1][2]).keys()),
        ]:
            body = source.split("def " + name, 1)[1].split("\ndef ", 1)[0]
            keys = re.findall(r'\(ascii "([a-z_]+)"', body)
            self.assertEqual(keys, sorted(expected))
            signature = (
                "Command parse_command("
                if name == "commandFields"
                else "RoundState parse_round_state("
            )
            fields = native.split(signature, 1)[1].split("require_fields", 1)[0]
            self.assertEqual(re.findall(r'std::string_view\{"([a-z_]+)"\}', fields), keys)


if __name__ == "__main__":
    unittest.main()
