from __future__ import annotations

from typing import Any
from omnigent_client import tool
from scripts.brightdata_client import search_literature as _implementation

@tool
def search_literature(query: 'str', max_results: 'int' = 5) -> 'dict[str, Any]':
    'Search approved source domains via Bright Data SERP and store candidates locally.'
    return _implementation(query=query, max_results=max_results)
