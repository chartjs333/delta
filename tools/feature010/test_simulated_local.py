"""Security boundary tests for non-promotable local simulation evidence."""

from __future__ import annotations

import base64
import copy
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import simulated_local as sim


class SimulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.folder = Path(cls.temporary.name)
        cls.identities = []
        cls.keys = []
        for index, controller in enumerate(sim.CONTROLLERS):
            key = cls.folder / f"key-{index}"
            public = cls.folder / f"public-{index}"
            sim.execute(["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(key)])
            sim.execute(
                [
                    "openssl",
                    "pkey",
                    "-in",
                    str(key),
                    "-pubout",
                    "-outform",
                    "DER",
                    "-out",
                    str(public),
                ]
            )
            cls.keys.append(key)
            cls.identities.append(
                {
                    "controller": controller,
                    "generation": f"{index:032x}",
                    "mode": sim.MODE,
                    "public_key_der": base64.b64encode(public.read_bytes()).decode(),
                }
            )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def setUp(self) -> None:
        self.body = {
            "mode": sim.MODE,
            "run_id": "sim-" + "a" * 32,
            "phase": "all-online",
            "purpose": "SIMULATED_INFRASTRUCTURE_ATTESTATION",
            "source_id": "sha256:" + "b" * 64,
        }
        self.votes = []
        for key, identity in zip(self.keys, self.identities, strict=True):
            message = self.folder / "message"
            signature = self.folder / "signature"
            message.write_bytes(
                sim.signing_message(self.body, identity["controller"], identity["generation"])
            )
            sim.execute(
                [
                    "openssl",
                    "pkeyutl",
                    "-sign",
                    "-inkey",
                    str(key),
                    "-rawin",
                    "-in",
                    str(message),
                    "-out",
                    str(signature),
                ]
            )
            self.votes.append(
                {
                    "controller": identity["controller"],
                    "generation": identity["generation"],
                    "body_id": sim.digest(sim.canonical(self.body)),
                    "signature": signature.read_bytes().hex(),
                }
            )

    def test_three_of_four_and_insufficient_quorum(self) -> None:
        self.assertTrue(sim.verify_attestations(self.body, self.identities, self.votes[:3]))
        self.assertFalse(sim.verify_attestations(self.body, self.identities, self.votes[:2]))

    def test_duplicate_signers_do_not_supply_quorum(self) -> None:
        with self.assertRaisesRegex(sim.SimulationError, "DUPLICATE"):
            sim.verify_attestations(self.body, self.identities, [self.votes[0]] * 3)

    def test_same_key_cannot_count_as_separate_identity(self) -> None:
        identities = copy.deepcopy(self.identities)
        identities[1]["public_key_der"] = identities[0]["public_key_der"]
        with self.assertRaisesRegex(sim.SimulationError, "KEY_REUSE"):
            sim.verify_attestations(self.body, identities, self.votes)

    def test_modified_body_rejected_even_with_same_source(self) -> None:
        with self.assertRaisesRegex(sim.SimulationError, "BODY_MISMATCH"):
            sim.verify_attestations(dict(self.body, phase="one-lost"), self.identities, self.votes)

    def test_tampered_signature_rejected(self) -> None:
        votes = copy.deepcopy(self.votes)
        votes[0]["signature"] = "00" * 64
        with self.assertRaisesRegex(sim.SimulationError, "SIGNATURE_INVALID"):
            sim.verify_attestations(self.body, self.identities, votes)

    def test_stale_generation_rejected(self) -> None:
        identities = copy.deepcopy(self.identities)
        identities[0]["generation"] = "f" * 32
        with self.assertRaisesRegex(sim.SimulationError, "STALE_GENERATION"):
            sim.verify_attestations(self.body, identities, self.votes)

    def test_production_and_runtime_signing_purposes_forbidden(self) -> None:
        for purpose in ("BENCHMARK_RESULT_VOTE", "BENCHMARK_DEFINITION_VOTE", "ACT-APPLY-VOTE"):
            with self.subTest(purpose=purpose), self.assertRaises(sim.SimulationError):
                sim.signing_message(dict(self.body, purpose=purpose), sim.CONTROLLERS[0], "0" * 32)

    def test_mode_relabel_and_extra_field_forbidden(self) -> None:
        for body in (dict(self.body, mode="REAL_WAN"), dict(self.body, gate_eligible=True)):
            with self.assertRaises(sim.SimulationError):
                sim.validate_body(body)

    def test_noncanonical_wire_input_forbidden(self) -> None:
        for encoded in (b'{"x":1,"x":2}', b'{"x": 1}', b'{"x":1.0}', b'{"x":NaN}'):
            with self.subTest(encoded=encoded), self.assertRaises(ValueError):
                sim.decode(encoded)

    def test_no_qualification_in_plan(self) -> None:
        self.assertFalse(sim.boundaries()["gate_eligible"])
        self.assertFalse(sim.boundaries()["feature011_admitted"])
        self.assertIsNone(sim.boundaries()["benchmark_result_qc"])
        self.assertIsNone(sim.boundaries()["feature010_go_checkpoint_sha"])


@unittest.skipUnless(os.environ.get("SIM_LOCAL_EVIDENCE"), "requires executed Docker evidence")
class ExecutedEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name) / "evidence"
        shutil.copytree(os.environ["SIM_LOCAL_EVIDENCE"], self.folder)

    def mutate(self, name: str, edit: object) -> None:
        path = self.folder / name
        document = sim.decode(path.read_bytes())
        edit(document)
        path.write_bytes(sim.canonical(document))

    def test_executed_evidence_verifies_offline(self) -> None:
        expected = (self.folder / "report.json").read_bytes()
        self.assertEqual(sim.canonical(sim.verify_bundle(self.folder)), expected)

    def test_phase_promotion_rejected(self) -> None:
        self.mutate("all-online.json", lambda doc: doc.update(gate_eligible=True))
        with self.assertRaisesRegex(sim.SimulationError, "PROMOTION_FORBIDDEN"):
            sim.verify_bundle(self.folder)

    def test_real_wan_relabel_rejected(self) -> None:
        self.mutate("all-online.json", lambda doc: doc.update(network="REAL_WAN"))
        with self.assertRaisesRegex(sim.SimulationError, "NETWORK_RELABEL"):
            sim.verify_bundle(self.folder)

    def test_manifest_integer_false_is_rejected(self) -> None:
        self.mutate("manifest.json", lambda doc: doc["boundaries"].update(gate_eligible=0))
        with self.assertRaisesRegex(sim.SimulationError, "MANIFEST_PROMOTION_FORBIDDEN"):
            sim.verify_bundle(self.folder)

    def test_source_replacement_rejected(self) -> None:
        (self.folder / "runner.py").write_bytes(b"changed")
        with self.assertRaisesRegex(sim.SimulationError, "SOURCE_BYTES_MISMATCH"):
            sim.verify_bundle(self.folder)

    def test_two_voters_cannot_be_reported_as_quorum(self) -> None:
        self.mutate("two-lost.json", lambda doc: doc.update(simulated_quorum_present=True))
        with self.assertRaisesRegex(sim.SimulationError, "QUORUM_BINDING"):
            sim.verify_bundle(self.folder)

    def test_extra_authority_field_is_rejected(self) -> None:
        self.mutate("all-online.json", lambda doc: doc.update(decision="GO"))
        with self.assertRaisesRegex(sim.SimulationError, "REPORT_FIELDS"):
            sim.verify_bundle(self.folder)

    def test_observation_duplicate_rejected(self) -> None:
        def duplicate(document: dict) -> None:
            document["observations"][1] = document["observations"][0]

        self.mutate("all-online.json", duplicate)
        with self.assertRaisesRegex(sim.SimulationError, "OBSERVATION_IDENTITY"):
            sim.verify_bundle(self.folder)


if __name__ == "__main__":
    unittest.main()
