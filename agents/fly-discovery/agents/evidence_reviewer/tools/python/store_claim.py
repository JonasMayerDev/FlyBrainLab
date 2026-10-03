from __future__ import annotations

from typing import Any
from omnigent_client import tool
from scripts.kb_store import store_claim as _implementation

@tool
def store_claim(claim_json: 'str') -> 'dict[str, Any]':
    'Persist a source-linked claim JSON object in the local knowledgebase.'
    return _implementation(claim_json=claim_json)
