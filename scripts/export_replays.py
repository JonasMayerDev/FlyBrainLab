"""Export bounded, traceable browser replays from completed recorded simulations.

No simulation, activity, anatomy or body movement is invented here. Layout positions
are assigned by the browser and explicitly described as schematic. Full spike
histograms are retained even when individual event display must be sampled.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/JonasMayerDev/FlyBrainLab"
MAX_EVENTS = 30_000
SOURCES = [
    {"title": "Shiu et al. (2024) · whole-brain LIF model", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/", "kind": "Published model", "scope": "Published sensorimotoric experiments; no general flight validation."},
    {"title": "Shiu author implementation · pinned commit", "url": "https://github.com/philshiu/Drosophila_brain_model/tree/91bdd1e7dcf193f3e7ca5a8933497fcef63b7960", "kind": "Reproduction code", "scope": "FAFB v783 tables and author LIF assumptions; compatibility adjustments recorded per run."},
    {"title": "FlyWire whole-brain connectivity · v783", "url": "https://zenodo.org/records/10676866", "kind": "Connectome · CC BY 4.0", "scope": "FlyWire Consortium (2024). Our model uses author-transformed connectivity tables, not raw synapse points."},
]


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def root_id(value: object) -> str:
    if isinstance(value, (float, bool)) or not str(value).isdigit():
        raise ValueError(f"Neuron ID must be an exact integer/string: {value!r}")
    return str(value)


def sample_ids() -> list[str]:
    path = ROOT / "data/brain/flywire783/Completeness_783.csv"
    if not path.exists():
        return []
    with path.open() as stream:
        reader = csv.reader(stream)
        next(reader)
        ids = [root_id(row[0]) for row in reader if row]
    stride = max(1, len(ids) // 256)
    return ids[::stride][:256]


def spikes(directory: Path, record: dict) -> tuple[list[dict], bool, Path | None]:
    source = directory / record.get("spikes_file", "spikes.parquet")
    if source.exists():
        import pyarrow.parquet as pq
        rows = pq.read_table(source, columns=["t_seconds", "flywire_id"]).to_pylist()
        events = [{"time_ms": round(float(row["t_seconds"]) * 1000, 6), "neuron_id": root_id(row["flywire_id"])} for row in rows]
        return sorted(events, key=lambda event: event["time_ms"]), True, source
    preview = directory / "spikes_preview.json"
    if not preview.exists():
        raise ValueError(f"No spike output exists for {record['run_id']}")
    value = json.loads(preview.read_text())
    events = [{"time_ms": round(float(row["t_seconds"]) * 1000, 6), "neuron_id": root_id(row["flywire_id"])} for row in value["events"]]
    return events, len(events) == int(record.get("spike_events", -1)), preview


def export_run(directory: Path, sampled_ids: list[str]) -> dict | None:
    path = directory / "run.json"
    record = json.loads(path.read_text())
    if record.get("status") != "completed":
        return None
    run_id = record["run_id"]
    if not run_id or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for char in run_id):
        raise ValueError(f"Unsafe replay filename: {run_id!r}")
    events, complete, spike_source = spikes(directory, record)
    duration = float(record["duration_ms"])
    if duration <= 0 or not math.isfinite(duration):
        raise ValueError(f"Invalid simulation duration in {run_id}")
    if any(not 0 <= event["time_ms"] <= duration for event in events):
        raise ValueError(f"Spike outside the recorded interval in {run_id}")
    if complete and len(events) != record["spike_events"]:
        raise ValueError(f"Spike count differs from run record in {run_id}")
    counts = Counter(event["neuron_id"] for event in events)
    targets = list(map(root_id, record.get("stimulated_neuron_ids", [])))
    readouts = list(map(root_id, record.get("readout_neuron_ids", [])))
    node_ids = list(dict.fromkeys(targets + readouts + [item[0] for item in counts.most_common(96)] + sampled_ids))
    bins = [0] * 100
    for event in events:
        bins[min(99, int(event["time_ms"] / duration * 100))] += 1
    displayed = events
    if len(events) > MAX_EVENTS:
        displayed = [events[int(index * len(events) / MAX_EVENTS)] for index in range(MAX_EVENTS)]
    classification = record.get("classification") or ("technical_setup_check" if "technical" in record.get("evidence_scope", "").lower() else "model_experiment")
    condition_names = {"sham": "Sham · 0 Hz", "upstream_drive": "Upstream drive · 150 Hz", "outgoing_disconnected": "Outgoing links disconnected", "direct_dng02": "Direct DNg02 calibration"}
    title = record.get("label") or condition_names.get(record.get("condition")) or ("Stimulated · 150 Hz" if record.get("stimulus_rate_hz") == 150 else "Sham · 0 Hz" if record.get("stimulus_rate_hz") == 0 else f"Stimulation · {record.get('stimulus_rate_hz', '?')} Hz")
    metadata = {key: record[key] for key in (
        "run_id", "status", "started_at_utc", "ended_at_utc", "dataset_version", "model_commit", "duration_ms", "stimulus_rate_hz", "seed", "n_trials", "timestep_ms", "simulation_scope", "body_connected", "evidence_scope", "versions", "limitations", "compatibility_adjustments", "data_loading_adjustments", "stimulated_neuron_ids", "neurons", "connection_rows", "spike_events", "active_neurons", "full_network_included", "backend", "wall_seconds", "max_process_rss_bytes", "experiment_id", "condition", "hypothesis", "question", "readout_neuron_ids", "controller", "motor_adapter", "orchestration", "silenced_neuron_ids", "metrics", "design_id", "design_sha256", "design_path", "readout_metrics", "execution_context", "orchestration_verified_by_this_module"
    ) if key in record}
    body = None
    body_file = directory / record.get("body_trajectory_file", "body_trajectory.json")
    if body_file.exists():
        body = json.loads(body_file.read_text())
    else:
        for body_record_file in sorted((ROOT / "data/body").glob("*/run.json")):
            body_record = json.loads(body_record_file.read_text())
            if body_record.get("status") != "completed" or (body_record.get("neural_provenance") or {}).get("run_id") != run_id:
                continue
            trajectory = body_record_file.parent / "trajectory.json"
            if not trajectory.exists():
                continue
            original = json.loads(trajectory.read_text())
            body = {key: original.get(key) for key in ("model", "model_commit", "controller", "loop", "flight_validated", "axis_convention")}
            body.update(adapter=body_record.get("adapter"), position_unit=original.get("units", {}).get("position"),
                duration_ms=body_record.get("metrics", {}).get("actual_duration_ms"), task_terminated_early=body_record.get("task_terminated_early"),
                limitations=body_record.get("limitations", []), metrics=body_record.get("metrics", {}),
                states=[{key: state[key] for key in ("time_ms", "position", "quaternion", "wing_angles_rad", "adapter_rate_hz", "wing_yaw_amplitude_factor") if key in state} for state in original["states"]],
                run_record_url=f"{REPOSITORY}/blob/main/{body_record_file.relative_to(ROOT)}", trajectory_sha256=digest(trajectory))
    run_sources = list(record.get("sources", SOURCES))
    if record.get("design_id"):
        run_sources.extend([
            {"title": "Frozen DNg02 experiment design", "url": f"{REPOSITORY}/blob/main/{record.get('design_path', 'research/designs/dng02-input-v1.json')}", "kind": "Preregistered model assay", "scope": "Two tests, three fixed seeds, 25 predefined DNg02 readouts; hypothesis selected before observing the response."},
            {"title": "DNg02 target identity and biological evidence", "url": f"{REPOSITORY}/blob/main/research/evidence/dng02_targets.json", "kind": "Evidence and exact v783 IDs", "scope": "Annotation release and graph-selected upstream identities. Flight-related biological evidence does not validate this model as a flying brain."},
        ])
    return {
        "schema_version": 1, "run_id": run_id, "title": title, "classification": classification,
        "recorded_simulation": True, "metadata": metadata,
        "activity": {"time_unit": "ms", "event_count": record["spike_events"], "events": displayed,
            "events_complete": complete and len(displayed) == len(events), "source_complete": complete,
            "display_sampling": "uniform event-index sampling" if len(displayed) < len(events) else "none",
            "histogram": {"bin_width_ms": duration / 100, "counts": bins, "complete": complete}},
        "graph": {"layout": "abstract schematic; no anatomical coordinates or inferred synapses",
            "selection": "all stimulated and readout IDs, 96 most active recorded cells, up to 256 uniformly sampled v783 model IDs",
            "nodes": [{"id": neuron_id, "target": neuron_id in targets, "readout": neuron_id in readouts, "spike_count": counts[neuron_id]} for neuron_id in node_ids],
            "edges": []},
        "body": body, "sources": run_sources,
        "provenance": {"run_record_url": f"{REPOSITORY}/blob/main/{path.relative_to(ROOT)}", "run_record_sha256": digest(path),
            "spike_source_url": f"{REPOSITORY}/blob/main/{spike_source.relative_to(ROOT)}" if spike_source else None,
            "spike_source_sha256": digest(spike_source) if spike_source else None,
            "model_url": f"https://github.com/philshiu/Drosophila_brain_model/tree/{record['model_commit']}",
            "exporter": "scripts/export_replays.py"},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=ROOT / "data/runs")
    parser.add_argument("--output", type=Path, default=ROOT / "data/replay")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    ids = sample_ids()
    exported = []
    for path in sorted(args.runs.glob("*/run.json")):
        run = export_run(path.parent, ids)
        if run:
            dump(args.output / f"{run['run_id']}.json", run)
            exported.append({key: run[key] for key in ("run_id", "title", "classification") } | {"file": f"{run['run_id']}.json", "metadata": run["metadata"], "body_available": bool(run.get("body"))})
    if not exported:
        raise ValueError("No completed recorded runs found")
    setup = ROOT / "data/runs/technical_setup_check.json"
    summary = json.loads(setup.read_text()) if setup.exists() else None
    comparisons = []
    for path in sorted((ROOT / "data/experiments").glob("comparison-*.json")):
        record = json.loads(path.read_text())
        if record.get("status") == "completed":
            comparisons.append({key: record.get(key) for key in ("design_id", "test", "execution_context", "run_ids", "summary", "orchestration_verified_by_this_module")} | {"url": f"{REPOSITORY}/blob/main/{path.relative_to(ROOT)}"})
    coupling_file = ROOT / "data/coupling/comparison.json"
    coupling = json.loads(coupling_file.read_text()) if coupling_file.exists() else None
    dump(args.output / "index.json", {"schema_version": 1, "exported_at_utc": datetime.now(timezone.utc).isoformat(), "repository_url": REPOSITORY, "runs": exported, "technical_setup_check": summary, "sources": SOURCES, "comparisons": comparisons, "coupling": coupling})
    print(json.dumps({"exported_runs": len(exported), "directory": str(args.output), "events_are_recorded": True}))


if __name__ == "__main__":
    main()
