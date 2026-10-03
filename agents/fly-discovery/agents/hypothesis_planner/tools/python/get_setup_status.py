from __future__ import annotations

from typing import Any
from omnigent_client import tool
from scripts.omnigent_tools import get_setup_status as _implementation

@tool
def get_setup_status() -> 'dict[str, Any]':
    'Inspect local model/data/tool availability without a paid request.'
    return _implementation()
