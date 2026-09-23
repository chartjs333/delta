"""Verify the exact Python file displayed/downloaded by the SDK page."""

import importlib.util
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np
from deltatorrent.data.base import ContractCompatibilityError
from deltatorrent.model_plugins.runner import (
    ModelPluginRunnerError,
    validate_model_dataset_capability,
)

SOURCE = Path(__file__).resolve().parents[1] / "admin-ui/src/modules/sdk/sdk_plugin_example.py"
spec = importlib.util.spec_from_file_location("sdk_example", SOURCE)
example = importlib.util.module_from_spec(spec)
spec.loader.exec_module(example)


class SdkExampleTests(unittest.TestCase):
    def test_real_registries_training_and_held_out_evaluation(self):
        runner = example.build_runner()
        trained = runner.train_ticket(ticket_id="sdk-ticket-01", partition_id="train-0")
        np.testing.assert_array_equal(trained.tensors["centroids"], [-3, 3])
        result = runner.evaluate(runner.model_plugin.create_model(trained.tensors["centroids"]))
        self.assertEqual(result.accuracy_ppm, 1_000_000)
        self.assertEqual(result.metrics, {"correct": 4, "total": 4})
        self.assertEqual(
            runner.model_plugin.parameter_schema().fingerprint, example.MODEL.parameter_schema_id
        )
        np.testing.assert_array_equal(runner.model_plugin.load_applied_checkpoint([-3, 3]), [-3, 3])

    def test_invalid_partition_samples_labels_and_checkpoint_are_rejected(self):
        plugin = example.CentroidPlugin()
        with self.assertRaisesRegex(ValueError, "UNKNOWN_PARTITION"):
            example.PointsProvider().training_partition("missing")
        for data in (([[float("nan")]], [0]), ([[1]], [2]), ([[1]], [0.5]), ([[1]], [0])):
            with self.subTest(data=data), self.assertRaises(ValueError):
                plugin.train_ticket(ticket_id="t", data=data)
        with self.assertRaisesRegex(ValueError, "INTEGER_COORDINATES_REQUIRED"):
            plugin.load_applied_checkpoint([1.5, 2])

    def test_contract_mismatch_and_consensus_scope_fail_closed(self):
        with self.assertRaises(ContractCompatibilityError):
            validate_model_dataset_capability(
                model_descriptor=example.MODEL,
                dataset_descriptor=replace(example.DATA, sample_kind="wrong"),
                requested_scope="PLUGIN_BOUNDARY",
            )
        with self.assertRaises(ModelPluginRunnerError):
            validate_model_dataset_capability(
                model_descriptor=example.MODEL,
                dataset_descriptor=example.DATA,
                requested_scope="STAGE_C_REAL_DRQ1",
            )
