"""Check that ANTHROPIC_API_KEY works, without printing it.

Reads the key like the lab does (environment first, then the repo-root .env), sends ONE
minimal request (claude-haiku-4-5, max 5 output tokens, well under one cent) and prints
only the outcome. Standard library only, so it runs without the project venv:

    python3 scripts/check_anthropic_key.py
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = "claude-haiku-4-5-20251001"


def env_value(name: str) -> str:
    v = os.environ.get(name, "").strip()
    if v:
        return v
    try:
        for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def main() -> int:
    key = env_value("ANTHROPIC_API_KEY")
    if not key:
        print("ANTHROPIC_API_KEY is empty: paste your key into .env (repo root) or export it, then rerun.")
        return 2
    source = "environment" if os.environ.get("ANTHROPIC_API_KEY") else ".env"
    print(f"key found in {source} (prefix {key[:7]}…, length {len(key)})")
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    ws = env_value("ANTHROPIC_WORKSPACE_ID")
    if ws:
        headers["anthropic-workspace-id"] = ws
    body = json.dumps({"model": MODEL, "max_tokens": 5,
                       "messages": [{"role": "user", "content": "Reply with: ok"}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read()).get("error", {})
        except (ValueError, AttributeError):
            err = {}
        print(f"FAILED: HTTP {e.code} {err.get('type', '')}: {err.get('message', e.reason)}")
        return 1
    except urllib.error.URLError as e:
        print(f"FAILED: network error: {e.reason}")
        return 1
    u = data.get("usage", {})
    print(f"OK: {data.get('model')} answered; usage {u.get('input_tokens')} in / {u.get('output_tokens')} out tokens")
    return 0


if __name__ == "__main__":
    sys.exit(main())
