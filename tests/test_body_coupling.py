"""Contract tests for causal replay and honest source validation."""
import unittest
import json
from pathlib import Path
import tempfile

from simulation.coupling import SpikeAmplitudeAdapter, canonical_digest, load_adapter
from simulation.body import sha256


class BodyCouplingContractTests(unittest.TestCase):
    def setUp(self):
        self.spec = {"readout_ids": ["1", "2"], "window_ms": 10.,
                     "reference_rate_hz": 100., "maximum_fractional_amplitude_increase": 0.1}

    def export(self, times):
        return {"events_are_complete": True, "readout_neuron_ids": ["1", "2"],
                "duration_ms": 200., "events": [{"t_seconds": t, "flywire_id": "1"} for t in times]}

    def test_trailing_window_is_causal_and_half_open(self):
        adapter = SpikeAmplitudeAdapter(self.spec, self.export([0.005, 0.010, 0.020]))
        self.assertEqual(adapter.update(0.005), (0., 1.))
        rate, factor = adapter.update(0.010)
        self.assertEqual(rate, 50.)  # Spike at exactly current t is not visible yet.
        self.assertAlmostEqual(factor, 1.05)
        self.assertEqual(adapter.update(0.020), (50., 1.05))

    def test_saturation_and_zero_signal(self):
        active = SpikeAmplitudeAdapter(self.spec, self.export([0.005] * 100))
        self.assertEqual(active.update(0.006)[1], 1.1)
        sham = SpikeAmplitudeAdapter(self.spec, self.export([]))
        self.assertEqual(sham.update(0.1), (0., 1.))

    def test_capped_preview_and_wrong_readout_rejected(self):
        capped = self.export([])
        capped["events_are_complete"] = False
        with self.assertRaises(ValueError):
            SpikeAmplitudeAdapter(self.spec, capped)
        wrong = self.export([])
        wrong["readout_neuron_ids"] = ["1", "3"]
        with self.assertRaises(ValueError):
            SpikeAmplitudeAdapter(self.spec, wrong)

    def test_no_extrapolation_or_foreign_events(self):
        adapter = SpikeAmplitudeAdapter(self.spec, self.export([]))
        with self.assertRaises(ValueError):
            adapter.update(0.21)
        outside = self.export([0.2001])
        with self.assertRaises(ValueError):
            SpikeAmplitudeAdapter(self.spec, outside)
        foreign = self.export([0.005])
        foreign["events"][0]["flywire_id"] = "999"
        with self.assertRaises(ValueError):
            SpikeAmplitudeAdapter(self.spec, foreign)

    def test_evidence_edit_rejected_even_when_readout_ids_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            target_path = Path(directory) / "targets.json"
            adapter_path = Path(directory) / "adapter.json"
            target_path.write_text(json.dumps({"readout_ids": ["1", "2"], "source": "original"}))
            spec = {**self.spec, "targets_sha256": sha256(target_path)}
            spec["specification_sha256"] = canonical_digest(spec)
            adapter_path.write_text(json.dumps(spec))
            self.assertEqual(load_adapter(adapter_path, target_path)["readout_ids"], ["1", "2"])
            target_path.write_text(json.dumps({"readout_ids": ["1", "2"], "source": "changed"}))
            with self.assertRaisesRegex(ValueError, "source hash"):
                load_adapter(adapter_path, target_path)


if __name__ == "__main__":
    unittest.main()
