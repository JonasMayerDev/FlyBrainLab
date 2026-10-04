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
import shutil
import tempfile
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
for role in ("fly_discovery", "researcher", "evidence_reviewer", "hypothesis_planner", "analyst"):
    EXPECTED_TOOLS[role].add("read_source_snapshot")
for role in ("fly_discovery", "experimenter"):
    EXPECTED_TOOLS[role].add("run_frozen_experiment")
for role in ("fly_discovery", "analyst"):
    EXPECTED_TOOLS[role].add("save_discovery_record")

DISCOVERY_PROMPT = (
    "Führe die tatsächliche DNg02-Forschungsschleife durch. Nutze die lokal gespeicherten echten "
    "Primärquellen, research/designs/dng02-input-v1.json und research/evidence/dng02_targets.json. "
    "Delegiere native Omnigent-Spezialagenten: researcher prüft Quellenfassungen; evidence_reviewer "
    "prüft DNg02-Funktionsbefund und v783-Zuordnung; hypothesis_planner prüft die zwei vorab "
    "eingefrorenen Testdesigns. Erst dann führt experimenter über run_frozen_experiment den "
    "neuen Test A aus. Analyst liest die echten Ergebnisse, beurteilt Kontrollen und entscheidet "
    "ergebnisabhängig zwischen Test B und direkter Kalibrierung als nächstem Experiment. "
    "Mindestens zwei Kandidaten, begründete Auswahl, strukturierte Quellen-/Claim-/Receipt-IDs "
    "und next decision erhalten. Analyst speichert mit save_discovery_record. Nutze keine "
    "alten manuellen Runs als Ersatz für die neue native Toolausführung. DNg02 reguliert nach "
    "Literatur Flügelamplitude bei bereits fliegenden Fliegen; kein Fluginitiations- oder "
    "allgemeiner biologischer Validierungsnachweis. Fehlende BrightData-Anmeldung ehrlich nennen, "
    "keine BrightData-Anfragen im Modus existing. Nach dem gespeicherten Ergebnis beenden."
)


def prepare_bundle(harness: str, model: str | None, evidence_mode: str) -> Path:
    """Produce an isolated native bundle; never edit user-level CLI settings."""
    import yaml
    path = Path(tempfile.mkdtemp(prefix="flybrain-omnigent-bundle-"))
    shutil.copytree(BUNDLE, path, dirs_exist_ok=True)
    for config in path.rglob("config.yaml"):
        data = yaml.safe_load(config.read_text())
        data["executor"]["config"]["harness"] = harness
        if model:
            data["executor"]["model"] = model
        data["skills"] = "none"
        data["tools"]["timeout"] = 600
        for policy in data.get("guardrails", {}).get("policies", {}).values():
            function = policy.get("function")
            if harness == "codex" and isinstance(function, dict) and "max_tool_calls_per_session" in str(function.get("path")):
                function["arguments"]["limit"] = 40 if data["name"] == "fly_discovery" else 20
            if isinstance(function, dict) and "expensive_models" in function.get("arguments", {}):
                function["arguments"]["expensive_models"] = ["claude", "sonnet", "haiku", "opus", "gpt"]
                # Subscription Codex still reports API-equivalent cost estimates.
                # Keep a bounded complete-loop allowance; no API key/purchase is added.
                if harness == "codex":
                    role = data["name"]
                    function["arguments"]["max_cost_usd"] = (16.0 if "subagent_cost_budget" in str(function.get("path"))
                        else 6.0)
        config.write_text(yaml.safe_dump(data, sort_keys=False))
    if evidence_mode == "existing":
        for filename in ("search_literature.py", "fetch_source.py"):
            for tool in path.rglob(filename):
                tool.unlink()
    return path

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


