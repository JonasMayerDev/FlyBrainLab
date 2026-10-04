from __future__ import annotations
from typing import Any
from omnigent_client import tool
from scripts.discovery_tools import save_discovery_record as _implementation

@tool
def save_discovery_record(record_json: str) -> dict[str, Any]:
    """Save evidence, actual numeric receipt, and result-dependent next decision; native trace verification remains pending."""
    return _implementation(record_json=record_json)
