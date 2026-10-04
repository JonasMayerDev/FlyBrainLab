import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from simulation.experiment import DESIGN_PATH, load_design, outgoing_mask, readout_metrics, summarize


class ExperimentIntegrityTests(unittest.TestCase):
    def test_sealed_targets_exist_and_stimulus_readout_do_not_overlap(self):
        design, digest = load_design()
        neurons = pd.read_csv(DESIGN_PATH.parents[2] / "data/brain/flywire783/Completeness_783.csv", index_col=0)
        installed = set(map(str, neurons.index))
        self.assertTrue(set(design["stimulus_ids"] + design["readout_ids"]) <= installed)
        self.assertFalse(set(design["stimulus_ids"]) & set(design["readout_ids"]))
        self.assertEqual(len(digest), 64)

    def test_modified_plan_cannot_run_with_previous_seal(self):
        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "design.json"
            copy.write_text(DESIGN_PATH.read_text() + " ")
            copy.with_suffix(".sha256").write_text(DESIGN_PATH.with_suffix(".sha256").read_text())
            with self.assertRaisesRegex(ValueError, "seal"):
                load_design(copy)

    def test_only_outgoing_source_edges_are_cut(self):
        pre = np.asarray([1, 2, 3, 1, 5])
        np.testing.assert_array_equal(outgoing_mask(pre, [1, 3]), [True, False, True, True, False])

    def test_population_rate_includes_silent_neurons(self):
        spikes = pd.DataFrame({"flywire_id": ["left-a", "left-a", "stimulus"]})
        metrics = readout_metrics(spikes, ["left-a", "left-b", "right-a"],
                                  {"left": ["left-a", "left-b"], "right": ["right-a"]}, ["stimulus"], 200)
        self.assertAlmostEqual(metrics["population_mean_rate_hz"], 2 / 0.6)
        self.assertEqual(metrics["group_mean_rate_hz"], {"left": 5.0, "right": 0.0})
        self.assertEqual(metrics["nonstimulated_active_neurons"], 1)

    def test_null_result_selects_calibration_and_keeps_raw_pairs(self):
        records = [{"condition": condition, "seed": seed,
                    "readout_metrics": {"population_mean_rate_hz": 0.0}}
                   for seed in [42, 43, 44] for condition in ["sham", "upstream_drive"]]
        summary = summarize(records, "A", {"seeds": [42, 43, 44]})
        self.assertFalse(summary["supports_model_hypothesis"])
        self.assertEqual(summary["next_test"], "calibration")
        self.assertEqual(summary["paired_difference_hz"], [0.0, 0.0, 0.0])


if __name__ == "__main__":
    unittest.main()
