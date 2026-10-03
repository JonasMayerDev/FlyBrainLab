from __future__ import annotations

from typing import Any
from omnigent_client import tool
from scripts.omnigent_tools import run_neural_pilot as _implementation

@tool
def run_neural_pilot(duration_ms: 'int' = 20, rate_hz: 'int' = 150, seed: 'int' = 42, neuron_ids: 'list[str] | None' = None) -> 'dict[str, Any]':
    'Run only the fixed small whole-network setup pilot, not a flight experiment.\n\nArbitrary model-neuron stimulation checks the numerical toolchain. The\nresearcher must not interpret this smoke test as a biological finding.'
    return _implementation(duration_ms=duration_ms, rate_hz=rate_hz, seed=seed, neuron_ids=neuron_ids)