def validate_setup(bundle: Path = BUNDLE, harness: str = "claude-sdk", evidence_mode: str = "brightdata") -> dict[str, Any]:
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
    spec = load(bundle, expand_env=False)
    agents: list[dict[str, Any]] = []
    for agent in [spec, *spec.sub_agents]:
        folder = bundle / "agents" / agent.source_rel_dir if agent.source_rel_dir else bundle
        tools = load_local_python_tools(agent.local_tools, folder, sandbox_enabled=False, agent_name=agent.name)
        actual = {tool.name() for tool in tools}
        expected = set(EXPECTED_TOOLS.get(agent.name, set()))
        if evidence_mode == "existing":
            expected -= {"search_literature", "fetch_source"}
        if actual != expected:
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
    startup = bounded_tool_access({"type": "tool_call", "data": {"name": "sys_agent_start"}})
    allowed = bounded_tool_access({"type": "tool_call", "data": {"name": "search_knowledge"}})
    denied = bounded_tool_access({"type": "tool_call", "data": {"name": "sys_os_shell"}})
    if not startup or startup["result"] != "ALLOW" or not allowed or allowed["result"] != "ALLOW" or not denied or denied["result"] != "DENY":
        raise ValueError("Tool-rights policy did not enforce its declared scope")
    brightdata = BrightDataConfig.from_environment().readiness()
    missing = (["ANTHROPIC_API_KEY"] if harness == "claude-sdk" and not os.environ.get("ANTHROPIC_API_KEY") else [])
    if evidence_mode == "brightdata":
        missing += brightdata["missing_variables"]
    return {"status": "offline_validated", "omnigent_version": installed, "bundle": str(bundle),
            "harness": harness, "evidence_mode": evidence_mode,
            "agents": agents, "local_setup": get_setup_status(),
            "brightdata_readiness": brightdata,
            "live_discovery_verified": False,
            "missing_environment": missing}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Offline-Konfiguration prüfen, ohne bezahlte Aufrufe")
    parser.add_argument("--prompt", help="Erste Nachricht an den Omnigent-Supervisor")
    parser.add_argument("--harness", choices=("claude-sdk", "codex"), default="claude-sdk")
    parser.add_argument("--evidence-mode", choices=("brightdata", "existing"), default="brightdata")
    parser.add_argument("--discovery", action="store_true", help="Neuen eingefrorenen DNg02-Test mit Handoffs ausführen")
    parser.add_argument("--model", help="Optional ein vom tatsächlichen Modellzugang unterstütztes Modell")
    parser.add_argument("--resume", help="Native bestehende Conversation-ID weiterführen; keine Handoffs nachbilden")
    args = parser.parse_args()
    try:
        bundle = prepare_bundle(args.harness, args.model, args.evidence_mode)
        result = validate_setup(bundle, args.harness, args.evidence_mode)
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
        state_root = Path.home() / "Library" / "Application Support" / "FlyDiscovery" / ("omnigent-codex" if args.harness == "codex" else "omnigent")
        env.setdefault("OMNIGENT_DATA_DIR", str(state_root / "data"))
        env.setdefault("OMNIGENT_CONFIG_HOME", str(state_root / "config"))
        env["OMNIGENT_NO_UPDATE_CHECK"] = "1"
        env["OMNIGENT_HOST_NO_OPEN"] = "1"
        if args.harness == "codex":
            executable_codex = shutil.which("codex")
            if not executable_codex:
                raise ValueError("Codex CLI fehlt; keine neue Anmeldung automatisch erstellen")
            auth = subprocess.run([executable_codex, "login", "status"], capture_output=True, text=True)
            if auth.returncode != 0:
                raise ValueError("Codex CLI ist nicht angemeldet; menschliche Anmeldung erforderlich")
            # Omnigent's subscription provider lets the CLI select its model.
            # A per-process wrapper selects the requested account-supported model
            # and suppresses unrelated user-config MCP servers. No auth is copied.
            import shlex
            wrapper = bundle / "codex-project-cli"
            overrides = " -c 'mcp_servers={}' -c 'features.shell_tool=false' -c 'features.unified_exec=false' -c 'web_search=\"disabled\"'"
            if args.model:
                overrides += " -c " + shlex.quote("model=" + json.dumps(args.model))
            # app-server owns its own -c flags; append after the subcommand.
            wrapper.write_text("#!/bin/sh\nexec " + shlex.quote(executable_codex) + ' "$@"' + overrides + "\n")
            wrapper.chmod(0o700)
            env["OMNIGENT_CODEX_PATH"] = str(wrapper)
            env["HARNESS_CODEX_DISABLE_NATIVE_TOOLS"] = "1"
            env["HARNESS_CODEX_ENABLE_WEB_SEARCH"] = "0"
        env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        # Omnigent's host->runner environment is deny-by-default. These
        # research tool inputs are intentional; no blanket secret passthrough.
        research_inputs = {
            "BRIGHTDATA_API_KEY", "BRIGHTDATA_SERP_ZONE", "BRIGHTDATA_UNLOCKER_ZONE",
            "BRIGHTDATA_MAX_REQUESTS", "BRIGHTDATA_MAX_COST_USD", "BRIGHTDATA_ESTIMATED_REQUEST_COST_USD",
            "BRIGHTDATA_TRANSPORT", "BRIGHTDATA_FREE_REQUEST_ALLOWANCE",
            "BRIGHTDATA_ALLOWED_DOMAINS", "RESEARCH_KB_DIR",
            "OMNIGENT_CODEX_PATH", "HARNESS_CODEX_DISABLE_NATIVE_TOOLS", "HARNESS_CODEX_ENABLE_WEB_SEARCH",
        }
        existing_inputs = {name.strip() for name in env.get("OMNIGENT_RUNNER_ENV_PASSTHROUGH", "").split(",") if name.strip()}
        env["OMNIGENT_RUNNER_ENV_PASSTHROUGH"] = ",".join(sorted(existing_inputs | research_inputs))
        prompt = args.prompt or (DISCOVERY_PROMPT if args.discovery else FIRST_PROMPT)
        command = [str(executable), "run", str(bundle), "--server", "local", "-p", prompt]
        if args.model:
            command += ["--model", args.model]
        if args.resume:
            if not __import__("re").fullmatch(r"[a-f0-9]{32}", args.resume):
                raise ValueError("Resume requires an actual native32hex conversation ID")
            command += ["--resume", args.resume]
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
