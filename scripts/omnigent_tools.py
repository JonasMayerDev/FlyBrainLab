"""Small, bounded local tools used by the native Omnigent agent spec.

This module does not orchestrate agents; Omnigent owns dispatch and sessions.
Credentials are read by the dedicated BrightData client, never returned here.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def get_setup_status() -> dict[str, Any]:
    """Inspect local model/data/tool availability without a paid request."""
    artifacts = {
        "dataset_manifest": "data/brain/manifest.json",
        "brain_module": "simulation/brain.py",
        "brightdata_client": "scripts/brightdata_client.py",
        "knowledgebase_module": "scripts/kb_store.py",
        "setup_check": "data/runs/technical_setup_check.json",
    }
    return {
        "files": {name: (PROJECT_ROOT / path).is_file() for name, path in artifacts.items()},
        "artifacts": artifacts,
        "limits": {
            "neural_pilot": "whole-network technical smoke only; no flight or biological validation",
            "body_coupling": "not implemented by this setup tool",
            "public_demo": "separate prerecorded viewer, not this local orchestration service",
        },
    }


def read_local_artifact(relative_path: str, max_chars: int = 12000) -> dict[str, Any]:
    """Read a bounded nonsecret project artifact from data, research, or simulation.

    Only JSON/JSONL/Markdown/text files are exposed, excluding hidden paths.
    """
    if not 100 <= max_chars <= 20000:
        raise ValueError("max_chars must be between 100 and 20000")
    relative = Path(relative_path)
    if relative.is_absolute() or any(part in {"..", "."} or part.startswith(".") for part in relative.parts):
        raise ValueError("Only nonhidden project-relative artifact paths are allowed")
    if not relative.parts or relative.parts[0] not in {"data", "research", "simulation"}:
        raise ValueError("Artifact must be under data/, research/, or simulation/")
    path = (PROJECT_ROOT / relative).resolve()
    path.relative_to(PROJECT_ROOT)
    if path.suffix.lower() not in {".json", ".jsonl", ".md", ".txt", ".sha256"}:
        raise ValueError("Unsupported artifact type")
    if not path.is_file():
        return {"status": "missing", "path": relative_path}
    with path.open(encoding="utf-8") as handle:
        content = handle.read(max_chars + 1)
    return {"status": "ok", "path": relative_path, "content": content[:max_chars], "truncated": len(content) > max_chars}


def run_neural_pilot(duration_ms: int = 20, rate_hz: int = 150, seed: int = 42,
                     neuron_ids: list[str] | None = None) -> dict[str, Any]:
    """Run only the fixed small whole-network setup pilot, not a flight experiment.

    Arbitrary model-neuron stimulation checks the numerical toolchain. The
    researcher must not interpret this smoke test as a biological finding.
    """
    if not 1 <= duration_ms <= 20 or not 0 <= rate_hz <= 150 or not 0 <= seed <= 100000:
        raise ValueError("Pilot limits: 1..20 ms, 0..150 Hz, seed 0..100000")
    if neuron_ids is not None and (not 1 <= len(neuron_ids) <= 32 or
                                   any(not isinstance(root_id, str) or not root_id.isdigit() for root_id in neuron_ids)):
        raise ValueError("Provide at most 32 FlyWire neuron IDs as digit strings")
    module = importlib.import_module("simulation.brain")
    if not hasattr(module, "run_pilot"):
        return {"status": "unavailable", "reason": "simulation.brain.run_pilot is not ready"}
    result = module.run_pilot(duration_ms=duration_ms, rate_hz=rate_hz, seed=seed, neuron_ids=neuron_ids)
    if not isinstance(result, dict):
        raise TypeError("run_pilot must return a structured result")
    return result
