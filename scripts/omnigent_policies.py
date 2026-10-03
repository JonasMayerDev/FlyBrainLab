"""Native Omnigent policy: expose only the setup/research tool surface."""

from __future__ import annotations

from typing import Any


def bounded_tool_access(event: dict[str, Any]) -> dict[str, Any] | None:
    """Block arbitrary OS, deployment, sharing, and credential-management tools.

    The user authorized local setup, research, KB writes, and small pilots.
    Omnigent's lifecycle/declared sub-agent tools remain available.
    """
    if event.get("type") != "tool_call":
        return None
    data = event.get("data") or {}
    target = str(data.get("name") or event.get("target") or "")
    # Harness MCP wrappers qualify names; compare the final tool component.
    name = target.rsplit("__", 1)[-1]
    allowed = {
        "get_setup_status", "read_local_artifact", "search_literature", "fetch_source",
        "store_source", "store_claim", "search_knowledge", "record_experiment",
        "run_neural_pilot", "researcher", "evidence_reviewer", "hypothesis_planner",
        "experimenter", "analyst", "sys_session_send", "sys_session_get_info",
        "sys_session_get_history", "sys_session_get_usage", "sys_read_inbox",
        "sys_session_list", "sys_session_cancel", "sys_cancel_async",
    }
    if name in allowed:
        return {"result": "ALLOW"}
    if name == "sys_call_async":
        arguments = data.get("arguments") or {}
        requested = str(arguments.get("tool") or arguments.get("name") or "").rsplit("__", 1)[-1]
        if requested in allowed:
            return {"result": "ALLOW"}
    return {"result": "DENY", "reason": "This setup session permits only declared local research, KB, pilot, and agent lifecycle tools."}
