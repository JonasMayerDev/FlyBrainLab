"""Frozen, bounded full-v783 DNg02 input experiments; no body/flight inference.

The same entry point is callable by Omnigent tools or by a human CLI. The
execution_context is a provenance label, never proof that orchestration occurred.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import resource
import time
from types import SimpleNamespace
from uuid import uuid4

from simulation.brain import DATA, ROOT, _model

DESIGN_PATH = ROOT / "research/designs/dng02-input-v1.json"


def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_design(path: str | Path = DESIGN_PATH) -> tuple[dict, str]:
    path = Path(path).resolve()
    design = json.loads(path.read_text())
    digest = digest_file(path)
    seal_path = path.with_suffix(".sha256")
    if not seal_path.exists() or seal_path.read_text().split()[0] != digest:
        raise ValueError("The preregistered design seal is missing or does not match")
    target_path = ROOT / design["target_file"]
    if digest_file(target_path) != design["target_file_sha256"]:
        raise ValueError("The preregistered target identity file was changed")
    if design["dataset_version"] != "FAFB FlyWire v783":
        raise ValueError("Only the installed v783 graph is authorized for this design")
    if not 1 <= design["duration_ms"] <= 200 or not 0 <= design["stimulus_rate_hz"] <= 300:
        raise ValueError("The experiment exceeds the bounded simulator limits")
    if set(design["stimulus_ids"]) & set(design["readout_ids"]):
        raise ValueError("Upstream targets must not directly stimulate the DNg02 readout")
    if len(design["stimulus_ids"]) > 32 or len(design["readout_ids"]) > 32:
        raise ValueError("The bounded design permits at most 32 stimulus/readout cells")
    return design, digest


def outgoing_mask(presynaptic_indices, stimulated_indices):
    """Ablation removes source axonal outputs, leaving all other edges intact."""
    import numpy as np
    return np.isin(presynaptic_indices, stimulated_indices)


def readout_metrics(spikes, readout_ids: list[str], groups: dict[str, list[str]],
                    stimulus_ids: list[str], duration_ms: float) -> dict:
    """Rates include every selected cell, including cells with zero spikes."""
    duration_s = duration_ms / 1000
    counts = spikes["flywire_id"].value_counts()
    per_cell = {root_id: int(counts.get(root_id, 0)) for root_id in readout_ids}
    group_rates = {name: sum(per_cell[root_id] for root_id in ids) / (len(ids) * duration_s)
                   for name, ids in groups.items()}
    readout_spikes = sum(per_cell.values())
    return {
        "readout_spike_events": readout_spikes,
        "readout_active_neurons": sum(count > 0 for count in per_cell.values()),
        "population_mean_rate_hz": readout_spikes / (len(readout_ids) * duration_s),
        "group_mean_rate_hz": group_rates,
        "right_minus_left_mean_rate_hz": group_rates["right"] - group_rates["left"],
        "per_neuron_spike_counts": per_cell,
        "nonstimulated_active_neurons": len(set(counts.index) - set(stimulus_ids)),
    }


def _run_condition(design: dict, design_digest: str, condition: str, seed: int,
                   execution_context: str) -> dict:
    import brian2 as b2
    import numpy as np
    import pandas as pd
    from simulation.download_brain import download

    download(verify_only=True)
    for name, expected in design["dataset_files_sha256"].items():
        if digest_file(DATA / name) != expected:
            raise ValueError(f"Dataset hash changed: {name}")
    neurons = pd.read_csv(DATA / "Completeness_783.csv", index_col=0)
    id_to_index = {str(int(root_id)): idx for idx, root_id in enumerate(neurons.index)}
    all_ids = design["stimulus_ids"] + design["readout_ids"]
    if missing := [root_id for root_id in all_ids if root_id not in id_to_index]:
        raise ValueError(f"Preregistered IDs absent from installed v783 graph: {missing}")
    duration_ms = design["duration_ms"]
    stimulus_ids = design["readout_ids"] if condition == "direct_dng02" else design["stimulus_ids"]
    rate_hz = 0 if condition == "sham" else design["stimulus_rate_hz"]
    run_id = "neural-dng02-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:6]
    output = ROOT / "data/runs" / run_id
    output.mkdir(parents=True, exist_ok=False)
    record = {
        "schema_version": 1, "run_id": run_id, "status": "running", "run_kind": "neural_simulation",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "design_id": design["design_id"], "design_sha256": design_digest,
        "question": design["question"], "hypothesis": design["hypothesis"],
        "design_path": str(DESIGN_PATH.relative_to(ROOT)), "condition": condition,
        "dataset_version": design["dataset_version"], "model_commit": design["model_commit"],
        "duration_ms": duration_ms, "stimulus_rate_hz": rate_hz, "seed": seed,
        "n_trials": 1, "n_processes": 1, "timestep_ms": design["timestep_ms"],
        "stimulated_neuron_ids": stimulus_ids, "readout_neuron_ids": design["readout_ids"],
        "readout_groups": design["readout_groups"],
        "simulation_scope": "whole downloaded v783 graph", "full_network_included": True,
        "body_connected": False, "sensor_feedback": False,
        "execution_context": execution_context,
        "orchestration_verified_by_this_module": False,
        "evidence_scope": "Frozen connectome-model prediction of DNg02 firing; no biological or flight validation",
        "limitations": design["limitations"],
        "result_path": str(output.relative_to(ROOT)),
        "backend": "Brian2 numpy runtime", "versions": {
            "python": platform.python_version(), "brian2": b2.__version__,
            "numpy": np.__version__, "pandas": pd.__version__},
    }
    started = time.monotonic()
    try:
        b2.start_scope()
        b2.prefs.codegen.target = "numpy"
        b2.defaultclock.dt = design["timestep_ms"] * b2.ms
        b2.seed(seed)
        authors = _model()
        authors.pd = SimpleNamespace(read_csv=pd.read_csv, DataFrame=pd.DataFrame,
            read_parquet=lambda path: pd.read_parquet(path, columns=[
                "Presynaptic_Index", "Postsynaptic_Index", "Excitatory x Connectivity"]))
        params = authors.default_params.copy()
        params.update(t_run=duration_ms * b2.ms, n_run=1, r_poi=rate_hz * b2.Hz)
        params["eq_rst"] = params["eq_rst"].replace("w = 0; ", "")
        record["compatibility_adjustments"] = ["Removed undeclared upstream reset assignment w=0; source untouched"]
        record["data_loading_adjustments"] = ["Projected three required connectivity columns; retained every edge and cell"]
        record["model_parameters"] = design["model_parameters"]
        neurons_group, synapses, monitor = authors.create_model(
            DATA / "Completeness_783.csv", DATA / "Connectivity_783.parquet", params)
        stimulus_indices = [id_to_index[root_id] for root_id in stimulus_ids]
        if condition == "outgoing_disconnected":
            mask = outgoing_mask(np.asarray(synapses.i), stimulus_indices)
            record["disconnected_connection_rows"] = int(mask.sum())
            cut_indices = np.flatnonzero(mask)
            record["disconnected_weight_abs_sum_before_mV"] = float(np.sum(np.abs(synapses.w[cut_indices] / b2.mV)))
            synapses.w[cut_indices] = 0 * b2.mV
            record["disconnected_weight_abs_sum_after_mV"] = float(np.sum(np.abs(synapses.w[cut_indices] / b2.mV)))
            if record["disconnected_weight_abs_sum_after_mV"] != 0:
                raise ValueError("Outgoing synapse ablation was not applied")
            record["ablation_semantics"] = "All outgoing source-neuron weights set to zero; incoming weights intact"
        inputs, neurons_group = authors.poi(neurons_group, stimulus_indices, [], params)
        record.update(neurons=len(neurons_group), connection_rows=len(synapses))
        network = b2.Network(neurons_group, synapses, monitor, *inputs)
        before_integrator = time.monotonic()
        network.run(duration_ms * b2.ms)
        record["integration_wall_seconds"] = round(time.monotonic() - before_integrator, 6)
        indices = np.asarray(monitor.i)
        times = np.asarray(monitor.t / b2.second)
        spikes = pd.DataFrame({"t_seconds": times, "neuron_index": indices,
            "flywire_id": [str(int(neurons.index[idx])) for idx in indices]})
        spikes.to_parquet(output / "spikes.parquet", index=False)
        sample = [{"t_seconds": float(t), "flywire_id": str(int(neurons.index[idx]))}
                  for idx, t in zip(indices[:1000], times[:1000])]
        (output / "spikes_preview.json").write_text(json.dumps({"recorded_simulation": True,
            "preview_is_capped": True, "max_preview_events": 1000, "events": sample}, indent=2) + "\n")
        readout_rows = spikes[spikes.flywire_id.isin(design["readout_ids"])]
        readout_events = [{"t_seconds": float(row.t_seconds), "flywire_id": row.flywire_id}
                          for row in readout_rows.itertuples()]
        (output / "readout_spikes.json").write_text(json.dumps({"recorded_simulation": True,
            "events_are_complete": True, "readout_neuron_ids": design["readout_ids"],
            "duration_ms": duration_ms, "events": readout_events}, indent=2) + "\n")
        metrics = readout_metrics(spikes, design["readout_ids"], design["readout_groups"], stimulus_ids, duration_ms)
        (output / "readout.json").write_text(json.dumps(metrics, indent=2) + "\n")
        record.update(status="completed", spike_events=len(spikes), active_neurons=len(set(indices.tolist())),
                      spikes_file="spikes.parquet", readout_file="readout.json", readout_metrics=metrics,
                      readout_spikes_file="readout_spikes.json")
    except Exception as exc:
        record.update(status="failed", error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        record["wall_seconds"] = round(time.monotonic() - started, 6)
        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        record["max_process_rss_bytes"] = int(peak_rss if platform.system() == "Darwin" else peak_rss * 1024)
        record["ended_at_utc"] = datetime.now(timezone.utc).isoformat()
        (output / "run.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


def summarize(records: list[dict], test: str, design: dict) -> dict:
    import numpy as np
    by_condition = {}
    for record in records:
        by_condition.setdefault(record["condition"], {})[record["seed"]] = record
    summary = {"test": test, "n_seeds": len(design["seeds"]), "inference": "descriptive model comparison; no p-value or biological replication"}
    for name, conditions in by_condition.items():
        rates = [conditions[seed]["readout_metrics"]["population_mean_rate_hz"] for seed in design["seeds"]]
        summary[name] = {"population_mean_rates_hz": rates, "mean_hz": float(np.mean(rates)),
            "sample_sd_hz": float(np.std(rates, ddof=1)), "min_hz": float(min(rates)), "max_hz": float(max(rates))}
    if test == "A":
        differences = [by_condition["upstream_drive"][s]["readout_metrics"]["population_mean_rate_hz"] -
                       by_condition["sham"][s]["readout_metrics"]["population_mean_rate_hz"] for s in design["seeds"]]
        supported = all(value > 0 for value in differences)
        summary.update(paired_difference_hz=differences, supports_model_hypothesis=supported,
            updated_decision="Run test B outgoing-disconnection causality control" if supported else "Run direct-DNg02 calibration; do not tune or replace the frozen targets to hide a null result",
            next_test="B" if supported else "calibration")
    elif test == "B":
        reductions = []
        for seed in design["seeds"]:
            driven = by_condition["upstream_drive"][seed]["readout_metrics"]["population_mean_rate_hz"]
            cut = by_condition["outgoing_disconnected"][seed]["readout_metrics"]["population_mean_rate_hz"]
            reductions.append(None if driven == 0 else 1 - cut / driven)
        supported = all(value is not None and value >= 0.8 for value in reductions)
        summary.update(paired_fraction_reduction=reductions, supports_outgoing_dependency=supported,
            updated_decision="Model output depends on source axonal weights; next validate upstream identities and test a matched non-target input before any biological flight claim" if supported else "Connectivity control did not reach the frozen 80% decrease criterion; inspect alternative paths and preserve the negative result",
            next_test="matched_input_and_sensory_validation")
    else:
        summary.update(updated_decision="Calibration measures direct-drive responsiveness only; it is not evidence of propagated function or flight")
    return summary


def run_experiment(test: str = "A", execution_context: str = "manual",
                   design_path: str | Path = DESIGN_PATH) -> dict:
    """Execute the sealed A/B/calibration test serially, using the frozen seeds."""
    if test not in {"A", "B", "calibration"}:
        raise ValueError("Choose a preregistered test: A, B or calibration")
    design, design_digest = load_design(design_path)
    conditions = {"A": ["sham", "upstream_drive"],
        "B": ["upstream_drive", "outgoing_disconnected"],
        "calibration": ["sham", "direct_dng02"]}[test]
    began = datetime.now(timezone.utc)
    started = time.monotonic()
    records = []
    for seed in design["seeds"]:
        for condition in conditions:
            record = _run_condition(design, design_digest, condition, seed, execution_context)
            records.append(record)
    result = {"schema_version": 1, "design_id": design["design_id"], "design_sha256": design_digest,
        "test": test, "status": "completed", "started_at_utc": began.isoformat(),
        "ended_at_utc": datetime.now(timezone.utc).isoformat(), "execution_context": execution_context,
        "orchestration_verified_by_this_module": False, "wall_seconds": round(time.monotonic()-started, 6),
        "run_ids": [record["run_id"] for record in records],
        "result_paths": [record["result_path"] for record in records],
        "summary": summarize(records, test, design),
        "runs": [{key: record[key] for key in ["run_id", "condition", "seed", "result_path", "wall_seconds", "readout_metrics"]} for record in records]}
    result_id = "comparison-dng02-" + began.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:6]
    comparison = ROOT / "data/experiments" / f"{result_id}.json"
    comparison.parent.mkdir(parents=True, exist_ok=True)
    result["comparison_path"] = str(comparison.relative_to(ROOT))
    comparison.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", choices=["A", "B", "calibration"], default="A")
    parser.add_argument("--execution-context", default="manual")
    args = parser.parse_args()
    print(json.dumps(run_experiment(args.test, args.execution_context), indent=2))
