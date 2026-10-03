from __future__ import annotations

from typing import Any
from omnigent_client import tool
from scripts.kb_store import search_knowledge as _implementation

@tool
def search_knowledge(query: 'str', collection: 'str' = 'claims', limit: 'int' = 20) -> 'list[dict[str, Any]]':
    'Search locally stored evidence, sources or run records; no network call.'
    return _implementation(query=query, collection=collection, limit=limit)
