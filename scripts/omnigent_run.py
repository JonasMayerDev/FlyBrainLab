"""Validate or launch the project's native Omnigent agent bundle.

--check performs no LLM request, BrightData request, or new neural simulation.
Actual launch expects credentials supplied through the parent environment.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "agents" / "fly-discovery"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXPECTED_TOOLS = {
    "fly_discovery": {"get_setup_status", "read_local_artifact", "search_literature", "fetch_source",
                      "store_source", "store_claim", "search_knowledge", "record_experiment", "run_neural_pilot"},
    "researcher": {"search_literature", "fetch_source", "store_source", "search_knowledge"},
    "evidence_reviewer": {"search_knowledge", "fetch_source", "store_claim"},
    "hypothesis_planner": {"search_knowledge", "get_setup_status", "store_claim"},
    "experimenter": {"get_setup_status", "read_local_artifact", "run_neural_pilot", "record_experiment", "search_knowledge"},
    "analyst": {"search_knowledge", "read_local_artifact", "record_experiment"},
}

FIRST_PROMPT = (
    "Starte den kleinen lokalen Setup-Discovery-Durchlauf. Prüfe vorhandene v783-Daten und echte "
    "Setup-Run-Records; verwende einen vorhandenen technischen Pilot statt ihn unnötig zu wiederholen. "
    "Delegiere Recherche und Evidenzprüfung über BrightData und die lokale Knowledgebase. "
    "Entwirf zwei konkrete zukünftige Tests und wähle einen nach Erkenntniswert/Machbarkeit/Kosten. "
    "Lass den Experiment-Agenten die tatsächlichen Setup-Messwerte prüfen/importieren, dann den "
    "Analyse-Agenten eine ergebnisabhängige nächste Entscheidung treffen. Höchstens zwei Suchen, "
    "zwei Fetches und ein neuer 20-ms-Pilot, falls noch keiner vorliegt. Kein Körper-/Flugnachweis "
    "und keine abgeschlossene biologische C3-Experiment-Schleife behaupten. Dokumentiere echte "
    "Agenten-Handoffs, Quellen, Messwerte, offene Voraussetzungen und die nächste Aktion."
)


def validate_setup() -> dict[str, Any]:
    """Load actual Omnigent schemas, specialist tools, and policies offline."""
    from omnigent.spec import load
    from omnigent.tools.local import load_local_python_tools
    from omnigent.policies.function import resolve_function_policy
    from scripts.omnigent_tools import get_setup_status
    from scripts.omnigent_policies import bounded_tool_access
    from scripts.brightdata_client import BrightDataConfig

    installed = importlib.metadata.version("omnigent")
    if installed != "0.16.0":
        raise ValueError(f"Validated version is omnigent==0.16.0; found {installed}")
    spec = load(BUNDLE, expand_env=False)
    agents: list[dict[str, Any]] = []
    for agent in [spec, *spec.sub_agents]:
        folder = BUNDLE / "agents" / agent.source_rel_dir if agent.source_rel_dir else BUNDLE
        tools = load_local_python_tools(agent.local_tools, folder, sandbox_enabled=False, agent_name=agent.name)
        actual = {tool.name() for tool in tools}
        if actual != EXPECTED_TOOLS.get(agent.name):
            raise ValueError(f"Incorrect tool surface for {agent.name}")
        if {tool.name for tool in agent.local_tools} != actual:
            raise ValueError(f"Runner file-tool names and callable names differ for {agent.name}")
        if not agent.instructions or len(agent.instructions) < 300 or agent.os_env is not None:
            raise ValueError(f"Missing instructions or unexpected OS grant for {agent.name}")
        if agent.guardrails is None:
            raise ValueError(f"Missing policies for {agent.name}")
        for policy in agent.guardrails.policies:
            resolve_function_policy(policy)
        agents.append({"name": agent.name, "tools": sorted(actual),
                       "policies": [policy.name for policy in agent.guardrails.policies]})
    allowed = bounded_tool_access({"type": "tool_call", "data": {"name": "search_knowledge"}})
    denied = bounded_tool_access({"type": "tool_call", "data": {"name": "sys_os_shell"}})
    if not allowed or allowed["result"] != "ALLOW" or not denied or denied["result"] != "DENY":
        raise ValueError("Tool-rights policy did not enforce its declared scope")
    brightdata = BrightDataConfig.from_environment().readiness()
    missing = (["ANTHROPIC_API_KEY"] if not os.environ.get("ANTHROPIC_API_KEY") else [])
    missing += brightdata["missing_variables"]
    return {"status": "offline_validated", "omnigent_version": installed, "bundle": str(BUNDLE),
            "agents": agents, "local_setup": get_setup_status(),
            "brightdata_readiness": brightdata,
            "live_discovery_verified": False,
            "missing_environment": missing}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Offline-Konfiguration prüfen, ohne bezahlte Aufrufe")
    parser.add_argument("--prompt", default=FIRST_PROMPT, help="Erste Nachricht an den Omnigent-Supervisor")
    parser.add_argument("--model", help="Optional ein Modell, das euer aktiver Claude-Zugang erlaubt")
    args = parser.parse_args()
    try:
        result = validate_setup()
        if args.check:
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if result["missing_environment"]:
            print("Live-Start noch nicht möglich. Fehlende Umgebungsvariablen: " +
                  ", ".join(result["missing_environment"]), file=sys.stderr)
            print("Schlüssel über scripts/with_credentials.py im Terminal verdeckt eingeben; keine Werte im Chat senden.", file=sys.stderr)
            return 2
        executable = ROOT / ".venv" / "bin" / "omnigent"
        if not executable.is_file():
            raise ValueError("Project .venv/bin/omnigent is missing")
        env = dict(os.environ)
        state_root = Path.home() / "Library" / "Application Support" / "FlyDiscovery" / "omnigent"
        env.setdefault("OMNIGENT_DATA_DIR", str(state_root / "data"))
        env.setdefault("OMNIGENT_CONFIG_HOME", str(state_root / "config"))
        env["OMNIGENT_NO_UPDATE_CHECK"] = "1"
        env["OMNIGENT_HOST_NO_OPEN"] = "1"
        env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        # Omnigent's host->runner environment is deny-by-default. These
        # research tool inputs are intentional; no blanket secret passthrough.
        research_inputs = {
            "BRIGHTDATA_API_KEY", "BRIGHTDATA_SERP_ZONE", "BRIGHTDATA_UNLOCKER_ZONE",
            "BRIGHTDATA_MAX_REQUESTS", "BRIGHTDATA_MAX_COST_USD", "BRIGHTDATA_ESTIMATED_REQUEST_COST_USD",
            "BRIGHTDATA_ALLOWED_DOMAINS", "RESEARCH_KB_DIR",
        }
        existing_inputs = {name.strip() for name in env.get("OMNIGENT_RUNNER_ENV_PASSTHROUGH", "").split(",") if name.strip()}
        env["OMNIGENT_RUNNER_ENV_PASSTHROUGH"] = ",".join(sorted(existing_inputs | research_inputs))
        command = [str(executable), "run", str(BUNDLE), "--server", "local", "-p", args.prompt]
        if args.model:
            command += ["--model", args.model]
        print("Starte native Omnigent-Orchestrierung mit fünf Spezialagenten. Die Weboberfläche bleibt lokal.")
        print("Modellkosten werden pro Session und Agentenbaum gemessen; BrightData hat einen separaten Request-/Schätzbudgetzähler.")
        return subprocess.call(command, cwd=ROOT, env=env)
    except (ValueError, ImportError, RuntimeError, OSError) as exc:
        print(f"Setup konnte nicht gestartet werden: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
