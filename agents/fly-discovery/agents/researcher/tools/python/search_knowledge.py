from __future__ import annotations

from typing import Any
from omnigent_client import tool
from scripts.kb_store import search_knowledge as _implementation

@tool
def search_knowledge(query: 'str', collection: 'str' = 'claims', limit: 'int' = 20) -> 'list[dict[str, Any]]':
    """Search collections claims, sources or runs only. Query AND-matches every word; use an empty query to enumerate or one precise term. No network call."""
    return _implementation(query=query, collection=collection, limit=limit)
