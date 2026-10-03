from __future__ import annotations

from typing import Any
from omnigent_client import tool
from scripts.brightdata_client import fetch_source as _implementation

@tool
def fetch_source(url: 'str', title: 'str' = '', dataset_version: 'str' = 'unknown', max_characters: 'int' = 20000) -> 'dict[str, Any]':
    'Retrieve an approved public source through Web Unlocker and save a local snapshot.'
    return _implementation(url=url, title=title, dataset_version=dataset_version, max_characters=max_characters)
