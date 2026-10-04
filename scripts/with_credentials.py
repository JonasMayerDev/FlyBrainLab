"""Run a project command with secrets entered via hidden terminal input.

No credential file, shell expansion or command-line secret arguments are used.
The child inherits secrets via its environment for this process lifetime only.
"""
from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path
import subprocess
import sys


def require_value(env: dict[str, str], name: str, *, secret: bool) -> None:
    if env.get(name):
        return
    if not sys.stdin.isatty():
        raise ValueError(f"{name} fehlt. Dieses Skript in einem interaktiven Terminal starten.")
    label = f"{name} (verdeckte Eingabe): " if secret else f"{name}: "
    value = (getpass.getpass(label) if secret else input(label)).strip()
    if not value or any(c in value for c in ("\n", "\r", "\x00")):
        raise ValueError(f"{name}: leerer oder ungültiger Wert; kein Prozess gestartet.")
    env[name] = value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anthropic", action="store_true", help="Anthropic-Key im Terminal abfragen")
    parser.add_argument("--brightdata", action="store_true", help="BrightData-Key, SERP-Zone und Budget abfragen")
    parser.add_argument("--unlocker", action="store_true", help="Zusätzlich BrightData-Unlocker-Zone abfragen")
    parser.add_argument("--brightdata-mcp", action="store_true", help="BrightData-MCP mit bestätigtem Freikontingent, ohne Produktzonen")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("Befehl nach -- angeben; zum Beispiel -- .venv/bin/python scripts/omnigent_run.py")
    if args.brightdata_mcp and (args.brightdata or args.unlocker):
        parser.error("--brightdata-mcp separat verwenden; --brightdata/--unlocker wählen die REST-Route.")
    env = dict(os.environ)
    root = Path(__file__).resolve().parents[1]
    try:
        if args.anthropic:
            require_value(env, "ANTHROPIC_API_KEY", secret=True)
        if args.brightdata_mcp:
            require_value(env, "BRIGHTDATA_API_KEY", secret=True)
            print("Verbleibende kostenlose MCP-Aufrufe zuerst im BrightData-Dashboard prüfen.")
            require_value(env, "BRIGHTDATA_FREE_REQUEST_ALLOWANCE", secret=False)
            allowance = int(env["BRIGHTDATA_FREE_REQUEST_ALLOWANCE"])
            max_requests = min(int(env.get("BRIGHTDATA_MAX_REQUESTS", "2")), 2, allowance)
            if allowance < 1 or max_requests < 1:
                raise ValueError("BrightData-MCP: bestätigtes Freikontingent und mindestens ein Request erforderlich.")
            env["BRIGHTDATA_TRANSPORT"] = "mcp"
            env["BRIGHTDATA_MAX_REQUESTS"] = str(max_requests)
            env["BRIGHTDATA_MAX_COST_USD"] = "0"
            env["BRIGHTDATA_ESTIMATED_REQUEST_COST_USD"] = "0"
            print(f"BrightData-MCP: maximal {max_requests} gezählte Versuche aus dem bestätigten Freikontingent.")
            print("Der lokale Zähler begrenzt Aufrufe; das gemeinsame Anbieter-Freikontingent separat im Blick behalten.")
        if args.brightdata or args.unlocker:
            env["BRIGHTDATA_TRANSPORT"] = "rest"
            require_value(env, "BRIGHTDATA_API_KEY", secret=True)
            if args.brightdata:
                require_value(env, "BRIGHTDATA_SERP_ZONE", secret=False)
            if args.unlocker:
                require_value(env, "BRIGHTDATA_UNLOCKER_ZONE", secret=False)
            max_requests = min(int(env.get("BRIGHTDATA_MAX_REQUESTS", "10")), 10)
            max_cost = min(float(env.get("BRIGHTDATA_MAX_COST_USD", "1")), 1.0)
            if max_requests < 1 or not 0 < max_cost <= 1:
                raise ValueError("BrightData: positives Request- und Schätzbudget erforderlich.")
            env["BRIGHTDATA_MAX_REQUESTS"] = str(max_requests)
            env["BRIGHTDATA_MAX_COST_USD"] = str(max_cost)
            print(f"BrightData: maximal {max_requests} Requests / {max_cost:g} USD Schätzbudget.")
            print("Der Preis je Request muss aus eurem aktiven Produktplan stammen.")
            require_value(env, "BRIGHTDATA_ESTIMATED_REQUEST_COST_USD", secret=False)
        if sys.platform == "darwin":
            state_root = Path.home() / "Library/Application Support/FlyDiscovery/omnigent"
        else:
            state_root = Path(env.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "FlyDiscovery/omnigent"
        env["OMNIGENT_DATA_DIR"] = str(state_root / "data")
        env["OMNIGENT_CONFIG_HOME"] = str(state_root / "config")
        env["OMNIGENT_NO_UPDATE_CHECK"] = "1"
        env["OMNIGENT_HOST_NO_OPEN"] = "1"
        print("Starte Projektbefehl. Schlüssel werden weder angezeigt noch in einer Datei gespeichert.")
        return subprocess.call(command, cwd=root, env=env)
    except (ValueError, EOFError, KeyboardInterrupt) as exc:
        if isinstance(exc, ValueError):
            print(str(exc), file=sys.stderr)
        else:
            print("Abgebrochen; kein neuer Prozess gestartet.", file=sys.stderr)
        return 2
    except OSError:
        print("Projektbefehl konnte nicht gestartet werden. Pfad/Installation prüfen.", file=sys.stderr)
        return 2
    finally:
        for key in ("ANTHROPIC_API_KEY", "BRIGHTDATA_API_KEY"):
            env.pop(key, None)


if __name__ == "__main__":
    raise SystemExit(main())
