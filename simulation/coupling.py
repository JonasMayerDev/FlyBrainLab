"""Frozen causal DNg02 spike replay -> wing amplitude -> real body dynamics.

This adapter is an explicit technical model assumption, not a calibrated VNC.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

from simulation.body import ROOT, run_body, sha256, write_json

ADAPTER_PATH = ROOT / "data/coupling/adapter_v1.json"


def canonical_digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def freeze_adapter() -> dict:
    """Write-once specification. Never tune gains after observing body outcomes."""
    if ADAPTER_PATH.exists():
        return load_adapter()
    targets_path = ROOT / "research/evidence/dng02_targets.json"
    targets = json.loads(targets_path.read_text())
    spec = {"schema_version": 1, "adapter_id": "dng02-wing-yaw-amplitude-v1",
            "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
            "readout_ids": targets["readout_ids"],
            "readout_grouping": "pooled mean across all 25 cells; no laterality inference",
            "targets_sha256": sha256(targets_path),
            "window_ms": 10., "reference_rate_hz": 100.,
            "maximum_fractional_amplitude_increase": 0.1,
            "wing_yaw_center_rad": 0.3, "wing_yaw_indices": [0, 3],
            "formula": "r(t)=count(events in [t-10ms,t))/(25*0.010s); u=clip(r/100Hz,0,1); yaw'=0.3+(1+0.1*u)*(yaw-0.3)",
            "neural_clock": "original simulation time; no stretching, repetition or extrapolated events",
            "controller_frequency_hz": 218.,
            "basis": "DNg02 population recruitment modulates wingbeat amplitude during flight (Namiki et al., 2022)",
            "basis_url": "https://doi.org/10.1016/j.cub.2022.01.008",
            "model_assumptions": ["10 ms window, 100 Hz scale, positive 10 percent gain and yaw-only modulation are chosen engineering assumptions.",
                                  "25 annotation entries pooled; no calibrated per-cell, per-subtype or left/right muscle mapping.",
                                  "The body uses the existing approximate author wingbeat generator without a learned flight policy.",
                                  "Recorded neural output drives body physics; sensory feedback is absent."]}
    spec["specification_sha256"] = canonical_digest(spec)
    ADAPTER_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_json(ADAPTER_PATH, spec)
    return spec


def load_adapter(adapter_path: Path | None = None, targets_path: Path | None = None) -> dict:
    adapter_path = adapter_path or ADAPTER_PATH
    targets_path = targets_path or ROOT / "research/evidence/dng02_targets.json"
    spec = json.loads(adapter_path.read_text())
    digest = spec.pop("specification_sha256")
    if canonical_digest(spec) != digest:
        raise ValueError("Frozen adapter specification hash does not match")
    spec["specification_sha256"] = digest
    targets_bytes = targets_path.read_bytes()
    if hashlib.sha256(targets_bytes).hexdigest() != spec["targets_sha256"]:
        raise ValueError("Current DNg02 evidence file differs from the frozen adapter's source hash")
    targets = json.loads(targets_bytes)
    if set(targets["readout_ids"]) != set(spec["readout_ids"]):
        raise ValueError("Current DNg02 evidence IDs differ from the frozen adapter")
    if not spec["readout_ids"] or len(set(spec["readout_ids"])) != len(spec["readout_ids"]):
        raise ValueError("Readout IDs must be unique and nonempty")
    return spec


class AmplitudePattern:
    """Wrap an author's test pattern without modifying installed author code."""
    def __init__(self, base, spec: dict):
        self.base = base
        self.spec = spec
        self.factor = 1.

    def __getattr__(self, name):
        return getattr(self.base, name)

    def step(self, ctrl_freq):
        angles = self.base.step(ctrl_freq=ctrl_freq).copy()
        center = self.spec["wing_yaw_center_rad"]
        for index in self.spec["wing_yaw_indices"]:
            angles[index] = center + self.factor * (angles[index] - center)
        return angles


class SpikeAmplitudeAdapter:
    def __init__(self, spec: dict, spike_export: dict):
        if spike_export.get("events_are_complete") is not True:
            raise ValueError("Coupling requires complete readout events, not a capped preview")
        if set(spike_export["readout_neuron_ids"]) != set(spec["readout_ids"]):
            raise ValueError("Frozen readout IDs do not match neural run IDs")
        self.spec = spec
        self.duration_ms = float(spike_export["duration_ms"])
        events = spike_export["events"]
        allowed = set(spec["readout_ids"])
        if any(str(e["flywire_id"]) not in allowed for e in events):
            raise ValueError("Spike export contains events outside frozen readout")
        self.times = sorted(float(e["t_seconds"]) for e in events)
        if any(not math.isfinite(t) or not 0 <= t < self.duration_ms / 1000 for t in self.times):
            raise ValueError("Spike times must be finite and inside the original neural horizon")
        self.pattern = None

    def attach(self, env) -> None:
        self.pattern = AmplitudePattern(env.task._wbpg, self.spec)
        env.task._wbpg = self.pattern

    def update(self, time_seconds: float) -> tuple[float, float]:
        if not 0 <= time_seconds < self.duration_ms / 1000 + 1e-10:
            raise ValueError("Body requested neural signal outside recorded horizon")
        window = self.spec["window_ms"] / 1000
        # bisect_left on both bounds gives a causal half-open trailing window.
        count = bisect_left(self.times, time_seconds) - bisect_left(self.times, time_seconds - window)
        rate = count / (len(self.spec["readout_ids"]) * window)
        normalized = min(1., max(0., rate / self.spec["reference_rate_hz"]))
        factor = 1. + self.spec["maximum_fractional_amplitude_increase"] * normalized
        if self.pattern is not None:
            self.pattern.factor = factor
        return rate, factor

    def provenance(self) -> dict:
        return {"adapter_id": self.spec["adapter_id"],
                "specification_path": "data/coupling/adapter_v1.json",
                "specification_sha256": self.spec["specification_sha256"],
                "readout_ids": self.spec["readout_ids"],
                "event_count": len(self.times), "window_ms": self.spec["window_ms"],
                "model_assumption": True, "biologically_calibrated": False,
                "mapping": self.spec["formula"]}


