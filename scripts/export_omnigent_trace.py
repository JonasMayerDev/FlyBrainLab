"""Export and audit one native Omnigent session tree, excluding source full text.

The local database is evidence. This script only reads the requested session's
items and role metadata; it never exports auth/session state or account tables.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from scripts.kb_store import atomic_json, utc_now

ROOT = Path(__file__).resolve().parents[1]
ROLES = {"researcher", "evidence_reviewer", "hypothesis_planner", "experimenter", "analyst"}
COMPLETED_ITEM = 1  # Persisted Omnigent 0.16 conversation item status.
NATIVE_MUTATION_TOOLS = {"shell", "apply_patch", "Bash", "Shell", "Write", "Edit", "MultiEdit"}
NATIVE_MUTATION_TOOLS |= {"sys_os_shell", "sys_os_write", "sys_os_edit", "exec_command", "bash", "write", "edit"}


def clean(value):
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items()
                if key.casefold() not in {"authorization", "api_key", "access_token", "refresh_token", "session_state", "runner_id", "host_id"}}
    if isinstance(value, list):
        return [clean(item) for item in value]
    if isinstance(value, str):
        if re.search(r"(?:sk-ant-|sk-proj-|ghp_|gho_)[A-Za-z0-9_-]{16,}", value):
            raise ValueError("Credential-looking content found: export stopped")
        return value.replace(str(ROOT), "<project>").replace(str(Path.home()), "<user-home>")
    return value


def parsed_json(value):
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
    return value


def assistant_text(item):
    data = item["data"]
    if item["type"] != 1 or data.get("role") != "assistant":
        return ""
    return "\n".join(block.get("text", "") for block in data.get("content", [])
                     if isinstance(block, dict) and isinstance(block.get("text"), str)).strip()


def successful_output(value):
    if isinstance(value, str):
        return not value.strip().casefold().startswith(("error:", "denied by policy", "failed:"))
    return not (isinstance(value, dict) and
                (value.get("error") or value.get("status") in {"failed", "error", "unavailable", "denied"}))


def tool_events(session):
    pending, events = {}, []
    for item in session["items"]:
        data = item["data"]
        if item["type"] == 2:
            pending[data.get("call_id")] = item
        elif item["type"] == 3 and data.get("call_id") in pending:
            call = pending[data["call_id"]]
            output = parsed_json(data.get("output"))
            events.append({"name": str(call["data"].get("name", "")).rsplit("__", 1)[-1],
                           "arguments": parsed_json(call["data"].get("arguments", {})),
                           "call": call, "result": item, "output": output,
                           "success": call["status"] == COMPLETED_ITEM and
                                      item["status"] == COMPLETED_ITEM and successful_output(output)})
    return events


def checked_artifact(path, directory):
    if not isinstance(path, str) or Path(path).is_absolute():
        raise ValueError("Expected a project-relative artifact path")
    resolved = (ROOT / path).resolve()
    resolved.relative_to((ROOT / directory).resolve())
    if not resolved.is_file():
        raise ValueError("Missing artifact: " + path)
    return resolved, json.loads(resolved.read_text())


def numeric_integrity(event):
    """Bind persisted tool output to sealed design, comparison and real spikes.

    Hashes below describe artifacts at verification time. A receipt did not
    originally seal every raw output, so this is not an immutable archival proof.
    """
    from simulation.experiment import summarize
    import pyarrow.parquet as pq

    output = event["output"]
    receipt_id = output.get("receipt_id", "")
    if not re.fullmatch(r"tool_[a-f0-9]{32}", receipt_id):
        raise ValueError("Malformed numeric receipt ID")
    expected_path = "data/discovery/tool-receipts/" + receipt_id + ".json"
    if output.get("receipt_path") != expected_path:
        raise ValueError("Numeric receipt path does not match its ID")
    receipt_path, receipt = checked_artifact(expected_path, "data/discovery/tool-receipts")
    if receipt != {k: v for k, v in output.items() if k != "receipt_path"}:
        raise ValueError("Persisted numeric receipt differs from native tool output")
    design_path, design = checked_artifact(receipt["design_path"], "research/designs")
    design_hash = hashlib.sha256(design_path.read_bytes()).hexdigest()
    seal = design_path.with_suffix(".sha256")
    if not seal.exists() or seal.read_text().split()[0] != design_hash or receipt["design_sha256"] != design_hash:
        raise ValueError("Design seal/receipt digest mismatch")
    target = (ROOT / design["target_file"]).resolve()
    target.relative_to((ROOT / "research").resolve())
    if hashlib.sha256(target.read_bytes()).hexdigest() != design["target_file_sha256"]:
        raise ValueError("Frozen target evidence digest mismatch")
    result = receipt["result"]
    comparison_path, comparison = checked_artifact(result["comparison_path"], "data/experiments")
    if comparison != result or result.get("status") != "completed" or result.get("design_sha256") != design_hash:
        raise ValueError("Comparison differs from the completed receipt result")
    test = receipt["test"]
    conditions = {"A": {"sham", "upstream_drive"}, "B": {"upstream_drive", "outgoing_disconnected"},
                  "calibration": {"sham", "direct_dng02"}}[test]
    if result.get("test") != test or len(result["runs"]) != len(design["seeds"]) * len(conditions):
        raise ValueError("Comparison test/run count does not match frozen design")
    records, hashes, pairs = [], {}, set()
    if result["run_ids"] != [r["run_id"] for r in result["runs"]]:
        raise ValueError("Comparison run ID list differs from its run entries")
    for entry in result["runs"]:
        run_id = entry["run_id"]
        if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id) or entry["result_path"] != "data/runs/" + run_id:
            raise ValueError("Run identity/path mismatch")
        run_path, run = checked_artifact(entry["result_path"] + "/run.json", "data/runs")
        if any(run.get(k) != entry[k] for k in ("run_id", "condition", "seed", "result_path", "wall_seconds", "readout_metrics")):
            raise ValueError("Run record differs from native comparison: " + run_id)
        if (run.get("status") != "completed" or run.get("design_sha256") != design_hash or
                run.get("dataset_version") != design["dataset_version"] or
                run.get("model_commit") != design["model_commit"] or
                run.get("duration_ms") != design["duration_ms"] or
                run.get("timestep_ms") != design["timestep_ms"] or
                run.get("readout_neuron_ids") != design["readout_ids"] or
                run.get("stimulated_neuron_ids") != (design["readout_ids"] if run["condition"] == "direct_dng02" else design["stimulus_ids"]) or
                run.get("stimulus_rate_hz") != (0 if run["condition"] == "sham" else design["stimulus_rate_hz"]) or
                run.get("full_network_included") is not True or
                run.get("execution_context") != "Omnigent native tool"):
            raise ValueError("Run does not match frozen native assay: " + run_id)
        pair = (run["seed"], run["condition"])
        if pair in pairs or pair[0] not in design["seeds"] or pair[1] not in conditions:
            raise ValueError("Duplicate/unregistered seed or condition")
        pairs.add(pair)
        readout_path, readout = checked_artifact(entry["result_path"] + "/readout.json", "data/runs")
        event_path, events = checked_artifact(entry["result_path"] + "/readout_spikes.json", "data/runs")
        if (readout != run["readout_metrics"] or events.get("events_are_complete") is not True or
                events.get("duration_ms") != design["duration_ms"] or events.get("readout_neuron_ids") != design["readout_ids"]):
            raise ValueError("Readout artifact does not match run record")
        spike_path = run_path.parent / run.get("spikes_file", "spikes.parquet")
        spike_path.resolve().relative_to(run_path.parent.resolve())
        spikes = pq.read_table(spike_path, columns=["t_seconds", "flywire_id"]).to_pylist()
        if len(spikes) != run["spike_events"] or any(not 0 <= e["t_seconds"] < design["duration_ms"] / 1000 for e in spikes):
            raise ValueError("Raw spike count/time differs from run")
        selected = [{"t_seconds": float(e["t_seconds"]), "flywire_id": e["flywire_id"]}
                    for e in spikes if e["flywire_id"] in design["readout_ids"]]
        counts = Counter(e["flywire_id"] for e in selected)
        per_cell = {cell: counts[cell] for cell in design["readout_ids"]}
        rate = len(selected) / (len(per_cell) * design["duration_ms"] / 1000)
        if (selected != events["events"] or per_cell != readout["per_neuron_spike_counts"] or
                rate != readout["population_mean_rate_hz"]):
            raise ValueError("Raw spikes do not reproduce recorded readout")
        records.append(run)
        for path in (run_path, readout_path, event_path, spike_path):
            hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    if summarize(records, test, design) != result["summary"]:
        raise ValueError("Comparison summary/branch does not reproduce from run records")
    for path in (receipt_path, comparison_path, design_path):
        hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"receipt_id": receipt_id, "test": test, "design_sha256": design_hash,
            "next_test": result["summary"].get("next_test"), "artifact_sha256_at_verification": hashes}


def reverify_prior_trace(reference, context):
    """Recheck an exported native tree and its previously hashed artifacts.

    Never use the exported boolean as evidence. Roots are visited once and
    cycles (including path aliases for the same root) fail closed.
    """
    path, prior = checked_artifact(reference["path"], "data/discovery")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if reference.get("sha256") and reference["sha256"] != digest:
        raise ValueError("Prior trace reference digest mismatch")
    prior_root = prior.get("root_conversation_id", "")
    sessions = prior.get("sessions", [])
    roots = [s for s in sessions if s.get("parent_conversation_id") is None]
    if (not re.fullmatch(r"[a-f0-9]{32}", prior_root) or len(roots) != 1 or
            roots[0].get("conversation_id") != prior_root or
            len({s["conversation_id"] for s in sessions}) != len(sessions)):
        raise ValueError("Prior trace has an invalid or remapped native root")
    if prior_root in context["visiting"]:
        raise ValueError("Cycle in prior native trace roots")
    if prior_root in context["verified"]:
        cached = context["verified"][prior_root]
        if cached["sha256"] != digest:
            raise ValueError("Conflicting prior trace content for the same native root")
        return {**cached, "path": reference["path"]}
    context["visiting"].add(prior_root)
    try:
        verification = verify_tree(sessions, prior.get("prior_traces", []), context)
    finally:
        context["visiting"].remove(prior_root)
    if not verification["passed"]:
        raise ValueError("Prior native tree failed reverification: " + "; ".join(verification["failures"]))
    archived = prior.get("verification", {})
    archived_records = {r["record_id"]: r for r in archived.get("verified_discovery_records", [])}
    for record in verification["verified_discovery_records"]:
        if archived_records.get(record["record_id"], {}).get("sha256") != record["sha256"]:
            raise ValueError("Prior analyst record changed after its recorded trace hash")
    archived_receipts = {r["receipt_id"]: r for r in archived.get("verified_numeric_receipts", [])}
    for receipt in verification["verified_numeric_receipts"]:
        if archived_receipts.get(receipt["receipt_id"], {}).get("artifact_sha256_at_verification") != receipt["artifact_sha256_at_verification"]:
            raise ValueError("Prior receipt/raw artifacts changed after recorded trace hashes")
    proof = {"path": reference["path"], "sha256": digest, "root_conversation_id": prior_root,
             "reverified": True, "verification": verification}
    context["verified"][prior_root] = proof
    return proof


def verify_tree(sessions, prior_traces=None, _context=None):
    """Fail closed on absent handoffs or unlinked numerical/decision artifacts."""
    failures, proofs, all_proofs, numeric, saved = [], {}, {}, [], []
    root = next(s for s in sessions if s["parent_conversation_id"] is None)
    context = _context or {"visiting": {root["conversation_id"]}, "verified": {}}
    external = []
    for reference in prior_traces or []:
        try:
            external.append(reverify_prior_trace(reference, context))
        except (ValueError, KeyError, TypeError, OSError, StopIteration) as exc:
            failures.append("Prior trace reverification failed: " + str(exc))
    root_events = tool_events(root)
    for role in sorted(ROLES):
        candidates = []
        for child in sessions:
            if child["role"] != role or child["parent_conversation_id"] != root["conversation_id"]:
                continue
            child_id = child["conversation_id"]
            launches = [e for e in root_events if e["name"] in {"sys_session_send", role} and e["success"] and
                        isinstance(e["output"], dict) and e["output"].get("conversation_id") == child_id and
                        e["output"].get("agent") == role]
            finals = [i for i in child["items"] if i["status"] == COMPLETED_ITEM and assistant_text(i)]
            if not launches or not finals:
                continue
            marker = "[System: sub-agent task " + child_id + " completed — " + role
            inboxes = [e for e in root_events if e["name"] == "sys_read_inbox" and e["success"] and
                       isinstance(e["output"], str) and marker in e["output"] and
                       " returned: " in e["output"].split(marker, 1)[1]]
            for inbox in inboxes:
                matching = [i for i in finals if i["created_at"] <= inbox["result"]["created_at"]]
                preceding = [e for e in launches if e["call"]["position"] < inbox["result"]["position"]]
                if not matching or not preceding:
                    continue
                final = matching[-1]
                if assistant_text(final)[:120] not in inbox["output"]:
                    continue
                if re.match(r"[\[\s]*(?:You've hit the.*cost budget|Denied by policy:|Exceeded \d+ tool calls|Blocked by.*policy)",
                            assistant_text(final), re.IGNORECASE):
                    continue
                candidates.append({"child": child, "launch": preceding[-1], "final": final, "inbox": inbox})
        if not candidates:
            failures.append("Missing successful final output and collected native handoff: " + role)
        else:
            candidates.sort(key=lambda p: p["inbox"]["result"]["position"])
            all_proofs[role] = candidates
            proofs[role] = candidates[-1]
    order = ["researcher", "evidence_reviewer", "hypothesis_planner", "experimenter", "analyst"]
    for before, after in zip(order, order[1:]):
        if before in proofs and after in proofs and proofs[before]["inbox"]["result"]["position"] >= proofs[after]["launch"]["call"]["position"]:
            failures.append("Specialist launched before preceding handoff was collected: " + after)
    if "researcher" in proofs:
        reads = [e for e in tool_events(proofs["researcher"]["child"]) if e["success"] and
                 e["name"] == "read_source_snapshot" and isinstance(e["output"], dict) and
                 e["output"].get("status") == "retrieved" and re.fullmatch(r"[a-f0-9]{64}", e["output"].get("content_sha256", ""))]
        if not reads:
            failures.append("Researcher has no successful hash-verified primary snapshot read")
    if "evidence_reviewer" in proofs:
        reviews = [e for e in tool_events(proofs["evidence_reviewer"]["child"]) if e["success"] and
                   ((e["name"] == "read_source_snapshot" and isinstance(e["output"], dict) and
                     e["output"].get("status") == "retrieved") or
                    (e["name"] == "search_knowledge" and bool(e["output"].get("result") if isinstance(e["output"], dict) else e["output"])))]
        if not reviews:
            failures.append("Evidence reviewer has no successful primary snapshot or nonempty KB evidence read")
    for session in sessions:
        for event in tool_events(session):
            if event["name"] == "run_frozen_experiment" and event["success"] and isinstance(event["output"], dict):
                try:
                    proof = numeric_integrity(event)
                    proof.update(role=session["role"], conversation_id=session["conversation_id"],
                                 call_created_at=event["call"]["created_at"], result_created_at=event["result"]["created_at"])
                    numeric.append(proof)
                except (ValueError, KeyError, TypeError, OSError, IndexError) as exc:
                    failures.append("Numeric integrity failed: " + str(exc))
            if event["name"] == "save_discovery_record" and event["success"] and isinstance(event["output"], dict):
                saved.append((session, event))
    eligible = []
    for receipt in numeric:
        for completion in all_proofs.get("experimenter", []):
            if (receipt["conversation_id"] == completion["child"]["conversation_id"] and
                    receipt["receipt_id"] in assistant_text(completion["final"]) and
                    any(receipt["call_created_at"] >= p["inbox"]["result"]["created_at"]
                        for p in all_proofs.get("hypothesis_planner", []))):
                receipt["collected_handoff_position"] = completion["inbox"]["result"]["position"]
                receipt["launch_position"] = completion["launch"]["call"]["position"]
                eligible.append(receipt)
                break
    if not eligible:
        failures.append("No intact native experimenter receipt after completed evidence/plan handoffs")
    if eligible and "hypothesis_planner" in proofs:
        plan_text = assistant_text(proofs["hypothesis_planner"]["final"])
        if (eligible[0]["design_sha256"] not in plan_text or
                not re.search(r"\bA\b", plan_text) or not re.search(r"\bB\b", plan_text)):
            failures.append("Planner final does not identify the sealed design and both registered tests A/B")
    record_proofs = []
    for session, event in saved:
        analyst_completion = next((p for p in all_proofs.get("analyst", [])
                                   if session["conversation_id"] == p["child"]["conversation_id"] and
                                   str(event["output"].get("record_id", "")) in assistant_text(p["final"])), None)
        if analyst_completion is None:
            failures.append("Discovery record was not saved by the completed analyst specialist")
            continue
        try:
            output = event["output"]
            path, record = checked_artifact(output["path"], "data/discovery")
            if record["record_id"] != output["record_id"]:
                raise ValueError("Discovery record ID differs from native save output")
            args = event["arguments"]
            submitted = parsed_json(args.get("record_json")) if isinstance(args, dict) else None
            if not isinstance(submitted, dict) or any(record.get(k) != v for k, v in submitted.items()):
                raise ValueError("Saved discovery record differs from analyst tool arguments")
            ids = record.get("tool_receipt_ids", [])
            linked = [n for n in eligible if n["receipt_id"] in ids]
            if not linked or set(ids) != {n["receipt_id"] for n in linked}:
                raise ValueError("Analyst record references receipts outside the verified specialist run")
            if len(set(record.get("candidate_tests", []))) < 2:
                raise ValueError("Analyst record lacks two distinct candidate tests")
            if not record.get("source_ids") or not record.get("claim_ids"):
                raise ValueError("Analyst record lacks source/claim links")
            retrieved_ids = {e["output"].get("source_id") for e in tool_events(proofs["researcher"]["child"])
                             if e["success"] and e["name"] == "read_source_snapshot" and isinstance(e["output"], dict)} if "researcher" in proofs else set()
            if not retrieved_ids.intersection(record["source_ids"]):
                raise ValueError("Analyst source links do not include any actually read researcher primary snapshot")
            selected = str(record.get("selected_test", "")).strip()
            matching = [n for n in linked if n["test"] == selected]
            if not matching:
                raise ValueError("Analyst selected_test does not match its numeric receipt")
            actual = matching[-1]
            if actual["next_test"] is None or record.get("next_test") != actual["next_test"]:
                raise ValueError("Analyst next_test differs from the frozen result-dependent branch")
            if event["call"]["created_at"] < actual["result_created_at"]:
                raise ValueError("Analyst saved the decision before experiment completion")
            analyst_input = json.dumps([i["data"] for i in session["items"] if i["type"] == 1 and i["data"].get("role") == "user"])
            if actual["receipt_id"] not in analyst_input:
                raise ValueError("Native analyst handoff did not supply the actual numeric receipt ID")
            if actual["collected_handoff_position"] >= analyst_completion["launch"]["call"]["position"]:
                raise ValueError("Analyst was launched before its selected experiment handoff was collected")
            if record["record_id"] not in assistant_text(analyst_completion["final"]):
                raise ValueError("Analyst final does not hand off its saved discovery record ID")
            record_proofs.append({"record_id": record["record_id"], "path": output["path"],
                                  "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                  "receipt_ids": ids, "selected_test": selected, "next_test": record["next_test"],
                                  "decision_saved_at": event["result"]["created_at"],
                                  "decision_handoff_collected_at": analyst_completion["inbox"]["result"]["created_at"],
                                  "collected_handoff_position": analyst_completion["inbox"]["result"]["position"]})
        except (ValueError, KeyError, TypeError, OSError) as exc:
            failures.append("Discovery record integrity failed: " + str(exc))
    if not record_proofs:
        failures.append("No intact analyst record linked to the actual experiment and frozen next decision")
    cross_session = []
    for receipt in eligible:
        if receipt["test"] not in {"B", "calibration"}:
            continue
        if any(
                record["selected_test"] == "A" and record["next_test"] == receipt["test"] and
                record["collected_handoff_position"] < receipt["launch_position"] for record in record_proofs):
            continue
        found = False
        for prior in external:
            for decision in prior["verification"]["verified_discovery_records"]:
                if decision["selected_test"] != "A" or decision["next_test"] != receipt["test"]:
                    continue
                source_receipts = [r for r in prior["verification"]["verified_numeric_receipts"]
                                   if r["receipt_id"] in decision["receipt_ids"] and r["test"] == "A" and
                                   r["design_sha256"] == receipt["design_sha256"]]
                if not source_receipts:
                    continue
                _, decision_content = checked_artifact(decision["path"], "data/discovery")
                for read in root_events:
                    output = read["output"]
                    if (read["name"] != "read_local_artifact" or not read["success"] or not isinstance(output, dict) or
                            output.get("status") != "ok" or output.get("path") != decision["path"] or
                            output.get("truncated") is not False or not isinstance(output.get("content"), str) or
                            not isinstance(read["arguments"], dict) or read["arguments"].get("relative_path") != decision["path"]):
                        continue
                    content_sha = hashlib.sha256(output["content"].encode()).hexdigest()
                    planners = [p for p in all_proofs.get("hypothesis_planner", []) if
                                read["result"]["position"] < p["launch"]["call"]["position"] < receipt["launch_position"]]
                    if (content_sha != decision["sha256"] or parsed_json(output["content"]) != decision_content or
                            not planners or read["result"]["created_at"] < decision["decision_handoff_collected_at"] or
                            read["result"]["created_at"] > receipt["call_created_at"]):
                        continue
                    cross_session.append({"current_root_conversation_id": root["conversation_id"],
                        "current_receipt_id": receipt["receipt_id"], "followup_test": receipt["test"],
                        "prior_root_conversation_id": prior["root_conversation_id"],
                        "prior_trace_path": prior["path"], "prior_trace_sha256": prior["sha256"],
                        "prior_tree_reverified": True, "prior_record_id": decision["record_id"],
                        "prior_record_path": decision["path"], "prior_record_sha256": decision["sha256"],
                        "prior_receipt_ids": [r["receipt_id"] for r in source_receipts],
                        "prior_receipt_sha256": {r["receipt_id"]: r["artifact_sha256_at_verification"][
                            "data/discovery/tool-receipts/" + r["receipt_id"] + ".json"] for r in source_receipts},
                        "prior_next_test": decision["next_test"],
                        "prior_decision_collected_at": decision["decision_handoff_collected_at"],
                        "current_record_read": {"path": output["path"], "content_sha256": content_sha,
                            "call_id": read["call"]["data"].get("call_id"), "result_position": read["result"]["position"],
                            "created_at": read["result"]["created_at"],
                            "result_item_sha256": read["result"]["local_item_sha256"]},
                        "current_planner_launch_position": planners[0]["launch"]["call"]["position"],
                        "current_experimenter_launch_position": receipt["launch_position"],
                        "current_numeric_call_created_at": receipt["call_created_at"]})
                    found = True
                    break
                if found:
                    break
            if found:
                break
        if not found:
            failures.append("Follow-up experiment lacks preceding collected result-dependent A decision: " + receipt["test"])
    native = [{"conversation_id": s["conversation_id"], "role": s["role"],
               "name": i["data"].get("name"), "call_created_at": i["created_at"]}
              for s in sessions for i in s["items"] if i["type"] == 2 and
              str(i["data"].get("name", "")).rsplit("__", 1)[-1] in NATIVE_MUTATION_TOOLS]
    return {"passed": not failures, "failures": failures,
            "completed_handoffs": [{"role": role, "conversation_id": p["child"]["conversation_id"],
                "final_item_sha256": p["final"]["local_item_sha256"],
                "inbox_result_item_sha256": p["inbox"]["result"]["local_item_sha256"]}
                for role, completions in all_proofs.items() for p in completions],
            "verified_numeric_receipts": numeric, "verified_discovery_records": record_proofs,
            "cross_session_followup_proofs": cross_session,
            "reverified_prior_traces": [{k: p[k] for k in ("path", "sha256", "root_conversation_id", "reverified")} for p in external],
            "unsuccessful_tool_outputs": [{"role": s["role"], "conversation_id": s["conversation_id"],
                "name": e["name"], "result_item_sha256": e["result"]["local_item_sha256"]}
                for s in sessions for e in tool_events(s) if not e["success"]],
            "sessions_without_successful_collected_handoff": [{"role": s["role"], "conversation_id": s["conversation_id"],
                "live_status": s.get("live_status")}
                for s in sessions if s["role"] in ROLES and not any(
                    p["child"]["conversation_id"] == s["conversation_id"] for p in all_proofs.get(s["role"], []))],
            "no_arbitrary_shell_or_apply_patch_observed": not native, "native_os_activity_observed": native,
            "native_tool_observation_scope": "Selected persisted session tree only; absence is not proof that all native capabilities were technically disabled"}


def runtime_labels(metadata, sessions, include_proof=False):
    labels = {"harness": set(), "model": set()}
    evidence = []
    def visit(value, source, path=""):
        if isinstance(value, dict):
            for key, item in value.items():
                field_path = path + "." + key if path else key
                if key in labels and isinstance(item, str) and item:
                    labels[key].add(item)
                    evidence.append({"source": source, "field_path": field_path, "field": key, "value": item})
                elif isinstance(item, (dict, list)):
                    visit(item, source, field_path)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                visit(item, source, path + f"[{index}]")
    for index, item in enumerate(metadata):
        source = ("conversations.session_overrides" if index % 2 == 0 else "omnigent_conversation_metadata.inference_snapshot") + f"; session_index={index // 2}"
        visit(parsed_json(item), source)
    for session in sessions:
        for event in tool_events(session):
            if event["name"] == "sys_session_get_info" and event["success"] and isinstance(event["output"], dict):
                visit({k: event["output"].get(k) for k in labels},
                      "sys_session_get_info result item " + event["result"]["local_item_sha256"])
    result = {key: next(iter(values)) if len(values) == 1 else "unknown" if not values else "mixed: " + ", ".join(sorted(values))
              for key, values in labels.items()}
    if include_proof:
        result["runtime_metadata_evidence"] = evidence
        result["runtime_metadata_scope"] = "Only stored session overrides/inference snapshot and successful native get_info outputs; absent persisted labels remain unknown; no hidden session state or auth exported"
    return result


def export_trace(database: Path, conversation: str, output: Path, prior_traces=None) -> dict:
    if not re.fullmatch(r"[a-f0-9]{32}", conversation):
        raise ValueError("Use a native 32-character conversation ID")
    db = sqlite3.connect("file:" + str(database.resolve()) + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    root_id = bytes.fromhex(conversation)
    root = db.execute("select * from conversations where id=?", (root_id,)).fetchone()
    if root is None or root["root_conversation_id"] != root_id:
        raise ValueError("Requested root conversation is missing")
    sessions = db.execute("""select c.id,c.parent_conversation_id,c.title,c.created_at,c.updated_at,
                                   c.session_overrides,m.sub_agent_name,m.live_status,m.inference_snapshot
                            from conversations c left join omnigent_conversation_metadata m on c.id=m.id
                            where c.root_conversation_id=? order by c.created_at""", (root_id,)).fetchall()
    traces, observed_roles, calls, receipts, saved_records, runtime_metadata = [], set(), [], [], [], []
    for session in sessions:
        runtime_metadata.extend([session["session_overrides"], session["inference_snapshot"]])
        role = session["sub_agent_name"] or "fly_discovery"
        if role in ROLES:
            observed_roles.add(role)
        items, names = [], {}
        for row in db.execute("select type,status,position,created_at,data from conversation_items where conversation_id=? order by position", (session["id"],)):
            raw = row["data"]
            data = json.loads(raw)
            if row["type"] == 2:
                names[data.get("call_id")] = data.get("name", "")
                calls.append({"role": role, "name": data.get("name"), "created_at": row["created_at"]})
            if row["type"] == 3 and isinstance(data.get("output"), str):
                try:
                    parsed = json.loads(data["output"])
                except json.JSONDecodeError:
                    parsed = data["output"]
                name = names.get(data.get("call_id"), "")
                if name.endswith("read_source_snapshot") and isinstance(parsed, dict):
                    text = parsed.pop("content", "")
                    parsed["snapshot_text_omitted"] = True
                    parsed["returned_text_characters"] = len(text)
                if name.endswith("run_frozen_experiment") and isinstance(parsed, dict) and "receipt_id" in parsed:
                    receipts.append({"receipt_id": parsed["receipt_id"], "role": role,
                                     "test": parsed.get("test"), "receipt_path": parsed.get("receipt_path")})
                if name.endswith("save_discovery_record") and isinstance(parsed, dict) and "record_id" in parsed:
                    saved_records.append(parsed)
                data["output"] = parsed
            items.append({"type": row["type"], "status": row["status"], "position": row["position"],
                          "created_at": row["created_at"], "data": clean(data),
                          "local_item_sha256": hashlib.sha256(raw.encode()).hexdigest()})
        traces.append({"conversation_id": session["id"].hex(), "role": role,
                       "parent_conversation_id": session["parent_conversation_id"].hex() if session["parent_conversation_id"] else None,
                       "title": session["title"], "created_at": session["created_at"],
                       "updated_at": session["updated_at"], "live_status": session["live_status"], "items": items})
    db.close()
    references = [{"path": str(Path(path).resolve().relative_to(ROOT))} for path in prior_traces or []]
    verification = verify_tree(traces, references)
    passed = verification["passed"]
    result = {"schema_version": 3, "exported_at": utc_now(), "omnigent_version": "0.16.0",
              "root_conversation_id": conversation, **runtime_labels(runtime_metadata, traces, include_proof=True),
              "evidence_mode": "independently retrieved cached primary evidence; BrightData unavailable",
              "roles_observed": sorted(observed_roles), "tool_calls": calls,
              "numeric_receipts": receipts, "saved_discovery_records": saved_records,
              "native_discovery_loop_verified": passed, "sessions": traces,
              "verification": verification,
              "prior_traces": verification["reverified_prior_traces"],
              "no_arbitrary_shell_or_apply_patch_observed": verification["no_arbitrary_shell_or_apply_patch_observed"],
              "verification_scope": "Successful collected native handoffs in order; actual experimenter receipt and sealed comparison/raw spike integrity; analyst record links and frozen next_test. Separate follow-up roots require recursive prior-tree reverification, unchanged archived artifact hashes and an exact prior-decision read before current planning/execution. Semantic scientific validity and immutable archival sealing remain separate.",
              "export_policy": "No auth/state tables; source snapshot text omitted, hashes retained"}
    atomic_json(output, clean(result))
    return {"path": str(output), "roles": sorted(observed_roles), "receipts": receipts,
            "saved_records": saved_records, "native_discovery_loop_verified": passed,
            "verification_failures": verification["failures"],
            "cross_session_followup_proofs": verification["cross_session_followup_proofs"],
            "no_arbitrary_shell_or_apply_patch_observed": verification["no_arbitrary_shell_or_apply_patch_observed"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--conversation", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prior-trace", type=Path, action="append", default=[], help="Independently reverify a prior native trace for a separately started follow-up root")
    parser.add_argument("--require-verified", action="store_true", help="Exit nonzero unless the strict native loop gate passes")
    args = parser.parse_args()
    result = export_trace(args.database, args.conversation, args.output, args.prior_trace)
    print(json.dumps(result, indent=2))
    if args.require_verified and not result["native_discovery_loop_verified"]:
        raise SystemExit(2)

if __name__ == "__main__":
    main()
