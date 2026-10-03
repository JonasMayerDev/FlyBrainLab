from __future__ import annotations

from typing import Any
from omnigent_client import tool
from scripts.kb_store import record_experiment as _implementation

@tool
def record_experiment(run_json: 'str') -> 'dict[str, Any]':
    'Record an experiment JSON with parameters, result and provenance IDs.'
    return _implementation(run_json=run_json)
