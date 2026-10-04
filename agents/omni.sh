#!/usr/bin/env bash
# Omnigent launcher for the Embodied Fly Lab on macOS / Linux (bash twin of agents/omni.ps1).
#
# Omnigent state lives outside the repo, keys are loaded from the repo-root .env (values never
# printed), the workspace-header proxy starts when ANTHROPIC_WORKSPACE_ID is set, and the lab runs
# with the project venv (.venv) so flylab.tools imports.
#
#   agents/omni.sh -ApproveAtLaunch lab "<question>"     # scripted full-lab run; the human pre-approves at launch
#   agents/omni.sh server --agent agents/fly_lab.yaml    # web UI (approve gates in the browser)
#   agents/omni.sh stop                                  # stop Omnigent server/daemon and the proxy
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
APPROVE=0
[[ "${1:-}" == "-ApproveAtLaunch" ]] && { APPROVE=1; shift; }
[[ $# -eq 0 ]] && set -- --help

if [[ "$(uname)" == "Darwin" ]]; then STATE="$HOME/Library/Application Support/FlyDiscovery/embodied-omnigent"
else STATE="${XDG_DATA_HOME:-$HOME/.local/share}/FlyDiscovery/embodied-omnigent"; fi
mkdir -p "$STATE/logs"
export OMNIGENT_CONFIG_HOME="$STATE" OMNIGENT_DATA_DIR="$STATE"
export DO_NOT_TRACK=1 OMNIGENT_ANALYTICS=0 OMNIGENT_NO_UPDATE_CHECK=1 OMNIGENT_HOST_NO_OPEN=1 PYTHONUTF8=1
export PATH="$ROOT/.venv/bin:$HOME/.local/bin:$PATH"   # omnigent + claude CLI for the claude-sdk harness

# Non-empty KEY=VALUE pairs from .env, without echoing values; the shell environment wins.
if [[ -f "$ROOT/.env" ]]; then
  while IFS= read -r line; do
    [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=[[:space:]]*(.*)$ ]] || continue
    k="${BASH_REMATCH[1]}"; v="${BASH_REMATCH[2]}"; v="${v%\"}"; v="${v#\"}"; v="${v%\'}"; v="${v#\'}"
    v="$(printf '%s' "$v" | sed -e 's/[[:space:]]*$//')"
    if [[ -n "$v" && -z "${!k:-}" ]]; then export "$k=$v"; echo "loaded $k from .env"; fi
  done < "$ROOT/.env"
fi

# Do not inherit an API endpoint or auth token from a parent tool (e.g. a Claude Code session): the lab
# talks to api.anthropic.com with the .env key, via the workspace proxy below when it is configured.
unset ANTHROPIC_BASE_URL ANTHROPIC_AUTH_TOKEN CLAUDECODE CLAUDE_CODE_ENTRYPOINT

PROXY_PORT="${FLYLAB_WS_PROXY_PORT:-8788}"
PROXY_URL="http://127.0.0.1:$PROXY_PORT"
proxy_ok() { [[ "$(curl -s --max-time 2 "$PROXY_URL/__flylab_proxy_health" 2>/dev/null)" == "ok" ]]; }

if [[ "$1" == "stop" ]]; then
  "$ROOT/.venv/bin/omnigent" stop || true
  pkill -f "anthropic_ws_proxy.py" && echo "workspace-header proxy stopped" || true
  exit 0
fi

if [[ -n "${ANTHROPIC_WORKSPACE_ID:-}" ]]; then
  if ! proxy_ok; then
    nohup "$PY" "$ROOT/agents/anthropic_ws_proxy.py" --port "$PROXY_PORT" --log "$STATE/logs/ws_proxy.log" >/dev/null 2>&1 &
    for _ in $(seq 1 30); do sleep 0.5; proxy_ok && break; done
    proxy_ok && echo "workspace-header proxy started on $PROXY_URL" || echo "WARNING: workspace-header proxy did not start ($STATE/logs/ws_proxy.log)"
  else
    echo "workspace-header proxy already running on $PROXY_URL"
  fi
  export ANTHROPIC_BASE_URL="$PROXY_URL"
fi

PREFLAG="$ROOT/data/cache/FLYLAB_PREAPPROVE"
cleanup() { [[ $APPROVE -eq 1 && -f "$PREFLAG" ]] && rm -f "$PREFLAG" && echo "pre-approval flag removed"; true; }
trap cleanup EXIT
if [[ $APPROVE -eq 1 ]]; then
  mkdir -p "$(dirname "$PREFLAG")"
  printf '{"by": "%s (human) at launch via agents/omni.sh -ApproveAtLaunch", "ts": "%s", "caps": "max 6 embodied runs, <= 40 screen candidates per call, cost_budget, 90 tool calls per session"}' \
    "${FLYLAB_APPROVER:-$USER}" "$(date +%Y-%m-%dT%H:%M:%S)" > "$PREFLAG"
  echo "PRE-APPROVED: gated lab actions run without prompts for this command (caps still enforced)"
elif [[ -f "$PREFLAG" ]]; then
  rm -f "$PREFLAG"; echo "stale pre-approval flag removed"
fi

cd "$ROOT"
if [[ "$1" == "lab" ]]; then
  shift
  "$PY" agents/run_lab.py "$@"
else
  "$ROOT/.venv/bin/omnigent" "$@"
fi
