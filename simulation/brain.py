"""Whole-network v783 checks and a bounded technical pilot of Shiu's LIF model.

This module produces neural activity only. It has no body adapter or flight claim.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import platform
import resource
import time
from types import SimpleNamespace
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/brain/flywire783"
VENDOR = ROOT / "simulation/vendor/shiu"


def _model():
    spec = importlib.util.spec_from_file_location("shiu_author_model", VENDOR / "model.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate() -> dict:
    import numpy as np
    import pandas as pd
    import pyarrow.parquet as pq

    from simulation.download_brain import download
    download(verify_only=True)
    neurons = pd.read_csv(DATA / "Completeness_783.csv", index_col=0)
    connectivity = pd.read_parquet(DATA / "Connectivity_783.parquet")
    required = ["Presynaptic_Index", "Postsynaptic_Index", "Excitatory x Connectivity"]
    if not neurons.index.is_unique:
        raise ValueError("v783 neuron IDs must be unique")
    if not set(required).issubset(connectivity.columns):
        raise ValueError("Author connectivity schema does not match the model")
    for column in required[:2]:
        indices = connectivity[column].to_numpy()
        if indices.min() < 0 or indices.max() >= len(neurons):
            raise ValueError(f"Out-of-range neuron index in {column}")
        if not np.equal(indices, np.floor(indices)).all():
            raise ValueError(f"Nonintegral neuron index in {column}")
    if not np.isfinite(connectivity[required[2]].to_numpy()).all():
        raise ValueError("Nonfinite connection weights")
    result = {
        "status": "validated", "dataset_version": "FAFB FlyWire v783",
        "neurons": len(neurons), "connection_rows": len(connectivity),
        "connections_are": "author-derived neuron-pair rows, not individual raw synapse points",
        "columns": list(connectivity.columns),
        "parquet_row_groups": pq.ParquetFile(DATA / "Connectivity_783.parquet").num_row_groups,
        "neuron_id_encoding": "Store FlyWire IDs as strings in JavaScript/JSON consumers; values exceed safe JS integer range",
    }
    (ROOT / "data/brain/validation.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def run_pilot(duration_ms: float = 20, rate_hz: float = 150, seed: int = 42,
              neuron_ids: list[str] | None = None) -> dict:
    """One process, full downloaded graph, <=200 ms, <=32 stimulation targets."""
    if not 1 <= duration_ms <= 200 or not 0 <= rate_hz <= 300:
        raise ValueError("Pilot limit: duration 1..200 ms and stimulation 0..300 Hz")
    if neuron_ids is not None and not 1 <= len(neuron_ids) <= 32:
        raise ValueError("Pilot requires 1..32 explicit target IDs")

    import brian2 as b2
    import numpy as np
    import pandas as pd
    import pyarrow

    from simulation.download_brain import download
    download(verify_only=True)
    run_id = "brain-pilot-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:6]
    output = ROOT / "data/runs" / run_id
    output.mkdir(parents=True, exist_ok=False)
    record = {"run_id": run_id, "status": "running", "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "dataset_version": "FAFB FlyWire v783", "model_commit": "91bdd1e7dcf193f3e7ca5a8933497fcef63b7960",
              "duration_ms": duration_ms, "stimulus_rate_hz": rate_hz, "seed": seed,
              "n_trials": 1, "n_processes": 1, "timestep_ms": 0.1,
              "simulation_scope": "whole downloaded v783 graph", "body_connected": False,
              "evidence_scope": "technical smoke test; no independent biological or flight validation",
              "versions": {"python": platform.python_version(), "brian2": b2.__version__, "numpy": np.__version__,
                           "pandas": pd.__version__, "pyarrow": pyarrow.__version__},
              "limitations": ["Short technical probe; insufficient for statistical behavioral conclusions.",
                              "No body dynamics, motor adapter or sensor feedback is connected.",
                              "Generic pilot target identity has not been functionally annotated.",
                              "LIF dynamics and signed weights are author-model assumptions."]}
    started = time.monotonic()
    try:
        b2.start_scope()
        b2.prefs.codegen.target = "numpy"
        b2.defaultclock.dt = 0.1 * b2.ms
        b2.seed(seed)
        authors = _model()
        # The author constructor only uses these three connectivity columns.
        # Project them during loading to avoid allocating unused ID/annotation columns
        # on the team's 8 GiB laptop. Every row and every neuron remains included.
        authors.pd = SimpleNamespace(
            read_csv=pd.read_csv,
            read_parquet=lambda path: pd.read_parquet(path, columns=[
                "Presynaptic_Index", "Postsynaptic_Index", "Excitatory x Connectivity"]),
            DataFrame=pd.DataFrame,
        )
        record["data_loading_adjustments"] = ["Projected only the three connectivity columns consumed by create_model; all rows retained."]
        params = authors.default_params.copy()
        params.update(t_run=duration_ms * b2.ms, n_run=1, r_poi=rate_hz * b2.Hz)
        # This pinned upstream model declares v, g and rfc, but no neuron w.
        # Keep its source untouched and record the removed invalid reset assignment.
        if "w = 0;" in params["eq_rst"]:
            params["eq_rst"] = params["eq_rst"].replace("w = 0; ", "")
            record["compatibility_adjustments"] = ["Removed assignment w=0 from reset: w is undeclared in the upstream neuron equations. Upstream source unchanged."]
        else:
            record["compatibility_adjustments"] = []
        neurons = pd.read_csv(DATA / "Completeness_783.csv", index_col=0)
        id_to_index = {str(int(root_id)): idx for idx, root_id in enumerate(neurons.index)}
        targets = neuron_ids or [str(int(neurons.index[0]))]
        missing = [root_id for root_id in targets if root_id not in id_to_index]
        if missing:
            raise ValueError(f"Target IDs are not present in v783: {missing}")
        record["stimulated_neuron_ids"] = targets
        neu, syn, monitor = authors.create_model(DATA / "Completeness_783.csv", DATA / "Connectivity_783.parquet", params)
        record.update(neurons=len(neu), connection_rows=len(syn))
        inputs, neu = authors.poi(neu, [id_to_index[root_id] for root_id in targets], [], params)
        network = b2.Network(neu, syn, monitor, *inputs)
        network.run(duration_ms * b2.ms)
        indices = np.asarray(monitor.i)
        times = np.asarray(monitor.t / b2.second)
        spikes = pd.DataFrame({"t_seconds": times, "neuron_index": indices,
                               "flywire_id": [str(int(neurons.index[idx])) for idx in indices]})
        spikes.to_parquet(output / "spikes.parquet", index=False)
        sample = [{"t_seconds": float(t), "flywire_id": str(int(neurons.index[idx]))}
                  for idx, t in zip(indices[:1000], times[:1000])]
        (output / "spikes_preview.json").write_text(json.dumps({"recorded_simulation": True, "preview_is_capped": True,
                                                               "max_preview_events": 1000, "events": sample}, indent=2) + "\n")
        record.update(status="completed", spike_events=len(spikes), active_neurons=len(set(indices.tolist())),
                      result_path=str(output.relative_to(ROOT)), spikes_file="spikes.parquet",
                      full_network_included=True, backend="Brian2 numpy runtime")
    except Exception as exc:
        record.update(status="failed", error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        record["wall_seconds"] = round(time.monotonic() - started, 3)
        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        record["max_process_rss_bytes"] = int(peak_rss if platform.system() == "Darwin" else peak_rss * 1024)
        record["ended_at_utc"] = datetime.now(timezone.utc).isoformat()
        (output / "run.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate", "pilot"])
    parser.add_argument("--duration-ms", type=float, default=20)
    parser.add_argument("--rate-hz", type=float, default=150)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--neuron-id", action="append", dest="neuron_ids")
    args = parser.parse_args()
    result = validate() if args.command == "validate" else run_pilot(args.duration_ms, args.rate_hz, args.seed, args.neuron_ids)
    print(json.dumps(result, indent=2))
