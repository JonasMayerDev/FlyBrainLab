from __future__ import annotations

from typing import Any
from omnigent_client import tool
from scripts.kb_store import store_source as _implementation

@tool
def store_source(source_json: 'str') -> 'dict[str, Any]':
    'Store source metadata JSON; metadata alone is not retrieved evidence.'
    return _implementation(source_json=source_json)
