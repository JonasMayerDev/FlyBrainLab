from __future__ import annotations
from typing import Any
from omnigent_client import tool
from scripts.discovery_tools import read_source_snapshot as _implementation

@tool
def read_source_snapshot(source_id: str, max_chars: int = 16000, offset: int = 0) -> dict[str, Any]:
    """Read a real hashed primary-source snapshot from the local KB."""
    return _implementation(source_id=source_id, max_chars=max_chars, offset=offset)
