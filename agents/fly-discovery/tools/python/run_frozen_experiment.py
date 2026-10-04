from __future__ import annotations
from typing import Any
from omnigent_client import tool
from scripts.discovery_tools import run_frozen_experiment as _implementation

@tool
def run_frozen_experiment(test: str = "A") -> dict[str, Any]:
    """Execute only preregistered DNg02 test A, B, or calibration and return actual results."""
    return _implementation(test=test)
