"""Report setup readiness without printing secrets or launching paid calls."""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def check() -> dict:
    from scripts.kb_store import default_kb_directory
    from scripts.brightdata_client import BrightDataConfig, BrightDataError

    packages = {}
    for name in ("omnigent", "brian2", "numpy", "pandas", "pyarrow", "joblib"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    validation_file = ROOT / "data/brain/validation.json"
    validation = json.loads(validation_file.read_text()) if validation_file.is_file() else None
    runs = []
    for path in sorted((ROOT / "data/runs").glob("*/run.json")):
        record = json.loads(path.read_text())
        runs.append({key: record.get(key) for key in (
            "run_id", "status", "neurons", "connection_rows", "duration_ms", "stimulus_rate_hz",
            "spike_events", "wall_seconds", "body_connected", "evidence_scope",
        )})
    kb_path = default_kb_directory()
    kb_counts = {}
    for name in ("sources", "claims", "runs"):
        path = kb_path / f"{name}.jsonl"
        kb_counts[name] = sum(bool(line.strip()) for line in path.read_text().splitlines()) if path.is_file() else None
    credentials = {name: bool(os.environ.get(name)) for name in (
        "ANTHROPIC_API_KEY", "BRIGHTDATA_API_KEY", "BRIGHTDATA_SERP_ZONE", "BRIGHTDATA_UNLOCKER_ZONE",
        "BRIGHTDATA_MAX_COST_USD", "BRIGHTDATA_ESTIMATED_REQUEST_COST_USD",
    )}
    try:
        brightdata = BrightDataConfig.from_environment().readiness()
    except BrightDataError as exc:
        brightdata = {"ready": False, "configuration_error": str(exc)}
    local_run_records = kb_path / "runs.jsonl"
    research_records = []
    if local_run_records.is_file():
        research_records = [json.loads(line) for line in local_run_records.read_text().splitlines() if line.strip()]
    verified_discovery = any(
        item.get("run_kind") == "research" and item.get("status") == "completed"
        and item.get("result", {}).get("recorded_under_omnigent") is True
        and item.get("result", {}).get("discovery_loop_verified") is True
        for item in research_records
    )
    return {
        "packages": packages,
        "brain_validation": validation,
        "brain_runs": runs,
        "knowledgebase": {"directory": str(kb_path), "counts": kb_counts, "storage": "local-jsonl"},
        "configured_in_this_process": credentials,
        "brightdata_configuration": brightdata,
        "live_research_configured": bool(brightdata["ready"] and credentials["ANTHROPIC_API_KEY"] and all(packages.values())),
        "live_research_loop_verified": verified_discovery,
        "discovery_verification_basis": "completed Omnigent research receipts with explicit verification flags; credential presence alone is insufficient",
        "body_connected": False,
        "published_demo": False,
        "note": "Credential flags only describe this process; no secret values or live calls are emitted. Native config check: scripts/omnigent_run.py --check.",
    }


if __name__ == "__main__":
    print(json.dumps(check(), ensure_ascii=False, indent=2))
