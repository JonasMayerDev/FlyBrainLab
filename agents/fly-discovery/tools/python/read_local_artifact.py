from __future__ import annotations

from typing import Any
from omnigent_client import tool
from scripts.omnigent_tools import read_local_artifact as _implementation

@tool
def read_local_artifact(relative_path: 'str', max_chars: 'int' = 12000) -> 'dict[str, Any]':
    'Read a bounded nonsecret project artifact from data, research, or simulation.\n\nOnly JSON/JSONL/Markdown/text files are exposed, excluding hidden paths.'
    return _implementation(relative_path=relative_path, max_chars=max_chars)