def run_coupled(neural_run_dir: Path) -> dict:
    spec = load_adapter()
    neural_run_dir = neural_run_dir.resolve()
    neural_run_dir.relative_to(ROOT / "data/runs")
    record_path = neural_run_dir / "run.json"
    neural = json.loads(record_path.read_text())
    if neural.get("status") != "completed" or neural.get("dataset_version") != "FAFB FlyWire v783":
        raise ValueError("Coupling requires a completed matching v783 neural run")
    events_path = neural_run_dir / "readout_spikes.json"
    spike_export = json.loads(events_path.read_text())
    if spike_export["duration_ms"] != neural["duration_ms"]:
        raise ValueError("Spike export duration does not match original run")
    adapter = SpikeAmplitudeAdapter(spec, spike_export)
    provenance = {"run_id": neural["run_id"], "condition": neural["condition"],
                  "result_path": str(neural_run_dir.relative_to(ROOT)),
                  "run_record_sha256": sha256(record_path),
                  "readout_events_sha256": sha256(events_path),
                  "neural_duration_ms": neural["duration_ms"],
                  "execution_context": neural.get("execution_context", "unspecified"),
                  "source_is_recorded_simulation": True}
    return run_body(neural["duration_ms"], neural["seed"], adapter=adapter,
                    neural_provenance=provenance)


def compare(body_run_dirs: list[Path]) -> dict:
    """Paired physical comparison at each seed's common measured horizon."""
    import numpy as np
    records = [json.loads((p / "run.json").read_text()) for p in body_run_dirs]
    grouped = {}
    for path, record in zip(body_run_dirs, records):
        if record["status"] != "completed" or not record.get("adapter"):
            raise ValueError("Comparison requires successful coupled run records")
        key = (record["seed"], record["neural_provenance"]["condition"])
        if key in grouped:
            raise ValueError("Duplicate body seed/condition")
        if record["adapter"]["specification_sha256"] != load_adapter()["specification_sha256"]:
            raise ValueError("Adapter must be identical across compared runs")
        grouped[key] = (record, json.loads((path / "trajectory.json").read_text())["states"])
    pairs = []
    for seed in sorted({r["seed"] for r in records}):
        if (seed, "sham") not in grouped or (seed, "upstream_drive") not in grouped:
            continue
        baseline, sham = grouped[(seed, "sham")]
        driven, active = grouped[(seed, "upstream_drive")]
        count = min(len(sham), len(active))
        if [s["time_ms"] for s in sham[:count]] != [s["time_ms"] for s in active[:count]]:
            raise ValueError("Paired body timestamps must match")
        if sham[0]["qpos"] != active[0]["qpos"] or sham[0]["qvel"] != active[0]["qvel"]:
            raise ValueError("Paired body initial physical state must match")
        positions_a = np.array([s["position"] for s in active[:count]])
        positions_s = np.array([s["position"] for s in sham[:count]])
        wing_a = np.array([s["wing_angles_rad"] for s in active[:count]])
        wing_s = np.array([s["wing_angles_rad"] for s in sham[:count]])
        pairs.append({"seed": seed, "sham_run_id": baseline["run_id"], "driven_run_id": driven["run_id"],
                      "common_horizon_ms": sham[count - 1]["time_ms"],
                      "root_position_difference_cm_at_common_horizon": float(np.linalg.norm(positions_a[-1] - positions_s[-1])),
                      "wing_angle_rms_difference_rad": float(np.sqrt(np.mean((wing_a - wing_s) ** 2))),
                      "max_driven_amplitude_factor": max(s["wing_yaw_amplitude_factor"] for s in active[:count]),
                      "max_sham_amplitude_factor": max(s["wing_yaw_amplitude_factor"] for s in sham[:count]),
                      "driven_terminated_early": driven["task_terminated_early"],
                      "sham_terminated_early": baseline["task_terminated_early"]})
    if not pairs:
        raise ValueError("No matched upstream_drive/sham seed pairs")
    result = {"schema_version": 1, "created_at_utc": datetime.now(timezone.utc).isoformat(),
              "comparison_kind": "technical open-loop brain-to-body adapter", "paired_results": pairs,
              "all_run_ids": [r["run_id"] for r in records],
              "adapter_sha256": load_adapter()["specification_sha256"],
              "interpretation": "Actual neural events affect a fixed controller input and measured body physics. The gain/controller choice is a model assumption; this does not validate biological flight.",
              "flight_validated": False,
              "next_decision": "Calibrate the rate-to-wing mapping and stabilize the existing flight controller before any biological or stable-flight claim."}
    write_json(ROOT / "data/coupling/comparison.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("freeze")
    run_parser = sub.add_parser("run")
    run_parser.add_argument("neural_run_dir", type=Path)
    comparison_parser = sub.add_parser("compare")
    comparison_parser.add_argument("body_run_dirs", type=Path, nargs="+")
    args = parser.parse_args()
    result = (freeze_adapter() if args.command == "freeze" else
              run_coupled(args.neural_run_dir) if args.command == "run" else compare(args.body_run_dirs))
    print(json.dumps(result, indent=2, allow_nan=False))
